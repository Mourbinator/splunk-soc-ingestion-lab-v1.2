#!/usr/bin/env python3
"""API SaaS simulée (pagination + limitation de débit) pour s'entraîner à écrire un poller.

Lancement :
    python3 collectors/api/mock_api.py --port 8081 --throttle-every 4 --retry-after 2

Comportement :
  GET /events?cursor=0&limit=100  -> {"items":[...], "nextLink": "<url>"|null, "resumeLink": "<url>"}
  - exige l'en-tête  Authorization: Bearer <clé>   (clé = variable MOCK_API_KEY, défaut « lab-mock-key »)
  - renvoie HTTP 429 + en-tête Retry-After une requête /events sur N (--throttle-every N)
  - renvoie HTTP 503 une requête /events sur M (--fail-every M)
  - GET /health -> 200
"""
import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_DATA = Path(__file__).resolve().parents[2] / "datasets" / "saas-audit.jsonl"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):          # journal discret
        if getattr(self.server, "verbose", False):
            super().log_message(fmt, *args)

    def _send(self, status, body=None, headers=None):
        raw = json.dumps(body).encode() if body is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        srv = self.server
        url = urlparse(self.path)
        if url.path == "/health":
            return self._send(200, {"status": "ok"})
        if url.path != "/events":
            return self._send(404, {"error": "not found"})
        if self.headers.get("Authorization") != f"Bearer {srv.api_key}":
            return self._send(401, {"error": "invalid or missing API key"})
        with srv.lock:
            srv.counter += 1
            n = srv.counter
        if srv.throttle_every and n % srv.throttle_every == 0:
            return self._send(429, {"error": "rate limit exceeded"}, {"Retry-After": str(srv.retry_after)})
        if srv.fail_every and n % srv.fail_every == 0:
            return self._send(503, {"error": "temporarily unavailable"})
        q = parse_qs(url.query)
        cursor = max(0, int(q.get("cursor", ["0"])[0]))
        limit = max(1, min(200, int(q.get("limit", ["100"])[0])))
        items = srv.data[cursor:cursor + limit]
        end = cursor + len(items)
        base = f"http://{self.headers.get('Host')}/events"
        body = {"items": items,
                "nextLink": f"{base}?cursor={end}&limit={limit}" if end < len(srv.data) else None,
                "resumeLink": f"{base}?cursor={end}&limit={limit}"}
        return self._send(200, body)


def make_server(host="127.0.0.1", port=8081, data_path=DEFAULT_DATA, throttle_every=0, retry_after=1,
                fail_every=0, api_key=None, verbose=False):
    srv = ThreadingHTTPServer((host, port), Handler)
    srv.data = [json.loads(line) for line in Path(data_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    srv.throttle_every, srv.retry_after, srv.fail_every = throttle_every, retry_after, fail_every
    srv.api_key = api_key or os.environ.get("MOCK_API_KEY", "lab-mock-key")
    srv.counter, srv.lock, srv.verbose = 0, threading.Lock(), verbose
    return srv


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8081)
    p.add_argument("--data", default=str(DEFAULT_DATA))
    p.add_argument("--throttle-every", type=int, default=0)
    p.add_argument("--retry-after", type=int, default=2)
    p.add_argument("--fail-every", type=int, default=0)
    p.add_argument("--verbose", action="store_true")
    a = p.parse_args()
    srv = make_server(a.host, a.port, a.data, a.throttle_every, a.retry_after, a.fail_every, verbose=a.verbose)
    print(f"Mock API sur http://{a.host}:{a.port}  ({len(srv.data)} événements, clé = {srv.api_key})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
