# PostHog Marketing Queries — HogQL Reference

*Harness reference for querying PostHog analytics for marketing data. Uses the personal API key approach (not the MCP OAuth flow, which has scope issues).*

---

## Authentication

Use the PostHog personal API key, not the MCP OAuth flow.

```bash
POSTHOG_API_KEY=$(grep '^POSTHOG_PERSONAL_API_KEY=' .env.local | cut -d= -f2-)
POSTHOG_PROJECT_ID=$(grep '^POSTHOG_PROJECT_ID=' .env.local | cut -d= -f2-)
```

**Base URL:** `https://us.posthog.com/api/projects/${POSTHOG_PROJECT_ID}/query`

> **Why not MCP?** The PostHog MCP server's OAuth flow returns `invalid_scope` errors. The personal API key approach is reliable and gives full HogQL access.

---

## Query Pattern

All queries use the HogQL endpoint via POST:

```bash
# Write query to temp file to avoid $ escaping issues in bash
node -e "
const query = {
  query: {
    kind: 'HogQLQuery',
    query: \`SELECT ... FROM events WHERE ...\`
  }
};
require('fs').writeFileSync('/tmp/posthog_query.json', JSON.stringify(query));
"

curl -s -X POST "https://us.posthog.com/api/projects/${POSTHOG_PROJECT_ID}/query" \
  -H "Authorization: Bearer ${POSTHOG_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @/tmp/posthog_query.json
```

> **CRITICAL: Use a temp file for queries.** PostHog property names use `$` prefixes (`properties.$current_url`, `properties.$referrer`) which bash interprets as variable expansion. Inline `node -e` with `$` in template literals also breaks. Always write to a file first.

---

## Common Marketing Queries

### 0. Event Hygiene Audit

Use this before attribution work. Unknown event names, missing session IDs, and missing UTMs create false certainty.

```sql
SELECT
  event,
  count() AS events,
  count(DISTINCT distinct_id) AS users,
  countIf(properties.$session_id IS NULL) AS missing_session_id,
  countIf(properties.utm_source IS NOT NULL) AS with_utm_source
FROM events
WHERE timestamp > now() - interval 30 day
GROUP BY event
ORDER BY events DESC
LIMIT 100
```

### 1. Pageviews by URL (Last 30 Days)

```sql
SELECT
  properties.$current_url AS url,
  count() AS views,
  count(DISTINCT properties.$session_id) AS sessions
FROM events
WHERE event = '$pageview'
  AND timestamp > now() - interval 30 day
GROUP BY url
ORDER BY views DESC
LIMIT 50
```

### 2. Pageviews with UTM Breakdown

```sql
SELECT
  properties.$current_url AS url,
  properties.utm_source AS utm_source,
  properties.utm_medium AS utm_medium,
  properties.utm_campaign AS utm_campaign,
  count() AS views
FROM events
WHERE event = '$pageview'
  AND timestamp > now() - interval 30 day
  AND properties.utm_source IS NOT NULL
GROUP BY url, utm_source, utm_medium, utm_campaign
ORDER BY views DESC
LIMIT 100
```

### 3. Traffic Sources (Referring Domains)

```sql
SELECT
  properties.$referrer AS referrer,
  count() AS visits,
  count(DISTINCT properties.$session_id) AS unique_sessions
FROM events
WHERE event = '$pageview'
  AND timestamp > now() - interval 30 day
  AND properties.$referrer IS NOT NULL
  AND properties.$referrer != ''
GROUP BY referrer
ORDER BY visits DESC
LIMIT 30
```

### 4. Landing Page Performance

```sql
SELECT
  properties.$current_url AS landing_page,
  count(DISTINCT properties.$session_id) AS sessions,
  count() AS total_pageviews,
  round(count() / count(DISTINCT properties.$session_id), 1) AS pages_per_session
FROM events
WHERE event = '$pageview'
  AND timestamp > now() - interval 30 day
GROUP BY landing_page
ORDER BY sessions DESC
LIMIT 30
```

### 5. Ad Visitor Journeys (UTM → Page Sequence)

```sql
SELECT
  properties.$session_id AS session_id,
  properties.utm_source AS utm_source,
  properties.utm_campaign AS utm_campaign,
  groupArray(properties.$current_url) AS page_sequence,
  count() AS pages_viewed,
  min(timestamp) AS first_pageview,
  max(timestamp) AS last_pageview
FROM events
WHERE event = '$pageview'
  AND timestamp > now() - interval 7 day
  AND properties.utm_source IS NOT NULL
GROUP BY session_id, utm_source, utm_campaign
ORDER BY first_pageview DESC
LIMIT 50
```

### 6. Signup Funnel Events

```sql
SELECT
  event,
  count() AS occurrences,
  count(DISTINCT distinct_id) AS unique_users
FROM events
WHERE event IN ('$pageview', 'signup_started', 'signup_completed', 'demo_requested', 'form_submitted')
  AND timestamp > now() - interval 30 day
GROUP BY event
ORDER BY occurrences DESC
```

> Adjust event names to match your product's actual event taxonomy.

### 7. Rage Clicks (Frustration Detection)

```sql
SELECT
  properties.$current_url AS url,
  count() AS rage_clicks,
  count(DISTINCT distinct_id) AS affected_users
FROM events
WHERE event = '$rageclick'
  AND timestamp > now() - interval 14 day
GROUP BY url
ORDER BY rage_clicks DESC
LIMIT 20
```

### 8. Campaign Attribution — Conversions by UTM

