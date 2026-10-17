# Talk track (presenter notes, about three minutes)

For the presenter only. The audience gets `case-study.html`.

1. **Bottom line:** The AI sorts NDA clauses against the lawyers' playbook, and code decides what a lawyer sees. I tested what one person can test without a lawyer: coverage, consistency, routing and hostile input. Code enforces the playbook in the routing. The AI's consistency is the weak point, and legal accuracy is not yet scored.
2. **The ask:** 45 minutes from each lawyer on the process discovery workbook, three one-hour worksheet sessions with the legal team, one playbook owner, a shadow pilot, and one front door for intake.
3. **The problem:** Every NDA waits for a lawyer, even the ones that match our template.
4. **The principle:** Lawyers set the rules and approve everything. The AI sorts clauses against those rules. Code decides what the lawyer sees.
5. **Discovery first:** Before we build, each lawyer fills in the process discovery workbook: their tasks, how they decide, real examples, their tools and their worries. Their red lines become hard limits.
6. **The gap we found:** The tracker lists the risks. It does not say where the line is for each one. That knowledge sat with the lawyers.
7. **The worksheet:** For each clause the lawyers write our position, what is fine, and what is never fine. Three questions decide how far the tool may go. This is the quality gate, and the lawyers own it.
8. **The playbook:** A script turns the worksheet into the playbook file. Anything a lawyer has not confirmed is marked "assumed".
9. **The engine:** Code masks personal data and screens for text aimed at the reviewer. The AI reads each contract against the playbook and quotes each clause. Code sends each finding to one of four places: matches, acceptable, drafted fix, or lawyer decides. When the playbook says escalate, or the AI's own reason says escalate, code escalates.
9a. **The evals:** 93% of tracked edits get a finding. Re-run the same NDA and the reviewers report the same issue only 39% to 52% of the time. The same clause type gets opposite verdicts in different NDAs. Three hostile NDAs did not change what reached a lawyer on the targeted clauses. These numbers are why the shadow pilot comes before any more automation.
10. **The lawyer's view:** "This came in, this is what we spotted, these are your decisions." When the tool finds a deviation on a high-stakes rule, its view stays hidden until the lawyer decides, so we can measure how often the tool agrees.
11. **Keep the easy wins:** If the tool takes all the easy NDAs, juniors lose the work they learn from and everyone is left with only hard cases. So some routine work goes back to people on purpose: a learning mode for juniors, and a pass-through rate where one NDA in N gets no tool output. Both reuse the shadow mechanism.
12. **Implementation:** The engine is the easy part. Most of the effort is fitting it into how NDAs arrive (mailbox, Word, PDF, DocuSign) and where lawyers work. We would start with a week of discovery, then a shared NDA mailbox and the existing review page.
13. **Limits:** The rules are our assumptions until a legal team confirms them, and the findings are not yet scored against a lawyer's answer key. A "matches" call still goes straight through, so the pilot needs a random sample of those for a lawyer. The annex lists every assumption.

## Interview probes: prepared answers

### Cue card: remember only these three lines

1. **Order forms → "Read, then check."** The AI reads the numbers out. Code checks them against limits.
2. **False "matches" → "Every high-risk topic gets a lawyer's eye."** You found a real gap. Code makes sure, not the AI.
3. **Test vs live → "Same brain, different door."** Same prompt and routing code. I would re-run all 30 live to prove it.

**If they push:** "I wrote that up. Can I send it after?"

### If they ask one more question

- **Order forms:** "The lanes, the shadow mode and the lawyer sign-off do not change."
- **False "matches":** "First fix: the confidence floor does not apply to a 'matches' call. That is one line of code."
- **Test vs live:** "The one real gap: the test did not run the data masking."

### Detail (do not memorise)

These answers reply to three points from an adversarial review. Items marked "proposal" are not built or tested.

### 1. Scope: from NDAs to order forms

- **Why NDAs first:** NDAs are high volume and low value, and the brief named them first. One contract type let us test the routing honestly.
- **What carries over:** The lanes, the playbook owner, the shadow mode and the rule that code routes and the AI only classifies. None of these is specific to NDAs.
- **What changes (proposal):** An order form is mostly fields, not clauses. Price, payment days, service levels and term are values in tables and schedules. For these, the AI extracts each value and quotes where it found it. Code then compares the value with a number in the playbook, for example "payment terms no longer than 60 days". The AI does not judge the number.
- **Schema change (proposal):** A playbook rule gets a second kind. A "clause" rule keeps today's verdicts. A "field" rule holds a type, a limit and a lane. Free-text terms in an order form stay as clause rules.
- **Honest limit:** Table extraction from PDFs is a new risk. We would test extraction accuracy alone before any routing.

### 2. A false "matches" on a high-risk topic, on their paper

- **Admit the gap first:** In `review.py`, the confidence floor does not apply to a "matches" verdict. A "matches" call with low confidence goes straight through. This is a one-line fix: apply the floor to "matches" on high-severity rules too.
- **On their paper there are no tracked changes**, so nothing in the text alerts code. Code must not depend on the AI to say "this is risky". The controls below do not depend on the AI's verdict (proposal):
  1. **Required topics:** Every high-risk rule must have a finding in every NDA. If a high-risk topic has no finding, code escalates the NDA.
  2. **Confirm, do not skip:** On their paper, a "matches" on a high-severity rule goes to the lawyer as a one-click confirm. The rule earns a skip only when the shadow log shows enough agreement.
  3. **Text check by code:** Code compares the quoted clause with our template wording. A "matches" with low similarity escalates.
  4. **Random sample:** A lawyer checks a random sample of "matches" calls during the trial and after it.
  5. **Second reader (phase 2):** A different model reads the same NDA. Disagreement on a high-risk topic escalates.

### 3. Test harness versus the production code in `engine/`

- **The same in both:** `build_prompt` renders the same playbook into the same prompt. The same `route` and `to_pred` code ran on the saved output. The `engine/review.py` in the package is the same file as the one that scored the test.
- **The differences:**
  1. **Transport:** In the test, a fresh Claude Sonnet session in Claude Code read the printed prompt and wrote the JSON. In production, one Messages API call sends the prompt.
  2. **Settings:** Production sets temperature 0 and a 16,000 token limit. The agent session used its own defaults, and its own system prompt and tools sat around our prompt.
  3. **Masking:** The live path masks personal data before the call and unmasks after it. The file path skips this, so the scored run did not test masking.
  4. **Parsing:** The live path extracts JSON from free text. The test files were clean JSON from the start.
  5. **Intake:** The test contracts already had `[[DEL]]` and `[[INS]]` markers. Production must convert Word, PDF and DocuSign files and extract tracked changes. None of this is built.
  6. **Operations:** Retries, timeouts, cost and latency are not tested.
- **How to close the gap:** Run the same 30 NDAs through the live API path with `--save-raw`. Compare the new raw output with `replay/`. The consistency evals show that some differences will come from the AI alone, so compare against the re-run spread, not against zero.
