# Scripts & Tools — load-on-demand detail

> Referenced from `AGENTS.md` / `CLAUDE.md` ("Load-on-demand detail"). Restored 2026-07-05 from the pre-slimming `CLAUDE.md.bak-20260618` sections (Publishing & Social, Competitive Intelligence, Campaign Management, Reporting, Google Ads Integration, Knowledge Cloner, OpenClaw Autonomous Mode) and verified against the current scripts. Every path below is checked by `python scripts/doctor.py`.
>
> **Approval doctrine applies to everything here:** nothing publishes or mutates a live channel without human approval. Publishing is OFF by default (`publishing.enabled` in `config.yaml`, `KAI_PUBLISH_ENABLED` env override — see `scripts/harness_config.py`).

---

## Publishing & Social

The content pipeline can publish to CMS platforms and social media **after human approval**.

### CMS Publishing (`scripts/publish/`)

| Platform | Script | Auth |
|----------|--------|------|
| WordPress | `scripts/publish/wordpress.py` | `WP_URL` + `WP_USERNAME` + `WP_APP_PASSWORD` |
| Ghost | `scripts/publish/ghost.py` | `GHOST_URL` + `GHOST_ADMIN_KEY` |
| Webflow | `scripts/publish/webflow.py` | `WEBFLOW_API_TOKEN` + `WEBFLOW_SITE_ID` + `WEBFLOW_COLLECTION_ID` |
| Static sites | `scripts/publish/markdown_to_site.py` | None (outputs markdown with frontmatter) |

### Social Posting (`scripts/social/`)

| Platform | Script | Auth |
|----------|--------|------|
| LinkedIn | `scripts/social/linkedin.py` | `LINKEDIN_ACCESS_TOKEN` |
| Twitter/X | `scripts/social/twitter.py` | Twitter API keys (4 vars) |
| Buffer | `scripts/social/buffer.py` | `BUFFER_ACCESS_TOKEN` (posts to all connected platforms) |
| Platform rule changes | `scripts/social/platform_change_monitor.py` | None (monitors policy pages → `harness/references/social-platform-monitor-report.md`) |

Per-platform organic posting rules live in `harness/references/` (see the ad-policy/organic table in `.claude/rules/architecture-and-memory.md`). Automation limits: `harness/references/social-automation-rules.md`.

### CLI Integration

```bash
python scripts/harness_cli.py run --task blog --site mysite --keyword "..." --publish wordpress
```

(`kai-harness` is this CLI; wrappers live in `bin/`.)

---

## Competitive Intelligence

### Scripts (`scripts/intel/`)

| Script | Purpose |
|--------|---------|
| `python scripts/intel/competitor_monitor.py --check` | Scan competitor RSS feeds + sitemaps for new content |
| `python scripts/intel/competitor_monitor.py --diff` | Show new pages since last scan |
| `python scripts/intel/serp_tracker.py --track` | Track keyword rankings daily |
| `python scripts/intel/serp_tracker.py --alerts` | Show position changes > 3 |
| `python scripts/intel/content_gap.py --site X` | Keywords competitors rank for that you don't |
| `python scripts/intel/market_brief.py` | AI-synthesized weekly competitive brief |
| `python scripts/intel/brand_pulse.py <brand> --domain <domain>` | Brand-pulse snapshot (reviews, mentions, share of voice) |

Reddit listening: `scripts/reddit_monitor/reddit_listener.py` + `scripts/reddit_monitor/reddit_digest.py` (profiles in `scripts/reddit_monitor/profiles`).

Add competitors to `config.yaml`:
```yaml
competitors:
  - url: "https://competitor.com"
    name: "Competitor Name"
    rss_feed: "https://competitor.com/blog/feed"
```

---

## Campaign Management

### Campaign Planner (`scripts/campaigns/campaign_planner.py`)

Generates all assets for a multi-channel campaign:

```bash
python scripts/campaigns/campaign_planner.py --goal "product launch" --product myproduct --keyword "ai crm" --type launch --save campaigns/q1/
```

**Output:** landing page copy, 5-email nurture sequence, social variants (LinkedIn/Twitter/Instagram), ad variants (Meta + Google), content calendar.

**Campaign types:** launch, promotion, webinar, seasonal, awareness

### Campaign Tracker (`scripts/campaigns/campaign_tracker.py`)

Track campaign performance across channels:

```bash
python scripts/campaigns/campaign_tracker.py --create "Q1 Launch" --dir campaigns/q1/
python scripts/campaigns/campaign_tracker.py --update "Q1 Launch" --channel email --metric opens --value 2450
python scripts/campaigns/campaign_tracker.py --report "Q1 Launch"
```

Editorial calendar store: `scripts/campaigns/calendar.py` (JSONL under `data/calendar`, path via `get_calendar_dir()` in `scripts/harness_config.py`). The agent loop's hourly `editorial_calendar_tick` turns due `planned` items into drafts (gate/approval unchanged); items stuck in `generating` are swept back to `planned` after `stale_generating_hours` (default 6).

Campaign identity: `campaign_planner.py --save` mints a `campaign_id` (`cmp-YYYYMMDD-<slug>`), auto-creates the tracker row, and records a `campaign_plan` RuntimeStore artifact; the id threads through `engine.generate()` → `data/content_log.json` entries → 30-day pending checks. Merge a legacy `~/.kai-marketing/content-log.jsonl` with `python scripts/content/migrate_legacy_log.py` (idempotent).

