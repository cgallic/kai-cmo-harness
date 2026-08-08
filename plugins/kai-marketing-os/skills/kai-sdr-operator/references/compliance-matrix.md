# SDR Compliance Matrix

This matrix is a routing guide, not legal advice. Browse official sources again before live use when rules, regions, platform terms, or sender policies may have changed.

Research date: 2026-05-27.

## Matrix

| Area | Applies When | Kai Rule | Primary Source |
|---|---|---|---|
| CAN-SPAM | B2B commercial email to U.S. recipients | Identify sender, avoid deceptive subjects, include physical address and opt-out, honor opt-out. | `https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business` |
| Gmail sender rules | Sending to Gmail or Google Workspace, especially bulk senders | Authenticate mail, keep spam rates low, support easy unsubscribe where required. | `https://support.google.com/a/answer/14229414?hl=en` |
| GDPR / PECR | EU or UK personal data and electronic marketing | Document lawful basis, minimize fields, honor objection and erasure requests, check local consent rules. | `https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/` |
| TCPA / SMS and calls | U.S. phone, SMS, autodialer, prerecorded, or AI voice workflows | Require consent review before calls or SMS. Respect do-not-call and opt-out. | `https://www.fcc.gov/document/fcc-adopts-rules-protect-consumers-unwanted-robocalls-and-texts` |
| LinkedIn terms | LinkedIn profile, member, messaging, ad, or lead-form data | Do not scrape, automate connection requests, automate DMs, or build sales databases from member data unless an approved program permits it. | `https://www.linkedin.com/help/linkedin/answer/a1341387/prohibited-software-and-extensions%3Flang%3Den` |
| Enrichment vendors | Apollo, Clay, RapidAPI providers, Apify actors, and similar data sources | Vendor output is not consent. Keep source, terms, provider, field provenance, suppression, and approval records. | Vendor docs plus account terms |
| Sequencers | Instantly, Smartlead, Outreach-like systems | Import only approved rows. Keep campaigns paused or queued unless send approval exists. | Vendor API docs and account settings |
| CRM | HubSpot, Salesforce, Pipedrive, Sheets, or warehouse | Use dry-run diffs before create or update. Do not trigger workflows or stage changes without approval. | Vendor API docs and admin policy |
| Employment / recruiting | Hiring, candidate outreach, employment services | Avoid protected traits and sensitive attributes. Use role-fit criteria and human review. | Applicable employment law and platform rules |
| Regulated industries | Healthcare, finance, legal, minors, housing, credit, political | Require human review before production. Remove unsupported claims. | Sector-specific law and platform policy |

## Required Compliance Fields

```text
region,channel,source_id,lawful_basis_or_consent_note,suppression_status,opt_out_path,sender_identity_id,claim_evidence_ids,approval_id
```

## Stop Conditions

Stop the loop when:

- Recipient requests opt-out or no contact.
- Complaint or legal concern appears.
- Sensitive personal data appears unexpectedly.
- Source rights are unclear.
- Sender authentication or opt-out path is missing.
- A user asks to bypass platform policy.

## Recheck Triggers

Browse or request updated docs when:

- The platform changed API access, sender requirements, or messaging terms.
- The workflow enters a new region.
- The channel changes from email to phone, SMS, social DM, or ads.
- The user asks for regulated-industry outreach.
- The last policy retrieval is older than 90 days.
