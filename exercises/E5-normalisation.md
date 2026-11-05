# E5 — Normalisation CIM : compléter, tester, versionner
**Module :** M5 · **Durée :** 8 h · **Livrables :** diff du TA, `CHANGELOG`, `preuves/E5-*`

1. **Network Traffic complet.** Vérifiez que `bytes`, `app`, `rule`, `transport`, `src`, `dest`, `action` existent. Ajoutez ce qui manque : `bytes_in`/`bytes_out`? (non, pas de données) → justifiez ; `dvc` (ex. valeur du host de l'événement) ; `direction` calculée (`src_zone`/`dest_zone` : `outbound` si dest_zone=`internet`…).
2. **Test de non-régression.** Écrivez 3 recherches SPL dans `tests/spl/` (`08-…`, `09-…`, `10-…`) qui échouent si : `action` n'est pas dans `{allowed,blocked,unknown}` · un événement n'a pas le tag `network` · `transport` n'est pas en minuscules. Décrivez le résultat attendu (0 ligne).
3. **Casser puis réparer.** Introduisez 2 régressions (ex. alias faux, tag manquant) dans `local/` ; montrez que vos tests les détectent ; réparez.
4. **Authentication (Linux).** Ajoutez `dest` (déjà), `src_user`… ? Complétez pour que `| datamodel Authentication Authentication search` retourne vos événements ; ajoutez un test.
5. **Change (bonus).** Pour `aws:cloudtrail` (événements IAM), `azure:activity` (rôles), `gcp:audit` (`SetIamPolicy`) : ajoutez `status` (`success`/`failure`), `object_category`, `command` (= `signature`), puis testez le modèle *Change*.
6. **Cycle de vie.** Incrémentez la version (`1.2.1`), ajoutez une entrée `CHANGELOG`, empaquetez (`tar czf`), décrivez le rollback.
7. **Documentation.** Créez un tableau « champ brut → champ CIM → règle » pour le firewall.

<details><summary>Indice (2)</summary>`index=... | where NOT match(action,"^(allowed|blocked|unknown)$")` ; pour les tags : `index=... NOT tag=network`.</details>
<details><summary>Indice (5)</summary>`EVAL-object_category = "iam"`, `EVAL-command = signature` — **attention** : un EVAL ne peut pas lire un autre EVAL ; `signature` vient d'un FIELDALIAS, c'est donc possible.</details>

## Critères (40 pts)
1: 8 · 2: 8 · 3: 6 · 4: 6 · 6: 6 · 7: 6 · bonus 6.
