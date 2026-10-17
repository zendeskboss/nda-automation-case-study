"""Build review.html (all-reviews.html in the package): a read-only view of the 30 saved reviews, routed by review.py.

    python -X utf8 tools/make_review_page.py
"""
import html, json, os, sys

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
os.chdir(PROJ)
import review  # noqa: E402

pb = review.load_playbook()
ids = ["C%02d" % i for i in range(1, 31)]
LABEL = {"escalate": "Lawyer decides", "deviation_draft": "Fix drafted", "acceptable": "Acceptable", "matches": "Matches"}
e = lambda s: html.escape("" if s is None else str(s))

contracts, rows = [], []
tot = {k: 0 for k in LABEL}
for cid in ids:
    raw = json.load(open(f"replay/{cid}.raw.json", encoding="utf-8"))
    r = review.route(raw, pb, text=open(f"contracts/{cid}.md", encoding="utf-8").read())
    counts = {k: 0 for k in LABEL}
    for f in r["findings"]:
        counts[f["verdict"]] += 1
        tot[f["verdict"]] += 1
    low = sum(1 for f in r["findings"] if f["confidence"] < r["threshold"] and f["ai_verdict"] != "matches")
    rows.append(f'<tr data-go="{cid}"><td><a href="#{cid}">{cid}</a></td><td>{e(r["paper"])}</td>'
                f'<td class="n esc">{counts["escalate"] or ""}</td><td class="n drf">{counts["deviation_draft"] or ""}</td>'
                f'<td class="n">{counts["acceptable"] or ""}</td><td class="n">{counts["matches"] or ""}</td><td class="n">{low or ""}</td></tr>')
    cards = []
    for f in r["findings"]:
        notes = "".join(f"<li>{e(n)}</li>" for n in f["routing_notes"])
        extra = ""
        if f.get("fallback_cited"): extra += f'<p class="k">Fallback cited</p><p>{e(f["fallback_cited"])}</p>'
        if f.get("request_answer"): extra += f'<p class="k">Known request {e(f["request_id"])}: playbook answer</p><p>{e(f["request_answer"])}</p>'
        if f.get("draft_redline"): extra += f'<p class="k">Drafted redline{" (an instruction, not wording)" if f.get("draft_kind") == "instruction" else ""}</p><p class="draft">{e(f["draft_redline"])}</p>'
        if f.get("note_to_counterparty"): extra += f'<p class="k">Note to counterparty</p><p>{e(f["note_to_counterparty"])}</p>'
        shadow = '<span class="tag sh">Shadow mode: lawyer sees this only after deciding</span>' if f["shadow"] else ""
        cards.append(f'''<article class="card v-{f["verdict"]}" data-v="{f["verdict"]}" data-low="{int(f["confidence"] < r["threshold"])}">
<header><span class="pill">{LABEL[f["verdict"]]}</span><b>Clause {e(f["clause_no"])}</b>
<span class="meta">{e(f["rule_id"])} · {e(f["topic"])} · severity {e(f["severity"])} · lane {e(f["lane_name"])} · AI said <i>{e(f["ai_verdict"])}</i>{" (no rule fits, so code treats it as <i>deviation</i>)" if f["rule_id"] == "PB22" and f["ai_verdict"] != "deviation" else ""} · confidence {f["confidence"]:.2f}</span>{shadow}</header>
<blockquote>{e(f["quote"])}</blockquote>
<p class="k">Why (AI)</p><p>{e(f["why"])}</p>{extra}
{f'<p class="k">Why it was routed here</p><ul>{notes}</ul>' if notes else ""}
</article>''')
    contracts.append(f'''<section id="{cid}" class="contract">
<h2>{cid} <small>{e(r["contract_type"])} · {e(r["paper"])} paper · parties ok: {e(r["parties_ok"])}</small></h2>
<p class="summary">{e(r["summary"])}</p>
{"".join(cards)}
<p class="top"><a href="#overview">Back to overview</a></p></section>''')

