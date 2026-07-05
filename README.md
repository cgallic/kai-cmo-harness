# Kai Marketing OS: Claude Code Skills For Growth Work

**Kai turns a product repo into a marketing workspace.** It gives Claude Code a marketing team, a source-aware brief, channel playbooks, policy references, quality gates, approval rules, and memory so the next run starts smarter.

Use it when you want an AI operator to create growth plans, landing pages, emails, ads, SEO/AEO work, audits, content calendars, SDR handoff, or repurposed assets from the same files your product team already uses.

## Why People Star This Repo

- **42 public `/kai` commands** for strategy, distribution, content, ads, SEO, CRO, lifecycle, SDR, launches, and analytics.
- **45 canonical skill docs** with triggers, inputs, outputs, gates, provenance, and failure modes.
- **A real knowledge base**: 54 playbooks, 36 checklists, 27 frameworks, 26 channel guides, 8 personas, 18 references, and 30 skill contracts.
- **Guardrails built in**: Four U's scoring, banned-word checks, SEO lint, policy references, provenance lint, privacy scanning, and mutation-risk lint.
- **Local-first by default**: use it inside Claude Code from your repo before wiring live channels.
- **Approval-led automation**: dry-run first, review the artifact, then approve external actions.

## 30-Second Demo

See it work before you read anything else:

```bash
git clone https://github.com/cgallic/kai-cmo-harness.git
cd kai-cmo-harness
pip install google-genai requests beautifulsoup4
export GEMINI_API_KEY=your-free-key    # Get one at https://aistudio.google.com/apikey

python demo/demo.py --url "https://yoursite.com" --keyword "best crm for startups"
```

One command. One API key. Outputs a scored blog post in ~60 seconds: research -> brief -> write -> quality gate -> scorecard.

See pre-generated examples in `demo/examples/`.

## Quick Start

Install the skills:

```bash
curl -fsSL https://raw.githubusercontent.com/cgallic/kai-cmo-harness/main/install.sh | bash
```

Open Claude Code in a product repo and run:

```text
/kai-start
/kai-growth-plan
```

`/kai-start` creates or refreshes `MARKETING.md` from the repo. `/kai-growth-plan` turns that context into a stage-specific plan, recommended workflows, metrics, budget notes, and anti-patterns.

Want the short setup guide? Read [Quick Start](docs/QUICK_START.md).

## 5 Useful First Runs

| Goal | Command | What Kai returns |
|---|---|---|
| Find the next growth move | `/kai-growth-plan` | Stage, channel bets, constraints, and what to ignore |
| Build the first growth hire OS | `/kai-growth-hacker` | B2B/B2C channel map, fan-out plan, test cards, gates, and metrics |
| Rewrite a page | `/kai-landing-page` | Page copy, proof table, CRO hypotheses, and approval notes |
| Plan search content | `/kai-content-calendar` | Topic map, keywords, personas, and source-backed priorities |
| Audit the funnel | `/kai-cro` | Findings, evidence, data gaps, and test ideas |
| Repurpose a source asset | `/kai-repurpose` | Quotes, social posts, email angles, clips, and a kill list |

## What Makes Kai Different

Most AI marketing tools start from a blank chat box. Kai starts from the repo: product docs, code, routes, pricing, examples, claims, and marketing memory.

That means the system can:

- create a brief before it writes
- choose the right channel playbook
- trace claims to evidence
- block risky copy before it ships
- route live actions through approval
- remember what worked after results come back

Kai is built for founders, indie hackers, SaaS teams, agencies, and product engineers who want Claude Code to help with actual growth work instead of generic copy.

## What This Is Not

Kai is not a prompt pack, a standalone chatbot, or a content spinner. It is a local operating surface for marketing work that needs source context, policy checks, quality gates, and repeatable workflows.

Autonomous campaign management is a guarded phase, not the starting promise. Kai ships the trusted operating layer first: product context, policy constraints, evidence, approvals, memory, and connector health.

