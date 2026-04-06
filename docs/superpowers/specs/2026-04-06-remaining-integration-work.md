# Remaining Integration Work

**Status:** 14 of 29 providers have working sync. This doc covers everything left.

**What's done:** GA4, GSC, Facebook, Instagram, LinkedIn, YouTube, Pinterest, Google Ads, Meta Ads, Mailchimp, SendGrid, Klaviyo, HubSpot, Stripe — all have sync endpoints, config pickers (where needed), wired Sync buttons, and display on the Analytics page.

---

## Patterns to Follow

Every sync endpoint follows the same structure. Reference any existing one as a template:

```
app-meetkai/app/api/sync/{provider}/route.ts
```

**Standard flow:**
1. Auth check via `createClient()` + `supabase.auth.getUser()`
2. Parse `brand_id` from POST body, verify brand ownership
3. Find integration via `createServiceClient().from("integrations").select("*").eq("brand_id", brand_id).eq("provider", "{provider}").eq("status", "connected").order("created_at", { ascending: false }).limit(1)`
4. Call provider API via Pipedream proxy: `pd.proxy.get({ url, accountId: integration.connected_account_id, externalUserId: brand_id })`
5. Insert into `channel_snapshots` with `{ brand_id, channel, provider, snapshot_data }`
6. Update `integrations.last_sync_at`
7. Return `{ status: "synced", data: snapshot }`

**Pipedream client:**
```typescript
import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { PipedreamClient } from "@pipedream/sdk";

function getPd() {
  return new PipedreamClient({
    projectId: process.env.PIPEDREAM_PROJECT_ID!,
    projectEnvironment:
      (process.env.PIPEDREAM_ENVIRONMENT as "development" | "production") || "development",
    clientId: process.env.PIPEDREAM_CLIENT_ID!,
    clientSecret: process.env.PIPEDREAM_CLIENT_SECRET!,
  });
}
```

**Proxy response unwrapping:**
```typescript
const res = await pd.proxy.get({ url, accountId, externalUserId: brand_id });
const data = ((res as { data?: SomeType })?.data ?? res) as SomeType;
```

**After creating a sync endpoint, you must also:**
1. Add it to `SYNC_ENDPOINTS` in `app-meetkai/app/(dashboard)/connect/page.tsx` (line ~251)
2. If it needs a config picker, add `configRequired` to the provider entry in `app-meetkai/lib/types.ts`
3. If it needs a picker endpoint, create `app/api/sync/{provider}/{picker}/route.ts` (GET)

---

## Task 1: Content & Utility Sync Endpoints (10 providers)

These are mostly action-oriented (publish/read), but several should pull basic stats too.

### 1.1: ConvertKit sync
- **Route:** `app/api/sync/convertkit/route.ts`
- **API:** `https://api.convertkit.com/v3/subscribers?api_secret=...` (Pipedream handles auth)
- **Also:** `https://api.convertkit.com/v3/sequences` and `https://api.convertkit.com/v3/automations`
- **Channel:** `email`
- **Snapshot:** `{ subscriber_count, sequences_count, automations_count }`
- **Config:** None

### 1.2: ActiveCampaign sync
- **Route:** `app/api/sync/activecampaign/route.ts`
- **API:** `https://{account}.api-us1.com/api/3/contacts` (count), `/api/3/campaigns` (count), `/api/3/deals` (count + value)
- **Note:** Pipedream resolves the account subdomain from the connected account
- **Channel:** `email`
- **Snapshot:** `{ contacts_count, campaigns_count, deals_count, deals_value, automations_count }`
- **Config:** None

### 1.3: X/Twitter sync
- **Route:** `app/api/sync/twitter/route.ts`
- **API:** `https://api.twitter.com/2/users/me?user.fields=public_metrics`
- **Channel:** `social`
- **Snapshot:** `{ username, followers, following, tweet_count, listed_count }`
- **Config:** None
- **Note:** Twitter API access is restricted/paid — endpoint should gracefully handle 403 errors with a clear message like "Twitter API access requires an elevated developer account"

### 1.4: Calendly sync
- **Route:** `app/api/sync/calendly/route.ts`
- **API:** `https://api.calendly.com/users/me` then `https://api.calendly.com/scheduled_events?user={uri}&status=active&count=100`
- **Channel:** `scheduling`
- **Snapshot:** `{ upcoming_events, total_events_30d, event_types_count }`
- **Config:** None