page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NDA Review Check</title><style>
:root{{--bg:#fbfaf7;--fg:#1d1d1b;--mute:#6b6a65;--card:#fff;--line:#e3e1da;--esc:#b4361f;--drf:#6b3fa0;--ok:#2f6f4f;--acc:#8a6d1c;--q:#f3f1ea}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#171715;--fg:#ecebe6;--mute:#a09e97;--card:#21211e;--line:#34332f;--esc:#ef7a62;--drf:#b896e6;--ok:#7cc59e;--acc:#d9b85a;--q:#2a2a26}}}}
:root[data-theme="dark"]{{--bg:#171715;--fg:#ecebe6;--mute:#a09e97;--card:#21211e;--line:#34332f;--esc:#ef7a62;--drf:#b896e6;--ok:#7cc59e;--acc:#d9b85a;--q:#2a2a26}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:900px;margin:0 auto;padding:24px 16px 80px}}h1{{font-size:24px;margin:0 0 4px}}h2{{font-size:20px;margin:40px 0 4px}}h2 small{{font-weight:400;color:var(--mute);font-size:13px}}
.lede{{color:var(--mute);margin:0 0 20px}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}td.esc{{color:var(--esc);font-weight:600}}td.drf{{color:var(--drf);font-weight:600}}tr[data-go]{{cursor:pointer}}tr[data-go]:hover{{background:var(--q)}}
a{{color:inherit}}.bar{{position:sticky;top:0;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);display:flex;gap:8px;flex-wrap:wrap;z-index:2}}
.bar button{{font:inherit;font-size:13px;padding:4px 10px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;cursor:pointer}}.bar button[aria-pressed="true"]{{border-color:var(--fg);font-weight:600}}
.card{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);border-radius:6px;padding:12px 14px;margin:10px 0}}
.v-escalate{{border-left-color:var(--esc)}}.v-deviation_draft{{border-left-color:var(--drf)}}.v-acceptable{{border-left-color:var(--acc)}}.v-matches{{border-left-color:var(--ok)}}
.card header{{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline}}.meta{{color:var(--mute);font-size:13px}}
.pill{{font-size:12px;font-weight:600;padding:1px 8px;border-radius:999px;border:1px solid currentColor}}.v-escalate .pill{{color:var(--esc)}}.v-deviation_draft .pill{{color:var(--drf)}}.v-acceptable .pill{{color:var(--acc)}}.v-matches .pill{{color:var(--ok)}}
.tag.sh{{font-size:12px;color:var(--drf)}}blockquote{{margin:10px 0;padding:8px 12px;background:var(--q);border-radius:4px;font-family:Georgia,serif;overflow-wrap:anywhere}}
.k{{margin:10px 0 2px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mute)}}.card p{{margin:0}}.card ul{{margin:2px 0 0;padding-left:20px}}.draft{{white-space:pre-wrap}}
.summary{{margin:0 0 8px}}.top{{font-size:13px}}.hide{{display:none}}
</style></head><body><main>
<h1 id="overview">NDA review check</h1>
<p class="lede">Read-only view of the 30 saved AI reviews, after review.py routing. "AI said" is the model's own verdict. The pill is where code sent it. Do not edit the findings: write any problem you see in RUN_NOTES.md. Totals: {tot["escalate"]} for a lawyer, {tot["deviation_draft"]} with a drafted fix, {tot["acceptable"]} acceptable, {tot["matches"]} match.</p>
<table><thead><tr><th>Contract</th><th>Paper</th><th class="n">Lawyer decides</th><th class="n">Fix drafted</th><th class="n">Acceptable</th><th class="n">Matches</th><th class="n">Low confidence</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
<div class="bar" role="group" aria-label="Filter findings">
<button data-f="all" aria-pressed="true">All</button><button data-f="escalate" aria-pressed="false">Lawyer decides</button><button data-f="deviation_draft" aria-pressed="false">Fix drafted</button>
<button data-f="acceptable" aria-pressed="false">Acceptable</button><button data-f="matches" aria-pressed="false">Matches</button><button data-f="low" aria-pressed="false">Low confidence</button></div>
{"".join(contracts)}
</main><script>
document.querySelectorAll('tr[data-go]').forEach(t=>t.onclick=()=>location.hash=t.dataset.go);
const bs=document.querySelectorAll('.bar button');
bs.forEach(b=>b.onclick=()=>{{bs.forEach(x=>x.setAttribute('aria-pressed',x===b));const f=b.dataset.f;
document.querySelectorAll('.card').forEach(c=>c.classList.toggle('hide',!(f==='all'||(f==='low'?c.dataset.low==='1':c.dataset.v===f))));}});
</script></body></html>'''
open("review.html", "w", encoding="utf-8").write(page)
print("written", tot)
