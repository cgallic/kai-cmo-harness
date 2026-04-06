# MeetKai Agentic Dashboard — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the MeetKai dashboard from a monitoring shell into an agentic AI CMO with gateway-connected execution, chat panel, risk-tiered approvals, and a mission control home page.

**Architecture:** The dashboard becomes a trigger surface for the gateway's skill router. Every button click and chat message maps to a gateway API call. A typed gateway client library (`lib/gateway/`) abstracts all HTTP calls. The Vercel AI SDK powers the chat panel with tool definitions that invoke gateway endpoints. New Supabase tables (`content`, `chat_messages`, `agent_runs`) store AI-generated artifacts.

**Tech Stack:** Next.js 14 (App Router), React 18, TypeScript 5.5, Supabase (auth + Postgres + Realtime), Tailwind CSS 3, Vercel AI SDK v4 (`ai` + `@ai-sdk/anthropic`), Zod, Lucide React.

**Codebase root:** `app-meetkai/` (all paths relative to this)

**Spec:** `docs/superpowers/specs/2026-04-05-agentic-dashboard-design.md`
**Gap analysis:** `docs/superpowers/specs/2026-04-05-meetkai-gap-analysis.md`

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `lib/gateway/client.ts` | Base HTTP client — fetch wrapper with auth, error handling, timeout |
| `lib/gateway/types.ts` | Gateway request/response TypeScript types |
| `lib/gateway/generate.ts` | `POST /generate` wrapper |
| `lib/gateway/audit.ts` | `GET /kai-operator/audit/{id}` wrapper |
| `lib/gateway/actions.ts` | `/ops/propose`, `/ops/proposals/*`, `/ops/actions/*` wrappers |
| `lib/gateway/analytics.ts` | `/webhooks/analytics/*` wrappers |
| `lib/gateway/runtime.ts` | `/runtime/*` wrappers (runs, approvals, artifacts) |
| `lib/gateway/agent.ts` | `/agent/*` wrappers (status, tasks, executions) |
| `app/api/chat/route.ts` | Vercel AI SDK streaming chat handler with 7 tool definitions |
| `components/chat/chat-panel.tsx` | Slide-out chat panel with useChat hook |
| `components/chat/message.tsx` | Chat message renderer (user, assistant, tool results) |
| `components/chat/tool-result.tsx` | Inline tool result cards (scores, content previews, action lists) |
| `components/dashboard/attention-items.tsx` | "Needs your attention" widget (pending approvals, alerts) |
| `components/dashboard/ai-activity.tsx` | Agent activity feed from agent_runs table |
| `components/dashboard/quick-actions.tsx` | Skill trigger cards (Write Content, Plan Calendar, etc.) |
| `app/(dashboard)/content/page.tsx` | Content & Actions merged page with tabs |
| `supabase/migrations/004_agentic.sql` | New tables + column additions |

### Modified Files

| File | Changes |
|------|---------|
| `lib/types.ts` | Add Content, AgentRun, ChatMessage types; add AutonomyMode type |
| `lib/hooks.ts` | Add useContent, useAgentRuns hooks; fix module-scope client |
| `lib/utils.ts` | Add riskTierColor, riskTierLabel helpers |
| `components/dashboard/quick-stats.tsx` | Fix score=0 falsy bug |
| `app/api/actions/execute/route.ts` | Replace static templates with gateway content engine call |
| `app/api/actions/generate/route.ts` | Fix risk tier inversion (critical→high) |
| `app/(dashboard)/dashboard/page.tsx` | Redesign to mission control layout |
| `app/(dashboard)/settings/page.tsx` | Add autonomy dial + gateway config section |
| `app/(dashboard)/layout.tsx` | Add chat panel toggle |
| `app/(dashboard)/analytics/page.tsx` | Fix GSC provider name lookup |
| `components/layout/sidebar.tsx` | Add Content nav item, reorder |

---

## Task 1: Critical Bug Fixes

**Files:**
- Modify: `components/dashboard/quick-stats.tsx:46-47`
- Modify: `app/api/actions/generate/route.ts:143`
- Modify: `app/(dashboard)/settings/page.tsx:337-338`
- Modify: `app/(dashboard)/analytics/page.tsx:52-53`

- [ ] **Step 1: Fix score=0 falsy bug in quick-stats**

In `components/dashboard/quick-stats.tsx`, line 46 uses `audit?.overall_score ? ...` which evaluates to false when score is 0.

Change line 46:
```typescript
// OLD
value: audit?.overall_score ? Math.round(audit.overall_score) : "—",
// NEW
value: audit?.overall_score != null ? Math.round(audit.overall_score) : "—",
```

And line 47:
```typescript
// OLD
color: audit?.overall_score
  ? audit.overall_score >= 70 ? "text-success" : audit.overall_score >= 40 ? "text-amber" : "text-error"
  : "text-text-tertiary",
// NEW
color: audit?.overall_score != null
  ? audit.overall_score >= 70 ? "text-success" : audit.overall_score >= 40 ? "text-amber" : "text-error"
  : "text-text-tertiary",
```

- [ ] **Step 2: Fix risk tier inversion in action generation**

In `app/api/actions/generate/route.ts`, line 143: critical findings should be "high" risk, warning should be "medium".

```typescript
// OLD
risk_tier: finding.severity === "critical" ? "medium" : "low",
// NEW
risk_tier: finding.severity === "critical" ? "high" : "medium",
```

- [ ] **Step 3: Fix GSC provider name mismatch in settings page**

In `app/(dashboard)/settings/page.tsx`, line 337-338 looks for `provider === "google_search_console"` but Supabase stores `provider: "gsc"` (matching the PROVIDERS config in types.ts).

```typescript
// OLD
const gscIntegration = integrations.find(
  (i) => i.provider === "google_search_console" && i.status === "connected"
);
// NEW
const gscIntegration = integrations.find(
  (i) => i.provider === "gsc" && i.status === "connected"
);
```

- [ ] **Step 4: Fix GSC provider name mismatch in analytics page**

Same bug in `app/(dashboard)/analytics/page.tsx`, line 52-53:

```typescript
// OLD
const gscConnected = integrations.some(
  (i) => i.provider === "google_search_console" && i.status === "connected"
);
// NEW
const gscConnected = integrations.some(
  (i) => i.provider === "gsc" && i.status === "connected"
);
```

- [ ] **Step 5: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add components/dashboard/quick-stats.tsx app/api/actions/generate/route.ts app/\(dashboard\)/settings/page.tsx app/\(dashboard\)/analytics/page.tsx
git commit -m "fix: score=0 falsy, risk tier inversion, GSC provider name mismatch"
```

---

## Task 2: Install New Dependencies

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Install ai, @ai-sdk/anthropic, and zod**

```bash
cd app-meetkai && pnpm add ai @ai-sdk/anthropic zod
```

- [ ] **Step 2: Add ANTHROPIC_API_KEY to env example**

Append to `.env.local.example`:
```
# AI Chat (Vercel AI SDK)
ANTHROPIC_API_KEY=

# Gateway
GATEWAY_URL=http://89.167.60.171:10002
GATEWAY_API_KEY=
```

- [ ] **Step 3: Commit**

```bash
git add package.json pnpm-lock.yaml .env.local.example
git commit -m "feat: add Vercel AI SDK, Anthropic provider, and Zod dependencies"
```

---

## Task 3: Database Migration

**Files:**
- Create: `supabase/migrations/004_agentic.sql`

- [ ] **Step 1: Write the migration file**

```sql
-- 004_agentic.sql: Agentic dashboard tables + column additions

-- Content generated by the AI CMO
create table public.content (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  format text not null,
  title text,
  body text,
  brief jsonb,
  gate_report jsonb,
  status text default 'draft',
  skill text,
  gateway_job_id text,
  gateway_run_id text,
  metadata jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  published_at timestamptz
);

