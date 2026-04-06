# Agent Prompt: Design & Build the MeetKai Client Dashboard

## Who you are

You are building `app.meetkai.xyz` — a client-facing AI CMO dashboard. This is the product surface where businesses connect their marketing accounts, see what an AI CMO finds, approve recommended actions, and watch results.

## The product in one sentence

A business owner submits their domain for a free marketing audit → gets a magic link to a dashboard → sees their audit score → connects Google Analytics / Search Console / social / email → gets live data + AI-generated marketing proposals they can approve with one click.

## The funnel

```
meetkai.xyz (landing page)
  → Free audit form (domain + email + name)
    → MiKai audit engine runs (7 categories, scores 0-100)
      → Email with magic link to app.meetkai.xyz
        → Dashboard: audit results + "connect accounts" CTA
          → Pipedream OAuth connects their GA4, GSC, social, email
            → Live data feeds into dashboard
              → AI proposes marketing actions (fix CTA, update copy, send email, post to social)
                → Owner approves/rejects
                  → Approved actions execute through Pipedream
                    → Results shown in dashboard
```

## What already exists (backend — DO NOT rebuild these)

### FastAPI Gateway (`gateway/`)
Running on the Hetzner VPS. These endpoints are live and tested:

**Connection management** (`/connections/`):
- `POST /connections/connect` — initiate OAuth flow, returns Pipedream connect link URL
- `POST /connections/confirm` — confirm OAuth completion, maps account to brand
- `POST /connections/{id}/verify` — check connection health
- `POST /connections/{id}/reconnect` — re-auth expired connections
- `POST /connections/{id}/disconnect` — disconnect preserving history
- `GET /connections/status/{brand_id}` — full connection status summary
- `POST /connections/verify-all/{brand_id}` — verify all integrations
- `GET /connections/health/{brand_id}` — health dashboard data
- `POST /connections/sync/{brand_id}` — sync all channel state
- `POST /connections/onboarding/checklist` — get connection checklist for a business
- `GET /connections/onboarding/status/{brand_id}` — onboarding progress
- `POST /connections/webhooks/pipedream/connect` — receives Pipedream OAuth callbacks

**Action management** (`/ops/`):
- `POST /ops/propose` — create action proposal
- `POST /ops/{id}/approve` — approve action
- `POST /ops/{id}/reject` — reject action
- `POST /ops/{id}/execute` — execute approved action
- `GET /ops/{id}` — get action details
- `GET /ops/pending` — list pending approvals

**Runtime** (`/runtime/`):
- Brand profiles, workspace metadata, run records

All endpoints require `X-API-Key` header.

### Pipedream Connect (live, tested)
- Project ID: `proj_jBs2MK1`
- Python SDK installed, credentials configured
- OAuth flows working — we've connected Google Analytics and pulled real data
- Supported providers: GA4, GSC, GitHub, WordPress, Shopify, Facebook, Instagram, LinkedIn, TikTok, YouTube, Mailchimp, Loops, SendGrid, Google Ads, Meta Ads

### MiKai Audit Engine (live)
- Runs at `meetkai.xyz/api/mikai/`
- Accepts domain + email + name
- Produces audit with scores across 7 categories
- Stores results as JSON + markdown on server
- Sends delivery email via Loops

### Data already flowing
- KaiCalls GA4: 1,282 sessions, 947 users, 31 conversions (last 28 days)
- Starrs Party GA4: 427 sessions, 360 users (last 28 days)
- Both registered in IntegrationRegistry with `connected_account_id`

## Infrastructure

| Component | Detail |
|-----------|--------|
| Server | 89.167.60.171 (Hetzner, Ubuntu 24.04, 16GB RAM) |
| Domain | `app.meetkai.xyz` (new subdomain — add block to `/etc/caddy/Caddyfile` and reload) |
| Reverse proxy | Caddy |
| Auth | **Supabase Auth** — magic links built-in, no custom JWT needed |
| API | FastAPI gateway on same server (port 8088) |
| Database | **Supabase Postgres** — users, brands, integrations, actions, audit results |
| Realtime | Supabase Realtime subscriptions (for live action status updates) |

