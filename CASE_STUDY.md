# NDA review: case study

## Bottom line

An AI tool sorts NDA clauses against the lawyers' playbook. Code decides what a lawyer sees. A lawyer approves everything before it goes out.

The case study page (`case-study.html`) is the current version. It leads with the evals that need no lawyer: coverage of tracked edits, variance between re-runs, consistency across contracts, and hostile input. See `evals/EVAL_REPORT.md`.

Code applies the routing rules, but it depends on the AI's verdict and confidence, so the AI's errors flow through. A clause the AI calls a match does not reach a lawyer. The shadow pilot needs a random sample of those.

Most of the remaining effort is in implementation: how NDAs reach the tool, in which format, and where the lawyer sees the result. The [annex](ANNEX_ASSUMPTIONS.md) lists the options and every assumption behind this test.

Two limits: the rules in this test are our assumptions, not positions confirmed by a legal team, and the findings are not yet scored against a lawyer's answer key.

## What it takes to move forward

1. **About 45 minutes from each legal team member** to fill in the [process discovery workbook](discovery/process_discovery_workbook.xlsx). It shows where their time goes, how they decide, and what must stay with people.
2. **Three one-hour sessions with the legal team** to fill in the [playbook worksheet](worksheet/playbook_worksheet.xlsx). This replaces every assumed position with a confirmed one.
3. **One playbook owner** who signs off each version of the rules.
4. **An implementation route**, chosen after a short look at how NDAs arrive today. This is the largest piece of work. See the [annex](ANNEX_ASSUMPTIONS.md#implementation-options).
5. **A shadow pilot on incoming NDAs.** On high-stakes rules the lawyer decides first and the tool's view is logged. A rule gets more automation only when the log shows the tool agrees with the lawyers often enough. The lawyers set that bar.
6. **A decision on how much routine work stays with people**, so junior lawyers still learn from the easy NDAs. See stage 11.

## Results from the test

This is where findings went. It is not an accuracy score.

| What happened to each clause finding | Findings | Share |
|---|---|---|
| Matches the playbook | 322 | 56% |
| Fits an approved fallback | 67 | 12% |
| Drafted fix for a lawyer to approve | 49 | 9% |
| Sent to a lawyer to decide | 134 | 23% |
| Total, across 30 NDAs | 572 | |

Each NDA had between 0 and 10 findings for a lawyer to decide.

## How the pieces fit

| Stage | Output | Status |
|---|---|---|
| 0. Process discovery | `discovery/process_discovery_workbook.xlsx` | Template ready |
| 1. Problem statement | Problem statement document | Done |
| 2. Tracker | Google Sheet with risk IDs R01 to R16 | Done |
| 3. Lawyer worksheet | `worksheet/playbook_worksheet.xlsx` | Built |
| 4. Playbook | `worksheet/worksheet_to_yaml.py` → `playbook.yaml` | Built |
| 5. Test set | `contracts/` (30 NDAs) | Done |
| 6. Review engine | `review.py` | Done |
| 7. Saved reviews | `replay/`, `preds/`, `review.html`, `RUN_NOTES.md` | Done |
| 8. Lawyer review page | `static/index.html`, `server.py`; demo app in `demo/index.html` | Prototype |
| 9. Intake | Outline below; options in the [annex](ANNEX_ASSUMPTIONS.md#implementation-options) | Not built |
| 10. Learn and widen | Outline below | Not built |
| 11. Keep the easy wins | Outline below | Not built |

Open any stage below for the detail.

---

<details>
<summary><b>0. Process discovery</b>: the team tells us how the work is done</summary>

File: [`discovery/process_discovery_workbook.xlsx`](discovery/process_discovery_workbook.xlsx)

Each member of the legal team fills in the workbook before we build anything. It takes about 45 minutes. It is a general template, so it works for any team and any process, not only NDAs.

| Tab | What the team writes | What we do with it |
|---|---|---|
| Tasks | Each task, how often, how long, how much judgement, the worst case | Find where the time goes, and which work is routine |
| How you decide | What they check first, what is fine, what makes them stop | The first draft of the playbook rules (stage 3) |
| Examples | Real cases with names removed, including hard ones | Test cases from real work (assumption A6 in the annex) |
| Tools and data | Where the work arrives, happens and ends up | The intake route (stage 9 and the annex) |
| Worries | Concerns and red lines, and how firm each one is | Hard limits on what the tool may do (stage 11) |
| Next steps | Actions, owners and dates | One shared action list |

A Summary tab builds itself. It shows hours a month for each task and a "fit for a tool" score: hours × (4 − judgement) × (4 − impact). Tasks that the team marks "Keep with people" are left out of the score.

The workbook makes promises to the team: they decide what stays with people, it is not used to judge their work, and they see what we build before anyone uses it.

In this case study the workbook is a blank template. No legal team filled it in.

</details>

<details>
<summary><b>1. Problem statement</b>: what we are solving</summary>

NDAs are high volume and mostly low risk, but every one waits for a lawyer. The business waits with it, and lawyers spend time on clauses that match the template word for word.

The goal: a lawyer spends time only on the clauses that need a lawyer, and can trust that the tool missed nothing.

</details>

<details>
<summary><b>2. Tracker</b>: which risks an NDA carries</summary>

The Google Sheet tracker logs each NDA and lists the risks an NDA can carry, each with an ID (R01 to R16). For example, R02 is the confidentiality period and R07 is governing law.

Every playbook rule points back to a risk ID, so every finding traces to a risk in the tracker.

The tracker names each risk but does not say where the line is. It says the confidentiality period is a risk. It does not say that 2 to 5 years is fine, 7 years is not, and a perpetual term needs a lawyer. That knowledge sat with the lawyers. Stage 3 writes it down.

</details>

<details>
<summary><b>3. Lawyer worksheet</b>: the lawyers define the rules</summary>

File: [`worksheet/playbook_worksheet.xlsx`](worksheet/playbook_worksheet.xlsx)

One row per topic in the template NDA. For each topic the lawyers write:

- the preferred position (what the template says)
- the fallbacks they would sign without a second look
- the red lines, as exact as possible (days, years, named words)
- a severity: High, Medium or Low
- how to fix a deviation, and a standard note to the counterparty
- whether a lawyer has confirmed the position (if not, it is marked "ASSUMED")

Three questions per topic set how far the tool may go:

- Q1. Could a wrong call cost IP, money or freedom to operate?
- Q2. Would two of our lawyers always make the same call from these words?
- Q3. Are you happy for the tool to draft the fix for a lawyer to approve?

The sheet suggests a lane from the answers. The lawyer can overrule it.

| Answers | Lane | When the clause deviates, the tool... |
|---|---|---|
| Q1 No, Q2 Yes, Q3 Yes | AI drafts | drafts the fix and the note for a lawyer to approve |
| Q1 Yes, Q2 Yes, Q3 Yes | Shadow | forms a view but hides it until the lawyer decides; both answers are logged |
| Any other answer | Lawyer only | flags and quotes the clause, and drafts nothing |

Other tabs cover scope, requests that counterparties often make, and escalation. A worked example tab shows one finished row.

In this case study no legal team filled in the worksheet. We wrote the playbook from the template and our own knowledge, and marked every unconfirmed position "ASSUMED".

</details>

<details>
<summary><b>4. Playbook</b>: the worksheet becomes rules the tool follows</summary>

Files: [`worksheet/worksheet_to_yaml.py`](worksheet/worksheet_to_yaml.py) → `playbook.yaml`

The script reads the worksheet and writes a draft playbook in the same format as `playbook.yaml`. Nobody retypes the lawyers' words. It lists every gap: a topic with no position, a request with no answer, a position not yet confirmed. The owner reviews the draft and freezes it with a version number.

```bash
python3 worksheet/worksheet_to_yaml.py worksheet/playbook_worksheet.xlsx worksheet/playbook.draft.yaml
```

`playbook.yaml` is plain text, so a lawyer can read it and every change shows as a diff. It holds:

- scope, owner and the severity scale
- rules PB01 to PB21, one per topic
- PB22, a fixed catch-all: any clause the tool cannot place goes to a lawyer
- requests RQ01 to RQ12, each with the team's standard answer

The current version is 1.0, frozen on 14 October 2026.

</details>

<details>
<summary><b>5. Test set</b>: 30 realistic NDAs</summary>

Folder: `contracts/`

30 mutual NDAs. Some are on the Halyard template with the counterparty's tracked changes. Some are on the counterparty's paper. They cover the common asks: a shorter confidentiality period, a different governing law, residuals, non-solicits, and one-way NDAs presented as mutual.

Tracked changes appear as `[[INS: ...]]`, `[[DEL: ...]]` and `[[COMMENT: ...]]`. That is the format the intake step would produce from a Word file.

</details>

<details>
<summary><b>6. Review engine</b>: the AI reads, code decides</summary>

File: `review.py`

1. It turns the playbook into the AI's instructions. The AI sees those rules and no other standard.
2. The AI reads one contract. For each clause it returns a rule ID, a verdict, an exact quote, a confidence score, a one-line reason and, for a deviation, a draft fix.
3. Code routes each finding by the lane the lawyers chose. A finding goes to a lawyer if no rule fits, if the rule is Lawyer only or Shadow, or if the AI's confidence is below 0.6.

The AI does the reading. Code decides what the lawyer sees, because code can be tested and audited, and the lawyers change it by changing the playbook.

</details>

<details>
<summary><b>7. Saved reviews</b>: what the AI said and where it went</summary>

| File | Contents | Purpose |
|---|---|---|
| `replay/` | The AI's raw answer for each contract | Re-run the routing or the demo without an API key |
| `preds/` | Routed findings, cut down to the fields an evaluation reads | Score against a lawyer's answer key, kept outside this folder |
| `review.html` | All 30 routed reviews on one page | Read every finding without starting the server |
| `RUN_NOTES.md` | Model, method and every problem found | Audit trail |
| `results.zip` | `replay/`, `preds/` and `RUN_NOTES.md` | Hand-in |

Each contract had its own fresh AI reviewer, so no finding carried over from one contract to the next.

Problems found: some quotes did not match the contract text exactly, one file had an encoding fault, and reviewers did not always choose the same way on edge cases. A script now checks every quote against the contract, and all 572 pass. No verdict was changed by hand.

</details>

<details>
<summary><b>8. Lawyer review page</b>: what the lawyer sees</summary>

Files: `static/index.html` (the page) and `server.py` (a local server). Decisions are saved to `logs/shadow_log.jsonl`.

The lawyer sees:

1. A one-line summary: who sent it, on whose paper, and whether it looks OK.
2. Findings in order: decisions for the lawyer, then drafted fixes to approve, then acceptable, then matches.
3. For each finding: the quote, the rule, the severity and the reason, plus the team's standard answer for known requests.
4. On Shadow rules, the tool's view stays hidden until the lawyer decides.

Each decision is logged next to the tool's verdict.

```bash
python3 server.py
```

Then open http://localhost:8765. Replay mode uses the saved reviews. Live mode needs an API key.

Replay mode lists all 30 contracts from `contracts/`. To use another folder, set `NDA_CONTRACTS`.

To try it without Python, open `demo/index.html` in a browser. This demo app holds the 30 saved reviews in one file and needs no server. It has no Live mode, and decisions stay in the viewer's browser. To rebuild it after the reviews change, run `python3 demo/build_demo.py`.

</details>

<details>
<summary><b>9. Intake</b>: from the counterparty to the lawyer (not built)</summary>

1. Receive through one front door: a shared inbox or a request form that asks for the counterparty, deal owner, purpose and deadline.
2. Log a row in the tracker.
3. Screen before any AI runs:
   - Not an NDA: send it to a lawyer untouched.
   - Counterparty on the "always a lawyer" list from the worksheet: send it to a lawyer.
   - Note whether it is our paper or theirs.
4. Convert the Word file to text, with tracked changes as `[[INS]]` and `[[DEL]]` markers.
5. Review with `review.py` against the frozen playbook.
6. Queue it on the lawyer's page as green (nothing to decide), amber (drafted fixes only) or red (at least one decision).
7. Decide and send. The lawyer approves, edits or overrules, and the tracker row moves on.

The smallest working version: a shared inbox, a script that runs on each new attachment, and the existing review page.

</details>

<details>
<summary><b>10. Learn and widen</b>: more automation, one rule at a time (not built)</summary>

1. On Shadow rules, the lawyer decides without seeing the tool's view, and the log records both answers.
2. For each rule, measure how often the tool agreed with the lawyer. A miss on a High rule costs 5, a miss on a Low rule costs 1.
3. When a rule meets the bar the lawyers set, the owner may move it from Shadow to AI drafts. That is a one-line change in the playbook and a new version number.
4. Set the confidence threshold from the log. The current 0.6 is a placeholder.
5. Send each overrule back to the worksheet. It usually means a rule's wording is unclear.

</details>

<details>
<summary><b>11. Keep the easy wins</b>: leave room for people to learn (future state, not built)</summary>

Junior lawyers build judgement on the easy NDAs. If the tool takes all of the easy work, two things happen:

- Juniors lose the work they learn from, so fewer people grow into senior reviewers.
- Everyone is left with only the hard cases. A full day of hard cases wears people out.

So the tool should hand some routine work back to people on purpose. We have not chosen the mechanism. Three options, which can be combined:

| Option | How it works | What it costs | What else it gives us |
|---|---|---|---|
| Learning mode per user | A setting per lawyer. For a lawyer in learning mode, the tool hides its view on every clause. The lawyer reviews first, then sees the tool's view and compares. | Slower reviews for those lawyers | Feedback on each review, at the moment it is most useful |
| Pass-through rate | One NDA in every N goes to a lawyer with no tool output. The tool still runs in the background and logs its view. The lawyers set N. | Fewer NDAs get the time saving | An unbiased sample to keep measuring the tool after go-live |
| Feedback in the document | The lawyer marks each finding as agree or disagree, with a short reason, where they read the contract | A few seconds per finding | Overrules go back into the worksheet and improve the rules |

The first two reuse the shadow mechanism that already exists: the tool's view stays hidden and the lawyer's decision is logged. The third extends the decision log on the review page.

Our starting suggestion is learning mode for junior lawyers plus a small pass-through rate for everyone. The legal team should make the final choice.

</details>

<details>
<summary><b>Folder map</b></summary>

```
NDA automation case study/
├── CASE_STUDY.md               this page
├── case_study.html             the same case study as a rich page (published artifact)
├── page/                       source of case_study.html (Zendesk Garden); `npm run build`
├── build_package.py            builds "NDA review case study.zip" for a new reader
├── PACKAGE_README.md           becomes README.md in that zip
├── ANNEX_ASSUMPTIONS.md        assumptions and implementation options
├── TALK_TRACK.md               presenter notes
├── discovery/
│   └── process_discovery_workbook.xlsx   stage 0: the team describes the work
├── worksheet/
│   ├── playbook_worksheet.xlsx   stage 3: lawyers define the rules and lanes
│   └── worksheet_to_yaml.py      stage 4: worksheet → draft playbook
├── playbook.yaml               stage 4: the frozen rules (v1.0)
├── contracts/                  stage 5: 30 test NDAs
├── review.py                   stage 6: AI instructions, AI call, routing
├── replay/                     stage 7: raw AI output per contract
├── preds/                      stage 7: routed findings for scoring
├── review.html                 stage 7: all 30 reviews on one page
├── RUN_NOTES.md                stage 7: how the run was done, what went wrong
├── results.zip                 stage 7: the hand-in
├── server.py                   stage 8: local server
├── static/index.html           stage 8: lawyer review page
├── demo/
│   ├── index.html                stage 8: demo app, opens in any browser
│   └── build_demo.py             rebuilds the demo app from replay/
└── CLAUDE.md                   instructions for the AI reviewer in stage 7
```

</details>
