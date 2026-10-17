"""Run or replay the v2 checklist review.

  python phase2/v2/run.py --run r1 --all                       live: calls Jev, writes runs/r1/
  python phase2/v2/run.py --run r1 --all --replay              no Jev calls: rebuild findings from saved evidence
  python phase2/v2/run.py --run adv --folder evals/adversarial/contracts A01 A02 A03
  python phase2/v2/run.py --run r1 --all --patch --policy v2.1   adds the v2.1 inputs, writes <id>.routed.v2.1.json

Per contract, runs/<run>/ holds:
  <id>.evidence.json  every clause, every question, every probability, thresholds and versions
  <id>.raw.json       findings in the v1 raw schema (same as replay/)
  <id>.routed.json    the v1 router's output: lanes and verdicts
"""
import argparse, glob, json, os, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine, review  # noqa: E402

def save(obj, path): json.dump(obj, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--run", required=True); ap.add_argument("--folder", default="contracts")
    ap.add_argument("--replay", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    # The default policy changes only through import_spotcheck.py, after a lawyer's check.
    dp = os.path.join(engine.V2, "default_policy.json")
    default_policy = json.load(open(dp, encoding="utf-8"))["default"] if os.path.exists(dp) else "v2.0"
    ap.add_argument("--policy", default=default_policy, choices=sorted(engine.POLICIES))
    ap.add_argument("--patch", action="store_true", help="add the v2.1 Jev inputs to saved evidence (few calls), then decide")
    a = ap.parse_args()
    folder = os.path.join(engine.ROOT, a.folder)
    ids = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(folder, "*.md"))) if a.all else a.ids
    out = os.path.join(engine.V2, "runs", a.run); os.makedirs(out, exist_ok=True)
    pb = review.load_playbook()
    sys.stdout.reconfigure(encoding="utf-8")
    with ThreadPoolExecutor(a.workers) as pool:
        for cid in ids:
            text = open(os.path.join(folder, cid + ".md"), encoding="utf-8").read()
            if a.replay or a.patch:
                ev = json.load(open(os.path.join(out, cid + ".evidence.json"), encoding="utf-8"))
                if ev["contract_sha256"] != engine.hashlib.sha256(text.encode()).hexdigest():
                    print(cid, "WARNING: the contract changed since this evidence was saved")
                if a.patch and "v2.1" not in ev.get("patches", []):
                    ev = engine.patch_v21(ev, text, pb, pool); save(ev, os.path.join(out, cid + ".evidence.json"))
            else:
                ev = engine.analyse(cid, text, pb, pool)
                save(ev, os.path.join(out, cid + ".evidence.json"))
            raw = engine.decide(ev, pb, a.policy)
            routed = review.route(raw, pb, text=text)
            sfx = "" if a.policy == "v2.0" else "." + a.policy
            save(raw, os.path.join(out, cid + ".raw%s.json" % sfx)); save(routed, os.path.join(out, cid + ".routed%s.json" % sfx))
            v = [f["verdict"] for f in routed["findings"]]
            errs = sum(1 for u in ev["units"] if u.get("error")) + sum(1 for u in ev["units"] for c in u.get("checks", {}).values() if "error" in c)
            print("%s units=%d findings=%d escalate=%d draft=%d acceptable=%d matches=%d jev_errors=%d injection=%s" % (
                cid, len(ev["units"]), len(v), v.count("escalate"), v.count("deviation_draft"), v.count("acceptable"),
                v.count("matches"), errs, routed["injection_suspected"]))
