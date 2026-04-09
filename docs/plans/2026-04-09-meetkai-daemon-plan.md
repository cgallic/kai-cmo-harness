# MeetKai Daemon — Implementation Plan

**Date**: 2026-04-09
**Status**: Draft v3 — SDK + OAuth + review fixes. Ready to build.

## Review Notes (2 independent agents)

### MUST-FIX before implementation

1. **Extend `agent/loop.py`, don't build a parallel daemon.** The `agent/` module already has `AgentLoop` (polling, scheduling, concurrency, retries, signal handling), `CronParser`, 10+ task handlers including `execute_approved.py`, and `kai/execution/executor.py` with full `ActionExecutor`. Add Claude Code subprocess spawning as a NEW task type under `agent/tasks/`, not a replacement executor.

2. **Reuse existing gateway routers.** `/agent/*` (13 endpoints) and `/runtime/*` (14 endpoints) already exist. Add 3-4 new endpoints to `/agent` router: `POST /agent/register-runtime`, `PATCH /agent/heartbeat`, `POST /agent/tasks/{id}/messages`. Don't create a separate `/daemon/*` router.

3. **Fix claim lock atomicity.** Supabase REST `is_("claimed_at", "null")` is NOT `SELECT ... FOR UPDATE`. Two agents can race. Use a Postgres function with `FOR UPDATE SKIP LOCKED` or advisory lock.

4. **Use Supabase `service_role` key.** RLS policies on `agent_runs` check `auth.uid()`. Daemon authenticates via API key, not as a Supabase user. Gateway writes must use `service_role` key.

5. **Fix semaphore in poller.** `async with semaphore: asyncio.create_task(...)` acquires then immediately releases. Semaphore must be acquired INSIDE the task coroutine.

6. **Fix Claude Code CLI flags.** Use `-p` not `--prompt`. Verify `CLAUDE_AUTO_APPROVE` env var name (may need `--dangerously-skip-permissions`).

### SHOULD-FIX

7. Add stale-daemon reaper (tasks claimed by dead runtimes → re-queue or fail).
8. Add retry logic (existing `agent/config.py` has `retry_attempts=3`).
9. Use `asyncio.gather` to read stdout + stderr concurrently (prevent deadlock).
10. Use `uuid_generate_v4()` to match existing migrations (not `gen_random_uuid()`).
11. Keep `ActionExecutor` for connector-backed actions. Use Claude Code only for content/analysis tasks.

### MVP SCOPE REDUCTION

- **Phase 1** (schema): Keep, but use `uuid_generate_v4()` and add claim lock function.
- **Phase 2** (gateway): Reduce from 10 new endpoints to 3-4, added to existing `/agent` router.
- **Phase 3** (daemon): Evolve `agent/loop.py`, add Claude Code task type under `agent/tasks/`.
- **Phase 4** (dashboard): CUT from MVP — prove daemon works first.
- **Phase 5** (integration): CUT from MVP — existing execution flow continues working.
- **Add**: systemd unit file, log rotation policy, resource limits.
- **Add**: Write `agent_messages` directly to Supabase (not through gateway) for streaming performance.

### Critical Existing Files to Integrate With
- `agent/loop.py` — existing AgentLoop (polling, scheduling, concurrency)
- `agent/scheduler.py` — existing CronParser and task scheduling
- `agent/tasks/execute_approved.py` — existing approved action execution
- `agent/config.py` — existing retry/concurrency config
- `kai/execution/executor.py` — existing ActionExecutor with dispatch tables
- `gateway/routers/agent.py` — existing agent API (13 endpoints)
- `gateway/routers/runtime.py` — existing runtime API (14 endpoints)

---

## Context

