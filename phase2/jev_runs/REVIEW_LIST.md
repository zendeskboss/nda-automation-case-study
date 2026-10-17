# Jev review list

Saved runs from `phase2/jev_runs/`. Quotes are copied from the saved reviews and the contracts.
This list shows where Jev and the LLM differ. It does not say which one is right.

## Part 1: Jev and the LLM disagree (26 findings)

`position_check` probabilities: matches_preferred / meets_fallback / breaches / unclear.

### 1. C01 clause 12.10 · PB18 Governing law and jurisdiction

- **LLM:** deviation (confidence 0.90), routed as `escalate`, lane `purple_ai`
- **Jev:** matches_preferred (confidence 0.48) · 0.61 / 0.35 / 0.02 / 0.02
- **LLM reason:** The clause itself keeps English law, but the counterparty comment asks for Delaware or New York law or silence on governing law and venue, which is a request to change governing law that the playbook says to decline.

> shall be governed by and construed in accordance with the law of England and Wales.

### 2. C04 clause 12.10 · PB18 Governing law and jurisdiction

- **LLM:** deviation (confidence 0.90), routed as `escalate`, lane `purple_ai`
- **Jev:** matches_preferred (confidence 0.81) · 0.86 / 0.00 / 0.09 / 0.05
- **LLM reason:** The margin comment asks for Irish governing law and exclusive Irish jurisdiction, although the clause text still reads England and Wales.

> our Board's preference is for this Agreement to be governed by the laws of Ireland and subject to the exclusive jurisdiction of the Irish courts in Clause 12.11

### 3. C04 clause 3.1 · PB04 Carve-outs

- **LLM:** matches (confidence 0.90), routed as `matches`, lane `purple_human`
- **Jev:** breaches (confidence 0.40) · 0.23 / 0.18 / 0.55 / 0.04
- **LLM reason:** All four carve-outs (public domain, already held, third party, independent development) are present with a 'written records or other reasonable evidence' standard.

> is independently developed by or on behalf of the Receiving Party without access to, use of, or reference to any of the Disclosing Party's Confidential Information.

### 4. C05 clause 10.3 · PB12 Term and survival

- **LLM:** deviation (confidence 0.70), routed as `escalate`, lane `purple_ai`
- **Jev:** matches_preferred (confidence 0.96) · 0.97 / 0.02 / 0.01 / 0.00
- **LLM reason:** The counterparty asks for survival of 18 months, below the 2-year minimum Halyard can accept, so this must be escalated; the clause text itself (3 years plus Trade Secrets) matches the playbook.

> Our internal policy caps post-termination confidentiality obligations at 18 months from the date of disclosure. Please confirm if Clause 10.3 can be amended accordingly.

### 5. C05 clause 12.10 · PB18 Governing law and jurisdiction

- **LLM:** deviation (confidence 0.70), routed as `escalate`, lane `purple_ai`
- **Jev:** matches_preferred (confidence 0.55) · 0.66 / 0.11 / 0.15 / 0.08
- **LLM reason:** The counterparty asks to change governing law and courts to Dutch law and Amsterdam, which the playbook does not accept; the clause text itself is England and Wales law and exclusive English jurisdiction.

> our standard position is for Dutch law and the District Court of Amsterdam (Rechtbank Amsterdam) to apply under Clauses 12.10 and 12.11

### 6. C05 clause 12.1 · PB19 Assignment

- **LLM:** matches (confidence 0.90), routed as `matches`, lane `purple_ai`
- **Jev:** breaches (confidence 0.68) · 0.15 / 0.00 / 0.76 / 0.09
- **LLM reason:** No assignment by either party without prior written consent.

> without the prior written consent of the other Party

### 7. C06 clause 12.10 · PB18 Governing law and jurisdiction

- **LLM:** deviation (confidence 0.90), routed as `escalate`, lane `purple_ai`
- **Jev:** matches_preferred (confidence 0.67) · 0.75 / 0.04 / 0.15 / 0.06
- **LLM reason:** A margin comment asks Halyard to accept New York law and exclusive New York courts in 12.10 and 12.11; the text is unchanged but the request is a change to non-English governing law and jurisdiction.

> all vendor NDAs to be governed by the laws of the State of New York with exclusive jurisdiction in the federal and state courts located in New York County, plus a mutual waiver of jury trial

### 8. C07 clause 7.2 (comment) · PB17 Residuals

