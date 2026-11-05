# E6 — Enrichissement : nouveau lookup, watchlist, performance
**Module :** M6 · **Durée :** 5 h · **Livrables :** CSV + config + `preuves/E6-*`

1. **Lookup utilisateurs.** Créez `soc_users.csv` (`user,department,is_privileged`) pour `alice,bob,svc-backup,root,admin`. Déclarez-le dans `transforms.conf` et ajoutez un `LOOKUP-soc_user = soc_users user OUTPUT department is_privileged` pour `linux:auth` (dans `SA-soc-enrichment`). Prouvez : `| stats count by department is_privileged`.
2. **Piège CIDR.** Trouvez la zone de `192.0.2.200`, `192.0.2.63`, `192.0.2.64`, `203.0.113.5`. Expliquez la dernière.
3. **Priorisation.** Écrivez une recherche qui liste les **5** actifs `critical`/`high` les plus visés par des refus, avec la zone d'origine dominante.
4. **Watchlist.** Générez `soc_watchlist_ips.csv` (sources ≥ 15 refus) puis utilisez-la dans une recherche de détection qui compte les accès **autorisés** de ces IP.
5. **Qualité de la table.** Introduisez volontairement un espace en trop dans un `ip` du CSV et un doublon : décrivez l'effet, puis écrivez une recherche de **contrôle de la table** (`| inputlookup ... | stats count by ip | where count>1`).
6. **Performance.** Mesurez la durée de la même recherche avec lookup **automatique** et avec `| lookup` placé après `stats` (Job Inspector). Concluez.
7. **Décision.** Pour chacun : table d'actifs, zones réseau, liste de menaces, comptes utilisateurs → *CSV / KV Store / lookup externe / index-time* et pourquoi.

<details><summary>Indice (2)</summary>Découpez les CIDR : /26 = 64 adresses (`.0-.63`, `.64-.127`), /25 = 128 (`.128-.255`).</details>

## Critères (30 pts)
1: 6 · 2: 4 · 3: 5 · 4: 5 · 5: 4 · 6: 3 · 7: 3.
