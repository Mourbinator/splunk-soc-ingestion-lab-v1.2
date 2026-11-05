# INC-01 — « Le firewall n'apparaît plus dans Splunk »
**Ticket :** depuis 10 min, plus aucun événement `soc:firewall`. Le pare-feu « envoie ». **Couche visée :** réseau / collecteur. **Durée :** 45 min.
**Pré-requis :** collecteur sain ; `index=network sourcetype=soc:firewall` reçoit des événements.

## Injection (formateur)
L'émetteur est « reconfiguré » avec le mauvais port :
```bash
python3 generators/send_syslog.py --host 127.0.0.1 --port 514 --count 50 --rate 0          # UDP : aucune erreur affichée !
python3 generators/send_syslog.py --host 127.0.0.1 --port 514 --count 5 --tcp              # TCP : « Connection refused »
```
## Symptôme
Zéro nouveau événement ; l'émetteur ne rapporte aucune erreur (UDP).

## Méthode guidée
1. **Constater** : `wc -l /var/log/soc-lab/firewall/firewall.log` à deux instants (ne grossit plus ?) ; `| tstats latest(_time) where index=network by sourcetype`.
2. **Couche réseau** : `sudo tcpdump -ni any port 514 -c 3` pendant l'envoi → des paquets partent mais… vers qui écoute-t-on ? `sudo ss -lntup | grep -E '514|5514'`.
3. **Hypothèse** : l'émetteur vise un port sur lequel personne n'écoute.
4. **Test** : `python3 generators/send_syslog.py --port 514 --tcp --count 1` → *refused* confirme.
5. **Correction** : émetteur → `--port 5514` ; relancez 50 événements ; prouvez 50 lignes puis 50 événements Splunk.
6. **Prévention** : alerte fraîcheur (Q02) sur `network`.

<details><summary>Indice 1</summary>UDP ne signale pas les erreurs ; TCP, si.</details>
<details><summary>Indice 2</summary>`ss -lntup` liste ce qui **écoute** vraiment.</details>

**Livrable :** post-mortem + capture `tcpdump` + sortie `ss`.
## Retour à la normale
Rien à défaire côté serveur ; renvoyez un lot sur 5514 et vérifiez le smoke test.
