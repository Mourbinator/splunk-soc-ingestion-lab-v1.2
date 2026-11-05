# M10 — Incidents et projet final (≈ 6 h)

## 🎯 Objectifs
Appliquer tout le cours : **diagnostiquer** une panne sans indice, la **prouver**, la **corriger**, **documenter**. Puis intégrer une **source nouvelle** de bout en bout.
**Prérequis :** M0–M9. **Exercices :** `exercises/incidents/INC-01…INC-10` et `exercises/E10-projet-final.md`.

## 🧠 La méthode en 6 temps
1. **Constater** : décrire le symptôme avec une mesure (*« 0 événement `network` depuis 14:05 »*, pas « ça ne marche pas »).
2. **Figer les preuves AVANT de toucher** : copie de la config, `btool`, captures, requêtes.
3. **Parcourir les couches** (`docs/DEPANNAGE.md`) de la source vers Splunk ; s'arrêter à la **première** couche fautive.
4. **Formuler une hypothèse** *testable* (« l'UF n'a pas le droit de lire le fichier »).
5. **Corriger une seule chose** à la fois et **prouver** le retour à la normale par des compteurs.
6. **Documenter** (`docs/POSTMORTEM-TEMPLATE.md`) et **prévenir** (alerte, test, doc).

## 🛠️ Pas à pas — comment dérouler un incident
1. Vérifiez l'état **sain** (`tests/ACCEPTANCE.md` « Smoke test »).
2. Un *binôme* (ou vous-même plus tard) exécute la section **« Injection »** de la fiche ; l'apprenant **ne lit pas** la suite.
3. L'apprenant applique la méthode, remplit le post-mortem.
4. Comparer avec `instructor/ANSWER-KEY.md` (cause, preuve, correctif, prévention).
5. Exécuter la section **« Retour à la normale »** avant l'incident suivant.
Barème : 40 % diagnostic (couches + preuves), 30 % correction, 20 % prévention, 10 % communication.

| INC | Thème | Couche concernée |
|---|---|---|
| 01 | Syslog n'arrive pas (mauvais port/protocole) | réseau / collecteur |
| 02 | UF muet : fichier illisible | fichier / droits |
| 03 | UF sans connexion à l'indexeur | transport |
| 04 | Événements perdus : index inexistant | routage / index |
| 05 | Mauvais sourcetype | métadonnées |
| 06 | Heures décalées (fuseau) | parsing |
| 07 | Pas de champs CIM / modèle vide | normalisation |
| 08 | Poller API : pages manquantes | API |
| 09 | HEC refuse (token/index) | API / sécurité |
| 10 | Événements multi-lignes éclatés | parsing |

## 🛠️ Projet final : intégrer une nouvelle source (journaux web « combined »)
**Livrables** : (1) contrat d'intake, (2) schéma, (3) config de collecte (UF + inputs), (4) TA `TA-soc-web` (props, transforms, eventtypes, tags CIM *Web*), (5) enrichissement (au moins 1 lookup), (6) 1 règle de routage ou de filtrage justifiée, (7) 3 recherches de qualité, (8) tests, (9) README + CHANGELOG, (10) un post-mortem sur une panne que vous avez provoquée.
Données : `datasets/web-access.log` (1000 lignes, format `combined`). Détails et barème : `exercises/E10-projet-final.md`.

## 📝 Auto-évaluation finale
Reprenez la liste de `docs/PARCOURS.md` (« Auto-évaluation finale »).
