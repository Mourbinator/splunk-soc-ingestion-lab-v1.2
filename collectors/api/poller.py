#!/usr/bin/env python3
"""Poller API -> Splunk HEC : pagination, checkpoint durable, retry/backoff, 429, déduplication, métriques.

Variables d'environnement (jamais dans Git) :
    API_BASE_URL      défaut http://127.0.0.1:8081
    API_KEY           clé de l'API (défaut lab-mock-key pour la mock API)
    SPLUNK_HEC_URL    ex. https://10.50.0.10:8088
    SPLUNK_HEC_TOKEN  token HEC dédié

Exemples :
    python3 collectors/api/poller.py --dry-run                       # sans Splunk : affiche seulement les métriques
    python3 collectors/api/poller.py --insecure                      # envoi réel (certificat HEC auto-signé du lab)
    python3 collectors/api/poller.py --max-pages 2                   # s'arrête après 2 pages (test de reprise)
    python3 collectors/api/poller.py --reset                         # efface le checkpoint et repart de zéro

Garanties :
  * « au moins une fois » : le checkpoint n'avance QU'APRÈS un envoi HEC réussi ;
  * « effectivement une fois » : les event_id déjà envoyés (fenêtre --dedup-window) sont ignorés.
"""
import argparse
import datetime as dt
import json
import os
import random
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


class FatalError(Exception):
    """Erreur inutile à réessayer (clé/token invalide, données refusées...)."""


class RetryableError(Exception):
    """Erreur temporaire : 429, 5xx, réseau."""

    def __init__(self, message, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class Config:
    api_base: str = "http://127.0.0.1:8081"
    api_key: str = "lab-mock-key"
    start_path: str = "/events?cursor=0&limit=100"
    hec_url: str = ""
    hec_token: str = ""
    hec_index: str = "saas"
    hec_sourcetype: str = "soc:saas:audit"
    hec_source: str = "soc-api-poller"
    hec_host: str = "api-poller"
    metrics_index: str = "lab_api"
    insecure: bool = False
    dry_run: bool = False
    checkpoint: str = "state/checkpoint.json"
    max_retries: int = 6
    backoff_base: float = 1.0
    backoff_cap: float = 30.0
    max_pages: int = 0            # 0 = illimité
    dedup_window: int = 5000
    timeout: float = 15.0
    sleep: Callable[[float], None] = field(default=time.sleep, repr=False)
    log: Callable[[str], None] = field(default=lambda m: print(m, file=sys.stderr), repr=False)


def new_metrics():
    return {"pages": 0, "fetched": 0, "sent": 0, "duplicates_skipped": 0, "rejected": 0,
            "retried": 0, "http_429": 0, "http_5xx": 0, "network_errors": 0}


# ---------------------------------------------------------------- checkpoint
def load_checkpoint(path):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"next": None, "seen_ids": [], "last_event_id": None}


