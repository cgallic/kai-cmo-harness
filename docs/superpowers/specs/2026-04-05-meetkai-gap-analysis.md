# MeetKai Dashboard — Full Gap Analysis

**Date:** 2026-04-05  
**Audited by:** 3 parallel subagents covering all 10 audit areas  
**Codebase:** `app-meetkai/` — Next.js 14 + Supabase + Pipedream + MiKai  
**Live:** `app.meetkai.xyz` (Vercel) → Supabase project `YOUR_PROJECT_REF`

---

## Executive Summary

The MeetKai Dashboard is approximately **25-30% complete** as an AI CMO product. The foundation is solid — clean component architecture, proper auth middleware, working RLS policies, Supabase Realtime subscriptions, and a functional GA4 sync pipeline. However, the product is hollow beyond this shell: **12 of 14 providers connect but do nothing**, GSC is broken by a provider name mismatch, action "execution" produces static markdown templates instead of real AI output, there are no scheduled syncs, no notification delivery, no content generation integration with the Kai harness, and no publishing capability. The biggest risk is that the product **creates an illusion of functionality** — green "Active" badges, "Execute" buttons, notification toggles — while doing almost nothing behind the scenes. A user who connects their accounts and clicks "Execute" on an action will receive a generic markdown checklist and wonder why they signed up.

---

## Scorecard

| Area | Status | Score | Blocking Issues |
|------|--------|:-----:|-----------------|
| 1. Connection Flow | Partial | 4/10 | GSC broken (provider name mismatch), 12/14 providers connect-but-do-nothing, 8 providers missing config pickers |
| 2. Analytics Page | Partial | 3/10 | Only GA4 works, GSC broken, date picker cosmetic, no social/email/ads analytics |
| 3. Audit Engine | Functional | 7/10 | MiKai integration works, fragile response parsing, no rate limiting |
| 4. Action Engine | Stub | 2/10 | Generation works but channel mapping broken, execution is static templates not real AI, risk tiers inverted |
| 5. Dashboard Page | Functional | 6/10 | Widgets work, empty states handled, score=0 bug, no Realtime on audits |
| 6. Settings Page | Partial | 4/10 | Basic save works, notification toggles are facade, missing billing/team/export |
| 7. Connect Page | Partial | 5/10 | GA4 config picker works, Sync button is dead, `window.location.reload()` used |
| 8. Auth & Security | Good | 7/10 | RLS properly enforced, service key isolated, but webhook unsigned, postMessage wildcard, no input validation |
| 9. Missing Features | Gap | 2/10 | No scheduled syncs, no notifications, no content gen, no publishing, no billing, no teams |
| 10. Code Quality | Good | 7/10 | Clean architecture, typed hooks, minor issues (unused import, console.logs, module-scope client) |

---

## Provider-by-Provider Breakdown

| Provider | Channel | appSlug | OAuth | Config Picker | Data Sync | What's Missing |
|----------|---------|---------|:-----:|:-------------:|:---------:|----------------|
| GA4 | analytics | `google_analytics` | Working | Select (properties) | Working (28d hardcoded) | Date range flexibility, `keyEvents` fallback for post-2024 properties |
| GSC | analytics | `google_search_console` | Working | Select (sites) | **BROKEN** | Fatal: PROVIDERS defines `provider: "gsc"` but all backend routes query `"google_search_console"`. Zero results every time. |
| GBP | analytics | `google_my_business` | Likely works | **Missing** (needs location picker) | **None** | Connect-but-do-nothing. Needs location picker, review sync, insights sync |
| WordPress | website | `wordpress_org` | Likely works | **Missing** (needs site picker) | **None** | Connect-but-do-nothing. Needs site picker, post/page sync |
| Shopify | website | `shopify` | Likely works | Text (store domain) | **None** | Store domain collected but never used. Needs order/product/traffic sync |
| Facebook | social | `facebook_pages` | Likely works | **Missing** (needs page picker) | **None** | Connect-but-do-nothing. Needs page picker, insights sync |
| Instagram | social | `instagram_business` | Likely works | **Missing** (needs page→IG picker) | **None** | Connect-but-do-nothing. Needs FB page→IG account picker, engagement sync |
| LinkedIn | social | `linkedin` | Likely works | **Missing** (needs company picker) | **None** | Connect-but-do-nothing. Needs personal vs company picker, analytics sync |
| TikTok | social | `tiktok_marketing` | Likely works | **Missing** (needs ad account picker) | **None** | Connect-but-do-nothing. Needs ad account picker, performance sync |
| YouTube | social | `youtube_data_api` | Likely works | **Missing** (needs channel picker) | **None** | Connect-but-do-nothing. Needs channel picker, video/subscriber sync |
| Mailchimp | email | `mailchimp` | Likely works | **Missing** (needs audience picker) | **None** | Connect-but-do-nothing. Needs audience picker, campaign performance sync |
| SendGrid | email | `sendgrid` | Likely works | None needed | **None** | Connect-but-do-nothing. Needs delivery stats sync |
| Google Ads | paid_media | `google_ads` | Likely works | Text (Customer ID) | **None** | Customer ID collected but never used. Should be dropdown. Needs campaign/spend sync |
| Meta Ads | paid_media | `facebook_marketing_api` | Likely works | Text (Ad Account ID) | **None** | Ad Account ID collected but never used. Should be dropdown. Needs campaign/ROAS sync |