## What you need to build

### 1. Next.js App (`app.meetkai.xyz`)

**Tech stack:**
- Next.js 14+ (App Router)
- Tailwind CSS
- Dark-first design (matches existing meetkai.xyz aesthetic)
- Deployed on the Hetzner VPS via PM2 or systemd

**Pages:**

#### `/` — Landing / Login
- If not authenticated: "Enter your email to access your dashboard" → sends magic link
- If authenticated: redirect to `/dashboard`

#### `/auth/verify?token=xxx` — Magic link handler
- Validates token, creates session (JWT cookie), redirects to `/dashboard`

#### `/dashboard` — Main dashboard
- **Audit score card** — overall score + per-category breakdown (from MiKai audit data)
- **Connected accounts** — status indicators for each channel (green/yellow/red/gray)
- **Quick stats** — sessions, users, conversions, bounce rate (from GA4 via `/connections/sync`)
- **Pending actions** — list of AI-proposed marketing actions awaiting approval
- **Recent activity** — execution log of completed actions

#### `/connect` — Account connection hub
- Shows the onboarding checklist (from `/connections/onboarding/checklist`)
- Each integration has a "Connect" button that:
  1. Calls `POST /connections/connect` to get a Pipedream connect link
  2. Opens the link in a popup/new tab for OAuth
  3. On success webhook, updates status to connected
- Shows connection health for already-connected accounts
- "Verify All" button

#### `/actions` — Action queue
- **Pending** tab — proposed actions with approve/reject buttons
- **Completed** tab — executed actions with results
- **Failed** tab — failed executions with error details
- Each action card shows:
  - Channel icon + action type
  - Intent (what it does, in plain English)
  - Risk tier badge (low/medium/high)
  - Proposed changes preview
  - Approve / Reject buttons (pending only)
  - Result summary (completed only)

#### `/analytics` — Analytics deep dive
- GA4 traffic chart (28 days)
- Top pages
- Traffic sources
- Conversion events
- Search Console: top queries, impressions, clicks, CTR
- All pulled via `/connections/sync` → Pipedream proxy → GA4/GSC APIs

#### `/settings` — Account settings
- Business profile (name, URL, category)
- Connected accounts management
- Notification preferences
- API key (for power users)

### 2. Supabase Backend

**Auth** — use Supabase Auth with magic links (built-in, zero custom code):
1. User enters email on `/` → `supabase.auth.signInWithOtp({ email })`
2. Supabase sends magic link email automatically
3. User clicks link → Supabase handles verification → session cookie set
4. All subsequent requests include Supabase session automatically
5. MiKai audit email also includes a link with `?email=xxx` that pre-fills the login

**Database tables (Supabase Postgres):**

```sql
-- Users get auto-created by Supabase Auth

-- Brands (one per business)
create table brands (
  id text primary key,
  user_id uuid references auth.users(id),
  name text not null,
  domain text,
  archetype text default 'local_service',
  created_at timestamptz default now()
);

-- Audit results (from MiKai)
create table audits (
  id uuid primary key default gen_random_uuid(),
  brand_id text references brands(id),
  domain text not null,
  overall_score integer,
  category_scores jsonb,
  findings jsonb,
  created_at timestamptz default now()
);

-- Connected integrations (mirrors IntegrationRegistry)
create table integrations (
  id text primary key,
  brand_id text references brands(id),
  channel text not null,
  provider text not null,
  status text default 'pending_auth',
  connected_account_id text,
  capabilities text[],
  scopes text[],
  config jsonb default '{}',
  last_verified_at timestamptz,
  last_sync_at timestamptz,
  last_error text,
  kill_switch boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Action proposals
create table actions (
  id text primary key,
  brand_id text references brands(id),
  channel text,
  action_type text,
  intent text,
  proposed_changes jsonb,
  risk_tier text default 'low',
  approval_state text default 'pending',
  execution_state text default 'pending',
  result_summary jsonb,
  created_at timestamptz default now(),
  executed_at timestamptz
);

-- Channel state snapshots (from sync)
create table channel_snapshots (
  id uuid primary key default gen_random_uuid(),
  brand_id text references brands(id),
  channel text,
  provider text,
  data jsonb,
  synced_at timestamptz default now()
);

-- Row-level security: users can only see their own brands
alter table brands enable row level security;
create policy "Users see own brands" on brands
  for all using (user_id = auth.uid());

alter table integrations enable row level security;
create policy "Users see own integrations" on integrations
  for all using (brand_id in (select id from brands where user_id = auth.uid()));

alter table actions enable row level security;
create policy "Users see own actions" on actions
  for all using (brand_id in (select id from brands where user_id = auth.uid()));

alter table audits enable row level security;
create policy "Users see own audits" on audits
  for all using (brand_id in (select id from brands where user_id = auth.uid()));

alter table channel_snapshots enable row level security;
create policy "Users see own snapshots" on channel_snapshots
  for all using (brand_id in (select id from brands where user_id = auth.uid()));
```