The Kai CMO Harness at `E:\Dev2\kai-cmo-harness-work` is a production marketing automation platform with:
- **Next.js dashboard** (`app-meetkai/`) with real-time Supabase subscriptions
- **FastAPI gateway** (`gateway/`) with SQLite job queue (ThreadPoolExecutor, max 4 workers)
- **184 Python modules** (`kai/`) — 8 audit engines, proposal ranking, compliance, connectors
- **39 Claude Code skills** (`harness/skills/`)
- **168 knowledge files** (`knowledge/`)
- **Supabase DB** with `agent_runs` table already wired for realtime updates

**The gap**: Everything runs manually (user triggers audit → approves actions → executes). No autonomous execution. The daemon bridges this gap — it's the engine that claims approved tasks, spawns Claude Code with the right skills, streams progress to the dashboard, and runs on a schedule.

**Inspiration**: Multica's daemon patterns — optimistic claim lock, heartbeat, log streaming, skill injection, session resumption.

---

## Claude Agent SDK (Official Anthropic Package)

The daemon MUST use the **Claude Agent SDK** — Anthropic's official package for spawning and managing Claude Code agents programmatically. This replaces raw subprocess spawning.

### Installation

```bash
pip install claude-agent-sdk
```

**Package**: `claude-agent-sdk` v0.1.13+ on PyPI (renamed from `claude-code-sdk`)
**GitHub**: `github.com/anthropics/claude-agent-sdk-python`
**Auth**: Claude Code OAuth (run `claude setup-token` once on VPS — no API key needed)

### Core API

```python
from claude_agent_sdk import query, ClaudeAgentOptions, ClaudeSDKClient

# One-shot execution (daemon task pattern)
async for message in query(
    prompt="Run SEO audit on https://example.com",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"],
        permission_mode="acceptEdits",    # Auto-approve file ops, deny dangerous ops
        max_turns=20,                     # Prevent infinite loops
        max_budget_usd=5.0,              # Cost cap per task
        cwd="/path/to/workdir",          # Isolated workdir with skills injected
        model="claude-sonnet-4-6",
    ),
):
    # Typed message objects — no JSON parsing needed
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                await stream_text(block.text)
            elif isinstance(block, ToolUseBlock):
                await stream_tool_use(block.name, block.input)
            elif isinstance(block, ThinkingBlock):
                await stream_thinking(block.thinking)
    elif isinstance(message, ResultMessage):
        session_id = message.session_id      # For resumption
        cost = message.total_cost_usd        # Actual cost
        turns = message.num_turns
        result = message.result              # Final text output
```

### Multi-Turn with Session Resumption

```python
# First task — capture session_id
async for msg in query(prompt="Audit the site", options=opts):
    if isinstance(msg, ResultMessage):
        session_id = msg.session_id

# Resume later (same session context preserved)
async for msg in query(
    prompt="Now fix the issues you found",
    options=ClaudeAgentOptions(resume=session_id, ...)
):
    ...
```

### Permission Modes (for daemon/headless)

| Mode | Use Case |
|------|----------|
| `acceptEdits` | Auto-approve file ops, ask for other actions (RECOMMENDED for daemon) |
| `dontAsk` | Deny anything not in `allowed_tools` (safest) |
| `bypassPermissions` | No checks at all (sandboxed environments only) |

### Message Types Yielded by `query()`

| Type | Contains |
|------|----------|
| `SystemMessage` (subtype "init") | `session_id`, available tools, model |
| `AssistantMessage` | `content: [TextBlock, ToolUseBlock, ThinkingBlock]` |
| `UserMessage` | Tool results |
| `ResultMessage` | `result`, `session_id`, `total_cost_usd`, `duration_ms`, `num_turns`, `stop_reason` |
| `StreamEvent` | Raw API events (with `include_partial_messages=True`) |
| `RateLimitEvent` | Rate limit info (SDK auto-retries) |

### ResultMessage Stop Reasons

| `stop_reason` | Meaning |
|---|---|
| `success` | Normal completion |
| `error_max_turns` | Hit turn limit |
| `error_max_budget_usd` | Hit cost cap |
| `error_during_execution` | Runtime error |

