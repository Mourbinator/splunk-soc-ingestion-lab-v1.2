# M8 — Ingestion et stockage (≈ 6 h)

## 🎯 Objectifs
Comprendre ce qui se passe **dans** l'indexeur (pipelines, files d'attente), lire les métriques internes, maîtriser le cycle de vie des données (buckets, rétention, archivage) et dimensionner.
**Prérequis :** M1, M4. **Exercice :** `exercises/E8-ingestion-stockage.md`.

## 🧠 Notions
**Pipelines et files d'attente.** Les données passent par des étapes reliées par des **files d'attente (queues)** :
`input → parsingQueue → aggQueue → typingQueue → indexQueue → disque`. Si une étape est lente, sa file se remplit (`blocked=true` dans `metrics.log`), la contre-pression remonte jusqu'à l'UF (qui garde ses données : c'est le rôle de l'**ACK**) — sinon c'est la **perte** (UDP, HEC sans ACK).

**Structure d'un index : les buckets.**
| État | Rôle | Défaut/paramètre |
|---|---|---|
| **hot** | en cours d'écriture | `maxHotBuckets`, `maxDataSize` (taille), `maxHotSpanSecs` |
| **warm** | fermé, recherché rapidement | `homePath` |
| **cold** | plus ancien, stockage moins cher | `coldPath` |
| **frozen** | **supprimé** ou archivé | `frozenTimePeriodInSecs` (âge), `maxTotalDataSizeMB` (taille), `coldToFrozenDir` (copie avant suppression) |
| **thawed** | données archivées réinjectées | `thawedPath` |
Un bucket est gelé quand **tous** ses événements dépassent l'âge limite **ou** quand l'index dépasse sa taille maximale (le plus vieux bucket part).

**Volumétrie.** Licence = volume **ingéré** par jour (Go/jour). Stockage ≈ 50 % du brut (à mesurer). **Dimensionnement :** `Go/jour × jours de rétention × 0,5 ≈ disque`.

## 🛠️ Pas à pas
### Étape 1 — Observer l'ingestion en direct
```spl
index=_internal source=*metrics.log* group=per_index_thruput earliest=-15m
| timechart span=1m sum(kb) by series
```
✅ Courbes par index. Générez du trafic (`send_syslog.py --count 2000 --rate 200`) et voyez `network` monter.

### Étape 2 — Les files d'attente
```spl
index=_internal source=*metrics.log* group=queue earliest=-15m
| eval fill_pct=round(current_size_kb/max_size_kb*100,1)
| stats max(fill_pct) as max_fill avg(fill_pct) as avg_fill by name
```
✅ Les files `parsingqueue`, `indexqueue`… avec un remplissage faible. Cherchez `blocked=true` :
`index=_internal source=*metrics.log* group=queue blocked=true | stats count by name`. 🔑 *Une file proche de 100 % = goulot d'étranglement en aval de cette file.*

### Étape 3 — Qui m'envoie des données ?
```spl
index=_internal source=*metrics.log* group=tcpin_connections earliest=-15m
| stats sum(kb) as kb latest(_time) as last by hostname sourceIp version
| eval last=strftime(last,"%F %T")
```
Les UF actifs ; `eps`/`kb` donnent leur débit.

### Étape 4 — Inspecter les buckets
```spl
| dbinspect index=network
| table bucketId state startEpoch endEpoch eventCount sizeOnDiskMB
| eval startEpoch=strftime(startEpoch,"%F %T"), endEpoch=strftime(endEpoch,"%F %T")
```
✅ Au moins un bucket `hot`. Notez `eventCount` et `sizeOnDiskMB` : **ratio disque/brut** = `sizeOnDiskMB*1048576 / (nb_événements × taille_moyenne)`.

### Étape 5 — Créer un index de démonstration à petite échelle
Créez `...\etc\apps\soc_lab_base\local\indexes.conf` (jamais dans `default/`) :
```
[lab_storage]
homePath   = $SPLUNK_DB/lab_storage/db
coldPath   = $SPLUNK_DB/lab_storage/colddb
thawedPath = $SPLUNK_DB/lab_storage/thaweddb
maxDataSize = 5
maxHotBuckets = 1
frozenTimePeriodInSecs = 604800
coldToFrozenDir = C:\splunk_frozen\lab_storage
```
Créez le dossier `C:\splunk_frozen\lab_storage`, redémarrez. (`maxDataSize = 5` : buckets de ~5 Mo, pour voir le cycle sans énorme volume.)

