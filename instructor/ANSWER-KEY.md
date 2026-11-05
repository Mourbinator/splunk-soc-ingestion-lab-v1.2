# Corrigé et notes formateur

> À consulter **après** avoir essayé. Les valeurs chiffrées viennent des datasets du dépôt ; ce qui dépend du comportement de Splunk sur *votre* version est signalé « à vérifier ».

## 1. Auto-évaluations des modules
**M0** — 1) Index-time : découpage (`LINE_BREAKER`), horodatage (`TIME_*`), réécriture `host/sourcetype/index`, masquage `SEDCMD`, `nullQueue`. Search-time : `EXTRACT`/`REPORT`, `FIELDALIAS`, `EVAL`, `LOOKUP`, tags/eventtypes. 2) Un UF n'a pas de tampon réseau adapté à un flux Syslog continu, perd les paquets UDP pendant ses redémarrages et mélange tous les émetteurs ; un collecteur écoute en permanence, tamponne et route. 3) 150 × 220 × 86 400 = 2 851 200 000 o ≈ **2,85 Go/jour**. 4) Valeur cible chiffrée, méthode de mesure (requête), période, responsable/action en cas de violation.

**M1** — 1) `system/local` gagne sur `apps/*/default` ; `btool inputs list --debug` le prouve (chaque ligne montre son fichier). 2) Le fishbucket mémorise l'identité (CRC) et la position de lecture. 3) `useACK` protège contre la perte entre l'UF et l'indexeur (réseau, redémarrage de Splunk) ; il ne protège pas la perte **avant** l'UF (UDP, fichier supprimé) ni une mauvaise configuration. 4) Limite `maxKBps` de l'UF (256 Ko/s par défaut) ; fichier énorme relu après rotation ; indexeur occupé (files).

**M2** — 1) PRI = facility×8+severity : 134 = 16×8+6 → local0.info. 2) PROCID, MSGID et STRUCTURED-DATA valent `-` (vides) : trois champs avant le message. 3) Écrit dans `unrouted.log` (puis `soc:unrouted` dans `lab_api`). 4) Comparer généré (`sent`) et reçu (comptage `event_id`) sur un lot suffisamment grand (≥ 10 000 → 30 manquants), avec la séquence des `event_id`.

**M3** — 1) `/raw` (l'événement est du texte brut, les règles de parsing s'appliquent). `/event` utilise le `time` fourni. 2) S'il était écrit avant, un plantage entre l'écriture et l'envoi perdrait des événements ; écrit après, le pire est un doublon, neutralisé par la déduplication. 3) 400 = requête invalide, la même requête échouera toujours (et le checkpoint ne doit pas avancer) ; 503 = situation temporaire. 4) Qu'un plantage ne laisse jamais un fichier à moitié écrit (écriture dans un `.tmp` puis `os.replace` atomique).

**M4** — 1) L'indexeur (ou le Heavy Forwarder) — pas l'UF pour du texte brut. 2) Pour ancrer l'horodatage au champ `event_time=` et non au premier nombre ressemblant à une date. 3) Format de date incorrect, `TIME_PREFIX` absent/mauvais, fuseau/epoch, ou valeur source à 0. 4) `EXTRACT-` = regex inline avec groupes nommés ; `REPORT-` = référence à une stanza de `transforms.conf` (réutilisable, plusieurs regex).

**M5** — 1) Extractions → FIELDALIAS → EVAL → LOOKUP → eventtypes → tags. 2) `network` + `communicate`. 3) Pour ne pas perdre la valeur brute et rendre les écarts diagnostiquables. 4) Les objets du TA sont visibles de toutes les apps.

**M6** — 1) Elles sont réservées à la documentation (non routables), donc absentes des bases GeoIP. 2) Search-time : rétroactif, la table change sans réindexer. 3) Le champ `zone` du lookup est renommé `src_zone` dans l'événement. 4) Table volumineuse (centaines de milliers de lignes), modifiée souvent ou en écriture concurrente.

**M7** — 1) Indexeur/Heavy Forwarder (premier composant qui parse), pas UF. 2) L'événement est supprimé avant indexation. 3) L'index-time est irréversible. 4) `_MetaData:Index` désigne l'**index** de destination (préfixe `_MetaData:` obligatoire) ; `MetaData:Host` modifie le champ `host`.

**M8** — 1) hot → warm → cold → frozen (→ thawed si restauré). 2) La file est pleine et bloque l'étape en amont. 3) UDP n'a pas d'accusé : un paquet jamais reçu n'est jamais redemandé. 4) 20 × 30 × 0,5 = **300 Go** (+ marge).

