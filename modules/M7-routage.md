# M7 — Routage, filtrage et masquage (≈ 5 h)

## 🎯 Objectifs
Décider **où** va chaque événement et **s'il** doit être conservé, corrigé ou masqué : au collecteur (syslog-ng) et à l'indexeur (`props.conf`/`transforms.conf`), avec les risques associés.
**Prérequis :** M2, M4. **Exercice :** `exercises/E7-routage.md`.

## 🧠 Notions
- Le routage peut se faire à **trois endroits** : (A) **collecteur** (syslog-ng : par émetteur/APP-NAME → fichier), (B) **indexeur/HF** (index-time : réécrire `host`, `sourcetype`, `index`, supprimer, masquer), (C) **entre instances** (`_TCP_ROUTING` sur un HF).
- **Index-time = irréversible.** Un événement envoyé dans la mauvaise destination, supprimé ou masqué **ne se récupère pas**. Procédure : *tester dans le sandbox → relire → déployer → surveiller*.
- **Anatomie d'une transformation** :
```
props.conf       [soc:firewall]
                 TRANSFORMS-<classe> = <transform1>, <transform2>   (exécutés dans l'ordre)
transforms.conf  [<transform1>]
                 REGEX    = <quand ?>
                 DEST_KEY = <quelle métadonnée modifier>   (MetaData:Host, MetaData:Sourcetype, _MetaData:Index, queue, _TCP_ROUTING)
                 FORMAT   = <nouvelle valeur>
```
- `SEDCMD-<nom> = s/regex/remplacement/g` : modifie le **texte brut** avant indexation (masquage).

## 🛠️ Pas à pas
> Tout se fait dans une app à vous : `...\etc\apps\soc_routing\local\{props,transforms}.conf` (la solution est dans `instructor/solutions/soc_routing/`). Testez sur le sandbox quand c'est possible, **redémarrez** après chaque modification.

### Partie A — Routage au collecteur (rappel M2)
`soc-lab.conf` envoie `soc-firewall` vers `firewall.log` et le reste vers `unrouted.log`. Ajoutez une 3ᵉ famille : filtre `program("^soc-vpn$")` → fichier `vpn.log` (destination + `log {}`), `syslog-ng --syntax-only`, test `send_syslog.py --app soc-vpn`.

### Partie B — Routage à l'indexeur

#### B1 — Réécrire `host` depuis le message
Les lignes produites par syslog-ng commencent par `<date> <hôte> event_id=…`.
```
# transforms.conf
[soc_set_host_from_line]
REGEX = ^\S+\s+(\S+)\s+event_id=
DEST_KEY = MetaData:Host
FORMAT = host::$1
# props.conf
[soc:firewall]
TRANSFORMS-soc_host = soc_set_host_from_line
```
Test : nouveaux événements via `send_syslog.py --hostname firewall01` → `index=network | stats count by host` ⇒ `firewall01` (et non le nom de la VM). *Les anciens événements ne changent pas.*

#### B2 — Corriger un sourcetype
Si un flux arrive avec un mauvais sourcetype (incident 05) :
```
[soc_fw_sourcetype]
REGEX = event_id=fw-
DEST_KEY = MetaData:Sourcetype
FORMAT = sourcetype::soc:firewall
```
à rattacher dans `props.conf` à la stanza **du sourcetype d'arrivée** (ex. `[soc:unrouted]`). Attention : le nouveau sourcetype déclenche ensuite **son** `props.conf`... sur les étapes search-time ; mais le découpage/horodatage d'index-time a déjà été fait avec l'ancien. 🔑 *Mieux vaut corriger à la source (inputs.conf).*

#### B3 — Router vers un autre index
```
[soc_route_rdp_to_security]
REGEX = \sdest_port=3389\s
DEST_KEY = _MetaData:Index
FORMAT = security
```
`TRANSFORMS-soc_idx = soc_route_rdp_to_security` dans `[soc:firewall]`. L'index `security` doit **exister**, sinon les événements sont perdus (voir incident 04). Test : `index=security sourcetype=soc:firewall`.

#### B4 — Filtrer le bruit (nullQueue)
Supprimer les DNS autorisés (haut volume, faible valeur) :
```
[soc_drop_dns_allow]
REGEX = (?=.*\sdest_port=53\s)(?=.*\saction=allow\s)
DEST_KEY = queue
FORMAT = nullQueue
```
Une transformation qui supprime doit s'exécuter **en premier** : voir B6 (un seul attribut `TRANSFORMS-` avec une liste ordonnée). Mesurez l'économie : comparez le volume avant/après (script E7). 🔑 *Avant de supprimer, mesurez ce que vous supprimez, et obtenez l'accord du propriétaire des données.*

#### B5 — Masquer des données sensibles (SEDCMD)
Dans `soc:app`, les lignes `DEBUG` contiennent `password=…` et `Authorization: Bearer …` :
```
[soc:app]
SEDCMD-soc_mask_password = s/password=\S+/password=********/g
SEDCMD-soc_mask_bearer = s/Bearer\s+\S+/Bearer ********/g
```
Test : `index=lab_sandbox sourcetype=soc:app earliest=0 | search password=* | table _raw`. ✅ `password=********`. 🔑 Un masquage **après coup** n'efface pas les anciennes données : il faut le faire **avant** la première ingestion.

#### B6 — Assembler dans le bon ordre
Dans une même stanza, **une seule** ligne `TRANSFORMS-` avec une liste ordonnée (l'ordre de la liste est l'ordre d'exécution ; entre attributs différents l'ordre dépend du nom, donc on évite) :
```
[soc:firewall]
TRANSFORMS-soc_pipeline = soc_drop_dns_allow, soc_set_host_from_line, soc_route_rdp_to_security
```
Redémarrez, envoyez un lot (`send_syslog.py --count 200`) et vérifiez les trois effets d'un coup (voir E7).

### Partie C — Entre instances (optionnel, `configs/hf/`)
Un Heavy Forwarder peut envoyer certains événements vers un autre groupe de destination :
```
# transforms.conf (HF)
[soc_route_rdp_to_group_b]
REGEX = dest_port=3389\b
DEST_KEY = _TCP_ROUTING
FORMAT = group_b
```
`outputs.conf` définit `[tcpout:group_a]` et `[tcpout:group_b]`. **Remplacer** la cible envoie *seulement* vers `group_b` ; pour envoyer vers les deux : `FORMAT = group_a,group_b`. Test : arrêter le second récepteur et observer les files d'attente (`blocked=true`, M8).

### Partie D — Vérifier et sécuriser vos changements
```bash
splunk btool props list soc:firewall --debug
splunk btool transforms list soc_drop_dns_allow --debug
splunk btool check
```
Checklist avant déploiement : *regex testée sur ≥ 20 lignes réelles, ordre des TRANSFORMS, index destinataire existant, test sur sandbox, plan de retour arrière, accord du propriétaire*.

## ⚠️ Pièges
- Regex trop large → on supprime ou on déplace **tout**.
- **Ordre** des transformations (la suppression doit précéder).
- Appliquer à l'UF : `TRANSFORMS-` **ne s'exécute pas** sur un UF (texte non structuré).
- Index inexistant → perte silencieuse.
- Masquage qui casse un parsing en aval (le `password=` fait partie d'un format de champ).

## 📝 Auto-évaluation
1. Où doivent vivre `TRANSFORMS-`/`SEDCMD-` ? 2. Que fait `DEST_KEY = queue / FORMAT = nullQueue` ?
3. Pourquoi tester d'abord sur le sandbox ? 4. Différence entre `_MetaData:Index` et `MetaData:Host` ?
