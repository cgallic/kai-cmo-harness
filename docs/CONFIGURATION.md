# Configuration Reference

All configuration flows through two files: `config.yaml` (structure and settings) and `.env` (secrets and credentials). The template renderer reads `config.yaml` and generates personalized workspace files that OpenClaw reads at runtime.

---

## config.yaml

Copy `config.yaml.example` to `config.yaml` and fill in your values.

### owner

Your identity. Injected into agent definitions and content briefs.

```yaml
owner:
  name: "Connor Gallic"
  company: "Kai Ventures"
  timezone: "America/New_York"    # Used for cron scheduling and report timestamps
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Your name, used in agent prompts and press release templates |
| `company` | Yes | Company name, used in content briefs |
| `timezone` | Yes | IANA timezone string. Cron jobs and heartbeats run in this timezone |

### products

Each product you're marketing. Every product gets its own domain agent, analytics keys, Discord channel, and proof points for content briefs.

```yaml
products:
  - id: kaicalls
    name: "KaiCalls"
    url: "https://kaicalls.com"
    description: "AI-powered call answering service for law firms"
    supabase_url_env: "KAICALLS_SUPABASE_URL"
    supabase_key_env: "KAICALLS_SUPABASE_KEY"
    ga4_property_env: "GA_KAICALLS_PROPERTY_ID"
    gsc_url_env: "GSC_KAICALLS_URL"
    discord_channel_id: "1469307381103198382"
    proof_points: |
      - Price: $69/mo. ClaireAI: $650/mo. Smith.ai: $300-500/mo.
      - 64% of inbound law firm calls arrive after 5pm or on weekends.
      - ROI math: 1 extra case at $3,000 avg = 262% annual ROI at $828/yr.
      - Setup: live in under 24 hours.
      - Verticals: personal injury, family law, criminal defense, immigration.

  - id: buildwithkai
    name: "BuildWithKai"
    url: "https://buildwithkai.com"
    description: "AI product builder platform"
    supabase_url_env: "BWK_SUPABASE_URL"
    supabase_key_env: "BWK_SUPABASE_KEY"
    ga4_property_env: "GA_BWK_PROPERTY_ID"
    gsc_url_env: "GSC_BWK_URL"
    discord_channel_id: "1469307544454566020"
    proof_points: |
      - 13 businesses onboarded, 125 business plans generated.
      - Basic plan: $5.99/mo. Free tier available.
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Lowercase slug. Used as site key in CLI commands and analytics lookups |
| `name` | Yes | Display name. Appears in Discord posts and reports |
| `url` | Yes | Product URL. Used in briefs and internal link suggestions |
| `description` | Yes | One-line description. Injected into agent prompts |
| `supabase_url_env` | No | Name of the `.env` variable holding the Supabase URL for this product |
| `supabase_key_env` | No | Name of the `.env` variable holding the Supabase service role key |
| `ga4_property_env` | No | Name of the `.env` variable holding the GA4 property ID |
| `gsc_url_env` | No | Name of the `.env` variable holding the GSC site URL |
| `discord_channel_id` | No | Discord channel ID for this product's alerts and approvals |
| `proof_points` | No | Verified facts injected into content briefs. Use real numbers only |

### discord

Channel IDs for cross-product routing (OpenClaw path only).

```yaml
discord:
  writer_channel_id: "1473311759896019199"     # Content drafts for approval
  finance_channel_id: "1469310816158482603"     # Revenue, MRR, churn alerts
  updates_channel_id: "1152334071960190988"     # Daily/weekly reports
  health_channel_id: "1469310837469610216"      # Infrastructure health
  research_channel_id: "1472596453527654475"    # Research digests, patent scans
```

| Field | Required | Description |
|-------|----------|-------------|
| `writer_channel_id` | No | Where content drafts are posted for human approval |
| `finance_channel_id` | No | Revenue alerts, at-risk subscriptions, Stripe events |
| `updates_channel_id` | No | Aggregated daily/weekly reports |
| `health_channel_id` | No | Server health, uptime, deploy results |
| `research_channel_id` | No | Research digests, SEO opportunities, patent scans |

### harness

Content pipeline behavior.

```yaml
harness:
  four_us_threshold: 12          # Minimum Four U's score for long-form (ads/email default to 10)
  max_gate_retries: 2            # Auto-revision attempts before escalating to human
  self_improvement: true         # Enable 30-day checks + pattern extraction + defaults update
  llm_provider: "gemini"         # gemini | openai | anthropic
  llm_model: "gemini-2.0-flash"  # Model used for content generation and Four U's scoring
```

| Field | Default | Description |
|-------|---------|-------------|
| `four_us_threshold` | `12` | Long-form content minimum (blog, SEO, LinkedIn, press). Ads and email use 10 |
| `max_gate_retries` | `2` | Number of auto-revision attempts. After this, draft surfaces to human |
| `self_improvement` | `true` | Enables pattern extraction from winners and auto-update of MARKETING.md |
| `llm_provider` | `gemini` | Which LLM provider to use for content generation |
| `llm_model` | `gemini-2.0-flash` | Specific model. Gemini 2.0 Flash is fast and cheap for content |

