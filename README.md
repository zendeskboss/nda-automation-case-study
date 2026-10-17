# NDA review: a case study

**Could a tool read NDAs first, so the business closes deals faster?**

Every NDA waits for a lawyer, even one that matches the company template word for word, and the deal waits with it. This case study tests an AI tool that does the routine reading against the legal team's own rules. Code decides what a lawyer sees. A lawyer approves everything.

> **Read this first.** This is a case study, with 30 made-up NDAs. All rules are our assumptions, made with best efforts and with no legal team to verify them. Any real build would fully involve the legal team. No lawyer has checked a single result, so nothing here measures legal accuracy.

## Start here

The finished case study is a small website in [`dist/NDA review case study/`](dist/NDA%20review%20case%20study/). GitHub shows HTML files as code, so download the repository (Code → Download ZIP) and open the files in a browser.

| Open | What it is |
|---|---|
| `case-study.html` | The story in plain English, about 6 minutes. Start here. |
| `deeper/` | Eight "go deeper" pages: the lawyers' rules, how the tool reads an NDA, testing, safety, building it, both Phase 2 pages, and every assumption. |
| `demo.html` | The screen a lawyer would use, with all 30 test NDAs loaded (Phase 1). It sends nothing anywhere. |
| `all-reviews.html` | Every Phase 1 finding for all 30 NDAs on one page. |

## The three phases

| | Phase 1 | Phase 2 | Phase 2.1 |
|---|---|---|---|
| How it reads | An AI model lists the issues it finds | A fixed checklist: Jev answers the same questions for every clause | Phase 2, tuned to send less to lawyers |
| Same issue found in all 5 repeat reviews (3 NDAs) | 39% to 52% | 93% to 98% | 93% to 100% |
| Tracked changes that got no attention (10 NDAs) | 13 | 0 | 0 |
| Items for lawyers (30 NDAs) | 183 | 451 | 335 |

- **Phase 1** worked, but it was not consistent: the same NDA, reviewed again, raised different issues.
- **Phase 2** stopped the AI from choosing what to look at. [Jev](https://docs.typesafe.ai) (TypeSafe's System One model) only picks from fixed answers. Across five runs it gave the same decision 97% of the time. Phase 2 checks more and plays safe, so it sends more to lawyers.
- **Phase 2.1** made six changes based on how the lawyers' rules work, and cut lawyer items by 26%. It is the default in this case study, marked "not checked by a lawyer". Lawyers' decisions would bring the number down further over time (the continuous improvement model on the main page).

Every number above comes from saved test results in this repository. The scorecards show how each one is measured: [`evals/EVAL_REPORT.md`](evals/EVAL_REPORT.md) (Phase 1), [`phase2/v2/SCORECARD.md`](phase2/v2/SCORECARD.md) (Phase 2) and [`phase2/v2/SCORECARD.v2.1.md`](phase2/v2/SCORECARD.v2.1.md) (Phase 2.1).

## What is in the repository

| Path | What it is |
|---|---|
| `review.py` | The Phase 1 engine: builds the AI's instructions from the playbook, calls the AI, and routes each finding with fixed rules. |
| `playbook.yaml` | The rules: 21 topic rules, a catch-all rule and 12 known counterparty requests. Every position is marked "assumed". |
| `contracts/` | The 30 test NDAs, C01 to C30. Tracked changes show as `[[INS: ...]]`, `[[DEL: ...]]` and `[[COMMENT: ...]]`. |
| `replay/`, `preds/` | Phase 1: the AI's saved answer for each NDA, and the routed findings. |
| `evals/` | Phase 1 evals that need no lawyer: coverage, consistency, re-runs (`variance/`) and hostile contracts (`adversarial/`). |
| `phase2/` | The first Jev test, its request bodies and the stability test. See [`phase2/README.md`](phase2/README.md). |
| `phase2/v2/` | Phase 2 and 2.1: the checklist engine, saved runs with full evidence, scorecards, the lawyer-load proposal and the lawyer spot-check sheet. See [`phase2/v2/README.md`](phase2/v2/README.md). |
| `phase2/story/` | The generator for the Phase 2 story page. |
| `tools/`, `redesign/`, `demo/` | The generators for the case study pages, the review page and the demo. |
| `discovery/`, `worksheet/` | The workbook each lawyer fills in first, and the worksheet where lawyers write the rules. |
| `server.py`, `static/` | A local server and the lawyer review page. |
| `dist/` | The built case study site. |
| `CASE_STUDY.md`, `ANNEX_ASSUMPTIONS.md` | The written case study and the full list of assumptions and build options. |

## Run it

You need Python 3 and `pyyaml`. The spot-check sheet also needs `openpyxl`. Nothing below calls a model unless a step says so.

Re-route the saved Phase 1 reviews:

```bash
python3 review.py --all --backend file --contracts contracts --out preds
```

Re-run the Phase 1 evals (writes `evals/EVAL_REPORT.md`):

```bash
python3 -X utf8 evals/run_evals.py
```

Rebuild every Phase 2.1 decision from the saved evidence, without calling Jev:

```bash
python3 phase2/v2/run.py --run r1 --all --replay --policy v2.1
```

Show the evidence behind one decision (any decision can be challenged this way):

```bash
python3 phase2/v2/challenge.py show r1 C01 12.10
```

Rebuild the Phase 2 scorecards:

```bash
POLICY=v2.1 python3 -X utf8 phase2/v2/evals.py
```

Rebuild the case study pages, then the `dist/` site:

```bash
python3 -X utf8 tools/make_story.py
```

```bash
python3 build_package.py
```

Live runs need keys: `ANTHROPIC_API_KEY` for a new Phase 1 review, and `TYPESAFE_API_KEY` for new Jev runs (`phase2/v2/run.py` without `--replay`). Before any text leaves the machine, the engine masks names, emails and phone numbers, and screens the contract for hidden instructions.

## How it was made

The Phase 1 reviews came from Claude Sonnet, one fresh reviewer per NDA, using the exact instructions the tool would send. In Phase 2 and 2.1, Jev answered the checklist questions, and code written with Claude Opus turned the answers into findings. Nobody wrote findings by hand.

## Still open

- **Legal accuracy.** A lawyer must check a sample. [`phase2/v2/spotcheck/SPOTCHECK_v2.1.xlsx`](phase2/v2/spotcheck/) is ready for the first 8 clauses.
- **Real NDAs.** All results come from 30 made-up NDAs. Real volumes, formats and requests may differ.
- **Business impact.** How much faster deals close depends on NDA volumes and waiting times today. The discovery workbook collects both, and a trial would measure the change.
