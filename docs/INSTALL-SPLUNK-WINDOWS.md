# Installation côté Windows (Splunk Enterprise)

Hypothèse : Splunk Enterprise est **déjà installé** (dossier habituel `C:\Program Files\Splunk`). Ouvrez **PowerShell en administrateur**.
Pour raccourcir les commandes :
```powershell
$SPLUNK = "C:\Program Files\Splunk"          # adaptez si besoin
& "$SPLUNK\bin\splunk.exe" version            # doit afficher la version
```

## Étape 1 — Copier les apps du dépôt
Placez-vous à la racine du dépôt (là où se trouve ce README), puis :
```powershell
$apps = "$SPLUNK\etc\apps"
Copy-Item -Recurse -Force .\splunk-apps\soc_lab_base      $apps
Copy-Item -Recurse -Force .\splunk-apps\soc_lab_quality   $apps
Copy-Item -Recurse -Force .\addons\TA-soc-firewall        $apps
Copy-Item -Recurse -Force .\addons\TA-soc-linux           $apps
Copy-Item -Recurse -Force .\addons\TA-soc-cloud           $apps
Copy-Item -Recurse -Force .\addons\TA-soc-app             $apps
Copy-Item -Recurse -Force .\addons\SA-soc-enrichment      $apps
```
> Pour un exercice de parsing (E4), vous **retirerez temporairement** un TA : gardez vos copies dans le dépôt.

## Étape 2 — Redémarrer et vérifier
```powershell
& "$SPLUNK\bin\splunk.exe" restart
& "$SPLUNK\bin\splunk.exe" btool indexes list network --debug     # l'index doit venir de soc_lab_base
& "$SPLUNK\bin\splunk.exe" btool props list soc:firewall --debug   # doit afficher les lignes de TA-soc-firewall
```
**Résultat attendu** : chaque ligne de `btool` est préfixée par le chemin du fichier source (`...\apps\TA-soc-firewall\default\props.conf`).
Dans Splunk Web : *Settings → Indexes* liste `win_event, linux, network, cloud, saas, security, lab_api, lab_sandbox`.

## Étape 3 — Réception S2S (déjà fournie par `soc_lab_base`)
`soc_lab_base/default/inputs.conf` ouvre `9997`. Contrôle :
```powershell
Get-NetTCPConnection -State Listen -LocalPort 9997,8088
```
Si Splunk ne l'a pas pris en compte : *Settings → Forwarding and receiving → Configure receiving → New Receiving Port → 9997*.

## Étape 4 — Pare-feu Windows (réseau privé du lab uniquement)
```powershell
New-NetFirewallRule -DisplayName "Splunk S2S lab" -Direction Inbound -Protocol TCP -LocalPort 9997,8088 `
  -RemoteAddress 10.50.0.0/24 -Action Allow
# Facultatif (Deployment Server / admin à distance) : 8089
New-NetFirewallRule -DisplayName "Splunk mgmt lab" -Direction Inbound -Protocol TCP -LocalPort 8089 `
  -RemoteAddress 10.50.0.0/24 -Action Allow
```
Ne mettez jamais `-RemoteAddress Any`.

## Étape 5 — Créer le token HEC (ne jamais le mettre dans Git)
1. *Settings → Data inputs → HTTP Event Collector → Global Settings* : **All Tokens = Enabled**, **Enable SSL = coché**, port **8088** → Save.
2. *New Token* : nom `soc-lab-hec`, **ne pas** cocher « Enable indexer acknowledgment » pour l'instant (voir M3).
3. *Input Settings* : sourcetype laissé « Automatic » (le poller le fournit), **Allowed indexes = `saas`, `lab_api`**, index par défaut `lab_api`.
4. Copiez le **Token Value** dans une variable d'environnement (PowerShell : `$env:SPLUNK_HEC_TOKEN="..."`).
5. Test :
```powershell
curl.exe -k https://localhost:8088/services/collector/health
# attendu : {"text":"HEC is healthy","code":17}
```

## Étape 6 — Splunk Common Information Model (pour M5)
Installer l'app **Splunk Common Information Model (CIM)** depuis *Apps → Find More Apps* (compte splunk.com requis).
Puis *Settings → Data models → CIM Setup* (ou « Common Information Model Add-on Builder » selon version) :
pour **Network Traffic** et **Authentication**, ajoutez les index `network` et `linux` à la liste d'index.
(Sans cette étape, vos événements sont bien normalisés mais le modèle de données ne les voit pas.)

## Étape 7 — Collecter des journaux Windows locaux (optionnel)
Sans VM Windows, Splunk peut lire **ses propres** journaux Windows : copiez `configs\uf-apps\soc_uf_windows\default\inputs.conf` dans une app
locale (`...\etc\apps\soc_win_local\local\inputs.conf`) puis redémarrez. Vérifiez ensuite :
```spl
| tstats count where index=win_event by sourcetype source
```

## Problèmes fréquents
| Symptôme | Cause probable | Vérification |
|---|---|---|
| Aucun index nouveau | app mal copiée (dossier imbriqué) | `...\etc\apps\soc_lab_base\default\indexes.conf` doit exister |
| UF ne se connecte pas | pare-feu ou mauvaise IP | `Test-NetConnection 10.50.0.10 -Port 9997` depuis la VM : `nc -vz 10.50.0.10 9997` |
| HEC 403 | token faux/désactivé | `curl.exe -k ... -H "Authorization: Splunk <token>"` |
