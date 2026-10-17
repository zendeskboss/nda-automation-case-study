# NDA review case study

A test of an AI tool that reviews NDAs against a legal team's own rules. The AI reads each contract. Code decides what the lawyer sees. A lawyer approves everything.

## Open these first

1. **`case-study.html`**: the story, in plain English. What we did, how we thought about it, what we found and what we would build. About 6 minutes. Open it in any browser.
2. **`deeper/`**: six pages for readers who want more on one topic: the lawyers' rules, how the tool reads an NDA, how we tested it, safety, what it would take to build, and every assumption. Each is linked from the story at the point where the question comes up.
3. **`demo.html`**: the screen a lawyer would use, with all 30 test NDAs loaded. It needs no install and sends nothing anywhere.
4. **`all-reviews.html`**: every finding for all 30 NDAs on one page.
5. **`engine/evals/EVAL_REPORT.md`**: for engineers, the full eval report behind the testing page.

## Folders

| Folder | What is in it |
|---|---|
| `discovery/` | The process discovery workbook. Each team member fills it in before we build anything (stage 0). |
| `rules/` | The worksheet where lawyers set the rules (stage 3), and the script that turns it into a playbook (stage 4). |
| `notes/` | The assumptions and implementation options, how the test run was made, presenter notes, and the instructions the AI reviewers followed. |
| `engine/` | The code that runs the review, the playbook, the 30 test NDAs and the saved results. Keep its layout as it is: the code expects these paths. |

## Inside `engine/`

| File or folder | What it is |
|---|---|
| `review.py` | The review engine: builds the AI's instructions from the playbook, calls the AI, routes each finding. |
| `playbook.yaml` | The rules, version 1.0. Positions marked "ASSUMED" are not yet confirmed by a lawyer. |
| `contracts/` | The 30 test NDAs, C01 to C30. Tracked changes show as `[[INS: ...]]` and `[[DEL: ...]]`. |
| `replay/` | The AI's raw answer for each NDA (`C01.raw.json` and so on). |
| `check_quotes.py` | Checks that every quote in `replay/` is exact text from its contract. |
| `preds/` | The routed findings for each NDA, ready to score against a lawyer's answer key. |
| `evals/` | `run_evals.py` and its report. `variance/` holds 4 re-runs each of C01, C05 and C12. `adversarial/` holds 3 hostile NDAs and their runs. `answer_key_template.csv` is for the test-set author to label. |
| `tools/make_review_page.py` | Rebuilds `all-reviews.html` from `replay/`. |
| `server.py`, `static/` | A local server and the lawyer review page. |
| `demo/build_app.py`, `demo/app.src.html` | Rebuilds `demo.html` from `replay/`: run `python3 demo/build_app.py`, then copy `demo/app.html` over `demo.html`. |

## Run it (optional)

You need Python 3 and the `pyyaml` package.

```bash
cd engine
python3 review.py --all --backend file --contracts contracts --out preds
python3 server.py
```

The first command re-routes the saved reviews. The second starts the review page at http://localhost:8765 (localhost only). A live review of a new NDA needs an `ANTHROPIC_API_KEY`. Before the call, the engine masks names, emails and phone numbers, and screens the text for prompt injection.

To re-run the evals: `python3 evals/run_evals.py`. It writes `evals/EVAL_REPORT.md`.

## Limits

The rules are our assumptions, not positions confirmed by a legal team. The findings are not yet scored against a lawyer's answer key, so nothing here measures legal accuracy. The evals measure coverage, consistency and robustness, which need no lawyer. The reviews came from Claude Sonnet subagents with the engine's exact prompt, not from the live API. `notes/assumptions-and-implementation.md` lists every assumption.
