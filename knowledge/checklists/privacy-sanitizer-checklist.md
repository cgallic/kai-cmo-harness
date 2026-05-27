# Privacy Sanitizer Checklist

> **Use when:** Handling transcripts, CRM exports, analytics exports, ad account data, customer messages, screenshots, source ledgers, prompt logs, or artifacts that may contain private data.

---

## Required Before Processing

- [ ] Declare mode: `sales_external`, `onboarding_connected`, or `internal_demo`.
- [ ] Identify data owner and approval owner.
- [ ] Confirm lawful basis, consent, or internal-use scope.
- [ ] Scan files before summarizing, uploading, embedding, or sending to another tool.
- [ ] Create `_data-gaps.md` if ownership, consent, or source quality is unclear.
- [ ] Stop external publication if private data cannot be removed safely.

---

## Must Detect

- [ ] Email addresses.
- [ ] Phone numbers.
- [ ] Physical addresses.
- [ ] Personal names when not approved for publication.
- [ ] Customer, patient, applicant, student, employee, or lead identifiers.
- [ ] Company names under NDA or private sales review.
- [ ] API keys, tokens, cookies, session IDs, OAuth secrets, webhook secrets.
- [ ] Ad account IDs, CRM IDs, invoice IDs, order IDs, ticket IDs.
- [ ] Payment, bank, tax, insurance, health, legal, or employment details.
- [ ] Raw transcripts that include private strategy, pricing, objections, or customer data.
- [ ] Screenshots with visible URLs, account names, email inboxes, dashboards, or exports.

---

## Sanitization Actions

- [ ] Replace private identifiers with stable labels such as `Customer A`, `Lead 12`, or `Account 3`.
- [ ] Preserve source meaning while removing contact details.
- [ ] Keep timestamps when needed for transcript or clip review.
- [ ] Keep aggregate numbers only when source approval allows it.
- [ ] Redact secrets completely; do not mask only the middle characters in publishable artifacts.
- [ ] Store raw files only in approved local/private locations.
- [ ] Do not log raw prompts, raw transcripts, file paths, secrets, client names, or private URLs in telemetry.

---

## Publication Gate

Before a client-facing artifact ships:

- [ ] No unapproved PII remains.
- [ ] No confidential strategy or internal pricing detail remains.
- [ ] No unsupported customer quote, endorsement, or case result remains.
- [ ] Quantitative claims cite approved sources.
- [ ] Screenshots are cropped or redacted.
- [ ] Demo data is labeled `internal_demo`.
- [ ] The approval owner has reviewed the sanitized artifact.

---

## Blockers

Stop and request review when:

- [ ] Consent or ownership is unknown.
- [ ] A transcript contains sensitive personal data.
- [ ] A customer quote is intended for public use without approval.
- [ ] A source file includes secrets or credentials.
- [ ] The requested output would expose private lead, customer, employee, patient, or applicant data.
- [ ] Sanitization would remove so much context that the claim cannot be supported.
