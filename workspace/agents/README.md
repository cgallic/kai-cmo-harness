# Agent Hierarchy

Three-tier architecture for Kai-CMO.

## Tiers

```
TIER 1: ORCHESTRATOR (main Kai-CMO session)
  └── Routes Discord messages, spawns domain agents, aggregates results

TIER 2: DOMAIN AGENTS (spawned in parallel on each heartbeat)
  ├── kaicalls-agent     →  #kai-calls
  ├── abp-agent          →  #awesome-backyard-parties
  ├── bwk-agent          →  #build-with-kai
  ├── finance-agent      →  #finance
  ├── infra-agent        →  #health
  ├── gate-agent         →  #zehrava
  └── research-agent     →  #research, #ai

TIER 3: SKILLS (procedural guides loaded into orchestrator context only)
  └── dev-workflow, kaicalls-outbound, abp-vendor-match, marketing-knowledge, patent-scanner
```

## How Heartbeat Works

1. Heartbeat fires → orchestrator reads HEARTBEAT.md
2. Reads each agent file in `/agents/` as task string
3. Spawns all domain agents in parallel via `sessions_spawn`
4. Calls `sessions_yield()` to receive results
5. Routes non-empty alerts to correct Discord channels
6. Posts aggregate to #updates if anything notable

## How to Spawn a Domain Agent

```
sessions_spawn(
  task=<contents of agents/<name>-agent.md>,
  label="heartbeat-<name>",
  mode="run",
  runtime="subagent",
  cleanup="keep"
)
```

## Adding a New Domain Agent

1. Create `/root/.openclaw/workspace/agents/<name>-agent.md`
2. Include: data to pull, checks to run, dedup rules, output format
3. Add channel mapping to AGENTS.md
4. Add spawn call to HEARTBEAT.md

## Rules

- Each agent gets ONLY its domain context. No cross-contamination.
- Agents post directly to their channel if alert is clear-cut.
- Ambiguous cross-product signals → return to orchestrator to decide.
- All dedup happens inside the agent, not in the orchestrator.
- Agents return structured output: `{ "alerted": bool, "channel": id, "summary": string }`
