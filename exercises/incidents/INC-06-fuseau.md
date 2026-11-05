# INC-06 — « Les connexions SSH sont datées d'hier / décalées de 13 heures »
**Couche visée :** parsing (horodatage). **Durée :** 45 min. Utilisez `lab_sandbox`.

## Injection (formateur)
```powershell
New-Item -ItemType Directory -Force "$SPLUNK\etc\apps\TA-soc-linux\local" | Out-Null
"[linux:auth]`nTZ = Pacific/Auckland" | Set-Content "$SPLUNK\etc\apps\TA-soc-linux\local\props.conf"
& "$SPLUNK\bin\splunk.exe" restart
# Sur la VM : générer des lignes « maintenant » puis (côté Windows) :
& "$SPLUNK\bin\splunk.exe" add oneshot "<chemin>\datasets\linux-auth.log" -sourcetype linux:auth -index lab_sandbox
```
## Symptôme
Les événements sont décalés de ~12-13 h par rapport à l'heure réelle ; les recherches « 15 dernières minutes » ne les voient pas.

## Méthode guidée
1. `index=lab_sandbox sourcetype=linux:auth | eval lag=_indextime-_time | stats avg(lag) min(lag) max(lag)` → `lag` très grand (≈ 46 000 s).
2. Comparez `_raw` (heure du texte) et `_time` : écart **constant**.
3. `btool props list linux:auth --debug | grep -i TZ` → qui impose `Pacific/Auckland` ? (`local/` de TA-soc-linux).
4. **Cause** : `TZ` incorrect → heure du texte interprétée dans le mauvais fuseau.
5. **Correction** : supprimer le `local/props.conf` ; restart ; **réingérer** (les données déjà indexées restent fausses).
6. **Prévention** : documenter le fuseau de chaque source (contrat), NTP, test de latence Q03 (lag négatif/énorme = alerte).

<details><summary>Indice</summary>Un décalage **constant** = fuseau ; un décalage **variable** = autre chose (horloge dérive, retard réel).</details>

**Livrable :** post-mortem + mesure du décalage avant/après.
## Retour à la normale
`Remove-Item -Recurse "$SPLUNK\etc\apps\TA-soc-linux\local"` ; restart ; nettoyez le sandbox (`docs/DEPANNAGE.md`).