- **LLM:** deviation (confidence 0.96), routed as `escalate`, lane `purple_human`
- **Jev:** matches_preferred (confidence 0.56) · 0.67 / 0.00 / 0.30 / 0.03
- **LLM reason:** The counterparty asks for a residuals right to use information retained in unaided memory, which the playbook does not permit in any form.

> we normally include a standard residuals clause confirming that our personnel are free to use general skills, know-how and experience retained in their unaided memories

### 9. C07 clause 3.1 · PB04 Carve-outs

- **LLM:** matches (confidence 0.93), routed as `matches`, lane `purple_human`
- **Jev:** breaches (confidence 0.77) · 0.10 / 0.07 / 0.83 / 0.00
- **LLM reason:** All four carve-outs are present, unnarrowed, with a written records or reasonable evidence standard.

> 3.1.4 is independently developed by or on behalf of the Receiving Party without access to, use of, or reference to any of the Disclosing Party's Confidential Information.

### 10. C08 clause 12.10 · PB18 Governing law and jurisdiction

- **LLM:** deviation (confidence 0.90), routed as `escalate`, lane `purple_ai`
- **Jev:** matches_preferred (confidence 0.40) · 0.55 / 0.02 / 0.36 / 0.07
- **LLM reason:** The margin comment asks for French law and exclusive Lyon jurisdiction, or Swiss law and courts, which is a request to move away from England and Wales.

> our group policy is to request French law and the exclusive jurisdiction of the Commercial Court of Lyon (Tribunal de commerce de Lyon), or failing that, neutral governing law and jurisdiction in Switzerland

### 11. C09 clause 3.1 · PB04 Carve-outs

- **LLM:** acceptable (confidence 0.50), routed as `escalate`, lane `purple_human`
- **Jev:** breaches (confidence 0.53) · 0.01 / 0.33 / 0.65 / 0.01
- **LLM reason:** Requiring contemporaneous written records is a stricter variant of the accepted 'written records' evidence standard, with the 'other reasonable evidence' option removed, which narrows the carve-outs.

> by [[INS: contemporaneous]] written records [[DEL: or other reasonable evidence]]

### 12. C09 clause 11.1 · PB13 Remedies

- **LLM:** matches (confidence 0.93), routed as `matches`, lane `orange`
- **Jev:** breaches (confidence 0.31) · 0.47 / 0.04 / 0.48 / 0.01
- **LLM reason:** Mutual right to seek equitable relief, with cumulative remedies in 11.2.

> a Party shall be entitled to seek the remedies of injunction, specific performance and other equitable relief

### 13. C10 clause 10.3 · PB12 Term and survival

- **LLM:** deviation (confidence 0.80), routed as `escalate`, lane `purple_ai`
- **Jev:** matches_preferred (confidence 0.89) · 0.92 / 0.07 / 0.01 / 0.00
- **LLM reason:** The comment asks for 2-year survival, which is acceptable, but also removal of Trade Secret protection, which the request rule says must be kept, so the request cannot be accepted as made.

> Can we reduce the 3-year period to 2 years and remove the open-ended Trade Secret survival tail?

### 14. C13 clause 3.1 · PB04 Carve-outs

- **LLM:** matches (confidence 0.90), routed as `matches`, lane `purple_human`
- **Jev:** breaches (confidence 0.64) · 0.19 / 0.06 / 0.73 / 0.02
- **LLM reason:** All four carve-outs are present (public domain, already known, third party, independently developed) with no narrowing beyond a demonstrate standard.

> is already in or enters the public domain without any breach of this Agreement

### 15. C13 clause 5.2 · PB07 Return and destruction

- **LLM:** matches (confidence 0.85), routed as `matches`, lane `purple_ai`
- **Jev:** breaches (confidence 0.25) · 0.22 / 0.07 / 0.44 / 0.27
- **LLM reason:** Return or destroy on request with a ten business day confirmation and an exception for legal copies and automated backups that stay confidential.

> The Recipient may keep copies of Confidential Information to the extent required by applicable law, regulatory compliance or automated electronic system backups created in the ordinary course of business.

### 16. C16 clause 10.2 · PB13 Remedies

- **LLM:** matches (confidence 0.85), routed as `matches`, lane `orange`
- **Jev:** breaches (confidence 0.31) · 0.15 / 0.33 / 0.48 / 0.04
- **LLM reason:** Equitable relief is available to the Disclosing Party, so mutual, and remedies are cumulative.

> the Disclosing Party shall be entitled, in addition to all other legal and equitable remedies available to it, to seek and obtain injunctive relief

