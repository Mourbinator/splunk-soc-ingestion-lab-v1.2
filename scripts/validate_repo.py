#!/usr/bin/env python3
"""Valide la cohérence du dépôt (hors Splunk). Code de sortie 0 = OK.

Contrôles : fichiers obligatoires · syntaxe des .conf Splunk · références (REPORT/TRANSFORMS/LOOKUP/tags) ·
index et sourcetypes des inputs · compilation Python · liens et chemins cités dans la documentation ·
secrets · datasets (comptes + génération déterministe).
"""
import filecmp
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors, warnings = [], []


def err(msg):
    errors.append(msg)


def rel(p):
    return p.relative_to(ROOT).as_posix()


REQUIRED = """README.md CHANGELOG.md LICENSE .gitignore
docs/PARCOURS.md docs/ARCHITECTURE.md docs/DATA-CONTRACT.md docs/GLOSSAIRE.md docs/DEPANNAGE.md docs/POSTMORTEM-TEMPLATE.md
docs/INSTALL-SPLUNK-WINDOWS.md docs/INSTALL-UBUNTU.md docs/IP-PLAN.md docs/PORT-MATRIX.md docs/SECURITY.md docs/SOURCETYPES.md
modules/M0-architecture.md modules/M1-agents-uf.md modules/M2-syslog-collecteur.md modules/M3-api-hec.md modules/M4-parsing.md
modules/M5-normalisation-cim.md modules/M6-enrichissement.md modules/M7-routage.md modules/M8-ingestion-stockage.md
modules/M9-qualite.md modules/M10-incidents-projet.md
exercises/README.md exercises/E0-architecture.md exercises/E1-uf.md exercises/E2-syslog.md exercises/E3-api-hec.md exercises/E4-parsing.md
exercises/E5-normalisation.md exercises/E6-enrichissement.md exercises/E7-routage.md exercises/E8-ingestion-stockage.md
exercises/E9-qualite.md exercises/E10-projet-final.md
exercises/incidents/INC-01-syslog-port.md exercises/incidents/INC-02-fichier-illisible.md exercises/incidents/INC-03-uf-sortie.md
exercises/incidents/INC-04-index-inexistant.md exercises/incidents/INC-05-sourcetype.md exercises/incidents/INC-06-fuseau.md
exercises/incidents/INC-07-cim.md exercises/incidents/INC-08-poller-429.md exercises/incidents/INC-09-hec-refus.md exercises/incidents/INC-10-multiligne.md
instructor/ANSWER-KEY.md instructor/solutions/soc_routing/default/props.conf instructor/solutions/soc_routing/default/transforms.conf
tests/ACCEPTANCE.md tests/test_poller.py tests/test_ta_regex.py
generators/gen_datasets.py generators/send_syslog.py generators/write_linux_logs.py generators/hec_send.py
collectors/api/poller.py collectors/api/mock_api.py collectors/api/poller_naive.py collectors/api/config.example.env
collectors/syslog/conf.d/soc-lab.conf collectors/syslog/syslog-ng.conf collectors/syslog/logrotate-soc-lab
configs/uf-apps/soc_uf_outputs/default/outputs.conf configs/uf-apps/soc_uf_linux/default/inputs.conf configs/uf-apps/soc_uf_windows/default/inputs.conf
splunk-apps/soc_lab_base/default/indexes.conf splunk-apps/soc_lab_base/default/inputs.conf splunk-apps/soc_lab_quality/default/savedsearches.conf
addons/TA-soc-firewall/default/props.conf addons/TA-soc-linux/default/props.conf addons/TA-soc-cloud/default/props.conf
addons/TA-soc-app/default/props.conf addons/SA-soc-enrichment/default/transforms.conf""".split()

EXPECTED_LINES = {"firewall.log": 2000, "firewall-anomalies.log": 14, "linux-auth.log": 561, "app-multiline.log": 282,
                  "web-access.log": 1000, "aws-cloudtrail.jsonl": 300, "azure-activity.jsonl": 300, "gcp-audit.jsonl": 200,
                  "m365-audit.jsonl": 300, "saas-audit.jsonl": 500}


def parse_conf(path):
    """Retourne {stanza: {clé: valeur}} ; signale les lignes invalides."""
    out, cur, pending = {}, None, ""
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip()
        if pending:
            line, pending = pending + line.lstrip(), ""
        if line.endswith("\\"):
            pending = line[:-1]
            continue
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            cur = out.setdefault(s[1:-1], {})
        elif "=" in s and cur is not None:
            k, v = s.split("=", 1)
            cur[k.strip()] = v.strip()
        else:
            err(f"{rel(path)}:{n}: ligne .conf invalide : {s[:60]!r}")
    return out


def check_required():
    for f in REQUIRED:
        if not (ROOT / f).exists():
            err(f"fichier obligatoire manquant : {f}")


def splunk_conf_files():
    skip = {"collectors"}
    for p in ROOT.rglob("*.conf"):
        if p.relative_to(ROOT).parts[0] in skip:
            continue
        yield p


