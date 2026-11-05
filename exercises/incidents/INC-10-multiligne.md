# INC-10 — « Les erreurs applicatives sont illisibles : une ligne par événement »
**Couche visée :** parsing (découpage). **Durée :** 60 min. Utilisez `lab_sandbox`.

## Injection (formateur)
Variante A (fragmentation) :
```powershell
New-Item -ItemType Directory -Force "$SPLUNK\etc\apps\TA-soc-app\local" | Out-Null
"[soc:app]`nSHOULD_LINEMERGE = false`nLINE_BREAKER = ([\r\n]+)" | Set-Content "$SPLUNK\etc\apps\TA-soc-app\local\props.conf"
& "$SPLUNK\bin\splunk.exe" restart
& "$SPLUNK\bin\splunk.exe" add oneshot "<chemin>\datasets\app-multiline.log" -sourcetype soc:app -index lab_sandbox
```
Variante B (fusion) : même fichier avec `LINE_BREAKER = ([\r\n]+)(?=NEVER_MATCHES)`.
## Symptôme
A : 282 « événements » dont des lignes `\tat com.lab…` isolées. B : quelques événements gigantesques.

## Méthode guidée
1. `index=lab_sandbox sourcetype=soc:app | stats count` : 282 (A) au lieu de 150 ; en B : très peu.
2. `| search "at com.lab"` : des lignes orphelines (A).
3. `btool props list soc:app --debug` : quel fichier impose `LINE_BREAKER` ? (`local/`).
4. **Cause A** : chaque ligne est un événement. **Cause B** : le délimiteur ne correspond jamais, l'événement ne se termine qu'à `TRUNCATE`.
5. **Correction** : supprimer le `local/props.conf` ; restart ; **vider le sandbox** ; réingérer → 150.
6. **Impact analytique** : pourquoi un compteur d'erreurs `ERROR` est-il faux en A ? (les traces sont comptées à part ; `exception_class` perdue).
7. **Prévention** : test de comptage (150 attendus) dans la recette du TA ; `TRUNCATE` raisonnable.

<details><summary>Indice</summary>Un événement doit commencer **là où** une ligne commence par un horodatage ; tout le reste lui appartient.</details>

**Livrable :** post-mortem + comptes A/B/normal.
## Retour à la normale
`Remove-Item -Recurse "$SPLUNK\etc\apps\TA-soc-app\local"` ; restart ; nettoyer le sandbox.
