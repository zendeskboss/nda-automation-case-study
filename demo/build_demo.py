"""Build the demo app: one HTML file that runs the review page with no Python and no server.

Run: python3 demo/build_demo.py   (writes demo/index.html)

It routes every saved review in replay/ once, with the same code as server.py, and puts the
contracts and the routed findings into the page. The page's calls to /api/... are answered from
that data. Live mode is removed. Lawyer decisions are kept in the viewer's browser only.
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import review  # noqa: E402

CONTRACTS = os.path.join(ROOT, "contracts")
REPLAY = os.path.join(ROOT, "replay")
PAGE = os.path.join(ROOT, "static", "index.html")
OUT = os.path.join(HERE, "index.html")

SHIM = r"""<script>
// Demo app: answers the page's /api calls from data built into this file. No server is used.
const DEMO = __DATA__;
const _json = (body, status=200) => new Response(JSON.stringify(body), {status, headers:{"content-type":"application/json"}});
window.fetch = async (url, opts={}) => {
  const path = String(url).split("?")[0];
  if (path === "/api/status") return _json(DEMO.status);
  if (path === "/api/samples") return _json(DEMO.samples);
  const m = path.match(/^\/api\/contract\/(C\d\d)$/);
  if (m) return DEMO.contracts[m[1]] ? _json({id:m[1], text:DEMO.contracts[m[1]]}) : _json({error:"not found"}, 404);
  if (path === "/api/review") {
    const id = JSON.parse(opts.body || "{}").id;
    return DEMO.results[id] ? _json(DEMO.results[id]) : _json({error:"No saved review for this contract."}, 404);
  }
  if (path === "/api/decision") {
    try {
      const log = JSON.parse(localStorage.getItem("nda-demo-decisions") || "[]");
      log.push({ts:new Date().toISOString(), ...JSON.parse(opts.body || "{}")});
      localStorage.setItem("nda-demo-decisions", JSON.stringify(log));
    } catch (e) {}
    return _json({ok:true});
  }
  return _json({error:"not found"}, 404);
};
</script>
"""

BANNER = ('<span class="note" style="flex-basis:100%">Demo app: saved AI reviews of 30 test NDAs, '
          'routed by the playbook rules. Nothing is sent anywhere. Your decisions stay in this browser.</span>')

def build():
    pb = review.load_playbook()
    contracts, results, samples = {}, {}, []
    for p in sorted(glob.glob(os.path.join(CONTRACTS, "C??.md"))):
        cid = os.path.basename(p)[:3]
        rp = os.path.join(REPLAY, cid + ".raw.json")
        if not os.path.exists(rp): continue
        raw = json.load(open(rp, encoding="utf-8"))
        contracts[cid] = open(p, encoding="utf-8").read()
        results[cid] = review.route(raw, pb)
        s = raw.get("summary") or ""
        samples.append(dict(id=cid, counterparty=s if len(s) <= 70 else s[:67] + "...",
                            paper=raw.get("paper", ""), replay=True))
    data = dict(status=dict(live=False, model="saved reviews", playbook=pb["meta"]["version"],
                            threshold=review.DEFAULT_THRESHOLD),
                samples=samples, contracts=contracts, results=results)
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    html = open(PAGE, encoding="utf-8").read()
    edits = [
        ("<title>NDA review</title>", "<title>NDA review demo</title>"),
        ("<h1>NDA review</h1>", "<h1>NDA review · demo app</h1>"),
        ('<div class="seg" role="group" aria-label="Mode">', '<div class="seg" role="group" aria-label="Mode" style="display:none">'),
        ('<span class="meta" id="meta"></span>', '<span class="meta" id="meta"></span>\n  ' + BANNER),
        ("<script>\nconst $ =", SHIM.replace("__DATA__", blob) + "<script>\nconst $ ="),
    ]
    for old, new in edits:
        if old not in html: raise SystemExit("static/index.html changed; cannot find: " + old[:60])
        html = html.replace(old, new, 1)
    with open(OUT, "w", encoding="utf-8") as f: f.write(html)
    print("wrote %s: %d contracts, %d KB" % (OUT, len(samples), os.path.getsize(OUT) // 1024))

if __name__ == "__main__":
    build()
