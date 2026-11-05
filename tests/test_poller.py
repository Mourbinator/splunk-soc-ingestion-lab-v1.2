"""Tests unitaires du poller (sans Splunk) : python3 -m unittest discover -s tests -v"""
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "collectors" / "api"))
import mock_api   # noqa: E402
import poller     # noqa: E402


def start(server):
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def stop(server):
    server.shutdown()
    server.server_close()


class FakeHec(ThreadingHTTPServer):
    def __init__(self, token="good", fail_first=0):
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                srv = self.server
                if self.headers.get("Authorization") != f"Splunk {srv.token}":
                    self.send_response(403); self.end_headers(); self.wfile.write(b'{"text":"Invalid token","code":4}'); return
                if srv.fail_first > 0:
                    srv.fail_first -= 1
                    self.send_response(503); self.end_headers(); self.wfile.write(b'{"text":"Server is busy","code":9}'); return
                srv.received += [json.loads(x) for x in body.decode().splitlines() if x]
                self.send_response(200); self.end_headers(); self.wfile.write(b'{"text":"Success","code":0}')
        super().__init__(("127.0.0.1", 0), H)
        self.token, self.fail_first, self.received = token, fail_first, []


class PollerTests(unittest.TestCase):
    def cfg(self, api, ck, **kw):
        base = dict(api_base=f"http://127.0.0.1:{api.server_address[1]}", checkpoint=str(ck), dry_run=True,
                    sleep=lambda s: None, log=lambda m: None)
        base.update(kw)
        return poller.Config(**base)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ck = self.tmp / "ck.json"

    def test_full_run_with_429_is_complete(self):
        api = start(mock_api.make_server(port=0, throttle_every=3, retry_after=0))
        m = poller.run(self.cfg(api, self.ck))
        self.assertEqual((m["fetched"], m["sent"]), (500, 500))
        self.assertGreater(m["http_429"], 0)
        self.assertEqual(m["http_429"], m["retried"])
        stop(api)

    def test_resume_from_checkpoint(self):
        api = start(mock_api.make_server(port=0))
        m1 = poller.run(self.cfg(api, self.ck, max_pages=2))
        m2 = poller.run(self.cfg(api, self.ck))
        self.assertEqual(m1["sent"], 200)
        self.assertEqual(m2["sent"], 300)
        m3 = poller.run(self.cfg(api, self.ck))          # plus rien de nouveau
        self.assertEqual(m3["sent"], 0)
        stop(api)

    def test_dedup_when_checkpoint_position_is_lost(self):
        api = start(mock_api.make_server(port=0))
        poller.run(self.cfg(api, self.ck))
        st = json.loads(self.ck.read_text()); st["next"] = None; self.ck.write_text(json.dumps(st))
        m = poller.run(self.cfg(api, self.ck))
        self.assertEqual((m["fetched"], m["sent"], m["duplicates_skipped"]), (500, 0, 500))
        stop(api)

    def test_bad_api_key_is_fatal(self):
        api = start(mock_api.make_server(port=0))
        with self.assertRaises(poller.FatalError):
            poller.run(self.cfg(api, self.ck, api_key="wrong"))
        stop(api)

    def test_503_from_api_is_retried(self):
        api = start(mock_api.make_server(port=0, fail_every=2))
        m = poller.run(self.cfg(api, self.ck))
        self.assertEqual(m["sent"], 500)
        self.assertGreater(m["http_5xx"], 0)
        stop(api)

    def test_hec_real_path_retry_and_payload(self):
        api = start(mock_api.make_server(port=0))
        hec = start(FakeHec(fail_first=2))
        m = poller.run(self.cfg(api, self.ck, dry_run=False, hec_url=f"http://127.0.0.1:{hec.server_address[1]}", hec_token="good"))
        self.assertEqual(m["sent"], 500)
        self.assertGreaterEqual(m["retried"], 2)
        saas = [e for e in hec.received if e["sourcetype"] == "soc:saas:audit"]
        self.assertEqual(len(saas), 500)
        self.assertEqual(saas[0]["index"], "saas")
        self.assertEqual(saas[0]["event"]["event_id"], "saas-0001")
        self.assertTrue(any(e["sourcetype"] == "soc:poller:metrics" for e in hec.received))
        stop(api); stop(hec)

    def test_hec_bad_token_is_fatal_and_checkpoint_does_not_advance(self):
        api = start(mock_api.make_server(port=0))
        hec = start(FakeHec(token="good"))
        with self.assertRaises(poller.FatalError):
            poller.run(self.cfg(api, self.ck, dry_run=False, hec_url=f"http://127.0.0.1:{hec.server_address[1]}", hec_token="bad"))
        self.assertFalse(self.ck.exists())
        stop(api); stop(hec)


if __name__ == "__main__":
    unittest.main()
