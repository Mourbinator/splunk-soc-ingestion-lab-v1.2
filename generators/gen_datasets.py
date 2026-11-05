#!/usr/bin/env python3
"""Génère les jeux de données synthétiques du lab (déterministes grâce à --seed).

Usage :
    python3 generators/gen_datasets.py                       # écrit dans ./datasets
    python3 generators/gen_datasets.py --start 2026-10-10T00:00:00+00:00 --seed 42

Toutes les IP sont réservées à la documentation (RFC 5737) et aucune donnée n'est réelle.
"""
import argparse
import datetime as dt
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPS = {443: "web browsing", 80: "web browsing", 8443: "web browsing",
        22: "secure shell", 53: "dns query", 3389: "remote desktop"}
PORTS = [443, 443, 443, 80, 22, 53, 53, 3389, 8443]
# Ces IP doivent exister dans addons/SA-soc-enrichment/lookups/soc_assets.csv
DEST_ASSETS = [10, 20, 21, 22, 30, 40, 50, 60]


def iso_z(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def fw_time(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S+0000")


def write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        shown = path.relative_to(ROOT)
    except ValueError:
        shown = path
    print(f"{shown}: {len(lines)} lignes")


def gen_firewall(rng, start, n):
    out = []
    for i in range(n):
        t = start + dt.timedelta(seconds=i)
        port = rng.choice(PORTS)
        proto = "udp" if (port == 53 and rng.random() < 0.9) else "tcp"
        r = rng.random()
        if port == 3389:
            action = "deny" if r < 0.7 else ("drop" if r < 0.85 else "allow")
        else:
            action = "allow" if r < 0.75 else ("deny" if r < 0.9 else "drop")
        dest = rng.choice(DEST_ASSETS) if rng.random() < 0.8 else rng.randint(1, 254)
        out.append(
            f'event_id=fw-ds0001-{i + 1:06d} event_time={fw_time(t)} '
            f'src_ip=192.0.2.{rng.randint(1, 254)} dest_ip=198.51.100.{dest} '
            f'src_port={rng.randint(1024, 65535)} dest_port={port} action={action} '
            f'protocol={proto} rule_id=LAB-{rng.randint(1, 20):02d} '
            f'bytes={rng.randint(60, 90000)} app="{APPS[port]}"')
    return out


def gen_firewall_anomalies(start):
    """Cas limites volontaires pour E4 (parsing) et E9 (qualité)."""
    def t(s):
        return fw_time(start + dt.timedelta(seconds=s))
    base = "src_ip=192.0.2.50 dest_ip=198.51.100.20 src_port=40000 dest_port=443 protocol=tcp rule_id=LAB-01"
    return [
        f"event_id=fw-an-0001 event_time={t(1)} {base}",                                  # action absente
        f"event_id=fw-an-0002 event_time={t(2)} dest_ip=198.51.100.20 src_port=40000 dest_port=443 action=allow protocol=tcp rule_id=LAB-01",  # src_ip absent
        f"event_id=fw-an-0003 event_time={t(3)} {base} action=reset",                      # action inconnue
        f"event_id=fw-an-0004 event_time=2026-10-10T00:00:04+9900 {base} action=allow",    # fuseau invalide
        f"event_id=fw-an-0005 event_time={t(5)} src_ip=2001:db8::10 dest_ip=2001:db8::20 src_port=40000 dest_port=443 action=allow protocol=tcp rule_id=LAB-01",  # IPv6
        f'event_id=fw-an-0006 event_time={t(6)} {base} action=allow app="a=b c d"',        # '=' dans une valeur citée
        f"event_id=fw-an-0007 event_time={t(7)} {base} action=allow",
        f"event_id=fw-an-0007 event_time={t(7)} {base} action=allow",                      # doublon exact
        f"event_id=fw-an-0009 {base} action=deny",                                         # event_time absent
        f"event_id=fw-an-0010 event_time={t(10)} src_ip=192.0.2.50 dest_ip=198.51.100.20 src_port=40000 dest_port=443 action=allow protocol=TCP rule_id=LAB-01",  # protocole en majuscules
        f"event_id=fw-an-0011 event_time={t(11)} {base} action=allow geo=FR",              # champ inconnu
        f"event_id=fw-an-0012 event_time={t(12)} src_ip=192.0.2.50 dest_ip=198.51.100.20 src_port=40000 dest_port=70000 action=allow protocol=tcp rule_id=LAB-01",  # port hors plage
        '{"event_id":"fw-an-0013","time":"2026-10-10T00:00:13Z","src":"192.0.2.50","dst":"198.51.100.20","verdict":"allow"}',  # dérive de format (JSON)
        f"fw-an-0014 {t(14)} 192.0.2.50 198.51.100.20 40000 443 allow tcp LAB-01",         # dérive de format (colonnes)
    ]


def ssh_line(ts, pid, kind, user, ip, port):
    stamp = f"{ts:%b} {ts.day:2d} {ts:%H:%M:%S}"
    if kind == "fail":
        return f"{stamp} lab-linux sshd[{pid}]: Failed password for {user} from {ip} port {port} ssh2"
    if kind == "fail_invalid":
        return f"{stamp} lab-linux sshd[{pid}]: Failed password for invalid user {user} from {ip} port {port} ssh2"
    if kind == "invalid":
        return f"{stamp} lab-linux sshd[{pid}]: Invalid user {user} from {ip} port {port}"
    if kind == "ok":
        return f"{stamp} lab-linux sshd[{pid}]: Accepted publickey for {user} from {ip} port {port} ssh2"
    if kind == "session":
        return f"{stamp} lab-linux sshd[{pid}]: pam_unix(sshd:session): session opened for user {user}(uid=1001) by (uid=0)"
    if kind == "sudo":
        return f"{stamp} lab-linux sudo:    {user} : TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND=/usr/bin/apt update"
    raise ValueError(kind)


def gen_linux(rng, start, n_base):
    users = ["alice", "bob", "svc-backup", "root"]
    events = []
    for i in range(n_base):
        ts = start + dt.timedelta(seconds=3 * i)
        kind = rng.choices(["fail", "ok", "invalid", "sudo", "session", "fail_invalid"], [30, 35, 10, 10, 10, 5])[0]
        user = "admin" if kind in ("invalid", "fail_invalid") else rng.choice(users)
        net = "192.0.2" if kind in ("fail", "invalid", "fail_invalid") else "198.51.100"
        events.append((ts, kind, user, f"{net}.{rng.randint(1, 254)}", rng.randint(1024, 65535)))
    # Brute force : 40 échecs en 40 s depuis 192.0.2.99 puis un succès (utile pour les détections)
    b0 = start + dt.timedelta(seconds=600)
    for k in range(40):
        events.append((b0 + dt.timedelta(seconds=k), "fail", "root", "192.0.2.99", 50000 + k))
    events.append((b0 + dt.timedelta(seconds=41), "ok", "root", "192.0.2.99", 50041))
    events.sort(key=lambda e: e[0])
    return [ssh_line(ts, 2000 + i, kind, user, ip, port) for i, (ts, kind, user, ip, port) in enumerate(events)]


def gen_multiline(rng, start, n):
    svcs = ["auth-svc", "payment-svc", "orders-svc", "inventory-svc"]
    out = []
    for i in range(n):
        t = start + dt.timedelta(seconds=2 * i, milliseconds=rng.randint(0, 999))
        stamp = t.strftime("%Y-%m-%d %H:%M:%S") + f",{t.microsecond // 1000:03d}"
        svc = rng.choice(svcs)
        r = rng.random()
        if r < 0.22:
            out += [
                f"{stamp} ERROR [{svc}] Unhandled exception processing order=ORD-{1000 + i}",
                "java.lang.IllegalStateException: Payment gateway timeout after 3000 ms",
                "\tat com.lab.payment.GatewayClient.charge(GatewayClient.java:142)",
                "\tat com.lab.payment.OrderService.process(OrderService.java:88)",
                "\tat com.lab.web.OrderController.post(OrderController.java:51)",
                "Caused by: java.net.SocketTimeoutException: Read timed out",
                "\tat java.base/java.net.SocketInputStream.read(SocketInputStream.java:186)",
            ]
        elif r < 0.35:
            out.append(f"{stamp} DEBUG [{svc}] login attempt user=alice password=P@ssw0rd-LAB from=192.0.2.{rng.randint(1, 254)}")
        elif r < 0.45:
            out.append(f"{stamp} DEBUG [{svc}] outbound call Authorization: Bearer lab.fake.token-{i:04d} status=200")
        elif r < 0.6:
            out.append(f"{stamp} WARN [{svc}] slow response {rng.randint(800, 3000)} ms")
        else:
            out.append(f"{stamp} INFO [{svc}] request ok user=bob duration={rng.randint(5, 300)}ms")
    return out


def gen_web(rng, start, n):
    paths = ["/", "/index.html", "/login", "/api/v1/items", "/static/app.js", "/admin", "/search?q=lab"]
    uas = ["Mozilla/5.0 (X11; Linux x86_64)", "curl/8.5.0", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"]
    out = []
    for i in range(n):
        t = start + dt.timedelta(seconds=i)
        status = rng.choices([200, 301, 304, 403, 404, 500], [70, 5, 8, 5, 8, 4])[0]
        stamp = t.strftime("%d/%b/%Y:%H:%M:%S +0000")
        verb = rng.choice(["GET", "GET", "POST"])
        out.append(f'192.0.2.{rng.randint(1, 254)} - - [{stamp}] "{verb} {rng.choice(paths)} HTTP/1.1" '
                   f'{status} {rng.randint(100, 50000)} "-" "{rng.choice(uas)}"')
    return out


def jl(rows):
    return [json.dumps(r, separators=(",", ":")) for r in rows]


def gen_aws(rng, start, n):
    names = [("s3.amazonaws.com", "GetObject"), ("s3.amazonaws.com", "PutObject"), ("signin.amazonaws.com", "ConsoleLogin"),
             ("iam.amazonaws.com", "CreateAccessKey"), ("iam.amazonaws.com", "AttachUserPolicy"), ("s3.amazonaws.com", "DeleteBucket")]
    rows = []
    for i in range(n):
        src, name = rng.choice(names)
        row = {"eventVersion": "1.08", "eventTime": iso_z(start + dt.timedelta(seconds=3 * i)), "eventSource": src,
               "eventName": name, "awsRegion": rng.choice(["us-east-1", "eu-west-3"]),
               "sourceIPAddress": f"192.0.2.{rng.randint(1, 254)}",
               "userIdentity": {"type": "IAMUser", "userName": rng.choice(["lab-user", "lab-admin", "svc-ci"])},
               "requestID": f"lab-aws-{i + 1:04d}"}
        if rng.random() < 0.08:
            row["errorCode"] = "AccessDenied"
        rows.append(row)
    return jl(rows)


def gen_azure(rng, start, n):
    ops = ["Microsoft.Storage/storageAccounts/listKeys/action", "Microsoft.Authorization/roleAssignments/write",
           "Microsoft.Compute/virtualMachines/start/action", "Microsoft.Network/networkSecurityGroups/write"]
    rows = [{"time": iso_z(start + dt.timedelta(seconds=3 * i)), "operationName": rng.choice(ops), "category": "Administrative",
             "caller": rng.choice(["lab.user@example.invalid", "lab.admin@example.invalid"]),
             "resourceId": "/subscriptions/lab/resourceGroups/rg-lab/providers/Microsoft.Storage/storageAccounts/labstore",
             "correlationId": f"lab-az-{i + 1:04d}", "status": rng.choice(["Succeeded", "Succeeded", "Failed"])} for i in range(n)]
    return jl(rows)


def gen_gcp(rng, start, n):
    methods = ["google.iam.admin.v1.CreateServiceAccountKey", "storage.objects.get", "compute.instances.insert", "SetIamPolicy"]
    rows = [{"timestamp": iso_z(start + dt.timedelta(seconds=4 * i)), "insertId": f"lab-gcp-{i + 1:04d}",
             "logName": "projects/lab/logs/cloudaudit.googleapis.com%2Factivity",
             "protoPayload": {"methodName": rng.choice(methods),
                              "authenticationInfo": {"principalEmail": rng.choice(["lab@example.invalid", "svc@example.invalid"])}}}
            for i in range(n)]
    return jl(rows)


def gen_m365(rng, start, n):
    ops = [("UserLoggedIn", "AzureActiveDirectory"), ("UserLoginFailed", "AzureActiveDirectory"),
           ("FileAccessed", "SharePoint"), ("MailItemsAccessed", "Exchange")]
    rows = []
    for i in range(n):
        op, wl = rng.choice(ops)
        rows.append({"CreationTime": iso_z(start + dt.timedelta(seconds=3 * i)), "Operation": op,
                     "UserId": rng.choice(["lab.user@example.invalid", "lab.admin@example.invalid"]), "Workload": wl,
                     "ResultStatus": "Failed" if op == "UserLoginFailed" else "Success",
                     "ClientIP": f"192.0.2.{rng.randint(1, 254)}", "Id": f"lab-m365-{i + 1:04d}"})
    return jl(rows)


def gen_saas(rng, start, n):
    actions = ["login_ok", "login_failed", "api_token_created", "file_shared", "user_invited"]
    rows = [{"event_time": iso_z(start + dt.timedelta(seconds=2 * i)), "actor": rng.choice(["lab-user", "lab-admin", "lab-svc"]),
             "action": rng.choice(actions), "source_ip": f"192.0.2.{rng.randint(1, 254)}", "target": "lab-app",
             "event_id": f"saas-{i + 1:04d}"} for i in range(n)]
    return jl(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "datasets"))
    ap.add_argument("--start", default="2026-10-10T00:00:00+00:00")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    out = Path(a.out)
    start = dt.datetime.fromisoformat(a.start)
    rng = random.Random(a.seed)
    write(out / "firewall.log", gen_firewall(rng, start, 2000))
    write(out / "firewall-anomalies.log", gen_firewall_anomalies(start))
    write(out / "linux-auth.log", gen_linux(rng, start, 520))
    write(out / "app-multiline.log", gen_multiline(rng, start, 150))
    write(out / "web-access.log", gen_web(rng, start, 1000))
    write(out / "aws-cloudtrail.jsonl", gen_aws(rng, start, 300))
    write(out / "azure-activity.jsonl", gen_azure(rng, start, 300))
    write(out / "gcp-audit.jsonl", gen_gcp(rng, start, 200))
    write(out / "m365-audit.jsonl", gen_m365(rng, start, 300))
    write(out / "saas-audit.jsonl", gen_saas(rng, start, 500))


if __name__ == "__main__":
    main()
