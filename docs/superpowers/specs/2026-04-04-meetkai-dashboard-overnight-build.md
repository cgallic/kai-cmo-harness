# MeetKai Dashboard — Overnight Engineering Brief

**Date:** 2026-04-04
**Author:** Connor (CEO)
**Status:** DISPATCH READY — 12 parallel work packages
**Repo:** `E:\Dev2\kai-cmo-harness-work\app-meetkai\`
**Live:** `app.meetkai.xyz` (Vercel) → Supabase project `YOUR_PROJECT_REF`

---

## What Exists

A Next.js 14 dashboard is live at `app.meetkai.xyz` with:
- Supabase Auth (magic links), 5 tables with RLS, Realtime on actions + integrations
- 6 pages: Login, Dashboard, Connect, Actions, Analytics, Settings
- Pipedream Connect OAuth working (GA4 connected, token creation + popup flow)
- GA4 analytics sync via Pipedream proxy (overview, daily, pages, sources)
- Dark-first design matching meetkai.xyz (amber accents, Fraunces/Outfit/JetBrains fonts)
- Deployed on Vercel with all env vars set

## What's Broken or Missing

The dashboard is ~60% done. The UI shell is solid but the backend intelligence layer doesn't exist yet — actions never execute, audits never generate, analytics has bugs, and there's no agentic layer. This doc specs every work package needed to ship a real product.

---

## WORK PACKAGE 1: Fix GA4 Property Selection

**Priority:** CRITICAL (blocks analytics for multi-property accounts)
**Files:** `app/api/analytics/sync/route.ts`, `app/api/analytics/properties/route.ts` (new), `app/(dashboard)/analytics/page.tsx`, `app/(dashboard)/settings/page.tsx`

### Problem
The sync route blindly grabs the first GA4 property it finds. Users with multiple properties (common — staging vs prod, multiple sites) get the wrong data with no way to choose.

### Spec

**New API route: `GET /api/analytics/properties`**
```
Request: { brand_id: string }
Response: {
  properties: Array<{
    property_id: string;       // "properties/123456789"
    display_name: string;      // "My Website - Production"
    account_name: string;      // "My Company"
  }>
}
```
Implementation:
1. Verify user auth + brand ownership
2. Get GA4 integration from Supabase (`provider: "ga4"`, `status: "connected"`)
3. Call `pd.proxy.get({ url: "https://analyticsadmin.googleapis.com/v1beta/accountSummaries", accountId })` 
4. Flatten all `accountSummaries[].propertySummaries[]` into a list
5. Return property_id, displayName, and parent account displayName

**Store selected property in integration config:**
```sql
-- integrations.config column (jsonb)
{ "ga4_property_id": "properties/123456789" }
```

**Update sync route** (`app/api/analytics/sync/route.ts`):
- Read `integration.config.ga4_property_id` instead of auto-detecting
- If not set, return `{ error: "No GA4 property selected", properties: [...list...] }` so the frontend can prompt selection
- Remove the `accountSummaries` auto-pick logic

**Update Settings page** (`app/(dashboard)/settings/page.tsx`):
- Add "Analytics Configuration" section below Business Profile
- Show a dropdown of GA4 properties (fetched from `/api/analytics/properties`)
- On select, update `integrations.config` via Supabase
- Show the currently selected property name

**Update Analytics page** (`app/(dashboard)/analytics/page.tsx`):
- If sync returns `properties` array (no property selected), show a property picker inline instead of the empty state
- After selection, auto-trigger sync

---

## WORK PACKAGE 2: Add GSC (Google Search Console) Sync

**Priority:** HIGH (analytics page expects GSC data but never fetches it)
**Files:** `app/api/analytics/sync/route.ts`, `app/api/connections/connect/route.ts`

### Problem
The analytics page renders a `gscQueries` table but the sync endpoint only pulls GA4 data. GSC is a separate Pipedream connection with its own OAuth.

### Spec

**GSC is a separate integration.** Users must connect it independently on the Connect page (it already appears as "Google Search Console" in the provider grid). After connecting, its `connected_account_id` is stored in its own `integrations` row.

**GSC property selection** (same pattern as GA4):

New API route: `GET /api/analytics/gsc-sites`
```
Request: { brand_id: string }
Response: {
  sites: Array<{
    site_url: string;        // "sc-domain:example.com" or "https://example.com/"
    permission_level: string; // "siteOwner", "siteFullUser", etc.
  }>
}
```
Implementation:
- Call `pd.proxy.get({ url: "https://www.googleapis.com/webmasters/v3/sites", accountId: gsc_account_id })`
- Store selected site in `integrations.config.gsc_site_url`

**Add GSC queries to sync** (append to existing sync route or create `/api/analytics/sync-gsc`):
```
Call: POST https://www.googleapis.com/webmasters/v3/sites/{siteUrl}/searchAnalytics/query
Body: {
  startDate: "2026-03-07",
  endDate: "2026-04-04",
  dimensions: ["query"],
  rowLimit: 25
}
Response rows → map to: { query, clicks, impressions, ctr, position }
```
Save to `channel_snapshots` with `channel: "analytics"`, `provider: "gsc"`.

**Update analytics page:**
- Read GSC snapshot separately: `snapshots.find(s => s.provider === "gsc")`
- Populate the existing `gscQueries` table (already built, just needs data)
- Add a separate "Sync GSC" button if GSC is connected

---

## WORK PACKAGE 3: Audit Engine Integration

**Priority:** HIGH (dashboard audit score ring shows nothing)
**Files:** `app/api/audits/run/route.ts` (new), `app/(dashboard)/dashboard/page.tsx`, `components/dashboard/audit-score-ring.tsx`

### Problem
The MiKai audit engine exists at `meetkai.xyz/api/mikai/` and produces JSON audit results. But nothing connects it to the dashboard. The audit score ring is empty forever.

### Spec

**New API route: `POST /api/audits/run`**
```
Request: { brand_id: string, domain: string }
Response: { audit_id: string, status: "running" | "completed", overall_score?: number }
```
Implementation:
1. Verify auth + brand ownership
2. Call MiKai audit API: `POST https://meetkai.xyz/api/mikai/` with `{ domain, email: user.email, name: brand.name }`
3. Parse the audit response — MiKai returns category scores across 7 dimensions:
   - offer_clarity, trust_and_proof, conversion_path, local_seo, speed_to_lead, reviews_reputation, channel_presence, follow_up_gaps
