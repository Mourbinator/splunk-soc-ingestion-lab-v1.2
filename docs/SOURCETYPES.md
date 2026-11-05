# Catalogue des sourcetypes

| Sourcetype | Index | Origine | TA | Notes |
|---|---|---|---|---|
| `soc:firewall` | `network` | syslog-ng → fichier → UF ; `send_syslog.py` | `TA-soc-firewall` | CIM Network Traffic |
| `linux:auth` | `linux` | UF (fichier simulé ou `/var/log/auth.log`) | `TA-soc-linux` | CIM Authentication |
| `linux:syslog` | `linux` | UF `/var/log/syslog` (désactivé) | — | pas de TA dans le lab |
| `soc:unrouted` | `lab_api` | syslog-ng (APP-NAME inconnu) | — | preuve que rien ne se perd silencieusement |
| `soc:app` | `lab_api` | UF (journal multi-lignes) | `TA-soc-app` | événements avec stack traces |
| `soc:saas:audit` | `saas` | poller API → HEC | `TA-soc-cloud` | `event_id` unique |
| `soc:poller:metrics` | `lab_api` | poller API → HEC | — | compteurs fetched/sent/retried |
| `soc:api` | `lab_api` | HEC (smoke tests) | — | |
| `aws:cloudtrail` | `cloud` | dataset JSONL | `TA-soc-cloud` | synthétique |
| `azure:activity` | `cloud` | dataset JSONL | `TA-soc-cloud` | synthétique |
| `gcp:audit` | `cloud` | dataset JSONL | `TA-soc-cloud` | synthétique |
| `m365:audit` | `saas` | dataset JSONL | `TA-soc-cloud` | synthétique |
| `soc:web:access` | `network` | projet final (E10) | à écrire par l'apprenant | format « combined » |
| Windows Event Log | `win_event` | UF Windows | — | **vérifier** le sourcetype obtenu (voir ci-dessous) |
| Sysmon | `security` | UF Windows (désactivé) | — | XML, optionnel |

### Windows : ne présumez pas du sourcetype
Selon la version de Splunk, la valeur de `renderXml` et la présence du Splunk Add-on for Microsoft Windows, le sourcetype obtenu
peut être `WinEventLog`, `WinEventLog:Security` ou `XmlWinEventLog`. Vérifiez toujours :
```spl
| tstats count where index=win_event by sourcetype source
```
