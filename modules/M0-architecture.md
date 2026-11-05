# M0 — Architecture, contrat d'intake et menaces (≈ 3 h)

## 🎯 Objectifs
À la fin du module vous saurez : (1) nommer chaque étape du chemin d'un événement, (2) rédiger un contrat d'intake, (3) estimer un volume, (4) lister les menaces d'une chaîne de collecte.
**Prérequis :** bases de Splunk. **Exercice associé :** `exercises/E0-architecture.md`.

## 🧠 Notions
**Le chemin d'un événement.** Pensez à un colis : *expéditeur* (source) → *point de dépôt* (collecte) → *transporteur* (transport) → *tri* (parsing) → *étiquetage* (enrichissement) → *aiguillage* (routage) → *entrepôt* (stockage). Un problème peut survenir à **chaque** étape ; diagnostiquer, c'est trouver l'étape.

**Agent, collecteur, API : quand utiliser quoi ?**
| Besoin | Choix | Pourquoi |
|---|---|---|
| Lire des fichiers ou journaux d'un serveur que vous administrez | **Agent (UF)** | léger, checkpoint, ACK |
| Recevoir du Syslog d'équipements réseau/sécurité | **Collecteur (syslog-ng)** | écoute des ports, tampon, route par émetteur |
| Interroger un service SaaS/cloud | **Poller → HEC** (ou add-on) | pagination, quotas, tokens |
| Recevoir des événements poussés par une application | **HEC direct** | simple, HTTPS |
| Router/filtrer avant l'indexeur, exécuter des scripts | **Heavy Forwarder** | parsing complet, mais lourd à exploiter |

**Index-time vs search-time.** *Index-time* = ce qui est figé **au moment de l'écriture** (découpage, `_time`, `host/source/sourcetype/index`, masquage, suppression). On ne peut pas « corriger » les événements déjà écrits. *Search-time* = ce qui est calculé **à la recherche** (extractions, alias, EVAL, lookups, tags) : rétroactif et réversible. **Règle : préférez le search-time ; n'utilisez l'index-time que si c'est indispensable.**

**Contrat d'intake.** Voir `docs/DATA-CONTRACT.md` : sans propriétaire, volume, SLO, tests, runbook et rollback, une source n'est pas « prête ».

## 🛠️ Pas à pas
### Étape 1 — Lire le dépôt comme un architecte (20 min)
1. Ouvrez `docs/ARCHITECTURE.md` et `docs/PORT-MATRIX.md`.
2. Sur papier, redessinez le flux **firewall** en notant, pour chaque flèche : protocole, port, qui initie la connexion, ce qui peut être perdu.
3. ✅ Vérifiez : votre schéma contient *syslog-ng*, un *fichier*, l'*UF*, le port *9997*. (UDP : perte possible ; TCP : non, sauf saturation ; S2S+ACK : non.)

### Étape 2 — Estimer un volume (30 min)
Formule : `volume/jour = événements/s × octets moyens × 86 400`.
```bash
# taille moyenne d'un événement du dataset
wc -c datasets/firewall.log | awk '{print $1}'      # octets totaux
wc -l datasets/firewall.log | awk '{print $1}'      # lignes
# moyenne ≈ totaux / lignes  → environ 190 octets
```
Exemple : 20 ev/s × 190 o × 86 400 ≈ **328 Mo/jour**. À 100 ev/s : ≈ 1,6 Go/jour. Splunk stocke grossièrement **~50 % du volume brut** (compression + index), *à mesurer* (voir M8).
✅ Calculez le volume pour 3 sources hypothétiques et comparez à votre disque (rétention 90 j).

### Étape 3 — Rédiger un contrat d'intake (45 min)
Copiez le tableau de `docs/DATA-CONTRACT.md` pour **une nouvelle source** (ex. logs d'un serveur web). Chaque ligne doit être **vérifiable** : « 95 % en < 120 s » est vérifiable ; « rapide » ne l'est pas.

### Étape 4 — Table de menaces (45 min)
Reprenez `docs/SECURITY.md`. Pour 5 menaces, ajoutez : *probabilité (1-3)*, *impact (1-3)*, *détection* (quelle requête SPL ou quel compteur la révélerait ?).

### Étape 5 — Choisir les ports et la matrice de flux (20 min)
Vérifiez qu'**aucun** port n'est exposé hors du réseau du lab et que le sens des connexions est correct (l'UF *initie* vers 9997 ; le poller *initie* vers 8088 ; les émetteurs Syslog *initient* vers 5514).

## ⚠️ Pièges
- Confondre *l'hôte qui écoute* et *celui qui initie* → pare-feu mal ouvert.
- Estimer le volume en lignes plutôt qu'en octets.
- Mettre une règle de parsing sur l'UF alors que **le premier composant qui parse** est l'indexeur.

## 📝 Auto-évaluation (réponses dans `instructor/ANSWER-KEY.md`)
1. Citez 3 réglages index-time et 3 réglages search-time.
2. Pourquoi ne met-on pas un UF « à l'écoute » du Syslog en production ?
3. Quel est le volume/jour de 150 ev/s à 220 octets ?
4. Donnez 3 éléments d'un contrat d'intake qui rendent un SLO *vérifiable*.
