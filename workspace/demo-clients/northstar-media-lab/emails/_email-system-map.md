# Northstar Media Lab Email System Map

| Stage | Email name | Trigger | Priority | Segment | Purpose |
|---|---|---|---|---|---|
| Welcome | Audit request received | `audit.requested` | P0 | Audit lead | Confirm request and set expectation for the audit score. |
| Nurture | Your audit score is ready | `audit.completed` | P0 | Audit lead | Deliver the score and move toward a diagnostic call. |
| Nurture | The booked-call gap | `lead.magnet.day_2` | P1 | Audit lead | Explain why cheap leads can still lose money. |
| Sales | Book the diagnostic | `audit.opened_no_call_24h` | P0 | Sales-qualified prospect | Convert engaged audit readers into booked calls. |
| Sales | Proposal recap | `proposal.sent` | P0 | Proposal open | Restate plan, scope, and next decision. |
| Onboarding | Access checklist | `client.signed` | P0 | New client | Collect account access, CRM details, and call tracking. |
| Onboarding | Kickoff agenda | `kickoff.scheduled` | P1 | New client | Prepare the client for the first 14 days. |
| Onboarding | First test shipped | `first.test.live` | P1 | New client | Show progress after the first creative test goes live. |
| Retention | Weekly signal report | `weekly.report.ready` | P0 | Active client | Turn reporting into a decision call. |
| Retention | New creative angle | `creative.test.ready` | P1 | Active client | Get approval for the next ad test. |
| Referral | Know another owner? | `client.milestone.90d` | P2 | Active client | Ask for a referral after value is visible. |
| Win-back | Should we close your file? | `prospect.inactive_30d` | P1 | Inactive prospect | Restart stalled opportunities or clean the list. |

## Priority Tiers
- **P0:** Needed for the live demo and launchable first system.
- **P1:** Adds stronger follow-up and client experience.
- **P2:** Adds compounding growth once the core flow is working.

## Flow Summary
- **Lead-to-call flow:** audit request -> audit ready -> booked-call gap -> diagnostic ask.
- **Sales flow:** diagnostic call -> proposal recap -> decision reminder handled by sales manually.
- **Client onboarding flow:** signed -> access checklist -> kickoff agenda -> first test shipped.
- **Retention flow:** weekly signal report -> creative angle approval -> referral milestone.
- **Win-back flow:** inactive prospect receives one plain-English close-file email.

