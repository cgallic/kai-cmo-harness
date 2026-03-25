# Analytics & Attribution Playbook

> **Use when:** Setting up marketing analytics, building attribution models, creating dashboards, or answering "which channel actually drives revenue?"

---

## The Analytics Stack

### Essential Tools by Stage

| Stage | Free Tier | Paid Upgrade |
|-------|-----------|-------------|
| Web analytics | GA4 | Mixpanel, Amplitude, PostHog |
| Search analytics | Google Search Console | Ahrefs, SEMrush |
| Ad platform analytics | Built into each platform | Supermetrics, Funnel.io |
| Email analytics | Built into ESP | Klaviyo, Customer.io |
| Attribution | GA4 + UTMs | Triple Whale, Rockerbox, Northbeam |
| BI / dashboards | Looker Studio (free) | Tableau, Metabase, Preset |
| Session recording | Microsoft Clarity (free) | Hotjar, FullStory |
| A/B testing | Google Optimize (sunset) | VWO, Optimizely, PostHog |

### The 80/20 Setup
For most companies, this covers 80% of analytics needs:
1. **GA4** — traffic, conversions, user behavior
2. **Google Search Console** — search performance, keyword data
3. **UTM parameters** — campaign attribution
4. **Looker Studio** — dashboards connecting GA4 + GSC + ad platforms
5. **Microsoft Clarity** — heatmaps and session recordings (free, unlimited)

---

## UTM Parameter Standard

### The 5 UTM Fields

| Parameter | Required | Purpose | Example |
|-----------|----------|---------|---------|
| `utm_source` | Yes | Where traffic comes from | facebook, google, newsletter |
| `utm_medium` | Yes | How it gets to you | cpc, email, social, referral |
| `utm_campaign` | Yes | Which campaign | spring-sale-2026, product-launch |
| `utm_content` | Recommended | Which ad/link variant | hero-banner, sidebar-cta, variant-a |
| `utm_term` | Optional | Keyword (search ads) | ai-receptionist |

### UTM Naming Convention

```
Lowercase, hyphens, no spaces, no special characters.

FORMAT: utm_source={platform}&utm_medium={type}&utm_campaign={name}&utm_content={variant}

EXAMPLES:
  Meta cold ads:    ?utm_source=facebook&utm_medium=cpc&utm_campaign=trial-signup-q1&utm_content=pain-hook-video
  Email newsletter: ?utm_source=newsletter&utm_medium=email&utm_campaign=weekly-digest-20260324&utm_content=top-cta
  LinkedIn organic: ?utm_source=linkedin&utm_medium=social&utm_campaign=thought-leadership&utm_content=ai-receptionist-post
  Google Search:    ?utm_source=google&utm_medium=cpc&utm_campaign=brand-terms&utm_term=kaicalls
```

### UTM Tracking Spreadsheet

Maintain a master sheet to prevent UTM chaos:

| Date | Campaign | Source | Medium | Content | Full URL | Owner |
|------|----------|--------|--------|---------|----------|-------|
| 2026-03-24 | trial-signup | facebook | cpc | pain-hook | https://...?utm_... | Marketing |

---

## Attribution Models

### The Attribution Problem

A customer might see:
1. Facebook ad (day 1)
2. Google search (day 5)
3. Email newsletter (day 10)
4. Direct visit → purchase (day 12)

Which channel gets credit? The answer depends on the model.

### Model Comparison

| Model | How It Works | Best For | Bias |
|-------|-------------|----------|------|
| **Last Click** | 100% credit to last touchpoint | Quick decisions, simple reporting | Ignores discovery channels |
| **First Click** | 100% credit to first touchpoint | Understanding awareness | Ignores conversion channels |
| **Linear** | Equal credit to all touchpoints | Fair overview | Treats all touches equally (unrealistic) |
| **Time Decay** | More credit to recent touches | Considered purchases | Undervalues awareness |
| **Position-Based (U-Shape)** | 40% first, 40% last, 20% split middle | Balanced view | Arbitrary weighting |
| **Data-Driven** | ML-based, platform assigns credit | Large datasets (GA4 needs 600+ conversions/month) | Black box, platform-biased |
| **Incrementality** | A/B test: show ads vs don't | True causal impact | Expensive, complex |

### Recommended Approach

1. **Start with UTM + last-click** (simple, actionable)
2. **Layer on GA4 data-driven** when you have enough data (600+ conversions/month)
3. **Run incrementality tests** on your biggest spend channels quarterly
4. **Never trust a single model** — look at first-touch AND last-touch together

### The Blended CAC Approach

Instead of attributing perfectly, track blended metrics:

```
Blended CAC = Total marketing spend / Total new customers

Channel contribution: If you turn off a channel and CAC goes up, that channel was contributing.
```

This avoids the attribution rabbit hole for most companies.

---

## GA4 Setup Checklist

### Events to Configure