### 17. C16 clause 2.3 · PB03 Purpose limitation

- **LLM:** matches (confidence 0.80), routed as `matches`, lane `purple_ai`
- **Jev:** unclear (confidence 0.63) · 0.09 / 0.13 / 0.06 / 0.72
- **LLM reason:** Use is restricted solely to the Authorised Purpose, which is acceptable once the purpose itself is narrowed.

> shall use the Confidential Information of the Disclosing Party solely and exclusively for the Authorised Purpose

### 18. C19 clause 3.1 · PB04 Carve-outs

- **LLM:** matches (confidence 0.85), routed as `matches`, lane `purple_human`
- **Jev:** breaches (confidence 0.73) · 0.14 / 0.04 / 0.80 / 0.02
- **LLM reason:** All four carve-outs are present (public domain, already held, lawfully received from a third party, independently developed) without narrowing.

> is or becomes publicly available without breach of this Agreement;

### 19. C20 clause 4.1 · PB04 Carve-outs

- **LLM:** acceptable (confidence 0.80), routed as `escalate`, lane `purple_human`
- **Jev:** unclear (confidence 0.25) · 0.18 / 0.24 / 0.14 / 0.44
- **LLM reason:** All four carve-outs (public domain, already held, third party, independently developed) are present, subject to a written-evidence standard.

> The confidentiality obligations in Clause 2 do not apply to any Information that the Recipient can verify by written evidence:

### 20. C20 clause 2.4 · PB03 Purpose limitation

- **LLM:** matches (confidence 0.75), routed as `matches`, lane `purple_ai`
- **Jev:** unclear (confidence 0.16) · 0.37 / 0.25 / 0.02 / 0.36
- **LLM reason:** Use is limited solely to the Purpose, a potential business relationship on a defined subject area.

> The Recipient shall use the Confidential Information solely for the Purpose

### 21. C21 clause 3.1 · PB05 Permitted disclosure to Representatives and Group

- **LLM:** matches (confidence 0.70), routed as `matches`, lane `purple_ai`
- **Jev:** breaches (confidence 0.48) · 0.09 / 0.08 / 0.61 / 0.22
- **LLM reason:** Need-to-know disclosure to Affiliates, officers, employees, counsel, accountants and advisors with liability for them; insurers are not named.

> The Receiving Party may disclose the Disclosing Party's Confidential Information only to those of its Representatives who need to know such information for the Purpose

### 22. C22 clause 3.1 · PB04 Carve-outs

- **LLM:** deviation (confidence 0.50), routed as `escalate`, lane `purple_human`
- **Jev:** meets_fallback (confidence 0.25) · 0.01 / 0.44 / 0.34 / 0.21
- **LLM reason:** All four carve-outs are present and a written-records standard is acceptable, but requiring contemporaneous records and (3.1.4) no access by the developing staff arguably narrows them; unsure so deviation.

> can prove by objective, contemporaneous written records

### 23. C22 clause 4.1 · PB05 Permitted disclosure to Representatives and Group

- **LLM:** acceptable (confidence 0.60), routed as `acceptable`, lane `purple_ai`
- **Jev:** breaches (confidence 0.57) · 0.06 / 0.08 / 0.68 / 0.18
- **LLM reason:** Representatives (directors, employees, advisers, auditors, Affiliates) may receive information on a need-to-know basis with the Receiving Party liable for them; insurers are not listed.

> only to those of its Representatives who have a strict need to know

### 24. C26 clause 3.1 · PB05 Permitted disclosure to Representatives and Group

- **LLM:** matches (confidence 0.75), routed as `matches`, lane `purple_ai`
- **Jev:** unclear (confidence 0.24) · 0.24 / 0.13 / 0.20 / 0.43
- **LLM reason:** Need-to-know disclosure to Affiliates, directors, officers, employees, advisers and auditors with Receiving Party liability under 3.2; insurers are not named but this is not a listed deviation.

> those of its Representatives who have a need to know such information in furtherance of the Transaction Purpose

### 25. C27 clause 4.1 · PB04 Carve-outs

- **LLM:** acceptable (confidence 0.60), routed as `escalate`, lane `purple_human`
- **Jev:** unclear (confidence 0.24) · 0.20 / 0.18 / 0.19 / 0.43
- **LLM reason:** All four carve-outs are present and the evidence standard is documentary records.

> Receiving Party can demonstrate through contemporaneous documentary evidence

### 26. C27 clause 5.1 · PB06 Compelled disclosure