def check_conf_and_refs():
    all_transforms, all_eventtypes, props_stanzas, parsed = {}, set(), set(), {}
    for p in splunk_conf_files():
        parsed[p] = parse_conf(p)
        if p.name == "transforms.conf":
            all_transforms.update({k: v for k, v in parsed[p].items()})
        if p.name == "eventtypes.conf":
            all_eventtypes.update(parsed[p].keys())
        if p.name == "props.conf" and "instructor" not in p.parts and "configs" not in p.parts:
            props_stanzas.update(parsed[p].keys())
    for p, conf in parsed.items():
        if p.name == "props.conf" and "instructor" not in p.parts:
            for st, kv in conf.items():
                for k, v in kv.items():
                    if k.startswith(("REPORT-", "TRANSFORMS-")):
                        for name in [x.strip() for x in v.split(",")]:
                            if name not in all_transforms and "configs/hf" not in rel(p):
                                err(f"{rel(p)} [{st}] {k} référence '{name}' absent de transforms.conf")
                    if k.startswith("LOOKUP-"):
                        if v.split()[0] not in all_transforms:
                            err(f"{rel(p)} [{st}] {k} : lookup '{v.split()[0]}' non déclaré")
        if p.name == "tags.conf":
            for st in conf:
                m = re.match(r"eventtype=(.+)", st)
                if m and m.group(1) not in all_eventtypes:
                    err(f"{rel(p)} : eventtype '{m.group(1)}' inconnu")
        if p.name == "transforms.conf" and "lookups" not in rel(p):
            for st, kv in conf.items():
                if "filename" in kv:
                    app = p.parents[1]
                    if not (app / "lookups" / kv["filename"]).exists():
                        err(f"{rel(p)} [{st}] : fichier lookup {kv['filename']} introuvable")
    # index et sourcetypes des inputs
    idx = parsed[ROOT / "splunk-apps/soc_lab_base/default/indexes.conf"]
    if len(idx) != 8:
        err(f"indexes.conf : 8 index attendus, {len(idx)} trouvés")
    allowed_without_ta = {"linux:syslog", "soc:unrouted", "soc:web:access", "soc:api", "soc:poller:metrics"}
    for p, conf in parsed.items():
        if p.name == "inputs.conf" and "uf-apps" in p.parts:
            for st, kv in conf.items():
                if "index" in kv and kv["index"] not in idx:
                    err(f"{rel(p)} [{st}] : index '{kv['index']}' absent de indexes.conf")
                sty = kv.get("sourcetype")
                if sty and sty not in props_stanzas and sty not in allowed_without_ta:
                    err(f"{rel(p)} [{st}] : sourcetype '{sty}' sans props.conf dans un TA")


def check_python():
    for p in ROOT.rglob("*.py"):
        try:
            py_compile.compile(str(p), doraise=True, cfile=str(Path(tempfile.gettempdir()) / "vr.pyc"))
        except py_compile.PyCompileError as e:
            err(f"{rel(p)} : erreur de syntaxe Python : {e.msg.splitlines()[-1]}")


def check_docs():
    tops = ("modules/", "exercises/", "docs/", "configs/", "collectors/", "addons/", "splunk-apps/", "generators/",
            "datasets/", "tests/", "scripts/", "instructor/")
    for p in list(ROOT.rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r"\[[^\]]*\]\(([^)#\s]+)\)", text):
            tgt = m.group(1)
            if "://" in tgt or tgt.startswith("mailto:"):
                continue
            if not (p.parent / tgt).resolve().exists():
                err(f"{rel(p)} : lien cassé → {tgt}")
        for m in re.finditer(r"`([^`\n]+)`", text):
            t = m.group(1).strip()
            if t.startswith(tops) and re.search(r"\.[A-Za-z0-9]+$", t) and not re.search(r"[<>*…\s{}$|\\]", t):
                if not (ROOT / t).exists():
                    err(f"{rel(p)} : chemin cité inexistant → {t}")


def check_secrets():
    pats = [re.compile(r"(?i)token\s*[=:]\s*['\"]?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
            re.compile(r"(?i)SPLUNK_HEC_TOKEN\s*=\s*(?!REMPLACER|<|\$|\"?\$)[^\s]{16,}"),
            re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----")]
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".conf", ".py", ".env", ".yml", ".csv", ".txt", ".example"}:
            if "__pycache__" in p.parts:
                continue
            t = p.read_text(encoding="utf-8", errors="ignore")
            for pat in pats:
                if pat.search(t):
                    err(f"{rel(p)} : secret potentiel ({pat.pattern[:30]}…)")


def check_datasets():
    for name, n in EXPECTED_LINES.items():
        f = ROOT / "datasets" / name
        if not f.exists():
            err(f"dataset manquant : {name}")
            continue
        got = len(f.read_text(encoding="utf-8").splitlines())
        if got != n:
            err(f"datasets/{name} : {got} lignes au lieu de {n}")
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([sys.executable, str(ROOT / "generators/gen_datasets.py"), "--out", d], capture_output=True, text=True)
        if r.returncode != 0:
            err("gen_datasets.py a échoué : " + r.stderr[-200:])
            return
        for name in EXPECTED_LINES:
            if not (Path(d) / name).exists() or not filecmp.cmp(ROOT / "datasets" / name, Path(d) / name, shallow=False):
                err(f"datasets/{name} ne correspond pas à la génération déterministe (seed 42)")


def main():
    check_required()
    check_conf_and_refs()
    check_python()
    check_docs()
    check_secrets()
    check_datasets()
    for w in warnings:
        print("WARN", w)
    if errors:
        for e in errors:
            print("ERREUR", e)
        print(f"\n{len(errors)} erreur(s).")
        return 1
    print("OK — dépôt cohérent (voir README : ces contrôles ne remplacent pas Splunk).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