**Summary:** 1 working sync (GA4), 1 broken sync (GSC), 12 connect-but-do-nothing providers. 8 providers missing required config pickers.

---

## Critical Gaps (must fix before any user touches this)

1. **GSC is completely broken — provider name mismatch.** `PROVIDERS` defines `provider: "gsc"` but every backend route queries for `"google_search_console"`. GSC will never sync, the site picker will never load, the analytics page will never show the GSC sync button. One-line fix in `lib/types.ts` or multiple backend files. **P0.**

2. **Action execution is completely fake.** `POST /api/actions/execute` generates static markdown checklists with placeholder text (`[Business Name]`, `[Phone Number]`). It doesn't call any API, modify any website, or produce personalized output. Users clicking "Approve & Execute" get generic advice documents. The entire approve/execute flow is theater. **P0.**

3. **12 of 14 providers are connect-but-do-nothing.** Users see green "Active" badges implying their data is flowing. Nothing is flowing. This is actively misleading. **P0.**

4. **Notification system is a facade.** Three toggles in settings (action completed, connection issues, weekly summary) store preferences in metadata but have zero delivery infrastructure. Users will toggle these expecting emails that never arrive. **P1 — remove UI or build backend.**

5. **No scheduled syncs.** Analytics data goes stale immediately after manual sync. For a "CMO dashboard" that claims to monitor marketing, this is disqualifying. **P1.**

6. **Webhook endpoint accepts unsigned requests.** Any attacker who knows the URL can forge POST payloads to mark arbitrary integrations as "connected" with fake account IDs. No HMAC, no IP whitelist. **P1 — security.**

7. **Channel mapping in action generation is dead code.** `mapCategoryToChannel` checks for keywords ("social", "email", "paid") that never appear in the 8 audit dimension names. 7/8 dimensions always map to `"website"`. The channel field on actions is nearly always wrong. **P1.**

8. **Risk tier is inverted.** Critical findings → "medium" risk. Warning findings → "low" risk. Nothing ever gets "high". Misrepresents severity to users. **P2.**

9. **No action deduplication.** Clicking "Generate Actions" twice creates duplicate actions. No idempotency check, no link to audit ID. **P2.**

10. **Date range picker is cosmetic.** The 7d/28d/90d selector changes local state but is never passed to sync API or used to filter snapshots. **P2.**

11. **Score of 0 shows as "--" in QuickStats.** `audit?.overall_score ? Math.round(...) : "--"` treats 0 as falsy. **P2 — bug.**

12. **`postMessage("*")` wildcard origin.** OAuth callback sends connection status to any opener window. Should restrict to app origin. **P2 — security.**

13. **"Sync" button on connect page cards is a dead button.** Every connected provider shows a "Sync" button with a refresh icon, but it has no `onClick` handler. Does nothing for any provider. **P2.**

14. **MiKai response parsing has no structural validation.** If the external MiKai API changes its response shape, all dimensions silently score 0 with no findings. No schema validation, no alerting. **P2.**

15. **No rate limiting on audit runs.** Users can spam "Re-run" and trigger unlimited requests to the MiKai API. No server-side throttle. **P2.**

---

## Missing Features (needed for launch)

