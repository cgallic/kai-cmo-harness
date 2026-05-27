# Observability And Run Ledger

The SDR loop needs run history before it needs a dashboard. Use this ledger to trace actions, approvals, connector calls, sends, replies, meetings, and memory promotion.

## Required Ledgers

| Ledger | File | Purpose |
|---|---|---|
| Run ledger | `run-ledger.jsonl` | One row per SDR loop run. |
| Action ledger | `action-ledger.jsonl` | One row per proposed or executed action. |
| Connector ledger | `connector-ledger.jsonl` | One row per connector call or dry run. |
| Approval ledger | `approval-ledger.jsonl` | One row per human decision. |
| Suppression ledger | `suppression-ledger.jsonl` | One row per opt-out, bounce block, do-not-contact, or complaint. |
| Memory ledger | `memory-ledger.md` or `memory-ledger.jsonl` | Outcome learnings and promotion status. |

## Run Record

```json
{
  "run_id": "run_001",
  "workflow": "kai-sdr-operator",
  "package_id": "pkg_acme",
  "mode": "b2b_sdr_engine",
  "started_at": "2026-05-27T00:00:00Z",
  "ended_at": null,
  "actor": "codex",
  "inputs": [],
  "outputs": [],
  "status": "running",
  "blocked_reason": null
}
```

## Action Record

```json
{
  "action_id": "act_001",
  "run_id": "run_001",
  "action_type": "dry_run",
  "system": "hubspot",
  "entity_count": 12,
  "dry_run_path": "workspace/sdr-operator/acme/dry-runs/act_001.json",
  "approval_id": null,
  "status": "dry_run_complete"
}
```

## Alert Rules

Create an alert or daily briefing note when:

- Any opt-out, complaint, or bounce appears.
- Send cap would be exceeded.
- Connector failure rate exceeds 5% in a run.
- More than 10% of rows are blocked for source or suppression gaps.
- A meeting is booked without meeting prep.
- A follow-up is due within 24 hours.
- Evidence expires before the planned send date.
- A CRM dry run would create duplicates.

## Run Closeout

Every run closeout should state:

- Inputs used.
- Actions proposed.
- Actions approved.
- Actions blocked.
- Sources added.
- Gaps added.
- Replies processed.
- Meetings prepared.
- Memory candidates created.
- Learnings promoted or held.