- **LLM:** matches (confidence 0.80), routed as `matches`, lane `purple_ai`
- **Jev:** unclear (confidence 0.49) · 0.30 / 0.05 / 0.03 / 0.62
- **LLM reason:** Legally required disclosure permitted, notice only to the extent legally permissible, cooperation at Disclosing Party's expense.

> provided that Receiving Party shall:

## Part 2: absent-preferred clause present, no finding (11)

Jev's contract check reads the topic as present, but the LLM made no finding on it.
Jev gives no location, so the lines below come from a keyword search. They are candidates only.

### 1. C01 · PB14 Indemnities and liability (Jev: present 0.52)

> 7.4 Neither the Disclosing Party nor any of its Representatives shall have any liability to the Receiving Party or to any other person resulting from the use of, or reliance upon, the Confidential Information by the Receiving Party, save that nothing in this Agreement shall exclude or limit either Party's liability for fraud or fraudulent misrepresentation.

> 10.2 Expiry or termination of this Agreement shall not affect any accrued rights, remedies, obligations or liabilities of the Parties existing at the date of expiry or termination.

### 2. C02 · PB14 Indemnities and liability (Jev: present 0.56)

> 7.4 Neither the Disclosing Party nor any of its Representatives shall have any liability to the Receiving Party or to any other person resulting from the use of, or reliance upon, the Confidential Information by the Receiving Party, save that nothing in this Agreement shall exclude or limit either Party's liability for fraud or fraudulent misrepresentation.

> 10.2 Expiry or termination of this Agreement shall not affect any accrued rights, remedies, obligations or liabilities of the Parties existing at the date of expiry or termination.

### 3. C05 · PB14 Indemnities and liability (Jev: present 0.54)

> (2) [[DEL: [COUNTERPARTY NAME], a company incorporated and registered in [JURISDICTION] with company number [NUMBER] whose registered office is at [ADDRESS]]][[INS: VLIET & VAN DER BERG ADVIES B.V., a private company with limited liability (besloten vennootschap met beperkte aansprakelijkheid) incorporated under the laws of the Netherlands, registered with the Dutch Trade Register (Kamer van Koophandel) under number 74829103 and having its corporate seat in Amsterdam and its principal place of business at Keizersgracht 482, 1017 EG Amsterdam, the Netherlands]] (Counterparty),

