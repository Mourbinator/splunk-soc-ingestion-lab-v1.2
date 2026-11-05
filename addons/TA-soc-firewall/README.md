# TA-soc-firewall v1.2

Technical Add-on pédagogique : parsing + normalisation CIM (Network Traffic) du sourcetype `soc:firewall`.

| Fichier | Rôle | Moment d'exécution |
|---|---|---|
| `props.conf` (LINE_BREAKER, TIME_*, TRUNCATE) | découpage et horodatage | **index-time** |
| `props.conf` (REPORT, FIELDALIAS, EVAL) + `transforms.conf` | extraction/normalisation | **search-time** |
| `eventtypes.conf` + `tags.conf` | reconnaissance par le modèle CIM | **search-time** |

Installation : copier le dossier dans `%SPLUNK_HOME%\etc\apps\`, puis `splunk restart`.
Contrôle : `splunk btool props list soc:firewall --debug`.

Corrections de la v1.1 : tags CIM sur *tout* le trafic (pas seulement les refus), `action` normalisée
(`allowed`/`blocked`/`unknown`) avec la valeur brute conservée dans `action_raw`, guillemets correctement retirés,
plus de double extraction (`KV_MODE = none`).
