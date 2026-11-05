# M5 — Normalisation : Technical Add-on et CIM (≈ 8 h)

## 🎯 Objectifs
Normaliser des champs et valeurs vers le **CIM**, faire reconnaître vos événements par un **modèle de données**, versionner et tester un TA.
**Prérequis :** M4, app CIM installée (`INSTALL-SPLUNK-WINDOWS.md` étape 6). **Exercice :** `exercises/E5-normalisation.md`.

## 🧠 Notions
- **Pourquoi normaliser ?** Un firewall écrit `src_ip`, un autre `source`, un troisième `SourceAddress`. Si chaque détection doit connaître tous les noms, elle ne passe pas à l'échelle. Le **CIM** fixe un vocabulaire : `src`, `dest`, `action`, `user`, `transport`…
- **Modèle de données (ex. Network Traffic)** : un « contrat » de champs. Il reconnaît un événement par **tags** (`network` + `communicate`). Les tags s'attachent à un **eventtype**.
- **Ordre d'application au search-time** (à retenir) : `extractions → FIELDALIAS → EVAL (champs calculés) → LOOKUP → eventtypes → tags`.
  Conséquence : un `FIELDALIAS` peut copier la valeur **brute** *avant* qu'un `EVAL` ne la remplace ; un `EVAL` ne peut pas s'appuyer sur un autre `EVAL`.
- **Normaliser = noms ET valeurs** : `deny`/`drop` → `blocked`, `allow` → `allowed` ; on garde la valeur brute dans `action_raw` pour ne rien perdre.
- **Un TA = un paquet** : `default/` (ne pas toucher), `local/` (surcharges), `metadata/`, `README`, version dans `app.conf`.

## 🛠️ Pas à pas
### Étape 1 — Voir l'état brut puis normalisé
Ingérez `firewall.log` dans le sandbox (voir M4). Puis :
```spl
index=lab_sandbox sourcetype=soc:firewall earliest=0
| stats count by action action_raw
```
✅ `allowed ↔ allow`, `blocked ↔ deny` et `blocked ↔ drop` (jamais `allow→blocked`). Vérifiez `| table src src_ip dest dest_ip transport protocol rule`.

### Étape 2 — Lire les 4 mécanismes dans `props.conf`
`FIELDALIAS-` (renomme), `EVAL-` (calcule), `REPORT-` (extrait), `LOOKUP-` (M6). Pour `EVAL-action`, expliquez pourquoi `action_raw` existe (ordre alias → eval).

### Étape 3 — Tags et eventtypes
```spl
index=lab_sandbox sourcetype=soc:firewall earliest=0 | stats count by eventtype tag
```
✅ Tous les événements portent `soc_firewall_traffic` et les tags `network`, `communicate`. Ceux `action=allowed` ont aussi `soc_firewall_allowed`.
👉 Le défaut de la v1.1 : seuls les refus avaient ces tags → les `allow` étaient invisibles du modèle.

### Étape 4 — Valider avec le modèle de données
Prérequis : l'index du sandbox (ou `network`) doit figurer dans les index du CIM Network Traffic.
```spl
| datamodel Network_Traffic All_Traffic search
| search sourcetype=soc:firewall
| stats count by All_Traffic.action
```
ou (si accélération) `| tstats count from datamodel=Network_Traffic where nodename=All_Traffic by All_Traffic.action`.
✅ Des lignes `allowed` et `blocked`. ❌ Aucun résultat → vérifiez dans l'ordre : *tags*, *index autorisé dans CIM Setup*, *période de recherche* (données du 10/10).

### Étape 5 — Authentication (Linux)
Ingérez `linux-auth.log` (`-sourcetype linux:auth`).
```spl
index=lab_sandbox sourcetype=linux:auth earliest=0
| stats count by action app
```
✅ `success`/`failure` pour `sshd`. Puis une première « détection » exploitant la normalisation :
```spl
index=lab_sandbox sourcetype=linux:auth action=failure earliest=0
| bin _time span=1m | stats count dc(user) as users by _time src | where count>=10
```
✅ 192.0.2.99 apparaît (40 échecs en 40 s). *Une détection écrite sur `action=failure` fonctionnera demain avec Windows et le cloud.*

### Étape 6 — Cloud et SaaS (mapping partiel)
Ingérez `m365-audit.jsonl` (`-sourcetype m365:audit`). Vérifiez `user`, `src`, `signature`, `action`. Pour `eventtype=soc_m365_login`, le tag `authentication` est posé : la ligne apparaît dans le modèle Authentication. **Exercice E5 bonus :** compléter le mapping *Change* pour AWS/Azure/GCP (`status`, `object_category`, `command`).

### Étape 7 — Cycle de vie d'un TA
1. **Modifier** dans `default/` (en dépôt) ou `local/` (urgence).
2. **Tester** : `python3 -m unittest discover -s tests` (simulation) + SPL de `tests/spl/`.
3. **Versionner** : `app.conf` `version`, ligne dans `CHANGELOG.md`.
4. **Packager** : `tar czf TA-soc-firewall-1.2.0.tgz TA-soc-firewall/`.
5. **Rollback** : redéployer la version précédente + `restart` (les données déjà indexées ne changent pas : c'est la force du search-time).

### Étape 8 — Régression
Cassez `tags.conf` (supprimez `communicate`), relancez l'étape 4 : plus rien dans le modèle. Rétablissez. 🔑 Gardez ce réflexe : *un test SPL par règle de normalisation*.

## ⚠️ Pièges
- Écraser `action` avec un `EVAL` **sans** conserver la valeur brute.
- Tags sur un eventtype trop étroit (v1.1).
- Oublier `export = system` dans `metadata/default.meta` → le TA n'est visible que dans son app.
- `KV_MODE=auto` + `REPORT` → doublons.
- Modifier directement les TA du CIM/Splunkbase au lieu d'ajouter une app.

## 📝 Auto-évaluation
1. Quel ordre d'application : EVAL, FIELDALIAS, LOOKUP ? 2. Quels tags rendent un événement « Network Traffic » ?
3. Pourquoi garder `action_raw` ? 4. Que veut dire `export = system` ?