## Install Options

**One-liner:**

```bash
curl -fsSL https://raw.githubusercontent.com/cgallic/kai-cmo-harness/main/install.sh | bash
```

**Manual:**

```bash
git clone https://github.com/cgallic/kai-cmo-harness.git /tmp/kai-install \
  && mkdir -p ~/.claude/skills \
  && cp -r /tmp/kai-install/harness/skills/kai /tmp/kai-install/harness/skills/kai-* /tmp/kai-install/harness/skills/kaicalls-design ~/.claude/skills/ \
  && rm -rf /tmp/kai-install \
  && echo "Installed. Type /kai-start in Claude Code."
```

## Repository Structure

```
kai-cmo-harness/
├── CLAUDE.md                    # Standalone Claude Code entry point
├── config.yaml.example          # Central config template
├── setup.sh                     # Interactive setup wizard
├── render_templates.py          # Jinja2 renderer for workspace files
│
├── knowledge/                   # 100+ marketing frameworks (ships as-is)
│   ├── frameworks/              # Core frameworks (AEO, copywriting, Meta ads)
│   ├── channels/                # Channel guides (blog, email, TikTok, etc.)
│   ├── checklists/              # Validation checklists
│   ├── personas/                # 8 audience personas
│   ├── playbooks/               # Strategic playbooks
│   └── design/                  # UI/UX design patterns
│
├── harness/                     # Pipeline config + quality gates
│   ├── brief-schema.md          # Content brief format
│   ├── skill-contracts/         # Format-specific YAML contracts
│   └── references/              # Cold email rules, Google Ads rules
│
├── workspace/                   # OpenClaw workspace templates
│   ├── MARKETING.md             # Operating config (parsed by harness)
│   ├── SOUL.md                  # Voice profile + banned words
│   ├── HEARTBEAT.md             # Agent heartbeat protocol
│   ├── AGENTS.md                # Agent hierarchy + data tools
│   ├── TOOLS.md                 # Tool configuration
│   └── agents/                  # Domain agent templates (.j2)
│
├── demo/                        # Instant demo (one command, one API key)
│   ├── demo.py                  # Single-file demo script
│   └── examples/                # Pre-generated output examples
│
├── scripts/                     # Python pipeline + analytics
│   ├── harness_cli.py           # Main CLI (brief → write → gate → approve → publish)
│   ├── quality_gates/           # four_us_score, banned_word_check, seo_lint
│   ├── self_improvement/        # Pattern extraction + harness updates
│   ├── content/                 # Content generation helpers
│   ├── leads/                   # Lead pipeline + conversion
│   ├── ads/                     # Ad management (Meta, Google Ads API)
│   ├── analytics/               # GA4, GSC, Stripe, Supabase, Meta Ads
│   ├── publish/                 # CMS publishing (WordPress, Ghost, Webflow, static)
│   ├── social/                  # Social posting (LinkedIn, Twitter/X, Buffer)
│   ├── intel/                   # Competitor monitoring, SERP tracking, content gaps
│   ├── campaigns/               # Campaign planner + tracker
│   ├── reporting/               # Weekly reports, CEO deck, HTML dashboard
│   └── knowledge_cloner/        # Expert knowledge extraction pipeline (14 modules)
│
├── agent/                       # Autonomous loop (optional)
│   ├── loop.py, scheduler.py    # Task scheduling + execution
│   ├── channels/                # Discord, WhatsApp integrations
│   └── tasks/                   # Generic + example product handlers
│
├── gateway/                     # FastAPI webhook gateway (optional)
│
├── deploy/                      # VPS deployment templates
│   ├── cloud-config.yaml.j2    # Cloud-init template
│   ├── cmo-agent.service        # systemd service
│   └── deploy.sh                # Git pull → restart → health check
│
├── examples/                    # Config examples by business type
│   ├── config.yaml.saas
│   ├── config.yaml.ecommerce
│   └── config.yaml.agency
│
└── docs/                        # Documentation
    ├── QUICK_START.md
    ├── CONFIGURATION.md
    ├── ADDING_PRODUCTS.md
    ├── ANALYTICS_SETUP.md
    └── ARCHITECTURE.md
```

