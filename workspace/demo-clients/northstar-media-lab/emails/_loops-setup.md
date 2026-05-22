# Loops Setup Notes

## Events To Create
- `audit.requested`
- `audit.completed`
- `lead.magnet.day_2`
- `audit.opened_no_call_24h`
- `proposal.sent`
- `client.signed`
- `kickoff.scheduled`
- `first.test.live`
- `weekly.report.ready`
- `creative.test.ready`
- `client.milestone.90d`
- `prospect.inactive_30d`

## Segments
- Audit lead
- Sales-qualified prospect
- Proposal open
- New client
- Active client
- Inactive prospect

## Custom Fields
- `first_name`
- `company_name`
- `service_area`
- `average_job_value`
- `primary_service_line`
- `audit_score`
- `diagnostic_call_url`
- `proposal_url`
- `kickoff_doc_url`
- `weekly_report_url`

## Sequence Flows

### Lead-To-Call Flow
1. Send `audit.requested` immediately.
2. Send `audit.completed` when the scorecard is ready.
3. Send `lead.magnet.day_2` after 2 days if no call is booked.
4. Send `audit.opened_no_call_24h` 24 hours after audit open if no call is booked.

### Sales Flow
1. Send `proposal.sent` when the proposal is created.
2. Let the account owner handle final decision follow-up manually.

### Client Onboarding Flow
1. Send `client.signed` immediately after signature.
2. Send `kickoff.scheduled` 1 day before kickoff.
3. Send `first.test.live` when the first test starts.

### Retention Flow
1. Send `weekly.report.ready` every Friday morning.
2. Send `creative.test.ready` when the next ad angle needs approval.
3. Send `client.milestone.90d` when account health is green at 90 days.

### Win-Back Flow
1. Send `prospect.inactive_30d` after 30 days without meaningful activity.
2. Suppress prospects who reply no or do not engage after the close-file email.

## Transactional vs Marketing
- **Transactional:** access checklist, kickoff agenda, first test shipped, weekly signal report, creative angle approval.
- **Marketing:** audit request received, audit score ready, booked-call gap, book diagnostic, proposal recap, referral ask, close-file email.

## Compliance Notes
- Marketing emails need unsubscribe handling.
- Transactional emails should stay tied to the account or service event.
- Do not import bought or scraped lists.
- Suppress inactive marketing contacts after 90-180 days without engagement.

