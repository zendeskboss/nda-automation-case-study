# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Task: produce the 30 saved NDA reviews

You are the reviewer in a case study. A lawyer approves everything you produce. Your job is only to
review each contract against the playbook and save your raw output. Code does the routing afterwards.

## Rules (these keep the evaluation honest)
- Review each contract independently. Use one fresh subagent per contract, or `/clear` between them.
  Do not carry findings from one contract to the next.
- Do not look for answer keys, labels, scores or the original test set. There are none in this folder.
  Do not read `playbook.yaml` directly. The prompt printed by the command below is the only playbook view you use.
- Do not edit `review.py`, `playbook.yaml` or the contracts.
- Use no standard other than the playbook in the prompt.

## Steps
1. For each contract id C01 to C30, print the prompt:
   `python3 review.py --print-prompt --contracts contracts C01`
2. Follow that prompt exactly (system part, then the user part with the contract) and write the JSON it asks for,
   and nothing else, to `replay/C01.raw.json`. It must be valid JSON in the schema the prompt gives.
   Quote clause text verbatim. Never invent clause text.
3. When all 30 exist, run:
   `python3 review.py --all --backend file --contracts contracts --out preds`
   Fix any file that fails to parse by re-reviewing that contract, not by hand-editing findings.
4. Record in `RUN_NOTES.md`: the model name shown in this session, today's date, whether subagents were used,
   and anything that went wrong.
5. Zip `replay/`, `preds/` and `RUN_NOTES.md` as `results.zip`.

Optional check: `python3 server.py`, open http://localhost:8765, Replay mode, pick a contract.

## Architecture

- `review.py` is the whole engine. `build_prompt` renders `playbook.yaml` into the system prompt,
  a backend returns raw JSON, and `route` applies deterministic rules. The model only classifies clauses.
- Backends: `anthropic` (live API, needs `ANTHROPIC_API_KEY`) and `file` (reads `replay/<id>.raw.json`).
  `--save-raw` writes live output into `replay/`.
- `route` decides each finding's lane from the playbook rule, not from the model: `purple_ai` gets a draft,
  `orange` is flagged and quoted only, `purple_human` hides the model's view (shadow mode).
  A finding with no rule, or with confidence below the floor (`NDA_CONFIDENCE_FLOOR`, default 0.6), escalates.
  `PB22` is the catch-all rule for unmatched clauses.
- `to_pred` keeps only the fields the evaluation reads. Output goes to `preds/<id>.pred.json`.
- `server.py` serves `static/index.html` and a small JSON API (Replay or Live mode).
  `/api/decision` appends lawyer decisions to `logs/shadow_log.jsonl`.
- Environment: `NDA_MODEL` (default `claude-sonnet-5-5`), `ANTHROPIC_BASE_URL`, `PORT`.

## Gotchas

- `review.py` and `server.py` default to `../testset`, which does not exist here. Pass `--contracts contracts` to `review.py`.
- `server.py` reads `../testset` and `<id>.labels.json` for its sample list, so Replay mode lists no samples here.
  Do not create those files. The task rules forbid labels.
- `_clean` strips decoy ids such as `(DX1)` from playbook text. Never put such ids into a prompt or a finding.
- Dependency: `pyyaml`. Everything else is the standard library. There is no test suite or linter.