-- Chat history for AI SDK persistence
create table public.chat_messages (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  role text not null,
  content text,
  tool_calls jsonb,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

-- Agent execution log (mirrors gateway but in Supabase for dashboard access)
create table public.agent_runs (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  task_type text not null,
  skill text,
  trigger text not null default 'dashboard',
  status text default 'pending',
  input jsonb,
  output jsonb,
  error text,
  risk_tier text default 'low',
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz default now()
);

-- Add columns to actions
alter table public.actions add column if not exists skill text;
alter table public.actions add column if not exists gateway_job_id text;
alter table public.actions add column if not exists trigger text default 'dashboard';

-- Add columns to brands
alter table public.brands add column if not exists autonomy_mode text default 'balanced';
alter table public.brands add column if not exists gateway_url text;
alter table public.brands add column if not exists gateway_key text;

-- RLS for new tables
alter table public.content enable row level security;
alter table public.chat_messages enable row level security;
alter table public.agent_runs enable row level security;

create policy "content_select" on public.content
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "content_insert" on public.content
  for insert with check (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "content_update" on public.content
  for update using (brand_id in (select id from public.brands where user_id = auth.uid()));

create policy "chat_messages_select" on public.chat_messages
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "chat_messages_insert" on public.chat_messages
  for insert with check (brand_id in (select id from public.brands where user_id = auth.uid()));

create policy "agent_runs_select" on public.agent_runs
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "agent_runs_insert" on public.agent_runs
  for insert with check (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "agent_runs_update" on public.agent_runs
  for update using (brand_id in (select id from public.brands where user_id = auth.uid()));

-- Indexes
create index idx_content_brand_id on public.content(brand_id);
create index idx_content_status on public.content(status);
create index idx_content_format on public.content(format);
create index idx_chat_brand_id on public.chat_messages(brand_id);
create index idx_agent_runs_brand_id on public.agent_runs(brand_id);
create index idx_agent_runs_status on public.agent_runs(status);

-- Updated_at triggers
create trigger content_updated_at before update on public.content
  for each row execute function update_updated_at();

-- Check constraints
alter table public.content
  add constraint valid_content_status
  check (status in ('draft', 'approved', 'published', 'rejected'));

alter table public.agent_runs
  add constraint valid_agent_run_status
  check (status in ('pending', 'running', 'completed', 'failed'));

alter table public.brands
  add constraint valid_autonomy_mode
  check (autonomy_mode in ('supervised', 'balanced', 'autonomous'));

-- Enable Realtime on new tables
alter publication supabase_realtime add table public.content;
alter publication supabase_realtime add table public.agent_runs;
```

- [ ] **Step 2: Commit**

```bash
git add supabase/migrations/004_agentic.sql
git commit -m "feat: add content, chat_messages, agent_runs tables + brand autonomy columns"
```

---

## Task 4: Types and Utils Updates

**Files:**
- Modify: `lib/types.ts`
- Modify: `lib/utils.ts`

- [ ] **Step 1: Add new types to lib/types.ts**

Append after the `ChannelSnapshot` interface (after line 93):

```typescript
export interface Content {
  id: string;
  brand_id: string;
  format: string;
  title: string | null;
  body: string | null;
  brief: Record<string, unknown> | null;
  gate_report: Record<string, unknown> | null;
  status: ContentStatus;
  skill: string | null;
  gateway_job_id: string | null;
  gateway_run_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export type ContentStatus = "draft" | "approved" | "published" | "rejected";

export interface AgentRun {
  id: string;
  brand_id: string;
  task_type: string;
  skill: string | null;
  trigger: string;
  status: "pending" | "running" | "completed" | "failed";
  input: Record<string, unknown> | null;
  output: Record<string, unknown> | null;
  error: string | null;
  risk_tier: "low" | "medium" | "high";
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  brand_id: string;
  role: "user" | "assistant" | "tool" | "system";
  content: string | null;
  tool_calls: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export type AutonomyMode = "supervised" | "balanced" | "autonomous";
```

- [ ] **Step 2: Add risk tier helpers to lib/utils.ts**

Append after `statusBgColor` function:

```typescript
export function riskTierColor(tier: string): string {
  switch (tier) {
    case "low": return "text-success";
    case "medium": return "text-amber";
    case "high": return "text-error";
    default: return "text-text-tertiary";
  }
}

export function riskTierBgColor(tier: string): string {
  switch (tier) {
    case "low": return "bg-success-dim";
    case "medium": return "bg-amber-dim";
    case "high": return "bg-error-dim";
    default: return "bg-border";
  }
}
```

- [ ] **Step 3: Verify types compile and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add lib/types.ts lib/utils.ts
git commit -m "feat: add Content, AgentRun, ChatMessage types and risk tier helpers"
```

---

## Task 5: Gateway Client Library

**Files:**
- Create: `lib/gateway/client.ts`
- Create: `lib/gateway/types.ts`
- Create: `lib/gateway/generate.ts`
- Create: `lib/gateway/audit.ts`
- Create: `lib/gateway/actions.ts`
- Create: `lib/gateway/analytics.ts`
- Create: `lib/gateway/runtime.ts`
- Create: `lib/gateway/agent.ts`

- [ ] **Step 1: Create base client**

Create `lib/gateway/client.ts`:

```typescript
const GATEWAY_URL = process.env.GATEWAY_URL || "http://89.167.60.171:10002";
const GATEWAY_API_KEY = process.env.GATEWAY_API_KEY || "";

export class GatewayError extends Error {
  constructor(
    public status: number,
    public body: unknown,
    message?: string,
  ) {
    super(message || `Gateway error ${status}`);
    this.name = "GatewayError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
  timeout?: number;
}

export async function gateway<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, params, timeout = 30000 } = options;

  const url = new URL(path, GATEWAY_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(url.toString(), {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(GATEWAY_API_KEY ? { "X-API-Key": GATEWAY_API_KEY } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    const data = await res.json();

    if (!res.ok) {
      throw new GatewayError(res.status, data, data?.error || `Gateway ${res.status}`);
    }

    return data as T;
  } finally {
    clearTimeout(timer);
  }
}
```

- [ ] **Step 2: Create gateway types**

Create `lib/gateway/types.ts`:

```typescript
export interface GatewayResponse<T = unknown> {
  success: boolean;
  data: T;
  error: string | null;
  timestamp: string;
}

export interface AsyncJobResponse {
  job_id: string;
  run_id?: string;
  status: "pending" | "queued";
  message: string;
}

export interface JobInfo {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  command: string;
  result: unknown;
  error: string | null;
  created_at: string;
  completed_at: string | null;
  artifacts: ArtifactInfo[];
}

export interface ArtifactInfo {
  artifact_id: string;
  artifact_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface GenerateRequest {
  format: string;
  site: string;
  keyword: string;
  persona?: string;
  dry_run?: boolean;
  skip_gates?: boolean;
  brand_id?: string;
  workflow?: string;
  surface?: "local" | "remote";
}

export interface ProposalRequest {
  brand_id: string;
  channel: string;
  action_type: string;
  intent: string;
  proposed_changes: Record<string, unknown>;
  source_run_id?: string;
  metadata?: Record<string, unknown>;
}

export interface ProposalResponse {
  action_id: string;
  risk_tier: string;
  policy_result: Record<string, unknown>;
  approval_state: string;
  auto_eligible: boolean;
}

export interface DashboardResponse {
  pending_count: number;
  recent_actions: unknown[];
  active_integrations: unknown[];
  channel_summary: Record<string, unknown>;
}

export interface AgentStatus {
  running: boolean;
  paused: boolean;
  tasks: unknown[];
  last_execution: string | null;
}

export interface AgentExecution {
  id: string;
  task_type: string;
  client: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  result: unknown;
  error: string | null;
}

export interface RunInfo {
  run_id: string;
  workflow: string;
  brand_id: string;
  status: string;
  surface: string;
  created_at: string;
  completed_at: string | null;
  artifacts: ArtifactInfo[];
}
```

- [ ] **Step 3: Create generate wrapper**

Create `lib/gateway/generate.ts`:

```typescript
import { gateway } from "./client";
import type { AsyncJobResponse, JobInfo } from "./types";

export async function generateContent(req: {
  format: string;
  site: string;
  keyword: string;
  persona?: string;
  dry_run?: boolean;
  skip_gates?: boolean;
  brand_id?: string;
}): Promise<AsyncJobResponse> {
  return gateway<AsyncJobResponse>("/generate", {
    method: "POST",
    body: { ...req, surface: "remote" },
    timeout: 60000,
  });
}

export async function getGenerateJob(jobId: string): Promise<JobInfo> {
  return gateway<JobInfo>(`/jobs/${jobId}`);
}

export async function getJobArtifacts(jobId: string) {
  return gateway<{ artifacts: unknown[] }>(`/jobs/${jobId}/artifacts`);
}
```

- [ ] **Step 4: Create audit wrapper**

Create `lib/gateway/audit.ts`:

```typescript
import { gateway } from "./client";

export async function runAudit(businessId: string, scope = "full") {
  return gateway<Record<string, unknown>>(`/kai-operator/audit/${businessId}`, {
    method: "GET",
    params: { scope },
    timeout: 120000,
  });
}
```

- [ ] **Step 5: Create actions wrapper**

Create `lib/gateway/actions.ts`:

```typescript
import { gateway } from "./client";
import type { ProposalRequest, ProposalResponse, DashboardResponse } from "./types";

export async function propose(req: ProposalRequest): Promise<ProposalResponse> {
  return gateway<ProposalResponse>("/ops/propose", {
    method: "POST",
    body: req,
  });
}

export async function listProposals(brandId: string, limit = 20) {
  return gateway<{ proposals: unknown[]; count: number }>("/ops/proposals", {
    params: { brand_id: brandId, limit },
  });
}

export async function approveProposal(actionId: string, note?: string) {
  return gateway(`/ops/proposals/${actionId}/approve`, {
    method: "POST",
    body: { note },
  });
}

export async function rejectProposal(actionId: string, note?: string) {
  return gateway(`/ops/proposals/${actionId}/reject`, {
    method: "POST",
    body: { note },
  });
}

export async function listActions(brandId: string, filters?: {
  channel?: string;
  approval_state?: string;
  execution_state?: string;
  limit?: number;
}) {
  return gateway<{ actions: unknown[] }>("/ops/actions", {
    params: { brand_id: brandId, ...filters },
  });
}

export async function getDashboard(brandId?: string): Promise<DashboardResponse> {
  return gateway<DashboardResponse>("/ops/dashboard", {
    params: brandId ? { brand_id: brandId } : {},
  });
}
```

- [ ] **Step 6: Create analytics wrapper**

Create `lib/gateway/analytics.ts`:

```typescript
import { gateway } from "./client";

export async function getAnalyticsSummary(client: string) {
  return gateway<Record<string, unknown>>("/webhooks/analytics/summary", {
    method: "POST",
    body: { client },
  });
}

export async function getGscQueries(client: string) {
  return gateway<Record<string, unknown>>("/webhooks/analytics/gsc/queries", {
    method: "POST",
    body: { client },
  });
}
```

- [ ] **Step 7: Create runtime wrapper**

Create `lib/gateway/runtime.ts`:

```typescript
import { gateway } from "./client";
import type { RunInfo } from "./types";

export async function listRuns(filters?: {
  brand_id?: string;
  workflow?: string;
  status?: string;
  limit?: number;
}) {
  return gateway<{ runs: RunInfo[] }>("/runtime/runs", {
    params: filters as Record<string, string | number>,
  });
}

export async function getRun(runId: string): Promise<RunInfo> {
  return gateway<RunInfo>(`/runtime/runs/${runId}`);
}

export async function approveRun(runId: string, note?: string) {
  return gateway(`/runtime/runs/${runId}/approve`, {
    method: "POST",
    body: { note },
  });
}

export async function rejectRun(runId: string, note?: string) {
  return gateway(`/runtime/runs/${runId}/reject`, {
    method: "POST",
    body: { note },
  });
}

export async function listApprovals(filters?: {
  brand_id?: string;
  workflow?: string;
  limit?: number;
}) {
  return gateway<{ approvals: RunInfo[] }>("/runtime/approvals", {
    params: filters as Record<string, string | number>,
  });
}

export async function listArtifacts(filters?: {
  brand_id?: string;
  artifact_type?: string;
  limit?: number;
}) {
  return gateway<{ artifacts: unknown[] }>("/runtime/artifacts", {
    params: filters as Record<string, string | number>,
  });
}
```

- [ ] **Step 8: Create agent wrapper**

Create `lib/gateway/agent.ts`:

```typescript
import { gateway } from "./client";
import type { AgentStatus, AgentExecution } from "./types";

export async function getAgentStatus(): Promise<AgentStatus> {
  return gateway<AgentStatus>("/agent/status");
}

export async function getRecentExecutions(limit = 20): Promise<{ executions: AgentExecution[] }> {
  return gateway<{ executions: AgentExecution[] }>("/agent/executions", {
    params: { limit },
  });
}

export async function getUpcomingTasks(limit = 10) {
  return gateway<{ tasks: unknown[] }>("/agent/upcoming", {
    params: { limit },
  });
}

export async function runTask(taskType: string) {
  return gateway("/agent/run/" + taskType, {
    method: "POST",
    timeout: 120000,
  });
}
```

- [ ] **Step 9: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add lib/gateway/
git commit -m "feat: gateway client library — typed wrappers for all gateway endpoints"
```

---

## Task 6: New Data Hooks

**Files:**
- Modify: `lib/hooks.ts`

- [ ] **Step 1: Fix module-scope client and add new hooks**

The current `lib/hooks.ts` creates a module-scope `createClient()` call at line 8. This is a known issue — it should be called inside each hook or memoized. Fix this and add the new hooks.

Replace the entire `lib/hooks.ts` file. The new version:
- Moves `createClient()` into each hook
- Adds `useContent(brandId)` hook
- Adds `useAgentRuns(brandId)` hook
- Keeps all existing hooks unchanged in behavior

Add these two hooks at the end of the file (after `useSnapshots`):

```typescript
export function useContent(brandId: string | undefined, filters?: { status?: string; format?: string }) {
  const [content, setContent] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchContent = useCallback(async () => {
    if (!brandId) { setLoading(false); return; }

    const supabase = createClient();
    let query = supabase
      .from("content")
      .select("*")
      .eq("brand_id", brandId)
      .order("created_at", { ascending: false })
      .limit(50);

    if (filters?.status) query = query.eq("status", filters.status);
    if (filters?.format) query = query.eq("format", filters.format);

    const { data, error } = await query;
    if (error) console.error("useContent error:", error.message);
    setContent(data || []);
    setLoading(false);
  }, [brandId, filters?.status, filters?.format]);

  useEffect(() => {
    fetchContent();

    if (!brandId) return;

    const supabase = createClient();
    const channel = supabase
      .channel("content-changes")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "content", filter: `brand_id=eq.${brandId}` },
        () => { fetchContent(); }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [brandId, fetchContent]);

  return { content, loading, refresh: fetchContent };
}

export function useAgentRuns(brandId: string | undefined) {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRuns = useCallback(async () => {
    if (!brandId) { setLoading(false); return; }

    const supabase = createClient();
    const { data, error } = await supabase
      .from("agent_runs")
      .select("*")
      .eq("brand_id", brandId)
      .order("created_at", { ascending: false })
      .limit(20);

    if (error) console.error("useAgentRuns error:", error.message);
    setRuns(data || []);
    setLoading(false);
  }, [brandId]);

  useEffect(() => {
    fetchRuns();

    if (!brandId) return;

    const supabase = createClient();
    const channel = supabase
      .channel("agent-runs-changes")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "agent_runs", filter: `brand_id=eq.${brandId}` },
        () => { fetchRuns(); }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [brandId, fetchRuns]);

  return { runs, loading, refresh: fetchRuns };
}
```

Also update the imports at the top of the file to include the new types:

```typescript
import type { Brand, Integration, Action, Audit, ChannelSnapshot, Content, AgentRun } from "@/lib/types";
```

And fix the module-scope client issue. Change line 8 from:
```typescript
const supabase = createClient();
```
to removing it entirely, and in each existing hook (`useBrand`, `useAudit`, `useIntegrations`, `useActions`, `useSnapshots`), add `const supabase = createClient();` at the start of the async function or the useEffect body where the client is used.

For `useBrand`, change the `refresh` callback to:
```typescript
const refresh = useCallback(async () => {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  // ... rest unchanged
```

For `useAudit`, change `fetchAudit` to:
```typescript
const fetchAudit = useCallback(async () => {
  if (!brandId) { setLoading(false); return; }
  const supabase = createClient();
  const { data: rows, error } = await supabase
  // ... rest unchanged
```

For `useIntegrations`, change the fetch function and subscription:
```typescript
useEffect(() => {
  if (!brandId) { setLoading(false); return; }

  async function fetch() {
    const supabase = createClient();
    const { data, error } = await supabase
    // ... rest unchanged
  }
  fetch();

  const supabase = createClient();
  const channel = supabase
  // ... subscription unchanged

  return () => { supabase.removeChannel(channel); };
}, [brandId]);
```

Apply the same pattern to `useActions` and `useSnapshots`.

- [ ] **Step 2: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add lib/hooks.ts
git commit -m "fix: move Supabase client out of module scope; add useContent, useAgentRuns hooks"
```

---

## Task 7: Rewrite Action Execution to Use Gateway

**Files:**
- Modify: `app/api/actions/execute/route.ts`

- [ ] **Step 1: Replace the static template execution with gateway call**

The current `execute/route.ts` generates static markdown templates. Replace with a gateway content engine call.

Replace the entire file:

```typescript
import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { generateContent, getGenerateJob } from "@/lib/gateway/generate";

interface ExecuteRequest {
  action_id: string;
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body: ExecuteRequest = await request.json();
  const { action_id } = body;

  if (!action_id) {
    return NextResponse.json({ error: "action_id is required" }, { status: 400 });
  }

  // Read action via user session (RLS ensures ownership)
  const { data: action, error: actionErr } = await supabase
    .from("actions")
    .select("*, brands!inner(name, url)")
    .eq("id", action_id)
    .single();

  if (actionErr || !action) {
    return NextResponse.json({ error: "Action not found" }, { status: 404 });
  }

  if (action.approval_state !== "approved") {
    return NextResponse.json({ error: "Action must be approved before execution" }, { status: 400 });
  }

  const serviceClient = await createServiceClient();

  // Mark as executing
  await serviceClient
    .from("actions")
    .update({ execution_state: "executing" })
    .eq("id", action_id);

  try {
    // Determine content format from action type
    const format = mapActionTypeToFormat(action.action_type);
    const brand = action.brands as { name: string; url: string | null };
    const proposed = action.proposed_changes as Record<string, string>;

    // Call gateway content engine
    const job = await generateContent({
      format,
      site: brand.name.toLowerCase().replace(/\s+/g, "-"),
      keyword: proposed.finding || action.intent || action.action_type,
      brand_id: action.brand_id,
    });

    // Poll for completion (up to 90 seconds)
    let result = await getGenerateJob(job.job_id);
    let attempts = 0;
    while (result.status === "pending" || result.status === "running") {
      if (attempts++ > 18) break; // 18 * 5s = 90s
      await new Promise((r) => setTimeout(r, 5000));
      result = await getGenerateJob(job.job_id);
    }

    if (result.status === "completed") {
      // Store result and mark completed
      await serviceClient
        .from("actions")
        .update({
          execution_state: "completed",
          result_summary: {
            gateway_job_id: job.job_id,
            deliverable: typeof result.result === "string" ? result.result : JSON.stringify(result.result),
            artifacts: result.artifacts?.map((a) => a.artifact_id) || [],
          },
          gateway_job_id: job.job_id,
          executed_at: new Date().toISOString(),
        })
        .eq("id", action_id);

      return NextResponse.json({ status: "completed", job_id: job.job_id, result: result.result });
    }

    // Job still running or failed — store partial state
    await serviceClient
      .from("actions")
      .update({
        execution_state: result.status === "failed" ? "failed" : "executing",
        result_summary: { gateway_job_id: job.job_id, error: result.error },
        gateway_job_id: job.job_id,
      })
      .eq("id", action_id);

    return NextResponse.json({
      status: result.status,
      job_id: job.job_id,
      message: result.status === "failed" ? result.error : "Still processing — check back shortly",
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);

    await serviceClient
      .from("actions")
      .update({
        execution_state: "failed",
        result_summary: { error: message },
      })
      .eq("id", action_id);

    return NextResponse.json({ status: "failed", error: message }, { status: 500 });
  }
}

function mapActionTypeToFormat(actionType: string): string {
  switch (actionType) {
    case "update_copy":
    case "fix_cta": return "landing-page";
    case "add_schema": return "blog";
    case "improve_seo": return "blog";
    case "improve_speed": return "blog";
    default: return "blog";
  }
}
```

- [ ] **Step 2: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add app/api/actions/execute/route.ts
git commit -m "feat: replace static action templates with gateway content engine execution"
```

---

## Task 8: Settings Page — Autonomy Dial + Gateway Config

**Files:**
- Modify: `app/(dashboard)/settings/page.tsx`

- [ ] **Step 1: Add AutonomySettings component**

Add this new component inside `settings/page.tsx`, before the closing of the file. Also add it to the settings page render:

First, add the import for the AutonomyMode type at the top:
```typescript
import type { Integration, Audit, AutonomyMode } from "@/lib/types";
```

Add the `Shield` icon to the lucide import:
```typescript
import { Save, User, Link2, Bell, BarChart3, Search, Shield } from "lucide-react";
```

Add this component at the end of the file (before the last closing brace is fine — it's a new standalone function component):

```typescript
function AutonomySettings({ brand }: { brand: ReturnType<typeof useBrand>["brand"] }) {
  const supabase = createClient();
  const [mode, setMode] = useState<AutonomyMode>(
    (brand?.metadata as Record<string, unknown>)?.autonomy_mode as AutonomyMode || "balanced"
  );
  const [saving, setSaving] = useState(false);

  const modes: { value: AutonomyMode; label: string; desc: string }[] = [
    { value: "supervised", label: "Supervised", desc: "All actions require approval" },
    { value: "balanced", label: "Balanced", desc: "Low-risk auto-executes, medium+ needs approval" },
    { value: "autonomous", label: "Autonomous", desc: "Only high-risk actions need approval" },
  ];

  async function handleChange(newMode: AutonomyMode) {
    if (!brand) return;
    setMode(newMode);
    setSaving(true);
    await supabase
      .from("brands")
      .update({ autonomy_mode: newMode })
      .eq("id", brand.id);
    setSaving(false);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-amber" />
          AI Autonomy
        </CardTitle>
      </CardHeader>
      <p className="text-xs text-text-tertiary mb-4">
        Control how much the AI CMO can do without your approval.
      </p>
      <div className="space-y-2">
        {modes.map((m) => (
          <button
            key={m.value}
            onClick={() => handleChange(m.value)}
            disabled={saving}
            className={cn(
              "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors",
              mode === m.value
                ? "bg-amber-dim border border-amber/30"
                : "bg-bg-elevated border border-border hover:border-border-hover"
            )}
          >
            <div className={cn(
              "w-3 h-3 rounded-full border-2",
              mode === m.value ? "border-amber bg-amber" : "border-text-tertiary"
            )} />
            <div>
              <p className="text-sm font-medium">{m.label}</p>
              <p className="text-xs text-text-tertiary">{m.desc}</p>
            </div>
          </button>
        ))}
      </div>
    </Card>
  );
}
```

Then update the render in the `SettingsPage` component to include the new section. After the `NotificationPreferences` block (around line 50), add `AutonomySettings`:

```typescript
{!isOnboarding && (
  <>
    <AutonomySettings brand={brand} />
    <AnalyticsConfiguration brand={brand} integrations={integrations} onConfigUpdated={refreshBrand} />
    <ConnectedAccountsList integrations={integrations} />
    <NotificationPreferences brand={brand} />
  </>
)}
```

- [ ] **Step 2: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add app/\(dashboard\)/settings/page.tsx
git commit -m "feat: add AI autonomy dial to settings page"
```

---

## Task 9: Dashboard Home Page — Mission Control Redesign

**Files:**
- Create: `components/dashboard/attention-items.tsx`
- Create: `components/dashboard/ai-activity.tsx`
- Create: `components/dashboard/quick-actions.tsx`
- Modify: `app/(dashboard)/dashboard/page.tsx`

- [ ] **Step 1: Create AttentionItems component**

Create `components/dashboard/attention-items.tsx`:

```typescript
"use client";

import { useMemo } from "react";
import Link from "next/link";
import { AlertTriangle, Clock, FileText, Link2 } from "lucide-react";
import { timeAgo } from "@/lib/utils";
import type { Action, Integration } from "@/lib/types";

interface AttentionItem {
  id: string;
  icon: typeof AlertTriangle;
  iconColor: string;
  title: string;
  subtitle: string;
  href: string;
}

interface AttentionItemsProps {
  actions: Action[];
  integrations: Integration[];
}

export function AttentionItems({ actions, integrations }: AttentionItemsProps) {
  const items = useMemo(() => {
    const result: AttentionItem[] = [];

    // Pending actions
    const pending = actions.filter((a) => a.approval_state === "pending");
    if (pending.length > 0) {
      result.push({
        id: "pending-actions",
        icon: Clock,
        iconColor: "text-amber",
        title: `${pending.length} action${pending.length > 1 ? "s" : ""} pending approval`,
        subtitle: `Oldest: ${timeAgo(pending[pending.length - 1].created_at)}`,
        href: "/actions",
      });
    }

    // Degraded integrations
    const degraded = integrations.filter(
      (i) => i.status === "degraded" || i.status === "error"
    );
    degraded.forEach((i) => {
      result.push({
        id: `degraded-${i.id}`,
        icon: AlertTriangle,
        iconColor: "text-error",
        title: `${i.provider} connection ${i.status}`,
        subtitle: i.last_sync_at ? `Last sync: ${timeAgo(i.last_sync_at)}` : "Never synced",
        href: "/connect",
      });
    });

    // Draft content
    // Note: this will be populated once content hooks are wired up

    return result;
  }, [actions, integrations]);

  return (
    <div className="card">
      <h3 className="section-title mb-4">Needs Your Attention</h3>
      {items.length === 0 ? (
        <p className="text-text-tertiary text-sm py-4 text-center">All clear</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.id}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-elevated transition-colors"
              >
                <Icon className={`w-4 h-4 ${item.iconColor} flex-shrink-0`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm">{item.title}</p>
                  <p className="text-xs text-text-tertiary">{item.subtitle}</p>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create AIActivity component**

Create `components/dashboard/ai-activity.tsx`:

```typescript
"use client";

import { cn, timeAgo } from "@/lib/utils";
import { Check, X, Loader2, Clock, BarChart3, FileText, Search } from "lucide-react";
import type { AgentRun } from "@/lib/types";

interface AIActivityProps {
  runs: AgentRun[];
  loading: boolean;
}

const statusIcons: Record<string, typeof Check> = {
  completed: Check,
  failed: X,
  running: Loader2,
  pending: Clock,
};

const taskIcons: Record<string, typeof Check> = {
  daily_analytics: BarChart3,
  daily_audit: Search,
  content_generate: FileText,
};

export function AIActivity({ runs, loading }: AIActivityProps) {
  if (loading) {
    return (
      <div className="card">
        <h3 className="section-title mb-4">AI Activity (24h)</h3>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-bg-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  // Filter to last 24 hours
  const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const recent = runs.filter((r) => r.created_at >= cutoff);

  return (
    <div className="card">
      <h3 className="section-title mb-4">AI Activity (24h)</h3>
      {recent.length === 0 ? (
        <p className="text-text-tertiary text-sm py-4 text-center">No agent activity in the last 24 hours</p>
      ) : (
        <div className="space-y-1">
          {recent.map((run) => {
            const StatusIcon = statusIcons[run.status] || Clock;
            const TaskIcon = taskIcons[run.task_type] || FileText;
            const statusColor =
              run.status === "completed" ? "text-success" :
              run.status === "failed" ? "text-error" :
              run.status === "running" ? "text-amber" : "text-text-tertiary";
            const bgColor =
              run.status === "completed" ? "bg-success-dim" :
              run.status === "failed" ? "bg-error-dim" :
              run.status === "running" ? "bg-amber-dim" : "bg-border";

            return (
              <div
                key={run.id}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-elevated transition-colors"
              >
                <div className={cn("w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0", bgColor)}>
                  <StatusIcon className={cn("w-3.5 h-3.5", statusColor)} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">
                    {run.skill || run.task_type.replace(/_/g, " ")}
                  </p>
                  <p className="text-xs text-text-tertiary">
                    {run.trigger} &middot; {timeAgo(run.created_at)}
                  </p>
                </div>
                {run.status === "failed" && run.error && (
                  <span className="text-xs text-error truncate max-w-[120px]">{run.error}</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create QuickActions component**

Create `components/dashboard/quick-actions.tsx`:

```typescript
"use client";

import { useRouter } from "next/navigation";
import {
  FileText, Calendar, Search, Megaphone, Mail, Users,
} from "lucide-react";

interface QuickAction {
  label: string;
  icon: typeof FileText;
  description: string;
  href: string;
}

const quickActions: QuickAction[] = [
  { label: "Write Content", icon: FileText, description: "Blog, email, social, ads", href: "/content?action=write" },
  { label: "Plan Calendar", icon: Calendar, description: "Monthly content calendar", href: "/content?action=calendar" },
  { label: "Audit Page", icon: Search, description: "CRO or SEO audit", href: "/analytics" },
  { label: "Run Ads", icon: Megaphone, description: "Ad campaign copy", href: "/content?action=ads" },
  { label: "Cold Outreach", icon: Mail, description: "Email sequences", href: "/content?action=outreach" },
  { label: "Competitor Intel", icon: Users, description: "Competitive analysis", href: "/content?action=competitors" },
];

export function QuickActions() {
  const router = useRouter();

  return (
    <div className="card">
      <h3 className="section-title mb-4">Quick Actions</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.label}
              onClick={() => router.push(action.href)}
              className="flex flex-col items-center gap-2 p-4 rounded-lg bg-bg-elevated border border-border hover:border-amber/30 hover:bg-amber-dim/30 transition-colors text-center"
            >
              <Icon className="w-5 h-5 text-amber" />
              <div>
                <p className="text-sm font-medium">{action.label}</p>
                <p className="text-[10px] text-text-tertiary">{action.description}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Rewrite the dashboard page to Mission Control layout**

Replace the entire `app/(dashboard)/dashboard/page.tsx`:

```typescript
"use client";

import { useState, useCallback } from "react";
import { useBrand, useAudit, useIntegrations, useActions, useSnapshots, useAgentRuns } from "@/lib/hooks";
import { QuickStats } from "@/components/dashboard/quick-stats";
import { AttentionItems } from "@/components/dashboard/attention-items";
import { AIActivity } from "@/components/dashboard/ai-activity";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { PendingActions } from "@/components/dashboard/pending-actions";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn, scoreColor } from "@/lib/utils";
import { Search, Sparkles } from "lucide-react";
import type { Audit } from "@/lib/types";

export default function DashboardPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { audit, loading: auditLoading, setAudit, refresh: refreshAudit } = useAudit(brand?.id);
  const { integrations } = useIntegrations(brand?.id);
  const { actions, refresh: refreshActions } = useActions(brand?.id);
  const { snapshots } = useSnapshots(brand?.id);
  const { runs, loading: runsLoading } = useAgentRuns(brand?.id);
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);

  const runAudit = useCallback(async () => {
    if (!brand?.id || auditRunning) return;
    setAuditRunning(true);
    setAuditError(null);

    try {
      const res = await fetch("/api/audits/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: brand.id, domain: brand.url }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAuditError(data.error || "Audit failed");
        return;
      }
      const newAudit: Audit = {
        id: data.audit_id,
        brand_id: brand.id,
        overall_score: data.overall_score,
        category_scores: data.category_scores || {},
        findings: data.findings || [],
        metadata: {},
        created_at: data.created_at || new Date().toISOString(),
      };
      setAudit(newAudit);
    } catch {
      setAuditError("Network error. Please try again.");
    } finally {
      setAuditRunning(false);
    }
  }, [brand, auditRunning, setAudit]);

  const [generating, setGenerating] = useState(false);
  const handleGenerate = useCallback(async () => {
    if (!brand?.id) return;
    setGenerating(true);
    try {
      await fetch("/api/actions/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: brand.id, source: "audit" }),
      });
      await refreshActions();
    } finally {
      setGenerating(false);
    }
  }, [brand?.id, refreshActions]);

  if (brandLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (!brand) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h2 className="font-display text-2xl font-semibold mb-2">Welcome to MeetKai</h2>
        <p className="text-text-secondary mb-6">Set up your business profile to get started.</p>
        <a href="/settings?onboarding=true" className="inline-flex items-center px-6 py-3 bg-amber text-background font-semibold rounded-[12px] hover:bg-amber-light transition-colors">
          Set up your profile
        </a>
      </div>
    );
  }

  const displayAudit = auditLoading ? null : audit;
  const score = displayAudit?.overall_score;

  return (
    <div className="space-y-6">
      {/* Hero: Score + Brand + Actions */}
      <div className="card flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex items-center gap-4 flex-1">
          {/* Score ring */}
          <div className="relative w-16 h-16 flex-shrink-0">
            <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
              <path
                d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#1e1e1e"
                strokeWidth="3"
              />
              {score != null && (
                <path
                  d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke={score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444"}
                  strokeWidth="3"
                  strokeDasharray={`${score}, 100`}
                  strokeLinecap="round"
                />
              )}
            </svg>
            <span className={cn(
              "absolute inset-0 flex items-center justify-center font-mono text-lg font-bold",
              score != null ? scoreColor(score) : "text-text-tertiary"
            )}>
              {score != null ? Math.round(score) : "—"}
            </span>
          </div>
          <div>
            <h1 className="font-display text-xl font-bold tracking-tight">{brand.name}</h1>
            <p className="text-text-secondary text-sm">{brand.url || "No website set"}</p>
            {score != null && (
              <p className="text-xs text-text-tertiary mt-0.5">Marketing Health Score</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={runAudit} loading={auditRunning}>
            <Search className="w-3.5 h-3.5" />
            Run Audit
          </Button>
          {audit && actions.filter((a) => a.approval_state === "pending").length === 0 && (
            <Button variant="primary" size="sm" onClick={handleGenerate} loading={generating}>
              <Sparkles className="w-3.5 h-3.5" />
              Generate Actions
            </Button>
          )}
        </div>
      </div>

      {/* Audit error */}
      {auditError && (
        <div className="bg-error-dim border border-error/20 rounded-[12px] px-4 py-3 text-sm text-error">
          {auditError}
        </div>
      )}

      {/* Quick stats */}
      <QuickStats audit={displayAudit} integrations={integrations} actions={actions} snapshots={snapshots} />

      {/* Two-column: Attention + AI Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AttentionItems actions={actions} integrations={integrations} />
        <AIActivity runs={runs} loading={runsLoading} />
      </div>

      {/* Quick actions */}
      <QuickActions />

      {/* Pending actions (compact, top 5) */}
      <PendingActions actions={actions} />
    </div>
  );
}
```

- [ ] **Step 5: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add components/dashboard/attention-items.tsx components/dashboard/ai-activity.tsx components/dashboard/quick-actions.tsx app/\(dashboard\)/dashboard/page.tsx
git commit -m "feat: redesign dashboard to mission control — score hero, attention items, AI activity, quick actions"
```

---

## Task 10: Content & Actions Merged Page

**Files:**
- Create: `app/(dashboard)/content/page.tsx`

- [ ] **Step 1: Create the content page**

Create `app/(dashboard)/content/page.tsx`:

```typescript
"use client";

import { useState, useCallback } from "react";
import { useBrand, useActions, useContent } from "@/lib/hooks";
import { Tabs } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge, RiskBadge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { cn, timeAgo } from "@/lib/utils";
import type { Action, Content } from "@/lib/types";
import { Check, X, ChevronDown, ChevronUp, FileText, Sparkles, Play, Eye } from "lucide-react";

export default function ContentPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { actions, loading: actionsLoading, refresh: refreshActions } = useActions(brand?.id);
  const { content, loading: contentLoading, refresh: refreshContent } = useContent(brand?.id);
  const [activeTab, setActiveTab] = useState("pending");

  const pending = actions.filter((a) => a.approval_state === "pending");
  const inProgress = actions.filter((a) => a.execution_state === "executing");
  const completed = actions.filter((a) => a.execution_state === "completed");

  const tabs = [
    { id: "pending", label: "Pending", count: pending.length },
    { id: "in-progress", label: "In Progress", count: inProgress.length },
    { id: "completed", label: "Completed", count: completed.length },
    { id: "library", label: "Content Library", count: content.length },
  ];

  const filtered =
    activeTab === "pending" ? pending :
    activeTab === "in-progress" ? inProgress :
    activeTab === "completed" ? completed : [];

  if (brandLoading || actionsLoading || contentLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-12 w-full" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">Content & Actions</h1>
          <p className="text-text-secondary text-sm mt-1">
            AI-generated content and marketing actions.
          </p>
        </div>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "library" ? (
        <ContentLibrary content={content} />
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-text-tertiary">
          <FileText className="w-10 h-10 mb-3 opacity-30" />
          <p className="text-sm">No {activeTab.replace("-", " ")} items</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((action) => (
            <ActionCard
              key={action.id}
              action={action}
              showActions={activeTab === "pending"}
              onUpdate={() => { refreshActions(); refreshContent(); }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ContentLibrary({ content }: { content: Content[] }) {
  if (content.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 text-text-tertiary">
        <FileText className="w-10 h-10 mb-3 opacity-30" />
        <p className="text-sm">No content generated yet</p>
        <p className="text-xs mt-1">Content will appear here after actions are executed.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {content.map((item) => (
        <ContentCard key={item.id} item={item} />
      ))}
    </div>
  );
}

function ContentCard({ item }: { item: Content }) {
  const [expanded, setExpanded] = useState(false);
  const gateReport = item.gate_report as Record<string, unknown> | null;
  const fourUsScore = gateReport?.four_us_total as number | undefined;

  return (
    <Card>
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <h3 className="text-sm font-semibold">{item.title || "Untitled"}</h3>
            <Badge status={item.status} />
            <span className="text-xs text-text-tertiary capitalize">{item.format}</span>
            {item.skill && (
              <span className="text-xs text-text-tertiary">{item.skill}</span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-text-tertiary">
            <span>{timeAgo(item.created_at)}</span>
            {fourUsScore != null && (
              <span className={cn(
                "font-mono font-semibold",
                fourUsScore >= 12 ? "text-success" : fourUsScore >= 10 ? "text-amber" : "text-error"
              )}>
                4U: {fourUsScore}/16
              </span>
            )}
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-2 text-text-tertiary hover:text-foreground transition-colors"
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>
      {expanded && item.body && (
        <div className="mt-4 pt-4 border-t border-border">
          <pre className="text-xs font-mono bg-bg-elevated rounded-lg p-3 overflow-x-auto text-text-secondary whitespace-pre-wrap max-h-96 overflow-y-auto">
            {item.body}
          </pre>
        </div>
      )}
    </Card>
  );
}

function ActionCard({
  action,
  showActions,
  onUpdate,
}: {
  action: Action;
  showActions: boolean;
  onUpdate: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const supabase = createClient();

  async function handleApprove() {
    setLoading("approved");
    try {
      await supabase
        .from("actions")
        .update({ approval_state: "approved" })
        .eq("id", action.id);
      await fetch("/api/actions/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: action.id }),
      });
      onUpdate();
    } finally {
      setLoading(null);
    }
  }

  async function handleReject() {
    setLoading("rejected");
    try {
      await supabase
        .from("actions")
        .update({ approval_state: "rejected" })
        .eq("id", action.id);
      onUpdate();
    } finally {
      setLoading(null);
    }
  }

  const resultSummary = action.result_summary as Record<string, unknown> | null;

  return (
    <Card>
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <h3 className="text-sm font-semibold">{action.intent || action.action_type}</h3>
            <RiskBadge tier={action.risk_tier} />
            <Badge status={action.approval_state} />
            {action.execution_state !== "pending" && (
              <Badge status={action.execution_state} label={action.execution_state} />
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-text-tertiary">
            <span className="capitalize">{action.channel}</span>
            <span className="capitalize">{action.action_type.replace(/_/g, " ")}</span>
            <span>{timeAgo(action.created_at)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {showActions && (
            <>
              <Button variant="primary" size="sm" onClick={handleApprove} loading={loading === "approved"}>
                <Play className="w-4 h-4" />
                Approve
              </Button>
              <Button variant="danger" size="sm" onClick={handleReject} loading={loading === "rejected"}>
                <X className="w-4 h-4" />
              </Button>
            </>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 text-text-tertiary hover:text-foreground transition-colors"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>
      {expanded && (
        <div className="mt-4 pt-4 border-t border-border space-y-3">
          {Object.keys(action.proposed_changes).length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-text-secondary mb-2">Proposed Changes</h4>
              <pre className="text-xs font-mono bg-bg-elevated rounded-lg p-3 overflow-x-auto text-text-secondary">
                {JSON.stringify(action.proposed_changes, null, 2)}
              </pre>
            </div>
          )}
          {resultSummary && (
            <div>
              <h4 className="text-xs font-medium text-text-secondary mb-2">Result</h4>
              {typeof resultSummary.deliverable === "string" ? (
                <pre className="text-xs font-mono bg-bg-elevated rounded-lg p-3 overflow-x-auto text-text-secondary whitespace-pre-wrap">
                  {resultSummary.deliverable}
                </pre>
              ) : (
                <pre className="text-xs font-mono bg-bg-elevated rounded-lg p-3 overflow-x-auto text-text-secondary">
                  {JSON.stringify(resultSummary, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
```

- [ ] **Step 2: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add app/\(dashboard\)/content/page.tsx
git commit -m "feat: add content & actions merged page with library, pending, in-progress, completed tabs"
```

---

## Task 11: Chat Panel — API Route

**Files:**
- Create: `app/api/chat/route.ts`

- [ ] **Step 1: Create the chat API route with tool definitions**

Create `app/api/chat/route.ts`:

```typescript
import { streamText, tool } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { z } from "zod";
import { createClient } from "@/lib/supabase/server";
import { gateway } from "@/lib/gateway/client";

export const maxDuration = 60;

export async function POST(req: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return new Response("Unauthorized", { status: 401 });
  }

  // Get brand context
  const { data: brands } = await supabase
    .from("brands")
    .select("id, name, url, archetype, metadata")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false })
    .limit(1);
  const brand = brands?.[0];

  // Get latest audit score
  let auditScore: number | null = null;
  if (brand) {
    const { data: audits } = await supabase
      .from("audits")
      .select("overall_score")
      .eq("brand_id", brand.id)
      .order("created_at", { ascending: false })
      .limit(1);
    auditScore = audits?.[0]?.overall_score ?? null;
  }

  // Get connected channels
  let connectedChannels: string[] = [];
  if (brand) {
    const { data: integrations } = await supabase
      .from("integrations")
      .select("provider, channel")
      .eq("brand_id", brand.id)
      .eq("status", "connected");
    connectedChannels = (integrations || []).map((i) => `${i.provider} (${i.channel})`);
  }

  const { messages } = await req.json();

  const systemPrompt = [
    `You are Kai, an AI CMO assistant for ${brand?.name || "a business"}.`,
    brand?.url ? `Website: ${brand.url}` : "",
    brand?.archetype ? `Business type: ${brand.archetype}` : "",
    auditScore != null ? `Current marketing health score: ${auditScore}/100` : "No audit run yet.",
    connectedChannels.length > 0 ? `Connected channels: ${connectedChannels.join(", ")}` : "No channels connected yet.",
    "",
    "You help the business owner understand their marketing performance and take action.",
    "Use tools to fetch data and execute marketing tasks. Be concise and actionable.",
    "When the user asks to create content, use the generate_content tool.",
    "When they ask about their score or marketing health, use get_score.",
  ].filter(Boolean).join("\n");

  const result = streamText({
    model: anthropic("claude-sonnet-4-20250514"),
    system: systemPrompt,
    messages,
    tools: {
      run_audit: tool({
        description: "Run a marketing audit on the user's website",
        parameters: z.object({
          domain: z.string().optional().describe("Domain to audit (uses brand URL if omitted)"),
        }),
        execute: async ({ domain }) => {
          if (!brand) return { error: "No brand profile found. Set up your profile first." };
          try {
            const res = await gateway(`/kai-operator/audit/${brand.id}`, {
              params: { scope: "full" },
              timeout: 120000,
            });
            return { success: true, data: res };
          } catch (e) {
            return { error: e instanceof Error ? e.message : "Audit failed" };
          }
        },
      }),
      generate_content: tool({
        description: "Generate marketing content (blog, email, social, ads, landing page)",
        parameters: z.object({
          format: z.enum(["blog", "email", "cold-email", "linkedin", "meta-ads", "google-ads", "tiktok", "landing-page", "press"]),
          keyword: z.string().describe("Topic or keyword for the content"),
          persona: z.string().optional().describe("Target persona"),
        }),
        execute: async ({ format, keyword, persona }) => {
          if (!brand) return { error: "No brand profile found." };
          try {
            const res = await gateway("/generate", {
              method: "POST",
              body: {
                format,
                keyword,
                persona,
                site: brand.name.toLowerCase().replace(/\s+/g, "-"),
                brand_id: brand.id,
                surface: "remote",
              },
              timeout: 60000,
            });
            return { success: true, data: res };
          } catch (e) {
            return { error: e instanceof Error ? e.message : "Generation failed" };
          }
        },
      }),
      get_analytics: tool({
        description: "Get current analytics data (traffic, rankings, performance)",
        parameters: z.object({
          channel: z.enum(["ga4", "gsc", "all"]).default("all"),
        }),
        execute: async () => {
          if (!brand) return { error: "No brand profile found." };
          try {
            const res = await gateway("/webhooks/analytics/summary", {
              method: "POST",
              body: { client: brand.name.toLowerCase().replace(/\s+/g, "-") },
            });
            return { success: true, data: res };
          } catch (e) {
            return { error: e instanceof Error ? e.message : "Analytics fetch failed" };
          }
        },
      }),
      propose_actions: tool({
        description: "Generate action proposals from latest audit findings",
        parameters: z.object({}),
        execute: async () => {
          if (!brand) return { error: "No brand profile found." };
          try {
            const res = await gateway("/ops/dashboard", {
              params: { brand_id: brand.id },
            });
            return { success: true, data: res };
          } catch (e) {
            return { error: e instanceof Error ? e.message : "Failed to get proposals" };
          }
        },
      }),
      approve_action: tool({
        description: "Approve a pending action by ID",
        parameters: z.object({
          action_id: z.string().describe("The action ID to approve"),
        }),
        execute: async ({ action_id }) => {
          try {
            const res = await gateway(`/ops/proposals/${action_id}/approve`, {
              method: "POST",
            });
            return { success: true, data: res };
          } catch (e) {
            return { error: e instanceof Error ? e.message : "Approval failed" };
          }
        },
      }),
      get_score: tool({
        description: "Get current marketing health score and breakdown",
        parameters: z.object({}),
        execute: async () => {
          if (!brand) return { error: "No brand profile found." };
          const { data: audits } = await supabase
            .from("audits")
            .select("overall_score, category_scores, findings, created_at")
            .eq("brand_id", brand.id)
            .order("created_at", { ascending: false })
            .limit(1);
          const latest = audits?.[0];
          if (!latest) return { score: null, message: "No audit has been run yet." };
          return {
            score: latest.overall_score,
            categories: latest.category_scores,
            finding_count: Array.isArray(latest.findings) ? latest.findings.length : 0,
            audited_at: latest.created_at,
          };
        },
      }),
      run_skill: tool({
        description: "Run a specific Kai marketing skill",
        parameters: z.object({
          skill: z.enum([
            "kai-seo-audit", "kai-cro", "kai-landing-page", "kai-email-system",
            "kai-ad-campaign", "kai-social", "kai-cold-outreach", "kai-competitors",
            "kai-content-calendar", "kai-brand", "kai-growth-plan",
          ]),
          context: z.string().optional().describe("Additional context for the skill"),
        }),
        execute: async ({ skill, context }) => {
          if (!brand) return { error: "No brand profile found." };
          try {
            const res = await gateway("/generate", {
              method: "POST",
              body: {
                format: skill,
                keyword: context || brand.name,
                site: brand.name.toLowerCase().replace(/\s+/g, "-"),
                brand_id: brand.id,
                surface: "remote",
              },
              timeout: 60000,
            });
            return { success: true, data: res };
          } catch (e) {
            return { error: e instanceof Error ? e.message : "Skill execution failed" };
          }
        },
      }),
    },
  });

  return result.toDataStreamResponse();
}
```

- [ ] **Step 2: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add app/api/chat/route.ts
git commit -m "feat: add Vercel AI SDK chat route with 7 gateway-connected tools"
```

---

## Task 12: Chat Panel — UI Components

**Files:**
- Create: `components/chat/chat-panel.tsx`
- Create: `components/chat/message.tsx`
- Create: `components/chat/tool-result.tsx`

- [ ] **Step 1: Create ToolResult component**

Create `components/chat/tool-result.tsx`:

```typescript
"use client";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Check, X, BarChart3, FileText, Search, Sparkles } from "lucide-react";

interface ToolResultProps {
  toolName: string;
  result: Record<string, unknown>;
}

export function ToolResult({ toolName, result }: ToolResultProps) {
  if (result.error) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-error-dim rounded-lg text-xs text-error">
        <X className="w-3.5 h-3.5 flex-shrink-0" />
        <span>{String(result.error)}</span>
      </div>
    );
  }

  switch (toolName) {
    case "get_score": {
      const score = result.score as number | null;
      return (
        <div className="flex items-center gap-3 px-3 py-2.5 bg-bg-elevated rounded-lg">
          <BarChart3 className="w-4 h-4 text-amber" />
          <div>
            <span className={cn(
              "font-mono font-bold text-lg",
              score != null && score >= 70 ? "text-success" :
              score != null && score >= 40 ? "text-amber" : "text-error"
            )}>
              {score != null ? `${Math.round(score)}/100` : "No score"}
            </span>
            {result.finding_count != null && (
              <span className="text-xs text-text-tertiary ml-2">
                {String(result.finding_count)} findings
              </span>
            )}
          </div>
        </div>
      );
    }
    case "generate_content":
    case "run_skill": {
      const data = result.data as Record<string, unknown> | undefined;
      return (
        <div className="flex items-center gap-2 px-3 py-2.5 bg-bg-elevated rounded-lg text-xs">
          <FileText className="w-4 h-4 text-amber flex-shrink-0" />
          <div>
            <p className="text-sm font-medium">Job queued</p>
            {data?.job_id && <p className="text-text-tertiary">ID: {String(data.job_id)}</p>}
          </div>
        </div>
      );
    }
    case "run_audit": {
      return (
        <div className="flex items-center gap-2 px-3 py-2.5 bg-bg-elevated rounded-lg text-xs">
          <Search className="w-4 h-4 text-amber flex-shrink-0" />
          <span className="text-sm">Audit running...</span>
        </div>
      );
    }
    default:
      return (
        <div className="flex items-center gap-2 px-3 py-2.5 bg-bg-elevated rounded-lg text-xs">
          <Check className="w-3.5 h-3.5 text-success flex-shrink-0" />
          <span className="text-text-secondary truncate">
            {JSON.stringify(result).slice(0, 100)}
          </span>
        </div>
      );
  }
}
```

- [ ] **Step 2: Create Message component**

Create `components/chat/message.tsx`:

```typescript
"use client";

import type { Message } from "ai";
import { cn } from "@/lib/utils";
import { ToolResult } from "./tool-result";
import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className={cn(
        "w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0",
        isUser ? "bg-amber-dim" : "bg-bg-elevated"
      )}>
        {isUser ? (
          <User className="w-3.5 h-3.5 text-amber" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-text-secondary" />
        )}
      </div>
      <div className={cn("max-w-[85%] space-y-2", isUser ? "items-end" : "items-start")}>
        {/* Text content */}
        {message.content && (
          <div className={cn(
            "px-3 py-2 rounded-lg text-sm",
            isUser
              ? "bg-amber text-background rounded-tr-none"
              : "bg-bg-elevated text-foreground rounded-tl-none"
          )}>
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        )}

        {/* Tool invocations */}
        {message.toolInvocations?.map((invocation) => (
          <div key={invocation.toolCallId} className="w-full">
            {invocation.state === "result" && (
              <ToolResult
                toolName={invocation.toolName}
                result={invocation.result as Record<string, unknown>}
              />
            )}
            {invocation.state === "call" && (
              <div className="flex items-center gap-2 px-3 py-2 bg-bg-elevated rounded-lg text-xs text-text-tertiary animate-pulse">
                <span>Calling {invocation.toolName}...</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create ChatPanel component**

Create `components/chat/chat-panel.tsx`:

```typescript
"use client";

import { useChat } from "ai/react";
import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "./message";
import { cn } from "@/lib/utils";
import { MessageSquare, X, Send, Loader2 } from "lucide-react";

export function ChatPanel() {
  const [open, setOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: "/api/chat",
    initialMessages: [
      {
        id: "welcome",
        role: "assistant",
        content: "Hey! I'm Kai, your AI CMO. Ask me about your marketing score, or tell me to write content, run an audit, or generate action proposals.",
      },
    ],
  });

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          "fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full flex items-center justify-center shadow-lg transition-colors",
          open ? "bg-card border border-border" : "bg-amber hover:bg-amber-light"
        )}
      >
        {open ? (
          <X className="w-5 h-5 text-foreground" />
        ) : (
          <MessageSquare className="w-5 h-5 text-background" />
        )}
      </button>

      {/* Chat panel */}
      <div className={cn(
        "fixed bottom-20 right-6 z-50 w-96 h-[600px] max-h-[80vh] bg-card border border-border rounded-[16px] shadow-2xl flex flex-col transition-all duration-200",
        open ? "opacity-100 scale-100 translate-y-0" : "opacity-0 scale-95 translate-y-4 pointer-events-none"
      )}>
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <div className="w-8 h-8 rounded-full bg-amber-dim flex items-center justify-center">
            <MessageSquare className="w-4 h-4 text-amber" />
          </div>
          <div>
            <p className="text-sm font-semibold">Kai</p>
            <p className="text-[10px] text-text-tertiary">AI CMO Assistant</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isLoading && messages[messages.length - 1]?.role === "user" && (
            <div className="flex items-center gap-2 text-text-tertiary text-xs">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-3 border-t border-border">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={handleInputChange}
              placeholder="Ask Kai anything..."
              className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-text-tertiary focus:outline-none focus:border-amber transition-colors"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="p-2 bg-amber text-background rounded-lg hover:bg-amber-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
```

- [ ] **Step 4: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add components/chat/
git commit -m "feat: add chat panel UI — message renderer, tool result cards, slide-out panel"
```

---

## Task 13: Layout and Sidebar Updates

**Files:**
- Modify: `app/(dashboard)/layout.tsx`
- Modify: `components/layout/sidebar.tsx`

- [ ] **Step 1: Add ChatPanel to dashboard layout**

Update `app/(dashboard)/layout.tsx` — add the chat panel import and render it:

```typescript
import { createClient } from "@/lib/supabase/server";
import { Sidebar } from "@/components/layout/sidebar";
import { ChatPanel } from "@/components/chat/chat-panel";
import { Toaster } from "sonner";

export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  return (
    <div className="min-h-screen">
      <Sidebar userEmail={user?.email} />
      <main className="lg:pl-60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-16 lg:pt-8">
          {children}
        </div>
      </main>
      <ChatPanel />
      <Toaster
        theme="dark"
        toastOptions={{
          style: {
            background: "#141414",
            border: "1px solid #1e1e1e",
            color: "#fafafa",
          },
        }}
      />
    </div>
  );
}
```

- [ ] **Step 2: Add Content nav item to sidebar**

In `components/layout/sidebar.tsx`, update the `navItems` array — add Content between Actions and Analytics:

```typescript
const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/connect", label: "Connect", icon: Link2 },
  { href: "/content", label: "Content", icon: FileText },
  { href: "/actions", label: "Actions", icon: Zap },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];
```

Also add `FileText` to the lucide imports:

```typescript
import {
  LayoutDashboard,
  Link2,
  Zap,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  FileText,
} from "lucide-react";
```

- [ ] **Step 3: Verify and commit**

```bash
cd app-meetkai && npx tsc --noEmit
git add app/\(dashboard\)/layout.tsx components/layout/sidebar.tsx
git commit -m "feat: add chat panel to layout, add Content nav item to sidebar"
```

---

## Task 14: Final Build Verification

- [ ] **Step 1: Run full TypeScript check**

```bash
cd app-meetkai && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 2: Run linter**

```bash
cd app-meetkai && npx next lint
```

Fix any lint errors that appear.

- [ ] **Step 3: Run build**

```bash
cd app-meetkai && npx next build
```

Expected: build succeeds with no errors. There may be warnings about dynamic routes — that's expected.

- [ ] **Step 4: Commit any lint fixes**

```bash
git add -A
git commit -m "fix: lint and build fixes"
```

---

## Verification Plan

### Manual Testing Checklist

After the build succeeds, start the dev server (`pnpm dev`) and verify:

1. **Dashboard home**: Score hero shows correctly (including score=0). Attention items list pending actions and degraded integrations. AI Activity shows "No agent activity" (empty state). Quick Actions grid with 6 cards links to correct pages.

2. **Quick stats**: Score of 0 shows "0" not "—". Connected count, pending count, sessions all display correctly.

3. **Settings**: Autonomy dial renders with 3 modes. Selecting a mode updates the brand. GSC integration lookup finds the correct provider by `"gsc"` (not `"google_search_console"`).

4. **Content page**: 4 tabs (Pending, In Progress, Completed, Library). Pending tab shows actions with Approve/Reject buttons. Approve triggers gateway execution. Library shows content items with quality gate scores.

5. **Chat panel**: Floating button in bottom-right. Opens slide-out panel. Can type "What's my score?" and get a tool call response. Can type "Write a blog post about AI receptionists" and get a generation job queued.

6. **Actions page**: Risk tiers show correctly — critical findings generate "high" risk actions.

7. **Analytics page**: GSC data shows when GSC integration exists with provider `"gsc"`.

8. **Sidebar**: Content nav item appears between Connect and Actions.

9. **Chat persistence**: Chat panel stays open when navigating between pages.

### Database

Run `004_agentic.sql` against Supabase. Verify:
- `content`, `chat_messages`, `agent_runs` tables exist
- `actions.skill`, `actions.gateway_job_id`, `actions.trigger` columns exist
- `brands.autonomy_mode`, `brands.gateway_url`, `brands.gateway_key` columns exist
- RLS policies prevent cross-brand access