### Key Options

| Option | Type | Purpose |
|---|---|---|
| `allowed_tools` | `list[str]` | Pre-approved tools |
| `disallowed_tools` | `list[str]` | Always blocked |
| `permission_mode` | `str` | Permission handling |
| `max_turns` | `int` | Turn limit |
| `max_budget_usd` | `float` | Cost cap |
| `model` | `str` | Model name or alias (sonnet, opus, haiku) |
| `cwd` | `str/Path` | Working directory |
| `env` | `dict` | Environment variables |
| `resume` | `str` | Session ID to resume |
| `system_prompt` | `str` | Custom system prompt |
| `append_system_prompt` | `str` | Append to default prompt |
| `thinking` | `dict` | `{"type": "adaptive"}` for extended thinking |
| `effort` | `str` | `low/medium/high/max` |
| `hooks` | `dict` | Lifecycle hooks |
| `agents` | `dict` | Inline subagent definitions |
| `mcp_servers` | `dict` | MCP server configs |
| `persist_session` | `bool` | Save session to disk |

### Hosting Pattern (Anthropic-recommended for daemons)

- **Long-Running Sessions**: Persistent process running multiple Claude Agent queries
- System requirements: Python 3.10+, ~1 GiB RAM, ~5 GiB disk, 1 CPU, outbound HTTPS
- Use `max_turns` to prevent infinite loops (agent sessions do NOT timeout on their own)
- Use `max_budget_usd` for cost control

---

## What We're Building

A Python daemon (`daemon/`) that runs on the VPS and:

1. **Detects** Claude Code CLI on PATH
2. **Registers** itself as a runtime with the gateway
3. **Heartbeats** every 15s to stay alive
4. **Polls** for claimable tasks (approved actions, scheduled jobs) every 3s
5. **Claims** tasks with optimistic locking (exactly-once execution)
6. **Injects** correct Kai skills + knowledge into a workdir
7. **Spawns** Claude Code subprocess with the task prompt
8. **Streams** stdout/stderr as `agent_messages` to Supabase (dashboard sees live progress)
9. **Completes** tasks — updates `agent_runs`, stores artifacts, optionally creates skills
10. **Schedules** recurring tasks via cron expressions

---

## Architecture

```
┌─────────────────────────────────────────────┐
│        app-meetkai Dashboard (Next.js)       │
│  useAgentRuns() ← Supabase Realtime          │
│  useAgentMessages() ← NEW realtime hook      │
│  Agent Panel: live progress, tool use, logs  │
└──────────────────┬──────────────────────────┘
                   │ Supabase Realtime (WS)
┌──────────────────▼──────────────────────────┐
│              Supabase (PostgreSQL)            │
│  agent_runs     — task lifecycle              │
│  agent_messages — execution transcript  NEW   │
│  runtimes       — registered daemons    NEW   │
│  schedules      — cron definitions      NEW   │
│  actions        — approval workflow (existing)│
└──────────────────┬──────────────────────────┘
                   │ HTTP (X-API-Key auth)
┌──────────────────▼──────────────────────────┐
│          gateway (FastAPI) — EXTENDED         │
│  POST /daemon/register                       │
│  PATCH /daemon/heartbeat                     │
│  POST /daemon/tasks/claim                    │
│  POST /daemon/tasks/{id}/start               │
│  POST /daemon/tasks/{id}/progress            │
│  POST /daemon/tasks/{id}/messages            │
│  POST /daemon/tasks/{id}/complete            │
│  POST /daemon/tasks/{id}/fail                │
│  GET  /daemon/schedules/pending              │
│  POST /daemon/schedules/{id}/triggered       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          MeetKai Daemon (Python, VPS)        │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Heartbeat │  │Poller    │  │Scheduler │  │
│  │(15s loop)│  │(3s loop) │  │(cron)    │  │
│  └──────────┘  └────┬─────┘  └────┬─────┘  │
│                     │              │         │
│                ┌────▼──────────────▼────┐    │
│                │    Task Executor       │    │
│                │  claim → inject skills │    │
│                │  → spawn claude        │    │
│                │  → stream logs         │    │
│                │  → complete/fail       │    │
│                └────────────────────────┘    │
└──────────────────┬──────────────────────────┘
                   │ subprocess
         ┌─────────▼──────────┐
         │  Claude Code CLI    │
         │  + .claude/skills/  │
         │  + knowledge/       │
         │  + task context     │
         └────────────────────┘
```

