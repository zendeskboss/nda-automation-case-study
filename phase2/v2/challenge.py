"""Challenge a v2 decision, or show the evidence behind it.

  python phase2/v2/challenge.py show r1 C01 12.10              every finding on clause 12.10, with its evidence
  python phase2/v2/challenge.py dispute r1 C01 12.10 PB18 --lawyer deviation --reason "Comment asks for Delaware law" --by "A. Lawyer"

A dispute is appended to phase2/v2/challenges.jsonl with a fingerprint of the evidence it disputes, so the log
stays valid even after a later run. Disputes are the input for tuning thresholds: no threshold changes without them.
"""
import argparse, hashlib, json, os, sys, time

V2 = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(V2, "challenges.jsonl")

def load(run, cid):
    d = os.path.join(V2, "runs", run)
    return (json.load(open(os.path.join(d, cid + ".routed.json"), encoding="utf-8")),
            json.load(open(os.path.join(d, cid + ".raw.json"), encoding="utf-8")),
            json.load(open(os.path.join(d, cid + ".evidence.json"), encoding="utf-8")))

def matches(run, cid, clause, rule=None):
    routed, raw, ev = load(run, cid)
    raws = [f for f in raw["findings"] if f["clause_no"] == clause and (rule is None or (f["rule_id"] or "PB22") == rule)]
    outs = [f for f in routed["findings"] if f["clause_no"] == clause and (rule is None or f["rule_id"] == rule)]
    return outs, raws, ev

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show"); s.add_argument("run"); s.add_argument("cid"); s.add_argument("clause"); s.add_argument("rule", nargs="?")
    d = sub.add_parser("dispute"); d.add_argument("run"); d.add_argument("cid"); d.add_argument("clause"); d.add_argument("rule")
    d.add_argument("--lawyer", required=True, choices=["matches", "acceptable", "deviation"])
    d.add_argument("--reason", required=True); d.add_argument("--by", required=True)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    outs, raws, ev = matches(a.run, a.cid, a.clause, a.rule)
    if not outs: sys.exit("No finding for %s clause %s %s in run %s." % (a.cid, a.clause, a.rule or "", a.run))
    if a.cmd == "show":
        for o, r in zip(outs, raws):
            print(json.dumps(dict(route=o["verdict"], lane=o["lane"], rule=o["rule_id"], tool_verdict=o["ai_verdict"],
                                  confidence=o["confidence"], why=o["why"], routing_notes=o["routing_notes"], quote=o["quote"],
                                  evidence=r.get("evidence"), thresholds=ev["thresholds"], engine=ev["engine"], model=ev["model"],
                                  playbook_version=ev["playbook_version"], contract_sha256=ev["contract_sha256"]), indent=1, ensure_ascii=False))
    else:
        o, r = outs[0], raws[0]
        fp = hashlib.sha256(json.dumps(r.get("evidence"), sort_keys=True).encode()).hexdigest()[:16]
        rec = dict(time=time.strftime("%Y-%m-%dT%H:%M:%S"), run=a.run, contract=a.cid, clause=a.clause, rule=a.rule,
                   tool_verdict=o["ai_verdict"], tool_route=o["verdict"], lawyer_verdict=a.lawyer, reason=a.reason, by=a.by,
                   evidence_fingerprint=fp, thresholds=ev["thresholds"], engine=ev["engine"], model=ev["model"])
        open(LOG, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("Recorded:", rec["contract"], rec["clause"], rec["rule"], rec["tool_verdict"], "->", rec["lawyer_verdict"])
