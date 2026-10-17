# Run notes

- **Date:** 2026-10-15
- **Model shown in this session:** Claude Opus 5.5 (`claude-opus-5-5`). Opus was the orchestrator only. It wrote no findings.
- **Reviewer model:** Sonnet. The Agent tool used the model alias `sonnet`. The exact model ID of the subagents is not shown in the session.
- **Subagents used:** yes.
  - 30 Sonnet subagents, one fresh subagent for each contract (C01 to C30). Each subagent printed its prompt with `review.py --print-prompt` and wrote only its own `replay/<id>.raw.json`.
  - 1 Haiku subagent did a read-only quote check of C01 to C20.
  - No subagent read `playbook.yaml`, another contract or another replay file. Each prompt said this, and each report confirmed it.
- **Batches:** C01 to C20 ran in parallel first. C21 to C30 ran in parallel after that.

## Checks

- All 30 raw files parse as JSON.
- A script checked each `quote` as an exact substring of the printed prompt (Python in UTF-8 mode). All 572 quotes pass.
- `python3 review.py --all --backend file --contracts contracts --out preds` parsed all 30 files (572 findings) with no error.

## What went wrong

1. **Quotes that were not exact (C01 to C20).** 16 quotes in 9 files did not match the contract text exactly:
   - C03: 1 quote. The reviewer dropped a bracket from a `[[INS: ...]]` marker.
   - C04, C05, C06, C08, C09, C10: 13 quotes. The reviewers quoted the text after the edits were accepted, without the `[[INS]]`/`[[DEL]]` markers. In C06 and C09 this also left a stray space before a comma.
   - C14, C16: 1 quote each. The quote crossed a line break, so only the whitespace was different.

   For each file, the same reviewer subagent that wrote the file corrected only the `quote` field. No verdict, rule or other field changed. No file was edited by hand.
2. **Encoding (C10).** The first C10 file had a replacement character (U+FFFD) where the contract has "ä". On Windows, `review.py --print-prompt` writes non-ASCII text incorrectly unless Python runs in UTF-8 mode (`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`). The C10 reviewer rewrote the quote in UTF-8.
3. **Reviewer prompt for C21 to C30.** Because of items 1 and 2, the C21 to C30 reviewers were told to keep the edit markers, to not cross a line break, to use UTF-8 mode, and to check their own quotes. All 10 passed the check on their first attempt.
4. **Different choices between reviewers.** Because each contract had its own reviewer, some choices are not the same across contracts:
   - For an unmatched clause, most reviewers used `rule_id: null`. C24 used `PB22`, the catch-all rule.
   - C05 and C10 set the verdict to `deviation` for a margin-comment request when the clause text itself matched the playbook.

   These are the reviewers' own outputs and were not changed.
5. **Haiku check total.** The Haiku report gave a total of 404 quotes and 27 failures. Its own table showed 391 quotes and 13 failures. The table was correct. The later script check confirmed the counts.

## Evals and routing guards (2026-10-16)

- **Model shown in this session:** Claude Opus 5.5 (`claude-opus-5-5`), orchestrator only. It wrote no findings.
- **Reviewer model:** Sonnet subagents (alias `sonnet`), one fresh subagent per run, the same method as the 30 reviews.
- **Saved reviews:** `replay/C01` to `C30` were not changed. `preds/` was regenerated from them with the current routing.

### Engine

1. Routing guards: a known request whose playbook answer says "escalate" (RQ01, RQ03, RQ10) goes to a lawyer. If the AI's verdict says pass but its own reason says escalate, the reason wins. On a Shadow rule, an "acceptable" call goes to a lawyer during the pilot. A drafted-fix finding with no draft goes to a lawyer. A draft that is an instruction, not wording, is labelled.
2. `ai_verdict` keeps the model's own verdict. Code's override for unmatched clauses shows as a routing note.
3. Personal data masking before the live API call, and an injection screen on the contract text. Prompt 2 adds an "untrusted input" block. The saved reviews used prompt 1; `--prompt-version 1` prints it exactly.
4. Every file is read and written as UTF-8, so `--print-prompt` works on Windows without `PYTHONUTF8=1`.
5. `server.py` listens on localhost only. The pages load no web fonts.

### Runs

- **Variance:** C01, C05 and C12, four more runs each with prompt 1 (`evals/variance/`). With the saved run this gives five runs per contract. All 12 runs parsed and passed the quote check. One reviewer fixed one quote (a capital letter) after its own check.
- **Injection:** three hostile contracts (`evals/adversarial/contracts/A01` to `A03`), each run once with the base prompt and once with the guarded, masked prompt. All 6 runs parsed and passed the quote check. In one run the reviewer used a request id that does not exist (RQ12); code drops unknown request ids.

`python3 evals/run_evals.py` writes `evals/EVAL_REPORT.md`. Nothing in it needs a lawyer, and nothing in it measures legal accuracy.

### Eval problems found and fixed before any number was used

- The first "insurers" probe counted any finding that mentioned insurers. 6 of its 9 "matches" do list insurers. The probe now looks for missing or removed insurers, and the count is 3.
- The first coverage matcher read clause numbers such as "1.1.9 and 10.4" as one number, so it reported covered edits as missed.
- The instruction-draft test first flagged "Replace with: '...'" drafts, which do give wording. It now needs a closed quote of 20 or more characters to count a draft as wording.
