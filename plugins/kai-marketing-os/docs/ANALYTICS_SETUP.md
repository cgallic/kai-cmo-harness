# Analytics Setup

Step-by-step instructions for connecting each analytics integration. All credentials go in `.env`. See `docs/CONFIGURATION.md` for the full `.env` reference.

---

## Google Analytics 4

GA4 provides traffic data: sessions, page views, sources, channels, daily trends.

### 1. Create a Google Cloud service account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select an existing one)
3. Enable the **Google Analytics Data API**:
   - Navigation menu > APIs & Services > Library
   - Search "Google Analytics Data API"
   - Click Enable
4. Create a service account:
   - Navigation menu > IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Name: `cmo-analytics` (or any name)
   - Grant no project-level roles (we grant access in GA4 directly)
   - Click Done
5. Create a key:
   - Click the service account you just created
   - Keys tab > Add Key > Create New Key > JSON
   - Download the JSON file
6. Save the JSON file:
   ```bash
   # Local development
   mkdir -p scripts/analytics/credentials
   mv ~/Downloads/your-file.json scripts/analytics/credentials/google-analytics-credentials.json

   # On VPS
   scp scripts/analytics/credentials/google-analytics-credentials.json root@your-vps:/opt/cmo-analytics/credentials/
   ```

### 2. Grant the service account access to GA4