First run: open Claude Code in any product repo and type `/kai-start`. Or type `/kai` to see the 42 public router commands. The [public skill manifest](docs/skill-manifest/README.md) documents 45 canonical `kai-*` skill pages.

## Current Status (v1.0.0, updated May 2026)

| Layer | Status | Notes |
|-------|--------|-------|
| Claude Code skill surface | Working | 42 public `/kai` router commands and 45 canonical skill pages load repo context, frameworks, contracts, and policy references |
| Runtime models + persistence | Built | Atomic writes, thread-safe records, audit log |
| Business profiling + audit engines | Built | Archetype detection, overlay inference, 8 audit categories, severity-weighted scoring, and multi-location support |
| Proposal ranking + bundling | Built | 5-factor weighted, dependency-aware |
| Approval + action lifecycle | Built | State machine enforced, tested |
| Compliance engine | Built | 100+ rules and 50+ regex patterns |
| Content pipeline + quality gates | Built | LLM-backed via `scripts/content/engine.py` |
| Knowledge base | Built | Current inventory is documented in `docs/system/governance-and-quality.md` |
| Connector execution | Wired, credential-gated | Pipedream-backed execution and direct script clients exist; live external actions require connected accounts and credentials |
| Learning + memory | Partial | Writeback and persistence exist; automatic retrieval into every proposal/content path is still being connected |
| Creative module | Partial | Generates briefs/templates; final prose is currently produced through the content scripts and Claude Code skills |
| Watchers/monitoring | Partial | Threshold logic is real; live data feeds, scheduling, and notifications are still being connected |
| Autonomous campaign loops | Guarded roadmap | Ad/reward components exist; unattended live-channel operation remains approval-gated and connector-dependent |
| Remote automation scheduling | Planned | Defined in module manifests, not triggered |

For the full assessment, see `docs/superpowers/specs/2026-04-03-system-current-state-report.md`.

## Related Links

