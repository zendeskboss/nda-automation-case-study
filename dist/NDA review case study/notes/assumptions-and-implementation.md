# Annex: assumptions and implementation

Back to the [case study](../case-study.html).

## Bottom line

The review engine works on clean text in a test folder. Real NDAs arrive by email, as Word files with tracked changes, as PDFs, or as DocuSign envelopes, and the lawyers work in Word or Google Docs. Fitting the tool into that flow is where we expect most of the effort. We have not tested any of it yet.

Each assumption below is something we must confirm with the legal team before a pilot.

## Assumptions

### About the rules

| # | Assumption | Why it matters | How to confirm |
|---|---|---|---|
| A1 | The playbook positions are correct. Every line marked "ASSUMED" in `engine/playbook.yaml` is our guess. | Wrong rules produce confident wrong answers. | The worksheet sessions |
| A2 | The playbook owner is the Head of Legal. | Someone must sign off each version. | Ask the legal team |
| A3 | The tracker holds the risk IDs R01 to R16 that the rules point to. | Findings must trace back to the team's own risk list. | Check the Google Sheet |
| A4 | The confidence threshold of 0.6 is a placeholder. | Too low lets wrong calls through. Too high sends everything to a lawyer. | Set it from the shadow log |
| A5 | The scope is mutual NDAs under the law of England and Wales. | Other contract types and other laws need their own rules. | The worksheet, tab 1 |

### About the test

| # | Assumption | Why it matters | How to confirm |
|---|---|---|---|
| A6 | The 30 test NDAs are like the real ones in content and mix. They are synthetic. | Real volume, formats and counterparty asks may differ. | Sample 30 to 50 real NDAs from the last year, starting with the Examples tab of the process discovery workbook |
| A7 | The results hold up when scored. The findings are not yet scored against a lawyer's answer key. | The lane split shows where findings went, not whether each call was right. | First the test-set author labels `evals/answer_key_template.csv` for a recall figure. Score `engine/preds/` against a lawyer's labels after that |
| A8 | The production model gives similar results. The test reviews were made by Claude Sonnet subagents in a Claude Code session with the engine's exact prompt, one per contract, not by the live API call in `review.py`. | A different set-up can give different findings. Re-runs of the same set-up already differ: see `evals/EVAL_REPORT.md`, section 5. | Re-run the 30 through the live API at temperature 0, five times each, and compare |
| A9 | Tracked changes convert cleanly to the `[[INS]]` and `[[DEL]]` markers. The test set was written in that format. | Conversion errors would make the tool judge the wrong text. | Convert 10 real Word files and check them by hand |

### About people and process

| # | Assumption | Why it matters | How to confirm |
|---|---|---|---|
| A10 | Three one-hour sessions are enough to fill in the worksheet. | Under-filled rules mean more escalations. | Run session 1 and adjust |
| A11 | Lawyers will act on a sorted list of findings and trust the routing. | Without trust, they re-read every NDA and save no time. | The shadow pilot |
| A12 | Masked contract text may go to an external AI provider. Signatory names, emails and phone numbers are masked first; company names and terms are not. | Data protection, confidentiality and client terms may forbid it. | Data protection and security review, the provider's zero-retention and DPA terms, and a proper PII detector |
| A14 | The injection screen and prompt guard hold against a real attacker. They were tested on 3 hostile NDAs only. | A tuned attack could pass the screen and talk the model into a "matches". | A red-team set of 50 or more hostile NDAs, run five times each through the live API |
| A13 | Keeping easy work with people (case study, stage 11) is worth the lost time saving. | It reduces throughput on purpose. | The legal team decides the rate |

## Implementation options

### The questions that decide the route

1. Where do NDAs arrive today: a shared mailbox, individual inboxes, a request form, or a contract system?
2. In which format: Word with tracked changes, PDF, Google Docs, or a DocuSign envelope?
3. Where do the lawyers work on them: Word, Google Docs, or email?
4. Where must the record end up: the tracker, a contract system, or a shared drive?

A short discovery (a week of watching how NDAs arrive) answers these. The "Tools and data" tab of the [process discovery workbook](../discovery/process-discovery-workbook.xlsx) collects the same facts from each lawyer. We should not choose a route before the discovery.

### The options

| Route | How it works | Strengths | Risks and unknowns |
|---|---|---|---|
| NDA mailbox and internal tool | Counterparties and staff send NDAs to one shared mailbox. A small service picks up each attachment, runs the review and sends the lawyer a link to the review page. | One front door. Works with any document format the converter handles. The review page already exists. | Needs hosting, mailbox access and security approval. People must change where they send NDAs. |
| Google Docs add-on (Apps Script) | The lawyer opens the NDA in Google Docs and runs the review from a side panel. Findings appear as comments on the clauses. | Works where the lawyers already work. Feedback can be a reply to a comment. The Docs API reads the counterparty's suggested edits inline (`suggestionsViewMode: SUGGESTIONS_INLINE`), so they map to our `[[INS]]` and `[[DEL]]` markers. The API can also write the tool's drafted fix as a suggestion (`writeMode: SUGGEST`) that the lawyer accepts or rejects. | Only fits if the team uses Google Docs. Apps Script quotas and approval to call an external AI service. |
| Word add-in | The same idea inside Word. Tracked changes are already in the file. | Fits teams that negotiate in Word, which is common for legal work. | Needs a Microsoft 365 add-in and IT approval. Reading tracked changes through the Word API needs a test. |
| DocuSign or a contract system | The review runs when an NDA enters the e-signature or contract workflow, for example through a webhook. | Fits teams that already route all contracts through one system. | E-signature usually starts after negotiation, so the redlines may already be gone and the file may be a flat PDF. A contract system may already offer AI review, which turns this into a buy-or-build decision. |

### Format cases the converter must handle

| Arrives as | What the tool must do |
|---|---|
| Our template in Word, with tracked changes | Convert the tracked changes to `[[INS]]` and `[[DEL]]` markers. This is the case the test set covers. |
| Our template in Google Docs, with suggested edits | Read the document with suggestions inline and convert each suggested insertion and deletion to the markers. The API supports this. |
| Our template, changed without tracked changes | Compare the file against our template to find the edits. Not built. |
| Their paper, Word or PDF | Review the whole text against the playbook. The engine already does this. PDFs need clean text extraction. |
| Scanned PDF | Text recognition (OCR) first. Error-prone. Send to a lawyer by default. |
| DocuSign envelope ready to sign | Extract the text and review it as their paper. Flag that the negotiation history is missing. |

### Our starting suggestion

Start with the NDA mailbox and the existing review page, because it does not depend on which editor the lawyers use. Add a Word or Google Docs add-in later, once the discovery shows where the lawyers work. Treat DocuSign as a final check before signature, not as the main entry point.