| # | Feature | Priority | Effort | Notes |
|---|---------|----------|--------|-------|
| 1 | **Data sync for all 14 providers** | Critical | XL | Each provider needs: API integration via Pipedream, data model, sync endpoint, analytics page display |
| 2 | **Config pickers for 8 providers** | Critical | L | Facebook, Instagram, LinkedIn, YouTube, Mailchimp, GBP, TikTok, WordPress need sub-account selection |
| 3 | **Real action execution (Kai harness integration)** | Critical | XL | Replace static templates with AI-generated content using the 30+ Kai marketing skills |
| 4 | **Scheduled syncs (cron/background)** | Critical | M | Auto-refresh analytics on a schedule, not just manual button clicks |
| 5 | **Notification/email delivery** | Critical | M | Wire up the notification toggles to actual email delivery (Resend, SendGrid, etc.) |
| 6 | **Onboarding wizard** | Critical | M | Guided: connect accounts → run audit → see results. Current onboarding is just settings form |
| 7 | **Billing/subscription (Stripe)** | Critical | L | Plans, usage limits, payment processing |
| 8 | **Scheduled audit re-runs** | Critical | S | Periodic marketing health checks with score trend tracking |
| 9 | **Integration health monitoring** | Critical | S | Detect broken connections, expired tokens, degraded providers |
| 10 | **Publishing to connected platforms** | High | XL | Push generated content to WordPress, social accounts, email providers |
| 11 | **Content generation pipeline** | High | L | Use Kai harness frameworks, quality gates, and personas to produce real content |
| 12 | **Input validation (zod)** | High | M | All API routes accept raw JSON with minimal checks |
| 13 | **Webhook signature validation** | High | S | Pipedream HMAC verification on webhook endpoint |

---

## Nice-to-Have (post-launch)

| # | Feature | Effort | Notes |
|---|---------|--------|-------|
| 1 | Multi-brand support (agency mode) | M | Schema supports one brand per user. Agencies need brand switcher |
| 2 | Team/collaboration | H | Invite members, roles (admin/viewer), team-level brand sharing |
| 3 | CopilotKit chat panel | M | Agentic copilot for marketing questions against user's data |
| 4 | Reporting (PDF/email) | M | Exportable reports for clients |
| 5 | Audit history & trends | S | Score comparison over time, delta tracking |
| 6 | Competitor monitoring | H | Track competitor changes, alerts |
| 7 | Data retention/cleanup policy | S | Snapshot table grows unbounded, needs TTL |
| 8 | Account deletion | S | No way to delete account or data |
| 9 | Data export | S | Export audit history, analytics, actions |
| 10 | White-label/custom domain | M | Agency branding |

---

## Dead Code & Cleanup

| File | Issue | Action |
|------|-------|--------|
| `components/ui/tabs.tsx:4` | `import { useState } from "react"` — unused import | Remove |
| `app/api/analytics/sync/route.ts:116` | `console.log("Using property:", propertyId)` | Remove |
| `app/api/connections/webhook/route.ts:54,61` | `console.log` / `console.warn` debug statements | Remove or replace with structured logging |
| `app/api/connections/confirm/route.ts:15,48,71,93` | Four `console.log` statements logging connection flow | Remove |
| `app/(dashboard)/connect/page.tsx:319` | `console.log("Confirm result:", confirmData)` in client code | Remove |
| `lib/hooks.ts:8` | `const supabase = createClient()` at module scope — singleton shared across components | Move inside hooks or use React context |
| `app/(dashboard)/connect/page.tsx:271,321` | `window.location.reload()` used as state management | Replace with `router.refresh()` or state invalidation |
| `lib/types.ts` | Provider `"gsc"` vs backend `"google_search_console"` mismatch | Align to one name |
| All API routes | Type casting with `as Record<string, unknown>` on Supabase responses | Add typed query helpers |

---

## Auth & Security Detail

### RLS Policy Review

| Table | Select | Insert | Update | Delete | Gap? |
|-------|--------|--------|--------|--------|------|
| brands | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | **NONE** | No delete policy — blocks deletion (not exploitable) |
| audits | Via brand ownership subquery | **NONE** (service role only) | **NONE** | **NONE** | Write-only via service role — secure by design |
| integrations | Via brand ownership subquery | Via brand ownership subquery | Via brand ownership subquery | **NONE** | No delete — disconnect sets status, can't remove rows |
| actions | Via brand ownership subquery | **NONE** (service role only) | Via brand ownership subquery | **NONE** | Inserts via service role, users can update approval state |
| channel_snapshots | Via brand ownership subquery | **NONE** (service role only) | **NONE** | **NONE** | Read-only for users — no gap |

