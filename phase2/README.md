# Phase 2: Jev post-lane check (hypothetical)

Jev is TypeSafe's System One model. It returns typed answers with probabilities. In phase 2 it runs
after `route` has set each finding's lane. It can only escalate. It never moves a finding to a safer lane,
and it never changes `playbook.yaml`.

All thresholds below are starting values. Tune them in shadow mode against lawyer decisions.

## Files

| File | One request per | Sent to |
| --- | --- | --- |
| `jev_finding_check.request.json` | finding | `POST https://api.typesafe.ai/v1/systemone` |
| `jev_contract_check.request.json` | contract | same endpoint |

`{{...}}` marks a value that code fills in. Code sends the finding requests in parallel.

## What code does before Jev

1. Check that each `quote` is verbatim in the contract (normalise whitespace and curly quotes).
   A quote that is not found means a fabricated finding: re-review the contract. Jev is not asked.
2. Copy the full clause text and the related clauses (shared defined terms, cross-references) into `state`.
3. Remove the three `draft_*` questions when `draft_redline` is null.
4. Add one `topic_present__<topic>` question for each playbook topic that has no finding.

## How code reads the answers

Escalate a finding to a lawyer when any line is true:

| Question | Escalate when |
| --- | --- |
| `rule_fit` | answer is not `fits`, or confidence < 0.8 |
| `position_check` | answer is `unclear`, or it disagrees with the LLM verdict (`breaches` vs `deviation`; `matches_preferred` / `meets_fallback` vs `matches` / `acceptable`) |
| `changed_elsewhere` | noul > 0.7 (0.3 to 0.7 adds a note for the lawyer, no escalation) |
| `risk_to_us` | score ≥ 2 (moderate) on a `purple_ai` finding |
| `draft_fixes_breach` | noul < 0.7 |
| `draft_extra_change` | noul > 0.3 |
| `draft_new_duty_for_us` | noul > 0.3 |

Contract result (policy in code, not in Jev):

| Result | When |
| --- | --- |
| Urgent | `document_type` is `not_nda` or `nda_inside_larger_deal`, or any `has_*` noul > 0.5 |
| Lawyer | any finding escalated, any `has_*` noul > 0.3, a needed topic missing (`topic_present__*` noul < 0.5), an absent-preferred topic present with no finding (noul > 0.5), `findings_conflict` noul > 0.3, or `overall_unusual` score ≥ 2 |

Absent-preferred topics are the rules whose preferred position is "no such clause": PB14 indemnities,
PB15 non-solicitation, PB16 non-compete and exclusivity, PB17 residuals. For these, absence is the good result.
In production, mark them in `playbook.yaml` with a field such as `expect: absent`.
| Release | none of the above |

## Failure rules

- Jev error, timeout, HTTP 429 or 529 after retries: treat as "escalate". Never treat as "release".
- Log each request, answer and resulting action next to the lawyer decision in `logs/shadow_log.jsonl`.
- Lopsided thresholds are deliberate: a missed risk costs more than one extra lawyer look.
