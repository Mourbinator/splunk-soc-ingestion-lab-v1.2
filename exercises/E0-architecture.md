# E0 — Architecture, contrat d'intake, menaces, volumétrie
**Module :** M0 · **Durée :** 3 h · **Livrables :** `preuves/E0-schema.png|md`, `preuves/E0-contrat.md`, `preuves/E0-menaces.md`, `preuves/E0-volumes.md`

**Scénario.** L'équipe Web (fictive) veut intégrer les journaux d'un serveur **nginx** dans le SOC : ~60 requêtes/s en journée, 20 la nuit, ~210 octets par ligne, format « combined ».

## Étapes
1. **Schéma.** Dessinez la chaîne complète (source → stockage) pour ces journaux : choix agent/collecteur/API ? où parse-t-on ? quels ports ? Justifiez en 3 lignes.
2. **Volume.** Calculez le volume brut/jour (jour 12 h à 60/s + nuit 12 h à 20/s) et le disque pour 90 jours à 50 %. Montrez vos calculs.
3. **Contrat d'intake.** Reprenez `docs/DATA-CONTRACT.md` et remplissez **toutes** les lignes pour cette source (propriétaire, SLO chiffrés, tests, runbook, rollback…).
4. **Menaces.** Tableau de 6 menaces : description, probabilité (1-3), impact (1-3), contre-mesure, **détection** (une requête SPL ou un compteur).
5. **Relecture croisée.** Relisez votre contrat avec la question : « une personne qui ne me connaît pas pourrait-elle *vérifier* chaque ligne ? »

<details><summary>Indice 1</summary>Une ligne de contrat est valide si on peut l'écrire sous forme de test (SPL, commande, seuil).</details>
<details><summary>Indice 2</summary>Volume/jour = Σ (événements/s × durée en s × octets).</details>
<details><summary>Indice 3</summary>(60×43200 + 20×43200) × 210 ≈ 725 Mo/jour brut ; ×90 j × 0,5 ≈ 32,7 Go.</details>

## Critères de réussite (20 pts)
| Critère | Pts |
|---|---:|
| Schéma complet, choix justifiés, ports/sens corrects | 5 |
| Calculs justes et expliqués | 4 |
| Contrat : 0 ligne vague, SLO mesurables | 6 |
| Menaces avec détection concrète | 5 |
