# M2 — Syslog et collecteurs (≈ 7 h)

## 🎯 Objectifs
Installer/configurer un collecteur Syslog (syslog-ng), comprendre UDP vs TCP vs TLS, router par émetteur, gérer droits et rotation, **mesurer** la perte et la prouver.
**Prérequis :** M1. **Exercice :** `exercises/E2-syslog.md`.

## 🧠 Notions
- **Syslog** : protocole d'envoi de logs. Format moderne **RFC 5424** : `<PRI>1 TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG`. `PRI = facility×8 + severity` (`<134>` = local0.info).
- **UDP** : « lancer une bouteille à la mer » : rapide, **sans accusé** ni retransmission. TCP : connexion + retransmission. TLS : TCP + chiffrement/authentification.
- **Pourquoi un collecteur devant Splunk** : (1) il écoute en permanence, **tamponne** quand Splunk redémarre ; (2) il sépare par émetteur/APP-NAME ; (3) il garde un fichier = point de reprise et de **preuve** ; (4) Splunk reste concentré sur l'indexation.
- **Routage collecteur** : *filtre* (`program("^soc-firewall$")`) → *destination* (un fichier). Tout ce qui ne correspond à rien va dans `unrouted.log` : **rien ne disparaît en silence**.
- **Rotation** : sans `logrotate`, le fichier grossit sans fin (disque plein = panne d'ingestion).

## 🛠️ Pas à pas
### Étape 1 — Lire la configuration
Ouvrez `collectors/syslog/conf.d/soc-lab.conf`. Repérez : 2 sources (UDP, TCP), 1 template, 2 filtres, 2 destinations, 2 `log {}`. Chaque `log {}` relie *source → filtre → destination*.

### Étape 2 — Installer et valider
```bash
sudo cp collectors/syslog/conf.d/soc-lab.conf /etc/syslog-ng/conf.d/
sudo syslog-ng --syntax-only && echo "SYNTAXE OK"
sudo systemctl restart syslog-ng
sudo ss -lntup | grep 5514
```
✅ deux lignes : `udp ... 0.0.0.0:5514` et `tcp ... LISTEN ... 0.0.0.0:5514`.

### Étape 3 — Voir passer un paquet
Terminal A : `sudo tcpdump -ni any udp port 5514 -A -c 2`
Terminal B : `python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 2 --rate 0`
✅ Dans A, la ligne `<134>1 2026-… firewall01 soc-firewall - - - event_id=fw-xxxxxx-000001 …`.

### Étape 4 — Envoyer 100 événements UDP et compter
```bash
: | sudo tee /var/log/soc-lab/firewall/firewall.log >/dev/null     # repartir d'un fichier vide (lab uniquement)
python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 100 --rate 50
wc -l /var/log/soc-lab/firewall/firewall.log
head -2 /var/log/soc-lab/firewall/firewall.log
```
✅ **100 lignes**. Chaque ligne : `2026-10-19T…+00:00 firewall01 event_id=fw-… event_time=… src_ip=…`. Le préfixe `date hôte` vient du *template* ; l'en-tête `<134>1 … soc-firewall - - -` a été consommé par l'analyse RFC 5424.
**Conservez le JSON** imprimé par le script (`run_id`, `sent`).

### Étape 5 — Tableau « généré / reçu / indexé »
| Point de mesure | Comment compter | 100 attendus ? |
|---|---|---|
| Généré | `sent` du JSON | 100 |
| Reçu par le collecteur | `grep -c "fw-<run_id>-" firewall.log` | 100 |
| Indexé par Splunk | `index=network sourcetype=soc:firewall event_id=fw-<run_id>-* \| stats dc(event_id)` | 100 |
Une différence = une perte à **localiser** : entre les deux premières lignes, c'est le réseau/collecteur ; entre les deux dernières, c'est l'UF/Splunk.

### Étape 6 — Même test en TCP
```bash
python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 100 --tcp
```
✅ Le fichier gagne 100 lignes (pas de lignes collées : le générateur ajoute un vrai `\n`).

### Étape 7 — Routage par APP-NAME
```bash
python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 5 --app other-app --hostname lab-app01
tail -3 /var/log/soc-lab/unrouted/unrouted.log
```
✅ Les 5 messages sont dans `unrouted.log`, **pas** dans `firewall.log`. Dans Splunk : `index=lab_api sourcetype=soc:unrouted`.

### Étape 8 — Droits de lecture
```bash
ls -l /var/log/soc-lab/firewall/firewall.log            # -rw-r----- root adm
id splunkfwd                                             # doit contenir adm
sudo -u splunkfwd head -1 /var/log/soc-lab/firewall/firewall.log   # doit afficher une ligne
```
❌ « Permission denied » → `sudo usermod -aG adm splunkfwd` puis **redémarrer l'UF** (les groupes se lisent au démarrage).

### Étape 9 — Rotation
```bash
sudo cp collectors/syslog/logrotate-soc-lab /etc/logrotate.d/soc-lab
sudo logrotate -d /etc/logrotate.d/soc-lab        # simulation (-d = debug, ne change rien)
sudo logrotate -f /etc/logrotate.d/soc-lab        # force une rotation
ls -l /var/log/soc-lab/firewall/
```
✅ Un `firewall.log` neuf + `firewall.log.1`. L'UF continue sur le nouveau fichier (la whitelist `firewall\.log$` ignore `.1` et `.gz`).

### Étape 10 — Mesurer la perte UDP (expérience)
```bash
python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 20000 --rate 0
grep -c "fw-<run_id>-" /var/log/soc-lab/firewall/firewall.log
```
En boucle locale, la perte est souvent nulle ; sur un réseau chargé elle apparaît. Le **but** est la méthode : *sent − reçu = perte*, et **c'est pour cela que l'on préfère TCP** pour les sources importantes.

### Étape 11 — (Avancé) TLS
Suivez les commentaires de `collectors/syslog/conf.d/soc-lab-tls.conf.example` : générez un certificat auto-signé, renommez en `.conf`, `syslog-ng --syntax-only`, redémarrez, testez avec `openssl s_client -connect 127.0.0.1:6514`.

### Étape 12 — (Alternative) rsyslog
Si votre équipe utilise rsyslog : `collectors/syslog/rsyslog-soc-lab.conf`. **Ne lancez pas** syslog-ng et rsyslog sur le même port. Comparez la forme exacte d'une ligne produite avec celle de syslog-ng : l'important est que `event_time=` soit présent.

## ⚠️ Pièges
- **Port 514** < 1024 : demande root ; le lab utilise **5514**.
- **DNS inverse** (`use_dns(yes)`) ralentit énormément : désactivé dans la conf.
- **Heure** : l'UDP ne transporte pas toujours le fuseau ; vérifiez la source de temps du firewall.
- **Fichiers énormes** sans rotation ; **droits** perdus après rotation (d'où `create 0640 root adm`).
- **Deux collecteurs** sur le même port : le second échoue à démarrer.

## 📝 Auto-évaluation
1. Que veut dire `<134>` ? 2. Pourquoi le message possède-t-il trois `-` avant `event_id` ?
3. Que devient un message d'APP-NAME inconnu ? 4. Comment prouver une perte UDP de 0,3 % ?
