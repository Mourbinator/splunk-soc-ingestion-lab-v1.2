"""Simule en Python les regex des TA sur les jeux de données (approximation de Splunk/PCRE, pas un test Splunk).
python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def conf_stanzas(path):
    out, cur = {}, None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            cur = out.setdefault(line[1:-1], {})
        elif "=" in line and cur is not None:
            k, v = line.split("=", 1)
            cur[k.strip()] = v.strip()
    return out


def kv_extract(line, transforms):
    fields = {}
    for name in ("soc_firewall_kv_quoted", "soc_firewall_kv_plain"):
        for m in re.finditer(transforms[name]["REGEX"], line):
            fields.setdefault(m.group(1), m.group(2))
    return fields


class FirewallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = conf_stanzas(ROOT / "addons/TA-soc-firewall/default/transforms.conf")
        cls.p = conf_stanzas(ROOT / "addons/TA-soc-firewall/default/props.conf")["soc:firewall"]

    def test_all_required_fields_extracted_on_main_dataset(self):
        required = ["event_id", "event_time", "src_ip", "dest_ip", "src_port", "dest_port", "action", "protocol", "rule_id"]
        lines = (ROOT / "datasets/firewall.log").read_text().splitlines()
        self.assertEqual(len(lines), 2000)
        for ln in lines:
            f = kv_extract(ln, self.t)
            for k in required:
                self.assertIn(k, f, ln)
            self.assertNotIn('"', f["app"])          # guillemets retirés

    def test_syslog_ng_prefixed_line(self):
        ln = '2026-10-19T10:00:00+00:00 firewall01 event_id=fw-abc123-000001 event_time=2026-10-19T10:00:00+0000 src_ip=192.0.2.1 dest_ip=198.51.100.10 src_port=1234 dest_port=443 action=allow protocol=tcp rule_id=LAB-01 bytes=10 app="web browsing"'
        f = kv_extract(ln, self.t)
        self.assertEqual((f["event_id"], f["app"], f["action"]), ("fw-abc123-000001", "web browsing", "allow"))

    def test_timestamp_prefix_and_format(self):
        import datetime as dt
        prefix = re.compile(self.p["TIME_PREFIX"])
        ln = (ROOT / "datasets/firewall.log").read_text().splitlines()[0]
        m = prefix.search(ln)
        ts = ln[m.end():m.end() + 24]
        self.assertEqual(dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").isoformat(), "2026-10-10T00:00:00+00:00")

    def test_anomalies_behave_as_documented(self):
        an = (ROOT / "datasets/firewall-anomalies.log").read_text().splitlines()
        f1 = kv_extract(an[0], self.t); self.assertNotIn("action", f1)                  # action absente
        f6 = kv_extract(an[5], self.t); self.assertEqual(f6["app"], "a=b c d")           # '=' dans la valeur citée
        f13 = kv_extract(an[12], self.t); self.assertEqual(f13, {})                      # JSON : rien extrait
        ids = [kv_extract(x, self.t).get("event_id") for x in an]
        self.assertEqual(ids.count("fw-an-0007"), 2)                                     # doublon exact


class OtherTaTests(unittest.TestCase):
    def test_linux_ssh_regex(self):
        p = conf_stanzas(ROOT / "addons/TA-soc-linux/default/props.conf")["linux:auth"]
        rx_ok = re.compile(p["EXTRACT-soc_ssh_result"].replace("(?<", "(?P<"))
        rx_inv = re.compile(p["EXTRACT-soc_ssh_invalid"].replace("(?<", "(?P<"))
        lines = (ROOT / "datasets/linux-auth.log").read_text().splitlines()
        self.assertEqual(len(lines), 561)
        hits = sum(1 for ln in lines if ("Failed" in ln or "Accepted" in ln) and rx_ok.search(ln))
        expected = sum(1 for ln in lines if "Failed password" in ln or "Accepted publickey" in ln)
        self.assertEqual(hits, expected)
        self.assertTrue(all(rx_inv.search(ln) for ln in lines if "Invalid user" in ln))
        m = rx_ok.search("Oct 10 00:00:03 lab-linux sshd[2003]: Failed password for invalid user admin from 192.0.2.11 port 51517 ssh2")
        self.assertEqual((m["user"], m["src"], m["src_port"]), ("admin", "192.0.2.11", "51517"))

    def test_multiline_breaker_makes_150_events(self):
        p = conf_stanzas(ROOT / "addons/TA-soc-app/default/props.conf")["soc:app"]
        text = (ROOT / "datasets/app-multiline.log").read_text()
        events = re.split(p["LINE_BREAKER"].replace("([\\r\\n]+)", "[\\r\\n]+", 1), text.strip("\n"))
        self.assertEqual(len(events), 150)
        self.assertTrue(any("Caused by" in e and e.count("\n") >= 6 for e in events))

    def test_json_datasets_are_valid_and_have_time_key(self):
        import json
        keys = {"aws-cloudtrail": "eventTime", "azure-activity": "time", "gcp-audit": "timestamp",
                "m365-audit": "CreationTime", "saas-audit": "event_time"}
        for name, key in keys.items():
            for ln in (ROOT / f"datasets/{name}.jsonl").read_text().splitlines():
                self.assertIn(key, json.loads(ln))

    def test_lookup_covers_generated_assets_and_rules(self):
        import csv
        assets = {r["ip"] for r in csv.DictReader((ROOT / "addons/SA-soc-enrichment/lookups/soc_assets.csv").read_text().splitlines())}
        for n in (10, 20, 21, 22, 30, 40, 50, 60):
            self.assertIn(f"198.51.100.{n}", assets)
        rules = {r["rule_id"] for r in csv.DictReader((ROOT / "addons/SA-soc-enrichment/lookups/soc_fw_rules.csv").read_text().splitlines())}
        self.assertEqual(rules, {f"LAB-{i:02d}" for i in range(1, 21)})


class RoutingSolutionTests(unittest.TestCase):
    """Vérifie en Python les regex du corrigé E7 (instructor/solutions/soc_routing)."""

    @classmethod
    def setUpClass(cls):
        base = ROOT / "instructor/solutions/soc_routing/default"
        cls.t = conf_stanzas(base / "transforms.conf")
        cls.p = conf_stanzas(base / "props.conf")

    def line(self, port, action, host="firewall01"):
        return (f"2026-10-19T10:00:00+00:00 {host} event_id=fw-abc123-000001 event_time=2026-10-19T10:00:00+0000 "
                f"src_ip=192.0.2.1 dest_ip=198.51.100.21 src_port=1234 dest_port={port} action={action} protocol=tcp "
                f"rule_id=LAB-01 bytes=10 app=\"x\"")

    def test_drop_only_dns_allow(self):
        rx = re.compile(self.t["soc_drop_dns_allow"]["REGEX"], re.S)
        self.assertTrue(rx.search(self.line(53, "allow")))
        self.assertFalse(rx.search(self.line(53, "deny")))
        self.assertFalse(rx.search(self.line(443, "allow")))

    def test_host_rewrite_and_rdp_route(self):
        m = re.search(self.t["soc_set_host_from_line"]["REGEX"], self.line(443, "allow", host="firewall07"))
        self.assertEqual(m.group(1), "firewall07")
        rx = re.compile(self.t["soc_route_rdp_to_security"]["REGEX"])
        self.assertTrue(rx.search(self.line(3389, "deny")))
        self.assertFalse(rx.search(self.line(33890, "deny")))

    def test_pipeline_order_puts_filter_first(self):
        order = [x.strip() for x in self.p["soc:firewall"]["TRANSFORMS-soc_pipeline"].split(",")]
        self.assertEqual(order[0], "soc_drop_dns_allow")

    def test_sedcmd_masks_secrets_in_dataset(self):
        text = (ROOT / "datasets/app-multiline.log").read_text()
        self.assertIn("password=P@ssw0rd-LAB", text)
        text = re.sub(r"password=\S+", "password=********", text)
        text = re.sub(r"Bearer\s+\S+", "Bearer ********", text)
        self.assertNotIn("P@ssw0rd-LAB", text)
        self.assertNotIn("lab.fake.token", text)


if __name__ == "__main__":
    unittest.main()
