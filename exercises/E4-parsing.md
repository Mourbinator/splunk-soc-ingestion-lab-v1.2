# E4 — Parsing : horodatage, multi-lignes, anomalies, TRUNCATE
**Module :** M4 · **Durée :** 8 h · **Livrables :** `preuves/E4-*`, `preuves/E4-anomalies.md`

Travaillez **uniquement** dans `lab_sandbox` (jetable). Notez avant chaque essai : hypothèse → test → résultat.

## Partie A — Horodatage
1. Ingérez `firewall.log`. Prouvez `_time` min/max et `count=2000`.
2. Cassez `TIME_PREFIX` (retirez le `\b`) puis `MAX_TIMESTAMP_LOOKAHEAD` (mettez 5) ; décrivez l'effet sur `_time` et dans `DateParserVerbose`.
3. Corrigez. Ingérez `linux-auth.log` et montrez que l'**année** a été déduite. Changez `TZ` et mesurez le décalage.

## Partie B — Multi-lignes
4. Ingérez `app-multiline.log` avec `TA-soc-app` : 150 événements. Trouvez l'événement contenant `ORD-` et `Caused by` et affichez sa `_raw`.
5. Remplacez `LINE_BREAKER` par `([\r\n]+)` + `SHOULD_LINEMERGE=false` → ? événements. Remplacez par un LINE_BREAKER qui ne matche jamais → ? événements. Expliquez.
6. Écrivez une regex `LINE_BREAKER` alternative acceptant aussi des horodatages `2026-10-10T00:00:07.412Z`.

## Partie C — Anomalies
7. Ingérez `firewall-anomalies.log`. Complétez : pour chacune des 14 lignes → *comportement observé* / *cause* / *décision* (corriger parsing, corriger source, rejeter, alerter).

## Partie D — TRUNCATE
8. Fabriquez un événement de 15 000 octets :
```bash
python3 -c "print('event_id=fw-big-000001 event_time=2026-10-10T00:00:00+0000 src_ip=192.0.2.1 dest_ip=198.51.100.10 src_port=1 dest_port=443 action=allow protocol=tcp rule_id=LAB-01 app=\"' + 'x'*15000 + '\"')" > big.log
```
Ingérez-le. Combien d'événements ? Quelle est la taille de `_raw` ? Que devient la fin ? Réglez `TRUNCATE` pour le conserver en entier **et** justifiez le risque d'une valeur illimitée.

## Partie E — Synthèse
9. Remplissez le tableau « réglage → index-time ou search-time → composant qui l'applique » pour 10 réglages.

<details><summary>Indice (5)</summary>Sans `SHOULD_LINEMERGE=false` ni LINE_BREAKER utile, Splunk fusionne ou coupe à chaque ligne. Comptez avec `| stats count`.</details>
<details><summary>Indice (8)</summary>La coupure se fait à `TRUNCATE` octets (10000 par défaut) : le reste est **ignoré** (pas indexé).</details>

## Critères (40 pts)
A : 10 · B : 10 · C : 10 (14 lignes) · D : 6 · E : 4.
