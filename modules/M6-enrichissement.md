# M6 — Enrichissement : lookups (≈ 5 h)

## 🎯 Objectifs
Ajouter du **contexte** (nom/criticité d'un serveur, zone réseau, description d'une règle) aux événements, automatiquement au search-time, en comprenant limites et performances.
**Prérequis :** M5. **Exercice :** `exercises/E6-enrichissement.md`.

## 🧠 Notions
- **Enrichir** = joindre une table de référence à l'événement. Ex. `dest_ip=198.51.100.21` → `dest_name=db-prod-01`, `dest_priority=critical`.
- **Search-time vs index-time.** Au **search-time** (lookup) : rétroactif, la table peut évoluer, coûte un peu de CPU à chaque recherche. À l'**index-time** : figé à l'écriture, rapide à la lecture, mais **faux dès que la table change**. Par défaut : search-time.
- **Types de lookups** : CSV (ce lab), **CIDR** (plage d'IP), *wildcard*, **KV Store** (grosses tables modifiables), externe (script). `iplocation` (GeoIP) enrichit les IP **publiques** ; les IP de documentation (192.0.2.0/24…) n'ont pas de localisation → d'où notre table de zones.
- **Lookup automatique** : `LOOKUP-<nom> = <lookup> <clé> [AS <champ_évent>] OUTPUT <champs>` dans `props.conf` ; Splunk l'applique à **chaque** événement du sourcetype.

## 🛠️ Pas à pas
### Étape 1 — Lire les tables
```spl
| inputlookup soc_assets.csv
| inputlookup soc_fw_rules.csv
| inputlookup soc_ip_zones.csv
```
Notez : clé `ip` (assets), `rule_id` (règles), `cidr` (zones).

### Étape 2 — Lookup **manuel** (comprendre avant d'automatiser)
```spl
index=lab_sandbox sourcetype=soc:firewall earliest=0
| lookup soc_assets ip AS dest_ip OUTPUT dest_name dest_priority
| stats count by dest_ip dest_name dest_priority
```
✅ Les IP `198.51.100.10/20/21/22/30/40/50/60` ont un nom ; les autres : champs vides.

### Étape 3 — Lookup **automatique**
Sans écrire `| lookup`, la requête suivante doit déjà donner les champs enrichis (SA-soc-enrichment installé, exporté `system`) :
```spl
index=lab_sandbox sourcetype=soc:firewall earliest=0
| stats count by dest_name dest_category dest_priority src_zone dest_zone rule_name rule_severity
| sort - count | head 20
```
✅ Des lignes comme `db-prod-01, database, critical, partner, dc-servers, ...`.
❌ Champs vides ? Vérifiez : (a) app `SA-soc-enrichment` présente, (b) `metadata/default.meta` → `export = system`, (c) `btool props list soc:firewall --debug` contient `LOOKUP-soc_*`, (d) refresh `debug/refresh`.

### Étape 4 — Lookup **CIDR**
Le champ `src_zone` vient de `soc_ip_zones.csv` (`match_type = CIDR(cidr)`). Testez : `| makeresults | eval src_ip="192.0.2.70" | lookup soc_ip_zones cidr AS src_ip OUTPUT zone` → `partner`.
Exercice : quelle zone pour `192.0.2.200` ? pour `203.0.113.5` ? (voir ANSWER-KEY.)

### Étape 5 — Utiliser l'enrichissement pour **prioriser**
```spl
index=lab_sandbox sourcetype=soc:firewall earliest=0 action=blocked dest_priority IN ("critical","high")
| stats count by dest_name src_zone | sort - count
```
🔑 L'enrichissement transforme « une IP a été bloquée » en « des **partenaires** ont tenté d'atteindre une **base critique** ».

### Étape 6 — Faire évoluer une table sans redémarrer
1. Ajoutez une ligne dans `soc_assets.csv` (`198.51.100.70,test-01,sandbox,low,team-dev`).
2. Redéployez le fichier ; les lookups CSV sont lus à la volée, un `debug/refresh` suffit en général.
3. Relancez l'étape 2 avec ce nouvel actif. 🔑 *Rétroactif : les événements d'hier bénéficient de la nouvelle ligne.*
4. Versionnez : ligne dans le CHANGELOG, `git diff` du CSV, relecture par le propriétaire de la donnée.

### Étape 7 — Fabriquer une watchlist dynamique
```spl
index=lab_sandbox sourcetype=soc:firewall earliest=0 action=blocked
| stats count by src_ip | where count>=15
| outputlookup soc_watchlist_ips.csv
```
Puis : `index=... [ | inputlookup soc_watchlist_ips.csv | fields src_ip ] | stats count by src_ip`. 🔑 La sortie d'une recherche devient l'entrée d'une autre.

### Étape 8 — Performance
- Taille d'une table CSV : jusqu'à quelques dizaines de milliers de lignes OK ; au-delà → **KV Store**.
- Un lookup automatique est exécuté sur *chaque* événement : n'en ajoutez pas par réflexe.
- `| lookup` en fin de recherche (après `stats`) coûte bien moins qu'avant.

## ⚠️ Pièges
- **Casse et espaces** dans le CSV (`" 198.51.100.10"`), BOM UTF-8, fins de ligne Windows.
- Lookup **non exporté** → champs vides dans les autres apps.
- Un lookup automatique qui **écrase** un champ existant (nommez vos sorties avec soin).
- Clé numérique vs texte (`rule_id`).
- Enrichir à l'index-time sans nécessité (table figée dans les données).

## 📝 Auto-évaluation
1. Pourquoi les IP de documentation n'ont-elles pas de géolocalisation ? 2. Search-time ou index-time pour une table d'actifs ? Pourquoi ?
3. Que fait `OUTPUT zone AS src_zone` ? 4. Quand préférer le KV Store ?
