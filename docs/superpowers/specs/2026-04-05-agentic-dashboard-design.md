# MeetKai Agentic Dashboard — Design Spec

**Date:** 2026-04-05
**Status:** Design — pending approval
**Prereq:** [Gap Analysis](./2026-04-05-meetkai-gap-analysis.md)

---

## Vision

MeetKai is an AI CMO that runs your marketing. Not a dashboard you stare at — a system that works while you sleep, shows you the score when you wake up, and takes orders when you have them.

Business owners open the app and see three things:
1. **How's my marketing doing?** (score, trends, what changed)
2. **What needs my attention?** (approvals, alerts, opportunities)
3. **What did the AI do overnight?** (actions taken, content generated, audits run)

When they want something — "write me a spring sale email campaign" — they say it in the chat. Or they click a button. Doesn't matter. Same brain, same output, same quality gates.

---

## Architecture: The Brain Pattern

One brain. Many triggers. The dashboard, chat, cron scheduler, and webhooks are all input surfaces to the same deterministic skill router that calls the same gateway.

```
┌─────────────────────────────────────────────────────┐
│                    TRIGGER LAYER                     │
│                                                     │
│  Dashboard UI    Chat (AI SDK)    Cron Agent    Webhooks  │
│  (buttons,       (freeform +     (scheduled    (score     │
│   cards,          skill flows)    tasks)        drops,    │
│   one-clicks)                                   alerts)  │
└──────────┬──────────┬──────────┬──────────┬──────┘
           │          │          │          │
           ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────┐
│                   SKILL ROUTER                       │
│                                                     │
│  Deterministic routing: trigger → skill → gateway   │
│  Maps actions to Kai skills (30+)                   │
│  Applies risk-tier policy (auto / approve / confirm)│
│  Manages multi-phase skill workflows                │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                GATEWAY (FastAPI)                     │
│                                                     │
│  /generate          Content engine (outcome engine)  │
│  /ops/propose       Action proposals + policy engine │
│  /ops/audit         MiKai audit engine               │
│  /agent/run         Task execution                   │
│  /runtime/*         Runs, artifacts, approvals       │
│  /webhooks/*        Analytics adapters               │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                   DATA LAYER                         │
│                                                     │
│  Supabase (brands, audits, integrations, actions,   │
│            snapshots, content, runs)                 │
│  Gateway SQLite (jobs, runs, artifacts)              │
│  Runtime Store (lineage, approvals)                  │
└─────────────────────────────────────────────────────┘
```

### Why This Matters

Every interaction — button click, chat message, cron tick, webhook event — goes through the same path: Skill Router → Gateway → Data Layer. This means:

- The chat doesn't need to be smart. It maps intent to skills. The skills are smart.
- Dashboard buttons are just deterministic skill invocations with pre-filled parameters.
- The cron agent uses the same skills the user triggers manually.
- Adding a new skill to the gateway makes it available everywhere simultaneously.

---

## Trigger Layer Design

### 1. Dashboard UI (deterministic triggers)

The dashboard is the monitoring + control surface. Every interactive element maps to a gateway call.

| UI Element | Gateway Call | Skill |
|------------|-------------|-------|
| "Run Audit" button | `POST /ops/audit/{brand_id}` | kai-audit |
| "Generate Actions" button | `POST /ops/propose` | Action engine |
| Approve action (one-click) | `POST /runtime/runs/{id}/approve` | — |
| "Sync Analytics" button | `POST /webhooks/analytics/sync` | — |
| "Write Content" card | `POST /generate` | kai-write |
| "Plan Content Calendar" card | `POST /generate` (format=calendar) | kai-content-calendar |
| "Audit Landing Page" card | `POST /ops/audit` + CRO params | kai-cro |

No chat required. Click → skill executes → result appears in dashboard.

### 2. Chat Panel (Vercel AI SDK)

For freeform requests and complex multi-phase skill flows.

**Tech stack:**
- `ai` package (Vercel AI SDK)
- `/api/chat/route.ts` — streaming route handler
- `useChat` hook on client
- Server-side tool definitions that map to gateway endpoints

