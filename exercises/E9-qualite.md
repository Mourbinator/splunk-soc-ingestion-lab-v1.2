# E9 — Qualité et supervision
**Module :** M9 · **Durée :** 7 h · **Livrables :** 8 contrôles documentés, 1 alerte, 1 tableau de bord

1. **Choisir 8 contrôles** parmi Q01–Q14 couvrant **les 7 dimensions** (volume, fraîcheur, retard, complétude, unicité, validité, dérive). Pour chacun : objectif, SPL, seuil, action attendue.
2. **Valider chaque contrôle** avec un cas **sain** et un cas **en défaut** que *vous provoquez* (ex. arrêt UF pour la fraîcheur, lot en double pour l'unicité).
3. **Alerte « source silencieuse »** (M9 étape 8), avec throttle, destinataire fictif, fiche de réponse (3 actions).
4. **Alerte « trou de séquence »** : déclenche si `missing>0` sur un lot **terminé** depuis 5 min (évitez les faux positifs d'un lot en cours).
5. **Tableau de bord** avec 5 panneaux et seuils colorés.
6. **Faux positifs.** Listez 5 situations où vos alertes se déclencheraient à tort et l'ajustement (fenêtres, exclusions, seuils adaptatifs).
7. **Revue.** Relisez `docs/DATA-CONTRACT.md` : chaque SLO est-il couvert par un contrôle ? Complétez le tableau SLO → recherche.

<details><summary>Indice (4)</summary>Un lot « terminé » = dernier événement du lot plus vieux que 5 minutes : `eval age=now()-latest(_time)` dans le `stats` par `run`.</details>

## Critères (35 pts)
1: 7 · 2: 8 · 3: 5 · 4: 5 · 5: 4 · 6: 3 · 7: 3.