| Event | Trigger | Purpose |
|-------|---------|---------|
| `page_view` | Auto | Traffic measurement |
| `sign_up` | Account creation | Conversion |
| `begin_checkout` | Cart/checkout start | Funnel step |
| `purchase` | Payment completed | Revenue |
| `generate_lead` | Form submission | Lead gen |
| `view_item` | Product/pricing page view | Interest signal |
| `scroll` | 90% page depth | Engagement |
| `click` | Outbound link clicks | Exit behavior |
| `file_download` | PDF/resource download | Content engagement |
| `video_start` / `video_complete` | Video play/finish | Content engagement |

### Key Reports to Build

1. **Traffic Sources** — which channels bring visitors (and which convert)
2. **Landing Page Performance** — conversion rate by entry page
3. **User Journey** — path from first visit to conversion
4. **Content Performance** — which pages drive engagement and conversions
5. **Campaign Performance** — UTM-tagged campaign results

---

## Dashboard Template

### Executive Dashboard (Weekly)

```
MARKETING DASHBOARD — Week of {date}
═══════════════════════════════════════

HEADLINE METRICS:
  Website sessions:     {N}         ({+/-}% vs last week)
  New users:            {N}         ({+/-}%)
  Conversion rate:      {N}%        ({+/-}%)
  New customers:        {N}         ({+/-}%)
  Revenue (attributed): ${N}        ({+/-}%)
  Blended CAC:          ${N}        ({+/-}%)

CHANNEL BREAKDOWN:
┌──────────────┬──────────┬─────────┬──────┬────────┬────────┐
│ Channel      │ Sessions │ Signups │ CVR  │ Spend  │ CAC    │
├──────────────┼──────────┼─────────┼──────┼────────┼────────┤
│ Organic SEO  │   2,400  │    48   │ 2.0% │   $0   │  $0    │
│ Meta Ads     │   1,800  │    27   │ 1.5% │ $2,700 │ $100   │
│ Google Ads   │   1,200  │    30   │ 2.5% │ $3,000 │ $100   │
│ Email        │     800  │    40   │ 5.0% │  $200  │  $5    │
│ LinkedIn     │     400  │     8   │ 2.0% │  $800  │ $100   │
│ Direct       │     600  │    18   │ 3.0% │   —    │  —     │
│ Referral     │     300  │    12   │ 4.0% │   —    │  —     │
├──────────────┼──────────┼─────────┼──────┼────────┼────────┤
│ TOTAL        │   7,500  │   183   │ 2.4% │ $6,700 │ $36.61 │
└──────────────┴──────────┴─────────┴──────┴────────┴────────┘

TOP PERFORMING CONTENT:
  1. /blog/ai-receptionists-law-firms — 1,200 sessions, 24 signups (2.0% CVR)
  2. /blog/missed-calls-cost — 800 sessions, 20 signups (2.5% CVR)
  3. /pricing — 600 sessions, 30 signups (5.0% CVR)

ACTIONS THIS WEEK:
  - {action 1}
  - {action 2}
  - {action 3}
```

### Content Marketing Dashboard (Monthly)

```
CONTENT PERFORMANCE — {month}
═══════════════════════════════

PRODUCTION:
  Published:       {N} pieces
  Gate pass rate:  {N}% first attempt
  Avg quality:     {N}/100

PERFORMANCE (30-day graded):
  Winners:         {N} ({pct}%)
  Average:         {N} ({pct}%)
  Underperformers: {N} ({pct}%)

SEO:
  Organic sessions:    {N} ({+/-}% MoM)
  Keywords page 1:     {N} ({+/-})
  Avg position:        {N} ({+/-})
  Featured snippets:   {N}

TOP 5 by traffic: [table]
TOP 5 by conversions: [table]
BIGGEST MOVERS: [keywords that gained/lost position]
```

---

## Reporting Cadence

| Frequency | What | Audience | Depth |
|-----------|------|----------|-------|
| Daily | Spend pacing, ad disapprovals, site errors | Ops/marketing | Light — dashboard check |
| Weekly | Channel performance, content metrics, campaign KPIs | Marketing team | Medium — executive dashboard |
| Monthly | Full funnel analysis, CAC trends, content retro | Leadership | Deep — strategy report |
| Quarterly | Attribution analysis, channel mix optimization, YoY trends | Exec team | Strategic — board-level |

---

## Common Analytics Pitfalls

| Pitfall | Why It Happens | Fix |
|---------|---------------|-----|
| Vanity metrics | "1M impressions!" means nothing if 0 conversions | Report conversions and revenue, not reach |
| Attribution worship | Spending weeks perfecting attribution model | Use blended CAC, run incrementality tests |
| Data hoarding | Collecting everything, analyzing nothing | Define 5-7 KPIs, ignore the rest |
| Channel bias | "Our Meta ROAS is 5x!" (ignoring assisted conversions) | Look at first-touch AND last-touch |
| Short time horizons | "This campaign failed" (after 3 days) | Wait for statistical significance (minimum 2 weeks) |
| Ignoring dark social | DMs, Slack shares, word-of-mouth don't have UTMs | Track "How did you hear about us?" on forms |
| Tool sprawl | 12 analytics tools, none integrated | Consolidate into 3-4 core tools |