**Row-level security** means the frontend can query Supabase directly for reads (audit scores, action history, integration status) without a proxy layer. Writes (approve action, trigger sync) go through the Next.js API routes → FastAPI gateway.

**Brand mapping:**
- When a user signs in, look up their email in `brands` table
- If no brand exists but a MiKai audit exists for their domain, auto-create the brand and import audit results
- If nothing exists, show onboarding flow

### 3. API Proxy Layer

The Next.js app needs a thin API route layer for **write operations** (connecting accounts, approving actions, triggering syncs). Reads can go directly to Supabase from the browser via RLS.

**Write path (Next.js API routes → FastAPI gateway):**
```
Browser → POST /api/connections/connect
  → Next.js route validates Supabase session, gets brand_id from DB
  → calls FastAPI gateway (localhost:8088/connections/connect) with X-API-Key
  → returns Pipedream connect link to browser
```

**Read path (direct Supabase):**
```
Browser → supabase.from('integrations').select('*')
  → RLS enforces user can only see their own brands' data
  → returns directly
```

This keeps the gateway API key server-side while giving the frontend fast reads.

### 4. Pipedream OAuth UI Flow

When a user clicks "Connect Google Analytics":
1. Frontend calls `POST /api/connect` with `{channel: "analytics", provider: "ga4"}`
2. API route calls gateway `POST /connections/connect` → gets `connect_link_url`
3. Frontend opens `connect_link_url` in a popup window
4. User completes OAuth in the popup
5. Pipedream sends webhook to `POST /connections/webhooks/pipedream/connect`
6. Gateway auto-confirms the connection
7. Frontend polls `/api/connections/status` until the integration shows as connected
8. Popup closes, dashboard updates

### 5. Real-time Updates

For the dashboard to feel alive:
- Poll `/api/connections/status` every 30s for connection health
- Poll `/api/actions/pending` every 60s for new proposals
- After approving an action, poll for execution result
- No WebSockets needed initially — polling is fine for MVP

## Design system (from live meetkai.xyz — match exactly)

**Colors (CSS custom properties):**
```css
--bg: #0a0a0a;
--bg-elevated: #111;
--bg-card: #141414;
--bg-card-hover: #181818;
--border: #1e1e1e;
--border-hover: #2a2a2a;
--text: #fafafa;
--text-secondary: #a1a1a1;
--text-tertiary: #6b6b6b;
--cream: #f2efe8;
--amber: #f59e0b;        /* primary accent */
--amber-light: #fbbf24;
--amber-dim: rgba(245,158,11,0.12);
--green: #22c55e;         /* success / connected */
--green-dim: rgba(34,197,94,0.12);
--red: #ef4444;           /* error / disconnected */
--red-dim: rgba(239,68,68,0.12);
--blue: #3b82f6;          /* info */
--blue-dim: rgba(59,130,246,0.12);
--purple: #a78bfa;
--purple-dim: rgba(167,139,250,0.12);
--radius: 12px;
--radius-lg: 16px;
```

**Typography:**
- Display/headings: `Fraunces` (serif, variable weight 400-900)
- Body/UI: `Outfit` (sans-serif, 300-700)
- Data/code/metrics: `JetBrains Mono` (monospace, 400-700)

