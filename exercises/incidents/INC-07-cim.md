# INC-07 — « Le modèle Network Traffic est vide » (ou ne montre qu'une partie)
**Couche visée :** normalisation. **Durée :** 45 min. Utilisez `lab_sandbox` et un index inclus dans la configuration CIM.

## Injection (formateur)
```powershell
New-Item -ItemType Directory -Force "$SPLUNK\etc\apps\TA-soc-firewall\local" | Out-Null
"[eventtype=soc_firewall_traffic]`ncommunicate = disabled" | Set-Content "$SPLUNK\etc\apps\TA-soc-firewall\local\tags.conf"
& "$SPLUNK\bin\splunk.exe" restart
```
## Symptôme
`| datamodel Network_Traffic All_Traffic search | search sourcetype=soc:firewall` ne renvoie rien. Les événements existent pourtant.

## Méthode guidée
1. `index=lab_sandbox sourcetype=soc:firewall | stats count by eventtype tag` → présence de `network` mais **pas** `communicate`.
2. `btool tags list --debug | grep -B1 -A2 soc_firewall_traffic` → qui désactive `communicate` ? (`local/tags.conf`).
3. **Cause** : le modèle exige `network` **et** `communicate`.
4. **Correction** : supprimer le fichier fautif ; refresh/restart.
5. **Test de non-régression** : ajoutez un fichier de test `10-tags.spl` dans le dossier `tests/spl/` : `index=... sourcetype=soc:firewall NOT (tag=network tag=communicate) | stats count` doit renvoyer 0.
6. **Prévention** : tests SPL en CI, pas de `local/` dans les TA de production, revue des diffs.

<details><summary>Indice</summary>Affichez la liste des `tag` sur quelques événements et comparez avec la documentation du modèle.</details>

**Livrable :** post-mortem + SPL de test.
## Retour à la normale
`Remove-Item "$SPLUNK\etc\apps\TA-soc-firewall\local\tags.conf"` ; restart.
