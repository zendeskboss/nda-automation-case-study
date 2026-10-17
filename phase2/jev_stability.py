"""Stability test: send the same contract check to Jev five times per contract and compare the answers.

Same input every time (the saved review, routed by review.route). Measures whether Jev gives the same answer
and the same escalation decision on every run. It does not measure accuracy.

Usage: python phase2/jev_stability.py [--runs 5]
Needs TYPESAFE_API_KEY. Writes jev_runs/stability.json.
"""
import json, os, sys, argparse, statistics as st
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import review, jev_test  # noqa: E402

def decision(k, v):
    """The escalation decision that code takes from one answer, with the README thresholds."""
    if k == "document_type": return v["choice"] in ("not_nda", "nda_inside_larger_deal")
    if k.startswith("has_"): return "urgent" if v["noul"] > 0.5 else ("lawyer" if v["noul"] > 0.3 else "none")
    if k.startswith("topic_present__"):
        return v["noul"] > 0.5 if k[15:] in jev_test.ABSENT_PREFERRED else v["noul"] < 0.5
    if k == "findings_conflict": return v["noul"] > 0.3
    if k == "overall_unusual": return v["score"] >= 2
    return None

def value(v):
    return v.get("choice") or v.get("noul", v.get("score"))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--runs", type=int, default=5); ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    pb = review.load_playbook()
    jobs = {}
    with ThreadPoolExecutor(a.workers) as pool:
        for n in range(1, 31):
            cid = "C%02d" % n
            text = open(os.path.join(ROOT, "contracts", cid + ".md"), encoding="utf-8").read()
            raw = json.load(open(os.path.join(ROOT, "replay", cid + ".raw.json"), encoding="utf-8"))
            state, qs = jev_test.contract_request(review.route(raw, pb, text=text), text, review.mask(text)[0], pb)
            jobs[cid] = [pool.submit(jev_test.call_jev, state, qs) for _ in range(a.runs)]
        res = {cid: [j.result()["answers"] for j in js] for cid, js in jobs.items()}

    per_q, rows = {}, []
    for cid, runs in res.items():
        for k in runs[0]:
            vals = [value(r[k]) for r in runs]
            decs = [decision(k, r[k]) for r in runs]
            numeric = all(isinstance(x, (int, float)) for x in vals)
            row = dict(contract=cid, question=k, values=vals, decisions=decs,
                       same_answer=len(set(vals)) == 1 if not numeric else None,
                       spread=round(max(vals) - min(vals), 4) if numeric else None,
                       same_decision=len(set(map(str, decs))) == 1)
            rows.append(row)
            q = "topic_present" if k.startswith("topic_present__") else k
            per_q.setdefault(q, []).append(row)
    summary = {}
    for q, rs in per_q.items():
        sp = [r["spread"] for r in rs if r["spread"] is not None]
        summary[q] = dict(cases=len(rs), same_decision=sum(r["same_decision"] for r in rs),
                          max_spread=max(sp) if sp else None, median_spread=st.median(sp) if sp else None,
                          same_answer=sum(bool(r["same_answer"]) for r in rs) if not sp else None)
    json.dump(dict(runs=a.runs, model=jev_test.MODEL, summary=summary, rows=rows),
              open(os.path.join(HERE, "jev_runs", "stability.json"), "w", encoding="utf-8"), indent=1)
    sys.stdout.reconfigure(encoding="utf-8")
    for q, s in summary.items(): print(q, s)
    flips = [r for r in rows if not r["same_decision"]]
    print("decision flips:", len(flips), "of", len(rows))
    for r in flips: print("  ", r["contract"], r["question"], r["values"])
