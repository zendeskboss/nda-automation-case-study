"""Build jev_runs/REVIEW_LIST.md: the findings where Jev and the LLM disagree, and the absent-preferred clauses
that Jev reads as present with no finding. Reads saved runs only; no Jev calls."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import review, jev_test  # noqa: E402

# Keyword search only, to help the reader find the clause. Jev's contract check gives no location.
KEYWORDS = {"PB14": r"indemni|hold harmless|liabilit", "PB15": r"solicit|entice|poach|hire",
            "PB16": r"compet|exclusiv", "PB17": r"residual|unaided memory|retained in"}
AGREE = jev_test.AGREE

pb = review.load_playbook()
dis, pres = [], []
for n in range(1, 31):
    cid = "C%02d" % n
    run = json.load(open(os.path.join(HERE, "jev_runs", cid + ".jev.json"), encoding="utf-8"))
    text = open(os.path.join(ROOT, "contracts", cid + ".md"), encoding="utf-8").read()
    raw = json.load(open(os.path.join(ROOT, "replay", cid + ".raw.json"), encoding="utf-8"))
    routed = review.route(raw, pb, text=text)["findings"]
    assert len(routed) == len(run["findings"]), cid
    for f, r in zip(routed, run["findings"]):
        assert (f["clause_no"], f["rule_id"]) == (r["clause_no"], r["rule_id"]), cid
        pc = (r.get("jev") or {}).get("position_check")
        if pc and pc["choice"] not in AGREE.get(r["llm_verdict"], set()):
            dis.append((cid, f, r, pc))
    for k, v in run["contract"]["answers"].items():
        rid = k[15:]
        if k.startswith("topic_present__") and rid in jev_test.ABSENT_PREFERRED and v["noul"] > 0.5:
            lines = [l for l in text.splitlines() if re.search(KEYWORDS[rid], l, re.I)]
            pres.append((cid, rid, v["noul"], lines))

def q(s): return "> " + (s or "").replace("\n", "\n> ")
o = ["# Jev review list", "",
     "Saved runs from `phase2/jev_runs/`. Quotes are copied from the saved reviews and the contracts.",
     "This list shows where Jev and the LLM differ. It does not say which one is right.", "",
     "## Part 1: Jev and the LLM disagree (%d findings)" % len(dis), "",
     "`position_check` probabilities: matches_preferred / meets_fallback / breaches / unclear.", ""]
for i, (cid, f, r, pc) in enumerate(dis, 1):
    p = pc["probabilities"]
    o += ["### %d. %s clause %s · %s %s" % (i, cid, f["clause_no"], f["rule_id"], f["topic"]), "",
          "- **LLM:** %s (confidence %.2f), routed as `%s`, lane `%s`" % (r["llm_verdict"], f["confidence"], r["routed"], r["lane"]),
          "- **Jev:** %s (confidence %.2f) · %s" % (pc["choice"], pc["confidence"], " / ".join("%.2f" % p.get(k, 0) for k in ("matches_preferred", "meets_fallback", "breaches", "unclear"))),
          "- **LLM reason:** %s" % f["why"], "", q(f["quote"]), ""]
o += ["## Part 2: absent-preferred clause present, no finding (%d)" % len(pres), "",
      "Jev's contract check reads the topic as present, but the LLM made no finding on it.",
      "Jev gives no location, so the lines below come from a keyword search. They are candidates only.", ""]
for i, (cid, rid, v, lines) in enumerate(pres, 1):
    o += ["### %d. %s · %s %s (Jev: present %.2f)" % (i, cid, rid, jev_test.rule_block(pb, rid)["topic"], v), ""]
    o += [q(l) + "\n" for l in lines[:4]] if lines else ["No keyword match. Read the contract.", ""]
open(os.path.join(HERE, "jev_runs", "REVIEW_LIST.md"), "w", encoding="utf-8").write("\n".join(o))
print("disagreements", len(dis), "present", len(pres))
