# E8 — Ingestion et stockage
**Module :** M8 · **Durée :** 6 h · **Livrables :** `preuves/E8-*`, `preuves/E8-dimensionnement.md`

1. **Débit.** Générez 20 000 événements (`send_syslog.py --count 20000 --rate 500 --tcp`). Avec `metrics.log`, tracez le débit par index (`per_index_thruput`) et relevez le **remplissage maximal** de chaque file (`parsingqueue`, `indexqueue`…).
2. **Goulot simulé.** Sur le PC Splunk, lancez une recherche lourde (ou une capture CPU) pendant l'envoi de 50 000 événements. Les files se remplissent-elles ? `blocked=true` apparaît-il ? Documentez, sans conclure plus que ce que vous mesurez.
3. **Index à petite échelle.** Créez `lab_storage` (M8, étape 5), ingérez assez de données pour obtenir ≥ 3 buckets. Fournissez le `dbinspect` et le ratio *disque/brut*.
4. **Rétention.** Démontrez le gel d'un bucket **avec archivage** dans `C:\splunk_frozen\lab_storage` (preuve : dossier + `BucketMover` dans `splunkd.log`). Expliquez la différence entre `frozenTimePeriodInSecs` et `maxTotalDataSizeMB`.
5. **Restauration.** Décrivez (et si possible testez) comment réinjecter un bucket archivé via `thawedPath` (documentation Splunk « Restore archived data ») sans dupliquer les données existantes.
6. **Contre-pression.** Reproduisez M8 étape 9 pour **UF** (0 perte) puis **UDP** (perte) ; tableau comparatif avec compteurs.
7. **Dimensionnement.** Calculez le disque pour : firewall 50 000 ev/h × 190 o, auth 5 000 ev/h × 110 o, 90 jours, ratio mesuré à l'étape 3 (sinon 50 %), marge 30 %. Indiquez le volume de licence/jour.
8. **Recommandations.** Écrivez 5 réglages `indexes.conf` que vous mettriez en production pour `network` et pourquoi.

<details><summary>Indice (2)</summary>Une file qui ne se vide pas = étape **suivante** lente (CPU, disque), pas l'étape où elle est mesurée.</details>
<details><summary>Indice (4)</summary>Après `roll-hot-buckets`, le bucket est **warm** ; le gel se base sur la date du **plus récent** événement du bucket.</details>

## Critères (35 pts)
1: 5 · 2: 4 · 3: 6 · 4: 6 · 5: 3 · 6: 5 · 7: 4 · 8: 2.