4. Calculate `overall_score` as weighted average (0-100)
5. Insert into `audits` table via service role client
6. Return the audit ID

**New API route: `GET /api/audits/latest`**
```
Request: { brand_id: string }
Response: { audit: Audit | null }
```
Simple wrapper — reads from Supabase `audits` table, returns latest for brand.

**Update Dashboard:**
- On first load, if no audit exists AND brand has a URL, show "Run your first audit" button
- Button calls `/api/audits/run` with brand.url
- Show loading state while audit runs
- After completion, audit score ring populates

**Update Settings:**
- Add "Run New Audit" button in the business profile section
- Show last audit date and score

---

## WORK PACKAGE 4: Action Proposal Engine

**Priority:** HIGH (actions page is empty forever without this)
**Files:** `app/api/actions/generate/route.ts` (new), `app/api/actions/execute/route.ts` (new)

### Problem
No service creates action proposals. The actions page has perfect UI (tabs, approve/reject, expandable details) but zero data.

### Spec

**Phase 1: Seed actions from audit findings.**

New API route: `POST /api/actions/generate`
```
Request: { brand_id: string, source: "audit" | "analytics" | "manual" }
Response: { actions: Action[], count: number }
```
Implementation:
1. Read the latest audit for the brand
2. For each finding with severity "critical" or "warning", generate an action proposal:
   ```
   {
     brand_id,
     action_type: "fix_cta" | "add_schema" | "improve_speed" | "update_copy" | etc.,
     channel: finding.category → map to channel,
     intent: "Update homepage CTA to include a phone number for lead capture",
     risk_tier: finding.severity === "critical" ? "medium" : "low",
     proposed_changes: { 
       finding: finding.description,
       recommendation: finding.recommendation,
       affected_url: "https://...",
     },
     approval_state: "pending",
     execution_state: "pending",
   }
   ```
