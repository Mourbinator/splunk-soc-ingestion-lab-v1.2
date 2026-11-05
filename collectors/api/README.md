# Collecteur API → HEC

| Fichier | Rôle |
|---|---|
| `mock_api.py` | API SaaS simulée : pagination `nextLink`, clé Bearer, 429 + `Retry-After`, 503 |
| `poller.py` | Poller de référence : checkpoint atomique, retry/backoff + jitter, dédup, métriques, HEC |
| `poller_naive.py` | Poller **volontairement mauvais** pour l'incident 08 |
| `config.example.env` | Modèle de variables d'environnement (copier en `.env`, ignoré par Git) |

Démarrage sans Splunk (test hors ligne) :
```bash
python3 collectors/api/mock_api.py --port 8081 --throttle-every 4 --retry-after 1 &
python3 collectors/api/poller.py --dry-run --reset
```
Le guide pas à pas est dans `modules/M3-api-hec.md`.
