#!/usr/bin/env python3
"""POLLER VOLONTAIREMENT DÉFAILLANT — support de l'incident 08. Ne pas utiliser en vrai.

Défauts : ignore Retry-After, ne réessaie pas, saute la page en cas d'erreur, pas de checkpoint,
pas de déduplication, pas de métriques d'erreur. Comptez ce qu'il récupère : le résultat est < 500.
"""
import json
import os
import urllib.error
import urllib.request

base = os.environ.get("API_BASE_URL", "http://127.0.0.1:8081")
key = os.environ.get("API_KEY", "lab-mock-key")
total, cursor = 0, 0
while cursor < 500:
    req = urllib.request.Request(f"{base}/events?cursor={cursor}&limit=100", headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            total += len(json.loads(r.read())["items"])
    except urllib.error.HTTPError as e:
        print(f"page cursor={cursor} : HTTP {e.code} (ignorée !)")
    cursor += 100
print("événements récupérés :", total, "/ 500 attendus")
