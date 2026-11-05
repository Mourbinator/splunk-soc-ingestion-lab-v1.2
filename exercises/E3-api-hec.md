# E3 — API/HEC : poller robuste
**Module :** M3 · **Durée :** 6 h · **Livrables :** `preuves/E3-*`, un patch de `poller.py` + test

1. **HEC manuel.** Reproduisez les 4 erreurs du tableau de M3 (étape 3) et remplissez le tableau « observé ».
2. **Conditions dégradées.** Lancez `mock_api.py --throttle-every 3 --fail-every 7 --retry-after 1`. Exécutez `poller.py --insecure --reset` vers HEC. Prouvez dans Splunk : `count=500`, `dc(event_id)=500`, et relevez `retried`, `http_429`, `http_5xx` dans les métriques.
3. **Reprise.** Interrompez le poller en plein vol (`Ctrl-C`) puis relancez : total final 500, 0 doublon. Montrez `state/checkpoint.json` avant/après.
4. **Dérive de position.** Vérifiez qu'en supprimant `next` du checkpoint (garder `seen_ids`) on n'envoie rien de plus. Que se passe-t-il si `seen_ids` est vidé **et** `next` supprimé ? (prédisez, testez, expliquez).
5. **Extension (code).** Ajoutez à `poller.py` une métrique `bytes_sent` (taille du payload HEC envoyé), puis un **test unitaire** dans `tests/test_poller.py` qui la vérifie. `python3 -m unittest discover -s tests -v` doit rester vert.
6. **Naïf vs robuste.** Lancez `poller_naive.py` avec le même mock. Listez **5** défauts et la correction de chacun dans `poller.py`.
7. **Secrets.** Vérifiez que ni token ni clé n'est dans Git (`git grep`), révoquez le token de test dans Splunk, créez-en un nouveau limité à l'index `saas`.
8. **(Bonus) ACK.** Créez un second token avec *indexer acknowledgment* : quels changements pour l'émetteur ? (canal, requête `/services/collector/ack`).

<details><summary>Indice (5)</summary>`hec_payload(...)` renvoie les octets envoyés : mesurez `len(payload)` dans `send_hec` avant l'appel.</details>
<details><summary>Indice (4)</summary>Sans mémoire des `event_id` ni position, le poller relit tout : doublons dans Splunk. D'où l'intérêt de **deux** protections.</details>

## Critères (35 pts)
1: 5 · 2: 6 · 3: 5 · 4: 4 · 5: 6 · 6: 5 · 7: 4 · bonus 4.
