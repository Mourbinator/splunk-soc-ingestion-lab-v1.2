# E10 — Projet final : intégrer les journaux web (format « combined »)
**Module :** M10 · **Durée :** 6 h (et plus selon votre rythme) · **Livrable :** un dossier `projet/` autonome

**Données :** `datasets/web-access.log` (1000 lignes). Exemple :
`192.0.2.77 - - [10/Oct/2026:00:00:03 +0000] "GET /login HTTP/1.1" 200 1523 "-" "curl/8.5.0"`

## Exigences
1. **Contrat d'intake** complet (E0 en mieux).
2. **Collecte** : UF dans une app `soc_uf_web` (monitor `/var/log/soc-lab/web`, index `network`, sourcetype `soc:web:access`) + déploiement documenté.
3. **TA `TA-soc-web`** : `props.conf` (découpage, horodatage `%d/%b/%Y:%H:%M:%S %z`, `TRUNCATE`), extractions (`src`, `method`, `uri_path`, `status`, `bytes`, `http_user_agent`), `eventtypes.conf` + `tags.conf` pour le modèle **Web** (`web`), alias CIM (`dest`, `http_method`, `status`).
4. **Enrichissement** : au moins 1 lookup (ex. criticité d'URI : `/admin`, `/login`).
5. **Routage/filtrage** : 1 règle justifiée (ex. `/static/*` vers un index à rétention courte **ou** filtrage), avec mesure d'impact.
6. **Qualité** : 3 contrôles (fraîcheur, dérive de format, taux d'erreurs 5xx).
7. **Tests** : tests Python (regex sur le dataset) + 3 SPL.
8. **Panne provoquée** et **post-mortem** (`docs/POSTMORTEM-TEMPLATE.md`).
9. **Documentation** : README, CHANGELOG, schéma.

## Démarche conseillée
Contrat → schéma → collecte → parsing (sandbox) → normalisation → enrichissement → routage → qualité → tests → panne → doc.

<details><summary>Indice (parsing)</summary>`LINE_BREAKER = ([\r\n]+)`, `TIME_PREFIX = \[`, `TIME_FORMAT = %d/%b/%Y:%H:%M:%S %z`, regex : `^(?<src>\S+)\s+\S+\s+\S+\s+\[[^\]]+\]\s+"(?<http_method>\S+)\s+(?<uri_path>\S+)\s+\S+"\s+(?<status>\d{3})\s+(?<bytes>\d+)\s+"(?<http_referrer>[^"]*)"\s+"(?<http_user_agent>[^"]*)"`.</details>
<details><summary>Indice (CIM Web)</summary>Tag `web` sur un eventtype `sourcetype=soc:web:access` ; champs attendus : `action`, `http_method`, `status`, `uri_path`, `src`, `dest`.</details>

## Barème (100 pts)
| Domaine | Pts |
|---|---:|
| Contrat et architecture | 10 |
| Collecte et déploiement | 10 |
| Parsing (horodatage, découpage, extractions) correct sur les 1000 lignes | 20 |
| Normalisation CIM validée par le modèle Web | 15 |
| Enrichissement | 8 |
| Routage + mesure | 8 |
| Qualité (3 contrôles testés) | 9 |
| Tests automatisés | 8 |
| Panne + post-mortem | 8 |
| Documentation et propreté (pas de secret, versions) | 4 |
Seuils : < 60 à reprendre · 60-79 acquis · 80+ maîtrise.
