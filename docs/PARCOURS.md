# Parcours — feuille de route à cocher

Conseil : un module = cours guidé (`modules/`) → exercice (`exercises/`) → comparaison avec le corrigé. Gardez un dossier
`preuves/` (captures, sorties de commandes, requêtes SPL) : chaque exercice demande des **preuves**, pas seulement un « ça marche ».

## Avant de commencer
- [ ] J'ai lu `README.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`
- [ ] Splunk Enterprise Windows installé et accessible (`http://localhost:8000`) — `docs/INSTALL-SPLUNK-WINDOWS.md`
- [ ] VM Ubuntu prête, en UTC, avec syslog-ng et l'Universal Forwarder — `docs/INSTALL-UBUNTU.md`
- [ ] Le « Smoke test » de `tests/ACCEPTANCE.md` est vert
- [ ] Je sais lancer `python3 scripts/validate_repo.py` et `python3 -m unittest discover -s tests`

## Progression
| ✔ | Module | Cours | Exercice | Preuve attendue |
|---|---|---|---|---|
| ☐ | M0 | `modules/M0-architecture.md` | E0 | diagramme + contrat d'intake complété + table de menaces |
| ☐ | M1 | `modules/M1-agents-uf.md` | E1 | événements `linux:auth` visibles + diagnostic d'une panne UF |
| ☐ | M2 | `modules/M2-syslog-collecteur.md` | E2 | tableau généré/reçu/indexé (écart expliqué) |
| ☐ | M3 | `modules/M3-api-hec.md` | E3 | 500 événements SaaS indexés malgré les 429, checkpoint prouvé |
| ☐ | M4 | `modules/M4-parsing.md` | E4 | `_time` correct, 150 événements multi-lignes, table des anomalies |
| ☐ | M5 | `modules/M5-normalisation-cim.md` | E5 | trafic reconnu par `Network_Traffic`, CHANGELOG du TA |
| ☐ | M6 | `modules/M6-enrichissement.md` | E6 | champs `dest_name`, `src_zone`… présents, lookup versionné |
| ☐ | M7 | `modules/M7-routage.md` | E7 | host/sourcetype/index réécrits, bruit filtré, mots de passe masqués |
| ☐ | M8 | `modules/M8-ingestion-stockage.md` | E8 | buckets inspectés, rétention démontrée, zéro perte après coupure |
| ☐ | M9 | `modules/M9-qualite.md` | E9 | 8 contrôles de qualité + 1 alerte testée |
| ☐ | M10 | `modules/M10-incidents-projet.md` | E10 + incidents | 3 post-mortems + projet final présenté |

## Rythme conseillé (≈ 67 h)
Semaine 1 : M0–M2 · Semaine 2 : M3–M4 · Semaine 3 : M5–M7 · Semaine 4 : M8–M10.

## Auto-évaluation finale
Cochez seulement ce que vous savez refaire **sans notes** :
- [ ] Dessiner la chaîne source → stockage d'une source inconnue et nommer le composant qui parse
- [ ] Dire pour chaque réglage s'il agit à l'**index-time** ou au **search-time**
- [ ] Prouver qu'aucun événement n'est perdu (compteurs source / collecteur / Splunk)
- [ ] Diagnostiquer une panne par couches en moins de 20 minutes avec des preuves
- [ ] Modifier un TA sans casser l'existant (tests, version, rollback)
