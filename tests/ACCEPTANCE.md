# Recette (acceptance) avec valeurs attendues

Cochez après exécution **et conservez la sortie** comme preuve. Les fenêtres de recherche supposent des événements générés « maintenant » (`earliest=-15m`) sauf mention.

## 0. Contrôles hors Splunk
| # | Commande | Attendu |
|---|---|---|
| 0.1 | `python3 scripts/validate_repo.py` | dernière ligne `OK` |
| 0.2 | `python3 -m unittest discover -s tests -v` | `Ran 19 tests ... OK` |
| 0.3 | `python3 generators/gen_datasets.py --out /tmp/ds && diff -r datasets /tmp/ds` | aucune différence (génération déterministe) |

## 1. Smoke test (état sain — à passer avant chaque incident)
| # | Étape | Commande / recherche | Attendu |
|---|---|---|---|
| 1.1 | Splunk écoute | `Get-NetTCPConnection -State Listen -LocalPort 9997,8088` | 2 lignes |
| 1.2 | Index présents | *Settings → Indexes* | 8 index du lab |
| 1.3 | UF connecté | `splunk list forward-server` (UF) | `Active forwards: <IP>:9997` |
| 1.4 | Collecteur | `sudo ss -lntup \| grep 5514` | udp **et** tcp |
| 1.5 | Firewall UDP 100 | `send_syslog.py --count 100 --rate 50` puis `index=network sourcetype=soc:firewall event_id=fw-<run>-* \| stats dc(event_id)` | **100** |
| 1.6 | Firewall TCP 100 | idem avec `--tcp` | **100** |
| 1.7 | SSH 30 | `write_linux_logs.py --count 30 --rate 0` puis `index=linux sourcetype=linux:auth \| stats count` (15 min) | **30** de plus |
| 1.8 | Routage collecteur | `send_syslog.py --app other-app --count 5` | 5 dans `index=lab_api sourcetype=soc:unrouted` ; 0 dans `soc:firewall` |
| 1.9 | HEC | `hec_send.py --count 3 --insecure` | `200 ... "code":0` + 3 événements `soc:api` |
| 1.10 | API | poller réel (`--reset`) avec mock `--throttle-every 4` | `saas` : `count=500`, `dc(event_id)=500` |

## 2. Données de référence (dans `lab_sandbox`, `earliest=0`)
| Jeu | Chargement | Recherche | Attendu |
|---|---|---|---|
| firewall | `oneshot firewall.log -sourcetype soc:firewall` | `\| stats count` / min-max `_time` | 2000 ; 2026-10-10 00:00:00 → 00:33:19 |
| firewall (CIM) | idem | `stats count by action action_raw` | uniquement `allowed↔allow`, `blocked↔deny/drop` |
| enrichissement | idem | `stats dc(dest_name)` | 8 noms (IP d'actifs) + valeurs vides pour les autres |
| ssh | `oneshot linux-auth.log -sourcetype linux:auth` | `stats count` ; `action=failure ... src=192.0.2.99` | 561 ; ≥ 40 échecs pour 192.0.2.99 |
| multi-lignes | `oneshot app-multiline.log -sourcetype soc:app` | `stats count` | **150** |
| anomalies | `oneshot firewall-anomalies.log -sourcetype soc:firewall` | `stats count` | 14 |
| JSON | `oneshot saas-audit.jsonl -sourcetype soc:saas:audit` | `stats count dc(event_id)` | 500 ; 500 |
| JSON | `aws-cloudtrail.jsonl` / `azure-activity.jsonl` / `gcp-audit.jsonl` / `m365-audit.jsonl` | `stats count` | 300 / 300 / 200 / 300 |

## 3. Qualité (après le smoke test)
| # | Contrôle | Attendu |
|---|---|---|
| 3.1 | Q06 trous de séquence | `missing=0` pour chaque `run` |
| 3.2 | Q05 doublons | aucun `event_id` en double sur les lots live |
| 3.3 | Q03 retard p95 | ≤ 120 s |
| 3.4 | Q02 fraîcheur | tous les sourcetypes actifs `OK` |

## 4. Critères de sortie du lab
- [ ] 0.1, 0.2, 1.x, 2.x, 3.x passés avec preuves
- [ ] 10 incidents traités (au moins 3 post-mortems complets)
- [ ] Projet final noté ≥ 60/100

> Rappel : ces valeurs ont été calculées à partir des datasets du dépôt. Les recherches SPL et le comportement de Splunk n'ont pas été exécutés par l'auteur sur votre version : en cas d'écart, **mesurez et investiguez** (c'est le but de l'exercice).