---

## Implementation

### Phase 1: Database Schema (Supabase)

**New file: `app-meetkai/supabase/migrations/005_daemon.sql`**

```sql
-- Runtimes: registered daemon instances
CREATE TABLE runtimes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  daemon_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  host_info JSONB DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'offline',
  last_heartbeat TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent messages: execution transcript (streamed in realtime)
CREATE TABLE agent_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
  brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
  seq INTEGER NOT NULL,
  msg_type TEXT NOT NULL,
  content TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_messages_run ON agent_messages(run_id, seq);

-- Schedules: recurring task definitions
CREATE TABLE schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  cron_expr TEXT NOT NULL,
  skill TEXT NOT NULL,
  task_type TEXT NOT NULL,
  input JSONB DEFAULT '{}',
  enabled BOOLEAN DEFAULT true,
  last_run_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Extend agent_runs with daemon fields
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS runtime_id UUID REFERENCES runtimes(id);
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS session_id TEXT;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS work_dir TEXT;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS schedule_id UUID REFERENCES schedules(id);
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS progress JSONB DEFAULT '{}';

-- Enable realtime for new tables
ALTER PUBLICATION supabase_realtime ADD TABLE agent_messages;
ALTER PUBLICATION supabase_realtime ADD TABLE runtimes;
ALTER PUBLICATION supabase_realtime ADD TABLE schedules;
```

---

### Phase 2: Gateway API Endpoints

**New file: `gateway/routers/daemon.py`**

| Endpoint | Method | Purpose |
|---|---|---|
| `/daemon/register` | POST | Register runtime (daemon_id, name, host_info, capabilities) → returns runtime_id |
| `/daemon/heartbeat` | PATCH | Update last_heartbeat, check for pending commands (drain, shutdown) |
| `/daemon/tasks/claim` | POST | Atomically claim next available task. Query: `agent_runs WHERE status='pending' AND claimed_at IS NULL ORDER BY created_at LIMIT 1` — set `runtime_id`, `claimed_at`, `status='running'` |
| `/daemon/tasks/{id}/start` | POST | Mark task as actively executing (`started_at = now()`) |
| `/daemon/tasks/{id}/progress` | POST | Update `progress` JSONB field (`{step, total, summary}`) |
| `/daemon/tasks/{id}/messages` | POST | Batch insert `agent_messages` rows |
| `/daemon/tasks/{id}/complete` | POST | Set `status='completed'`, `completed_at`, `output`, `session_id`, `work_dir` |
| `/daemon/tasks/{id}/fail` | POST | Set `status='failed'`, `error`, `completed_at` |
| `/daemon/schedules/pending` | GET | Return schedules where `next_run_at <= now() AND enabled = true` |
| `/daemon/schedules/{id}/triggered` | POST | Update `last_run_at`, compute `next_run_at`, create `agent_runs` row |

**Claim lock implementation** (exactly-once):
```python
result = supabase.table("agent_runs") \
    .update({"runtime_id": runtime_id, "claimed_at": "now()", "status": "running"}) \
    .eq("id", task_id) \
    .is_("claimed_at", "null") \
    .execute()
```

**Mount in `gateway/main.py`:**
```python
from gateway.routers.daemon import router as daemon_router
app.include_router(daemon_router, prefix="/daemon", dependencies=[Depends(verify_api_key)])
```