**Tool definitions (launch set):**

```typescript
const tools = {
  run_audit: {
    description: "Run a marketing audit on the user's website",
    parameters: z.object({ domain: z.string().optional() }),
    execute: async ({ domain }) => gateway.post('/ops/audit/{brand_id}', { domain })
  },
  generate_content: {
    description: "Generate marketing content (blog, email, social, ads, landing page)",
    parameters: z.object({
      format: z.enum(['blog', 'email', 'cold-email', 'linkedin', 'meta-ads', 'google-ads', 'tiktok', 'landing-page', 'press']),
      keyword: z.string(),
      persona: z.string().optional()
    }),
    execute: async (params) => gateway.post('/generate', params)
  },
  get_analytics: {
    description: "Get current analytics data (traffic, rankings, performance)",
    parameters: z.object({ channel: z.enum(['ga4', 'gsc', 'all']).default('all') }),
    execute: async ({ channel }) => gateway.get('/webhooks/analytics/summary')
  },
  propose_actions: {
    description: "Generate action proposals from latest audit findings",
    parameters: z.object({}),
    execute: async () => gateway.post('/ops/propose')
  },
  approve_action: {
    description: "Approve a pending action",
    parameters: z.object({ action_id: z.string() }),
    execute: async ({ action_id }) => gateway.post(`/runtime/runs/${action_id}/approve`)
  },
  get_score: {
    description: "Get current marketing health score and breakdown",
    parameters: z.object({}),
    execute: async () => gateway.get('/ops/audit/{brand_id}/latest')
  },
  run_skill: {
    description: "Run a specific Kai marketing skill",
    parameters: z.object({
      skill: z.enum([
        'kai-seo-audit', 'kai-cro', 'kai-landing-page', 'kai-email-system',
        'kai-ad-campaign', 'kai-social', 'kai-cold-outreach', 'kai-competitors',
        'kai-content-calendar', 'kai-brand', 'kai-growth-plan'
      ]),
      context: z.string().optional()
    }),
    execute: async ({ skill, context }) => gateway.post('/generate', { skill, context })
  }
}
```

**Chat behavior:**
- System prompt includes brand context (name, URL, archetype, score, connected channels)
- Tool calls are deterministic — the AI selects the tool, gateway executes it
- Results stream back and render inline (content previews, score cards, action lists)
- Multi-phase skills (like kai-write) can be conversational: "What persona?" → "What angle?" → generate
- Simple requests are one-shot: "What's my score?" → tool call → answer

### 3. Cron Agent (existing scheduler)

Already built in `agent/scheduler.py`. Connects to dashboard via:
- Gateway endpoints for execution
- Supabase for result storage
- Dashboard Realtime subscriptions for live updates

**Launch schedule:**
| Task | Cron | What It Does |
|------|------|-------------|
| `daily_analytics` | `0 6 * * *` | Pull GA4/GSC, generate briefing |
| `daily_audit` | `0 7 * * *` | Re-run MiKai audit, detect score changes |
| `connector_health` | `0 */6 * * *` | Check integration health, flag degraded |
| `weekly_report` | `0 9 * * 1` | Weekly marketing summary |

### 4. Webhooks / Event Triggers

Reactive triggers that fire skills based on events:

| Event | Trigger | Skill |
|-------|---------|-------|
| Score drops >10 points | Audit comparison | Auto-generate fix actions |
| New integration connected | Connection webhook | Auto-run audit for that channel |
| Action approved | Approval webhook | Execute via content engine |
| Content published | Content log | Schedule 30-day performance check |

---

## Risk-Tiered Autonomy

Every action has a risk tier. The user sets a global "autonomy dial."

### Risk Classification

| Tier | Actions | Examples |
|------|---------|---------|
| **Low** | Read-only, internal drafts | Pull analytics, run audit, generate draft content, score a page |
| **Medium** | Publishable content, outbound comms | Send email campaign, publish blog post, post to social, change ad copy |
| **High** | Money, infrastructure, deletions | Change ad budget, modify website code, delete content, alter integrations |

