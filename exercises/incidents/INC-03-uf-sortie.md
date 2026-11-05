# INC-03 — « Plus aucun événement venant de la VM Ubuntu »
**Couche visée :** transport. **Durée :** 45 min.

## Injection (formateur)
```bash
sudo sed -i 's/10\.50\.0\.10:9997/10.50.0.100:9997/' /opt/splunkforwarder/etc/apps/soc_uf_outputs/default/outputs.conf
sudo /opt/splunkforwarder/bin/splunk restart
python3 generators/write_linux_logs.py --count 50 --rate 0
```
## Symptôme
Plus aucun événement des deux sources de la VM (`linux`, `network`).

## Méthode guidée
1. **Constater** : `index=_internal host=<vm> | stats latest(_time)` → ancien (les UF envoient aussi leurs logs internes).
2. **Réseau** : `nc -vz 10.50.0.10 9997` → OK ; donc le réseau n'est pas en cause.
3. **UF** : `splunk list forward-server` → *Configured but inactive* ; `btool outputs list --debug` → quelle IP ?
4. **Log UF** : `grep TcpOutputProc …/splunkd.log | tail` → échecs de connexion vers `10.50.0.100`.
5. **Correction** : restaurer l'IP ; restart ; attendre la reconnexion.
6. **Preuve de rattrapage** : les 50 lignes sont arrivées (compteur) — expliquez pourquoi il n'y a pas de perte (l'UF a gardé ses données).
7. **Prévention** : déploiement par DS (config centrale) ; alerte Q10.

<details><summary>Indice</summary>`btool` montre l'adresse **effective**, pas celle que vous croyez avoir.</details>

**Livrable :** post-mortem + `btool` avant/après.
## Retour à la normale
`sudo sed -i 's/10\.50\.0\.100:9997/10.50.0.10:9997/' /opt/splunkforwarder/etc/apps/soc_uf_outputs/default/outputs.conf && sudo /opt/splunkforwarder/bin/splunk restart`
