# Installation côté Ubuntu (VM : collecteur Syslog + Universal Forwarder + générateurs)

Testé conceptuellement pour Ubuntu 22.04/24.04. Toutes les commandes sont exécutées sur la VM. Remplacez `10.50.0.10` par l'IP du PC Splunk.

## Étape 1 — Préparer le système
```bash
sudo timedatectl set-timezone UTC          # IMPORTANT : le format SSH n'a pas de fuseau (voir M4)
timedatectl                                 # « Time zone: Etc/UTC » et « System clock synchronized: yes »
sudo apt update && sudo apt install -y python3 netcat-openbsd tcpdump curl
nc -vz 10.50.0.10 9997                      # (plus tard, quand Splunk écoute) : « succeeded »
```

## Étape 2 — Récupérer le dépôt
Copiez le dépôt sur la VM (zip + `scp`, ou dossier partagé), puis :
```bash
cd ~/splunk-soc-ingestion-lab-v1.2
python3 scripts/validate_repo.py            # doit se terminer par « OK »
```

## Étape 3 — Collecteur syslog-ng
```bash
sudo apt install -y syslog-ng-core
sudo cp collectors/syslog/conf.d/soc-lab.conf /etc/syslog-ng/conf.d/
sudo syslog-ng --syntax-only && echo "SYNTAXE OK"
sudo systemctl restart syslog-ng && systemctl is-active syslog-ng
sudo ss -lntup | grep 5514                  # doit montrer udp ET tcp sur 0.0.0.0:5514
sudo ufw status                             # si actif : sudo ufw allow from 10.50.0.0/24 to any port 5514
```
> Si `/etc/syslog-ng/syslog-ng.conf` n'inclut pas `conf.d`, ajoutez la ligne `@include "/etc/syslog-ng/conf.d/*.conf"` à la fin.

## Étape 4 — Dossiers de travail
```bash
sudo mkdir -p /var/log/soc-lab/{firewall,unrouted,generated,app,web}
sudo chown -R root:adm /var/log/soc-lab && sudo chmod -R 0770 /var/log/soc-lab/generated
sudo chown "$USER":adm /var/log/soc-lab/generated   # pour que write_linux_logs.py puisse écrire
```

## Étape 5 — Universal Forwarder
1. Téléchargez le `.deb` de l'**Universal Forwarder** sur le site de Splunk (compte requis) — version compatible avec votre Splunk Enterprise.
2. Installation et premier démarrage :
```bash
sudo dpkg -i splunkforwarder-*.deb
sudo /opt/splunkforwarder/bin/splunk start --accept-license      # crée l'admin local de l'UF : notez le mot de passe
sudo /opt/splunkforwarder/bin/splunk enable boot-start
ps -o user= -C splunkd | head -1                                  # utilisateur qui exécute l'UF (souvent splunkfwd)
```
3. Autoriser la lecture des fichiers système (groupe `adm`) — remplacez `splunkfwd` par l'utilisateur obtenu ci-dessus :
```bash
sudo usermod -aG adm splunkfwd
```
4. Déployer les apps de configuration du lab :
```bash
sudo cp -r configs/uf-apps/soc_uf_outputs configs/uf-apps/soc_uf_linux /opt/splunkforwarder/etc/apps/
sudo sed -i 's/10\.50\.0\.10/<IP_DU_PC_SPLUNK>/' /opt/splunkforwarder/etc/apps/soc_uf_outputs/default/outputs.conf
sudo chown -R splunkfwd:splunkfwd /opt/splunkforwarder/etc/apps/soc_uf_*
sudo /opt/splunkforwarder/bin/splunk restart
```
5. Vérifier :
```bash
sudo /opt/splunkforwarder/bin/splunk list forward-server       # « Active forwards: 10.50.0.10:9997 »
sudo /opt/splunkforwarder/bin/splunk btool inputs list --debug | grep -A3 "soc-lab/firewall"
```

## Étape 4bis — Premiers événements
```bash
python3 generators/write_linux_logs.py --count 20 --rate 0
python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 20 --rate 0
wc -l /var/log/soc-lab/firewall/firewall.log /var/log/soc-lab/generated/auth-sim.log
```
Puis dans Splunk : `index=network OR index=linux earliest=-15m | stats count by index sourcetype`.

## Désinstaller proprement
```bash
sudo /opt/splunkforwarder/bin/splunk stop && sudo /opt/splunkforwarder/bin/splunk disable boot-start
sudo dpkg -r splunkforwarder && sudo rm -rf /opt/splunkforwarder
```