> 7.4 [[DEL: Neither the Disclosing Party nor any of its Representatives shall have any liability to the Receiving Party or to any other person resulting from the use of, or reliance upon, the Confidential Information by the Receiving Party, save that nothing in this Agreement shall exclude or limit either Party's liability for fraud or fraudulent misrepresentation.]][[INS: Save as hereinafter expressly provided to the contrary, neither the Disclosing Party nor any of its Representatives whosoever shall incur or be subject to any liability howsoever arising, whether in contract, tort (including negligence), breach of statutory duty or otherwise, unto the Receiving Party or any third party whomsoever resulting from the utilisation of, or reliance upon, the Confidential Information by the Receiving Party; provided always that, notwithstanding the foregoing or anything else herein contained, nothing in this Agreement shall operate or be construed so as to exclude, restrict or limit the liability of either Party in respect of fraud or fraudulent misrepresentation.]]

> 10.2 Expiry or termination of this Agreement shall not affect any accrued rights, remedies, obligations or liabilities of the Parties existing at the date of expiry or termination.

### 4. C08 · PB14 Indemnities and liability (Jev: present 0.51)

> 7.4 Neither the Disclosing Party nor any of its Representatives shall have any liability to the Receiving Party or to any other person resulting from the use of, or reliance upon, the Confidential Information by the Receiving Party, save that nothing in this Agreement shall exclude or limit either Party's liability for fraud or fraudulent misrepresentation.

> 10.2 Expiry or termination of this Agreement shall not affect any accrued rights, remedies, obligations or liabilities of the Parties existing at the date of expiry or termination.

### 5. C09 · PB14 Indemnities and liability (Jev: present 0.54)

> 7.4 Neither the Disclosing Party nor any of its Representatives shall have any liability to the Receiving Party or to any other person resulting from the use of, or reliance upon, the Confidential Information by the Receiving Party, save that nothing in this Agreement shall exclude or limit either Party's liability for fraud or fraudulent misrepresentation.

> 10.2 Expiry or termination of this Agreement shall not affect any accrued rights, remedies, obligations or liabilities of the Parties existing at the date of expiry or termination.

### 6. C10 · PB14 Indemnities and liability (Jev: present 0.54)

> 7.4 Neither the Disclosing Party nor any of its Representatives shall have any liability to the Receiving Party or to any other person resulting from the use of, or reliance upon, the Confidential Information by the Receiving Party, save that nothing in this Agreement shall exclude or limit either Party's liability for fraud or fraudulent misrepresentation.

> 10.2 Expiry or termination of this Agreement shall not affect any accrued rights, remedies, obligations or liabilities of the Parties existing at the date of expiry or termination.

### 7. C16 · PB14 Indemnities and liability (Jev: present 0.54)

> 8.2 Neither Party nor its Representatives shall have any liability or responsibility to the other Party or any other person resulting from any use of, evaluation of, or reliance upon the Disclosing Party's Confidential Information, except as expressly provided in this Agreement or in any definitive written agreement subsequently entered into by the Parties.

### 8. C22 · PB14 Indemnities and liability (Jev: present 0.51)

> 8.2 The Disclosing Party shall have no liability whatsoever for any direct, indirect, incidental, consequential, or economic loss or damage arising from or in connection with the Receiving Party's use of, reliance upon, or inability to use the Confidential Information, except in instances of deliberate intent (Vorsatz) or gross negligence (grobe Fahrlässigkeit).

### 9. C25 · PB14 Indemnities and liability (Jev: present 0.54)

> (1) VANDENBERG STRATEGY & TECHNOLOGY ADVISORY B.V., a private limited liability company (besloten vennootschap met beperkte aansprakelijkheid) incorporated under the laws of the Netherlands, having its statutory seat in Amsterdam, the Netherlands, and its principal place of business at Keizersgracht 482, 1016 EG Amsterdam, registered with the Dutch Chamber of Commerce (Kamer van Koophandel) under registration number 68412953 ("Vandenberg"); and

> 1.1.10 "Person" means any natural person, corporation, partnership, limited liability company, cooperative, association, trust, unincorporated organization, or other legal entity.

> 8.2 Limitation of Liability

> Neither Party shall incur any liability toward the other Party arising out of or resulting from the other Party's use of or reliance upon any Confidential Information disclosed pursuant to this Agreement, except in instances of deliberate fraud or fraudulent misrepresentation.

### 10. C26 · PB16 Non-compete and exclusivity (Jev: present 0.63)

> 5.2 Nothing contained in this Agreement shall restrict either Party or its Affiliates from independently acquiring, designing, developing, procuring, evaluating, marketing or licensing products, software, architectures or services that may be competitive with or functionally similar to those offered or developed by the other Party, provided that such activities do not breach the express non-disclosure provisions of this Agreement.

> 7.1 All right, title and interest in and to the Confidential Information, including all intellectual property rights therein, shall remain the sole and exclusive property of the Disclosing Party or its respective licensors.

> 10.2 Accordingly, in the event of any breach or threatened breach of this Agreement, the non-breaching Party shall be entitled to seek injunctive relief, specific performance and other equitable remedies in any court of competent jurisdiction, without prejudice to any other rights or remedies to which it may be entitled at law or in equity, and without the requirement to post any bond or prove actual damages.

> 11.5 If any provision of this Agreement is held to be invalid, illegal or unenforceable by any court of competent jurisdiction, such provision shall be severed or modified to the minimum extent necessary, and the remaining provisions of this Agreement shall remain in full force and effect.

### 11. C30 · PB16 Non-compete and exclusivity (Jev: present 0.61)

> 2.1.2 use the Proprietary Information solely and strictly for the evaluation and execution of the Permitted Purpose and for no other commercial, developmental, or competitive purpose;

> 2.1.3 restrict distribution of and access to Proprietary Information exclusively to those of its Representatives who have a genuine need to know such information for the Permitted Purpose, provided that each such Representative is bound by non-disclosure undertakings at least as protective as those contained in this Agreement; and

> 5.1 All Proprietary Information, including all worldwide patents, copyrights, trade secrets, trademarks, and other intellectual property rights subsisting therein, remains the exclusive property of the Disclosing Party or its respective licensors.

> 8.1 The Parties recognise and agree that any unauthorised use, dissemination, or disclosure of Proprietary Information would cause substantial, immediate, and irreparable injury to the Disclosing Party for which financial damages alone would not provide an adequate remedy. Consequently, the Disclosing Party shall be entitled to seek injunctive relief, specific performance, and other available equitable remedies from any court of competent jurisdiction without the necessity of proving actual damages or posting any bond.
