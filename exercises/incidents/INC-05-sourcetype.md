# INC-05 — « Les champs `src`, `dest`, `action` n'existent plus »
**Couche visée :** métadonnées (sourcetype). **Durée :** 45 min.

## Injection (formateur)
Éditez `/opt/splunkforwarder/etc/apps/soc_uf_linux/default/inputs.conf` (`sudo nano`), supprimez la ligne `sourcetype = soc:firewall` de la stanza `[monitor:///var/log/soc-lab/firewall]`, puis :
```bash
sudo /opt/splunkforwarder/bin/splunk restart
python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 50 --tcp --rate 0
```
## Symptôme
Des événements arrivent mais les détections/tableaux basés sur `sourcetype=soc:firewall` sont vides.

## Méthode guidée
1. `| tstats count where index=network earliest=-15m by sourcetype source` → un sourcetype inattendu.
2. `btool inputs list --debug` sur l'UF : la stanza n'a plus de `sourcetype`.
3. **Impact** : TA non appliqué (pas de TIME_PREFIX, pas d'alias CIM, pas de tags).
4. **Correction** : restaurer la ligne ; restart UF.
5. **Les 50 événements déjà indexés** gardent le mauvais sourcetype : proposez 2 stratégies (réingestion dans un index sandbox ; règle de réécriture `soc_fw_sourcetype` M7-B2 à titre transitoire) et leurs risques.
6. **Prévention** : test de conformité `sourcetype` attendu par index (SPL), revue de config, DS.

<details><summary>Indice</summary>Sans `sourcetype`, Splunk en choisit un lui-même (souvent à partir du nom de fichier).</details>

**Livrable :** post-mortem + comparaison avant/après des champs.
## Retour à la normale
Remettez `sourcetype = soc:firewall` sous `index = network` dans la stanza firewall ; restart UF.
