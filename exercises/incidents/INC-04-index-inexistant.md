# INC-04 — « Les données arrivent… mais `index=network` est vide »
**Couche visée :** routage / index. **Durée :** 45 min.

## Injection (formateur)
Dans `soc_uf_linux/default/inputs.conf` (VM), la stanza firewall passe de `index = network` à `index = netwrok` ; restart UF ; `send_syslog.py --count 100 --tcp`.
```bash
sudo sed -i '0,/index = network/s//index = netwrok/' /opt/splunkforwarder/etc/apps/soc_uf_linux/default/inputs.conf
sudo /opt/splunkforwarder/bin/splunk restart
python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 100 --tcp --rate 0
```
## Symptôme
Fichier collecteur OK, UF « active », mais plus d'événements dans `network`.

## Méthode guidée
1. `| tstats count where index=* earliest=-15m by index` : où vont les événements ? (nulle part ?)
2. Chercher les rejets côté Splunk : `index=_internal sourcetype=splunkd "unconfigured/disabled/deleted index"` (Q13).
3. `rex "index='(?<bad_index>[^']+)'"` → `netwrok`.
4. **Cause** : l'index n'existe pas → événements **supprimés** (pas de « last chance index » configuré).
5. **Correction** : corriger la faute ; restart UF.
6. **Récupération** : les 100 événements sont **perdus** ; rejouez-les (`send_syslog.py`, ou `oneshot` du fichier collecteur dans le bon index). Quels risques de doublons ?
7. **Prévention** : alerte Q13 ; relecture/validation de config avant déploiement ; DS ; `lastChanceIndex` (paramètre à étudier dans la doc).

<details><summary>Indice 1</summary>Splunk journalise chaque événement reçu pour un index inconnu dans `splunkd.log`.</details>

**Livrable :** post-mortem incluant l'analyse de **perte de données** (combien, récupérable ?).
## Retour à la normale
`sudo sed -i 's/index = netwrok/index = network/' …inputs.conf` + restart UF.