---

### Phase 3: The Daemon

**New directory: `daemon/`**

```
daemon/
├── __init__.py
├── __main__.py          # Entry point: python -m daemon start
├── config.py            # Configuration (env vars, defaults)
├── client.py            # HTTP client for gateway API
├── detector.py          # CLI detection (claude on PATH)
├── executor.py          # Task execution (spawn claude, stream output)
├── injector.py          # Skill + knowledge injection into workdir
├── poller.py            # Poll loop (claim tasks every 3s)
├── heartbeat.py         # Heartbeat loop (15s)
├── scheduler.py         # Cron schedule checker
├── models.py            # Pydantic models (Task, Runtime, Message)
└── requirements.txt     # claude-agent-sdk, supabase, pydantic, croniter, httpx
```

#### config.py

```python
@dataclass
class DaemonConfig:
    gateway_url: str          # env: MEETKAI_GATEWAY_URL (default: http://localhost:8088)
    gateway_key: str          # env: CMO_GATEWAY_API_KEY
    daemon_id: str            # env: MEETKAI_DAEMON_ID (default: hostname)
    poll_interval: int = 3    # seconds
    heartbeat_interval: int = 15
    max_concurrent: int = 4
    agent_timeout: int = 7200  # 2 hours
    workspaces_root: str      # env: MEETKAI_WORKSPACES_ROOT (default: ~/meetkai_workspaces)
    skills_path: str          # path to harness/skills/
    knowledge_path: str       # path to knowledge/
```

#### detector.py

```python
import shutil
import subprocess

def detect_runtimes() -> list[Runtime]:
    """Detect Claude Code CLI on PATH. SDK requires it installed."""
    runtimes = []
    claude_path = shutil.which("claude")
    if claude_path:
        result = subprocess.run([claude_path, "--version"], capture_output=True, text=True)
        runtimes.append(Runtime(
            name="Claude-Code",
            cmd=claude_path,
            version=result.stdout.strip(),
            capabilities=["content-gen", "audit", "analysis", "code-gen"]
        ))
    # SDK spawns claude CLI as subprocess internally — 
    # we just need to verify it's on PATH
    return runtimes
```

#### injector.py

Before spawning Claude Code, create an isolated workdir:

```
{workspaces_root}/{brand_id}/{run_id_short}/
├── workdir/
│   ├── CLAUDE.md           # Task-specific instructions
│   ├── .claude/skills/     # Relevant Kai skills copied here
│   │   ├── kai-seo-audit/SKILL.md
│   │   └── kai-gate/SKILL.md
│   ├── knowledge/          # Relevant frameworks symlinked
│   │   ├── algorithmic-authorship.md
│   │   └── seo-checklist.md
│   └── context/
│       └── task.md         # Task description, brand info, action details
├── output/
└── logs/
```

**Skill routing** — map task_type → skills to inject:

```python
SKILL_MAP = {
    "audit": ["kai-audit", "kai-seo-audit", "kai-cro"],
    "content": ["kai-write", "kai-brief", "kai-gate"],
    "seo": ["kai-seo-audit", "seo-content-writing", "technical-seo"],
    "ads": ["kai-ad-campaign", "kai-daily-ad-review", "meta-advertising"],
    "email": ["kai-email-system", "kai-newsletter"],
    "social": ["kai-social", "kai-video", "tiktok-marketing"],
    "analytics": ["kai-analytics"],
    "competitors": ["kai-competitors", "kai-surround-sound"],
}
```

#### executor.py (uses Claude Agent SDK)

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import (
    AssistantMessage, ResultMessage, SystemMessage,
    TextBlock, ToolUseBlock, ThinkingBlock
)

# Permission mode per task risk tier
PERMISSION_MODES = {
    "low": "acceptEdits",       # Auto-approve file ops
    "medium": "acceptEdits",    # Auto-approve file ops
    "high": "dontAsk",          # Only pre-approved tools
}

