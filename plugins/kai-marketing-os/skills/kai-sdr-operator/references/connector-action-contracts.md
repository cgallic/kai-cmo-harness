# Connector Action Contracts

Every connector action must use one of these action types. The action type sets approval, trace, and allowed output behavior.

## Action Types

| Action | Description | Approval |
|---|---|---|
| `read_preview` | Read a small sample or metadata without spending credits or changing state. | Not required unless data is sensitive. |
| `dry_run` | Build a preview, diff, or payload without calling the live mutation endpoint. | Not required, but attach evidence. |
| `paid_read` | Spend credits or billable API calls to enrich or retrieve data. | Required. |
| `export` | Move data out of a source system. | Required. |
| `import` | Add records to CRM, sequencer, sheet, database, or queue. | Required. |
| `update` | Change records, owners, stages, tasks, notes, fields, or associations. | Required. |
| `send` | Send email, DM, SMS, call, invite, or other outbound message. | Required. |
| `unsubscribe` | Add opt-out or do-not-contact state. | Required by policy; may execute immediately if the user has authorized suppression writes. |
| `analytics` | Read performance, reply, bounce, meeting, or source-quality data. | Not required unless export or sensitive data is involved. |

## Required Action Record

```yaml
action_id: act_...
action_type: read_preview
connector: hubspot
system_account: portal_or_workspace_id
scope: accounts|contacts|campaign|sheet|calendar
row_count: 0
fields_touched: []
source_ids: []
evidence_ids: []
cost_cap: null
dry_run_path: null
approval_id: null
requested_by: operator
status: proposed
created_at: 2026-05-27T00:00:00Z
```

## Status Values

```text
proposed,ready_for_dry_run,dry_run_complete,approval_requested,approved,rejected,running,completed,failed,rolled_back,blocked
```

## Universal Blocks

Block an action when:

- `action_type` is `paid_read`, `export`, `import`, `update`, or `send` and `approval_id` is missing.
- `send` has no suppression check, sender identity, opt-out path, or claim evidence.
- `import` or `update` has no dry-run diff.
- `paid_read` has no cost cap.
- The connector terms are unclear.
- The payload includes sensitive personal data without review.
- The action would bypass access controls, CAPTCHA, login walls, paywalls, robots rules, platform rules, or rate limits.

## Connector Output Contract

Every connector output should include:

```yaml
connector_run_id: crun_...
action_id: act_...
connector: clay
action_type: paid_read
input_hash: sha256...
output_path: workspace/sdr-operator/acme/runs/crun_...json
row_count_in: 0
row_count_out: 0
field_provenance: []
errors: []
blocked_rows: []
retrieved_at: 2026-05-27T00:00:00Z
```

## Dry-Run Diff Shape

```yaml
dry_run_id: dry_...
target_system: hubspot
action_type: import
create_count: 12
update_count: 4
skip_count: 8
blocked_count: 3
protected_fields: []
sample_rows: []
rollback_plan: delete_import_batch_or_revert_fields
```
