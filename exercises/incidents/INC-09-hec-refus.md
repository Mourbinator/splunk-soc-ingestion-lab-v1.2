# INC-09 — « Le poller dit fatal : HEC refuse »
**Couche visée :** API / sécurité. **Durée :** 45 min.

## Injection (formateur)
```bash
export SPLUNK_HEC_TOKEN='token-faux'                                  # cas A
python3 collectors/api/poller.py --insecure --reset                    # → fatal HEC 403
export SPLUNK_HEC_TOKEN='<le vrai token>'                              # cas B
python3 collectors/api/poller.py --insecure --reset --index main       # → fatal HEC 400 (index interdit pour le token)
```
## Symptôme
Le poller s'arrête avec un message `[fatal] HEC …`.

## Méthode guidée
1. Lisez le message : code **HTTP** et corps (`code` HEC).
2. **Cas A (403)** : token invalide/désactivé. Vérifiez dans Splunk (*Settings → HEC*) et dans l'environnement (`echo` du début du token seulement).
3. **Cas B (400)** : index non autorisé. Comparez *Allowed indexes* du token avec `--index`.
4. **Pourquoi `fatal` et pas `retry` ?** Réessayer ne changera rien ; 503 seul est réessayable.
5. **Vérifiez** que le checkpoint **n'a pas avancé** : `state/checkpoint.json` absent ou inchangé. Pourquoi est-ce essentiel ?
6. **Correction** : bon token, bon index ; relance → 500 événements.
7. **Prévention** : un token par usage, index autorisés minimaux, rotation, alerte Q11, **pas** de token dans l'historique Git.

<details><summary>Indice</summary>Le tableau des codes HEC est dans `modules/M3-api-hec.md`.</details>

**Livrable :** post-mortem + tableau code → cause → action.
## Retour à la normale
Restaurez la variable avec le bon token ; supprimez `state/checkpoint.json` si nécessaire.
