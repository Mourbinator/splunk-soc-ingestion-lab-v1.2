# E7 — Routage, filtrage, masquage
**Module :** M7 · **Durée :** 5 h · **Livrables :** app `soc_routing`, `preuves/E7-avant-apres.md`

**Cahier des charges** (équipe SOC) :
- (R1) Le champ `host` des événements firewall doit être l'**émetteur réel** (ex. `firewall01`).
- (R2) Les événements RDP (port 3389) vont dans l'index `security`.
- (R3) Les DNS autorisés (port 53, `action=allow`) ne doivent plus être indexés.
- (R4) Dans `soc:app`, mots de passe et jetons Bearer sont masqués.

## Étapes
1. **Mesures avant** : sur un lot de **1000** événements (`send_syslog.py --count 1000 --rate 0 --tcp`, notez le `run_id`) comptez, **avant** tout changement, les événements DNS-allow et RDP attendus (sur le fichier du collecteur avec `grep`/`awk`).
2. Créez `soc_routing/local/{props,transforms}.conf` implémentant R1–R4 (voir M7). Utilisez **un seul** `TRANSFORMS-` ordonné pour R1–R3.
3. `btool check`, redémarrez, envoyez un **nouveau** lot de 1000 (nouveau `run_id`).
4. **Preuves après** : `host=firewall01`, nombre dans `security`, 0 DNS-allow indexé (mais présents dans le fichier du collecteur), `soc:app` sans mot de passe.
5. Calculez l'**économie de volume** (octets) due à R3 sur une journée à 20 ev/s.
6. **L'ordre compte.** Ajoutez une règle R5 : tout événement `dest_ip=198.51.100.21` (base de données) va dans l'index `lab_api` (`DEST_KEY = _MetaData:Index`). Un événement RDP vers `198.51.100.21` correspond à **R2 et R5** : **prédisez** dans quel index il finit selon l'ordre de la liste, testez les deux ordres (`btool`, restart, nouveau lot) et expliquez (la dernière transformation exécutée l'emporte). Retirez R5 ensuite.
7. **Plan de retour arrière** : comment annulez-vous R3 si on découvre que le DNS-allow servait à une détection ?
8. **(Bonus HF)** Reproduisez R2 avec `_TCP_ROUTING` via `configs/hf/`.

<details><summary>Indice (R1)</summary>`REGEX = ^\S+\s+(\S+)\s+event_id=` ; `DEST_KEY = MetaData:Host` ; `FORMAT = host::$1`.</details>
<details><summary>Indice (R3)</summary>Deux lookaheads : `(?=.*\sdest_port=53\s)(?=.*\saction=allow\s)`.</details>

## Critères (35 pts)
1: 4 · 2: 10 · 4: 8 · 5: 3 · 6: 4 · 7: 3 · bonus 3.
