# NDA review v2: checklist first (prototype)

v1 asks an LLM to read the contract and list the issues it finds, so each run finds a different set of issues.
v2 reverses this. Fixed questions decide what gets checked, and Jev (TypeSafe's System One model) answers them.

Results against v1: [SCORECARD.md](SCORECARD.md). Read its summary first.

## How it works

1. **Split (code).** The contract becomes clauses: sub-clauses join their clause (3.1.1 joins 3.1), and each
   definition stays on its own. Margin comments and tracked edits stay with their clause.
2. **Map (Jev).** Every clause gets one question: which playbook topic is this? The clause maps to every rule with
   probability ≥ 0.25 (max 3). "Other term" ≥ 0.5 becomes an unrecognised-term finding.
3. **Check (code and Jev).** For each clause and rule, Jev answers the same questions every time: position
   (matches, fallback, breach, unclear), whether a margin comment asks for a change, which fallback fits, and which
   known counterparty request it is. Code checks the governing law, the return period and the survival period.
4. **Decide (code).** `engine.decide()` turns the answers into findings in the v1 schema. All thresholds are in
   `engine.T`. Code checks and comments can only make a result stricter. A topic with no clause becomes a finding.
5. **Route (unchanged v1 code).** `review.route` applies the playbook lanes, the confidence floor, the shadow lane,
   the known-request conditions and the injection screen.

The LLM is not called in this prototype. Drafts come from the saved v1 review when the same rule and clause match.
Otherwise the route says "a lawyer writes the fix". In production, the LLM drafts only confirmed breaches.

## Why each decision can be challenged

- Every quote is a contract clause copied by code. A quote cannot be invented.
- `runs/<run>/<id>.evidence.json` keeps every clause, every question, every probability, the thresholds,
  the engine, model and playbook versions, and a hash of the contract.
- `run.py --replay` rebuilds every finding from that evidence without calling Jev. The scorecard checks that
  the replay is identical for all 30 contracts.
- `challenge.py show` prints the evidence for one decision. `challenge.py dispute` records a lawyer's verdict in
  `challenges.jsonl`, with a fingerprint of the evidence. Thresholds change only on evidence from that log.

## Commands

```bash
python phase2/v2/run.py --run r1 --all
```

```bash
python phase2/v2/run.py --run r1 --all --replay
```

```bash
python phase2/v2/challenge.py show r1 C01 12.10
```

```bash
python -X utf8 phase2/v2/evals.py
```

Live runs need `TYPESAFE_API_KEY`. Replay, challenge and evals need no key.

## Default policy and the lawyer spot-check

For this case study the default policy is **v2.1, not checked by a lawyer** (`default_policy.json`, source
"case study: no lawyer check"). There is no lawyer in the case study. Before any real use, a lawyer must do the
spot-check below ([LOAD_PROPOSAL.md](LOAD_PROPOSAL.md)).

1. Send `spotcheck/SPOTCHECK_v2.1.xlsx` to the lawyer. It has the 8 clauses that v2.1 passes and v1 sent to a lawyer.
2. Import the returned sheet:

```bash
python -X utf8 phase2/v2/import_spotcheck.py phase2/v2/spotcheck/SPOTCHECK_v2.1.xlsx
```

The import refuses an incomplete sheet. It writes each answer to `challenges.jsonl` and writes
`default_policy.json`: v2.1 if no row is overturned, otherwise v2.0. `run.py` reads that file for its default.

## Known limits

- **No accuracy measure.** Everything in the scorecard is consistency, coverage, robustness or traceability.
- **Lawyer load is 2.5 times v1** (451 against 183 items on 30 contracts). The scorecard lists the reasons.
  The v1 confidence floor (0.6) was set for LLM self-ratings, not for Jev probabilities. Tune it from lawyer
  disputes, not from this data.
- **Same text in different contracts** gets the same route 87% of the time, below the 95% target. Jev also reads
  each contract's own definitions, which differ. Whether that difference is right needs a lawyer.
- The change test renames the counterparty's full name only, not its short name.
- `ABSENT_PREFERRED` (PB14 to PB17) is in code. In production it belongs in `playbook.yaml`.