### server

VPS deployment config (OpenClaw path only).

```yaml
server:
  host: "89.167.60.171"
  user: "root"
  workspace_path: "~/.openclaw/workspace"
  analytics_path: "/opt/cmo-analytics"
  venv_python: "/opt/cmo-analytics/venv/bin/python3"
```

| Field | Default | Description |
|-------|---------|-------------|
| `host` | — | VPS IP address |
| `user` | `root` | SSH user |
| `workspace_path` | `~/.openclaw/workspace` | Where OpenClaw reads its workspace files |
| `analytics_path` | `/opt/cmo-analytics` | Where analytics scripts and data live |
| `venv_python` | `/opt/cmo-analytics/venv/bin/python3` | Python binary inside the virtualenv |

### schedule

Cron expressions for automated tasks (OpenClaw path only). All times are in the `owner.timezone`.

```yaml
schedule:
  daily_report: "0 8 * * *"       # 8am daily
  weekly_report: "0 8 * * 1"      # 8am Monday
  pattern_extract: "0 8 * * 1"    # 8am Monday
  performance_check: "0 9 1 * *"  # 9am 1st of month
```

| Field | Default | Description |
|-------|---------|-------------|
| `daily_report` | `0 8 * * *` | Daily analytics digest posted to Discord |
| `weekly_report` | `0 8 * * 1` | Weekly strategy report |
| `pattern_extract` | `0 8 * * 1` | Analyze content winners, update what-works.md |
| `performance_check` | `0 9 1 * *` | Pull 30-day GSC + GA4 data for published content |

---

## .env

Copy `.env.example` to `.env`. Never commit `.env` to version control.

### LLM Providers

```bash
# Content generation (harness pipeline)
GEMINI_API_KEY=AIzaSyxxx

# Autonomous agent (OpenClaw path)
ANTHROPIC_API_KEY=sk-ant-xxx
AGENT_DEFAULT_MODEL=claude-3-5-haiku-20241022
AGENT_OPUS_MODEL=claude-opus-4-5-20251101
AGENT_HAIKU_MODEL=claude-3-5-haiku-20241022
```

### Supabase (per product)

```bash
# Generic / default
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxx

# Product-specific (names must match config.yaml supabase_url_env / supabase_key_env)
KAICALLS_SUPABASE_URL=https://xxx.supabase.co
KAICALLS_SUPABASE_KEY=eyJxxx
BWK_SUPABASE_URL=https://xxx.supabase.co
BWK_SUPABASE_KEY=eyJxxx
ABP_SUPABASE_URL=https://xxx.supabase.co
ABP_SUPABASE_KEY=eyJxxx
```

### Google Analytics 4

```bash
# Path to service account JSON (shared across all properties)
GOOGLE_CREDENTIALS_PATH=/opt/cmo-analytics/credentials/google-analytics-credentials.json

# Per-site property IDs (format: GA_{SITE_KEY}_PROPERTY_ID)
GA_KAICALLS_PROPERTY_ID=123456789
GA_BWK_PROPERTY_ID=234567890
GA_ABP_PROPERTY_ID=345678901
```

### Google Search Console

```bash
# Per-site URLs (format: GSC_{SITE_KEY}_URL)
# Use sc-domain: prefix for domain properties
GSC_KAICALLS_URL=sc-domain:kaicalls.com
GSC_BWK_URL=sc-domain:buildwithkai.com
GSC_ABP_URL=sc-domain:awesomebackyardparties.com
```

### Meta / Facebook Ads

```bash
META_ACCESS_TOKEN=your-access-token
META_AD_ACCOUNT_ID=act_123456789
```

### Stripe

```bash
STRIPE_API_KEY=sk_live_xxx
```

### Discord (OpenClaw path)

```bash
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=default-channel-id
```

### Email Services

```bash
RESEND_API_KEY=re_xxx
LOOPS_API_KEY=your-loops-key
LOOPS_API_KEY_KAICALLS=your-kaicalls-loops-key
```

### Cold Email (Instantly)

```bash
INSTANTLY_API_KEY=your-instantly-key
```

### LinkedIn Ads

```bash
LINKEDINADS_ACCESS_TOKEN=your-linkedin-access-token
```

### Twilio WhatsApp (agent notifications)

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=+14155238886
AGENT_OWNER_PHONE=+1234567890
```

### Agent Behavior

```bash
AGENT_POLLING_INTERVAL=60          # Seconds between scheduler checks
AGENT_MAX_CONCURRENT_TASKS=3       # Parallel task limit
AGENT_TASK_TIMEOUT=300             # Task timeout in seconds
AGENT_RETRY_ATTEMPTS=3            # Retry count on failure
AGENT_RETRY_DELAY=60              # Seconds between retries

