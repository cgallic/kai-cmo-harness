# Heartbeat

On every heartbeat: fan out to domain agents in parallel, yield for results, route alerts.

---

## Protocol

### Step 1 — Spawn All Domain Agents in Parallel

Read each agent file, spawn as subagent with that file's content as the task.
All spawns happen before any yield.

```
sessions_spawn(task=<agents/kaicalls-agent.md contents>, label="hb-kaicalls", mode="run", runtime="subagent")
sessions_spawn(task=<agents/abp-agent.md contents>,      label="hb-abp",      mode="run", runtime="subagent")
sessions_spawn(task=<agents/finance-agent.md contents>,  label="hb-finance",  mode="run", runtime="subagent")
sessions_spawn(task=<agents/gate-agent.md contents>,     label="hb-gate",     mode="run", runtime="subagent")
sessions_spawn(task=<agents/bwk-agent.md contents>,      label="hb-bwk",      mode="run", runtime="subagent")
sessions_spawn(task=<agents/infra-agent.md contents>,    label="hb-infra",    mode="run", runtime="subagent")
```

Research agent spawns on its own cron (daily 8am ET) — skip at routine heartbeat intervals.

### Step 2 — Yield

```
sessions_yield()
```

Wait for all domain agents to complete and push results back.

### Step 3 — Route Results

Each agent returns either `NOTHING` or an alert string.
- `NOTHING` → no action needed from orchestrator
- Alert string → agent already posted to its channel; orchestrator logs it
- Multiple alerts → post aggregate to #updates if more than 2 products flagged

### Step 4 — Proactive Memory Scan (every heartbeat, script self-throttles to 6h)

```bash
cd /opt/cmo-analytics && source venv/bin/activate
python3 scripts/proactive_heartbeat.py --json --force
```

Read `/tmp/proactive_heartbeat_signals.json`. For each signal, post `message` field to `channel_id`.

### Step 5 — Acknowledge

If no alerts from any agent and memory scan is clean: reply `HEARTBEAT_OK`

---

## Domain Agent → Channel Map

| Agent | File | Discord Channel | Channel ID |
|-------|------|----------------|-----------|
| KaiCalls | agents/kaicalls-agent.md | #kai-calls | 1469307381103198382 |
| ABP | agents/abp-agent.md | #awesome-backyard-parties | 1469310748290191441 |
| Finance | agents/finance-agent.md | #finance | 1469310816158482603 |
| Gate | agents/gate-agent.md | #zehrava | 1480049743530037308 |
| BWK | agents/bwk-agent.md | #build-with-kai | 1469307544454566020 |
| Infra | agents/infra-agent.md | #health | 1469310837469610216 |
| Research | agents/research-agent.md | #research, #ai | 1472596453527654475, 1472908303267926087 |

---

## Daily-Only Checks (8am ET heartbeat only)

Run these only when the heartbeat fires at ~8am ET. Skip at all other intervals.

### Blog Post
1. Check #research (channel 1472596453527654475) for unwritten papers/links since yesterday
2. If found → write blog post → publish to `/var/www/meetkai/blog/` → update index → post to #meet-kai
3. If nothing → check `/opt/meetkai-data/content-calendar.md` → pick first unchecked Tier 1 item
4. Never write a post marked `[done]` in the calendar

### Reddit Monitor
Automated via cron — skip manual check. Log: `/var/log/reddit-monitor.log`

---

## Event-Driven Triggers (no heartbeat needed)

These fire independently via webhooks:

| Trigger | Agent | Action |
|---------|-------|--------|
| New KaiCalls lead (webhook) | kaicalls-agent | Outreach queue |
| New ABP form submission | abp-agent | Vendor match + Gate proposal |
| Stripe webhook (charge failed) | finance-agent | At-risk alert |
| Gate webhook (intent created) | gate-agent | Post to #zehrava |
| #research message with attachment | research-agent | Ingest + summarize |

---

## What Was Removed

The following were serial checks in the old HEARTBEAT.md. They now live in domain agents:
- Email campaign replies (kaicalls-agent step 2)
- At-risk revenue (finance-agent)
- KaiCalls leads (kaicalls-agent step 1)
- KaiCalls lead outreach (kaicalls-agent step 2)
- Hot lead follow-up (kaicalls-agent step 3)
- ABP leads (abp-agent)
- ABP widget/phone leads (abp-agent step 1)
- ABP lead auto-match (abp-agent steps 3–4)
- BWK activity (bwk-agent)
- Traffic anomalies → moved to daily digest (research-agent)
- Gate health (gate-agent)
- Proactive memory scan (step 4 above, still orchestrator-level)
