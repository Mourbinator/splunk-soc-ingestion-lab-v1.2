# M4 — Parsing : découpage, horodatage, extractions (≈ 8 h)

## 🎯 Objectifs
Savoir **où** et **comment** Splunk découpe les événements, détermine `_time` et extrait des champs ; écrire un `props.conf`/`transforms.conf` propre ; tester sans casser la production.
**Prérequis :** M1. **Exercice :** `exercises/E4-parsing.md`.

## 🧠 Notions
**Les étapes (simplifiées) de l'indexeur.** `Input → Parsing → Merging (line merge, horodatage) → Typing → Indexing`. Ce qui se règle en **parsing/merging** est **index-time** :
| Besoin | Réglage `props.conf` | Index-time ? |
|---|---|---|
| Où finit un événement ? | `LINE_BREAKER`, `SHOULD_LINEMERGE`, `BREAK_ONLY_BEFORE` | oui |
| Taille maximale | `TRUNCATE` (défaut 10000 octets) | oui |
| Où est l'heure ? Quel format ? | `TIME_PREFIX`, `TIME_FORMAT`, `MAX_TIMESTAMP_LOOKAHEAD`, `TZ` | oui |
| Extraire des champs | `EXTRACT-`, `REPORT-` + `transforms.conf`, `KV_MODE` | **non** (search-time) |
| Champs indexés (rare) | `INDEXED_EXTRACTIONS`, `TRANSFORMS-` avec `WRITE_META` | oui (à éviter) |

