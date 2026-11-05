# M9 — Qualité et supervision de la collecte (≈ 7 h)

## 🎯 Objectifs
Mesurer objectivement la santé de l'ingestion avec 7 dimensions, transformer les mesures en **alertes**, et distinguer « la source ne parle plus » de « Splunk n'a rien reçu ».
**Prérequis :** M1–M6. **Exercice :** `exercises/E9-qualite.md`. Outils : `splunk-apps/soc_lab_quality` (14 recherches, désactivées), `tests/spl/`.

## 🧠 Notions — les 7 dimensions
| Dimension | Question | Mesure (voir Q01–Q14) |
|---|---|---|
| **Volume** | Combien ? comparé à d'habitude ? | `tstats count` par sourcetype/host |
| **Fraîcheur** | Quand ai-je vu le dernier événement ? | `latest(_time)` → âge |
| **Retard (latence)** | Combien entre l'événement et l'indexation ? | `_indextime - _time`, p95 |
| **Complétude** | Manque-t-il des événements ? des champs ? | trous de séquence, champs obligatoires |
| **Unicité** | Doublons ? | `stats count by event_id` |
| **Validité** | Valeurs permises ? | `action_raw` inconnu |
| **Dérive** | Le format a-t-il changé ? | lignes hors regex du contrat |
**SLO** : un objectif chiffré (ex. 95 % < 120 s). **Alerte** : déclenche quand un SLO est violé, avec **throttling** pour ne pas spammer.

## 🛠️ Pas à pas
### Étape 1 — Générer du trafic « vivant »
Les datasets ont des dates du 10/10 ; pour la **fraîcheur** et le **retard**, il faut des événements récents :
```bash
python3 generators/send_syslog.py --host 127.0.0.1 --port 5514 --count 600 --rate 10 --tcp     # ≈ 1 min
```
**Conservez le JSON** (run_id, sent).

### Étape 2 — Activer et lire les recherches
Application *SOC Lab Quality* : ouvrez *Searches, reports and alerts*, lancez **Q01** (volume) et **Q02** (fraîcheur). Chaque recherche est **désactivée** : ouvrez-la, copiez le SPL, exécutez-le dans Search, **adaptez** la période (-15 min).

### Étape 3 — Retard d'indexation (Q03)
✅ `p95_lag` de quelques secondes (collecteur + UF + indexeur). *Attention* : un `lag` **négatif** ou énorme signale un problème d'**horloge** ou de **fuseau**, pas de réseau. 🔑 Un SLO de latence n'a de sens que si les horloges sont synchronisées (NTP).

### Étape 4 — Complétude par numéro de séquence (Q06)
Les `event_id` portent un numéro de séquence → trous détectables.
```spl
index=network sourcetype=soc:firewall earliest=-30m
| rex field=event_id "^fw-(?<run>[a-z0-9]+)-(?<seq>\d+)$"
| stats min(seq) as first max(seq) as last dc(seq) as received by run
| eval expected=tonumber(last)-tonumber(first)+1, missing=expected-received
```
✅ Pour votre `run_id`, `missing=0`. **Test** : générez un lot en arrêtant l'UF à mi-chemin → `missing>0` temporairement ; puis relancez l'UF : `missing` retombe à 0 (preuve du rattrapage).

### Étape 5 — Doublons et validité (Q05, Q07)
Ingérez deux fois `firewall-anomalies.log` dans le sandbox → Q05 (`event_id` en double) montre `fw-an-0007` avec `copies=4`.
Q07 montre `action=reset` (inconnu).

### Étape 6 — Dérive de format (Q08)
`firewall-anomalies.log` contient 2 lignes d'un **autre format** (JSON, colonnes). Q08 les liste. 🔑 *La dérive est la panne la plus insidieuse : rien n'est perdu, mais rien n'est exploitable.*

### Étape 7 — Santé interne (Q09, Q10, Q11, Q13, Q14)
Pour chacune, dites : *quelle panne détecte-t-elle ?* (parsing/horodatage ; UF muet ; erreurs HEC ; index inexistant ; files bloquées).

### Étape 8 — Créer une alerte « source silencieuse »
1. Partez de Q02, ajoutez : `| where age_s>300 AND index="network"`.
2. *Save As → Alert* : planifiée toutes les 5 min, déclenchement si résultats > 0, **Throttle** 30 min.
3. Test : arrêtez l'UF 6 minutes → l'alerte se déclenche ; relancez → elle se rétablit.
4. Écrivez sa **fiche** : propriétaire, seuil, action attendue, faux positifs connus (arrêt programmé…).

### Étape 9 — Tableau de bord minimal
Un tableau de bord *Ingestion SOC* : (1) volume par sourcetype (Q01), (2) fraîcheur (Q02), (3) p95 retard (Q03), (4) trous de séquence (Q06), (5) erreurs de parsing (Q09). Chaque panneau a un **seuil lisible** (vert/orange/rouge).

## ⚠️ Pièges
- Mesurer la fraîcheur avec `index=… | head 1` (lent et trompeur) au lieu de `tstats`.
- Alerter sans **throttling**.
- Ne pas distinguer *source silencieuse légitime* (week-end) de *panne*.
- Comparer des périodes différentes (datasets du 10/10 vs temps réel).
- Seuils arbitraires jamais révisés.

## 📝 Auto-évaluation
1. Pourquoi `tstats` pour la fraîcheur ? 2. Que signifie un `lag` négatif ? 3. Comment détecter un trou **sans** compter à la main ?
4. Donnez 3 faux positifs d'une alerte « silence ».
