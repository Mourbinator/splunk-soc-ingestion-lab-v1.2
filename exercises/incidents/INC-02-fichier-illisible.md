# INC-02 — « L'UF ne remonte plus rien du firewall »
**Couche visée :** fichier / droits. **Durée :** 45 min. **Pré-requis :** chaîne firewall saine.

## Injection (formateur)
```bash
sudo chown root:root /var/log/soc-lab/firewall/firewall.log
sudo chmod 600 /var/log/soc-lab/firewall/firewall.log
python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 100 --tcp
```
## Symptôme
Le fichier **grossit** (le collecteur écrit), mais Splunk ne reçoit plus rien.

## Méthode guidée
1. **Couches 1-3 OK ?** collecteur (fichier qui grossit : oui). Donc le problème est **après** le fichier.
2. **UF** : `splunk list inputstatus` (état du fichier) ; `tail -100 /opt/splunkforwarder/var/log/splunk/splunkd.log` — cherchez « permission » (le libellé exact varie selon la version).
3. **Preuve** : `sudo -u splunkfwd head -1 /var/log/soc-lab/firewall/firewall.log` → *Permission denied*.
4. **Correction** : `sudo chgrp adm … && sudo chmod 640 …` ; vérifiez le groupe de l'UF (`id splunkfwd`).
5. **Prouver le rattrapage** : les 100 lignes apparaissent-elles ? (l'UF reprend là où il en était) — comptez avec `run_id`.
6. **Prévention** : `create 0640 root adm` dans logrotate ; alerte Q10 (UF silencieux) ; test de lecture dans le runbook.

<details><summary>Indice 1</summary>Comparez qui **écrit** (root) et qui **lit** (utilisateur de l'UF).</details>
<details><summary>Indice 2</summary>`ls -l` + `id splunkfwd` + `sudo -u splunkfwd`.</details>

**Livrable :** post-mortem avec les 2 preuves (côté UF, côté fichier).
## Retour à la normale
`sudo chgrp adm /var/log/soc-lab/firewall/firewall.log && sudo chmod 640 /var/log/soc-lab/firewall/firewall.log`
