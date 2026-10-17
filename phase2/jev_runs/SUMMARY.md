# Jev dry run, 2026-10-17

Model: `jev-latest`. Input: the 30 saved reviews in `replay/`, routed by `review.route`, with contracts from `contracts/`.
Script: `phase2/jev_test.py --all`. Raw answers per contract: `jev_runs/Cxx.jev.json`.

**This run measures plumbing, speed, cost and agreement with the LLM. It does not measure accuracy.**
There are no lawyer decisions or labels to compare with.

## Plumbing

| Measure | Result |
| --- | --- |
| Requests | 602 (572 finding checks, 30 contract checks) |
| Errors | 0 |
| Quotes not found verbatim | 0 |
| Time per request | median 0.24 s, max 0.58 s |
| Tokens | 980,525 in, 92,794 out |

## Agreement with the LLM (`position_check`, 556 findings)

| LLM verdict | Jev answer | Count |
| --- | --- | --- |
| matches / acceptable | matches_preferred / meets_fallback | 382 |
| deviation | breaches | 148 |
| matches | breaches | 9 |
| deviation | matches_preferred / meets_fallback | 9 |
| matches / acceptable | unclear | 6 |
| acceptable | breaches | 2 |

Jev agrees with the LLM on 530 of 556 findings (95%). The 26 disagreements are the cases for a lawyer to read first.

## Result with the README thresholds

All 30 contracts go to a lawyer (20 urgent, 10 lawyer, 0 release). The thresholds are too strict:

1. **Missing-topic check: a design error, not a Jev error.** 118 flags. Most are PB15 non-solicitation (27 of 27),
   PB17 residuals (23 of 23) and PB16 non-compete (21 of 24). For these topics the preferred position is that the clause
   is absent, so "missing" is the good result. The rule must ask "present" only for topics that a contract needs.
2. **`changed_elsewhere` > 0.3: too low.** 100 of the 155 new finding escalations, and 89 of them have no other reason.
   The quartiles are 0.05 / 0.06 / 0.28, so 0.3 catches the top quarter of all findings.
3. **Urgent triggers:** uncapped liability (12 contracts), non-compete (6), IP transfer (6), exclusivity (5).
   These are plausible for this test set, but no label confirms them.

## Re-score after two fixes (no new Jev calls)

Command: `python phase2/jev_test.py --all --rescore`.

1. Missing-topic rule: PB14, PB15, PB16 and PB17 prefer no clause. For these, code now flags a clause that is
   present with no finding, not a missing clause.
2. `changed_elsewhere`: escalates above 0.7. From 0.3 to 0.7 it adds a note for the lawyer only.

| Measure | Before | After |
| --- | --- | --- |
| Findings that Jev newly escalates | 155 | 71 |
| Findings with a note only | 0 | 120 |
| Missing-topic flags | 118 | 35 |
| Absent-preferred clause present, no finding | not checked | 11 |
| Contracts: urgent / lawyer / release | 20 / 10 / 0 | 20 / 10 / 0 |

The contract results do not change, for two reasons:

- The current routing already escalates at least one finding in 29 of 30 contracts. C13 is the only exception,
  and Jev escalates two C13 findings where it reads a breach and the LLM reads a match (clauses 3.1 and 5.2).
- 20 contracts are urgent from the `has_*` checks, which the two fixes do not touch.

So "release" is not a fair measure on this test set. Each escalated finding is a better one.

Top reasons for the 71 new finding escalations: draft extra change (35), risk score ≥ 2 on an AI-draft finding (29),
draft may not fix (10), position breaches vs LLM (10), draft new duty (10), changed elsewhere > 0.7 (9).

## Next steps

- Read the 26 disagreements and the 11 present-but-unreviewed clauses against the contracts.
  That is the first real evidence on whether Jev adds value.
- The `draft_extra_change` and `risk_to_us` checks give most new escalations. Check a sample before you trust them.
- Move the absent-preferred list from code into `playbook.yaml`.

## Stability test: five runs of the contract check

Command: `python phase2/jev_stability.py`. Same input five times per contract, 150 requests. Raw data: `jev_runs/stability.json`.

| Measure | Result |
| --- | --- |
| Questions compared (30 contracts) | 376 |
| Same escalation decision on all five runs | 364 (97%) |
| `document_type`: same answer on all five runs | 30 of 30 |
| Probability spread across runs, median per question | 0.01 to 0.06 |
| Largest spread | 0.12 |

Jev is not fully deterministic: the probabilities move a little between runs. All 12 decision flips are answers
that sit within 0.07 of a threshold, for example C08 PB14 present: 0.50 / 0.52 / 0.48 / 0.52 / 0.49 against 0.5.
Four of the 12 are the PB14 indemnity question, which is already known to be too broad.

**Comparison with the LLM:** the case study found that five fresh LLM reviewers raise the same issue only 39% to 52%
of the time. The two numbers measure different things, so do not compare them directly. The LLM number asks
"is the same issue raised?". The Jev number asks "does a fixed question get the same decision?". The result
supports the design idea: a fixed checklist of Jev questions gives a stable list of checks on every run.

**Fix for the flips:** treat an answer close to its threshold (for example within 0.05) as "send to a lawyer"
and record it as borderline. Then a small change between runs cannot change the outcome.