3. Insert all into `actions` table via service role
4. Return created actions

**Phase 2: Generate actions from analytics anomalies.**
- If bounce rate > 70%, propose "Improve page load speed" or "Revise above-fold content"
- If a top page has 0 conversions, propose "Add CTA to high-traffic page"
- If traffic dropped >20% week-over-week, propose "Investigate traffic drop"

**Phase 3: Action execution** (post-approval).

New API route: `POST /api/actions/execute`
```
Request: { action_id: string }
Response: { status: "executing" | "completed" | "failed", result?: object }
```
For MVP, execution means:
1. Mark `execution_state: "executing"`
2. Based on `action_type`, generate the deliverable (copy, schema markup, meta tags, etc.) using Claude API
3. Store result in `result_summary`
4. Mark `execution_state: "completed"`

The approve button on the actions page should call this after changing `approval_state` to `"approved"`.

---

## WORK PACKAGE 5: Branding & Assets

**Priority:** HIGH (no favicon, no logo, no og:image — looks unfinished)
**Files:** `public/` (new directory), `app/layout.tsx`

### Spec

**Create `app-meetkai/public/` with:**
- `favicon.ico` — 32x32, dark background with amber "K" or Kai logomark
- `favicon-16x16.png`, `favicon-32x32.png`
- `apple-touch-icon.png` — 180x180
- `logo.svg` — MeetKai wordmark (Fraunces font, "Meet" white + "Kai" amber)
- `logo-icon.svg` — Just the "K" mark for small spaces
- `og-image.png` — 1200x630, dark background, MeetKai logo + "AI CMO Dashboard" tagline
- `robots.txt`:
  ```
  User-agent: *
  Allow: /
  Disallow: /api/
  Disallow: /dashboard
  Disallow: /connect
  Disallow: /actions
  Disallow: /analytics
  Disallow: /settings
  ```

**Update `app/layout.tsx` metadata:**
```typescript
export const metadata: Metadata = {
  title: {
    default: "MeetKai Dashboard",
    template: "%s | MeetKai",
  },
  description: "AI CMO Dashboard — connect your marketing accounts, see what AI finds, approve actions.",
  metadataBase: new URL("https://app.meetkai.xyz"),
  openGraph: {
    title: "MeetKai — AI CMO Dashboard",
    description: "Connect your marketing accounts. Get AI-powered audits. Approve actions with one click.",
    url: "https://app.meetkai.xyz",
    siteName: "MeetKai",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "MeetKai — AI CMO Dashboard",
    description: "Connect your marketing accounts. Get AI-powered audits. Approve actions with one click.",
    images: ["/og-image.png"],
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
};
```

**Update sidebar logo:** Replace the text "MeetKai" with the SVG logomark + wordmark.

---

## WORK PACKAGE 6: Error Handling & Polish

**Priority:** MEDIUM (app crashes silently on errors)
**Files:** `app/(dashboard)/error.tsx` (new), `app/not-found.tsx` (new), `app/(dashboard)/*/page.tsx` (all pages)

### Spec

**Global error boundary** — `app/(dashboard)/error.tsx`:
```typescript
"use client";
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <h2 className="font-display text-xl font-semibold mb-2">Something went wrong</h2>
      <p className="text-text-secondary text-sm mb-6">{error.message}</p>
      <button onClick={reset} className="...">Try again</button>
    </div>
  );
}
```

**Not found page** — `app/not-found.tsx`:
- "Page not found" with link back to dashboard

**API error standardization:**
All API routes should return:
```json
{ "error": "Human-readable message", "code": "MACHINE_CODE", "detail": "..." }
```

**Toast notifications:**
- Install `sonner` (lightweight toast library)
- Add `<Toaster />` to dashboard layout
- Show toast on: action approved, action rejected, sync completed, connection confirmed, errors

**Loading states audit:**
- Every page already has skeleton loaders — verify they work
- Add loading.tsx to `(dashboard)/` for route transitions

---

## WORK PACKAGE 7: Connect Page — Full OAuth for All Providers

**Priority:** MEDIUM (only GA4 tested, other providers untested)
**Files:** `app/api/connections/connect/route.ts`, `app/(dashboard)/connect/page.tsx`

