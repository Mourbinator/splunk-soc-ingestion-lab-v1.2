#!/usr/bin/env python3
"""Envoie quelques événements de test au HTTP Event Collector (smoke test, M3).

Variables d'environnement (jamais dans Git) :
    SPLUNK_HEC_URL    ex. https://10.50.0.10:8088
    SPLUNK_HEC_TOKEN  le token créé dans Splunk Web

Exemple :
    python3 generators/hec_send.py --count 3 --index lab_api --insecure
"""
import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--index", default="lab_api")
    p.add_argument("--sourcetype", default="soc:api")
    p.add_argument("--insecure", action="store_true", help="n'autorise QUE pour un lab : ignore le certificat auto-signé")
    a = p.parse_args()

    url = os.environ.get("SPLUNK_HEC_URL", "").rstrip("/")
    token = os.environ.get("SPLUNK_HEC_TOKEN", "")
    if not url or not token:
        print("Définissez SPLUNK_HEC_URL et SPLUNK_HEC_TOKEN dans l'environnement.", file=sys.stderr)
        return 2
    ctx = ssl._create_unverified_context() if a.insecure else None
    payload = "\n".join(json.dumps({"time": time.time(), "host": "hec-smoke-test", "index": a.index,
                                    "sourcetype": a.sourcetype, "event": {"message": "hello hec", "seq": i}})
                        for i in range(1, a.count + 1)).encode()
    req = urllib.request.Request(url + "/services/collector/event", data=payload, method="POST",
                                 headers={"Authorization": f"Splunk {token}"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            print(r.status, r.read().decode())
            return 0
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode())
        return 1
    except urllib.error.URLError as e:
        print("Connexion impossible :", e.reason)
        return 1


if __name__ == "__main__":
    sys.exit(main())
