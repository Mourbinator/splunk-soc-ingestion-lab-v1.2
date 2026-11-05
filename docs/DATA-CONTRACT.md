# Contrat d'intake — firewall synthétique

Un **contrat d'intake** est l'accord écrit entre l'équipe qui produit les logs et l'équipe qui les collecte. Sans lui, personne
ne sait si « ça marche » (et personne ne sait qui appeler quand ça casse).

| Élément | Contrat |
|---|---|
| Propriétaire (source) | équipe Réseau (fictive) — contact : `reseau@example.invalid` |
| Propriétaire (collecte) | équipe SOC Ingestion |
| Sourcetype / Index | `soc:firewall` / `network` |
| Transport | Syslog RFC 5424, UDP/TCP 5514 → syslog-ng → fichier → UF → S2S |
| Fréquence / volume | 20 événements/s en pic lab (≈ 190 octets/événement ≈ 330 Mo/jour au pic soutenu) |
| Horodatage | `event_time` ISO 8601 avec fuseau (`2026-10-10T00:00:01+0000`) ; source de temps : NTP du firewall |
| Champs obligatoires | `event_id`, `event_time`, `src_ip`, `dest_ip`, `src_port`, `dest_port`, `action`, `protocol`, `rule_id` |
| Champs optionnels | `bytes`, `app` (peut contenir des espaces → entre guillemets) |
| Valeurs de `action` (brut) | `allow`, `deny`, `drop` ; normalisées CIM : `allowed`, `blocked` ; autre → `unknown` |
| `event_id` | unique ; format `fw-<lot>-<séquence 6 chiffres>` (sert à détecter pertes et doublons) |
| Fraîcheur (SLO) | 95 % des événements visibles dans Splunk en moins de **120 s** |
| Exhaustivité (SLO) | 100 % des événements envoyés en TCP ; UDP : perte tolérée < 0,1 % hors saturation |
| Retry | UF : `useACK=true` ; syslog TCP : l'émetteur doit rejouer ; poller API : backoff exponentiel |
| Confidentialité | données synthétiques, aucune donnée client |
| Tests | `tests/ACCEPTANCE.md`, `tests/spl/*.spl`, `tests/test_ta_regex.py` |
| Runbook | `docs/DEPANNAGE.md` + `exercises/incidents/` |
| Rollback | retirer l'app TA (ou revenir à la version précédente) + `splunk restart` ; les données déjà indexées restent |

Un intake est **incomplet** sans : propriétaire, fréquence, volume, stratégie de retry, champs obligatoires, source de temps,
index/sourcetype, tests, runbook et rollback.
