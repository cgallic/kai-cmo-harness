# Loop Events And Transitions

Use this state table so accounts, contacts, replies, meetings, and CRM handoffs move through the SDR loop predictably.

## Account Transitions

| From | Event | To | Required Evidence |
|---|---|---|---|
| `sourced` | `source_checked` | `source_approved` | `source_id`, terms note |
| `source_approved` | `suppression_checked` | `ready_for_enrichment` | suppression source |
| `ready_for_enrichment` | `enrichment_complete` | `enriched` | field provenance |
| `enriched` | `score_complete` | `scored` | scoring model |
| `scored` | `human_approved` | `approved_for_contact_mapping` | approval record |
| `approved_for_contact_mapping` | `contact_mapped` | `approved_for_copy` | contact role evidence |
| `approved_for_copy` | `copy_ready` | `queued` | cold email gate |
| `queued` | `test_cohort_sent_or_handoff` | `sent` | approval record |
| `sent` | `reply_received` | `replied` | reply record |
| `replied` | `meeting_booked` | `meeting_booked` | meeting record |
| `meeting_booked` | `meeting_completed` | `meeting_completed` | notes or transcript |
| `meeting_completed` | `sales_accepted` | `opportunity_created` | AE or owner acceptance |
| any | `blocked` | `blocked` | blocker reason |
| any | `suppressed` | `suppressed` | suppression event |
| any | `disqualified` | `disqualified` | disqualification reason |

## Reply Transitions

| Reply Category | Event | Next State | Action |
|---|---|---|---|
| `interested` | `meeting_requested` | `meeting_prep_needed` | Trigger `/kai-sales-meeting-prep`. |
| `objection` | `response_allowed` | `response_draft_needed` | Draft one response with evidence. |
| `referral` | `permission_captured` | `new_contact_review` | Create referred contact candidate. |
| `not_now` | `reminder_allowed` | `nurture_task_proposed` | Propose reminder task. |
| `wrong_person` | `routing_allowed` | `routing_request_draft` | Ask for owner only if appropriate. |
| `opt_out` | `suppression_required` | `suppressed` | Add global suppression. |
| `bounce` | `invalid_contact` | `blocked` | Block the address. |
| `complaint` | `human_review_required` | `held_for_review` | Stop sequence and route owner. |

## Meeting Transitions

| From | Event | To | Required Evidence |
|---|---|---|---|
| `meeting_prep_needed` | `prep_complete` | `ready_for_meeting` | meeting brief |
| `ready_for_meeting` | `completed` | `follow_up_needed` | notes or transcript |
| `ready_for_meeting` | `no_show` | `no_show_follow_up_review` | calendar or owner note |
| `follow_up_needed` | `follow_up_drafted` | `crm_handoff_needed` | draft follow-up |
| `crm_handoff_needed` | `sales_accepted` | `opportunity_created` | owner approval |

## Event Record

```yaml
event_id: evt_...
entity_type: account
entity_id: acct_...
from_state: sourced
event: source_checked
to_state: source_approved
actor: kai-sdr-operator
evidence_ids: []
approval_id: null
created_at: 2026-05-27T00:00:00Z
```

## Stale State Rules

- Evidence older than its `expires_at` cannot support new outreach.
- `queued` rows older than 14 days require review before send.
- `not_now` reminders must include a user-approved date or business trigger.
- No-show follow-up requires meeting owner approval.
- Suppression events never expire unless a compliance owner removes them.
