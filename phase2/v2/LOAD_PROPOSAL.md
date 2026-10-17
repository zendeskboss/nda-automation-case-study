# Lawyer load: proposal v2.1

**Result:** policy v2.1 cuts lawyer items from 451 to 335 on the 30 contracts (−26%). v1 had 183, so v2.1 is still
1.8 times v1. No robustness test fails, and every tracked edit still gets a finding.

Policy v2.1 is in `engine.POLICIES`. It uses the same saved Jev answers as v2.0, plus two small additions
(below). v2.0 stays available, and its replay is unchanged. Full scorecard: [SCORECARD.v2.1.md](SCORECARD.v2.1.md).

## How the changes were chosen

The request was "no tuning on this data alone". So each change follows from one of these sources, not from a
threshold search on these 30 contracts:

- the structure of the playbook (severity, lanes, our paper against their paper)
- correct use of Jev's probabilities
- the run-to-run noise that the separate stability test measured

**Limit:** I chose which escalation types to look at from the breakdown on these 30 contracts. To check that the
changes do not depend on a few contracts, the effect is shown for each half of the set. Both halves fall by a
similar share: C01–C15 by 22%, C16–C30 by 29%.

## The six changes

| # | Change | Reason | Items removed alone | C01–C15 / C16–C30 |
|---|---|---|---|---|
| 1 | **Pass or not pass on summed probabilities** | A clause with "matches 0.45, fallback 0.40, breach 0.15" is a pass at 0.85. v2.0 read it as "fallback 0.40", below the 0.6 floor. That is a misuse of the probabilities, not a doubt. | 45 | 31 / 14 |
| 2 | **Borderline band by severity** | High rules keep the 0.30 band. Low and Medium rules use 0.38: two times the largest run-to-run spread from the stability test (0.12), so run-to-run noise cannot flip a pass. | 24 | 3 / 21 |
| 3 | **Unedited template text on our paper is not re-reviewed** | Halyard's own template wording is approved. v2.0 sent unchanged clauses such as "no partnership" (12.6) to a lawyer. | 16 | 16 / 0 |
| 4 | **Edited definitions are checked against the rules that use the term** | "Representatives" is checked under PB05, "Data Protection Legislation" under PB11. The lawyer gets the rule context, not "no rule fits". The item still goes to a lawyer (see "Corrected" below). | +8 (more context, not fewer items) | +8 / 0 |
| 5 | **Mutuality is one whole-agreement question** | Mutuality (PB01) is a property of the whole agreement, so no single clause maps to it. v2.0 reported it "missing" in 15 contracts. v2.1 asks Jev once per contract. | 9 | 2 / 7 |
| 6 | **One "missing topics" item per contract** | A contract with no publicity, personal data and reverse-engineering clause gave three items. Now it is one item that lists each topic with its severity. The lawyer reads the same facts once. | 39 | 5 / 34 |

The six changes overlap, so the single effects do not add up to the total (116).

Changes 4 and 5 need new Jev calls: one per contract for mutuality, and up to three per edited definition.
`run.py --patch` adds them to the saved evidence. Nothing else is re-run.

## Corrected during the check

The first version of change 4 let Jev pass an edited definition. Seven "Business Day" edits (Ireland added),
"Key Personnel" (C05) and "Trade Secret" (C08) then passed without a lawyer, and tracked edits passed by the tool
rose from 40 to 62. That broke v2's rule that a tracked edit on our paper must not pass unseen. Now an edited
definition always reaches a lawyer, with the rule context added. Tracked edits passed by the tool: v1 42,
v2.0 40, v2.1 44.

## Safety checks

| Check | Result |
|---|---|
| Jev outage, borderline pass, replay, verbatim quotes, evidence records | all pass |
| Tracked edits with no finding (C01–C10) | 0 |
| Every edited definition reaches a lawyer | yes, 19 of 19 |
| Tracked edits passed by the tool | 44 (v1: 42, v2.0: 40) |
| Lawyer items in v2.0 that v2.1 passes, where v1 also sent the clause to a lawyer | **8: a lawyer should spot-check these** |

The 8 items for a spot-check. v1 and v2.0 both sent them to a lawyer; v2.1 passes them:

| Contract | Clause | Rule | Severity | v2.1 | Jev |
|---|---|---|---|---|---|
| C14 | 6.1 | PB07 Return and destruction | Low | acceptable | pass 0.85, breach 0.13 |
| C15 | 10.1 | PB19 Assignment | Low | acceptable | pass 0.75, breach 0.24 |
| C24 | 1.1.7 | PB05 Representatives | Medium | matches | pass 0.66 |
| C27 | 1.1.4 | PB05 Representatives | Medium | matches | pass 0.69 |
| C29 | 4.3 | PB06 Compelled disclosure | Medium | acceptable | pass 0.93, breach 0.04 |
| C30 | 1.1.6 | PB05 Representatives | Medium | matches | pass 0.65 |
| C30 | 2.1 | PB20 Reverse engineering | Low | matches | pass 0.70, breach 0.23 |
| C30 | 9.4 | PB19 Assignment | Low | acceptable | pass 0.76, breach 0.23 |

Three of them are PB05 definitions of "Representatives" with a pass probability of 0.65 to 0.69. If a lawyer
finds that these are real deviations, the Medium band (0.38) is too wide for PB05, and the challenge log records it.

Two edited clauses now pass that v2.0 escalated: C03 6.2 (PB07, pass 0.93) and C09 recital (A) (PB03, pass 0.88).

## Risks

- **Change 3 needs a template check in production.** The prototype trusts the tracked-change markers. An edit
  made without track changes would pass as template text. In production, compare each clause with a hash of the
  approved Halyard template. That template file is not in this folder.
- **Consistency moved a little.** Same route in all five runs: C01 95%, C05 95% (v2.0 98%), C12 90% (v2.0 88%).
  Same text in other contracts: 89% (v2.0 87%).

## What still goes to a lawyer (335 items)

| Reason | Items | Proposal |
|---|---|---|
| Playbook lane: lawyer only or shadow | 57 | Keep. The playbook sets this, not the tool. |
| Breach with no draft | 45 | In production the LLM drafts these. They stay lawyer items, but approving a draft is quick. |
| Jev answer "unclear" | 40 | Next step: send these to the LLM as a second reader first. Only a disagreement goes to a lawyer. |
| Borderline pass | 40 | Keep until the challenge log shows how often a borderline pass is really a breach. |
| Term that no rule covers | 31 | Keep. Mostly their paper: unknown terms need a lawyer. |
| Confidence below the 0.6 floor | 28 | Set the floor for Jev from the challenge log. 0.6 was set for LLM self-ratings. |
| Missing topics (one item per contract) | 24 | Keep. |
| Edited clause with no rule | 19 | Keep. |
| Margin comment asks for a change | 13 | Keep. |

## Not done, and why

- **No threshold was searched or fitted.** The only new number (0.38) comes from the stability test.
- **Items are not lawyer time.** A drafted fix takes a minute, and an unknown term can take much longer. A time
  estimate per item type needs a lawyer's view.
- **Accuracy is still not measured.** The 8 spot-check items are the cheapest first step.

## Decision needed

Adopt v2.1 as the default policy, after a lawyer spot-checks the 8 items above?
