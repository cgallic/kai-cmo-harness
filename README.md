# Kai Marketing OS: Claude Code Skills For Growth Work

**Kai turns a product repo into a marketing workspace.** It gives Claude Code a marketing team, a source-aware brief, channel playbooks, policy references, quality gates, approval rules, and memory so the next run starts smarter.

Use it when you want an AI operator to create growth plans, landing pages, emails, ads, SEO/AEO work, audits, content calendars, SDR handoff, or repurposed assets from the same files your product team already uses.

**The only requirement is Claude Code (or Cursor/Codex) already running.** No SaaS account, no API keys, no config files. If your terminal can run `/kai-start`, you have the whole system.

> Built by [Connor Gallic](https://pr.linkedin.com/in/cgallic) — follow on LinkedIn for more agentic marketing systems.

## Try Kai In 60 Seconds — No API Key

Inside Claude Code:

```text
/plugin marketplace add cgallic/kai-cmo-harness
/plugin install kai@kai-marketing-os
/kai:kai-gate <paste or point at any draft — a landing page, an email, your README>
```

Kai scores the draft against the Four U's rubric, the banned-word tiers, and platform rules, then returns a scorecard with a pass/fail verdict and specific fixes. Your OAuth session does the judging — nothing leaves your machine, nothing to sign up for.

## What The Output Looks Like

Every piece Kai writes must pass the gate before it ships. This is the actual scorecard format, from `demo/examples/saas-blog-post/`:

> ## Four U's Score: 13/16
>
> | Dimension | Score | Reasoning |
> |-----------|-------|-----------|
> | **Unique** | 4/4 | Stage-matched framework (pre-revenue / post-PMF / scaling) not found in any top-10 result. Survey data and switching cost table are original angles. |
> | **Useful** | 3/4 | 30-minute CRM evaluation checklist is immediately actionable. Deducted 1 point: no downloadable comparison template. |
> | **Ultra-Specific** | 3/4 | 23 hours migration time, 73% abandon rate, $14,000 switching cost. Deducted 1 point: some claims cite vendor-published data. |
> | **Urgent** | 3/4 | Switching-tax framing creates cost-of-inaction pressure. Deducted 1 point: no seasonal urgency hook. |
>
> **Total: 13/16** — Passes threshold (minimum 12).
> **Banned Words Check: PASS** · **SEO Compliance: PASS (1 warning)**

Three complete worked examples — brief, draft, and scorecard — live in [`demo/examples/`](demo/examples/): a SaaS blog post, a law-firm landing page, and an e-commerce product page.

## What You Get

- **49 public `/kai` commands** for strategy, distribution, content, ads, SEO, CRO, lifecycle, SDR, launches, and analytics.
- **54 `kai-*` skills** with triggers, inputs, outputs, gates, provenance, and failure modes.
- **A real knowledge base**: 67 playbooks, 37 checklists, 38 frameworks, 31 channel guides, 8 personas, platform policy references, and 33 skill contracts.
- **Guardrails built in**: Four U's scoring, banned-word checks, SEO lint, policy references, provenance lint, privacy scanning, and mutation-risk lint.
- **Local-first by default**: use it inside Claude Code from your repo before wiring live channels.
- **Approval-led automation**: dry-run first, review the artifact, then approve external actions.
- **Goals, not just tasks**: `/kai-goal` takes a business outcome, decomposes it into work items, and keeps going across sessions until a gate says the floor was met.

## `done` Is Not A Verdict

Most agent harnesses call work finished when a file exists. Kai splits that into three claims and lets a gate — not the agent that did the work — decide:

- **E — Execution.** Did the effect happen at the real target? A draft on disk is E1. A live URL that returns 200 with the approved body is E5.
- **C — Craft.** Does it clear the gates, the platform policy, and the provenance rule, plus a read by someone who didn't write it?
- **O — Outcome.** Did the number move, measured against a threshold declared *before* ship?

Two verdicts: **SHIPPED** (E and C met, outcome still owed) and **CLOSED** (all three). The rule that makes it work: *the actor may submit evidence, the actor may not issue its own verdict.* Evidence whose verifier is the producer gets discarded, and a baseline written after ship is rejected outright.

```bash
python -m scripts.quality_gates.eco_gate floors   # the floor for each kind of work
python -m scripts.quality_gates.eco_gate debt     # what shipped but never got measured
```

Full standard: [`docs/system/eco-completion-standard.md`](docs/system/eco-completion-standard.md) · Marketing floors: [`harness/references/eco-marketing-floors.md`](harness/references/eco-marketing-floors.md)

## Quick Start: From Install To Growth Plan

The plugin install above ships every skill **plus the knowledge base they run on** (frameworks, checklists, channel guides, policy references, quality gates — ~7 MB) and keeps them updated. Then open any product repo and run:

```text
/kai-start
/kai-growth-plan
```

`/kai-start` reads your repo, plays back what your product is, and writes `MARKETING.md` — once, in about 2 minutes. `/kai-growth-plan` turns that context into a stage-specific plan, recommended workflows, metrics, budget notes, and anti-patterns.

Prefer a shell one-liner? Same result:

```bash
curl -fsSL https://raw.githubusercontent.com/cgallic/kai-cmo-harness/main/install.sh | bash
```

Want the short setup guide? Read [Quick Start](docs/QUICK_START.md). Want to watch the whole pipeline run as a script (research → brief → write → gate → scorecard)? `python demo/demo.py --url "https://yoursite.com" --keyword "best crm for startups"` does it in ~60 seconds with one free Gemini key.

## Useful First Runs

| Goal | Command | What Kai returns |
|---|---|---|
| Find the next growth move | `/kai-growth-plan` | Stage, channel bets, constraints, and what to ignore |
| Build the first growth hire OS | `/kai-growth-hacker` | B2B/B2C channel map, fan-out plan, test cards, gates, and metrics |
| Rewrite a page | `/kai-landing-page` | Page copy, proof table, CRO hypotheses, and approval notes |
| Plan search content | `/kai-content-calendar` | Topic map, keywords, personas, and source-backed priorities |
| Audit the funnel | `/kai-cro` | Findings, evidence, data gaps, and test ideas |
| Repurpose a source asset | `/kai-repurpose` | Quotes, social posts, email angles, clips, and a kill list |

## What Makes Kai Different

Most AI marketing tools are either a blank chat box, a narrow content generator, or a dashboard that cannot understand your product repo. Kai does the opposite. It runs where your product already lives — the terminal — and starts from the repo: product docs, code, routes, pricing, examples, claims, and marketing memory.

That means the system can:

- create a brief before it writes
- choose the right channel playbook
- trace claims to evidence
- block risky copy before it ships
- route live actions through approval
- remember what worked after results come back

Kai makes marketing behave more like engineering work: source-aware, inspectable, gated, and repeatable. It is built for founders, indie hackers, SaaS teams, agencies, and product engineers who want Claude Code to help with actual growth work instead of generic copy.

## What This Is Not

Kai is not a prompt pack, a standalone chatbot, or a content spinner. It is a local operating surface for marketing work that needs source context, policy checks, quality gates, and repeatable workflows.

Autonomous campaign management is a guarded phase, not the starting promise. Kai ships the trusted operating layer first: product context, policy constraints, evidence, approvals, memory, and connector health.

## Why Not A Blank Chat?

Fair question — Claude is free-form and prompt packs are everywhere. Here is the honest comparison:

| | Blank Claude chat | Prompt pack | Marketing script toolbox | **Kai** |
|---|---|---|---|---|
| Reads your product repo first | You paste context manually | No | No | Yes — `/kai-start` builds the profile once |
| Channel playbooks + platform policy | From model memory, unverified | Static templates | Per-script docs | 67 playbooks, 26 channel guides, per-platform ad policy references, loaded per task |
| Quality gate before shipping | No | No | Sometimes a lint script | Four U's 12/16 threshold, banned-word tiers, SEO lint, provenance lint — every piece |
| Claims traced to sources | No | No | No | Provenance rules: no invented metrics, data gaps declared, collector-sourced numbers |
| Approval before live actions | N/A | N/A | Env-var scripts fire directly | Dry-run first, human approval gates every mutation |
| Remembers what worked | Per-conversation only | No | No | Git-backed memory: lessons, edge cases, measured losers, 30-day checks |

The chat box is faster for a one-off caption. Kai is for marketing you have to stand behind: repeatable, source-aware, and checked before it ships.

## How It Works

The first time you run a `/kai` command in a project, Kai:

1. **Reads your codebase** — `CLAUDE.md`, `README.md`, package files, routes, schemas, product docs, and existing marketing notes.
2. **Builds a runtime profile** — workspace, brand, archetype/module defaults, proof points, channels, and operating constraints.
3. **Creates `MARKETING.md` as a readable export** — ICP, personas, brand voice, positioning, value props, landscape, and operating defaults.
4. **Runs the workflow** — writes, audits, plans, scores, researches, routes approvals, and packages the requested marketing asset.

Every later command runs from the same workspace/brand/module model. Content follows one path:

```
Research -> Brief -> Write -> Quality Gate -> Approval -> Publish -> Log -> 30-day Check
```

## Install Options

**Pick your version first.** Kai ships the same 50 skills two ways, and neither is deprecated:

| | `kai` (v1) | `kai-v2` |
|---|---|---|
| Shape | Numbered phases and explicit steps | Objective, completion floor, constraints — route is yours |
| Install on | Smaller or older models; work that must produce an identical shape every run | Claude Opus 5 / Sonnet 5 class models |

Same knowledge base, same gates, same governance, same output paths. Both can be installed together — Claude Code namespaces them as `/kai:*` and `/kai-v2:*`. Details: [`docs/system/skill-versions.md`](docs/system/skill-versions.md).

**Cowork (no terminal needed):** Kai installs as a plugin from this repo, no clone and no shell.

1. Open **Customize → Plugins** in the sidebar.
2. Select **Add marketplace** and enter `cgallic/kai-cmo-harness`.
3. Install **Kai Marketing OS** (or **Kai Marketing OS v2**), then open it to see its skills and agents.

You get 50 skills, 3 marketing subagents (evidence collector, craft reviewer, research scout), the full knowledge base, and the quality gates — about 10 MB and 580 files, well inside Cowork's plugin limits. Everything runs from the plugin package: no repo checkout, no `PYTHONPATH`, no API keys. Start with `/kai-start`, or `/kai-goal` if you want Kai chasing an outcome rather than producing one asset.

**Plugin (Claude Code CLI or desktop):** two lines inside Claude Code. Auto-updating, includes the knowledge base, nothing touches your shell.

```text
/plugin marketplace add cgallic/kai-cmo-harness
/plugin install kai@kai-marketing-os
```

Plugin skills are namespaced: type `/kai:kai-start`, `/kai:kai-growth-plan`, and so on.

**Shell one-liner:** installs skills to `~/.claude/skills/` and the knowledge base to `~/.claude/kai/`. Use this if you prefer un-namespaced commands (`/kai-start`) or want to read the script first.

```bash
curl -fsSL https://raw.githubusercontent.com/cgallic/kai-cmo-harness/main/install.sh | bash
```

**Repo copy (Cursor, Codex, claude.ai/code web, client repos):** these surfaces don't persist `~/.claude/skills`, so put Kai in the repo itself. Clone this repo and copy `AGENTS.md`, `knowledge/`, `harness/`, `memory/`, and `scripts/quality_gates/` into your project root — the agent picks it up from `AGENTS.md` on the next session. Details in [Quick Start](docs/QUICK_START.md).

Verify any install from a clone:

```bash
python scripts/doctor.py   # confirms referenced files exist, gates run, golden corpus passes
```

## The 49 Public `/kai` Commands

The tables below list the 49 public router commands plus `/kai-start`, the onboarding skill that bootstraps every project. These commands work through Claude Code's skill system. They load knowledge files and framework instructions for the LLM. Type `/kai` for the router and help menu. The [public skill manifest](docs/skill-manifest/README.md) documents 46 canonical `kai-*` skill pages with the same schema: triggers, inputs, outputs, gates, provenance, and failure modes.

### Produce marketing assets

| Command | What you get |
|---|---|
| `/kai-write` | One piece of content: blog, email, LinkedIn post, ad, press release, script, or landing copy |
| `/kai-landing-page` | Complete conversion-focused landing page copy |
| `/kai-email-system` | Full lifecycle and transactional email system |
| `/kai-ad-campaign` | Paid campaign across major ad platforms |
| `/kai-content-calendar` | Month or quarter of planned content mapped to keywords and personas |
| `/kai-content-batching` | Pillars turned into a gated 30-day multi-platform content batch |
| `/kai-social` | Batch social posts across LinkedIn, X, TikTok, Instagram, and YouTube |
| `/kai-video` | Video scripts and clipping plans for short-form and long-form video |
| `/kai-hook-bench` | Ranked, provenance-tagged hook bank per persona and channel |
| `/kai-proof-builder` | Provenance-clean proof library — testimonials, stats, case proof |
| `/kai-cold-outreach` | Cold email sequences and outbound messaging |
| `/kai-sdr-operator` | SDR operator package for lead sources, scoring, outreach handoff, and reply triage |
| `/kai-sdr-reply-triage` | Reply classification, suppression handling, CRM handoff, and next actions |
| `/kai-sales-meeting-prep` | Meeting briefs, discovery plans, follow-up drafts, and sales handoff notes |
| `/kai-reddit-listen` | Configure and run a Reddit intelligence bank with scoring, dashboard review, alerts, digests, and content briefs |
| `/kai-newsletter` | Newsletter editions, subject lines, and structure |
| `/kai-case-study` | Customer case study from interview notes or product data |
| `/kai-client-dashboard` | White-labeled, client-facing intelligence dashboard with brand shell, page set, and retention plays |
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
| `/kai-funnel-audit` | Full-funnel awareness and lead-capture audit on collected data |
| `/kai-retro` | Learning retrospective — mine gate failures, diagnose losers, promote lessons into enforced checks |
| `/kai-html-presentation` | Client-ready HTML deck for audit and report delivery |
| `/kai-data-dashboard` | Dashboard specs or static dashboards from sourced Kai data |

### Plan strategy

| Command | What you get |
|---|---|
| `/kai-start` | Reads your repo, plays back your product, and writes `MARKETING.md` |
| `/kai-brief` | Content brief before writing |
| `/kai-growth-plan` | Marketing plan by stage: pre-launch, launch, growth, or scale |
| `/kai-gtm-pack` | Package the plan for a client: cross-linked private page set topped by a client hub (the ask, access grants, signup checklist) |
| `/kai-growth-hacker` | First-growth-hire distribution OS across B2B and B2C channels |
| `/kai-offer-builder` | Grand Slam Offer construction scored on the Value Equation |
| `/kai-brand` | Brand positioning and messaging framework |
| `/kai-budget` | Marketing budget and channel allocation |
| `/kai-retention` | Customer retention system and lifecycle plan |

### Research and analyze

| Command | What you get |
|---|---|
| `/kai-competitors` | Competitive teardown and sales battlecards |
| `/kai-brand-pulse` | Cited public brand intelligence across web, news, social, Reddit, and review sites |
| `/kai-surround-sound` | AEO/GEO strategy for agent-readiness, source-quality, and measured AI-search visibility |
| `/kai-analytics` | Analytics and attribution setup |
| `/kai` | Command router and help menu |

## What Is Included

Kai ships with a real marketing knowledge base, more than prompts:

- **67 marketing playbook docs** — growth loops, growth hacker OS, CRO, pricing, competitive intel, content repurposing, lifecycle marketing, launches, retargeting, ABM, partnerships, and more
- **33 frameworks** — SEO rules, AEO/GEO strategy, AI-search optimization, perception engineering, copywriting formulas, quality-rater guidance, query fan-out, and LLM citation tracking
- **36 checklists** — technical SEO, ad launches, growth hacker OS, content quality, email, PR, website launches, social audits, creative production, privacy scanning, mutation-risk review, and paid acquisition
- **26 channel guides** — SEO content, LinkedIn, Meta ads, TikTok, YouTube, X/Twitter, Instagram, newsletters, podcasts, community, affiliate/referral, and press
- **Platform policy references** — ad platform policies, organic posting rules, API notes, compliance references, provenance rules, and creator disclosure for every major channel
- **33 skill contracts** — output specs for content, ads, outreach, growth-hacker packages, meetings, experiments, clips, podcasts, lead dossiers, and other marketing assets
- **8 audience personas** — pains, hooks, objections, emotional drivers, and voice guidance
- **Quality gates** — Four U's, banned-word checks, proof density, specificity, platform compliance, SEO linting, and AI-slop detection

## Repository Structure

```text
kai-cmo-harness/
├── AGENTS.md / CLAUDE.md          # Agent entry points (AGENTS.md is the source of truth)
├── install.sh                     # Shell installer: skills + knowledge base
├── .claude-plugin/                # Claude Code plugin marketplace manifest
├── plugins/kai-marketing-os/      # Plugin package
│
├── harness/                       # Operator surface
│   ├── skills/                    # /kai router + 53 kai-* skills + kaicalls-design
│   ├── skill-contracts/           # 33 per-format output contracts (YAML)
│   ├── references/                # Ad policies, organic rules, compliance references
│   ├── voice-gate/                # LLM-as-judge voice-consistency gate
│   └── brief-schema.md            # Content brief template
│
├── knowledge/                     # Marketing knowledge base
│   ├── frameworks/                # AEO/AI search, copywriting, Google Ads, Meta, science
│   ├── playbooks/                 # 67 strategic playbooks
│   ├── checklists/                # 36 validation checklists
│   ├── channels/                  # 26 channel guides
│   ├── personas/                  # 8 audience personas
│   └── people/                    # Cloned-expert knowledge bases
│
├── scripts/                       # Python pipeline
│   ├── doctor.py                  # Preflight self-check — run on every fresh clone
│   ├── harness_cli.py             # Pipeline CLI: brief → write → gate → approve → publish
│   ├── quality_gates/             # four_us_score, banned_word_check, seo_lint, provenance
│   ├── content/                   # Outcome engine (engine.py), briefs, writers
│   ├── publish/ social/ intel/    # CMS publishing, social posting, competitive intel
│   ├── campaigns/ reporting/ ads/ # Campaign planner/tracker, reports, Google Ads API
│   └── knowledge_cloner/          # Expert knowledge extraction pipeline
│
├── kai/                           # Runtime layer: models, state, goals, approvals
├── memory/                        # Git-backed learning: lessons, edge cases, losers
├── agent/                         # Autonomous loop (optional)
├── gateway/                       # FastAPI remote runner (optional)
├── workspace/                     # CMO-agent operating workspace + dashboard
├── demo/                          # One-command demo + pre-generated examples
├── evals/golden/                  # Golden corpus (gate regression cases)
├── deploy/                        # VPS deployment templates
├── docs/                          # QUICK_START, CONFIGURATION, ARCHITECTURE, system/
└── legacy/                        # Retired surfaces kept for reference
```

## Core Use Cases

- **SaaS founders:** go from "we need marketing" to a concrete plan — landing page, launch content, lifecycle emails, cold outreach, SEO roadmap, paid campaign angles, and AI-search visibility.
- **Agencies:** install Kai inside a client repo and create repeatable strategy, content, campaign, and audit workflows without rebuilding your operating system for every account.
- **Indie hackers:** use `/kai-growth-plan`, `/kai-growth-hacker`, `/kai-landing-page`, `/kai-cold-outreach`, and `/kai-content-calendar` to create a practical marketing system without hiring a team.
- **Local-service businesses:** use Kai's business profiling, audits, and proposal ranking to turn a service business website into a prioritized marketing action plan.
- **AI-search visibility:** use `/kai-surround-sound` and the AEO/GEO knowledge base to target the questions people ask ChatGPT, Perplexity, Gemini, Claude, and Google AI Overviews when comparing products in your category.

## Where To Start

- **New launch:** `/kai-growth-plan` → `/kai-email-system` → `/kai-landing-page`
- **Running ads:** `/kai-ad-campaign` → `/kai-cro` → `/kai-retarget`
- **Need AI-search mentions:** `/kai-surround-sound` → `/kai-competitors` → `/kai-seo-audit`
- **Want the full machine:** `/kai-launch`

## Beyond Content: The Python Pipeline

Everything below is optional — the skills work without it. The Python layer adds publishing, monitoring, and reporting for teams that want the full loop. All commands run from a clone of this repo.

### Publishing

Publishing is truthful and double-opt-in. The content engine never invents URLs: a gate-approved piece either publishes for real — when `publishing.enabled` plus a `publishing.sites.<site>.platform` entry are set in `config.yaml` (env override `KAI_PUBLISH_ENABLED`) — and logs the URL the CMS returned, or it's logged as `approved_unpublished` until you publish manually and backfill with `content_log.mark_published(entry_id, url)`. That backfill also arms the 30-day performance check. WordPress publishes are idempotent and default to `status=draft`.

```bash
# Full pipeline with CMS publishing (WordPress, Ghost, Webflow, or static markdown)
python scripts/harness_cli.py run --task blog --site mysite --keyword "ai crm" --publish wordpress

# Social posting
python scripts/social/linkedin.py --content "Your LinkedIn post"
python scripts/social/twitter.py --content "Your tweet"
python scripts/social/buffer.py --content "Scheduled post" --platforms linkedin twitter
```

### Competitive Intelligence

```bash
python scripts/intel/competitor_monitor.py --check    # RSS + sitemap scan
python scripts/intel/competitor_monitor.py --diff     # New pages since last check
python scripts/intel/content_gap.py --site mysite     # Keywords they rank for, you don't
python scripts/intel/market_brief.py                  # AI-synthesized weekly market brief
```

### Campaign Management

```bash
python scripts/campaigns/campaign_planner.py --goal "product launch" --product myproduct --keyword "ai crm" --type launch --save campaigns/q1/
```

Generates: landing page, 5-email sequence, social variants (LinkedIn/Twitter/Instagram), ad variants (Meta + Google), content calendar. `--save` mints a `campaign_id` that threads through the tracker, runtime artifacts, the content log, and 30-day performance checks.

### Goals & the Weekly CMO Review

```bash
python scripts/harness_cli.py goals add --brand mysite --name "Q3 signups" --kpi signups --target 500 --deadline 2026-09-30
python scripts/harness_cli.py goals list   # shows pace vs deadline
```

Every Monday the agent loop's `cmo_review` task measures each goal's pace from graded 30-day results, decomposes behind-pace goals into task graphs, and executes them through the normal approval gates. It also runs the 30-day performance check (nightly), weekly pattern extraction, and an hourly editorial-calendar tick — dated content plans become pipeline runs automatically.

### Reporting

```bash
python scripts/reporting/weekly_report.py --save reports/week.md   # Full weekly report
python scripts/build_dashboard.py                                  # Rebuild the HTML dashboard
python scripts/reporting/ceo_deck.py                               # 5-slide CEO deck
```

### Google Ads

```bash
python scripts/ads/google_ads.py campaigns          # Campaign performance
python scripts/ads/google_ads.py keywords           # Keyword data
python scripts/ads/google_ads.py search-terms       # Find negatives + opportunities
python scripts/ads/google_ads_optimize.py --analyze # AI-powered optimization
```

Read-only pulls are safe to run; anything that mutates a live ad account goes through the approval gate first.

### Knowledge Cloner

Extract expert knowledge from YouTube, podcasts, articles, and GitHub repos into structured frameworks:

```bash
python -m scripts.knowledge_cloner init "Alex Hormozi" --domain "Business"
python -m scripts.knowledge_cloner discover alex-hormozi --youtube https://www.youtube.com/@AlexHormozi/videos --limit 20
python -m scripts.knowledge_cloner pipeline alex-hormozi --max-cost 10.00
```

6-phase pipeline: Discover → Transcribe → Extract → Distill → Synthesize → Operationalize. Outputs 5 distilled docs + 4 operational tools + quality report. ~$3.50 for 40 sources via OpenRouter. See `scripts/knowledge_cloner/README.md`.

### Dashboard

Kai includes a single-file HTML dashboard for active goals, tasks, and integrations.

```bash
python -m http.server 8000
# then open http://localhost:8000/workspace/dashboard.html
```

Deploy it by clicking **One-Click Deploy** in the dashboard (Netlify token required), running `./deploy.sh` (macOS/Linux) or `deploy.bat` (Windows), or pushing the repo to Vercel/Netlify — `vercel.json` and `netlify.toml` are included.

This is the operator's own dashboard, not a client deliverable. To stand up a white-labeled, client-facing dashboard for one of your own clients, use `/kai-client-dashboard`.

## Current Status (v1.0.0, updated July 2026)

| Layer | Status | Notes |
|-------|--------|-------|
| Claude Code skill surface | Working | 49 public `/kai` router commands and 54 `kai-*` skills load repo context, frameworks, contracts, and policy references |
| Runtime models + persistence | Built | Atomic writes, thread-safe records, audit log |
| Business profiling + audit engines | Built | Archetype detection, overlay inference, 8 audit categories, severity-weighted scoring, and multi-location support |
| Proposal ranking + bundling | Built | 5-factor weighted, dependency-aware |
| Approval + action lifecycle | Built | State machine enforced, tested |
| Compliance engine | Built | 100+ rules and 50+ regex patterns |
| Content pipeline + quality gates | Built | LLM-backed via `scripts/content/engine.py` |
| Knowledge base | Built | Current inventory is documented in `docs/system/governance-and-quality.md` |
| Connector execution | Wired, credential-gated | Pipedream-backed execution and direct script clients exist; live external actions require connected accounts and credentials |
| Learning + memory | Built | Approval writeback persists learnings; the writing prompt auto-retrieves winners (`what-works.md`), measured losers (`memory/what-doesnt-work.md`), and runtime memory; proposals attach prior brand learnings via `action_from_finding`; framework attribution grades knowledge docs from 30-day results |
| Creative module | Built (by design) | Emits structured briefs, recipes, and variant/QA specs; final prose renders through the LLM-backed `scripts/content/` writers and Claude Code skills — a deliberate separation, not a gap |
| Watchers/monitoring | Built, credential-gated feeds | Website-health watchers fetch live (HTTP status, TLS expiry, forms, phone, tracking); watcher packs run on the agent loop's daily `watchers_tick` and dispatch immediate findings via Discord/WhatsApp; ad/lead watchers read connector data and need credentials |
| Autonomous campaign loops | Guarded, working | Scheduled ad/lead/content tasks and reward scoring run via the operator-started agent loop; publishing happens only through the approval queue and credentialed connectors — never unattended |
| Remote automation scheduling | Planned | Declared in module manifests but not yet dispatched; today's scheduled surface is the agent cron loop plus a monthly GitHub Actions policy monitor |

For the full assessment, see `docs/superpowers/specs/2026-04-03-system-current-state-report.md`.

## Requirements

- [Claude Code](https://claude.ai/download) running. That's the whole list.
- Cursor, Codex, and claude.ai/code work too, via the repo-copy install.
- Optional, only for live data: analytics/ad-platform credentials if you want Kai to pull real performance numbers or publish through connectors.

No SaaS account, no signup, no API key for the core workflow. The harness is local files plus the agent you already run.

## Related Links

- [MeetKai](https://meetkai.xyz): the operator layer behind Kai Marketing OS workflows.
- [KaiCalls](https://kaicalls.com): a Kai-owned AI voice agent product for small-business phone answering and lead capture when the business is phone-led.
- [How Kai markets KaiCalls](docs/HOW_KAI_MARKETS_KAICALLS.md): the dogfooding case study — every KaiCalls marketing decision runs through this repo.
- [Connor Gallic](https://connorgallic.com): founder building Kai, KaiCalls, and AI automation systems.
- [How Kai runs paid ads](docs/AI_POWERED_ADS_SYSTEM.md): plain-English explanation of the paid media workflow.
- [System guide](docs/system/README.md): architecture pages, Mermaid diagrams, and runtime schemas.
- [Public skill manifest](docs/skill-manifest/README.md): versioned API-style docs for every canonical `kai-*` skill.

## Related Search Terms

AI marketing agent, AI CMO, Claude Code skills, Claude Code slash commands, Claude Code marketing skills, marketing automation agent, SaaS marketing agent, startup growth marketing AI, local service marketing OS, SEO content agent, answer engine optimization agent, generative engine optimization, GEO agent, AEO agent, LLM citation strategy, ChatGPT search optimization, Perplexity SEO, Claude search optimization, AI Overviews optimization, landing page copy agent, lifecycle email agent, paid ads agent, content calendar generator, marketing audit agent, product launch agent, AI growth marketing assistant.

## License

**The plugin is MIT. The hosted service is not.**

Everything `/plugin install` puts on your machine — all the skills, the whole
knowledge base, the subagents, and the quality gates — is MIT. Use it
commercially, fork it, ship it inside your own paid product. No strings.

The rest of the repository (`app-meetkai/`, `daemon/`, `agent/`, `gateway/`,
`kai/`, and the remaining `scripts/`) is under the Elastic License 2.0: read it,
self-host it, run it for your own company, but don't resell it as a hosted
service.

Commits published before 2026-08-08 were MIT in their entirety, and stay MIT —
relicensing isn't retroactive.

See [`LICENSING.md`](LICENSING.md) for the path-by-path map.
