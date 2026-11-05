# E2 — Collecteur Syslog : routage, droits, rotation, mesure de perte
**Module :** M2 · **Durée :** 7 h · **Livrables :** `preuves/E2-compteurs.md`, `preuves/E2-config.diff`

1. **Tableau de compteurs.** Envoyez 500 événements UDP puis 500 TCP (`--count 500`). Pour chaque lot, notez *généré / reçu fichier / indexé Splunk* (utilisez le `run_id`). Expliquez tout écart.
2. **Nouveau flux.** Ajoutez au collecteur une 3ᵉ famille `soc-vpn` écrite dans `/var/log/soc-lab/vpn/vpn.log` (destination + filtre + `log{}`) ; validez `--syntax-only` ; testez avec `--app soc-vpn`. Les messages `other-app` doivent **toujours** aller dans `unrouted.log`.
3. **Droits.** Remettez volontairement `chmod 600` sur `firewall.log`, constatez le silence côté Splunk, retrouvez la cause avec 2 preuves, corrigez, et expliquez comment éviter la récidive après rotation (`create 0640 root adm`).
4. **Rotation.** `logrotate -f` en plein envoi (`--count 2000 --rate 100` dans un autre terminal). Vérifiez : aucun événement perdu ? Comparez les compteurs.
5. **Perte UDP.** Mesurez la perte à débit élevé (`--rate 0 --count 50000`). Si vous ne perdez rien : réduisez `log-iw-size`/la taille du buffer UDP du noyau (recherche : `sysctl net.core.rmem_max`) et recommencez, **ou** conclusivement expliquez pourquoi la perte n'apparaît pas en boucle locale.
6. **Format.** Rédigez 5 lignes qui expliquent le message RFC 5424 de `send_syslog.py` : chaque champ de l'en-tête et pourquoi il y a trois `-`.
7. **(Bonus) TLS** sur 6514 avec `openssl s_client` comme preuve.

<details><summary>Indice (étape 2)</summary>Copiez `f_soc_firewall` → `f_soc_vpn` (`program("^soc-vpn$")`), `d_soc_firewall` → `d_soc_vpn`, et adaptez `f_soc_other` : `not (filter(f_soc_firewall) or filter(f_soc_vpn))`.</details>
<details><summary>Indice (étape 4)</summary>`copytruncate` n'est pas utilisé ; syslog-ng doit rouvrir le fichier : `syslog-ng-ctl reload` dans `postrotate`.</details>

## Critères (35 pts)
1: 8 · 2: 6 · 3: 6 · 4: 5 · 5: 5 · 6: 5 · bonus 4.