### Spec

**Test and fix OAuth for each provider category:**

| Provider | App Slug | Known Issues |
|----------|----------|-------------|
| Google Analytics | `google_analytics` | Working ✓ |
| Google Search Console | `google_search_console` | Untested — needs separate OAuth scope |
| Google Business | `google_my_business` | Untested |
| WordPress | `wordpress_org` | Untested — may need site URL |
| Shopify | `shopify` | Untested — needs store domain |
| Facebook Pages | `facebook_pages` | Untested |
| Instagram Business | `instagram_business` | Untested — requires FB page connection first |
| LinkedIn | `linkedin` | Untested |
| TikTok Marketing | `tiktok_marketing` | Untested |
| YouTube Data API | `youtube_data_api` | Untested |
| Mailchimp | `mailchimp` | Untested |
| SendGrid | `sendgrid` | Untested — API key, not OAuth |
| Google Ads | `google_ads` | Untested — needs customer ID selection |
| Meta Ads | `facebook_marketing_api` | Untested — needs ad account selection |

**For each provider:**
1. Verify the Pipedream app slug resolves correctly
2. Test the full popup → callback → confirm flow
3. Add provider-specific config selection where needed (e.g., Shopify store domain, Google Ads customer ID)
4. Update the confirm route to handle provider-specific account structures

**Add "Verify" button functionality:**
- For connected accounts, call `pd.accounts.list({ externalUserId: brand_id })` and check credentials are still valid
- Show "healthy" or "needs reconnection" status

---

## WORK PACKAGE 8: Dashboard Widgets — Wire to Real Data

**Priority:** MEDIUM (widgets exist but show stale/empty data)
**Files:** `app/(dashboard)/dashboard/page.tsx`, `components/dashboard/*.tsx`

### Spec

**Quick Stats widget:**
- "Sessions (28d)" should read from latest `channel_snapshots` where `provider: "ga4"` — already implemented but verify it works after sync
- Add "Last synced: 2h ago" subtitle using `integrations.last_sync_at`
- Add click-to-navigate: clicking "Sessions" goes to `/analytics`

**Audit Score Ring:**
- After WP3 (audit engine) is done, this will populate automatically
- Add "Re-run audit" button in the card header
- Add "Last audited: 3d ago" using `audits.created_at`

**Connected Accounts:**
- Shows current integrations — already works via `useIntegrations` hook
- Add health indicator dot (green = connected + synced in last 24h, yellow = connected but stale, red = error/degraded)

**Pending Actions:**
- After WP4 (action engine) is done, this will populate
- Already has approve/reject buttons wired to Supabase — verify Realtime updates the list

**Activity Feed:**
- Shows actions that have been approved/rejected — already works
- Add audit completion events: "Audit completed — score: 72"
- Add connection events: "Google Analytics connected"

---

## WORK PACKAGE 9: Agentic Layer — CopilotKit + A2UI Panel

**Priority:** FUTURE (spec it now, build after core is solid)
**Files:** `app/api/copilotkit/[[...slug]]/route.ts` (new), `components/layout/copilot-panel.tsx` (new), `app/(dashboard)/layout.tsx`, `agent/` (new Python service)

### Spec

This is the "wow" layer — a collapsible AI assistant panel on the right side of every dashboard page. The agent can:
- Answer questions about the user's marketing data ("What's my bounce rate?")
- Propose actions as rich UI cards with approve/reject buttons (A2UI)
- Walk users through connection flows conversationally
- Summarize audit findings and recommend priorities
- Generate content (ad copy, email, social posts) on request

**Frontend packages to add:**
```json
"@copilotkit/react-core": "~1.50.0",
"@copilotkit/runtime": "~1.50.0",
"@copilotkit/a2ui-renderer": "0.0.2",
"@a2a-js/sdk": "0.2.5",
"@ag-ui/a2a": "0.00.6",
"@a2ui/lit": "^0.8.1",
"hono": "^4.6.18"
```