### Autonomy Modes

| Mode | Low Risk | Medium Risk | High Risk |
|------|----------|-------------|-----------|
| **Supervised** | Notify after | Propose → approve | Propose → explain → confirm |
| **Balanced** (default) | Auto-execute | Propose → one-click approve | Propose → explain → confirm |
| **Autonomous** | Auto-execute | Auto-execute, notify after | Propose → one-click approve |

Stored in `brands.metadata.autonomy_mode`. Default: Balanced.

---

## Dashboard Pages (Redesigned)

### Page 1: Home (Mission Control)

The first thing a business owner sees. No clicks required to understand status.

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Marketing Health Score: 67/100 ↑3         [Run Audit]  │
│  ████████████████████░░░░░░░░░░                         │
│                                                         │
│  8 dimensions: offer ✓  trust ⚠  CRO ✗  SEO ✓  ...    │
└─────────────────────────────────────────────────────────┘
┌──────────────────────┐  ┌──────────────────────────────┐
│  NEEDS YOUR ATTENTION │  │  AI ACTIVITY (last 24h)      │
│                      │  │                              │
│  ⚡ 3 actions pending │  │  ✓ Analytics synced (6am)    │
│  ⚠ GSC token expiring│  │  ✓ Audit re-run: 67 (+3)    │
│  📝 2 drafts ready   │  │  ✓ Blog draft: "5 ways..."  │
│                      │  │  ⏳ Email campaign queued    │
│  [Approve All Low    │  │  ✗ Ad sync failed (retry 2)  │
│   Risk Actions]      │  │                              │
└──────────────────────┘  └──────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  QUICK ACTIONS                                          │
│                                                         │
│  [Write Content]  [Plan Calendar]  [Audit Page]         │
│  [Run Ads]        [Cold Outreach]  [Competitor Intel]   │
└─────────────────────────────────────────────────────────┘
```

**Data sources:**
- Score: `audits` table (latest)
- Needs attention: `actions` where `approval_state = 'pending'` + integration health
- AI activity: `actions` + gateway job history + agent execution log
- Quick actions: Hardcoded cards that trigger gateway skills

### Page 2: Connect

Same as current but with fixes from gap analysis:
- Fix GSC provider name mismatch
- Add config pickers for 8 providers
- Wire up the dead Sync button
- Remove `window.location.reload()`
- Show "no data sync yet" honestly for providers without sync endpoints

### Page 3: Analytics

Currently only GA4. Redesigned to show whatever data is available:

**Sections (show/hide based on connected providers):**
- Website traffic (GA4)
- Search performance (GSC)
- Social metrics (when social providers have sync)
- Email performance (when email providers have sync)
- Ad performance (when ad providers have sync)

Date range picker wired to actually filter data. Sync buttons call gateway analytics adapters.

### Page 4: Content & Actions

Merged page replacing the separate "Actions" page. This is where the AI's work lives.

**Tabs:**
- **Pending** — Actions/content awaiting approval. One-click approve, bulk approve for low-risk.
- **In Progress** — Currently executing (with live status via Realtime)
- **Completed** — Generated content, executed actions, with quality gate scores
- **Content Library** — All generated content organized by format, date, status

Each item shows:
- What skill generated it
- Quality gate score (Four U's)
- Risk tier badge
- Preview/expand for full content
- Approve / Reject / Revise actions

### Page 5: Settings

Current settings plus:
- **Autonomy dial** — Supervised / Balanced / Autonomous
- **Notification preferences** — Actually wired to delivery
- **Gateway connection** — API URL + key configuration
- **Agent schedule** — View/modify cron tasks
- Brand profile (existing)

### Chat Panel (persistent sidebar)

Always accessible via a toggle button (bottom-right or sidebar icon). Slides out as a right panel overlaying the current page.

**Behavior:**
- Persists across page navigation (conversation doesn't reset)
- Renders tool results inline (content preview cards, score widgets, action lists)
- Can reference current page context ("audit THIS page" when on analytics)
- Shows typing/thinking indicator during gateway calls
- History persisted to Supabase for continuity across sessions

---

## Data Model Changes

### New Supabase Tables

```sql
-- Content generated by the AI CMO
CREATE TABLE content (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id UUID REFERENCES brands(id),
  format TEXT NOT NULL, -- blog, email, linkedin, meta-ads, etc.
  title TEXT,
  body TEXT, -- the generated content
  brief JSONB, -- the brief that produced it
  gate_report JSONB, -- Four U's scores, banned word check, etc.
  status TEXT DEFAULT 'draft', -- draft, approved, published, rejected
  skill TEXT, -- which kai skill produced it
  gateway_job_id TEXT, -- link to gateway job
  gateway_run_id TEXT, -- link to gateway run
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  published_at TIMESTAMPTZ
);

