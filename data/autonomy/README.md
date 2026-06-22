# Autonomy ledger

This folder holds `ledger.jsonl`, the append-only record of every autonomy run
(GitHub issue #27). The file is runtime data and is gitignored; only this README
is tracked so the location stays discoverable.

## What writes here

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

## Controls

- `KAI_AUTONOMY_LEDGER=0` disables writes.
- `KAI_AUTONOMY_DIR=/some/path` redirects the ledger location.
