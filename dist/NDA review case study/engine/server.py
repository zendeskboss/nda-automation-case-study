"""Local server for the NDA review prototype. Standard library only.
Run: python3 server.py   then open http://localhost:8765
"""
import json, os, glob, time, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import review

HERE = os.path.dirname(os.path.abspath(__file__))
# Contracts folder: NDA_CONTRACTS if set, else ../testset if it exists, else ./contracts.
_TESTSET = os.path.join(HERE, "..", "testset")
TESTSET = os.environ.get("NDA_CONTRACTS") or (_TESTSET if os.path.isdir(_TESTSET) else os.path.join(HERE, "contracts"))
REPLAY = os.path.join(HERE, "replay")
LOG = os.path.join(HERE, "logs", "shadow_log.jsonl")
PB = review.load_playbook()
PORT = int(os.environ.get("PORT", "8765"))

def load_replay(cid):
    # Read as UTF-8 here: on Windows the default encoding breaks quotes with non-ASCII text.
    p = os.path.join(REPLAY, cid + ".raw.json")
    if not os.path.exists(p): raise FileNotFoundError(cid)
    return json.load(open(p, encoding="utf-8"))

def samples():
    out = []
    for p in sorted(glob.glob(os.path.join(TESTSET, "C??.md"))):
        cid = os.path.basename(p)[:3]
        has_replay = os.path.exists(os.path.join(REPLAY, cid + ".raw.json"))
        lp = p.replace(".md", ".labels.json")
        if os.path.exists(lp):
            lab = json.load(open(lp, encoding="utf-8"))
        else:
            # No labels in this folder: label the sample from the saved review instead.
            raw = load_replay(cid) if has_replay else {}
            s = raw.get("summary") or ""
            lab = dict(counterparty=s if len(s) <= 70 else s[:67] + "...", paper=raw.get("paper", ""))
        out.append(dict(id=cid, counterparty=lab.get("counterparty", ""), paper=lab.get("paper", ""), replay=has_replay))
    return out

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._send(200, open(os.path.join(HERE, "static", "index.html"), "rb").read(), "text/html")
        if path == "/api/status":
            return self._send(200, dict(live=bool(os.environ.get("ANTHROPIC_API_KEY")), model=review.DEFAULT_MODEL,
                                        playbook=PB["meta"]["version"], threshold=review.DEFAULT_THRESHOLD))
        if path == "/api/samples": return self._send(200, samples())
        m = re.match(r"/api/contract/(C\d\d)$", path)
        if m:
            p = os.path.join(TESTSET, m.group(1) + ".md")
            return self._send(200, dict(id=m.group(1), text=open(p, encoding="utf-8").read())) if os.path.exists(p) else self._send(404, dict(error="not found"))
        self._send(404, dict(error="not found"))

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/review":
            mode = body.get("mode", "replay"); cid = body.get("id") or "PASTED"; text = body.get("text", "")
            try:
                if mode == "replay":
                    p = os.path.join(TESTSET, cid + ".md")
                    src = open(p, encoding="utf-8").read() if os.path.exists(p) else None
                    routed = review.route(load_replay(cid), PB, text=src)  # text runs the injection screen
                else:
                    if not text: return self._send(400, dict(error="Paste the contract text first."))
                    _, routed = review.review(cid, text, "anthropic", pb=PB)
                return self._send(200, routed)
            except FileNotFoundError:
                return self._send(404, dict(error="No saved run for this contract. Switch to Live, or pick another."))
            except Exception as e:
                return self._send(500, dict(error=str(e)))
        if self.path == "/api/decision":
            # Shadow log: the tool's verdict is recorded, then the lawyer's decision, so agreement can be measured later.
            rec = dict(ts=time.strftime("%Y-%m-%dT%H:%M:%S"), **{k: body.get(k) for k in
                       ("contract", "clause_no", "rule_id", "ai_verdict", "lawyer_decision", "action")})
            os.makedirs(os.path.dirname(LOG), exist_ok=True)
            open(LOG, "a", encoding="utf-8").write(json.dumps(rec) + "\n")
            return self._send(200, dict(ok=True))
        self._send(404, dict(error="not found"))

    def log_message(self, *a): pass

if __name__ == "__main__":
    print("NDA review prototype on http://localhost:%d  (live: %s)" % (PORT, "yes" if os.environ.get("ANTHROPIC_API_KEY") else "no, replay only"))
    # Localhost only: the pages hold contract text. Set HOST=0.0.0.0 only on a trusted network.
    ThreadingHTTPServer((os.environ.get("HOST", "127.0.0.1"), PORT), H).serve_forever()