### Étape 6 — Voir le cycle hot → warm
1. Ingérez `firewall.log` plusieurs fois dans `lab_storage` (`oneshot`) pour dépasser 5 Mo, ou forcez : `& "$SPLUNK\bin\splunk.exe" _internal call /data/indexes/lab_storage/roll-hot-buckets -method POST`.
2. `| dbinspect index=lab_storage | table bucketId state eventCount sizeOnDiskMB`. ✅ Passage de `hot` à `warm`.

### Étape 7 — Démontrer la rétention (gel)
1. Les données du dataset datent du **10/10/2026**. Avec `frozenTimePeriodInSecs = 3600` (1 h) dans `lab_storage` et des événements plus anciens, les buckets **warm** deviennent éligibles au gel.
2. Modifiez la valeur à 3600, redémarrez, forcez un roll (étape 6), attendez 1-5 minutes.
3. Preuve : `| dbinspect index=lab_storage` ne montre plus les buckets, `C:\splunk_frozen\lab_storage` contient une copie, et :
```spl
index=_internal sourcetype=splunkd component=BucketMover earliest=-30m | table _time _raw
```
🔑 *Splunk gèle selon l'âge du **plus récent** événement d'un bucket ; sans `coldToFrozenDir` ou script, « frozen » = **supprimé**.* (Le moment exact dépend de la version : cherchez dans les logs plutôt que d'attendre.)

### Étape 8 — Licence et volume
```spl
index=_internal source=*license_usage.log type=Usage earliest=-7d
| stats sum(b) as bytes by idx | eval MB=round(bytes/1048576,2) | sort - MB
```
(Fonctionne si vous avez les droits sur `_internal` ; sinon *Settings → Licensing*.)

### Étape 9 — Test de contre-pression (panne contrôlée)
1. Notez le nombre d'événements `linux:auth` indexés.
2. Arrêtez Splunk (Windows). Générez 200 lignes sur la VM (`write_linux_logs.py --count 200 --rate 0`).
3. Sur l'UF : `splunk list forward-server` → *inactive*. Regardez `splunkd.log` : tentatives de reconnexion.
4. Redémarrez Splunk. Attendez la reconnexion.
5. ✅ Le total augmente de **exactement 200**. Comparez avec un flux **UDP** (arrêtez syslog-ng, envoyez 200 messages UDP : ils sont **perdus**). Rédigez la conclusion.

### Étape 10 — Dimensionner (calcul à rendre)
Pour 50 000 ev/h de firewall (190 o), 5 000 ev/h d'auth (110 o), rétention 90 j : brut/jour, stockage estimé (×0,5), marge 30 %. (Corrigé dans ANSWER-KEY.)

### Étape 11 — Pour aller plus loin (sans lab)
| Sujet | Idée |
|---|---|
| Cluster d'indexeurs | réplication des buckets, `repFactor`, `searchFactor` |
| SmartStore | buckets en stockage objet |
| Volumes | `[volume:...]` pour regrouper les disques |
| Archivage | `coldToFrozenScript`, restauration par `thawedPath` |

## ⚠️ Pièges
- Un seul disque qui se remplit → l'indexation **s'arrête** (alerte `minFreeSpace`).
- `frozenTimePeriodInSecs` court sur des données au **timestamp ancien** : gel immédiat (voir étape 7).
- Confondre retention (âge) et plafond (taille) : le plus restrictif gagne.
- Oublier `coldToFrozenDir` : « frozen » = suppression définitive.
- Changer `default/indexes.conf` d'une app au lieu de `local/`.

## 📝 Auto-évaluation
1. Dans quel ordre vont les buckets ? 2. Que signifie `blocked=true` ? 3. Pourquoi l'ACK n'aide-t-il pas en UDP ?
4. Calculez le disque pour 20 Go/jour sur 30 jours (hypothèse 50 %).
