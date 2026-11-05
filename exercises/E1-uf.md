# E1 — Agent UF : ajouter une source, prouver la reprise, diagnostiquer
**Module :** M1 · **Durée :** 6 h · **Livrables :** `preuves/E1-*.txt|png`

## Partie A — Ajouter une nouvelle source (≈ 2 h)
1. Sur la VM, créez le dossier `/var/log/soc-lab/custom` et un fichier `/var/log/soc-lab/custom/maintenance.log` avec 10 lignes de votre choix.
2. Dans **l'app** `soc_uf_linux` (pas dans `system/local`), ajoutez un `[monitor://…/custom]` : index `linux`, sourcetype `linux:syslog`, `whitelist = \.log$`.
3. Validez avec `btool` que **votre** stanza est effective et trouvez la ligne qui l'annonce.
4. Redémarrez l'UF et prouvez dans Splunk : `index=linux source=*maintenance.log | stats count` = 10.
5. Ajoutez 5 lignes → 15. Redémarrez l'UF → toujours 15 (checkpoint).

## Partie B — Rotation et ré-ingestion (≈ 1 h)
6. Renommez le fichier (`mv maintenance.log maintenance.log.1`) puis recréez `maintenance.log` avec 3 **nouvelles** lignes. Combien d'événements attendez-vous ? Vérifiez : justifiez le résultat (le `.log.1` est-il relu ? pourquoi ?).
7. Recréez `maintenance.log` avec **exactement les mêmes** 10 premières lignes qu'au départ. Que se passe-t-il ? (indice : CRC des premiers octets).

## Partie C — Panne contrôlée (≈ 1 h 30)
8. Arrêtez Splunk côté Windows, générez 100 lignes SSH (`write_linux_logs.py --count 100 --rate 0`), relancez Splunk. Prouvez : +100, 0 doublon. Quel réglage l'a permis ?

## Partie D — Diagnostic d'un UF muet (≈ 1 h 30)
9. Un binôme (ou vous plus tard) modifie une chose parmi : `disabled = 1`, mauvais chemin, utilisateur sans droit, mauvais index, mauvaise IP de sortie. Suivez la méthode `docs/DEPANNAGE.md` et nommez la cause avec **deux preuves** (une côté UF, une côté Splunk).

## Partie E — (Bonus) Deployment Server
10. Faites déployer `soc_uf_linux` par le DS plutôt que par copie manuelle (M1, étape 10). Prouvez la version déployée (`splunk btool inputs list --debug`).

<details><summary>Indice 1 (partie B)</summary>Le monitor suit un **fichier** par son contenu (début) et sa position, pas par son nom. Un fichier renommé n'est pas relu s'il est déjà connu.</details>
<details><summary>Indice 2 (partie D)</summary>`splunk list monitor`, `splunk list inputstatus`, `splunkd.log` de l'UF, `index=_internal host=<vm>`.</details>

## Critères (30 pts)
A : 8 · B : 6 (explications justes) · C : 6 · D : 7 (2 preuves, cause exacte) · E : bonus 3.