-- Chat history for AI SDK persistence
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id UUID REFERENCES brands(id),
  role TEXT NOT NULL, -- user, assistant, tool, system
  content TEXT,
  tool_calls JSONB, -- tool invocations and results
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Agent execution log (mirrors gateway but in Supabase for dashboard access)
CREATE TABLE agent_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id UUID REFERENCES brands(id),
  task_type TEXT NOT NULL,
  skill TEXT,
  trigger TEXT NOT NULL, -- 'dashboard', 'chat', 'cron', 'webhook', 'event'
  status TEXT DEFAULT 'pending', -- pending, running, completed, failed
  input JSONB,
  output JSONB,
  error TEXT,
  risk_tier TEXT DEFAULT 'low',
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

**RLS:** Same pattern — all tables scoped to brand ownership via `brand_id → brands.user_id = auth.uid()`.

### Modified Tables

```sql
-- Add to actions table
ALTER TABLE actions ADD COLUMN skill TEXT; -- which kai skill
ALTER TABLE actions ADD COLUMN gateway_job_id TEXT;
ALTER TABLE actions ADD COLUMN trigger TEXT DEFAULT 'dashboard'; -- dashboard, chat, cron, webhook

-- Add to brands table
ALTER TABLE brands ADD COLUMN autonomy_mode TEXT DEFAULT 'balanced';
ALTER TABLE brands ADD COLUMN gateway_url TEXT;
ALTER TABLE brands ADD COLUMN gateway_key TEXT; -- stored server-side only, never sent to client
```

---

## Gateway Client

A typed client library in the Next.js app that wraps all gateway calls:

```
lib/gateway/
├── client.ts          -- Base HTTP client (fetch + auth + error handling)
├── generate.ts        -- POST /generate wrapper
├── audit.ts           -- POST /ops/audit wrapper
├── actions.ts         -- /ops/propose, /ops/actions/* wrappers
├── agent.ts           -- /agent/* wrappers
├── analytics.ts       -- /webhooks/analytics/* wrappers
├── runtime.ts         -- /runtime/* wrappers (runs, approvals, artifacts)
└── types.ts           -- Gateway request/response types
```

Every dashboard component and API route uses this client instead of raw fetch calls. The chat tool definitions use it too.

---

## New Dependencies

```json
{
  "ai": "^4.0",              // Vercel AI SDK
  "@ai-sdk/anthropic": "^1.0", // Claude as chat backbone
  "zod": "^3.23"              // Input validation (also fixes security gap)
}
```

---

## Launch Slice (Phase 1)

What ships first — the minimum version a business owner would pay for:

| # | Feature | What Ships |
|---|---------|-----------|
| 1 | **Fix critical bugs** | GSC provider name, score=0 falsy, risk tier inversion, dead sync button |
| 2 | **Gateway client** | Typed client library connecting dashboard → gateway |
| 3 | **Home page redesign** | Mission control: score + attention items + AI activity + quick actions |
| 4 | **Real action execution** | Actions route through gateway content engine, not static templates |
| 5 | **Chat panel** | Vercel AI SDK, 7 tools (audit, generate, analytics, propose, approve, score, run_skill) |
| 6 | **Risk-tiered approvals** | Low/medium/high classification + autonomy dial in settings |
| 7 | **Content page** | View generated content with quality scores, approve/reject/revise |
| 8 | **Agent activity feed** | Show what the cron agent has done (pulls from gateway job history) |

