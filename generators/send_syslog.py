#!/usr/bin/env python3
"""Envoie des messages Syslog RFC 5424 synthétiques (firewall) en UDP ou TCP.

Exemples :
    python3 generators/send_syslog.py --host 10.50.0.40 --port 5514 --count 100
    python3 generators/send_syslog.py --host 10.50.0.40 --port 5514 --count 100 --tcp
    python3 generators/send_syslog.py --count 10 --app other-app        # test de routage (M7)

Le script affiche un résumé JSON : CONSERVEZ-LE, il sert de compteur source pour comparer
« généré / reçu par le collecteur / indexé par Splunk ».
Format du message : <PRI>1 TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
(le champ STRUCTURED-DATA vaut '-' quand il est vide : il faut donc trois '-' avant le message).
"""
import argparse
import datetime
import json
import random
import socket
import sys
import time


def build_message(app, hostname, run_id, seq, rng):
    now = datetime.datetime.now(datetime.timezone.utc)
    hdr_ts = now.isoformat(timespec="seconds")                 # RFC 3339 : 2026-10-19T10:00:00+00:00
    ev_ts = now.strftime("%Y-%m-%dT%H:%M:%S%z")                # format du contrat : 2026-10-19T10:00:00+0000
    head = f"<134>1 {hdr_ts} {hostname} {app} - - -"
    if app == "soc-firewall":
        body = (f"event_id=fw-{run_id}-{seq:06d} event_time={ev_ts} "
                f"src_ip=192.0.2.{rng.randint(1, 254)} dest_ip=198.51.100.{rng.choice([10, 20, 21, 22, 30, 40, 50, 60])} "
                f"src_port={rng.randint(1024, 65535)} dest_port={rng.choice([22, 53, 80, 443, 3389])} "
                f"action={rng.choice(['allow', 'allow', 'allow', 'deny', 'drop'])} "
                f"protocol={rng.choice(['tcp', 'udp'])} rule_id=LAB-{rng.randint(1, 20):02d} "
                f"bytes={rng.randint(60, 90000)} app=\"web browsing\"")
    else:
        body = f"msg_id={run_id}-{seq:06d} message=\"hello from {app}\""
    return f"{head} {body}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5514)
    p.add_argument("--count", type=int, default=10)
    p.add_argument("--tcp", action="store_true", help="TCP au lieu d'UDP")
    p.add_argument("--app", default="soc-firewall", help="APP-NAME syslog (sert au routage côté collecteur)")
    p.add_argument("--hostname", default="firewall01", help="HOSTNAME dans l'en-tête syslog")
    p.add_argument("--rate", type=float, default=20.0, help="événements par seconde (0 = sans pause)")
    p.add_argument("--run-id", default=None, help="identifiant de lot (6 caractères) ; aléatoire par défaut")
    a = p.parse_args()

    rng = random.Random()
    run_id = a.run_id or f"{rng.randrange(16**6):06x}"
    sock_type = socket.SOCK_STREAM if a.tcp else socket.SOCK_DGRAM
    pause = (1.0 / a.rate) if a.rate > 0 else 0
    sent = 0
    with socket.socket(socket.AF_INET, sock_type) as s:
        if a.tcp:
            s.connect((a.host, a.port))
        for i in range(1, a.count + 1):
            msg = build_message(a.app, a.hostname, run_id, i, rng)
            if a.tcp:
                s.sendall(msg.encode("utf-8") + b"\n")      # vrai saut de ligne (octet 0x0A)
            else:
                s.sendto(msg.encode("utf-8"), (a.host, a.port))
            sent += 1
            if pause:
                time.sleep(pause)
    print(json.dumps({"run_id": run_id, "app": a.app, "proto": "tcp" if a.tcp else "udp",
                      "sent": sent, "first_event_id": f"fw-{run_id}-000001", "last_event_id": f"fw-{run_id}-{sent:06d}"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