```css
--display: 'Fraunces', Georgia, serif;
--body: 'Outfit', -apple-system, sans-serif;
--mono: 'JetBrains Mono', monospace;
```

**Visual patterns from the live site:**
- Subtle noise texture overlay (`feTurbulence` SVG filter, opacity 0.03)
- Grid background lines (64px grid, `rgba(255,255,255,0.02)`)
- Card borders with `--border` color, hover states with `--border-hover`
- No decorative elements — every pixel earns its space
- Status-driven: green/amber/red dots for health states
- Card-based layout for all data

The dashboard must feel like a premium extension of meetkai.xyz, not a separate product. Same fonts, same colors, same card style.

## What NOT to build

- No billing/payments (yet)
- No team/multi-user (yet — Supabase Auth handles this when ready)
- No custom auth — use Supabase Auth magic links, not custom JWT
- No notification system beyond email
- No mobile app — responsive web is enough
- Do not rebuild any backend logic — use the existing gateway endpoints for writes
- Use Supabase Postgres for all persistent data — NOT file-backed JSON for the dashboard
- Use Supabase Realtime subscriptions for live updates on action execution status (not polling)

## Success criteria

The dashboard is done when:
1. A business owner receives a magic link after submitting an audit
2. They click it and land on a dashboard showing their audit score
3. They click "Connect Google Analytics" and complete OAuth
4. Their real traffic data appears on the dashboard within 30 seconds
5. An AI-proposed action (e.g., "Update homepage CTA") appears in their queue
6. They click "Approve" and the action executes through Pipedream
7. The result shows up in their activity feed

## File structure suggestion

```
app-meetkai/
├── app/
│   ├── layout.tsx              # Root layout (dark theme, nav)
│   ├── page.tsx                # Landing / login
│   ├── auth/
│   │   └── verify/page.tsx     # Magic link handler
│   ├── dashboard/
│   │   └── page.tsx            # Main dashboard
│   ├── connect/
│   │   └── page.tsx            # Account connection hub
│   ├── actions/
│   │   └── page.tsx            # Action queue
│   ├── analytics/
│   │   └── page.tsx            # Analytics deep dive
│   ├── settings/
│   │   └── page.tsx            # Account settings
│   └── api/
│       ├── auth/
│       │   ├── login/route.ts      # Send magic link
│       │   └── verify/route.ts     # Verify magic link token
│       ├── connections/
│       │   └── [...path]/route.ts  # Proxy to gateway /connections/*
│       ├── actions/
│       │   └── [...path]/route.ts  # Proxy to gateway /ops/*
│       └── analytics/
│           └── route.ts            # Proxy to gateway analytics
├── components/
│   ├── ui/                     # Shared UI primitives
│   ├── dashboard/              # Dashboard-specific components
│   ├── connect/                # Connection flow components
│   └── actions/                # Action queue components
├── lib/
│   ├── supabase/
│   │   ├── client.ts           # Browser Supabase client
│   │   ├── server.ts           # Server-side Supabase client (service role)
│   │   └── middleware.ts       # Auth middleware for API routes
│   ├── gateway.ts              # FastAPI gateway client (server-side)
│   └── hooks.ts                # React hooks (useConnections, useActions, useBrand)
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

## Environment variables needed

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # server-side only, for admin ops

# Gateway (server-side only)
GATEWAY_URL=http://localhost:8088
GATEWAY_API_KEY=<the CMO_GATEWAY_API_KEY>

# Pipedream
NEXT_PUBLIC_PIPEDREAM_PROJECT_ID=proj_jBs2MK1

# App
NEXT_PUBLIC_APP_URL=https://app.meetkai.xyz
```

## Deploying to the server

```bash
# 1. Build locally or on server
cd /opt/app-meetkai
pnpm install && pnpm build

# 2. Run via PM2
pm2 start pnpm --name "app-meetkai" -- start -- --port 3010

# 3. Add Caddy block
# In /etc/caddy/Caddyfile:
app.meetkai.xyz {
    reverse_proxy 127.0.0.1:3010
    encode gzip
}

# 4. Reload Caddy
caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy
```