1. Go to [Google Analytics](https://analytics.google.com/)
2. Admin (gear icon) > Account Access Management (or Property Access Management)
3. Click the **+** button > Add users
4. Enter the service account email (looks like `cmo-analytics@your-project.iam.gserviceaccount.com`)
5. Set role to **Viewer** (read-only is sufficient)
6. Click Add

Repeat for each GA4 property you want to track.

### 3. Get the property ID

1. In GA4, go to Admin > Property Settings
2. The Property ID is a number like `123456789` at the top
3. Copy it

### 4. Set environment variables

```bash
# Path to the service account JSON
GOOGLE_CREDENTIALS_PATH=/opt/cmo-analytics/credentials/google-analytics-credentials.json

# Per-site property IDs
GA_KAICALLS_PROPERTY_ID=123456789
GA_BWK_PROPERTY_ID=234567890
GA_ABP_PROPERTY_ID=345678901
```

### 5. Verify

```bash
cd /opt/cmo-analytics && source venv/bin/activate
python -m analytics.cli ga overview --site=kaicalls --days=7
```

Expected output: sessions, users, page views, bounce rate, avg session duration.

### CLI commands

```bash
cmo ga4 sites                                # List all configured sites
cmo ga4 overview --site=kaicalls --days=7    # Traffic overview
cmo ga4 pages --site=kaicalls --days=30      # Top pages
cmo ga4 sources --site=kaicalls --days=30    # Traffic sources
cmo ga4 channels --site=kaicalls --days=30   # Channel breakdown
cmo ga4 daily --site=kaicalls --days=14      # Daily trend
cmo ga4 all --days=7                         # All sites overview
```

---

## Google Search Console

GSC provides search data: queries, rankings, click-through rates, impressions, SEO opportunities.

### 1. Enable the Search Console API

1. In [Google Cloud Console](https://console.cloud.google.com/), select the same project
2. Enable the **Google Search Console API**:
   - APIs & Services > Library
   - Search "Search Console API" (also called "Google Search Console API")
   - Click Enable

### 2. Add your site to Search Console

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add property > Domain property (recommended)
3. Enter your domain: `kaicalls.com`
4. Verify ownership via DNS TXT record (follow the instructions shown)

### 3. Grant the service account access

1. In Search Console, go to Settings > Users and permissions
2. Click "Add user"
3. Enter the service account email: `cmo-analytics@your-project.iam.gserviceaccount.com`
4. Set permission to **Full** (read access requires Full in GSC)
5. Click Add

### 4. Set environment variables

```bash
# Per-site URLs (use sc-domain: prefix for domain properties)
GSC_KAICALLS_URL=sc-domain:kaicalls.com
GSC_BWK_URL=sc-domain:buildwithkai.com
GSC_ABP_URL=sc-domain:awesomebackyardparties.com

# The credentials JSON is the same file used for GA4
# GOOGLE_CREDENTIALS_PATH is already set
```

### 5. Verify

```bash
cmo gsc queries --site=kaicalls --limit=10
```

Expected output: top search queries with clicks, impressions, CTR, and average position.

### CLI commands

```bash
cmo gsc sites                                # List all configured sites
cmo gsc queries --site=kaicalls --limit=20   # Top search queries
cmo gsc pages --site=kaicalls --limit=20     # Top pages in search
cmo gsc opportunities --site=kaicalls        # SEO opportunities (high impressions, low CTR)
cmo gsc devices --site=kaicalls              # Device breakdown
cmo gsc countries --site=kaicalls            # Country breakdown
cmo gsc daily --site=kaicalls                # Daily performance
cmo gsc gaps --site=kaicalls                 # Content gaps
```

---

## Stripe

Stripe provides revenue data: MRR, subscriptions, charges, churn risk.

### 1. Get your API key

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Developers > API keys
3. Copy the **Secret key** (starts with `sk_live_` for production, `sk_test_` for testing)

Use the restricted key approach for better security:
1. Developers > API keys > Create restricted key
2. Grant read access to: Customers, Subscriptions, Charges, Invoices
3. Copy the restricted key

### 2. Set environment variable

```bash
STRIPE_API_KEY=sk_live_xxx
```

### 3. Verify

```bash
cmo stripe_report mrr
```

Expected output: current MRR, active subscription count.

### CLI commands

```bash
cmo stripe_report mrr                    # Current MRR
cmo stripe_report revenue --days=30      # Revenue summary
cmo stripe_report subs                   # Active subscriptions
cmo stripe_report customers --limit=50   # Customer list
cmo stripe_report overview               # Full overview
cmo stripe_report at-risk                # Churning subscriptions
```

### Note on shared Stripe accounts

If multiple products share the same Stripe account, MRR and revenue figures represent the combined total. The harness does not automatically split revenue by product. Tag subscriptions with product metadata in Stripe to enable per-product filtering.

---

## Supabase

Supabase provides product database access: leads, users, calls, business metrics.

### 1. Create a project (or use existing)

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. New Project (or select existing)
3. Note the project URL and anon/service role key

### 2. Get the service role key

1. In Supabase, go to Settings > API
2. Copy the **Project URL**: `https://xxx.supabase.co`
3. Copy the **service_role key** (under "Project API keys")

Use the service role key (not the anon key) for server-side analytics. It bypasses Row Level Security.

### 3. Set environment variables

```bash
# Per-product (names must match config.yaml supabase_url_env and supabase_key_env)
KAICALLS_SUPABASE_URL=https://xxx.supabase.co
KAICALLS_SUPABASE_KEY=eyJxxx

BWK_SUPABASE_URL=https://yyy.supabase.co
BWK_SUPABASE_KEY=eyJyyy
```

### 4. Verify

```bash
cmo kaicalls counts     # Check table row counts
cmo kaicalls dashboard  # Full dashboard
```

### CLI commands (per product)

```bash
# KaiCalls
cmo kaicalls leads --days=7 --limit=10    # Recent leads
cmo kaicalls calls --days=7               # Call volume
cmo kaicalls agents                       # Agent performance
cmo kaicalls dashboard --days=30          # Full dashboard

# BuildWithKai
cmo bwk businesses --limit=20            # All businesses
cmo bwk plans --limit=20                 # Business plans
cmo bwk dashboard                        # Full dashboard

# Amazing Backyard Parties
cmo abp leads --limit=20                 # Recent leads
cmo abp vendors                          # All vendors
cmo abp dashboard                        # Full dashboard
```

---

## Meta / Facebook Ads

Meta Ads API provides campaign data: spend, impressions, CTR, CPL, ROAS.

### 1. Create a Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. My Apps > Create App
3. Select "Business" type
4. Add the **Marketing API** product

### 2. Get an access token

**Short-lived token (testing):**
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Add permissions: `ads_read`, `ads_management`
4. Generate token
5. This token expires in ~1 hour

**Long-lived token (production):**
1. Exchange the short-lived token for a long-lived one:
   ```bash
   curl "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN"
   ```
2. This gives a 60-day token
3. For truly permanent access, set up a System User in Business Manager:
   - Business Settings > System Users > Add
   - Generate token with `ads_read` permission

### 3. Get your ad account ID

1. Go to [Meta Ads Manager](https://www.facebook.com/adsmanager/)
2. The ad account ID is in the URL or dropdown (format: `act_123456789`)
3. Include the `act_` prefix

### 4. Set environment variables

```bash
META_ACCESS_TOKEN=your-long-lived-or-system-user-token
META_AD_ACCOUNT_ID=act_123456789
```

### 5. Verify

```bash
cmo meta_ads campaigns
```

### CLI commands

```bash
cmo meta_ads campaigns                # All campaigns + status
cmo meta_ads spend --days=7           # Spend summary
cmo meta_ads performance --days=7     # Impressions, CTR, CPL, ROAS
cmo meta_ads dashboard                # Full overview
```

---

## Instantly (Cold Email)

Instantly provides cold email campaign data: sent, opened, replied, bounced.

### 1. Get your API key

1. Go to [Instantly Dashboard](https://app.instantly.ai/)
2. Settings > Integrations > API
3. Copy your API key

### 2. Set environment variable

```bash
INSTANTLY_API_KEY=your-instantly-key
```

### 3. Verify

```bash
cmo instantly campaigns
```

### CLI commands

```bash
cmo instantly campaigns                   # All campaigns + status
cmo instantly stats --all                 # Stats across all campaigns
cmo instantly stats --campaign_id=<id>    # Stats for one campaign
```

---

## Loops (Email Marketing)

Loops provides email automation: contacts, events, transactional sends.

### 1. Get your API key

1. Go to [Loops Dashboard](https://app.loops.so/)
2. Settings > API
3. Copy your API key

### 2. Set environment variables

```bash
LOOPS_API_KEY=your-default-loops-key
LOOPS_API_KEY_KAICALLS=your-kaicalls-loops-key   # If using separate account per product
```

### 3. Verify

```bash
cmo loops status
```

### CLI commands

```bash
cmo loops status                                              # API key + account name
cmo loops dashboard                                           # Account status + lists
cmo loops find --email=user@example.com                       # Find contact
cmo loops add --email=user@example.com --first_name=Jane      # Add/update contact
cmo loops event --email=user@example.com --event=signup       # Trigger automation
cmo loops send --email=user@example.com --transaction_id=xxx  # Send transactional email
```

Note: Loops does not expose campaign open/click analytics via API. Check the Loops dashboard for campaign stats.

---

## Resend (Transactional Email)

Resend provides email delivery data: sent, delivered, bounced, domain health.

### 1. Get your API key

1. Go to [Resend Dashboard](https://resend.com/overview)
2. API Keys > Create API Key
3. Copy the key

### 2. Set environment variable

```bash
RESEND_API_KEY=re_xxx
```

### 3. Verify

```bash
cmo resend_report domains
```

### CLI commands

```bash
cmo resend_report domains            # Domain health (verified domains)
cmo resend_report recent --limit=20  # Recent sent emails + delivery status
cmo resend_report stats --limit=100  # Delivery stats by site
cmo resend_report dashboard          # Full email delivery overview
```

---

## Credential File Locations

| File | Local Path | VPS Path |
|------|-----------|----------|
| `.env` | `kai-cmo-harness/.env` | `/opt/cmo-analytics/.env` |
| Google service account JSON | `scripts/analytics/credentials/google-analytics-credentials.json` | `/opt/cmo-analytics/credentials/google-analytics-credentials.json` |

The analytics config module searches for `.env` in this order:
1. `scripts/.env`
2. `scripts/analytics/.env`
3. `~/.cmo-agent.env`

The Google credentials file is searched in this order:
1. `GOOGLE_CREDENTIALS_PATH` env var (if set)
2. `scripts/analytics/credentials/google-analytics-credentials.json`
3. `~/.claude/google-analytics-credentials.json`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Permission denied" on GA4 | Service account email not added as Viewer in GA4 property |
| "403 Forbidden" on GSC | Service account email not added as user in Search Console (needs Full permission) |
| Empty results from GA4 | Check property ID is correct (Admin > Property Settings). New properties have no historical data |
| `GOOGLE_CREDENTIALS_PATH` not found | Verify the JSON file exists at the path. Use absolute paths in `.env` |
| Meta token expired | Short-lived tokens expire in 1h. Use a System User token for production |
| Stripe returns empty | Check if using test key (`sk_test_`) vs live key (`sk_live_`). Test mode has no production data |
| Supabase "Invalid API key" | Use the **service_role** key, not the anon key. The service_role key starts with `eyJ` and is much longer |
| Instantly "Unauthorized" | Regenerate API key in Instantly dashboard. Keys can be invalidated |