**CopilotKit runtime route** (`app/api/copilotkit/[[...slug]]/route.ts`):
```typescript
import { CopilotRuntime, createCopilotEndpoint, InMemoryAgentRunner } from "@copilotkit/runtime/v2";
import { handle } from "hono/vercel";
import { A2AAgent } from "@ag-ui/a2a";
import { A2AClient } from "@a2a-js/sdk/client";

const a2aClient = new A2AClient(process.env.KAI_AGENT_URL || "http://YOUR_GATEWAY_HOST:10002");
const agent = new A2AAgent({ a2aClient });
const runtime = new CopilotRuntime({
  agents: { default: agent },
  runner: new InMemoryAgentRunner(),
});
const app = createCopilotEndpoint({ runtime, basePath: "/api/copilotkit" });
export const GET = handle(app);
export const POST = handle(app);
```

**Copilot panel component** (`components/layout/copilot-panel.tsx`):
- Collapsible from the right edge (380px wide)
- Toggle button in the top-right of the dashboard
- Uses `CopilotKitProvider` + `CopilotChat` with A2UI renderer
- Theme customized to match meetkai.xyz dark palette

**A2UI theme** (`app/theme.ts`):
- Map meetkai.xyz colors to A2UI tokens:
  - `--n-0` → `#0a0a0a` (background)
  - `--n-10` → `#141414` (card)
  - `--p-30` → `#f59e0b` (amber accent)
  - etc.

**Python A2A agent** (`agent/`):
- Runs on the Hetzner VPS alongside the gateway
- Has tools: `get_audit`, `get_analytics`, `list_actions`, `propose_action`, `get_connections`
- Each tool calls Supabase directly (service role key) to read/write data
- A2UI templates for: audit summary card, action proposal card, analytics highlight card
- Prompt instructs agent to be a marketing CMO assistant

**A2UI templates the agent should generate:**

1. **Action Proposal Card:**
```json
[
  { "beginRendering": { "surfaceId": "action-1", "root": "root" } },
  { "surfaceUpdate": { "surfaceId": "action-1", "components": [
    { "id": "root", "component": { "Card": { "children": { "explicitList": ["title", "desc", "buttons"] } } } },
    { "id": "title", "component": { "Text": { "usageHint": "h3", "text": { "literalString": "Update Homepage CTA" } } } },
    { "id": "desc", "component": { "Text": { "text": { "literalString": "Add a phone number..." } } } },
    { "id": "buttons", "component": { "Row": { "children": { "explicitList": ["approve-btn", "reject-btn"] } } } },
    { "id": "approve-btn", "component": { "Button": { "child": "approve-text", "primary": true, "action": { "name": "approve_action", "context": [{ "key": "action_id", "value": { "literalString": "uuid-here" } }] } } } },
    { "id": "approve-text", "component": { "Text": { "text": { "literalString": "Approve" } } } },
    { "id": "reject-btn", "component": { "Button": { "child": "reject-text", "action": { "name": "reject_action", "context": [{ "key": "action_id", "value": { "literalString": "uuid-here" } }] } } } },
    { "id": "reject-text", "component": { "Text": { "text": { "literalString": "Reject" } } } }
  ] } }
]
```

2. **Analytics Highlight Card** — sessions count, trend arrow, top source
3. **Audit Summary Card** — overall score ring, top 3 findings

---

## WORK PACKAGE 10: Pipedream Webhook (Server-Side Connection Confirmation)

**Priority:** MEDIUM (current flow relies on client-side confirm which can fail)
**Files:** `app/api/connections/webhook/route.ts` (rewrite)

### Problem
The webhook route exists but is never called by Pipedream. The current flow relies on the popup posting a message to the parent window, which then calls `/api/connections/confirm`. If the user closes the browser before the confirm fires, the connection is lost.

### Spec

**Configure Pipedream webhook URL:**
- In the Pipedream project settings, set the webhook URL to `https://app.meetkai.xyz/api/connections/webhook`
- Pipedream will POST to this URL when any account is connected

