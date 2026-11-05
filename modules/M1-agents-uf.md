# M1 — Agents : Universal Forwarder et S2S (≈ 6 h)

## 🎯 Objectifs
Installer et configurer un UF, comprendre `inputs.conf`/`outputs.conf`, prouver qu'une donnée traverse la chaîne, diagnostiquer un UF muet, gérer les UF à grande échelle (Deployment Server).
**Prérequis :** M0, `docs/INSTALL-UBUNTU.md` terminé. **Exercice :** `exercises/E1-uf.md`.

## 🧠 Notions
- **UF** : programme léger. Il **ne parse pas** (pas de `LINE_BREAKER` côté UF pour du texte brut) : il découpe en blocs, ajoute `host/source/sourcetype/index` et envoie.
- **inputs.conf** : *quoi lire*. `[monitor:///chemin]` suit un fichier/dossier. Réglages clés : `index`, `sourcetype`, `whitelist`/`blacklist` (regex), `disabled`, `ignoreOlderThan`.
- **outputs.conf** : *où envoyer*. `[tcpout:groupe] server = ip:9997`, `useACK = true`.
- **Fishbucket** : base interne qui retient « jusqu'où » chaque fichier a été lu (via un CRC des premiers octets). Redémarrer l'UF **ne ré-envoie pas** ce qui est déjà lu.
- **S2S + ACK** : l'UF conserve les données en mémoire/disque tant que l'indexeur n'a pas confirmé l'écriture → pas de perte lors d'une coupure.
- **Précédence des fichiers de config** : `system/local` > `apps/*/local` > `apps/*/default` > `system/default`. Utilisez `btool` pour savoir **laquelle gagne**.
- **App de configuration** : on ne met pas ses réglages dans `system/local` mais dans une **app** (`soc_uf_outputs`, `soc_uf_linux`) → déployable, versionnable.

## 🛠️ Pas à pas
### Étape 1 — Vérifier que Splunk écoute (Windows)
```powershell
Get-NetTCPConnection -State Listen -LocalPort 9997
```
✅ Une ligne `LocalPort 9997 ... Listen`. Sinon revoyez `INSTALL-SPLUNK-WINDOWS.md` étape 3.

### Étape 2 — Vérifier la connectivité depuis l'UF (Ubuntu)
```bash
nc -vz 10.50.0.10 9997        # attendu : "succeeded!"
```
❌ « Connection timed out » = pare-feu/route ; « refused » = Splunk n'écoute pas.

### Étape 3 — Lire l'app de sortie
```bash
cat /opt/splunkforwarder/etc/apps/soc_uf_outputs/default/outputs.conf
sudo /opt/splunkforwarder/bin/splunk btool outputs list --debug | grep -E "server|useACK"
sudo /opt/splunkforwarder/bin/splunk list forward-server
```
✅ `Active forwards: 10.50.0.10:9997`. (Si c'est *Configured but inactive*, la connexion échoue → étape 2.)

### Étape 4 — Lire l'app d'entrées
```bash
sudo /opt/splunkforwarder/bin/splunk btool inputs list --debug | grep -B1 -A6 "generated"
sudo /opt/splunkforwarder/bin/splunk list monitor
```
Notez dans la sortie : `index = linux`, `sourcetype = linux:auth`. Chaque ligne indique le fichier d'origine → c'est la **preuve** de l'app qui gagne.

### Étape 5 — Générer des événements et les retrouver
```bash
python3 generators/write_linux_logs.py --count 30 --rate 0
```
Dans Splunk (fenêtre « 15 dernières minutes ») :
```spl
index=linux sourcetype=linux:auth | stats count by host source
```
✅ `count = 30`, `host` = nom de la VM, `source` = `/var/log/soc-lab/generated/auth-sim.log`. Attendre 10-60 s la première fois.
❌ Rien ? Passez à l'étape 6.

### Étape 6 — Suivre l'UF par ses propres logs
Sur l'UF :
```bash
sudo tail -50 /opt/splunkforwarder/var/log/splunk/splunkd.log
sudo /opt/splunkforwarder/bin/splunk list inputstatus | head -40
```
Dans Splunk (les UF envoient aussi leurs logs internes) :
```spl
index=_internal host=<nom_de_la_VM> sourcetype=splunkd log_level IN (WARN,ERROR) | stats count by component
```
Composants parlants : `TcpOutputProc` (sortie réseau), `TailReader`/`WatchedFile` (lecture de fichiers), `FileInputTracker`.

### Étape 7 — Comprendre le checkpoint
1. `sudo /opt/splunkforwarder/bin/splunk restart`.
2. Relancez la recherche de l'étape 5 → **toujours 30**, pas 60 : l'UF n'a pas relu le fichier.
3. Ajoutez 10 lignes (`--count 10`) → **40**. Il n'envoie que la suite.

### Étape 8 — Prouver l'ACK (panne contrôlée)
1. Sur le PC Windows : `Stop-Service Splunkd` (ou arrêtez Splunk).
2. Sur la VM : `python3 generators/write_linux_logs.py --count 50 --rate 0`.
3. `sudo /opt/splunkforwarder/bin/splunk list forward-server` → *inactive*.
4. Relancez Splunk ; attendez 1-2 min.
5. ✅ `index=linux sourcetype=linux:auth | stats count` passe de **40 à 90**, sans doublon : `| stats count by _raw | where count>1` ne renvoie rien (sur vos lignes générées, qui sont distinctes par PID et heure).

### Étape 9 — Limiter ou libérer le débit
Un UF est limité par défaut à **256 Ko/s** (`[thruput] maxKBps = 256` dans `limits.conf`). Sur gros volumes, c'est une cause classique de **retard**. Ne le changez pas ici ; sachez où : `splunk btool limits list thruput --debug`.

### Étape 10 — (Optionnel) Deployment Server
1. Sur Windows (Splunk = DS) : créez `...\etc\deployment-apps\soc_uf_linux\` et copiez-y `configs/uf-apps/soc_uf_linux/*`.
2. Copiez `configs/deployment-server/serverclass.conf` dans `...\etc\system\local\`, `splunk reload deploy-server`.
3. Sur l'UF : `splunk set deploy-poll 10.50.0.10:8089` puis `restart` (ou utilisez `deploymentclient.conf`).
4. Dans Splunk Web : *Settings → Forwarder Management* : le client apparaît ; vérifiez l'app déployée.
✅ Vous savez changer la config de 100 UF sans y toucher individuellement. **Attention** : l'app déployée écrase la version locale ; exportez-la d'abord.

## ⚠️ Pièges
- **UF sans droit de lecture** : fichier lisible par vous, pas par `splunkfwd` (voir E2, incident 02).
- **`index` inexistant** : l'UF envoie, Splunk jette ou range ailleurs (incident 04).
- **`crcSalt`/rotation** : deux fichiers dont les 256 premiers octets sont identiques peuvent être pris pour le même ; sachez que `initCrcLength` et `crcSalt` existent.
- Mettre des **secrets** dans `outputs.conf` pushé par Git.
- Fichiers `.gz` de rotation relus : utilisez `whitelist`/`blacklist` (voir `inputs.conf`).

## 📝 Auto-évaluation
1. Quel fichier gagne entre `apps/soc_uf_linux/default/inputs.conf` et `system/local/inputs.conf` ? Quel outil le prouve ?
2. Pourquoi l'UF ne duplique-t-il pas les événements au redémarrage ?
3. Que protège `useACK=true` ? Que ne protège-t-il **pas** ?
4. Donnez 2 raisons d'un retard d'ingestion qui n'est pas une panne.