**Verdict:** RLS is sound. User A cannot access User B's data. Service role is properly isolated to server-side code only.

### Security Vulnerabilities

| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | Webhook endpoint accepts unsigned requests | High | `app/api/connections/webhook/route.ts` |
| 2 | `postMessage("*")` wildcard origin | Medium | `app/api/connections/callback/route.ts` |
| 3 | postMessage listener has no origin check | Medium | `app/(dashboard)/connect/page.tsx` |
| 4 | No input validation library (zod/yup) | Medium | All API routes |
| 5 | No rate limiting on any endpoint | Low | All API routes |
| 6 | No CSRF protection beyond Supabase auth | Low | All mutation endpoints |
| 7 | Open redirect potential in auth callback | Low | `app/auth/callback/route.ts` (mitigated by `origin` prepend) |

---

## Realtime Assessment

| Hook | Realtime? | Status |
|------|:---------:|--------|
| `useIntegrations` | Yes | Working — subscribes to `integrations-changes`, handles INSERT/UPDATE/DELETE |
| `useActions` | Yes | Working — subscribes to `actions-changes`, re-fetches on change |
| `useAudit` | **No** | Stale until manual refresh or navigation |
| `useSnapshots` | **No** | Stale until manual refresh or navigation |
| `useBrand` | **No** | Stale until manual refresh |

**Latent bug:** Channel names are hardcoded (`"integrations-changes"`, `"actions-changes"`). If two components use the same hook simultaneously, the second mount creates a channel with the same name, potentially causing conflicts. Currently mitigated by routing structure (different pages).

---

## Recommended Next Sprint (Work Packages)

| # | Work Package | Size | Dependencies | Description |
|---|-------------|:----:|:------------:|-------------|
| WP1 | **Fix GSC provider name mismatch** | S | None | Change `provider: "gsc"` to `"google_search_console"` in PROVIDERS array (or update all backend queries). One-line fix that unblocks GSC sync. |
| WP2 | **Fix action engine fundamentals** | M | None | Fix risk tier mapping (critical→high, warning→medium). Fix channel mapping (use dimension names directly). Add action deduplication (check for existing actions per audit). Fix score=0 falsy bug. |
| WP3 | **Fix security issues** | M | None | Add Pipedream webhook HMAC signature validation. Restrict `postMessage` to app origin. Add origin check on message listener. Add zod request body validation on all API routes. |
| WP4 | **Build real action execution (Kai harness integration)** | L | WP2 | Replace static markdown templates with calls to Kai marketing skills. Use brand context, audit findings, and connected data to generate personalized, actionable deliverables. |
| WP5 | **Add config pickers for 8 providers** | L | None | Facebook (page picker), Instagram (page→IG), LinkedIn (company), YouTube (channel), Mailchimp (audience), GBP (location), TikTok (ad account), WordPress (site). Each needs an API endpoint + dropdown component. |
| WP6 | **Build sync pipelines for top-priority providers** | XL | WP5 | Start with: Facebook Pages (insights), Google Ads (campaigns), Meta Ads (campaigns). Each needs: Pipedream proxy route, data model, snapshot storage, analytics page display. |
| WP7 | **Scheduled syncs & audit re-runs** | M | WP6 | Implement cron-based auto-sync for connected providers. Add periodic audit re-runs with score trend tracking. Options: Vercel Cron, Supabase pg_cron, or external scheduler. |
| WP8 | **Notification system** | M | WP7 | Wire notification preferences to actual email delivery (Resend/SendGrid). Send alerts on: score changes, action approvals needed, connection degradation, weekly digest. |
| WP9 | **Onboarding wizard** | M | WP1-WP3 | Multi-step flow: welcome → connect first account → run first audit → see results → generate first actions. Progress tracking, skip options. |
| WP10 | **Code quality cleanup** | S | None | Remove console.logs, fix unused imports, move module-scope Supabase client into hooks, replace `window.location.reload()`, make date picker functional, wire up dead Sync button. |
