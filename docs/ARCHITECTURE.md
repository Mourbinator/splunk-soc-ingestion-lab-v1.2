# Architecture de collecte

## Le chemin d'un événement (vocabulaire commun à tout le lab)
```text
 SOURCE ─► COLLECTE ─► TRANSPORT ─► PARSING ─► (ENRICHISSEMENT) ─► ROUTAGE ─► INDEXATION ─► STOCKAGE ─► RECHERCHE
 firewall   agent UF     S2S/HTTP   découpage   lookups             index,      écriture     buckets     SPL, CIM,
 app, OS    syslog-ng    syslog     horodatage  (search-time)       sourcetype  sur disque   hot→frozen  alertes
 API SaaS   poller       TCP/UDP    champs                          host,
                                                                    filtrage
```
| Étape | Question à se poser | Où dans ce lab |
|---|---|---|
| Source | Qui génère ? quel format ? quelle horloge ? | `datasets/`, `generators/` |
| Collecte | Agent, collecteur ou API ? qui garde l'état (checkpoint) ? | `configs/uf-apps/`, `collectors/` |
| Transport | Perte possible ? chiffré ? accusé de réception ? | UDP vs TCP vs S2S+ACK vs HTTPS |
| Parsing | Où découpe-t-on les événements ? d'où vient `_time` ? | `addons/TA-soc-*` (`props.conf`) |
| Enrichissement | Quel contexte ajouter (actif, zone, règle) ? | `addons/SA-soc-enrichment` |
| Routage | Vers quel index/sourcetype/host ? que filtre-t-on ? | M7 |
| Indexation/Stockage | Quelle rétention ? quelle taille ? | `splunk-apps/soc_lab_base/default/indexes.conf` |

## Flux du lab
```text
Fichiers Linux simulés ─► UF ─── S2S :9997 (ACK) ────────────────────────────┐
Windows Event Logs ────► UF ─── S2S :9997 (ACK) ────────────────────────────┤
Firewall ─► syslog-ng :5514 ─► firewall.log ─► UF ─── S2S :9997 ─────────────┤─► Splunk (Windows)
API SaaS ─► poller (checkpoint, retry) ─── HTTPS HEC :8088 ─────────────────┘
```
## Rôles
- **UF (Universal Forwarder)** : léger, **ne parse pas** (sauf données structurées), lit des fichiers/journaux Windows, garde un checkpoint, envoie en S2S avec ACK.
- **syslog-ng / rsyslog** : reçoit le Syslog (UDP/TCP), **tamponne**, route par APP-NAME, écrit des fichiers qui seront lus par l'UF. Un UF ne sait pas « écouter » proprement le Syslog en production : on met un collecteur devant.
- **HEC (HTTP Event Collector)** : endpoint HTTPS de Splunk (token) pour applications et connecteurs API.
- **Poller API** : programme qui interroge une API (pagination, quotas), garde un checkpoint et pousse vers HEC.
- **Heavy Forwarder (optionnel)** : Splunk complet qui parse/route avant l'indexeur ; seulement si un besoin réel le justifie.
- **Indexeur** : parse (si personne avant), route, écrit sur disque. Ici : le même Splunk que le search head.
- **TA / SA** : paquets de configuration (parsing, normalisation CIM, enrichissement).

## Règles d'or
1. **Un seul collecteur par port** et **une seule collecte par fichier** (pas d'UF *et* d'un autre agent sur le même fichier).
2. Le **sourcetype reflète le format**, pas seulement le produit.
3. Un réglage d'**index-time** (découpage, horodatage, routage) doit exister sur le **premier composant qui parse** ; un réglage de **search-time** (extractions, alias, lookups, tags) sur le search head.
4. **Mesurez avant de corriger** : compteurs source / collecteur / Splunk sur la même fenêtre.
5. Ajoutez un Heavy Forwarder **uniquement** pour une exigence réelle (routage, API, connectivité).

## Index du lab (8)
| Index | Usage |
|---|---|
| `win_event` | Windows Security/System/Application |
| `linux` | SSH et journaux Linux |
| `network` | firewall, web |
| `cloud` | AWS, Azure, GCP |
| `saas` | M365 et API SaaS |
| `security` | Sysmon, événements sensibles routés (M7) |
| `lab_api` | HEC de test, métriques du poller, syslog non routé, logs applicatifs |
| `lab_sandbox` | bac à sable jetable pour les exercices de parsing |

Le catalogue des sourcetypes est dans `docs/SOURCETYPES.md`.
