#!/usr/bin/env python3
"""Ajoute des événements SSH synthétiques (format auth.log) à un fichier.

Exemple :
    mkdir -p /var/log/soc-lab/generated
    python3 generators/write_linux_logs.py --output /var/log/soc-lab/generated/auth-sim.log --count 50

Les horodatages utilisent l'heure LOCALE de la VM, comme le vrai syslog : sans année ni fuseau.
Cette particularité est volontaire (voir M4 et l'incident 06).
"""
import argparse
import datetime
import json
import random
import time
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--output", default="/var/log/soc-lab/generated/auth-sim.log")
    p.add_argument("--count", type=int, default=20)
    p.add_argument("--rate", type=float, default=10.0, help="lignes par seconde (0 = sans pause)")
    a = p.parse_args()

    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random()
    pause = (1.0 / a.rate) if a.rate > 0 else 0
    with out.open("a", encoding="utf-8") as f:
        for i in range(a.count):
            now = datetime.datetime.now()
            stamp = f"{now:%b} {now.day:2d} {now:%H:%M:%S}"
            user = rng.choice(["alice", "bob", "svc-backup", "root"])
            pid = 2000 + i
            if rng.random() < 0.25:
                line = f"{stamp} lab-linux sshd[{pid}]: Failed password for {user} from 192.0.2.{rng.randint(1, 254)} port {rng.randint(1024, 65535)} ssh2"
            else:
                line = f"{stamp} lab-linux sshd[{pid}]: Accepted publickey for {user} from 198.51.100.{rng.randint(1, 254)} port {rng.randint(1024, 65535)} ssh2"
            f.write(line + "\n")            # vrai saut de ligne
            f.flush()
            if pause:
                time.sleep(pause)
    print(json.dumps({"output": str(out), "written": a.count}))


if __name__ == "__main__":
    main()
