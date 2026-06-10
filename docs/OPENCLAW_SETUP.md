# OpenClaw Autonomous CMO — Setup

This guide turns the harness from an interactive Claude Code toolkit into an autonomous agent: scheduled heartbeats, Discord/WhatsApp command channels, domain task routing, and human-in-the-loop approval before anything publishes.

Everything here maps to code in `agent/` — if this doc and the code disagree, the code wins; file the discrepancy in `memory/edge-cases.md`.

## Prerequisites

- A server (or always-on machine) with Python 3.11+
- This repo cloned, with `python scripts/doctor.py` passing
- An Anthropic API key (agent reasoning)
- A Discord bot token + channel, or Twilio WhatsApp credentials (command + approval channel)
- Optional: Gemini key (content gates/writing), Google credentials (GSC/GA4 performance loop)

## 1. Configure environment

The agent loads `.env` from the repo root and `scripts/.env` (see `agent/config.py`). Set:

```bash
# Required — reasoning
ANTHROPIC_API_KEY=sk-ant-...

# Channels (enable at least one)
DISCORD_BOT_TOKEN=...
DISCORD_CHANNEL_ID=...            # default channel for notifications/approvals
AGENT_DISCORD_ENABLED=true

TWILIO_ACCOUNT_SID=...            # WhatsApp channel (optional)
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=+1...
AGENT_OWNER_PHONE=+1...           # where approvals/alerts go
AGENT_WHATSAPP_ENABLED=false

# Content pipeline (optional but recommended)
GEMINI_API_KEY=...                # draft writing + Four U's judge (the judge also
                                  # accepts ANTHROPIC_API_KEY or OPENAI_API_KEY;
                                  # pin with KAI_LLM_PROVIDER / KAI_LLM_MODEL)
GOOGLE_CREDENTIALS_PATH=...       # GSC/GA4 for briefs + 30-day checks

# Behavior tuning (defaults shown)
AGENT_POLLING_INTERVAL=60         # seconds between scheduler checks
AGENT_MAX_CONCURRENT_TASKS=3
AGENT_TASK_TIMEOUT=300
AGENT_RETRY_ATTEMPTS=3
AGENT_RETRY_DELAY=60
AGENT_SCHEDULER_ENABLED=true
AGENT_NOTIFY_ON_FAILURE=true
AGENT_NOTIFY_ON_APPROVAL=true
AGENT_DAILY_SUMMARY=true

# Model routing (defaults in agent/config.py)
AGENT_DEFAULT_MODEL=claude-3-5-haiku-20241022
AGENT_OPUS_MODEL=claude-opus-4-5-20251101
```

## 2. Prepare the workspace files

The agent reads its operating identity from `workspace/`:

| File | Role |
|------|------|
| `workspace/MARKETING.md` | Operating config: sites, formats, thresholds (auto-updated by the learning loop) |
| `workspace/AGENTS.md` | Domain agent definitions and routing |
| `workspace/HEARTBEAT.md` | Heartbeat rules — what to check on each scheduled wake |
| `workspace/IDENTITY.md`, `workspace/SOUL.md` | Brand identity and voice |
| `workspace/TOOLS.md` | Tool/connector availability |

Run `/kai-start` in Claude Code first if `MARKETING.md` doesn't exist yet.

## 3. Initialize and inspect the schedule

```bash
python -m agent.loop --init-tasks       # create default scheduled tasks (one-time)
python -m agent.loop --test-schedule    # list upcoming tasks + cron expressions, then exit
```

State persists in `agent/agent.db` (SQLite, gitignored). Default task types live in `agent/tasks/` — content pipeline, daily analytics, connector health, SEO optimization, social staleness, weekly report, lead outreach, ad management, and `execute_approved` (runs only after human approval).

The self-improvement crons from `harness/ARCHITECTURE.md` ride along:

- `0 2 * * *` — `performance_check.py` (30-day GSC/GA4 pull, winner/loser grading)
- `0 14 * * 1` — `pattern_extract.py` (winner pattern mining → `what-works.md`)
- `30 14 * * 1` — `harness_defaults_update.py` (threshold/defaults update, with `.bak` backups)

## 4. Run the loop

```bash
python -m agent.loop
```

For production, wrap it in a process manager:

```ini
# /etc/systemd/system/kai-agent.service
[Unit]
Description=Kai Autonomous CMO
After=network.target

[Service]
WorkingDirectory=/opt/kai-cmo-harness
ExecStart=/usr/bin/python3 -m agent.loop
Restart=on-failure
RestartSec=30
EnvironmentFile=/opt/kai-cmo-harness/.env

[Install]
WantedBy=multi-user.target
```

## 5. Approval flow

Nothing publishes without approval. Content that passes the quality gates posts to Discord (or WhatsApp) for a human reaction; `agent/tasks/execute_approved.py` executes only approved items. Gate double-failures and `risk_tier=high` items can never auto-approve — they escalate with the specific failure list.

## 6. Wire in the learning loop

The autonomous mode generates the data the learning loop feeds on:

- Gate runs append to `data/learning/gate_runs.jsonl` automatically.
- Schedule a monthly `/kai-retro` (or run it manually after sprints) to mine failures, diagnose losers, and graduate lessons. See `docs/system/learning-loop.md`.
- Watch `memory/edge-cases.md` EC-11/EC-12/EC-13 — the known sharp edges of long-running autonomous deployments (defaults rewrite validation, pending-check loss, circuit-breaker resets).

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Loop starts, no tasks fire | Tasks never initialized | `python -m agent.loop --init-tasks` |
| No Discord messages | Token/channel unset or `AGENT_DISCORD_ENABLED=false` | check `.env`, re-run `python scripts/doctor.py` |
| Four U's gate crashes | `GEMINI_API_KEY` missing | set it, or rely on the offline gates (banned words, SEO lint) |
| Performance checks return errors | Google credentials missing | set `GOOGLE_CREDENTIALS_PATH`; missing data is a data gap, never a zero |
| Repeated Gemini failures after restart | Circuit breaker is in-memory (EC-13) | investigate the API failure before restarting again |