**Quel composant applique quoi ?** Le *premier composant qui parse* : indexeur (ou Heavy Forwarder s'il y en a un). L'UF **n'applique pas** `LINE_BREAKER` pour du texte non structuré. Les réglages **search-time** s'appliquent sur le search head.

**Bonnes pratiques.** Toujours préciser `LINE_BREAKER` + `SHOULD_LINEMERGE=false` (rapide), `TIME_PREFIX` + `TIME_FORMAT` + `MAX_TIMESTAMP_LOOKAHEAD`, `TRUNCATE` raisonnable. Préférer le search-time pour les champs.
**Précédence de `props.conf`** : une stanza peut cibler `[sourcetype]`, `[source::chemin]` ou `[host::nom]` ; `source::` > `host::` > sourcetype selon le type de réglage ; testez avec `btool`.

## 🛠️ Pas à pas
### Étape 0 — Préparer le terrain
- Index `lab_sandbox` existe (`btool indexes list lab_sandbox`).
- Variable PowerShell : `$SPLUNK="C:\Program Files\Splunk"` ; `$DS="C:\chemin\splunk-soc-ingestion-lab-v1.2\datasets"`.
- Ingérer un fichier **une fois** : `& "$SPLUNK\bin\splunk.exe" add oneshot "$DS\firewall.log" -sourcetype soc:firewall -index lab_sandbox`.
- Recherche : `index=lab_sandbox earliest=0 | stats count by sourcetype` (les données datent du 10/10/2026 : utilisez *All time* ou `earliest=0`).

### Étape 1 — Voir ce que Splunk fait **sans** TA
1. Retirez temporairement le TA : `Move-Item "$SPLUNK\etc\apps\TA-soc-firewall" "$env:TEMP\"` puis `splunk restart`.
2. Videz le sandbox (voir `docs/DEPANNAGE.md`, « Repartir d'un index propre »), puis `oneshot` du fichier avec `-sourcetype soc:firewall`.
3. Observez : `index=lab_sandbox | table _time _raw | head`. Notez où est `_time` (souvent bien **deviné**, parfois faux) et que les champs `src_ip`… sont présents grâce à l'extraction automatique `key=value` (KV_MODE par défaut).
4. Remettez le TA, redémarrez. **Ne continuez pas sans l'avoir remis.**

### Étape 2 — Lire `props.conf` du TA ligne par ligne
Ouvrez `addons/TA-soc-firewall/default/props.conf`. Pour chaque ligne écrivez : *index-time ou search-time ? quel problème évite-t-elle ?* (correction dans `instructor/ANSWER-KEY.md`).

### Étape 3 — Prouver l'horodatage
```spl
index=lab_sandbox sourcetype=soc:firewall earliest=0
| eval lag_s=_indextime-_time
| stats min(_time) as first max(_time) as last count
| eval first=strftime(first,"%F %T"), last=strftime(last,"%F %T")
```
✅ `first = 2026-10-10 00:00:00`, `last = 2026-10-10 00:33:19`, `count = 2000`.

### Étape 4 — Casser l'horodatage volontairement
1. Dans une **copie** (`...\apps\TA-soc-firewall\local\props.conf`), mettez `[soc:firewall]` + `TIME_FORMAT = %d/%m/%Y %H:%M:%S`.
2. `restart`, videz le sandbox, réingérez.
3. Constat : `_time` = heure d'indexation (ou date aberrante) ; cherchez l'alerte :
```spl
index=_internal sourcetype=splunkd component=DateParserVerbose earliest=-15m | table _time log_level _raw
```
4. Supprimez `local\props.conf`, redémarrez, revalidez. 🔑 *Un `_time` faux est un bug silencieux : les recherches temporelles passent à côté des événements.*

### Étape 5 — Le fuseau horaire (format SSH sans année ni fuseau)
1. Ingérez `datasets/linux-auth.log` avec `-sourcetype linux:auth` dans le sandbox.
2. Résultat : événements du 10 octobre ; l'**année** est déduite par Splunk, le **fuseau** vient de `TZ = UTC` (`TA-soc-linux`).
3. Expérience : mettez `TZ = America/New_York` dans un `local/props.conf`, réingérez : l'heure décale de 4 h. 🔑 *Sans fuseau dans les logs, le TZ de la source est une information à **documenter** dans le contrat d'intake.*

### Étape 6 — Découpage multi-lignes
1. Copiez `datasets/app-multiline.log` sur la VM : `sudo cp datasets/app-multiline.log /var/log/soc-lab/app/app.log` et passez `disabled = 0` pour `[monitor:///var/log/soc-lab/app]` (dans l'app `soc_uf_linux`), ou ingérez par `oneshot` avec `-sourcetype soc:app`.
2. **Avec** `TA-soc-app` : `index=lab_sandbox sourcetype=soc:app | stats count` → **150** ; `| search "Caused by" | head 1 | table _raw` montre l'événement avec **toute** sa stack trace.
3. **Sans** TA-soc-app (retirez le dossier, redémarrez, réingérez) : le défaut (`SHOULD_LINEMERGE=true`) peut recoller correctement ici, mais change si les lignes n'ont pas de date en tête → comparez le nombre d'événements.
4. Cassez volontairement : `SHOULD_LINEMERGE=false` + `LINE_BREAKER=([\r\n]+)` → **282** événements (une ligne = un événement). C'est le symptôme de l'incident 10 (fragmentation).
5. Retour à la normale.

### Étape 7 — Extractions search-time et champs
```spl
index=lab_sandbox sourcetype=soc:firewall earliest=0 | head 5 | table event_id src_ip dest_ip dest_port action action_raw app
```
✅ `app` **sans guillemets** (extraction `quoted`). Ouvrez `transforms.conf` : deux regex, une pour les valeurs entre guillemets et une pour les simples. Pourquoi deux ? (*Les guillemets sont conservés si on utilise une seule regex qui capture `"…"`.*)

### Étape 8 — Anomalies : le parsing face au réel
Ingérez `datasets/firewall-anomalies.log` (sandbox), puis :
```spl
index=lab_sandbox source=*firewall-anomalies.log earliest=0
| table event_id action src_ip protocol dest_port app _raw
```
Complétez le tableau (voir E4) : pour chaque anomalie, *que voit-on ? faut-il corriger le parsing, le TA, ou rejeter la donnée ?* Exemples : `fw-an-0001` (pas d'`action`), `0006` (valeur avec `=`), `0013` (JSON : aucun champ extrait).

### Étape 9 — Utiliser l'assistant « Add Data »
*Settings → Add Data → Upload* : chargez `firewall.log`, sourcetype `soc:firewall`. Regardez l'aperçu : fautes de découpage ou d'heure sautent aux yeux. 🔑 L'assistant est un **atelier de mise au point** ; la configuration finale va dans un **TA versionné**, pas dans `local` d'un poste.

### Étape 10 — Cartographier « où mettre quoi »
Remplissez : `LINE_BREAKER` → *indexeur/HF* · `EXTRACT-` → *search head* · `SEDCMD` → *indexeur/HF* · `inputs.conf` → *UF*. (Réponse en fin de `ANSWER-KEY.md`.)

## ⚠️ Pièges
- Modifier `props.conf` et attendre un effet sur les **anciennes** données (impossible pour l'index-time).
- Oublier `MAX_TIMESTAMP_LOOKAHEAD` → Splunk prend un nombre quelconque comme date.
- `TRUNCATE = 0` (illimité) = risque mémoire.
- `KV_MODE=auto` **et** `REPORT-` sur les mêmes champs → doublons (valeurs multiples) : d'où `KV_MODE = none` dans le TA firewall.
- Placer les réglages sur l'UF « parce que c'est là que les données entrent ».

## 📝 Auto-évaluation
1. Quel composant applique `LINE_BREAKER` ? 2. Pourquoi `TIME_PREFIX = \bevent_time=` ?
3. Un `_time` à 1970 : donnez 3 causes. 4. Différence `EXTRACT-` / `REPORT-` ?