### Phase 2 (fast follow)
- Config pickers for 8 providers
- Sync pipelines for Facebook, Google Ads, Meta Ads
- Scheduled syncs via cron
- Notification delivery (Resend)
- Onboarding wizard

### Phase 3 (scale)
- Multi-brand / agency mode
- Billing (Stripe)
- Team collaboration
- Publishing to connected platforms
- Chat history persistence
- Conversational multi-phase skill flows

---

## File Changes Summary

### New Files
| File | Purpose |
|------|---------|
| `lib/gateway/client.ts` | Gateway HTTP client |
| `lib/gateway/generate.ts` | Content generation wrapper |
| `lib/gateway/audit.ts` | Audit wrapper |
| `lib/gateway/actions.ts` | Action proposal wrapper |
| `lib/gateway/agent.ts` | Agent control wrapper |
| `lib/gateway/analytics.ts` | Analytics wrapper |
| `lib/gateway/runtime.ts` | Runtime wrapper |
| `lib/gateway/types.ts` | Gateway types |
| `app/api/chat/route.ts` | Vercel AI SDK chat handler with tools |
| `app/(dashboard)/content/page.tsx` | Content & actions merged page |
| `components/chat/chat-panel.tsx` | Slide-out chat panel |
| `components/chat/message.tsx` | Chat message renderer |
| `components/chat/tool-result.tsx` | Inline tool result cards |
| `components/dashboard/mission-control.tsx` | Redesigned home hero |
| `components/dashboard/attention-items.tsx` | "Needs your attention" widget |
| `components/dashboard/ai-activity.tsx` | Agent activity feed |
| `components/dashboard/quick-actions.tsx` | Skill trigger cards |
| `supabase/migrations/004_agentic.sql` | New tables + alterations |

### Modified Files
| File | Changes |
|------|---------|
| `lib/types.ts` | Fix GSC provider name, add Content/AgentRun/ChatMessage types, add autonomy mode |
| `lib/hooks.ts` | Add useContent, useAgentRuns, useChatHistory hooks, fix module-scope client |
| `lib/utils.ts` | Add risk tier helpers |
| `app/(dashboard)/dashboard/page.tsx` | Complete redesign to mission control layout |
| `app/(dashboard)/actions/page.tsx` | Redirect to /content or merge |
| `app/(dashboard)/settings/page.tsx` | Add autonomy dial, gateway config |
| `app/(dashboard)/layout.tsx` | Add chat panel toggle |
| `components/dashboard/quick-stats.tsx` | Fix score=0 bug, wire to gateway |
| `components/dashboard/activity-feed.tsx` | Rewrite to use agent_runs table |
| `components/dashboard/pending-actions.tsx` | Add risk tier badges, bulk approve |
| `app/api/actions/execute/route.ts` | Replace template stubs with gateway calls |
| `app/api/actions/generate/route.ts` | Fix channel mapping, risk tiers, dedup |
| `package.json` | Add ai, @ai-sdk/anthropic, zod |

### Deleted Files
| File | Reason |
|------|--------|
| None | No files deleted in Phase 1 |

---

## Verification Plan

### Manual Testing
1. Open dashboard → see score, attention items, activity feed with real data
2. Click "Run Audit" → audit runs via gateway → score updates in real time
3. Click "Generate Actions" → actions appear with correct risk tiers and channels
4. Approve a low-risk action → auto-executes via gateway content engine → result appears in content page
5. Open chat → "What's my marketing score?" → tool call → score displayed inline
6. Chat → "Write me a blog post about AI receptionists" → gateway /generate call → content draft appears
7. Change autonomy dial to Autonomous → low-risk actions auto-execute
8. Check that cron agent activity shows in AI Activity feed

### Automated Checks
- All API routes have zod input validation
- Gateway client handles auth failures and timeouts gracefully
- Chat tools map correctly to gateway endpoints
- RLS on new tables prevents cross-brand access
- Risk tier classification matches the spec
- Quality gate scores display correctly on content cards