**Rewrite webhook route:**
```typescript
// POST /api/connections/webhook
// Called by Pipedream when OAuth completes — no user session, use service role
export async function POST(request: Request) {
  const body = await request.json();
  // Pipedream sends: { id, external_user_id, app: { name_slug }, ... }
  const { external_user_id: brandId, id: accountId, app } = body;
  
  // Find matching pending integration
  const serviceClient = await createServiceClient();
  const { data: integration } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brandId)
    .eq("status", "pending_auth")
    .order("created_at", { ascending: false })
    .limit(1)
    .single();
  
  if (integration) {
    await serviceClient.from("integrations").update({
      status: "connected",
      connected_account_id: accountId,
      connected_at: new Date().toISOString(),
    }).eq("id", integration.id);
  }
  
  return NextResponse.json({ ok: true });
}
```

This makes the connection confirmation server-side and reliable — even if the popup/browser crashes.

---

## WORK PACKAGE 11: Supabase Schema Hardening

**Priority:** MEDIUM
**Files:** `supabase/migrations/003_hardening.sql` (new)

### Spec

```sql
-- Add service_role INSERT policies for server-side writes
create policy "service_insert_audits" on public.audits
  for insert with check (true);  -- Service role bypasses RLS anyway, but explicit

create policy "service_insert_actions" on public.actions
  for insert with check (true);

create policy "service_insert_snapshots" on public.channel_snapshots
  for insert with check (true);

-- Add updated_at auto-update trigger
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger brands_updated_at before update on public.brands
  for each row execute function update_updated_at();
create trigger integrations_updated_at before update on public.integrations
  for each row execute function update_updated_at();
create trigger actions_updated_at before update on public.actions
  for each row execute function update_updated_at();

-- Add unique constraint to prevent duplicate integrations
alter table public.integrations
  add constraint unique_brand_channel_provider
  unique (brand_id, channel, provider);

-- Add check constraints
alter table public.actions
  add constraint valid_approval_state
  check (approval_state in ('pending', 'approved', 'rejected', 'auto_approved', 'held'));
alter table public.actions
  add constraint valid_execution_state
  check (execution_state in ('pending', 'executing', 'completed', 'failed', 'rolled_back'));
alter table public.integrations
  add constraint valid_status
  check (status in ('pending_auth', 'connected', 'degraded', 'disconnected', 'error'));
```

---

## WORK PACKAGE 12: CI/CD & Developer Experience

**Priority:** LOW (not blocking launch but needed for team velocity)
**Files:** `.github/workflows/` (new), `app-meetkai/.env.local.example`, root `CLAUDE.md`

### Spec

**GitHub Action: lint + typecheck on PR**
```yaml
name: Dashboard CI
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: app-meetkai
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm, cache-dependency-path: app-meetkai/pnpm-lock.yaml }
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm build
```

**Vercel auto-deploy:**
- Connect the GitHub repo to Vercel if not already done
- Set root directory to `app-meetkai/`
- Enable automatic deployments on push to `main`

**Update `.env.local.example`** with ALL required vars:
```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Pipedream Connect
PIPEDREAM_CLIENT_ID=
PIPEDREAM_CLIENT_SECRET=
PIPEDREAM_PROJECT_ID=proj_YOUR_PROJECT_ID
PIPEDREAM_ENVIRONMENT=development

# App
NEXT_PUBLIC_APP_URL=https://app.meetkai.xyz

# Future: Agent
KAI_AGENT_URL=http://YOUR_GATEWAY_HOST:10002
```

---

## API Reference (Complete)

Every API route this dashboard has or needs, fully specced:

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/auth/callback?code=xxx` | None | Supabase magic link callback, exchanges code for session |

### Connections
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/connections/connect` | User session | Create Pipedream connect token, return OAuth popup URL |
| GET | `/api/connections/callback?provider=xxx` | None | OAuth popup callback — posts message to opener, closes |
| POST | `/api/connections/confirm` | User session | Mark integration as connected, look up Pipedream account ID |
| POST | `/api/connections/webhook` | None (Pipedream) | Server-side OAuth confirmation webhook from Pipedream |

**`POST /api/connections/connect` spec:**
```
Headers: Cookie (Supabase session)
Body: { brand_id: string, channel: string, provider: string, app_slug: string }
Response 200: { token: string, expires_at: string, connect_link_url: string }
Response 200 (no Pipedream): { status: "pending_auth", message: string }
Response 401: { error: "Unauthorized" }
Response 404: { error: "Brand not found" }
Response 502: { error: "Failed to create connect token", detail: string }
```