# Tool sets per task type
TOOL_SETS = {
    "audit": ["Read", "Glob", "Grep", "WebFetch", "WebSearch", "Bash"],
    "content": ["Read", "Edit", "Write", "Glob", "Grep", "WebFetch", "WebSearch"],
    "seo": ["Read", "Glob", "Grep", "WebFetch", "WebSearch", "Bash"],
    "ads": ["Read", "Glob", "Grep", "WebFetch"],
    "analytics": ["Read", "Glob", "Grep", "Bash"],
}

async def execute_task(task: AgentTask, config: DaemonConfig, supabase_client):
    """Execute a task using Claude Agent SDK."""

    # 1. Prepare workdir with skills + knowledge
    workdir = injector.prepare_workdir(task, config)

    # 2. Build prompt from task context
    prompt = build_prompt(task)

    # 3. Determine permissions and tools
    tools = TOOL_SETS.get(task.task_type, ["Read", "Glob", "Grep"])
    perm_mode = PERMISSION_MODES.get(task.risk_tier, "dontAsk")

    # 4. Build SDK options
    options = ClaudeAgentOptions(
        allowed_tools=tools,
        permission_mode=perm_mode,
        max_turns=30,
        max_budget_usd=config.max_budget_per_task,  # e.g. $5.00
        cwd=str(workdir),
        model="claude-sonnet-4-6",
        persist_session=True,  # Enable session resumption
        # Resume prior session if this is a continuation
        resume=task.prior_session_id if task.prior_session_id else None,
        # Auth: Claude Code OAuth — no ANTHROPIC_API_KEY needed
        # Run `claude setup-token` once on VPS to generate long-lived token
        # SDK spawns `claude` CLI which uses the stored OAuth token
    )

    # 5. Execute via SDK — stream messages to Supabase
    seq = 0
    session_id = None
    final_result = None
    total_cost = 0.0
    messages_batch = []

    try:
        async for message in query(prompt=prompt, options=options):

            if isinstance(message, SystemMessage) and message.subtype == "init":
                session_id = message.data.get("session_id")

            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        messages_batch.append({
                            "run_id": str(task.id),
                            "brand_id": str(task.brand_id),
                            "seq": seq,
                            "msg_type": "text",
                            "content": block.text,
                            "metadata": {},
                        })
                    elif isinstance(block, ToolUseBlock):
                        messages_batch.append({
                            "run_id": str(task.id),
                            "brand_id": str(task.brand_id),
                            "seq": seq,
                            "msg_type": "tool_use",
                            "content": block.name,
                            "metadata": {"input": _truncate(block.input, 8192)},
                        })
                    elif isinstance(block, ThinkingBlock):
                        messages_batch.append({
                            "run_id": str(task.id),
                            "brand_id": str(task.brand_id),
                            "seq": seq,
                            "msg_type": "thinking",
                            "content": block.thinking[:2000],
                            "metadata": {},
                        })
                    seq += 1

                # Flush batch every 10 messages (dashboard sees live progress)
                if len(messages_batch) >= 10:
                    await _flush_messages(supabase_client, messages_batch)
                    messages_batch = []

            elif isinstance(message, ResultMessage):
                session_id = message.session_id
                total_cost = message.total_cost_usd
                final_result = message.result

                if message.stop_reason == "success":
                    # Flush remaining messages
                    if messages_batch:
                        await _flush_messages(supabase_client, messages_batch)

                    await _complete_task(supabase_client, task, {
                        "status": "completed",
                        "output": {"result": final_result, "cost_usd": total_cost},
                        "session_id": session_id,
                        "work_dir": str(workdir),
                        "completed_at": datetime.utcnow().isoformat(),
                    })
                else:
                    # Hit limit or error
                    await _fail_task(supabase_client, task, {
                        "error": f"Stop reason: {message.stop_reason}",
                        "output": {"partial_result": final_result, "cost_usd": total_cost},
                        "session_id": session_id,
                    })

    except Exception as e:
        if messages_batch:
            await _flush_messages(supabase_client, messages_batch)
        await _fail_task(supabase_client, task, {"error": str(e)})


