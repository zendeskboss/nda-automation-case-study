"""NDA review v2: checklist first.

Code splits the contract into clauses. Jev maps every clause to a playbook rule, then answers a fixed set of
questions for each (clause, rule) pair. Code turns the answers into findings in the v1 raw format, and the
unchanged v1 router (review.route) applies the playbook lanes. The LLM is not called: drafts are reused from
the saved v1 review where the same rule and clause match, otherwise a lawyer drafts.

Principles
- Every quote is a whole contract line copied by code, so a quote cannot be invented.
- Every clause is mapped. An edited clause that maps to no rule still becomes a finding, so no tracked edit is silent.
- Code checks and Jev can only make a result stricter. A Jev error becomes an escalation.
- Every decision keeps its evidence: the text, the questions, every probability, the thresholds, the versions.
  `decide()` rebuilds every finding from saved answers, so any decision can be replayed and challenged.
"""
import hashlib, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor

V2 = os.path.dirname(os.path.abspath(__file__))
PHASE2 = os.path.dirname(V2)
ROOT = os.path.dirname(PHASE2)
for p in (ROOT, PHASE2):
    if p not in sys.path: sys.path.insert(0, p)
import review, jev_test  # noqa: E402

ENGINE_VERSION = "v2.0"
# Thresholds. All decisions read them from here, and every evidence record stores them.
T = dict(
    map_min=0.25,          # a clause maps to every rule with at least this probability (max 3 rules)
    map_other=0.5,         # "other_term" at or above this makes an unrecognised-term finding
    comment_request=0.5,   # a margin comment that asks to move away from the position makes a deviation
    request_match=0.5,     # a known counterparty request (RQxx) is named at or above this
    borderline=0.3,        # a pass with P(breaches) + P(unclear) at or above this goes to a lawyer
)
REQUIRED_SKIP = {"PB21", "PB22"} | jev_test.ABSENT_PREFERRED  # topics whose absence is not a finding

# ---------- playbook (the prompt view only: review.render_playbook) ----------
def catalogue(pb):
    rules = {r["id"]: jev_test.rule_block(pb, r["id"]) for r in pb["rules"]}
    reqs = {}
    lines = review.render_playbook(pb).splitlines()
    on = False
    for l in lines:
        if l.startswith("KNOWN COUNTERPARTY REQUESTS"): on = True; continue
        if on and re.match(r"^RQ\d\d \|", l):
            rid, topic, rule, ans = [x.strip() for x in l.split("|", 3)]
            reqs[rid] = dict(id=rid, topic=topic, rule=rule.replace("rule", "").strip(), answer=ans)
    return rules, reqs

# ---------- splitter ----------
MARK = re.compile(r"\[\[(INS|DEL|COMMENT):\s*(.*?)\]\]", re.S)
NUM = re.compile(r"^\s*(?:\[\[INS:\s*)?(\d+(?:\.\d+)*)\.?\s")
END = re.compile(r"^\s*(?:Signed for|SIGNED|Signed by|IN WITNESS|This Agreement has been entered|EXECUTED|Executed)", re.I)
RECITAL = re.compile(r"^\s*\(([A-Z])\)\s")

