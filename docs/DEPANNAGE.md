# Aide-mémoire de diagnostic (par couche)

**Règle : avancez de la source vers Splunk, une couche à la fois, et notez une preuve à chaque couche.**

| # | Couche | Question | Commande / recherche |
|---|---|---|---|
| 1 | Source | L'émetteur envoie-t-il ? | `python3 generators/send_syslog.py ... ` (lire le JSON de résumé) |
| 2 | Réseau | Le paquet arrive-t-il ? | `sudo tcpdump -ni any port 5514 -c 5` · `nc -vz <ip> <port>` |
| 3 | Collecteur | Le port écoute-t-il ? | `sudo ss -lntup \| grep 5514` · `sudo journalctl -u syslog-ng -n 50` |
| 4 | Fichier | Le fichier grossit-il ? droits ? | `wc -l fichier` · `ls -l fichier` · `sudo -u splunkfwd head -1 fichier` |
| 5 | Agent | L'UF lit-il et envoie-t-il ? | `splunk list monitor` · `splunk list inputstatus` · `splunk list forward-server` |
| 6 | Agent (log) | Erreurs côté UF ? | `sudo tail -100 /opt/splunkforwarder/var/log/splunk/splunkd.log` |
| 7 | Réception | L'indexeur reçoit-il ? | `index=_internal source=*metrics.log* group=tcpin_connections` |
| 8 | Index | Le bon index existe-t-il ? | `index=_internal "unconfigured/disabled/deleted index"` |
| 9 | Parsing | Horodatage/découpage OK ? | `index=_internal sourcetype=splunkd component=DateParserVerbose` |
| 10 | Config | Quelle config est effective ? | `splunk btool props list <sourcetype> --debug` |
| 11 | Search-time | Champs/tags OK ? | `... \| table _time host sourcetype action action_raw src dest` · `eventtype=*` |
| 12 | Qualité | Complet ? sans doublon ? | `tests/spl/04-completude-sequence.spl` |

## Commandes Splunk utiles
```bash
splunk btool inputs list --debug | less         # configuration effective des inputs
splunk btool props list soc:firewall --debug
splunk btool check                               # syntaxe des .conf
splunk list monitor                              # fichiers surveillés (UF)
splunk list inputstatus                          # état de lecture par fichier (UF)
splunk list forward-server                       # cibles actives/inactives (UF)
splunk restart
```
(Windows : `& "C:\Program Files\Splunk\bin\splunk.exe" <commande>` ; UF Linux : `/opt/splunkforwarder/bin/splunk`.)

## Rafraîchir sans redémarrer ?
- Search-time (extractions, alias, lookups, tags) : `https://localhost:8000/en-US/debug/refresh` ou `| extract reload=T`.
- Index-time (découpage, horodatage, routage) : **redémarrer** Splunk ; et ne s'applique **qu'aux nouvelles données**.

## Repartir d'un index propre (sandbox seulement)
```powershell
& "$SPLUNK\bin\splunk.exe" stop
& "$SPLUNK\bin\splunk.exe" clean eventdata -index lab_sandbox -f
& "$SPLUNK\bin\splunk.exe" start
```
`| delete` ne fait que **masquer** les événements : l'espace disque n'est pas libéré.

## Réingérer un fichier à la demande
```powershell
& "$SPLUNK\bin\splunk.exe" add oneshot "C:\chemin\datasets\firewall.log" -sourcetype soc:firewall -index lab_sandbox
```
(`oneshot` envoie le fichier **une fois** ; recommencez après avoir nettoyé l'index pour éviter les doublons.)
