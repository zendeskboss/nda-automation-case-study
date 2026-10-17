"""Write page/src/data.js for the case study page, from the saved reviews and the eval results.

    python -X utf8 evals/run_evals.py && python -X utf8 tools/make_page_data.py && (cd redesign && node build.mjs)

Every number on the case study page comes from here, so the page and the engine cannot disagree.
"""
import collections, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import review  # noqa: E402

pb = review.load_playbook()
IDS = ["C%02d" % i for i in range(1, 31)]
K = {"matches": 0, "acceptable": 1, "deviation_draft": 2, "escalate": 3}
contracts, topics, reasons = [], collections.OrderedDict(), collections.Counter()
pass_high = 0
for r in pb["rules"]:
    topics[r["id"]] = [r["id"], r["topic"], r["severity"], r["lane"], 0, 0, 0, 0]
for cid in IDS:
    raw = json.load(open(os.path.join(ROOT, "replay", cid + ".raw.json"), encoding="utf-8"))
    text = open(os.path.join(ROOT, "contracts", cid + ".md"), encoding="utf-8").read()
    r = review.route(raw, pb, text=text)
    n = [0, 0, 0, 0]
    for f in r["findings"]:
        n[K[f["verdict"]]] += 1
        topics[f["rule_id"]][4 + K[f["verdict"]]] += 1
        if f["verdict"] == "matches" and f["lane"] in ("orange", "purple_human"):
            pass_high += 1
        if f["verdict"] not in ("escalate", "deviation_draft"):
            continue
        for note in f["routing_notes"]:
            for key, lab in [("No playbook rule", "No rule fits"), ("below", "Low confidence"),
                             ("view stays hidden", "Shadow rule deviation"), ("flags and quotes only", "Lawyer-only rule deviation"),
                             ("escalation condition", "Playbook answer says escalate"), ("confirms every fallback", "Shadow rule fallback"),
                             ("reason says", "AI's reason says escalate"), ("gave no draft", "No draft given"),
                             ("prompt injection", "Possible prompt injection")]:
                if key in note:
                    reasons[lab] += 1
    contracts.append([cid, r["paper"]] + n + [r["summary"]])
ev = json.load(open(os.path.join(ROOT, "evals", "results.json"), encoding="utf-8"))
ev["pass_high"] = pass_high
out = "export const CONTRACTS=%s;\nexport const TOPICS=%s;\nexport const REASONS=%s;\nexport const EVALS=%s;\n" % (
    json.dumps(contracts, ensure_ascii=False), json.dumps([t for t in topics.values() if sum(t[4:])], ensure_ascii=False),
    json.dumps(reasons.most_common(), ensure_ascii=False), json.dumps(ev, ensure_ascii=False))
open(os.path.join(ROOT, "page", "src", "data.js"), "w", encoding="utf-8", newline="\n").write(out)
print("wrote page/src/data.js:", {k: sum(c[2 + i] for c in contracts) for k, i in K.items()}, dict(reasons))
