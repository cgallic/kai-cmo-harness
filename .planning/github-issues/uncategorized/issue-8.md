---
issue: 8
title: "Add HALO-style trace optimization loop to CMO harness"
state: OPEN
labels: []
assignees: []
created: 2026-05-02T23:36:09Z
updated: 2026-05-02T23:36:09Z
author: cgallic
url: https://github.com/cgallic/kai-cmo-harness/issues/8
comments_count: 0
reactions_count: 0
---

# #8: Add HALO-style trace optimization loop to CMO harness

## Description

## Context

The CMO harness is a strong candidate for HALO-style harness optimization: it already has repeatable scheduled tasks, task execution records, retries, client-specific business ops, and notification paths. What it lacks is span-level tracing rich enough to diagnose recurring failures, low-signal outputs, weak prompts, brittle tool boundaries, and noisy alerts.

Current local implementation inspected in `/opt/cmo-agent`:

- `agent/loop.py` — scheduler/execution loop, retries, notifications
- `agent/models.py` — `ScheduledTask`, `TaskExecution`, SQLite storage
- task handlers for daily analytics, weekly reports, content pipeline, SEO, lead outreach, ad management, KaiCalls/ABP/BuildWithKai ops
- execution DB currently captures mostly `task_id`, `status`, timestamps, `result`, `error`, and `retry_count`

That is enough for uptime, but not enough for trace-based harness improvement.

## Goal

Turn the CMO harness into a trace-producing marketing ops agent that can be analyzed by HALO or a similar trace-diagnosis loop.

Long-term target:

> The CMO agent learns which signals are actually useful, then improves its prompts, task inputs, alert thresholds, and reporting structure based on production trace outcomes.

## Proposed work

### 1. Add structured span-level tracing

Wrap every scheduled task execution with trace/span capture:

```json
{
  "trace_id": "...",
  "task_id": "weekly_report",
  "client": "kaicalls",
  "span": "fetch_metrics",
  "status": "ok",
  "duration_ms": 842,
  "inputs": {},
  "outputs_summary": "...",
  "error": null
}
```

Recommended spans:

- scheduler decision
- task start/end
- external API fetches
- LLM prompt/model/output/token usage
- data transformation
- recommendation synthesis
- notification delivery
- timeout/failure/retry

### 2. Add a trace store/exporter

Add either a SQLite `task_spans` table or JSONL writer, plus an export command:

```bash
python -m agent.traces.export --since 7d > traces/cmo_traces.jsonl
```

### 3. Run HALO-style diagnosis on real failures

Example prompts:

```bash
halo traces/cmo_traces.jsonl \
  -p "Find recurring task failures, weak prompt/tool boundaries, missing context, notification spam, and scheduler issues. Suggest concrete harness changes."
```

```bash
halo traces/cmo_traces.jsonl \
  -p "Analyze why weekly business reports are low-signal. Identify missing inputs, bad aggregation, weak synthesis, and notification formatting problems."
```

### 4. Add result-quality labels

Capture downstream usefulness signals where available:

- `sent`
- `ignored`
- `useful`
- `noisy`
- `wrong`
- `action_taken`

This lets the harness optimize for business usefulness, not just successful execution.

### 5. Schedule recurring harness review

Run a weekly trace diagnosis over the last 7 days and create/apply concrete harness improvement tasks.

## Expected early improvements

Likely issues this will surface:

- reports are too cron-output-like instead of CMO/executive-grade
- task failures lack enough context to self-debug
- tasks do not distinguish no-data vs API failure vs real business anomaly
- notification routing is blunt/noisy
- retries do not modify context or strategy
- no scoring loop for report usefulness
- Connor feedback/reactions are not incorporated into future output quality

## Acceptance criteria

- [ ] Task executions produce structured trace spans
- [ ] LLM calls capture prompt name/version, model, token usage, and summarized output
- [ ] External calls capture endpoint/service, duration, status, and redacted error details
- [ ] Trace export produces HALO-compatible JSONL
- [ ] Weekly trace diagnosis can run on the last 7 days of executions
- [ ] Diagnosis output includes actionable harness changes, not just summaries
- [ ] Sensitive values are redacted before storage/export