**`POST /api/connections/confirm` spec:**
```
Headers: Cookie (Supabase session)
Body: { brand_id: string, provider: string }
Response 200: { status: "connected", connected_account_id: string | null }
Response 401: { error: "Unauthorized" }
Response 404: { error: "Brand not found" } | { error: "No integration found" }
Response 500: { error: "Failed to update integration" }
```

### Analytics
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/analytics/sync` | User session | Pull GA4 data via Pipedream proxy, save to channel_snapshots |
| GET | `/api/analytics/properties` | User session | List GA4 properties for connected account |
| GET | `/api/analytics/gsc-sites` | User session | List GSC sites for connected account |

**`POST /api/analytics/sync` spec:**
```
Headers: Cookie (Supabase session)
Body: { brand_id: string }
Response 200: { status: "synced", data: {
  sessions: number, users: number, pageviews: number,
  bounce_rate: number, avg_session_duration: number, conversions: number,
  daily: Array<{ date: string, sessions: number, users: number }>,
  top_pages: Array<{ path: string, views: number, avg_time: number, bounce_rate: number }>,
  sources: Array<{ source: string, sessions: number, percentage: number }>
}}
Response 404: { error: "Google Analytics not connected" }
Response 404: { error: "No GA4 property selected", properties: Array<...> }
Response 502: { error: "Sync failed", detail: string }
```

### Audits
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/audits/run` | User session | Trigger MiKai audit for a domain |
| GET | `/api/audits/latest?brand_id=xxx` | User session | Get latest audit for a brand |

### Actions
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/actions/generate` | User session | Generate action proposals from audit/analytics |
| POST | `/api/actions/execute` | User session | Execute an approved action |

### Future: Agent
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET/POST | `/api/copilotkit/[...slug]` | User session | CopilotKit runtime endpoint for agentic panel |

---

## Dispatch Plan

These work packages can run in parallel. Suggested assignment:

| WP | Name | Estimated Size | Dependencies |
|----|------|---------------|-------------|
| 1 | GA4 Property Selection | Small | None |
| 2 | GSC Sync | Small | None |
| 3 | Audit Engine | Medium | None |
| 4 | Action Proposal Engine | Medium | WP3 (for audit-based actions) |
| 5 | Branding & Assets | Small | None |
| 6 | Error Handling & Polish | Small | None |
| 7 | OAuth All Providers | Medium | None |
| 8 | Dashboard Widgets | Small | WP3, WP4 |
| 9 | Agentic Layer (spec only) | Large | All above |
| 10 | Pipedream Webhook | Small | None |
| 11 | Schema Hardening | Small | None |
| 12 | CI/CD | Small | None |

**Parallelization:** WP1, WP2, WP3, WP5, WP6, WP7, WP10, WP11, WP12 can all run simultaneously. WP4 should start after WP3. WP8 after WP3+WP4. WP9 is design/spec work only for now.

---

## Ground Rules for All Agents

1. **Working directory:** `E:\Dev2\kai-cmo-harness-work\app-meetkai\`
2. **Build must pass:** Run `pnpm build` after every change. The build is currently clean — do not break it.
3. **TypeScript strict:** No `any` types. Use the existing types from `lib/types.ts` or extend them.
4. **Design system:** Match the existing dark theme. Colors in `tailwind.config.ts`. Fonts are Fraunces (display), Outfit (body), JetBrains Mono (data).
5. **Supabase patterns:** Use `createClient()` for user-session reads, `createServiceClient()` for server-side writes that need to bypass RLS.
6. **Pipedream SDK:** Use `PipedreamClient` from `@pipedream/sdk`. Token creation: `pd.tokens.create({ externalUserId })`. Proxy calls: `pd.proxy.get({ url, accountId, externalUserId })` and `pd.proxy.post({ url, accountId, externalUserId, body })`.
7. **No new dependencies** without justification. The stack is: Next.js 14, Supabase, Pipedream SDK, Recharts, Lucide, Tailwind.
8. **Commit messages:** One commit per work package. Format: `WP{N}: {description}`
9. **Do not modify** existing working features. If you need to extend a file, read it first.
