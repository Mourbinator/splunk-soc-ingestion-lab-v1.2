# INC-08 — « Il manque des événements SaaS (et personne ne voit d'erreur) »
**Couche visée :** API. **Durée :** 60 min.

## Injection (formateur)
```bash
python3 collectors/api/mock_api.py --port 8081 --throttle-every 3 --retry-after 1 --verbose &    # API qui limite le débit
python3 collectors/api/poller_naive.py                                                           # le « poller en production »
```
## Symptôme
Le « poller » a fini sans erreur, mais Splunk contient **moins de 500** événements SaaS (`saas-0001…0500`).

## Méthode guidée
1. **Mesurer le manque** : sortie du script (`événements récupérés : N / 500`). Dans Splunk, `| stats dc(event_id)` et lister les **trous** (`saas-NNNN` manquants par plages de 100).
2. **Côté API** : les logs `--verbose` du mock montrent des `429`.
3. **Lire le code** de `poller_naive.py` : que fait-il d'un HTTP 429 ? (il saute la page).
4. **Cause** : pas de gestion de `429`/`Retry-After`, pas de retry, pas de checkpoint.
5. **Correction** : utilisez `poller.py` (dry-run puis réel) → 500/500 ; expliquez `retried` et `http_429` dans les métriques.
6. **Rattrapage** : réinjecter **uniquement** les pages manquantes sans doublon : comment (dédup `event_id`) ?
7. **Prévention** : alerte sur `sent != fetched`, test automatisé du poller, suivi des métriques (Q12).

<details><summary>Indice</summary>Les trous sont des **multiples de 100** : c'est la signature d'une page entière perdue.</details>

**Livrable :** post-mortem + tableau des trous + preuve 500/500.
## Retour à la normale
Arrêtez le mock (`kill %1`) ; videz l'index/état de test (`state/`).
