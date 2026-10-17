"""Phase 2 dry run: send the saved reviews through Jev's post-lane checks.

Reads replay/<id>.raw.json and contracts/<id>.md, routes each finding with review.route, then asks Jev the
questions in jev_finding_check.request.json and jev_contract_check.request.json. Jev can only escalate.

This measures plumbing, speed, cost and agreement with the LLM. It does not measure accuracy: there are no
lawyer decisions or labels to compare with.

Usage: python phase2/jev_test.py C04          (one contract)
       python phase2/jev_test.py --all
       python phase2/jev_test.py --all --rescore   (new thresholds on saved answers, no Jev calls)
Needs TYPESAFE_API_KEY.
"""
import json, os, re, sys, time, argparse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import review  # noqa: E402

API = "https://api.typesafe.ai/v1/systemone"
MODEL = os.environ.get("JEV_MODEL", "jev-latest")
OUT = os.path.join(HERE, "jev_runs")
TEMPLATE_F = json.load(open(os.path.join(HERE, "jev_finding_check.request.json"), encoding="utf-8"))["questions"]
TEMPLATE_C = json.load(open(os.path.join(HERE, "jev_contract_check.request.json"), encoding="utf-8"))["questions"]

# ---------- Jev call ----------
def call_jev(state, questions, tries=5):
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key: raise RuntimeError("TYPESAFE_API_KEY is not set")
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode()
    for n in range(tries):
        req = urllib.request.Request(API, body, {"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
            data["_seconds"] = round(time.time() - t0, 2)
            return data
        except urllib.error.HTTPError as e:
            if e.code in (429, 529) and n < tries - 1:
                time.sleep(2 ** n); continue
            raise RuntimeError("Jev HTTP %s: %s" % (e.code, e.read().decode(errors="replace")[:300]))
        except (urllib.error.URLError, TimeoutError) as e:
            if n < tries - 1: time.sleep(2 ** n); continue
            raise RuntimeError("Jev network error: %s" % e)

# ---------- text helpers ----------
def norm(s):
    s = (s or "").replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()

def accept_edits(text):
    """The contract as it reads after the counterparty edits are accepted."""
    text = re.sub(r"\[\[DEL:.*?\]\]", "", text, flags=re.S)
    text = re.sub(r"\[\[COMMENT:.*?\]\]", "", text, flags=re.S)
    return re.sub(r"\[\[INS:\s?(.*?)\]\]", r"\1", text, flags=re.S)

def quote_found(quote, text):
    q = norm(quote)
    return bool(q) and (q in norm(text) or q in norm(accept_edits(text)))

def clause_lines(text):
    return [l for l in text.splitlines() if l.strip()]

def clause_for(quote, text):
    """The contract line(s) that hold the quote; the first 60 characters as a fallback."""
    lines = clause_lines(text)
    q = norm(quote)
    for i, l in enumerate(lines):
        if q and (q in norm(l) or q in norm(accept_edits(l))): return l
    head = q[:60]
    for l in lines:
        if head and (head in norm(l) or head in norm(accept_edits(l))): return l
    return None

DEF = re.compile(r"^\s*1\.\d+(?:\.\d+)?\s+([A-Z][\w ]{2,40}?)\s+(?:means|has the meaning|includes)\b")
XREF = re.compile(r"(?i)\bclauses?\s+(\d+(?:\.\d+)*)")

def related_for(clause, text, limit=6):
    lines = clause_lines(text)
    rel = []
    for l in lines:
        m = DEF.match(accept_edits(l))
        if m and l != clause and re.search(r"\b%s\b" % re.escape(m.group(1).strip()), accept_edits(clause)):
            rel.append(l)
    for ref in XREF.findall(clause):
        for l in lines:
            if re.match(r"\s*%s\s" % re.escape(ref), l) and l != clause and l not in rel:
                rel.append(l); break
    return [dict(clause_no=(re.match(r"\s*([\d.]+)", l) or [None, "?"])[1], text=l) for l in rel[:limit]]

def rule_block(pb, rid):
    """This rule exactly as the review prompt shows it (review.render_playbook), split into fields."""
    lines = review.render_playbook(pb).splitlines()
    out, on = dict(id=rid, topic="", preferred_position="", acceptable_fallbacks=[], not_acceptable=[]), False
    for l in lines:
        if re.match(r"^PB\d\d \|", l):
            on = l.startswith(rid + " |")
            if on: out["topic"] = l.split("|")[1].strip()
            continue
        if not on: continue
        s = l.strip()
        if s.startswith("PREFERRED:"): out["preferred_position"] = s[10:].strip()
        elif s.startswith("ACCEPTABLE:"): out["acceptable_fallbacks"].append(s[11:].strip())
        elif s.startswith("DEVIATION:"): out["not_acceptable"].append(s[10:].strip())
    return out

# ---------- per finding ----------
def finding_request(f, text, masked, pb, found_map):
    m = lambda s: review.mask(s)[0] if s else s
    clause = clause_for(f["quote"], text) or f["quote"]
    rule = rule_block(pb, f["rule_id"])
    state = dict(
        contract_id=None,
        parties=dict(us="Halyard"),
        finding=dict(clause_no=f["clause_no"], quote=m(f["quote"]), clause_text=m(clause), rule_id=f["rule_id"],
                     lane=f["lane"], llm_verdict=f["ai_verdict"], llm_confidence=f["confidence"], llm_reason=f["why"]),
        rule=rule,
        related_clauses=[dict(clause_no=r["clause_no"], text=m(r["text"])) for r in related_for(clause, text)],
        draft=dict(draft_redline=f["draft_redline"]))
    qs = {k: v for k, v in TEMPLATE_F.items() if not (k.startswith("draft_") and not f["draft_redline"])}
    if f["rule_id"] == "PB22":
        # Catch-all finding: ask whether a specific rule covers it instead.
        crit = {r["id"]: "The clause deals with %s." % r["topic"] for r in pb["rules"] if r["id"] != "PB22"}
        crit["none"] = "No rule in this list covers the clause."
        qs["pb22_rule"] = dict(type="choice", criteria=crit,
            instructions="Which playbook rule covers the subject of the clause in `finding.clause_text`? Judge the subject only.")
        qs.pop("rule_fit", None); qs.pop("position_check", None)
    return state, qs

AGREE = {"deviation": {"breaches"}, "matches": {"matches_preferred", "meets_fallback"}, "acceptable": {"matches_preferred", "meets_fallback"}}

def judge_finding(f, ans):
    """README thresholds. Returns the list of reasons Jev escalates this finding."""
    r, a = [], ans
    if "rule_fit" in a:
        if a["rule_fit"]["choice"] != "fits": r.append("rule_fit=%s" % a["rule_fit"]["choice"])
        elif a["rule_fit"]["confidence"] < 0.8: r.append("rule_fit confidence %.2f" % a["rule_fit"]["confidence"])
    if "position_check" in a:
        c = a["position_check"]["choice"]
        if c == "unclear": r.append("position unclear")
        elif c not in AGREE.get(f["ai_verdict"], set()): r.append("position %s vs LLM %s" % (c, f["ai_verdict"]))
    if "pb22_rule" in a and a["pb22_rule"]["choice"] != "none": r.append("catch-all fits %s" % a["pb22_rule"]["choice"])
    # Above 0.7 escalates. Between 0.3 and 0.7 is only a note to the lawyer (see finding_notes).
    if a.get("changed_elsewhere", {}).get("noul", 0) > 0.7: r.append("changed elsewhere %.2f" % a["changed_elsewhere"]["noul"])
    if f["lane"] == "purple_ai" and a.get("risk_to_us", {}).get("score", 0) >= 2: r.append("risk score %.1f" % a["risk_to_us"]["score"])
    if "draft_fixes_breach" in a and a["draft_fixes_breach"]["noul"] < 0.7: r.append("draft may not fix %.2f" % a["draft_fixes_breach"]["noul"])
    if a.get("draft_extra_change", {}).get("noul", 0) > 0.3: r.append("draft extra change %.2f" % a["draft_extra_change"]["noul"])
    if a.get("draft_new_duty_for_us", {}).get("noul", 0) > 0.3: r.append("draft new duty %.2f" % a["draft_new_duty_for_us"]["noul"])
    return r

def finding_notes(a):
    v = a.get("changed_elsewhere", {}).get("noul", 0)
    return ["another clause may change this one (%.2f)" % v] if 0.3 < v <= 0.7 else []

# ---------- per contract ----------
# Rules whose preferred position is that the clause is absent ("No indemnity", "No non-solicitation clause", ...).
# For these, a clause that is present with no finding is the risk; a missing clause is the good result.
# In production this belongs in playbook.yaml as a field, for example `expect: absent`.
ABSENT_PREFERRED = {"PB14", "PB15", "PB16", "PB17"}
def contract_request(routed, text, masked, pb):
    covered = {f["rule_id"] for f in routed["findings"]}
    state = dict(parties=dict(us="Halyard"), contract_text=masked,
                 findings=[dict(clause_no=f["clause_no"], rule_id=f["rule_id"], topic=f["topic"], lane=f["lane"],
                                verdict=f["verdict"], draft_redline=f["draft_redline"]) for f in routed["findings"]])
    qs = {k: v for k, v in TEMPLATE_C.items() if not k.startswith("topic_present__")}
    for r in pb["rules"]:
        if r["id"] in covered or r["id"] in ("PB21", "PB22"): continue
        rb = rule_block(pb, r["id"])
        qs["topic_present__" + r["id"]] = dict(type="noul", instructions=
            "Does `contract_text` contain a clause that deals with this topic: %s? The playbook position on it is: %s"
            % (rb["topic"], rb["preferred_position"]))
    return state, qs

def judge_contract(a):
    urgent, lawyer = [], []
    if a["document_type"]["choice"] in ("not_nda", "nda_inside_larger_deal"): urgent.append("document_type=" + a["document_type"]["choice"])
    for k, v in a.items():
        if k.startswith("has_"):
            if v["noul"] > 0.5: urgent.append("%s %.2f" % (k, v["noul"]))
            elif v["noul"] > 0.3: lawyer.append("%s %.2f" % (k, v["noul"]))
        if k.startswith("topic_present__"):
            rid = k[15:]
            if rid in ABSENT_PREFERRED:
                if v["noul"] > 0.5: lawyer.append("unreviewed %s clause present %.2f" % (rid, v["noul"]))
            elif v["noul"] < 0.5: lawyer.append("missing %s %.2f" % (rid, v["noul"]))
    if a["findings_conflict"]["noul"] > 0.3: lawyer.append("findings conflict %.2f" % a["findings_conflict"]["noul"])
    if a["overall_unusual"]["score"] >= 2: lawyer.append("unusual %.1f" % a["overall_unusual"]["score"])
    return urgent, lawyer

# ---------- run ----------
def run(cid, pb, pool):
    text = open(os.path.join(ROOT, "contracts", cid + ".md"), encoding="utf-8").read()
    raw = json.load(open(os.path.join(ROOT, "replay", cid + ".raw.json"), encoding="utf-8"))
    routed = review.route(raw, pb, text=text)
    masked, found_map = review.mask(text)
    rows, jobs = [], []
    for f in routed["findings"]:
        ok = quote_found(f["quote"], text)
        row = dict(clause_no=f["clause_no"], rule_id=f["rule_id"], lane=f["lane"], llm_verdict=f["ai_verdict"],
                   routed=f["verdict"], confidence=f["confidence"], quote_found=ok)
        rows.append(row)
        if not ok:
            row["jev"] = None; row["jev_escalate"] = ["quote not found: re-review"]; continue
        st, qs = finding_request(f, text, masked, pb, found_map); st["contract_id"] = cid
        jobs.append((row, f, pool.submit(call_jev, st, qs)))
    cst, cqs = contract_request(routed, text, masked, pb)
    cjob = pool.submit(call_jev, cst, cqs)
    for row, f, job in jobs:
        try:
            res = job.result(); row["jev"] = res["answers"]; row["usage"] = res.get("usage"); row["seconds"] = res["_seconds"]
            row["jev_escalate"] = judge_finding(f, res["answers"])
        except Exception as e:
            row["jev"] = None; row["error"] = str(e); row["jev_escalate"] = ["Jev error: escalate"]
    try:
        cres = cjob.result(); urgent, lawyer = judge_contract(cres["answers"])
        contract = dict(answers=cres["answers"], usage=cres.get("usage"), seconds=cres["_seconds"], urgent=urgent, lawyer=lawyer)
    except Exception as e:
        contract = dict(error=str(e), urgent=["Jev error: escalate"], lawyer=[])
    out = score(dict(contract_id=cid, model=MODEL, findings=rows, contract=contract))
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, cid + ".jev.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return out

def score(out):
    """Apply the thresholds to saved Jev answers. Changing a threshold needs no new Jev call."""
    rows, contract = out["findings"], out["contract"]
    for r in rows:
        if not r["quote_found"]: r["jev_escalate"], r["notes"] = ["quote not found: re-review"], []
        elif r.get("jev") is None: r["jev_escalate"], r["notes"] = ["Jev error: escalate"], []
        else:
            r["jev_escalate"] = judge_finding(dict(lane=r["lane"], ai_verdict=r["llm_verdict"]), r["jev"])
            r["notes"] = finding_notes(r["jev"])
    if "answers" in contract: contract["urgent"], contract["lawyer"] = judge_contract(contract["answers"])
    newly = [r for r in rows if r["jev_escalate"] and r["routed"] != "escalate"]
    out["result"] = "urgent" if contract["urgent"] else ("lawyer" if contract["lawyer"] or any(r["routed"] == "escalate" or r["jev_escalate"] for r in rows) else "release")
    out["summary"] = dict(findings=len(rows), routed_escalate=sum(r["routed"] == "escalate" for r in rows),
                          jev_new_escalations=len(newly), notes=sum(bool(r["notes"]) for r in rows),
                          quote_missing=sum(not r["quote_found"] for r in rows),
                          errors=sum("error" in r for r in rows) + ("error" in contract))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("ids", nargs="*"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--rescore", action="store_true", help="re-apply the thresholds to saved answers in jev_runs/; no Jev calls")
    a = ap.parse_args()
    ids = ["C%02d" % i for i in range(1, 31)] if a.all else a.ids
    sys.stdout.reconfigure(encoding="utf-8")
    show = lambda o: print("%s %-7s findings=%d routed_escalate=%d jev_new=%d notes=%d quote_missing=%d errors=%d" % (
        o["contract_id"], o["result"], *(o["summary"][k] for k in ("findings", "routed_escalate", "jev_new_escalations", "notes", "quote_missing", "errors"))))
    if a.rescore:
        for cid in ids:
            p = os.path.join(OUT, cid + ".jev.json")
            o = score(json.load(open(p, encoding="utf-8")))
            json.dump(o, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False); show(o)
        raise SystemExit
    pb = review.load_playbook()
    with ThreadPoolExecutor(a.workers) as pool:
        for cid in ids: show(run(cid, pb, pool))