### 1.5: Notion — read-only sync
- **Route:** `app/api/sync/notion/route.ts`
- **API:** `https://api.notion.com/v1/search` with `{ filter: { property: "object", value: "database" } }` — requires `Notion-Version: 2022-06-28` header
- **Channel:** `content`
- **Snapshot:** `{ databases_count, pages_count }`
- **Config:** None (just counting accessible resources)

### 1.6: Google Sheets — read-only sync
- **Route:** `app/api/sync/google-sheets/route.ts`
- **API:** `https://www.googleapis.com/drive/v3/files?q=mimeType='application/vnd.google-apps.spreadsheet'&fields=files(id,name,modifiedTime)&pageSize=20`
- **Channel:** `content`
- **Snapshot:** `{ spreadsheets_count, recent_sheets: [{ id, name, modified_at }] }`
- **Config:** None

### 1.7: Airtable — read-only sync
- **Route:** `app/api/sync/airtable/route.ts`
- **API:** `https://api.airtable.com/v0/meta/bases`
- **Channel:** `content`
- **Snapshot:** `{ bases_count, bases: [{ id, name }] }`
- **Config:** None

### 1.8: WordPress — site info sync
- **Route:** `app/api/sync/wordpress/route.ts`
- **API:** Try WP REST API: `https://{site}/wp-json/wp/v2/posts?per_page=1&_fields=id` (get total from headers), `/wp-json/wp/v2/pages?per_page=1&_fields=id`
- **Challenge:** Need the site URL — either from integration config or autodiscovery
- **Channel:** `website`
- **Snapshot:** `{ posts_count, pages_count, site_url }`
- **Config:** Add `configRequired: { key: "wordpress_site_url", label: "Site URL", type: "text" }` to the WordPress provider in types.ts

### 1.9: Shopify — store stats sync
- **Route:** `app/api/sync/shopify/route.ts`
- **API:** `https://{store}.myshopify.com/admin/api/2024-01/products/count.json`, `orders/count.json`
- **Already has:** `configRequired` with `shopify_store` text input in types.ts
- **Channel:** `website`
- **Snapshot:** `{ products_count, orders_count_30d, store_domain }`

### 1.10: Webflow / Squarespace / Slack / GBP — placeholder endpoints
These 4 are lower priority. Create minimal placeholder sync endpoints that:
- Verify the connection works (auth check + integration lookup)
- Return `{ status: "synced", data: { connected: true, provider: "{name}" } }`
- Save a minimal snapshot: `{ connected: true, synced_at: new Date().toISOString() }`
- Can be fleshed out later

**Routes:**
- `app/api/sync/webflow/route.ts` — channel: `website`
- `app/api/sync/squarespace/route.ts` — channel: `website`
- `app/api/sync/slack/route.ts` — channel: `notifications`
- `app/api/sync/gbp/route.ts` — channel: `analytics`

**After all 10 are created:** Add all to `SYNC_ENDPOINTS` in `app/(dashboard)/connect/page.tsx`:
```typescript
convertkit: "/api/sync/convertkit",
activecampaign: "/api/sync/activecampaign",
twitter: "/api/sync/twitter",
calendly: "/api/sync/calendly",
notion: "/api/sync/notion",
google_sheets: "/api/sync/google-sheets",
airtable: "/api/sync/airtable",
wordpress: "/api/sync/wordpress",
shopify: "/api/sync/shopify",
webflow: "/api/sync/webflow",
squarespace: "/api/sync/squarespace",
slack: "/api/sync/slack",
gbp: "/api/sync/gbp",
```

---

## Task 2: Infrastructure

### 2.1: Sync status tracking
Add visual sync status to the connect page ProviderCard.

**Changes to `app/(dashboard)/connect/page.tsx`:**
- Show `last_sync_at` timestamp below the provider name when the integration has been synced (use `timeAgo()` from `@/lib/utils`)
- If a sync fails (handleSync catches error), show the error inline on the card
- The `integration.last_sync_at` field already exists in the DB — just display it

### 2.2: Scheduled syncs (P4.2)
Create a cron-triggered API route that syncs all connected providers for all brands.

**Route:** `app/api/cron/sync-all/route.ts`

**Flow:**
1. Verify cron secret: `if (request.headers.get("authorization") !== \`Bearer \${process.env.CRON_SECRET}\`) return 401`
2. Fetch all integrations with `status = "connected"` using `createServiceClient()`
3. Group by `brand_id`
4. For each brand, call each provider's sync endpoint internally (import the handler or use fetch to localhost)
5. Log results
6. Return summary

