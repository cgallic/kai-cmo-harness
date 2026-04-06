# Integration Sync Task List

**Status:** 2 of 29 providers have working sync. This doc maps every provider to what's needed for end-to-end functionality.

**Current state:**
- **FULL** (2): GA4, GSC — OAuth + sync + config picker + data display
- **OAUTH ONLY** (21): Connect via Pipedream but do nothing after
- **NEEDS CONFIG** (4): Shopify, Google Ads, Meta Ads, Stripe — have text config picker but no sync
- **COMING SOON** (1): TikTok — no Pipedream app exists
- **Sync button on /connect page has no onClick handler** — dead button

---

## Priority 0: Fix the dead Sync button

The Sync button on `/connect` page (line ~407) has no `onClick`. Wire it to call the appropriate sync endpoint for each provider.

**Files:**
- Modify: `app/(dashboard)/connect/page.tsx` — add `handleSync` to ProviderCard

---

## Priority 1: High-Value Sync Endpoints (data users actually need)

Each task = create an API route that:
1. Looks up the provider's integration + connected_account_id
2. Calls the provider's API via Pipedream proxy (`pd.proxy.get/post`)
3. Stores results in `channel_snapshots` table
4. Returns the data

### Task 1.1: Facebook Pages sync
- **Route:** `app/api/sync/facebook/route.ts`
- **Pipedream proxy URL:** `https://graph.facebook.com/v19.0/me/accounts` (list pages), then `https://graph.facebook.com/v19.0/{page_id}/insights` (page metrics)
- **Config needed:** Page picker (user may manage multiple pages) — add `configRequired` with endpoint
- **Data to store:** followers, reach, impressions, engagement, post count (28d)
- **Display:** Add Facebook card to Analytics page

### Task 1.2: Instagram Business sync
- **Route:** `app/api/sync/instagram/route.ts`
- **Pipedream proxy URL:** `https://graph.facebook.com/v19.0/me/accounts` → get IG account → `https://graph.facebook.com/v19.0/{ig_id}/insights`
- **Config needed:** Account picker (linked through Facebook Page)
- **Data to store:** followers, reach, impressions, profile_views, website_clicks
- **Display:** Add Instagram card to Analytics page

### Task 1.3: Google Ads sync
- **Route:** `app/api/sync/google-ads/route.ts`
- **Pipedream proxy URL:** `https://googleads.googleapis.com/v16/customers/{customer_id}/googleAds:searchStream`
- **Config needed:** Already has `google_ads_customer_id` text input — need account picker via `https://googleads.googleapis.com/v16/customers:listAccessibleCustomers`
- **Data to store:** impressions, clicks, cost, conversions, CTR, CPC (28d)
- **Display:** Add Google Ads card to Analytics page

### Task 1.4: Meta Ads sync
- **Route:** `app/api/sync/meta-ads/route.ts`
- **Pipedream proxy URL:** `https://graph.facebook.com/v19.0/act_{account_id}/insights`
- **Config needed:** Already has `meta_ads_account_id` text input — need account picker via `https://graph.facebook.com/v19.0/me/adaccounts`
- **Data to store:** spend, impressions, clicks, conversions, CPM, CPC, ROAS (28d)
- **Display:** Add Meta Ads card to Analytics page

### Task 1.5: Mailchimp sync
- **Route:** `app/api/sync/mailchimp/route.ts`
- **Pipedream proxy URL:** `https://{dc}.api.mailchimp.com/3.0/lists` (audiences), `https://{dc}.api.mailchimp.com/3.0/reports` (campaign stats)
- **Config needed:** Audience/list picker
- **Data to store:** subscriber_count, open_rate, click_rate, campaigns_sent, unsubscribe_rate
- **Display:** Add Email section to Analytics page

### Task 1.6: LinkedIn sync
- **Route:** `app/api/sync/linkedin/route.ts`
- **Pipedream proxy URL:** `https://api.linkedin.com/v2/organizationalEntityShareStatistics` (company page stats)
- **Config needed:** Organization picker via `https://api.linkedin.com/v2/organizationAcls`
- **Data to store:** followers, impressions, clicks, engagement_rate, shares
- **Display:** Add LinkedIn card to Analytics page

---

## Priority 2: Medium-Value Sync Endpoints

### Task 2.1: YouTube sync
- **Route:** `app/api/sync/youtube/route.ts`
- **Pipedream proxy URL:** `https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&mine=true`
- **Config needed:** Channel picker (usually one)
- **Data to store:** subscribers, views, videos, watch_time

### Task 2.2: Stripe sync
- **Route:** `app/api/sync/stripe/route.ts`
- **Pipedream proxy URL:** `https://api.stripe.com/v1/charges?limit=100` (or balance/transactions)
- **Config needed:** Already has `stripe_account_id` text input
- **Data to store:** MRR, total_revenue, active_subscriptions, churn_rate
- **Note:** Gateway already has `/stripe/*` endpoints — consider proxying through gateway instead

### Task 2.3: HubSpot sync
- **Route:** `app/api/sync/hubspot/route.ts`
- **Pipedream proxy URL:** `https://api.hubapi.com/crm/v3/objects/contacts` + `deals` + `companies`
- **Config needed:** None (single account)
- **Data to store:** contacts_count, deals_count, deals_value, pipeline_summary