AGENT_NOTIFY_ON_FAILURE=true      # WhatsApp alert on task failure
AGENT_NOTIFY_ON_APPROVAL=true     # WhatsApp alert when approval needed
AGENT_DAILY_SUMMARY=true          # Send daily summary to owner
AGENT_WHATSAPP_ENABLED=true       # Enable WhatsApp channel
AGENT_DISCORD_ENABLED=true        # Enable Discord channel
AGENT_SCHEDULER_ENABLED=true      # Enable scheduled task execution
```

### Webhook Gateway

```bash
CMO_GATEWAY_API_KEY=your-secure-api-key     # Generate with: openssl rand -hex 32
CMO_GATEWAY_HOST=0.0.0.0
CMO_GATEWAY_PORT=8088
CMO_GATEWAY_DEBUG=false
```

### Site Registry (JSON)

```bash
SITES_CONFIG={"kaicalls":{"name":"KaiCalls","url":"https://kaicalls.com","category":"product"},"buildwithkai":{"name":"BuildWithKai","url":"https://buildwithkai.com","category":"product"}}
```

---

## How Config Flows

```
config.yaml  ──┐
               ├──>  render_templates.py  ──>  workspace/ files  ──>  OpenClaw reads them
.env         ──┘

                     Generates:
                     ├── workspace/agents/*.md     (from .j2 templates)
                     ├── workspace/MARKETING.md    (if contains Jinja2 syntax)
                     ├── workspace/HEARTBEAT.md    (if contains Jinja2 syntax)
                     ├── workspace/AGENTS.md       (if contains Jinja2 syntax)
                     └── workspace/TOOLS.md        (if contains Jinja2 syntax)
```

### Template syntax

Workspace files can contain Jinja2 syntax. The renderer detects `{{ }}`, `{% %}`, or `{# #}` tags and renders them with the config context.

Available template variables:

```
{{ owner.name }}                    → "Connor Gallic"
{{ owner.company }}                 → "Kai Ventures"
{{ owner.timezone }}                → "America/New_York"

{% for product in products %}
  {{ product.id }}                  → "kaicalls"
  {{ product.name }}                → "KaiCalls"
  {{ product.url }}                 → "https://kaicalls.com"
  {{ product.description }}         → "AI-powered call answering..."
  {{ product.discord_channel_id }}  → "1469307381103198382"
  {{ product.proof_points }}        → multiline string
{% endfor %}

{{ discord.writer_channel_id }}     → "1473311759896019199"
{{ harness.four_us_threshold }}     → 12
{{ server.host }}                   → "89.167.60.171"
{{ schedule.daily_report }}         → "0 8 * * *"
```

Agent `.j2` templates in `workspace/agents/` are rendered to `.md` files automatically.

### Runtime config: MARKETING.md

The harness CLI (`scripts/harness_cli.py`) parses `MARKETING.md` on every run using the `MarketingConfig` class. It extracts:

- **Skill contracts table** -> per-format thresholds (Four U's minimum, SEO lint required/skipped)
- **Products + site keys table** -> Discord channel routing
- **Framework map table** -> which knowledge files to load per content type
- **Non-negotiables section** -> injected into every write prompt
- **Learned defaults section** -> auto-written by `harness_defaults_update.py` from winner patterns

MARKETING.md is the operating config for the write agent. Changing it changes pipeline behavior without editing code.

---

## Example Configs by Business Type

### SaaS Product

```yaml
owner:
  name: "Jane Smith"
  company: "Acme SaaS"
  timezone: "America/Los_Angeles"

products:
  - id: acmesaas
    name: "Acme SaaS"
    url: "https://acmesaas.com"
    description: "Project management for remote teams"
    ga4_property_env: "GA_ACMESAAS_PROPERTY_ID"
    gsc_url_env: "GSC_ACMESAAS_URL"
    proof_points: |
      - 2,400 teams onboarded. 94% retention at 12 months.
      - Pricing: $12/user/mo (Starter), $29/user/mo (Pro).
      - Average team saves 6.2 hours/week on status updates.

harness:
  four_us_threshold: 12
  max_gate_retries: 2
  llm_provider: "gemini"
  llm_model: "gemini-2.0-flash"
```

### E-commerce / DTC

```yaml
products:
  - id: mystore
    name: "MyStore"
    url: "https://mystore.com"
    description: "Sustainable home goods, direct to consumer"
    ga4_property_env: "GA_MYSTORE_PROPERTY_ID"
    gsc_url_env: "GSC_MYSTORE_URL"
    proof_points: |
      - 14,000+ orders shipped. 4.8 star average review.
      - Free shipping over $75. 30-day returns.
      - Bestseller: Bamboo Towel Set ($34.99), 3,200 units sold.

harness:
  four_us_threshold: 12
  max_gate_retries: 2
  llm_model: "gemini-2.0-flash"
```

### Agency with Multiple Clients

```yaml
products:
  - id: client_alpha
    name: "Alpha Corp"
    url: "https://alphacorp.com"
    description: "Enterprise cybersecurity platform"
    discord_channel_id: "111111111111111111"
    proof_points: |
      - SOC 2 Type II certified. 99.99% uptime SLA.

  - id: client_beta
    name: "Beta Fitness"
    url: "https://betafitness.com"
    description: "Online personal training marketplace"
    discord_channel_id: "222222222222222222"
    proof_points: |
      - 850 certified trainers. 12,000 active clients.
```

Each client gets its own domain agent, Discord channel, and analytics pipeline.