def save_checkpoint(path, state):
    """Écriture atomique : on écrit un fichier temporaire puis on le renomme."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    os.replace(tmp, p)


# ---------------------------------------------------------------- HTTP
def http_call(url, method="GET", headers=None, data=None, insecure=False, timeout=15.0):
    ctx = ssl._create_unverified_context() if (insecure and url.startswith("https")) else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise RetryableError(f"réseau : {e}")


def parse_retry_after(headers):
    value = {k.lower(): v for k, v in headers.items()}.get("retry-after")
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def with_retry(fn, cfg, metrics, label):
    """Exécute fn() ; réessaie sur RetryableError avec backoff exponentiel + jitter, en respectant Retry-After."""
    attempt = 0
    while True:
        try:
            return fn()
        except RetryableError as e:
            attempt += 1
            if attempt > cfg.max_retries:
                raise FatalError(f"{label} : abandon après {cfg.max_retries} tentatives ({e})")
            metrics["retried"] += 1
            if e.retry_after is not None:
                wait = e.retry_after + random.uniform(0, 0.25)                       # le serveur décide
            else:
                ceiling = min(cfg.backoff_cap, cfg.backoff_base * (2 ** (attempt - 1)))
                wait = ceiling / 2 + random.uniform(0, ceiling / 2)                  # « equal jitter »
            cfg.log(f"[retry {attempt}/{cfg.max_retries}] {label} : {e} -> attente {wait:.2f}s")
            cfg.sleep(wait)


# ---------------------------------------------------------------- API
def fetch_page(url, cfg, metrics):
    status, headers, body = http_call(url, headers={"Authorization": f"Bearer {cfg.api_key}"},
                                      insecure=cfg.insecure, timeout=cfg.timeout)
    if status == 200:
        return json.loads(body)
    if status == 429:
        metrics["http_429"] += 1
        raise RetryableError("HTTP 429", retry_after=parse_retry_after(headers))
    if status >= 500:
        metrics["http_5xx"] += 1
        raise RetryableError(f"HTTP {status}")
    raise FatalError(f"API HTTP {status} : {body[:200]!r} (vérifier API_KEY / URL)")


# ---------------------------------------------------------------- HEC
def to_epoch(value):
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return time.time()


def hec_payload(events, cfg, index=None, sourcetype=None):
    lines = []
    for ev in events:
        lines.append(json.dumps({"time": to_epoch(ev.get("event_time")), "host": cfg.hec_host, "source": cfg.hec_source,
                                 "sourcetype": sourcetype or cfg.hec_sourcetype, "index": index or cfg.hec_index,
                                 "event": ev}, separators=(",", ":")))
    return "\n".join(lines).encode("utf-8")


def send_hec(events, cfg, metrics, index=None, sourcetype=None):
    if not events:
        return
    if cfg.dry_run:
        metrics["sent"] += len(events)
        return
    url = cfg.hec_url.rstrip("/") + "/services/collector/event"
    status, headers, body = http_call(url, "POST", {"Authorization": f"Splunk {cfg.hec_token}"},
                                      hec_payload(events, cfg, index, sourcetype), cfg.insecure, cfg.timeout)
    if status == 200:
        metrics["sent"] += len(events)
        return
    text = body[:300].decode("utf-8", "replace")
    if status in (401, 403):
        raise FatalError(f"HEC {status} : token absent/invalide/désactivé ({text})")
    if status == 400:
        metrics["rejected"] += len(events)
        raise FatalError(f"HEC 400 : lot refusé, le checkpoint N'AVANCE PAS ({text})")
    if status in (500, 502, 503, 504):
        metrics["http_5xx"] += 1
        raise RetryableError(f"HEC {status}")
    raise FatalError(f"HEC statut inattendu {status} : {text}")


# ---------------------------------------------------------------- boucle principale
def run(cfg):
    metrics = new_metrics()
    state = load_checkpoint(cfg.checkpoint)
    seen = list(state.get("seen_ids", []))
    seen_set = set(seen)
    url = urllib.parse.urljoin(cfg.api_base, state.get("next") or cfg.start_path)
    while url:
        page = with_retry(lambda: fetch_page(url, cfg, metrics), cfg, metrics, f"GET {url}")
        items = page.get("items", [])
        metrics["pages"] += 1
        metrics["fetched"] += len(items)
        fresh = [e for e in items if e.get("event_id") not in seen_set]
        metrics["duplicates_skipped"] += len(items) - len(fresh)
        with_retry(lambda: send_hec(fresh, cfg, metrics), cfg, metrics, "POST HEC")
        for e in fresh:
            seen.append(e["event_id"])
            seen_set.add(e["event_id"])
        if len(seen) > cfg.dedup_window:
            seen = seen[-cfg.dedup_window:]
            seen_set = set(seen)
        next_link = page.get("nextLink")
        state.update({"next": next_link or page.get("resumeLink") or state.get("next"), "seen_ids": seen,
                      "last_event_id": seen[-1] if seen else state.get("last_event_id")})
        save_checkpoint(cfg.checkpoint, state)          # APRÈS l'envoi réussi
        url = urllib.parse.urljoin(cfg.api_base, next_link) if next_link else None
        if cfg.max_pages and metrics["pages"] >= cfg.max_pages:
            break
    metrics["checkpoint_next"] = state.get("next")
    if not cfg.dry_run and cfg.hec_url:
        try:       # métriques envoyées en « best effort » dans lab_api
            send_hec([{"event_time": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "event_id": f"poller-metrics-{int(time.time())}", **metrics}], cfg, new_metrics(),
                     index=cfg.metrics_index, sourcetype="soc:poller:metrics")
        except (FatalError, RetryableError) as e:
            cfg.log(f"[warn] métriques non envoyées : {e}")
    return metrics


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="n'envoie rien à Splunk")
    p.add_argument("--insecure", action="store_true", help="LAB UNIQUEMENT : accepte le certificat HEC auto-signé")
    p.add_argument("--max-pages", type=int, default=0)
    p.add_argument("--checkpoint", default="state/checkpoint.json")
    p.add_argument("--reset", action="store_true", help="supprime le checkpoint avant de démarrer")
    p.add_argument("--index", default="saas")
    p.add_argument("--max-retries", type=int, default=6)
    p.add_argument("--backoff-base", type=float, default=1.0)
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    cfg = Config(api_base=os.environ.get("API_BASE_URL", "http://127.0.0.1:8081"),
                 api_key=os.environ.get("API_KEY", "lab-mock-key"),
                 hec_url=os.environ.get("SPLUNK_HEC_URL", ""), hec_token=os.environ.get("SPLUNK_HEC_TOKEN", ""),
                 insecure=a.insecure or os.environ.get("HEC_INSECURE") == "1", dry_run=a.dry_run,
                 max_pages=a.max_pages, checkpoint=a.checkpoint, hec_index=a.index,
                 max_retries=a.max_retries, backoff_base=a.backoff_base)
    if not cfg.dry_run and not (cfg.hec_url and cfg.hec_token):
        print("SPLUNK_HEC_URL / SPLUNK_HEC_TOKEN manquants (ou utilisez --dry-run).", file=sys.stderr)
        return 2
    if cfg.insecure:
        print("[warn] vérification TLS désactivée : acceptable en lab, jamais en production.", file=sys.stderr)
    if a.reset and Path(cfg.checkpoint).exists():
        Path(cfg.checkpoint).unlink()
    try:
        metrics = run(cfg)
    except FatalError as e:
        print(f"[fatal] {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    print(json.dumps(metrics))
    return 0


if __name__ == "__main__":
    sys.exit(main())
