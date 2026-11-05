# Post-mortem d'incident d'ingestion (modèle)

**Incident :** (n° et titre) · **Date/heure début-fin :** · **Auteur :**

1. **Résumé** (3 phrases : quoi, impact, durée).
2. **Impact** : quelles sources/index, combien d'événements perdus ou faux, qui est affecté.
3. **Chronologie** : heure — constat — preuve (commande/requête + extrait de résultat).
4. **Diagnostic par couche** : tableau couche → vérifié ? → résultat (voir `DEPANNAGE.md`).
5. **Cause racine** (une seule phrase factuelle) et **facteurs contributifs**.
6. **Correction appliquée** (fichier, ligne avant/après) et **preuve de retour à la normale** (compteurs, SPL).
7. **Récupération des données** (rejeu, réingestion, perte acceptée ?).
8. **Actions préventives** : alerte à créer, test à ajouter, documentation à corriger — avec responsable et échéance.
9. **Ce qui a bien/mal fonctionné** dans la détection et la réponse.

Règle : décrire des **faits et des systèmes**, jamais chercher un coupable.