**Vercel cron config** — add to `vercel.json`:
```json
{
  "crons": [
    { "path": "/api/cron/sync-all", "schedule": "0 6 * * *" }
  ]
}
```

### 2.3: Analytics page — add remaining providers to display
The Analytics page (`app/(dashboard)/analytics/page.tsx`) currently displays: Facebook, Instagram, LinkedIn, YouTube, Pinterest, Google Ads, Meta Ads, Mailchimp, SendGrid, Klaviyo, HubSpot, Stripe.

**Add display cards for the new providers in appropriate sections:**

In the **Social Media** section, add X/Twitter:
```typescript
{twitterSnap && (
  <MetricCard icon={Twitter} name="X / Twitter" color="text-gray-400" metrics={[
    { label: "Followers", value: formatNumber(twitterSnap.followers as number) },
    { label: "Tweets", value: formatNumber(twitterSnap.tweet_count as number) },
  ]} />
)}
```

In the **Email** section, add ConvertKit and ActiveCampaign:
```typescript
{ckSnap && (
  <MetricCard icon={UserCheck} name="ConvertKit" color="text-red-400" metrics={[
    { label: "Subscribers", value: formatNumber(ckSnap.subscriber_count as number) },
    { label: "Sequences", value: formatNumber(ckSnap.sequences_count as number) },
  ]} />
)}
{acSnap && (
  <MetricCard icon={Send} name="ActiveCampaign" color="text-blue-500" metrics={[
    { label: "Contacts", value: formatNumber(acSnap.contacts_count as number) },
    { label: "Campaigns", value: formatNumber(acSnap.campaigns_count as number) },
  ]} />
)}
```

Add a **Scheduling** section for Calendly:
```typescript
{calendlySnap && (
  <Section title="Scheduling">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <MetricCard icon={Calendar} name="Calendly" color="text-blue-500" metrics={[
        { label: "Upcoming", value: formatNumber(calendlySnap.upcoming_events as number) },
        { label: "Events (30d)", value: formatNumber(calendlySnap.total_events_30d as number) },
      ]} />
    </div>
  </Section>
)}
```

Add a **Content** section for Notion, Google Sheets, Airtable:
```typescript
{(notionSnap || sheetsSnap || airtableSnap) && (
  <Section title="Content Tools">
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {notionSnap && <MetricCard ... />}
      {sheetsSnap && <MetricCard ... />}
      {airtableSnap && <MetricCard ... />}
    </div>
  </Section>
)}
```

Remember to add the `getSnap()` calls for each new provider and the corresponding `const xxxSnap = getSnap(snapshots, "xxx")` declarations.

---

## Task 3: Bug — GSC "No sites found"

The GSC config picker on `/connect` shows "No sites found." The endpoint at `app/api/analytics/gsc-sites/route.ts` is correct — the issue is likely:

1. The Google account used for OAuth doesn't have verified sites in Search Console
2. The OAuth scope granted during Pipedream connection didn't include `webmasters.readonly`

**Improvement:** Update the "No sites found" message in the ConfigPicker component (`app/(dashboard)/connect/page.tsx` line ~199) to be more helpful:

Change:
```typescript
return (
  <p className="text-xs text-text-tertiary mt-2">
    No {cfg.label.toLowerCase()}s found.
  </p>
);
```

To:
```typescript
return (
  <p className="text-xs text-text-tertiary mt-2">
    No {cfg.label.toLowerCase()}s found.
    {provider.provider === "gsc" && " Make sure this Google account has verified sites in Search Console."}
  </p>
);
```

This requires passing `provider` into the ConfigPicker or checking `cfg.key` instead.

---

## File Reference

| File | Purpose |
|------|---------|
| `app/(dashboard)/connect/page.tsx` | Connect page — ProviderCard, ConfigPicker, SYNC_ENDPOINTS map |
| `app/(dashboard)/analytics/page.tsx` | Analytics page — multi-provider display |
| `lib/types.ts` | PROVIDERS array, ProviderConfig, configRequired definitions |
| `lib/hooks.ts` | useSnapshots, useIntegrations hooks |
| `app/api/sync/{provider}/route.ts` | Individual sync endpoints |
| `app/api/analytics/sync/route.ts` | GA4 sync (reference implementation) |
| `app/api/analytics/sync-gsc/route.ts` | GSC sync |
| `supabase/migrations/001_init.sql` | DB schema (integrations, channel_snapshots tables) |
