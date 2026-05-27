# SDR Data Model

Use this model for every SDR operating package. The goal is durable state that a human, agent, CRM, sequencer, or future UI can read without guessing.

## Core Entities

| Entity | Purpose | Required IDs |
|---|---|---|
| `account` | Company, organization, location, partner, or buyer group. | `account_id`, `source_id` |
| `contact` | Person or role-based contact tied to an account. | `contact_id`, `account_id`, `source_id` |
| `source` | Where data came from and why it is allowed. | `source_id`, `source_name`, `retrieved_at` |
| `evidence` | Proof for fit, trigger, role, pain, or claim. | `evidence_id`, `source_id`, `retrieved_at` |
| `run` | One execution pass through the SDR loop. | `run_id`, `package_id` |
| `action` | Proposed or executed connector, CRM, sequencer, phone, SMS, email, or calendar action. | `action_id`, `run_id` |
| `connector_run` | Dry-run or live connector call. | `connector_run_id`, `action_id` |
| `schedule` | Planned recurring loop, reminder, follow-up, or review. | `schedule_id`, `entity_id` |
| `approval` | Human approval or rejection of a live action. | `approval_id`, `action_id`, `approver` |
| `suppression_event` | Opt-out, do-not-contact, bounce, complaint, or invalid address state. | `suppression_event_id`, `contact_id` |
| `consent_event` | Consent, lawful-basis note, or permission trail. | `consent_event_id`, `contact_id` |
| `message` | Drafted or sent outbound touch. | `message_id`, `contact_id`, `sequence_id` |
| `reply` | Inbound response, bounce, opt-out, referral, or objection. | `reply_id`, `message_id`, `contact_id` |
| `meeting` | Booked, completed, no-show, or canceled meeting. | `meeting_id`, `account_id`, `contact_id` |
| `crm_handoff` | Proposed CRM record, task, note, owner, or stage change. | `handoff_id`, `approval_id` |
| `learning` | Outcome memory promoted from real results. | `learning_id`, `evidence_id` |

## Account Fields

Minimum account fields:

```text
account_id,company,website,industry,geo,company_size,segment,source_id,fit_score,timing_score,pain_score,reachability_score,compliance_score,total_score,disqualification_reason,status,owner,next_action,created_at,updated_at
```

Account statuses:

```text
sourced,enriched,scored,blocked,approved_for_contact_mapping,approved_for_copy,queued,sent,replied,meeting_booked,meeting_completed,opportunity_created,disqualified,suppressed,closed_lost,closed_won
```

## Contact Fields

Minimum contact fields:

```text
contact_id,account_id,name,title,role_category,seniority,channel,email,phone,linkedin_url,source_id,personalization_note,personalization_evidence_id,suppression_status,consent_basis,confidence,status,next_action
```

Do not store sensitive personal attributes unless a lawful basis, business need, and human approval are documented.

## Run Fields

Minimum run fields:

```text
run_id,package_id,workflow,mode,actor,started_at,ended_at,status,input_paths,output_paths,blocked_reason
```

Run statuses:

```text
proposed,running,blocked,needs_approval,completed,failed,closed
```

## Action Fields

Minimum action fields:

```text
action_id,run_id,action_type,system,scope,row_count,fields_touched,cost_cap,dry_run_path,approval_id,status,created_at
```

Action types:

- `read_preview`
- `dry_run`
- `paid_read`
- `export`
- `import`
- `update`
- `send`
- `unsubscribe`
- `analytics`

## Connector Run Fields

Minimum connector run fields:

```text
connector_run_id,action_id,connector,input_hash,output_path,row_count_in,row_count_out,field_provenance,errors,blocked_rows,retrieved_at
```

## Schedule Fields

Minimum schedule fields:

```text
schedule_id,entity_type,entity_id,schedule_type,due_at,owner,status,approval_id,notes
```

Schedule types:

- `follow_up`
- `not_now_reminder`
- `policy_refresh`
- `evidence_refresh`
- `weekly_learning_loop`
- `daily_briefing`

## Evidence Fields

Minimum evidence fields:

```text
evidence_id,source_id,evidence_type,claim_supported,url_or_note,retrieved_at,confidence,expires_at,owner
```

Evidence types:

- `fit`
- `trigger`
- `pain`
- `role`
- `claim`
- `suppression`
- `consent`
- `meeting`
- `outcome`

## Approval Fields

Minimum approval fields:

```text
approval_id,action_id,action_type,risk_tier,requested_by,approver,decision,decision_at,conditions,rollback_plan,evidence_ids
```

Approval decisions:

- `approved`
- `approved_with_conditions`
- `rejected`
- `needs_more_evidence`
- `expired`

## Suppression Event Fields

Minimum suppression event fields:

```text
suppression_event_id,contact_id,account_id,event_type,source,received_at,applies_to,reason,owner
```

Suppression event types:

- `opt_out`
- `do_not_contact`
- `bounce`
- `complaint`
- `invalid_address`
- `manual_suppression`

Suppression events should block future outreach until a compliance owner resolves them.

## Consent Event Fields

Minimum consent event fields:

```text
consent_event_id,contact_id,account_id,channel,basis_or_permission,source_id,evidence_id,recorded_at,expires_at,owner
```

## Learning Fields

Minimum learning fields:

```text
learning_id,learning_type,segment,signal,observed_result,sample_size,confidence,promoted_to_default,created_at,expires_at
```

Learning types:

- `source_quality`
- `trigger_quality`
- `message_quality`
- `persona_quality`
- `objection_pattern`
- `meeting_quality`
- `crm_stage_quality`

Promote a learning only when it comes from real outcomes, not from model preference.
