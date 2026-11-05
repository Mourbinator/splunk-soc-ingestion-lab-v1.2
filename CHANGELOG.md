# Changelog

## 1.2.0
### Corrigé
- Générateurs : les sauts de ligne étaient écrits `\\n` (antislash + n) au lieu d'un vrai retour à la ligne ; `send_syslog.py` produisait en plus un message RFC 5424 invalide (champ STRUCTURED-DATA manquant).
- Chaîne firewall cassée : l'UF ne lisait jamais le fichier écrit par syslog-ng (inputs ajoutés).
- TA firewall : tags CIM seulement sur les refus → maintenant sur tout le trafic ; `action` normalisée (valeur brute dans `action_raw`) ; guillemets retirés ; double extraction supprimée (`KV_MODE = none`).
- `compressed = true` retiré des `outputs.conf` (réglage à ne faire que des deux côtés) ; sourcetypes Windows : vérification explicite demandée.
- Validateur : ne testait que 9 fichiers ; il contrôle maintenant `.conf`, références, liens, secrets et datasets.
### Ajouté
- **Cours guidé** par module (`modules/M0` … `M10`), exercices détaillés E0–E10, 10 incidents avec injection de panne.
- Nouveaux sujets : **enrichissement** (lookups CSV/CIDR), **routage** (syslog-ng, index-time, nullQueue, SEDCMD, `_TCP_ROUTING`), **ingestion/stockage** (files d'attente, buckets, rétention, frozen), **supervision qualité** (14 recherches).
- Collecteur syslog : TCP + UDP, routage par APP-NAME, TLS (exemple), rsyslog (alternative), logrotate.
- API : `mock_api.py` (pagination, 401, 429, 503), `poller.py` de référence (checkpoint atomique, backoff, dédup, métriques), `poller_naive.py` (incident).
- TA : `TA-soc-linux`, `TA-soc-cloud` (AWS/Azure/GCP/M365/SaaS), `TA-soc-app` (multi-lignes), `SA-soc-enrichment`.
- Apps Splunk : `soc_lab_base` (index + réception + HEC), `soc_lab_quality` (recherches enregistrées désactivées).
- Apps UF prêtes à déployer + exemple Deployment Server et Heavy Forwarder.
- Datasets : 2000 événements firewall + 14 anomalies, 561 lignes SSH, 150 événements multi-lignes, 5 jeux JSON (200–500 lignes), logs web (projet).
- Tests Python (poller, regex des TA) et `tests/ACCEPTANCE.md` avec valeurs attendues chiffrées.
## 1.1.0
- Lab adapté à Splunk Enterprise sous Windows ; collecte UF/Syslog/HEC, TA firewall, datasets synthétiques, exercices et corrigés.