### Goals & Weekly CMO Review

```bash
python scripts/harness_cli.py goals add --brand <brand> --name "<goal name>" --kpi <kpi> --target <value> --deadline YYYY-MM-DD
python scripts/harness_cli.py goals list      # pace vs deadline
python scripts/harness_cli.py goals update <goal-id> --current <value>
# Auto-refreshable KPIs: content_published, content_winners, organic_clicks, organic_impressions
```

Goals persist in `data/runtime/goals/` (`GoalRegistry`). The weekly `cmo_review` task (Mon 07:00, `agent/tasks/cmo_review.py`) refreshes goal progress from graded 30-day results, computes pace vs deadline, decomposes behind-pace goals into task graphs (`GoalDecomposer` → executed by `agent/loop.py`), flags failed graphs `needs_replan`, and writes a snapshot to `data/runtime/goals/reviews/`. All resulting actions flow through ActionStore approval + mandate validation. Without an LLM key it still snapshots and notifies — it just skips decomposition.

---

## Reporting

| Script | Output |
|--------|--------|
| `scripts/reporting/weekly_report.py` | Markdown report (traffic, SEO, content, competitive, recommendations) |
| `scripts/reporting/ceo_deck.py` | 5-slide Marp/Slidev deck |
| `scripts/reporting/dashboard.html` | Single-file HTML dashboard (open in browser, no server) |

```bash
python scripts/reporting/weekly_report.py --save reports/week.md
python scripts/build_dashboard.py   # rebuild the HTML dashboard
```

---

## Google Ads Integration

### API Scripts (`scripts/ads/`)

| Script | Purpose |
|--------|---------|
| `python scripts/ads/google_ads.py campaigns` | Campaign performance (spend, ROAS, CPC, CTR) |
| `python scripts/ads/google_ads.py keywords` | Keyword performance with Quality Scores |
| `python scripts/ads/google_ads.py search-terms` | Search terms report for negatives + opportunities |
| `python scripts/ads/google_ads.py summary` | Account-level summary |
| `python scripts/ads/google_ads_optimize.py --analyze` | Full AI-powered optimization report |
| `python scripts/ads/google_ads_optimize.py --negatives` | Negative keyword suggestions |
| `python scripts/ads/google_ads_optimize.py --budget` | Budget reallocation recommendations |

Read-only pulls are safe to run; **anything that mutates a live ad account goes through the approval gate first** (see `scripts/ads/upload.py` guardrails and `tests/test_ads_upload_guardrails.py`).

### Knowledge (`knowledge/frameworks/google-ads/`)

| File | Topic |
|------|-------|
| `knowledge/frameworks/google-ads/google-ads-auction-deep-dive.md` | Ad Rank, Quality Score, Smart Bidding |
| `knowledge/frameworks/google-ads/google-ads-pmax-deep-dive.md` | Performance Max architecture + optimization |
| `knowledge/frameworks/google-ads/google-ads-rsa-deep-dive.md` | RSA combinations, pinning, ad strength |

---

## Knowledge Cloner

Extract expert knowledge from any source into structured, actionable knowledge bases.

**Pipeline:** Discover → Transcribe → Extract → Distill → Synthesize → Operationalize → Quality Gate

```bash
python -m scripts.knowledge_cloner init "Expert Name" --domain "Marketing"
python -m scripts.knowledge_cloner discover expert-name --youtube https://www.youtube.com/@Channel/videos
python -m scripts.knowledge_cloner pipeline expert-name --max-cost 10.00
```

**Sources:** YouTube channels, podcast RSS feeds, articles, GitHub repos, local files

**Output (per expert):** 5 distilled docs (frameworks, tactics, edges, principles, anti-patterns), 4 operational outputs (quick reference, decision trees, checklists, AI prompts), and a quality report with 5-gate evaluation. Results land in `knowledge/people/`.

**Cost:** ~$3.50 for 40 sources via OpenRouter. See `scripts/knowledge_cloner/README.md`.

---

## Advanced: OpenClaw Autonomous Mode

The harness can run as a fully autonomous marketing agent via OpenClaw. This enables:

- Discord-based command interface for content requests (`scripts/content/harness_discord.py` — paths come from `scripts/harness_config.py`; set `CMO_BASE_DIR`/`VENV_PYTHON` for deployed installs)
- Scheduled heartbeats that monitor content performance (`workspace/HEARTBEAT.md`)
- Domain-specific agents with skill routing (`workspace/agents/`)
- Human-in-the-loop approval gates before publishing
- Persistent memory across sessions via git-backed state (`memory/`)

Setup requires a server, Discord bot token, and OpenClaw runtime. See `docs/OPENCLAW_SETUP.md` for the full walkthrough. The optional proactive memory scan in `workspace/HEARTBEAT.md` step 4 is external deployment tooling — configure it with `KAI_PROACTIVE_HEARTBEAT` or skip it on a fresh clone.

---

## Usage Pattern

```
1. Check the AGENTS.md Framework Map to find the right framework for your task
2. Load the primary framework file as context
3. Load the skill contract from harness/skill-contracts/
4. Create a brief using harness/brief-schema.md
5. Write the content applying framework rules
6. Run quality gate scripts to validate
7. Fix failures and re-run (max 2 retries)
8. Get human approval, then ship it
```