- [MeetKai](https://meetkai.xyz): the operator layer behind Kai Marketing OS workflows.
- [KaiCalls](https://kaicalls.com): a Kai-owned AI voice agent product for small-business phone answering and lead capture when the business is phone-led.
- [Connor Gallic](https://connorgallic.com): founder building Kai, KaiCalls, and AI automation systems.
- [How Kai runs paid ads](docs/AI_POWERED_ADS_SYSTEM.md): plain-English explanation of the paid media workflow.
- [System guide](docs/system/README.md): architecture pages, Mermaid diagrams, and runtime schemas.
- [Public skill manifest](docs/skill-manifest/README.md): versioned API-style docs for every canonical `kai-*` skill.

## Optional Dashboard Deployment

Kai includes an interactive dashboard for active goals, tasks, and integrations.

### Path A: Direct Browser Deploy
1. Start the local web server by double-clicking `serve.bat` on Windows or running `./serve.sh` on macOS/Linux.
2. Open `http://localhost:8000/workspace/dashboard.html`.
3. Click **One-Click Deploy**.
4. Enter a Netlify Personal Access Token.
5. Deploy the dashboard. The URL and Site ID are cached in browser `localStorage`.

### Path B: Desktop Launchers
- **Windows:** double-click `deploy.bat`.
- **macOS/Linux:** run `./deploy.sh`.

### Path C: Git-Backed Hosting
Push this repository to GitHub and link it to Vercel or Netlify. The repo includes `vercel.json` and `netlify.toml`.

## Publishing

Publishing is truthful and double-opt-in. The content engine never invents URLs: a gate-approved piece either publishes for real — when `publishing.enabled` plus a `publishing.sites.<site>.platform` entry are set in `config.yaml` (env override `KAI_PUBLISH_ENABLED`) — and logs the URL the CMS returned, or it's logged as `approved_unpublished` until you publish manually and backfill with `content_log.mark_published(entry_id, url)`. That backfill is also what arms the 30-day performance check. WordPress publishes are idempotent (slug lookup updates instead of duplicating) and default to `status=draft`.

The legacy CLI path publishes explicitly:

```bash
# Publish to WordPress
kai-harness run --task blog --site mysite --keyword "ai crm" --publish wordpress

# Publish to Ghost CMS
kai-harness run --task blog --site mysite --keyword "ai crm" --publish ghost

# Generate static site markdown (Hugo/Jekyll/Astro)
kai-harness run --task blog --site mysite --keyword "ai crm" --publish markdown
```

Social media posting:

```bash
python scripts/social/linkedin.py --content "Your LinkedIn post"
python scripts/social/twitter.py --content "Your tweet"
python scripts/social/buffer.py --content "Scheduled post" --platforms linkedin twitter
```

## Competitive Intelligence

Monitor competitors automatically:

```bash
kai-harness intel --check               # RSS + sitemap scan
kai-harness intel --diff                # New pages since last check
kai-harness intel --gaps --site mysite  # Keywords they rank for, you don't
kai-harness intel --brief               # AI-synthesized weekly market brief
```

## Campaign Management

Generate all assets for a multi-channel campaign:

```bash
kai-harness campaign --goal "product launch" --product myproduct --keyword "ai crm" --save campaigns/q1/
```

Generates: landing page, 5-email sequence, social variants (LinkedIn/Twitter/Instagram), ad variants (Meta + Google), content calendar. `--save` mints a `campaign_id` that threads through the tracker, runtime artifacts, the content log, and 30-day performance checks.

## Goals & the Weekly CMO Review

Give the machine targets and it plans against them:

```bash
python scripts/harness_cli.py goals add --brand mysite --name "Q3 signups" --kpi signups --target 500 --deadline 2026-09-30
python scripts/harness_cli.py goals list   # shows pace vs deadline
```

Every Monday the agent loop's `cmo_review` task measures each goal's pace from graded 30-day results, decomposes behind-pace goals into task graphs, and executes them through the normal approval gates. It also runs the 30-day performance check (nightly), weekly pattern extraction, and an hourly editorial-calendar tick (`data/calendar/editorial.jsonl`) — dated content plans become pipeline runs automatically.

## Reporting

```bash
kai-harness weekly-report                          # Full weekly report
kai-harness weekly-report --save reports/week.md   # Save to file
kai-harness dashboard                              # Open HTML dashboard in browser
python scripts/reporting/ceo_deck.py               # Generate 5-slide CEO deck
```

## Google Ads Integration

```bash
python scripts/ads/google_ads.py campaigns         # Campaign performance
python scripts/ads/google_ads.py keywords           # Keyword data
python scripts/ads/google_ads.py search-terms       # Find negatives + opportunities
python scripts/ads/google_ads_optimize.py --analyze # AI-powered optimization
```

## Knowledge Cloner

Extract expert knowledge from YouTube, podcasts, articles, and GitHub repos into structured frameworks:

```bash
python -m scripts.knowledge_cloner init "Alex Hormozi" --domain "Business"
python -m scripts.knowledge_cloner discover alex-hormozi --youtube https://www.youtube.com/@AlexHormozi/videos --limit 20
python -m scripts.knowledge_cloner pipeline alex-hormozi --max-cost 10.00
```

6-phase pipeline: Discover → Transcribe → Extract → Distill → Synthesize → Operationalize. Outputs 5 distilled docs + 4 operational tools + quality report. ~$3.50 for 40 sources via OpenRouter.

See `scripts/knowledge_cloner/README.md` for full docs.

## Self-Improvement

## Why this exists

Most AI marketing tools are either:

1. a blank chat box,
2. a narrow content generator, or
3. a dashboard that cannot understand your product repo.

Kai does the opposite. It runs where your product already lives — the terminal — and gives Claude Code a structured marketing operating system: command routing, strategy documents, platform policies, channel playbooks, QA gates, approval workflows, runtime models, and repeatable growth workflows.

That is why the current moat is the repo-native operating layer. Kai makes marketing behave more like engineering work: source-aware, inspectable, gated, and repeatable. Campaign automation becomes safer because the system already knows the product, the claims, the rules, and the approval path.

## Product shape

### Kai Runtime

The code-level workspace layer:

- workspace profile
- brand memory
- module activation
- run and artifact persistence
- approval state
- integrations and connector health

### Kai Operator Surface

The interactive layer builders use today:

- `/kai` skills in Claude Code
- local CLI and gateway surfaces
- dashboard artifacts
- quality gates and approval workflows

### Kai Marketing OS

The marketing-specific operating system:

- quality gates
- archetype-specific workflows
- campaign and content orchestration
- approvals
- approval-led learning loops

## Quick examples

| Need | Command | Output |
|---|---|---|
| "What should I do for marketing?" | `/kai-growth-plan` | Stage-specific growth plan with what to do and what to ignore |
| "Write a landing page" | `/kai-landing-page` | Hero, value props, objections, proof, CTAs, and page structure |
| "Create my ad campaign" | `/kai-ad-campaign` | Paid campaign with funnel stages, variants, and platform constraints |
| "Write all my product emails" | `/kai-email-system` | Welcome, activation, onboarding, trial, retention, and win-back emails |
| "Plan a month of content" | `/kai-content-calendar` | Keyword- and persona-mapped content calendar |
| "Audit my marketing" | `/kai-audit` | Prioritized marketing health report |
| "Improve AI-search visibility" | `/kai-surround-sound` | Agent-readiness, source-quality, and AI-search visibility strategy |
| "Turn this blog into social posts" | `/kai-repurpose` | 15–25 assets for LinkedIn, X, TikTok, Instagram, email, and YouTube |

## How it works

The first time you run a `/kai` command in a project, Kai:

1. **Reads your codebase** — `CLAUDE.md`, `README.md`, package files, routes, schemas, product docs, and existing marketing notes.
2. **Builds a runtime profile** — workspace, brand, archetype/module defaults, proof points, channels, and operating constraints.
3. **Creates `MARKETING.md` as a readable export** — ICP, personas, brand voice, positioning, value props, landscape, and operating defaults.
4. **Runs the workflow** — writes, audits, plans, scores, researches, routes approvals, and packages the requested marketing asset.

Every later command should run from the same workspace/brand/module model. `MARKETING.md` remains useful for humans, while the runtime contract lives in code.

## Architecture

```text
Kai Marketing OS
  -> outcome engine, quality gate, approvals, archetype modules

Kai Runtime
  -> skills, subagents, hooks, memory, plugins, local/remote runs

Implementation
  -> scripts/content, scripts/quality, gateway, agent, knowledge
```

The canonical runtime models live in `kai/runtime/`.

## 42 public router commands, 45 canonical skills

These commands work through Claude Code's skill system. They load knowledge files and framework instructions for the LLM. They do not invoke the `kai/` Python runtime directly.

The table below reflects the `/kai` router surface. The complete canonical skill inventory lives in the [public skill manifest](docs/skill-manifest/README.md), which includes 45 canonical `kai-*` pages.

### Produce marketing assets

| Command | What you get |
|---|---|
| `/kai-write` | One piece of content: blog, email, LinkedIn post, ad, press release, script, or landing copy |
| `/kai-landing-page` | Complete conversion-focused landing page copy |
| `/kai-email-system` | Full lifecycle and transactional email system |
| `/kai-ad-campaign` | Paid campaign across major ad platforms |
| `/kai-content-calendar` | Month or quarter of planned content mapped to keywords and personas |
| `/kai-social` | Batch social posts across LinkedIn, X, TikTok, Instagram, and YouTube |
| `/kai-video` | Video scripts and clipping plans for short-form and long-form video |
| `/kai-cold-outreach` | Cold email sequences and outbound messaging |
| `/kai-sdr-operator` | SDR operator package for lead sources, scoring, outreach handoff, and reply triage |
| `/kai-sdr-reply-triage` | Reply classification, suppression handling, CRM handoff, and next actions |
| `/kai-sales-meeting-prep` | Meeting briefs, discovery plans, follow-up drafts, and sales handoff notes |
| `/kai-reddit-listen` | Monitor subreddits and draft profile-driven replies to Discord |
| `/kai-newsletter` | Newsletter editions, subject lines, and structure |
| `/kai-case-study` | Customer case study from interview notes or product data |
| `/kai-product-maker` | Ship a Gumroad-ready digital product: ebook, card deck, flipbook, or guide |
| `/kai-repurpose` | One source asset turned into 15–25 channel-native pieces |
| `/kai-launch` | Product launch system: emails, ads, PR, social, content, and timeline |
| `/kai-retarget` | Retargeting and remarketing campaign plan |
| `/kai-influencer` | Creator and influencer marketing campaign |
| `/kai-webinar` | Webinar or event marketing plan and follow-up |
| `/kai-podcast` | Podcast launch or guest strategy |
| `/kai-abm` | Account-based marketing for enterprise sales |
| `/kai-partnership` | Co-marketing and partnership campaign |

### Audit and improve

| Command | What you get |
|---|---|
| `/kai-gate` | Quality score for any content using Four U's, banned words, specificity, proof, and platform checks |
| `/kai-audit` | Full marketing audit across SEO, content, email, ads, social, CRO, and positioning |
| `/kai-weekly-audit` | 7-day marketing scorecard with urgent flags, source-backed findings, and actions |
| `/kai-monthly-audit` | 30-day executive marketing review with strategic learning and next-month plan |
| `/kai-seo-audit` | Technical SEO and semantic SEO audit with prioritized fixes |
| `/kai-cro` | Conversion-rate audit for landing pages and funnels |
| `/kai-html-presentation` | Client-ready HTML deck for audit and report delivery |
| `/kai-data-dashboard` | Dashboard specs or static dashboards from sourced Kai data |

### Plan strategy

| Command | What you get |
|---|---|
| `/kai-brief` | Content brief before writing |
| `/kai-growth-plan` | Marketing plan by stage: pre-launch, launch, growth, or scale |
| `/kai-growth-hacker` | First-growth-hire distribution OS across B2B and B2C channels |
| `/kai-brand` | Brand positioning and messaging framework |
| `/kai-budget` | Marketing budget and channel allocation |
| `/kai-retention` | Customer retention system and lifecycle plan |

### Research and analyze

| Command | What you get |
|---|---|
| `/kai-competitors` | Competitive teardown and sales battlecards |
| `/kai-surround-sound` | AEO/GEO strategy for agent-readiness, source-quality, and measured AI-search visibility |
| `/kai-analytics` | Analytics and attribution setup |
| `/kai` | Command router and help menu |

## What is included

Kai ships with a real marketing knowledge base, more than prompts:

- **54 marketing playbook docs** — growth loops, growth hacker OS, CRO, pricing, competitive intel, content repurposing, lifecycle marketing, launches, retargeting, ABM, partnerships, and more
- **27 frameworks** — SEO rules, AEO/GEO strategy, AI-search optimization, perception engineering, copywriting formulas, quality-rater guidance, query fan-out, and LLM citation tracking
- **36 checklists** — technical SEO, ad launches, growth hacker OS, content quality, email, PR, website launches, social audits, creative production, privacy scanning, mutation-risk review, and paid acquisition
- **26 channel guides** — SEO content, LinkedIn, Meta ads, TikTok, YouTube, X/Twitter, Instagram, newsletters, podcasts, community, affiliate/referral, and press
- **18 harness references** — ad platform policies, API notes, compliance references, provenance rules, creator disclosure, and analytics query templates
- **30 skill contracts** — output specs for content, ads, outreach, growth-hacker packages, meetings, experiments, clips, podcasts, lead dossiers, and other marketing assets
- **8 audience personas** — pains, hooks, objections, emotional drivers, and voice guidance
- **Quality gates** — Four U's, banned-word checks, proof density, specificity, platform compliance, SEO linting, and AI-slop detection

## Core use cases

### For SaaS founders

Use Kai to go from "we need marketing" to a concrete plan: landing page, launch content, lifecycle emails, cold outreach, SEO roadmap, paid campaign angles, and AI-search visibility.

### For agencies

Install Kai inside a client repo and create repeatable strategy, content, campaign, and audit workflows without rebuilding your operating system for every account.

### For indie hackers

Use `/kai-growth-plan`, `/kai-growth-hacker`, `/kai-landing-page`, `/kai-cold-outreach`, and `/kai-content-calendar` to create a practical marketing system without hiring a team.

### For local-service businesses

Use Kai's business profiling, audits, and proposal ranking to turn a service business website into a prioritized marketing action plan.

### For AI-search visibility

Use `/kai-surround-sound` and the AEO/GEO knowledge base to target the questions people ask ChatGPT, Perplexity, Gemini, Claude, and Google AI Overviews when comparing products in your category.

## Repository map

```text
harness/skills/              Claude Code slash-command skills
knowledge/                   Marketing playbooks, frameworks, checklists, personas, policies
kai/runtime/                 Runtime models, state, profiles, goals registry, approvals, and lifecycle
agent/                       Subagent task scheduler and Task Graph Decomposer (goals-to-DAG planner)
kai/execution/               Task Orchestrator mapping nodes to task handlers
kai/analytics/               Attribution engine and closed-loop ActionRewards feedback loop
scripts/quality/             Content quality gate and scoring rules
scripts/content/             Briefing, writing, reporting, and content workflow scripts
scripts/analytics/           Search Console, GA4, Stripe, Meta, and competitive monitoring utilities
harness/references/          Ad policy and compliance references
harness/skill-contracts/     Output contracts for common marketing assets
workspace/                   Example CMO-agent operating workspace
tools/docker/                Modal and RunPod media-generation worker templates
```

## Where to start

- **New launch:** `/kai-growth-plan` -> `/kai-email-system` -> `/kai-landing-page`
- **Running ads:** `/kai-ad-campaign` → `/kai-cro` → `/kai-retarget`
- **Need AI-search mentions:** `/kai-surround-sound` → `/kai-competitors` → `/kai-seo-audit`
- **Want the full machine:** `/kai-launch`

## Requirements

- [Claude Code](https://claude.ai/download)
- A terminal
- Optional: analytics/ad-platform credentials if you want Kai to pull real performance data

No SaaS account is required. The core harness is local files and Claude Code skills.

## Related search terms

AI marketing agent, AI CMO, Claude Code skills, Claude Code slash commands, Claude Code marketing skills, marketing automation agent, SaaS marketing agent, startup growth marketing AI, local service marketing OS, SEO content agent, answer engine optimization agent, generative engine optimization, GEO agent, AEO agent, LLM citation strategy, ChatGPT search optimization, Perplexity SEO, Claude search optimization, AI Overviews optimization, landing page copy agent, lifecycle email agent, paid ads agent, content calendar generator, marketing audit agent, product launch agent, AI growth marketing assistant.

## License

MIT — see [`LICENSE`](LICENSE).
