# Autonomy data

This folder holds the runtime files behind the Kai autonomy control layer
(GitHub issue #27). The files are runtime data and are gitignored; only this
README is tracked so the location stays discoverable.

- `ledger.jsonl` — append-only record of every autonomy run.
- `approval_queue.jsonl` — append-only queue of risky actions waiting on a human.

Both honor `KAI_AUTONOMY_DIR` to redirect their location.

## The ledger (`ledger.jsonl`)

`scripts/autonomy/ledger.py` appends one JSON object per automation run. The
social platform monitor (`scripts.social.platform_change_monitor`) is the first
converted automation. Each record carries:

`run_id`, `workflow`, `started_at`, `finished_at`, `inputs`, `sources_checked`,
`findings`, `actions_taken`, `files_changed`, `validation`, `risk_level`,
`requires_human`, `blockers`, `lessons`, `followups`.

Every finding inside a record carries an explicit `decision` (one of
`auto_fix`, `auto_pr`, `stage_for_approval`, `escalate`, `block`) and a
`risk_level`, set by `scripts/autonomy/decisions.py`.

## Reading it

```python
from scripts.autonomy.ledger import read_records, mine_repeated_lessons

records = read_records()
repeated = mine_repeated_lessons(records, min_count=2)  # promotion candidates
```

## The approval queue (`approval_queue.jsonl`)

`scripts/autonomy/approval_queue.py` is the one canonical hold for risky actions
(outbound email, client claims, live publish, paid media, account/credential
changes, deploys). When `route_decision` routes a finding to
`stage_for_approval`, `stage_findings(...)` lands it here instead of acting.

The queue is an append-only **event log** folded into current state on read, so
it doubles as an audit trail (queued → validated → resolved). Unlike the ledger,
`enqueue` raises on persistence failure and there is no disable switch —
silently dropping a staged action would be a safety regression.

```python
from scripts.autonomy.approval_queue import list_pending, approve, reject

for item in list_pending():           # risky actions awaiting a human
    print(item["action_kind"], item["risk_level"])
approve(item_id, resolved_by="connor", resolution_note="ok")
```

## The operator brief

`python -m scripts.autonomy.operator_brief [--since N] [--out PATH]` reads the
ledger and approval queue and renders a decision-oriented weekly brief (biggest
risks, approvals needed, failed automations, stale/broken sources, recurring
lessons to promote). It only restates ledger/queue facts — it invents nothing.

## Controls

- `KAI_AUTONOMY_LEDGER=0` disables ledger writes (the approval queue has no
  equivalent switch by design).
- `KAI_AUTONOMY_DIR=/some/path` redirects both the ledger and the queue.
