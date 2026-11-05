# Splunk SOC Ingestion Lab v1.2
**Parcours pratique, pas à pas, pour maîtriser les architectures de collecte et de traitement des événements :**
agents, collecteurs, API, Syslog, parsing, normalisation, enrichissement, routage, ingestion et stockage.

Langue : français · Durée : ≈ 67 h · Public : analyste/ingénieur junior qui connaît les bases de Splunk
(rechercher, `stats`, `table`, créer un index) · Cible : Splunk Enterprise déjà installé sous Windows + une VM Ubuntu.

## Ce que vous saurez faire à la fin
1. Concevoir une chaîne de collecte complète et la **documenter** (contrat d'intake, ports, menaces, rollback).
2. Déployer et diagnostiquer des **agents** (Universal Forwarder), des **collecteurs Syslog** (UDP/TCP/TLS) et des **intégrations API/HEC**.
3. Écrire le **parsing** (découpage, horodatage, extractions) et la **normalisation CIM** dans un Technical Add-on versionné.
4. **Enrichir** (lookups : actifs, règles, zones CIDR) et **router/filtrer/masquer** des événements.
5. Comprendre l'**ingestion et le stockage** (pipelines, files d'attente, buckets, rétention, volumétrie).
6. **Mesurer la qualité** (volume, fraîcheur, retard, complétude, doublons, dérive) et résoudre 10 incidents types.

## Comment utiliser ce dépôt (important)
Chaque module a **trois couches** — suivez-les dans cet ordre :

| Couche | Dossier | Ce que c'est |
|---|---|---|
| 1. **Cours guidé** | `modules/` | Notions expliquées simplement + manipulations **pas à pas** avec le résultat attendu |
| 2. **Exercice autonome** | `exercises/` | Un objectif, des étapes, des indices progressifs, des critères de réussite |
| 3. **Corrigé** | `instructor/ANSWER-KEY.md` | Solutions et explications — à ouvrir **après** avoir essayé |

Commencez par `docs/PARCOURS.md` (feuille de route à cocher) puis `docs/GLOSSAIRE.md` si un terme est inconnu.

## Architecture cible
```text
PC Windows — Splunk Enterprise (10.50.0.10, exemple)        indexeur + parsing + search head
  Web 8000 | management 8089 | S2S receiving 9997 | HEC 8088 (HTTPS)
        ▲ S2S (UF)                       ▲ HTTPS (HEC)
        │                                │
VM Ubuntu (10.50.0.40, exemple)
  syslog-ng :5514 udp/tcp ──► /var/log/soc-lab/firewall/firewall.log ──► Universal Forwarder ──► :9997
  generators/ (firewall syslog, SSH, API simulée)   collectors/api/poller.py ──► :8088
        ▲
        └── Syslog UDP/TCP 5514 (émetteurs : generators/send_syslog.py)

VM Windows optionnelle (10.50.0.50) : Universal Forwarder + Windows Event Logs (+ Sysmon facultatif)
```
Le plan IP est un exemple. Ne publiez jamais Splunk ni les ports de collecte sur Internet.

## Parcours et durées
| Module | Notes (cours guidé) | Exercice | Durée |
|---|---|---|---:|
| M0 Architecture, contrat d'intake, menaces | `modules/M0-architecture.md` | E0 | 3 h |
| M1 Agents : Universal Forwarder et S2S | `modules/M1-agents-uf.md` | E1 | 6 h |
| M2 Syslog et collecteurs | `modules/M2-syslog-collecteur.md` | E2 | 7 h |
| M3 API et HEC | `modules/M3-api-hec.md` | E3 | 6 h |
| M4 Parsing : découpage, horodatage, extractions | `modules/M4-parsing.md` | E4 | 8 h |
| M5 Normalisation : TA et CIM | `modules/M5-normalisation-cim.md` | E5 | 8 h |
| M6 Enrichissement : lookups | `modules/M6-enrichissement.md` | E6 | 5 h |
| M7 Routage, filtrage, masquage | `modules/M7-routage.md` | E7 | 5 h |
| M8 Ingestion et stockage | `modules/M8-ingestion-stockage.md` | E8 | 6 h |
| M9 Qualité et supervision | `modules/M9-qualite.md` | E9 | 7 h |
| M10 Incidents et projet final | `modules/M10-incidents-projet.md` | E10 + 10 incidents | 6 h |

## Couverture des compétences
| Compétence | Où la pratiquer |
|---|---|
| Agents | M1/E1 (UF, `outputs.conf`, `inputs.conf`, ACK, Deployment Server), `configs/uf-apps/` |
| Collecteurs | M2/E2 (syslog-ng, rsyslog, rotation, permissions), `collectors/syslog/` |
| API | M3/E3 (poller, pagination, 429, checkpoint, dédup), `collectors/api/` |
| Syslog | M2/E2 (UDP, TCP, TLS, RFC 5424, routage par APP-NAME) |
| Parsing | M4/E4 (`LINE_BREAKER`, `TIME_*`, `TRUNCATE`, REPORT/EXTRACT), `addons/TA-soc-*` |
| Normalisation | M5/E5 (alias, EVAL, eventtypes, tags, CIM), `addons/TA-soc-firewall` |
| Enrichissement | M6/E6 (CSV, CIDR, lookups automatiques), `addons/SA-soc-enrichment` |
| Routage | M2 (collecteur), M7/E7 (index-time : host/sourcetype/index, nullQueue, SEDCMD, `_TCP_ROUTING`) |
| Ingestion | M1, M8/E8 (pipelines, files d'attente, `metrics.log`, backpressure) |
| Stockage | M8/E8 (buckets, `indexes.conf`, rétention, archivage frozen, volumétrie) |
| Qualité | M9/E9 (`splunk-apps/soc_lab_quality`, `tests/spl/`) |

## Démarrage rapide
1. Lire `docs/ARCHITECTURE.md` et `docs/SECURITY.md`.
2. Installer côté Windows : `docs/INSTALL-SPLUNK-WINDOWS.md` ; côté Ubuntu : `docs/INSTALL-UBUNTU.md`.
3. Valider l'installation avec la section « Smoke test » de `tests/ACCEPTANCE.md`.
4. Dérouler `docs/PARCOURS.md` module par module.

## Contrôles automatiques fournis
```bash
python3 scripts/validate_repo.py          # cohérence du dépôt (syntaxe .conf, références, liens, secrets, datasets)
python3 -m unittest discover -s tests -v  # tests du poller et simulation des regex des TA sur les datasets
```
Ces contrôles **ne remplacent pas Splunk** : les regex sont simulées en Python (PCRE ≈ `re`). Les `.conf` et le SPL n'ont pas
été exécutés sur *votre* version de Splunk. Validez toujours avec `btool` et Splunk Web.

## Limites et règles
- Données **synthétiques** (IP RFC 5737, domaines `.invalid`), pas des exports officiels de fournisseurs.
- Aucun binaire/licence Splunk, Windows ou Sysmon n'est fourni.
- Les configurations sont des **modèles à tester** sur votre version (voir `docs/DEPANNAGE.md`).
- Ne commitez **jamais** tokens, clés, mots de passe, données réelles (`.gitignore` aide mais ne protège pas de tout).