### Task 2.4: SendGrid sync
- **Route:** `app/api/sync/sendgrid/route.ts`
- **Pipedream proxy URL:** `https://api.sendgrid.com/v3/stats`
- **Config needed:** None
- **Data to store:** delivered, opens, clicks, bounces, spam_reports

### Task 2.5: Klaviyo sync
- **Route:** `app/api/sync/klaviyo/route.ts`
- **Pipedream proxy URL:** `https://a.klaviyo.com/api/metrics/` + `https://a.klaviyo.com/api/lists/`
- **Config needed:** None
- **Data to store:** list_count, subscriber_count, campaign_stats

### Task 2.6: Pinterest sync
- **Route:** `app/api/sync/pinterest/route.ts`
- **Pipedream proxy URL:** `https://api.pinterest.com/v5/user_account/analytics`
- **Config needed:** None
- **Data to store:** impressions, saves, clicks, followers

---

## Priority 3: Content & Utility Integrations (no sync — action-oriented)

These don't need sync endpoints — they're used for publishing/reading content, not pulling metrics.

### Task 3.1: WordPress — publish endpoint
- Write posts via `https://public-api.wordpress.com/rest/v1.1/sites/{site}/posts/new`
- Or WP REST API: `https://{site}/wp-json/wp/v2/posts`
- Config needed: Site URL picker

### Task 3.2: Shopify — store data endpoint
- Pull products/orders via `https://{store}.myshopify.com/admin/api/2024-01/`
- Config needed: Already has store domain

### Task 3.3: Slack — notification delivery
- Send messages via `https://slack.com/api/chat.postMessage`
- Config needed: Channel picker via `https://slack.com/api/conversations.list`
- Use for: action approvals, alerts, weekly summaries

### Task 3.4: Notion — content library sync
- Read/write pages via `https://api.notion.com/v1/pages`
- Config needed: Database picker via `https://api.notion.com/v1/search`
- Use for: content calendar, brief storage

### Task 3.5: Google Sheets — data export
- Read/write via `https://sheets.googleapis.com/v4/spreadsheets/{id}`
- Config needed: Spreadsheet picker
- Use for: reporting, content calendars

### Task 3.6: Airtable — content database
- Read/write via `https://api.airtable.com/v0/{baseId}/{tableName}`
- Config needed: Base + table picker
- Use for: content tracking, campaign management

### Task 3.7: Webflow — site publishing
- Manage CMS items via `https://api.webflow.com/v2/sites/{site_id}/collections`
- Config needed: Site picker

### Task 3.8: Squarespace — site publishing
- Manage pages/blog via Squarespace API
- Config needed: Site picker

### Task 3.9: Calendly — meeting sync
- Pull events via `https://api.calendly.com/scheduled_events`
- Config needed: None
- Use for: lead tracking, meeting counts

### Task 3.10: ConvertKit — email stats
- Pull subscribers/sequences via `https://api.convertkit.com/v3/`
- Config needed: None
- Data: subscriber_count, sequences, automations

### Task 3.11: ActiveCampaign — email + CRM stats
- Pull contacts/campaigns via `https://{account}.api-us1.com/api/3/`
- Config needed: None
- Data: contacts, campaigns, automations, deals

### Task 3.12: X/Twitter — social stats
- Pull metrics via `https://api.twitter.com/2/users/me`
- Config needed: None
- Data: followers, tweets, impressions
- **Note:** Twitter API access is restricted/paid — may not work for all users

---

## Priority 4: Infrastructure

### Task 4.1: Wire Sync button on /connect page
Add `onClick` handler to the Sync button in ProviderCard that calls the correct `/api/sync/{provider}` route based on the provider.

### Task 4.2: Scheduled syncs
Create a cron job (or use existing agent scheduler) that runs daily syncs for all connected providers. Use the gateway's agent task system.

### Task 4.3: Analytics page — multi-provider display
Redesign the Analytics page to show data from ALL connected providers, not just GA4 and GSC. Show/hide sections based on which providers are connected and have data.

### Task 4.4: Config pickers for providers that need them
Several providers (Facebook, Instagram, LinkedIn, YouTube, etc.) need account/page/channel pickers after OAuth. Create generic list endpoints that fetch available accounts from each provider's API.

### Task 4.5: Sync status tracking
Add `last_sync_at`, `sync_status`, `sync_error` tracking to the integrations table so users can see when data was last pulled and if there were errors.

---

## Implementation Order

**Sprint 1 (highest impact):**
1. Fix dead Sync button (P0)
2. Facebook Pages sync (P1.1)
3. Google Ads sync (P1.3)
4. Meta Ads sync (P1.4)
5. Mailchimp sync (P1.5)

**Sprint 2:**
6. Instagram sync (P1.2)
7. LinkedIn sync (P1.6)
8. YouTube sync (P2.1)
9. Stripe sync (P2.2)
10. Multi-provider Analytics page (P4.3)

**Sprint 3:**
11. HubSpot sync (P2.3)
12. SendGrid sync (P2.4)
13. Slack notifications (P3.3)
14. Scheduled syncs (P4.2)
15. Config pickers (P4.4)

**Sprint 4:**
16-27. Remaining P2 and P3 tasks
