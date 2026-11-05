# M3 — API et HEC (≈ 6 h)

## 🎯 Objectifs
Envoyer des événements à Splunk via **HEC**, écrire/exploiter un **poller** d'API (pagination, quota, reprise, déduplication), lire les codes d'erreur HEC, gérer les secrets.
**Prérequis :** M1, token HEC créé (`docs/INSTALL-SPLUNK-WINDOWS.md` étape 5). **Exercice :** `exercises/E3-api-hec.md`.

## 🧠 Notions
- **HEC** : endpoint HTTPS de Splunk (`:8088`) protégé par un **token** (`Authorization: Splunk <token>`).
  - `/services/collector/event` : événements **JSON** avec métadonnées (`time`, `host`, `source`, `sourcetype`, `index`, `event`). Le `time` fourni est utilisé tel quel (les règles `TIME_*` ne s'appliquent pas).
  - `/services/collector/raw` : texte brut (le parsing `props.conf` s'applique).
  - `/services/collector/health` : test de santé.
- **Poller** : c'est *vous* qui interrogez l'API à intervalle régulier. Trois problèmes à résoudre : **pagination** (suivre `nextLink`), **quotas** (HTTP 429 + `Retry-After`), **reprise** (checkpoint) sans **doublon** (déduplication par identifiant unique).
- **Garanties de livraison** : *au plus une fois* (peut perdre), *au moins une fois* (peut dupliquer), *exactement une fois* (idéal). Le poller du lab = **au moins une fois + déduplication** ≈ « effectivement une fois » :
  le checkpoint n'avance **qu'après** un envoi réussi.
- **Backoff exponentiel avec jitter** : attendre `1, 2, 4, 8… s` (± aléa) entre deux essais pour ne pas marteler un service en difficulté. Si l'API dit `Retry-After: 2`, on obéit.

### Codes de réponse HEC (à vérifier dans la doc de votre version)
| HTTP | `code` | Sens | Réessayer ? |
|---|---|---|---|
| 200 | 0 | Succès | — |
| 400 | 6 | Format de données invalide | non (corriger) |
| 400 | 7 | Index incorrect/non autorisé pour ce token | non |
| 400 | 5 / 12 / 13 | Pas de données / champ `event` manquant ou vide | non |
| 401 | 2 / 3 | Token absent / autorisation invalide | non |
| 403 | 1 / 4 | Token désactivé / invalide | non |
| 503 | 9 | Serveur occupé | **oui**, avec backoff |

## 🛠️ Pas à pas
### Étape 1 — Variables d'environnement (jamais dans Git)
Linux : `export SPLUNK_HEC_URL=https://10.50.0.10:8088 SPLUNK_HEC_TOKEN='<votre token>' HEC_INSECURE=1`
PowerShell : `$env:SPLUNK_HEC_URL="https://localhost:8088"; $env:SPLUNK_HEC_TOKEN="<votre token>"`
(`HEC_INSECURE=1` : le certificat HEC par défaut est auto-signé ; **toléré en lab seulement**.)

### Étape 2 — Test de santé puis premier événement
```bash
curl -k "$SPLUNK_HEC_URL/services/collector/health"
curl -k "$SPLUNK_HEC_URL/services/collector/event" -H "Authorization: Splunk $SPLUNK_HEC_TOKEN" \
     -d '{"event":"hello hec","sourcetype":"soc:api","index":"lab_api"}'
# attendu : {"text":"Success","code":0}
```
Dans Splunk : `index=lab_api sourcetype=soc:api | table _time host source sourcetype _raw`.
✅ Un événement `hello hec`. Notez le `source` (= `http:<nom du token>`).

### Étape 3 — Provoquer les erreurs pour les reconnaître
| Essai | Modification | Résultat attendu |
|---|---|---|
| Mauvais token | `Splunk mauvais` | HTTP 403, `Invalid token` |
| Pas d'en-tête | retirer `-H` | HTTP 401, `Token is required` |
| Index interdit | `"index":"main"` | HTTP 400, `Incorrect index` |
| JSON cassé | enlever `}` | HTTP 400, `Invalid data format` |
Remplissez la colonne « Résultat observé » dans vos notes : c'est votre tableau de diagnostic.

### Étape 4 — Le script de smoke test
```bash
python3 generators/hec_send.py --count 3 --index lab_api --insecure
```
✅ `200 {"text":"Success","code":0}`. Puis `index=lab_api sourcetype=soc:api | stats count`.

### Étape 5 — Démarrer l'API simulée avec limitation de débit
Terminal A :
```bash
python3 collectors/api/mock_api.py --port 8081 --throttle-every 4 --retry-after 2 --verbose
```
Elle sert 500 événements (`datasets/saas-audit.jsonl`), 100 par page, et répond **429** toutes les 4 requêtes.
Terminal B : `curl -s -H "Authorization: Bearer lab-mock-key" "http://127.0.0.1:8081/events?cursor=0&limit=2"`
✅ JSON avec `items`, `nextLink`, `resumeLink`.

### Étape 6 — Poller **sans** Splunk (dry-run)
```bash
python3 collectors/api/poller.py --dry-run --reset
```
✅ Sortie (adaptée) :
`{"pages": 5, "fetched": 500, "sent": 500, "duplicates_skipped": 0, "retried": 1, "http_429": 1, ...}`
Dans stderr : une ligne `[retry 1/6] ... HTTP 429 -> attente 2.xx s` (le poller **a obéi** au `Retry-After`).

### Étape 7 — Poller réel vers HEC
```bash
python3 collectors/api/poller.py --insecure --reset
```
Dans Splunk :
```spl
index=saas sourcetype=soc:saas:audit | stats count dc(event_id)
index=lab_api sourcetype=soc:poller:metrics | table _time fetched sent retried http_429
```
✅ `count = 500`, `dc = 500`, et une ligne de métriques.

### Étape 8 — Prouver le checkpoint (reprise)
```bash
python3 collectors/api/poller.py --insecure --reset --max-pages 2    # envoie 200 événements puis s'arrête
cat state/checkpoint.json | head -c 300; echo                          # "next": ".../events?cursor=200..."
python3 collectors/api/poller.py --insecure                            # reprend et envoie les 300 restants
```
⚠️ Utilisez un **index vide** (ou nettoyez) avant : sinon vous comptez des anciens événements. ✅ Total 500, aucun doublon.

### Étape 9 — Prouver la déduplication
1. Éditez `state/checkpoint.json` : mettez `"next": null` (on « perd » la position, mais on garde `seen_ids`).
2. Relancez le poller : `{"fetched": 500, "sent": 0, "duplicates_skipped": 500}` → rien n'est réenvoyé.
👉 C'est la protection contre le cas « le poller a planté **après** l'envoi mais **avant** l'écriture du checkpoint ».

### Étape 10 — Comparer avec le poller naïf
```bash
python3 collectors/api/poller_naive.py     # événements récupérés : < 500 (pages perdues sur 429)
```
Listez 4 défauts de `poller_naive.py` (voir incident 08).

### Étape 11 — Lire le code du poller
Dans `collectors/api/poller.py`, repérez : `with_retry` (backoff + jitter), `fetch_page` (429/5xx = réessayable ; 401/403 = fatal), `send_hec` (400 = **fatal et le checkpoint n'avance pas**), `save_checkpoint` (écriture atomique `os.replace`), `run` (ordre : *récupérer → dédupliquer → envoyer → checkpoint*).

### Étape 12 — Hygiène des secrets
- Le token n'est **que** dans l'environnement ; `.gitignore` exclut `.env`, `*.token`.
- Test : `git grep -n "SPLUNK_HEC_TOKEN=" -- . ':!collectors/api/config.example.env'` ne doit rien montrer de réel.
- En cas de fuite : **révoquer** le token (Settings → HEC → Delete/Disable) puis en créer un autre.

## ⚠️ Pièges
- HEC `/event` : un `time` absent = heure de réception ; mal formaté = événement daté 1970 ou ignoré.
- `index` non autorisé pour le token = rejet **du lot entier**.
- Certificats : `--insecure` partout « parce que ça marche » = habitude dangereuse.
- Pas de dédup = doublons à chaque reprise ; checkpoint écrit avant l'envoi = **pertes** à chaque plantage.
- Ignorer `Retry-After` = être banni par l'API.

## 📝 Auto-évaluation
1. `/event` ou `/raw` : lequel applique `props.conf` ? 2. Pourquoi le checkpoint est-il écrit **après** l'envoi ?
3. Pourquoi 400 est-il « fatal » et 503 « réessayable » ? 4. Que garantit l'écriture atomique du checkpoint ?
