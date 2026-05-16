# HALO-Style Trace Optimization

## Goal

The autonomous CMO agent now emits structured task spans so failed, slow, noisy, or low-signal runs can be reviewed as traces.

The trace loop is:

```
scheduled task -> spans -> JSONL export -> diagnosis -> harness changes
```

## What Gets Captured

| Span | Captures |
|------|----------|
| `scheduler.decision` | task chosen for execution, task type, next run time |
| `task.handler.resolve` | task handler class |
| `task.execute` | timeout, handler, summarized result |
| `task.complete` | completed output summary |
| `task.timeout` | timeout boundary |
| `task.failure` | redacted error |
| `task.retry_decision` | retry limit, current count, decision |
| `notification.delivery` | channel, service, delivery result |
| `llm.complete` / `llm.chat` | model, prompt name, prompt version, token usage, output summary |

Sensitive fields are redacted before storage and export. Tokens, authorization headers, cookies, emails, phone numbers, and URL token parameters are not written in plain text.

## Storage

HALO spans are stored in SQLite in the existing `task_spans` table. The lightweight recorder used by `agent.traces.recorder` stores compatibility spans in `task_span_records` to avoid colliding with the HALO schema.

Key fields:

- `trace_id`
- `execution_id`
- `task_id`
- `client`
- `span`
- `status`
- `duration_ms`
- `inputs`
- `outputs_summary`
- `error`
- `metadata`

## Export

Export the last 7 days as JSONL:

```bash
python -m agent.traces.export --since 7d > traces/cmo_traces.jsonl
```

Useful filters:

```bash
python -m agent.traces.export --since 24h --status error
python -m agent.traces.export --since 7d --task-id weekly_report
python -m agent.traces.export --trace-id trace_abc123
```

Each line is a JSON object with `trace_id`, `span_id`, `task_id`, `span`, `status`, `duration_ms`, `inputs`, `outputs_summary`, `error`, and `metadata`.

## Weekly Diagnosis

Run the built-in heuristic review:

```bash
python -m agent.traces.diagnose --since 7d
```

The diagnosis looks for:

- recurring task failures
- broad or slow boundaries
- LLM spans without prompt name/version
- noisy notification paths
- missing usefulness labels

Use the output as the weekly harness improvement queue.

## Prompt Metadata

Pass prompt metadata to LLM calls:

```python
await llm_router.complete(
    prompt,
    task_type="weekly_report",
    prompt_name="weekly_report",
    prompt_version="v1",
)
```

The router records provider, model, token usage, prompt name, prompt version, and a redacted output summary.

## Next Useful Label Loop

After a task completes, downstream systems should label usefulness when available:

- `sent`
- `ignored`
- `useful`
- `noisy`
- `wrong`
- `action_taken`

Those labels should live on task outputs or action records, then get pulled into diagnosis so optimization targets business usefulness instead of mere uptime.