def split(text):
    """Contract -> clause units. One unit per paragraph line, from the parties block to the signature block."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"^\s*(BETWEEN|\(1\)|THIS AGREEMENT|PARTIES)", l, re.I)), 0)
    end = next((i for i, l in enumerate(lines) if i > start and END.match(l)), len(lines))
    units, section = [], "Parties"
    for i in range(start, end):
        raw = lines[i]
        if not raw.strip(): continue
        marks = [(m.group(1), m.group(2).strip()) for m in MARK.finditer(raw)]
        after = jev_test.accept_edits(raw).strip()
        num = NUM.match(raw)
        if num: section = "Clauses"
        rec = RECITAL.match(raw)
        heading = not marks and len(after) < 70 and not re.search(r"[.;:,]\s*$", after)
        if heading or len(re.sub(r"\W", "", after)) < 20 and not marks: continue
        clause_no = num.group(1) if num else (("(%s)" % rec.group(1)) if rec else section)
        units.append(dict(uid="L%03d" % (i + 1), line=i + 1, clause_no=clause_no, raw=raw, after_edits=after,
                          edits=[dict(kind=k, text=t) for k, t in marks if k != "COMMENT"],
                          comments=[t for k, t in marks if k == "COMMENT"]))
    return group(units)

DEFINITION = re.compile(r"""^\s*[\d.]+\s+["“]?[A-Z][\w &'-]{1,50}["”]?(?:\s+or\s+["“][^"”]+["”])?\s+(?:means|shall mean|has the meaning|includes)\b""")

def group_key(u):
    """Sub-clauses join their clause (3.1.1 joins 3.1). A definition stays on its own, because each one is a separate term."""
    n = u["clause_no"]
    if not re.match(r"\d", n) or DEFINITION.match(u["after_edits"]): return u["uid"]
    return ".".join(n.split(".")[:2])

def group(units):
    out = []
    for u in units:
        k = group_key(u)
        if out and out[-1]["_key"] == k:
            g = out[-1]
            g["raw"] += "\n" + u["raw"]; g["after_edits"] += "\n" + u["after_edits"]
            g["edits"] += u["edits"]; g["comments"] += u["comments"]; g["lines"].append(u["line"])
        else:
            out.append(dict(u, _key=k, clause_no=k if k != u["uid"] else u["clause_no"], lines=[u["line"]]))
    for g in out: g.pop("_key")
    return out

# ---------- Jev questions ----------
def map_question(rules):
    crit = {rid: "%s. Playbook position: %s" % (r["topic"], r["preferred_position"][:180])
            for rid, r in rules.items() if rid != "PB22"}
    crit["other_term"] = "A substantive contract term that none of the listed topics covers."
    crit["not_a_term"] = "Not a contract term: party details, a recital, a heading, a cross-reference list or a signature line."
    crit["definition_or_interpretation"] = ("A definition or an interpretation rule (how words, headings or references are read) "
                                            "that sets no obligation by itself and is not the definition of Confidential Information.")
    return dict(type="choice", criteria=crit, instructions=
        "Which playbook topic does the clause in `clause.after_edits` deal with? Use `clause.comments` only to understand "
        "the clause. Judge the subject of the clause, not whether it is acceptable.")

def check_questions(unit, rule, reqs):
    qs = dict(position_check=dict(TEMPLATE_POS))
    if unit["comments"]:
        qs["comment_request"] = dict(type="noul", instructions=
            "Does any margin comment in `clause.comments` ask Halyard to change the clause so that it no longer gives "
            "the result in `rule.preferred_position`, or ask Halyard to accept something that `rule.preferred_position` does not give?")
    if rule["acceptable_fallbacks"]:
        crit = {"F%d" % (i + 1): a for i, a in enumerate(rule["acceptable_fallbacks"])}
        crit["none"] = "No listed fallback describes the clause."
        qs["fallback"] = dict(type="choice", criteria=crit, instructions=
            "Which acceptable fallback in `rule.acceptable_fallbacks` best describes the clause in `clause.after_edits`?")
    rq = {k: v for k, v in reqs.items() if v["rule"] == rule["id"]}
    if rq and (unit["edits"] or unit["comments"]):
        crit = {k: "%s: %s" % (v["topic"], v["answer"][:200]) for k, v in rq.items()}
        crit["none"] = "The edits and comments make none of these requests."
        qs["request"] = dict(type="choice", criteria=crit, instructions=
            "Which known counterparty request do the edits in `clause.edits` or the comments in `clause.comments` make?")
    return qs

TEMPLATE_POS = jev_test.TEMPLATE_F["position_check"] | dict(instructions=
    "Compare the clause as it reads after the counterparty edits are accepted (`clause.after_edits`) with the company "
    "position in `rule`. Use `related_clauses` when they change what the clause means. Ignore old-fashioned or wordy "
    "drafting when the substance is the same. Do not judge the margin comments here.")

def masked(s): return review.mask(s)[0] if s else s

def unit_state(unit, text, rule=None):
    st = dict(parties=dict(us="Halyard"), clause=dict(clause_no=unit["clause_no"], text_with_edits=masked(unit["raw"]),
              after_edits=masked(unit["after_edits"]), edits=[dict(e, text=masked(e["text"])) for e in unit["edits"]],
              comments=[masked(c) for c in unit["comments"]]))
    if rule is not None:
        st["rule"] = rule
        st["related_clauses"] = [dict(clause_no=r["clause_no"], text=masked(r["text"])) for r in jev_test.related_for(unit["raw"], text)]
    return st

# ---------- code checks (deterministic; they can only make a result stricter) ----------
WORDNUM = dict(one=1, two=2, three=3, four=4, five=5, six=6, seven=7, eight=8, nine=9, ten=10)
def _num(s):
    s = s.lower(); return int(s) if s.isdigit() else WORDNUM.get(s)

def code_checks(rid, after):
    out = []
    a = after
    if rid == "PB18":
        bad = re.findall(r"(?i)\b(Ireland|Irish|Delaware|New York|Scotland|Scottish|Northern Ireland|France|Germany|Netherlands|Singapore|California)\b", a)
        if re.search(r"(?i)governed by|jurisdiction", a) and bad:
            out.append(dict(check="PB18 other law or courts", result="fail", evidence=sorted(set(bad))))
    if rid == "PB07":
        m = re.search(r"(?i)within\s+(?:\w+\s+\()?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\)?\s+Business Days", a)
        if m and _num(m.group(1)) is not None and _num(m.group(1)) < 10:
            out.append(dict(check="PB07 return period under 10 Business Days", result="fail", evidence=m.group(0)))
    if rid == "PB12":
        m = re.search(r"(?i)period of\s+(?:\w+\s+\()?(\d+|one|two|three|four|five)\)?\s+years?", a)
        if m and re.search(r"(?i)surviv", a) and _num(m.group(1)) is not None and _num(m.group(1)) < 3:
            out.append(dict(check="PB12 survival under 3 years", result="fail", evidence=m.group(0)))
    return out

# ---------- run Jev ----------
def ask(pool, state, qs):
    return pool.submit(jev_test.call_jev, state, qs)

def analyse(cid, text, pb, pool, contract_dir="contracts"):
    """Call Jev for one contract. Returns the evidence record (answers included); decide() turns it into findings."""
    rules, reqs = catalogue(pb)
    units = split(text)
    mq = map_question(rules)
    jobs = [(u, ask(pool, unit_state(u, text), dict(map=mq))) for u in units]
    for u, j in jobs:
        try: r = j.result(); u["map"] = r["answers"]["map"]; u["usage"] = [r.get("usage")]
        except Exception as e: u["map"] = None; u["error"] = str(e)
    checks = []
    for u in units:
        if not u.get("map"): continue
        p = u["map"]["probabilities"]
        mapped = sorted((k for k, v in p.items() if k.startswith("PB") and v >= T["map_min"]), key=lambda k: -p[k])[:3]
        u["mapped"] = mapped
        for rid in mapped:
            st = unit_state(u, text, rules[rid])
            checks.append((u, rid, ask(pool, st, check_questions(u, rules[rid], reqs))))
    for u, rid, j in checks:
        u.setdefault("checks", {})
        try: r = j.result(); u["checks"][rid] = dict(answers=r["answers"], code=code_checks(rid, u["after_edits"])); u["usage"].append(r.get("usage"))
        except Exception as e: u["checks"][rid] = dict(error=str(e), code=code_checks(rid, u["after_edits"]))
    return dict(contract_id=cid, engine=ENGINE_VERSION, model=jev_test.MODEL, thresholds=T,
                playbook_version=pb["meta"]["version"], contract_sha256=hashlib.sha256(text.encode()).hexdigest(),
                created=time.strftime("%Y-%m-%dT%H:%M:%S"), units=units)

# ---------- decide (pure code: replayable) ----------
V = {"matches_preferred": "matches", "meets_fallback": "acceptable", "breaches": "deviation", "unclear": "deviation"}

def v1_drafts(cid):
    p = os.path.join(ROOT, "replay", cid + ".raw.json")
    if not os.path.exists(p): return {}
    d = {}
    for f in json.load(open(p, encoding="utf-8"))["findings"]:
        if f.get("verdict") == "deviation" and f.get("draft_redline"):
            for c in re.findall(r"\d+(?:\.\d+)*", str(f.get("clause_no"))):
                d.setdefault((f.get("rule_id"), c), f)
    return d

# Policy v2.1: the lawyer-load proposal. Every change is a rule from the playbook's structure or from the measured
# run-to-run noise, not a threshold fitted to these 30 contracts. v2.0 stays available for comparison.
POLICIES = {
    "v2.0": dict(sum_classes=False, borderline_by_severity=False, skip_unedited_template=False,
                 definitions_via_term=False, mutuality_whole_contract=False, one_missing_item=False),
    "v2.1": dict(sum_classes=True, borderline_by_severity=True, skip_unedited_template=True,
                 definitions_via_term=True, mutuality_whole_contract=True, one_missing_item=True),
}
# Borderline band for Low and Medium rules: two times the largest run-to-run spread that the stability test measured
# (0.12), so a pass is escalated when P(pass) - P(not pass) < 0.24, that is P(not pass) > 0.38. High rules keep 0.3.
NOISE_BAND = 0.38

def decide(ev, pb, policy="v2.0"):
    """Evidence record -> raw findings in the v1 schema. No model calls."""
    pol = POLICIES[policy]
    rules, reqs = catalogue(pb)
    sev = {r["id"]: r["severity"] for r in pb["rules"]}
    drafts = v1_drafts(ev["contract_id"])
    th = ev["thresholds"]
    paper = "ours" if any(u["edits"] or u["comments"] for u in ev["units"]) else "theirs"
    out, covered, missing = [], set(), []
    for u in ev["units"]:
        base = dict(clause_no=u["clause_no"], quote=u["raw"].strip(), request_id=None, draft_redline=None,
                    note_to_counterparty=None, fallback_cited=None, evidence=dict(uid=u["uid"], line=u["line"], policy=policy))
        if not u.get("map"):
            out.append(dict(base, rule_id=None, verdict="deviation", confidence=0.0,
                            why="Jev error on this clause (%s): a lawyer must decide." % u.get("error", "?")))
            continue
        p = u["map"]["probabilities"]
        base["evidence"]["map"] = {k: round(v, 3) for k, v in sorted(p.items(), key=lambda x: -x[1])[:5]}
        mapped = list(u["mapped"])
        if pol["definitions_via_term"] and not mapped and u.get("mapped_via_term"):
            mapped = [r for r in u["mapped_via_term"] if r in u.get("checks", {})]
            base["evidence"]["mapped_via_term"] = u.get("term")
        if not mapped:
            edited = bool(u["edits"] or u["comments"])
            if edited or p.get("other_term", 0) >= th["map_other"]:
                if pol["skip_unedited_template"] and paper == "ours" and not edited:
                    continue  # our own template text with no tracked edit: approved wording (needs a template hash check in production)
                why = ("Edited clause that maps to no playbook rule: a lawyer must decide." if edited
                       else "Substantive term that no playbook rule covers (Jev other_term %.2f)." % p.get("other_term", 0))
                out.append(dict(base, rule_id=None, verdict="deviation", confidence=1.0, why=why))
            continue
        for rid in mapped:
            covered.add(rid)
            c = u["checks"].get(rid, {})
            f = dict(base, rule_id=rid, evidence=dict(base["evidence"], rule=rid, code=c.get("code", [])))
            if "error" in c:
                out.append(dict(f, verdict="deviation", confidence=0.0, why="Jev error on the check: a lawyer must decide.")); continue
            a = c["answers"]; pc = a["position_check"]; pr = pc["probabilities"]
            f["evidence"]["answers"] = a
            p_pass = pr.get("matches_preferred", 0) + pr.get("meets_fallback", 0)
            p_not = pr.get("breaches", 0) + pr.get("unclear", 0)
            if pol["sum_classes"]:
                # Decide pass or not pass first, on the summed probabilities. Then name the kind.
                if p_pass >= p_not:
                    choice = "matches_preferred" if pr.get("matches_preferred", 0) >= pr.get("meets_fallback", 0) else "meets_fallback"
                    conf = p_pass
                else:
                    choice = "breaches" if pr.get("breaches", 0) >= pr.get("unclear", 0) else "unclear"
                    conf = pr["breaches"] if choice == "breaches" else 0.0
                verdict = V[choice]
                why = ["Jev reads the clause as %s against %s %s (pass %.2f, breach %.2f, unclear %.2f)." % (
                    choice.replace("_", " "), rid, rules[rid]["topic"], p_pass, pr.get("breaches", 0), pr.get("unclear", 0))]
            else:
                choice = pc["choice"]; verdict = V[choice]; conf = pr[choice] if choice != "unclear" else 0.0
                why = ["Jev reads the clause as %s (%.2f) against %s %s." % (choice.replace("_", " "), pr[choice], rid, rules[rid]["topic"])]
            if a.get("comment_request", {}).get("noul", 0) >= th["comment_request"]:
                verdict, conf = "deviation", a["comment_request"]["noul"]
                why.append("A margin comment asks to move away from the playbook position (%.2f)." % conf)
            fails = [x for x in c.get("code", []) if x["result"] == "fail"]
            if fails:
                verdict, conf = "deviation", 1.0
                why.append("Code check failed: %s." % "; ".join("%s (%s)" % (x["check"], x["evidence"]) for x in fails))
            if base["evidence"].get("mapped_via_term") and verdict in ("matches", "acceptable"):
                # The term mapping adds context for the lawyer. It must not let a tracked edit pass unseen.
                why.append("Edited definition of '%s': this must be reviewed by a lawyer." % base["evidence"]["mapped_via_term"])
            band = th["borderline"] if not pol["borderline_by_severity"] or sev[rid] == "High" else NOISE_BAND
            if verdict in ("matches", "acceptable") and p_not >= band:
                why.append("Borderline: breach or unclear %.2f, so this must be reviewed by a lawyer." % p_not)
            fb = a.get("fallback", {})
            if verdict == "acceptable" and fb.get("choice", "none") != "none":
                f["fallback_cited"] = rules[rid]["acceptable_fallbacks"][int(fb["choice"][1:]) - 1]
            rq = a.get("request", {})
            if rq.get("choice", "none") != "none" and rq["probabilities"][rq["choice"]] >= th["request_match"]:
                f["request_id"] = rq["choice"]
            if verdict == "deviation":
                d = next((drafts[(rid, n)] for n in [u["clause_no"]] + [u["clause_no"].rsplit(".", 1)[0]] if (rid, n) in drafts), None)
                if d:
                    f["draft_redline"], f["note_to_counterparty"] = d["draft_redline"], d.get("note_to_counterparty")
                    f["evidence"]["draft_source"] = "v1 replay %s clause %s" % (rid, d["clause_no"])
            out.append(dict(f, verdict=verdict, confidence=round(conf, 4), why=" ".join(why)))
    mut = ev.get("contract_checks", {}).get("mutuality")
    skip = set(REQUIRED_SKIP) | ({"PB01"} if pol["mutuality_whole_contract"] and mut else set())
    if pol["mutuality_whole_contract"] and mut and mut["noul"] < 0.5:
        out.append(dict(clause_no="Whole agreement", quote=None, rule_id="PB01", verdict="deviation", confidence=round(1 - mut["noul"], 4),
                        request_id=None, draft_redline=None, note_to_counterparty=None, fallback_cited=None,
                        why="Jev reads the agreement as not equally mutual (mutual %.2f): a lawyer must decide." % mut["noul"],
                        evidence=dict(policy=policy, contract_check="mutuality", answer=mut)))
    for rid in rules:
        if rid not in covered and rid not in skip: missing.append(rid)
    if missing and pol["one_missing_item"]:
        out.append(dict(clause_no="Missing", quote=None, rule_id=None, verdict="deviation", confidence=1.0, request_id=None,
                        draft_redline=None, note_to_counterparty=None, fallback_cited=None,
                        why="No clause maps to these topics: %s. A lawyer decides whether each one needs a clause." % "; ".join(
                            "%s %s (%s)" % (r, rules[r]["topic"], sev[r]) for r in missing),
                        evidence=dict(policy=policy, missing=missing)))
    else:
        for rid in missing:
            out.append(dict(clause_no="Missing", quote=None, rule_id=rid, verdict="deviation", confidence=1.0, request_id=None,
                            draft_redline=None, note_to_counterparty=None, fallback_cited=None,
                            why="No clause in the contract maps to %s %s: a lawyer must decide." % (rid, rules[rid]["topic"]),
                            evidence=dict(missing=rid)))
    return dict(contract_type=None, paper=paper, parties_ok=None, summary="v2 checklist review", findings=out,
                prompt_version=ENGINE_VERSION if policy == "v2.0" else "%s/%s" % (ENGINE_VERSION, policy))

# ---------- v2.1 extra Jev calls (added to saved evidence; nothing else is re-run) ----------
MUTUALITY_Q = dict(type="noul", instructions=
    "Do the confidentiality obligations in `contract_text` bind both parties equally, so that each party can be the "
    "disclosing party and the receiving party, and the definition of confidential information protects both?")
TERM = re.compile(r"""^\s*[\d.]+\s+["“]?(.+?)["”]?\s+(?:or\s+["“][^"”]+["”]\s+)?(?:means|shall mean|has the meaning|includes)\b""")

def patch_v21(ev, text, pb, pool):
    """Adds the two v2.1 inputs to a saved evidence record: rule checks for edited definitions, and one
    whole-contract mutuality question. Existing answers are not touched."""
    rules, reqs = catalogue(pb)
    jobs = []
    for u in ev["units"]:
        m = TERM.match(u["after_edits"])
        if not (m and DEFINITION.match(u["after_edits"]) and u.get("map") and not u["mapped"] and (u["edits"] or u["comments"])): continue
        term = m.group(1).strip()
        users = {}
        for v in ev["units"]:
            if v is u or not v.get("mapped"): continue
            if re.search(r"\b%s\b" % re.escape(term), v["after_edits"]):
                for r in v["mapped"]: users[r] = users.get(r, 0) + 1
        u["term"] = term
        u["mapped_via_term"] = sorted(users, key=lambda r: -users[r])[:3]
        u.setdefault("checks", {}); u.setdefault("usage", [])
        for rid in u["mapped_via_term"]:
            jobs.append((u, rid, ask(pool, unit_state(u, text, rules[rid]), check_questions(u, rules[rid], reqs))))
    mj = ask(pool, dict(parties=dict(us="Halyard"), contract_text=review.mask(text)[0]), dict(mutuality=MUTUALITY_Q))
    for u, rid, j in jobs:
        try: r = j.result(); u["checks"][rid] = dict(answers=r["answers"], code=code_checks(rid, u["after_edits"])); u["usage"].append(r.get("usage"))
        except Exception as e: u["checks"][rid] = dict(error=str(e), code=code_checks(rid, u["after_edits"]))
    try: r = mj.result(); ev.setdefault("contract_checks", {})["mutuality"] = r["answers"]["mutuality"]; ev["contract_usage"] = r.get("usage")
    except Exception as e: ev.setdefault("contract_checks", {})["mutuality_error"] = str(e)
    ev["patches"] = sorted(set(ev.get("patches", [])) | {"v2.1"})
    return ev

def review_v2(cid, text, pb, pool):
    ev = analyse(cid, text, pb, pool)
    raw = decide(ev, pb)
    return ev, raw, review.route(raw, pb, text=text)