```sql
SELECT
  properties.utm_source AS source,
  properties.utm_medium AS medium,
  properties.utm_campaign AS campaign,
  countIf(event = '$pageview') AS pageviews,
  countIf(event = 'signup_completed') AS signups,
  countIf(event = 'demo_requested') AS demos,
  round(countIf(event = 'signup_completed') / countIf(event = '$pageview') * 100, 2) AS conversion_rate_pct
FROM events
WHERE timestamp > now() - interval 30 day
  AND properties.utm_source IS NOT NULL
GROUP BY source, medium, campaign
ORDER BY pageviews DESC
LIMIT 30
```

### 9. Daily Traffic Trend

```sql
SELECT
  toDate(timestamp) AS day,
  count() AS pageviews,
  count(DISTINCT distinct_id) AS unique_visitors,
  count(DISTINCT properties.$session_id) AS sessions
FROM events
WHERE event = '$pageview'
  AND timestamp > now() - interval 30 day
GROUP BY day
ORDER BY day ASC
```

### 10. Device / Browser Breakdown

```sql
SELECT
  properties.$device_type AS device,
  properties.$browser AS browser,
  count() AS pageviews,
  count(DISTINCT distinct_id) AS unique_visitors
FROM events
WHERE event = '$pageview'
  AND timestamp > now() - interval 30 day
GROUP BY device, browser
ORDER BY pageviews DESC
LIMIT 20
```

### 11. Signup Cohort Retention By Acquisition Source

```sql
WITH signups AS (
  SELECT
    distinct_id,
    min(timestamp) AS signup_time,
    argMin(properties.utm_source, timestamp) AS signup_source
  FROM events
  WHERE event = 'signup_completed'
    AND timestamp > now() - interval 90 day
  GROUP BY distinct_id
)
SELECT
  signup_source,
  count() AS signups,
  countIf(e.event = 'activation_completed'
    AND e.timestamp <= signups.signup_time + interval 14 day) AS activated_14d,
  round(activated_14d / signups * 100, 2) AS activation_rate_pct
FROM signups
LEFT JOIN events e ON e.distinct_id = signups.distinct_id
GROUP BY signup_source
ORDER BY signups DESC
```

### 12. Holdout Lift For Lifecycle Campaigns

Requires a stable property such as `lifecycle_holdout_group = 'test' | 'control'`.

```sql
SELECT
  properties.lifecycle_campaign AS campaign,
  properties.lifecycle_holdout_group AS holdout_group,
  count(DISTINCT distinct_id) AS users,
  countIf(event = 'purchase_completed') AS purchases,
  round(purchases / users * 100, 2) AS purchase_rate_pct
FROM events
WHERE timestamp > now() - interval 30 day
  AND properties.lifecycle_campaign IS NOT NULL
  AND properties.lifecycle_holdout_group IN ('test', 'control')
GROUP BY campaign, holdout_group
ORDER BY campaign, holdout_group
```

Report lift only after checking randomization, exclusions, sample size, and guardrails. Do not call attributed revenue incremental without a control group or another causal method.

### 13. Assisted Conversion Touches

```sql
WITH converters AS (
  SELECT
    distinct_id,
    min(timestamp) AS conversion_time
  FROM events
  WHERE event IN ('signup_completed', 'demo_requested', 'purchase_completed')
    AND timestamp > now() - interval 30 day
  GROUP BY distinct_id
)
SELECT
  e.properties.utm_source AS source,
  e.properties.utm_medium AS medium,
  e.properties.utm_campaign AS campaign,
  count(DISTINCT e.distinct_id) AS assisted_converters
FROM events e
INNER JOIN converters c ON e.distinct_id = c.distinct_id
WHERE e.timestamp BETWEEN c.conversion_time - interval 30 day AND c.conversion_time
  AND e.properties.utm_source IS NOT NULL
  AND e.event = '$pageview'
GROUP BY source, medium, campaign
ORDER BY assisted_converters DESC
LIMIT 50
```

Assisted touch counts are directional. They show presence in journeys, not causal lift.

### 14. Preference And Suppression Audit

```sql
SELECT
  event,
  properties.unsubscribe_scope AS unsubscribe_scope,
  properties.list_id AS list_id,
  count() AS events,
  count(DISTINCT distinct_id) AS users
FROM events
WHERE event IN ('email_subscribed', 'email_unsubscribed', 'email_complaint_received')
  AND timestamp > now() - interval 90 day
GROUP BY event, unsubscribe_scope, list_id
ORDER BY events DESC
```

---

## Response Parsing

PostHog returns results as `{ results: [[col1, col2, ...], ...], columns: ["col1", "col2", ...] }`.

```bash
# Parse with Node.js (Windows-safe)
node -e "
let d='';
process.stdin.on('data',c=>d+=c);
process.stdin.on('end',()=>{
  const r = JSON.parse(d);
  console.log('Columns:', r.columns.join(' | '));
  r.results.forEach(row => console.log(row.join(' | ')));
});
" < /tmp/posthog_response.json
```

---

## Environment Variables

Expected `.env.local` keys:

```
POSTHOG_PERSONAL_API_KEY=phx_...
POSTHOG_PROJECT_ID=<numeric project ID>
```

---

*Queries tested against PostHog Cloud (us.posthog.com) as of April 2026. HogQL syntax may evolve — check PostHog docs for breaking changes.*

## Source Notes

References retrieved 2026-05-17: PostHog HogQL docs, PostHog event docs, Google Meridian docs, and IAB incremental measurement guidance. Queries are templates; verify event names, consent rules, and identity-stitching policy before using results in client-facing claims.