**M9** — 1) Il lit les métadonnées indexées sans scanner les événements : très rapide. 2) Horloge de la source en avance ou fuseau mal interprété (l'événement paraît « dans le futur »). 3) Séquence min/max + `dc(seq)` par lot. 4) Maintenance planifiée, week-end pour une source métier, changement de nom d'hôte, fenêtre de recherche trop courte, source volontairement arrêtée.

## 2. Corrigés des exercices
### E0
- Volume : (60×43 200 + 20×43 200) × 210 ≈ **726 Mo/jour** brut ; ×90 j ×0,5 ≈ **32,7 Go**.
- Choix : fichiers nginx sur un serveur administré → **UF** (agent) + app de config déployée ; pas de collecteur (pas de Syslog) ; parsing sur l'indexeur.
- SLO vérifiables : fraîcheur (`tstats latest(_time)`), retard p95, complétude (trous de séquence impossibles ici : proposer un contrôle par volume horaire vs nginx `status`), dérive de format (regex).

### E1
- Partie B-6 : `maintenance.log.1` ne correspond pas à `whitelist = \.log$` → **non relu** ; le nouveau `maintenance.log` produit **3 événements**.
- Partie B-7 : à vérifier sur votre version. Un fichier dont le début est identique à un fichier déjà vu peut être considéré comme connu (CRC des premiers octets) et ne pas être relu ; `crcSalt = <SOURCE>` ou une modification de `initCrcLength` change ce comportement. Démontrer et expliquer est l'objectif.
- Partie C : `useACK = true` (et le fait que l'UF cesse de lire quand la sortie est bloquée).
- Partie D : cause exacte parmi les 5 pannes ; preuves : `splunk btool inputs list --debug`/`list inputstatus`/`splunkd.log` (UF) et `tstats`/`_internal` (Splunk).

### E2
- UDP et TCP : écart attendu **0** en boucle locale ; une perte en UDP se localise entre « généré » et « reçu fichier ».
- Étape 2 : `filter f_soc_other { not (filter(f_soc_firewall) or filter(f_soc_vpn)); };` ; destination `d_soc_vpn` (chemin `/var/log/soc-lab/vpn/vpn.log`) ; `log { source(s_soc_udp); source(s_soc_tcp); filter(f_soc_vpn); destination(d_soc_vpn); };`.
- Étape 4 : avec `postrotate ... syslog-ng-ctl reload`, la perte est nulle ; sans reload, syslog-ng continue d'écrire dans l'ancien fichier renommé (fuite d'événements côté UF).
- Étape 5 : en boucle locale la perte est souvent nulle car le noyau absorbe tout ; sur réseau réel, le tampon du socket UDP (`net.core.rmem_max`) déborde.

### E3
- Étape 2 : `retried ≥ http_429 + http_5xx` (chaque erreur réessayable est comptée) ; total toujours 500.
- Étape 4 : si `seen_ids` **et** `next` sont perdus, le poller relit tout et **renvoie 500 doublons** (`count=1000`, `dc=500`) → c'est pourquoi un vrai poller utilise aussi un curseur temporel (`since`).
- Étape 5 (patch) :
```python
# new_metrics(): ajouter "bytes_sent": 0
# send_hec(): remplacer l'appel par
payload = hec_payload(events, cfg, index, sourcetype)
status, headers, body = http_call(url, "POST", {"Authorization": f"Splunk {cfg.hec_token}"}, payload, cfg.insecure, cfg.timeout)
if status == 200:
    metrics["sent"] += len(events); metrics["bytes_sent"] += len(payload); return
```
Test : `self.assertGreater(m["bytes_sent"], 0)` dans `test_hec_real_path_retry_and_payload`.
- Étape 6 — 5 défauts : ignore `Retry-After` ; pas de retry ; saute la page ; pas de checkpoint ; pas de dédup (et pas de métriques d'erreurs).

### E4
- A-2 : sans `\b` le préfixe peut accrocher un autre texte contenant `event_time=` ; avec `MAX_TIMESTAMP_LOOKAHEAD=5` l'horodatage n'est pas lu en entier → `_time` faux/héritée + avertissements `DateParserVerbose`.
- B-5 : `SHOULD_LINEMERGE=false` + `([\r\n]+)` → **282** ; `LINE_BREAKER` jamais satisfait → quelques événements très longs (coupés à `TRUNCATE`).
- B-6 : `([\r\n]+)(?=\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}[,.]\d{3}Z?\s)`.
- Anomalies (14 lignes) :
| # | Observation | Décision |
|---|---|---|
| 0001 | pas d'`action` → `action=unknown` | alerte validité (Q04/Q07) |
| 0002 | pas de `src_ip` → `src` vide | alerte champs obligatoires |
| 0003 | `action=reset` → `unknown` | demander au propriétaire ; éventuellement mapper `reset→blocked` |
| 0004 | fuseau `+9900` invalide → horodatage non fiable (avertissements) | rejeter à la source |
| 0005 | IPv6 extraite ; les lookups CIDR IPv4 ne s'appliquent pas | étendre les lookups |
| 0006 | `app="a=b c d"` bien extrait (regex « quoted ») | OK ; ajouter un test |
| 0007 ×2 | deux événements de même `event_id` | dédup à la source ou `dedup` ; alerte Q05 |
| 0009 | pas d'`event_time` → `_time` héritée/horloge d'indexation | violation du contrat ; Q03 |
| 0010 | `protocol=TCP` → `transport=tcp` (EVAL `lower`) | OK |
| 0011 | champ `geo` inconnu extrait tel quel | noter la dérive, pas de blocage |
| 0012 | `dest_port=70000` extrait | contrôle de validité (1–65535) |
| 0013 | JSON : aucun champ | dérive de format (Q08) |
| 0014 | colonnes : aucun champ | dérive de format (Q08) |
- D : `TRUNCATE` par défaut 10 000 → `_raw` tronquée à 10 000 octets, la suite est **ignorée** ; pour conserver : `TRUNCATE = 20000` (valeur bornée) ; `0` = illimité → risque mémoire/événement géant.
- E (où l'applique-t-on) : `LINE_BREAKER`, `TRUNCATE`, `TIME_*`, `SEDCMD`, `TRANSFORMS-` → **indexeur/HF** ; `EXTRACT`, `REPORT`, `KV_MODE`, `FIELDALIAS`, `EVAL`, `LOOKUP`, tags/eventtypes → **search head** ; `inputs.conf`, `INDEXED_EXTRACTIONS` → **agent**.

### E5 (pistes)
```
# props.conf (soc:firewall) — ajouts possibles
EVAL-dvc = host
EVAL-direction = case(dest_zone=="internet","outbound", src_zone=="internet","inbound", true(),"internal")
```
(`direction` dépend des lookups, exécutés **après** les EVAL : la valeur serait vide → piège ! Solution : la calculer à la recherche ou avec un lookup/`eval` dans la recherche.) Tests SPL : `index=... sourcetype=soc:firewall | where NOT match(action,"^(allowed|blocked|unknown)$") | stats count` → 0 ; `NOT tag=network` → 0 ; `| where transport!=lower(transport)` → 0.
Change : `EVAL-status = case(...)`, `EVAL-object_category = "iam"`, `EVAL-command = signature` (valide car `signature` vient d'un FIELDALIAS).

### E6
```
# soc_users.csv
user,department,is_privileged
alice,finance,false
bob,it,false
svc-backup,it,true
root,it,true
admin,it,true
# transforms.conf
[soc_users]
filename = soc_users.csv
# props.conf (SA-soc-enrichment)
[linux:auth]
LOOKUP-soc_user = soc_users user OUTPUT department is_privileged
```
CIDR : `192.0.2.200` → `internet` (/25 .128–.255) ; `192.0.2.63` → `guest-wifi` ; `192.0.2.64` → `partner` ; `203.0.113.5` → **aucune** zone (absent de la table : plage de documentation non déclarée).

### E7
- Fichiers : voir `instructor/solutions/soc_routing/default/`.
- Mesures : comptez sur le fichier collecteur `grep -c 'dest_port=53 action=allow'` et `grep -c 'dest_port=3389'` pour le lot ; après : `index=network ... dest_port=53 action=allow` doit donner 0 et `index=security` ≈ nombre de RDP.
- Économie R3 : 20 ev/s × 86 400 × 190 o × P(DNS-allow) ; avec `send_syslog.py` (port 53 une fois sur 5, allow 60 %) P ≈ 0,12 → ≈ 39 Mo/jour pour 20 ev/s ; avec le dataset (2/9 des ports, allow 75 %) P ≈ 0,17 → ≈ 55 Mo/jour. Recalculez avec vos propres mesures.
- Ordre (R2/R5) : les deux transformations écrivent `_MetaData:Index` ; **la dernière exécutée gagne** (liste ordonnée : l'ordre de la liste est l'ordre d'exécution).
- Retour arrière R3 : retirer `soc_drop_dns_allow` de la liste, `restart` ; les événements supprimés **ne reviennent pas** : prévoir un rejeu depuis le fichier du collecteur (seule source conservée).

### E8
- Dimensionnement : firewall 50 000×24×190 = 228 Mo/j ; auth 5 000×24×110 = 13,2 Mo/j → **241 Mo/j** brut ; ×90 = 21,7 Go ; ×0,5 = 10,8 Go ; +30 % ≈ **14,1 Go**. Licence ≈ 0,24 Go/j.
- Réglages `network` en prod (exemples) : `frozenTimePeriodInSecs`, `maxTotalDataSizeMB`, `maxDataSize = auto`, `coldToFrozenDir`/script, volumes séparés hot/cold.
- Gel : selon l'âge du **plus récent** événement du bucket.

### E9
Mapping 7 dimensions → recherches : Volume Q01 · Fraîcheur Q02 · Retard Q03 · Complétude Q04/Q06 · Unicité Q05 · Validité Q07 · Dérive Q08. Santé interne : Q09–Q14. Alerte « trou » : `... | stats latest(_time) as last min(seq) ... by run | where now()-last>300 AND missing>0`.

### E10
Voir barème. Contrôles attendus : 1000 événements, `_time` = 10/10/2026 00:00:00→00:16:39 (1 par seconde), `status` ∈ {200,301,304,403,404,500}, tag `web`, 3 recherches qualité, tests regex sur 1000 lignes.

## 3. Corrigés des incidents
| INC | Cause racine | Preuves clés | Correctif | Prévention |
|---|---|---|---|---|
| 01 | Émetteur vers le port 514 (personne n'écoute) | UDP silencieux ; TCP *refused* ; `ss` n'a que 5514 ; tcpdump montre l'émission | `--port 5514` | alerte fraîcheur Q02, contrat avec port, test d'accueil |
| 02 | Fichier `root:root 600` illisible pour l'UF | `sudo -u splunkfwd head` → denied ; `splunkd.log` (UF) avertit des droits ; le fichier grossit | `chgrp adm` + `chmod 640`, UF dans `adm` | logrotate `create 0640 root adm`, Q10, test de lecture au runbook |
| 03 | `outputs.conf` : IP fausse (10.50.0.100) | `list forward-server` *inactive* ; `btool outputs` ; `TcpOutputProc` en erreur ; `nc` vers la bonne IP OK | restaurer l'IP, restart | Deployment Server, Q10 |
| 04 | `index = netwrok` (inexistant) | `splunkd` « unconfigured/disabled/deleted index » ; `tstats` ne voit pas l'index ; fichier collecteur OK | corriger la faute, rejouer les 100 événements | alerte Q13, revue de config, `lastChanceIndex` (à étudier) |
| 05 | Pas de `sourcetype` sur l'input | `tstats ... by sourcetype source` : sourcetype inattendu ; `btool inputs` | restaurer la ligne ; réingérer l'historique ou `soc_fw_sourcetype` temporaire | test sourcetype attendu par index |
| 06 | `TZ = Pacific/Auckland` dans `local/` | `lag` ≈ 46 000 s constant ; `btool props` montre `local/` | supprimer `local/`, restart, réingérer | contrat (fuseau), Q03, pas de `local/` en prod |
| 07 | `communicate = disabled` dans `local/tags.conf` | `stats by eventtype tag` : pas de `communicate` ; `btool tags` | supprimer `local/tags.conf` | test SPL de tags, pas de `local/` |
| 08 | Poller sans retry/429 : pages perdues | trous par blocs de 100 ; 429 dans les logs du mock ; code | `poller.py` (retry + checkpoint + dédup) | alerte `sent != fetched`, tests auto, Q12 |
| 09 | Token faux (403) / index interdit (400) | message `[fatal] HEC 403/400` ; Allowed indexes du token ; checkpoint inchangé | bon token / bon index | un token par usage, rotation, Q11 |
| 10 | `LINE_BREAKER` perturbé dans `local/` | 282 (ou très peu) au lieu de 150 ; `btool props soc:app` | supprimer `local/`, restart, vider le sandbox, réingérer | test de comptage (150) dans la recette du TA |

## 4. Évaluation et animation
- **Rubrique générale** (chaque exercice) : exactitude technique 40 % · preuves 30 % · compréhension (explications) 20 % · propreté (secrets, versions, documentation) 10 %.
- **Signaux d'un apprenant qui maîtrise** : il cite spontanément *où* s'applique un réglage, donne une **mesure** avant de conclure, change **une** chose à la fois et sait expliquer le *pourquoi* d'une perte.
- **Questions de relance** : « Comment le prouves-tu ? », « Et si c'était du Syslog UDP ? », « Que se passe-t-il pour les anciennes données ? ».
- **Limites** : les chiffres de rattrapage, la durée du gel de buckets et le libellé exact des messages de `splunkd.log` varient selon la version : faire constater, ne pas faire apprendre par cœur.