async def _flush_messages(supabase_client, batch: list):
    """Write message batch directly to Supabase (bypasses gateway for speed)."""
    supabase_client.table("agent_messages").insert(batch).execute()
    batch.clear()


def _truncate(data, max_len: int) -> dict:
    """Truncate tool input/output to prevent oversized DB writes."""
    s = json.dumps(data) if isinstance(data, dict) else str(data)
    if len(s) > max_len:
        return {"truncated": s[:max_len], "_truncated": True}
    return data
```

#### poller.py

```python
async def poll_loop(config: DaemonConfig, client: DaemonClient):
    semaphore = asyncio.Semaphore(config.max_concurrent)

    while True:
        task = await client.claim_task(config.runtime_id)
        if task:
            async with semaphore:
                asyncio.create_task(execute_task(task, config, client))

        await asyncio.sleep(config.poll_interval)
```

#### scheduler.py

```python
async def schedule_loop(config: DaemonConfig, client: DaemonClient):
    while True:
        pending = await client.get_pending_schedules()
        for schedule in pending:
            await client.trigger_schedule(schedule.id)

        await asyncio.sleep(60)  # Check every minute
```

#### __main__.py

```python
async def main():
    config = DaemonConfig.from_env()

    # 1. Detect CLIs
    runtimes = detect_runtimes()
    if not runtimes:
        print("No agent CLIs found on PATH")
        sys.exit(1)

    # 2. Register with gateway
    client = DaemonClient(config)
    runtime_id = await client.register(runtimes[0])
    config.runtime_id = runtime_id

    # 3. Start concurrent loops
    await asyncio.gather(
        heartbeat_loop(config, client),
        poll_loop(config, client),
        schedule_loop(config, client),
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Phase 4: Dashboard — Agent Panel

**New components in `app-meetkai/`:**

1. **`app/(dashboard)/agents/page.tsx`** — Agent overview page
   - Runtime status (online/offline, last heartbeat)
   - Running tasks with live progress
   - Task history (recent completions, failures)
   - Schedule management (create/edit/enable/disable cron tasks)

2. **`components/dashboard/agent-live-view.tsx`** — Real-time execution viewer
   - Uses `useAgentMessages(runId)` hook (new)
   - Renders message stream: thinking, tool use (collapsible), text output, errors
   - Progress bar from `agent_runs.progress` field
   - Elapsed time counter

3. **`lib/hooks.ts`** — Add new hooks:
   ```typescript
   export function useAgentMessages(runId: string | undefined) {
     // Subscribe to agent_messages filtered by run_id
     // Realtime: INSERT events on agent_messages
   }

   export function useRuntimes() {
     // Subscribe to runtimes table
   }

   export function useSchedules(brandId: string | undefined) {
     // Subscribe to schedules table
   }
   ```

4. **`lib/types.ts`** — Add types:
   ```typescript
   export interface AgentMessage {
     id: string; run_id: string; brand_id: string;
     seq: number; msg_type: "text"|"tool_use"|"tool_result"|"thinking"|"error"|"status";
     content: string; metadata: Record<string, unknown>;
     created_at: string;
   }

   export interface Runtime {
     id: string; daemon_id: string; name: string;
     host_info: Record<string, unknown>;
     status: "online"|"offline"|"draining";
     last_heartbeat: string; created_at: string;
   }

   export interface Schedule {
     id: string; brand_id: string; name: string;
     cron_expr: string; skill: string; task_type: string;
     input: Record<string, unknown>; enabled: boolean;
     last_run_at: string | null; next_run_at: string | null;
   }
   ```

---

### Phase 5: Task Creation Integration

Wire the existing approval workflow to create daemon-claimable tasks:

1. **When user clicks "Execute" on an approved action** → Insert `agent_runs` row with `status: 'pending'`, `trigger: 'dashboard'`
2. **When schedule fires** → Insert `agent_runs` row with `status: 'pending'`, `trigger: 'scheduled'`, `schedule_id`
3. **When user creates task from agents page** → Insert `agent_runs` row with `status: 'pending'`, `trigger: 'manual'`

The daemon picks up all pending rows regardless of trigger source.

---

## Files to Create

| File | Purpose |
|---|---|
| `daemon/__init__.py` | Package init |
| `daemon/__main__.py` | Entry point |
| `daemon/config.py` | Configuration from env vars |
| `daemon/client.py` | HTTP client for gateway daemon API |
| `daemon/detector.py` | Claude Code CLI detection |
| `daemon/executor.py` | Task execution (spawn, stream, complete) |
| `daemon/injector.py` | Skill + knowledge injection into workdir |
| `daemon/poller.py` | Poll loop (3s) |
| `daemon/heartbeat.py` | Heartbeat loop (15s) |
| `daemon/scheduler.py` | Cron schedule checker |
| `daemon/models.py` | Pydantic data models |
| `daemon/requirements.txt` | Dependencies |
| `app-meetkai/supabase/migrations/005_daemon.sql` | Schema additions |
| `gateway/routers/daemon.py` | Gateway daemon API |
| `app-meetkai/app/(dashboard)/agents/page.tsx` | Agents dashboard |
| `app-meetkai/components/dashboard/agent-live-view.tsx` | Live execution viewer |

## Files to Modify

| File | Change |
|---|---|
| `gateway/main.py` | Mount daemon router |
| `gateway/requirements.txt` | Add supabase-py, croniter |
| `app-meetkai/lib/types.ts` | Add AgentMessage, Runtime, Schedule types |
| `app-meetkai/lib/hooks.ts` | Add useAgentMessages, useRuntimes, useSchedules |
| `app-meetkai/app/api/actions/execute/route.ts` | Insert agent_runs row instead of inline gateway call |

## Existing Code to Reuse

| What | Where | How |
|---|---|---|
| Job queue pattern | `gateway/jobs.py` | Follow same create → submit → poll → complete pattern |
| Auth middleware | `gateway/auth.py` | Reuse `verify_api_key` for daemon endpoints |
| Agent runs realtime | `app-meetkai/lib/hooks.ts:useAgentRuns` | Extend pattern for agent_messages |
| Execution monitor | `kai/operator/execution_monitor.py` | Reuse ExecutionState enum, ActionHistory JSONL |
| Skill definitions | `harness/skills/*/SKILL.md` | Copy into workdir for injection |
| Knowledge files | `knowledge/` | Symlink relevant frameworks into workdir |
| TypeScript types | `app-meetkai/lib/types.ts` | Extend existing AgentRun interface |
| Dashboard layout | `app-meetkai/app/(dashboard)/dashboard/page.tsx` | Follow same component structure |

---

## Verification

1. **Schema**: Run `005_daemon.sql` → verify tables created
2. **Gateway**: `POST /daemon/register` → runtime in `runtimes` table
3. **Daemon startup**: `python -m daemon start` → CLI detection, registration, heartbeat
4. **Task claim**: Insert pending `agent_run` → daemon claims within 3s
5. **Execution**: Daemon spawns Claude Code → `agent_messages` streaming to Supabase
6. **Dashboard**: Agents page → real-time progress via Supabase Realtime
7. **Completion**: Task finishes → `agent_runs.status = 'completed'`
8. **Scheduling**: Daily audit at 8am → daemon triggers correctly
9. **Failure**: Kill Claude mid-task → `status='failed'` with error
10. **Concurrency**: 5 queued tasks → 4 run in parallel (max_concurrent)
