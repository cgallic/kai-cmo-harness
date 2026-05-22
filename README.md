# Kai Marketing OS — Marketing, From The Repo

**Kai Marketing OS is a repo-native marketing runtime for Claude Code.** It turns a product repository into a marketing workspace with briefs, playbooks, skill contracts, platform policy references, quality gates, and reusable marketing memory.

If you searched for **AI marketing agent**, **Claude Code marketing skills**, **AI CMO**, **repo-native marketing OS**, **marketing automation for startups**, **SEO content agent**, **GEO / AEO agent**, **LLM citation strategy**, or **AI growth marketing assistant**, this is the repo you wanted.

## Related links

- [MeetKai](https://meetkai.xyz) — the operator layer behind Kai Marketing OS workflows.
- [KaiCalls](https://kaicalls.com) — a Kai-owned AI voice agent product for small-business phone answering and lead capture when the business is phone-led.
- [Connor Gallic](https://connorgallic.com) — founder building Kai, KaiCalls, and AI automation systems.
- [How Kai runs paid ads](docs/AI_POWERED_ADS_SYSTEM.md) — plain-English explanation of the paid media workflow.
- [System guide](docs/system/README.md) — architecture pages, Mermaid diagrams, and runtime schemas.
- [Public skill manifest](docs/skill-manifest/README.md) — versioned API-style docs for every canonical `kai-*` skill.

## Start here

Kai is for people who need marketing work done from the repo, not from a blank chat window.

| You are | What Kai helps with | Start with |
|---|---|---|
| **Business owner** | Turn "we need more customers" into a clear plan, campaigns, pages, emails, and follow-up work | `/kai-growth-plan` |
| **Marketing operator** | Produce briefs, ads, content, landing pages, email systems, audits, and quality reports from one workspace | `/kai` |
| **Developer** | Give an AI agent structured product context, policy checks, files, workflows, and repeatable commands | `README.md` + `harness/skills/` |
| **Agency or consultant** | Install a reusable marketing operating system inside client repos | `docs/QUICK_START.md` |

The simplest way to understand Kai: it reads the business, chooses the right marketing workflow, creates the work, checks it, and leaves a record so the next run is smarter.

## 3-minute demo loop

Run this in a product repo when you want to see the core workflow:

```text
/kai-start
/kai-growth-plan
```

The first command creates or refreshes `MARKETING.md` from the repo. The second command turns that context into a stage-specific growth plan, skill routing, metrics, budget notes, and anti-patterns. See [workspace/growth-plan](workspace/growth-plan) for a sample output generated from this repo.

## What Kai is

Kai is a **repo-native marketing operating system that runs inside Claude Code**.

It uses Claude Code's operator experience — skills, subagents, hooks, memory, and terminal-native workflows — and adds marketing-specific infrastructure:

- **Business profiling** with archetype detection and overlay inference
- **Audit engines** that score businesses across 8 categories with real algorithms
- **Proposal ranking** with 5-factor weighted scoring, dependency resolution, and capacity pruning
- **Approval workflows** with risk-based auto-approval and state machine enforcement
- **Compliance checking** with 100+ rules and regex pattern matching
- **Quality gates**: Four U's scoring, banned-word detection, SEO linting, proof density, and AI-slop checks
- **Current inventory**: 42 skill directories, 40 canonical `kai-*` skill docs, 36 public `/kai` router commands, 48 playbook docs, 32 checklists, 27 framework docs, 17 channel guides, 8 audience persona profiles, 18 harness references, and 15 skill contracts
- **Claude Code marketing skills** for content, ads, lifecycle, SEO, GEO/AEO, audits, launches, and growth planning

- **Claude Code marketing skills** for content, ads, lifecycle, SEO, GEO/AEO, audits, launches, and growth planning

It is built for founders, indie hackers, SaaS teams, agencies, and product engineers who want Claude Code to help with actual growth work instead of generic copy generation.

## What this is not

Kai is not a prompt pack, a standalone chatbot, or a content spinner. It is a local operating surface for marketing work that needs source context, policy checks, quality gates, and repeatable workflows.

## Current status (v1.0.0, April 2026)

| Layer | Status | Notes |
|-------|--------|-------|
| Runtime models + persistence | Built | Atomic writes, thread-safe, audit log |
| Goal Registry & Decomposer | Built | File-backed goals registry (`goals.py`) + cycle-free Task Graph Decomposer (`decomposer.py`) |
| Closed-loop Rewards | Built | Outcome attribution metrics & performance feedback scoring loop (`rewards.py`) |
| AutoReason & Ad loop | Built | Automated ad variant iteration & AutoReason tournament integration (`ad_loop.py`) |
| Audit engines (8 categories) | Built | Real scoring algorithms, 239 tests passing |
| Proposal ranking + bundling | Built | 5-factor weighted, dependency-aware |
| Approval + action lifecycle | Built | State machine enforced, tested |
| Compliance engine | Built | 100+ rules, 50+ regex patterns |
| Content pipeline + quality gates | Built | LLM-backed via `scripts/content/engine.py` |
| Knowledge base | Built | Current inventory is documented in `docs/system/governance-and-quality.md` |
| Connector business logic | Partial | Request construction complete, HTTP transport not wired |
| Creative module | Partial | Generates briefs/templates, not final content |
| Watchers/monitoring | Partial | Threshold logic real, data feeds not connected |
| Agent loop / subagent orchestration | Partial | TaskOrchestrator and scheduled tasks mapped; autonomous execution loops planned |
| Remote automation scheduling | Planned | Defined in module manifests, not triggered |

For the full assessment, see `docs/superpowers/specs/2026-04-03-system-current-state-report.md`.

## Install

**Option 1 — One-liner**:

```bash
curl -fsSL https://raw.githubusercontent.com/cgallic/kai-cmo-harness/main/install.sh | bash
```

**Option 2 — Manual**:

```bash
git clone https://github.com/cgallic/kai-cmo-harness.git /tmp/kai-install \
  && cp -r /tmp/kai-install/harness/skills/kai* ~/.claude/skills/ \
  && rm -rf /tmp/kai-install \
  && echo "Installed. Type /kai-start in Claude Code."
```

**First run:** open Claude Code in any product repo and type `/kai-start` for guided setup. It reads your codebase, creates `MARKETING.md`, and recommends your first command.

Or type `/kai` to see the 36 public router commands. The broader [public skill manifest](docs/skill-manifest/README.md) documents all 40 canonical `harness/skills/kai-*` skill directories, including newer and specialist skills that are not all listed in the router table.

## One-Click Live Dashboard Deployment

Kai compiles a complete, interactive, premium dashboard to help you and your subagents visualize active goals, tasks, and integrations. You can deploy it live to the web in one click:

### Path A: Direct Browser Deploy (Zero-Config)
1. Open your compiled dashboard locally at `workspace/dashboard.html` in your browser.
2. Click the **One-Click Deploy** button in the top-right header.
3. Enter your **Netlify Personal Access Token** (the modal includes a link to generate a free token in 30 seconds).
4. Click **Deploy Dashboard**. The dashboard will automatically compile its layout and active agent states into an in-memory ZIP and upload it directly to Netlify. 
5. The URL and Site ID are cached locally in your browser's `localStorage` so future deploys take exactly one click.

### Path B: Double-Click Desktop Launchers
Run the deployment process directly from your workspace folder:
- **Windows:** Double-click the `deploy.bat` launcher. It compiles the latest dashboard state and pushes it to Netlify via a zero-dependency Python script.
- **macOS/Linux:** Open a terminal in the repository root and run `./deploy.sh`.

### Path C: Git-Backed Auto-Deploy
Push this repository to GitHub and link your repository to Vercel or Netlify. The repo includes pre-configured `vercel.json` and `netlify.toml` files to auto-compile and host the dashboard.

## Why this exists

Most AI marketing tools are either:

1. a blank chat box,
2. a narrow content generator, or
3. a dashboard that cannot understand your product repo.

Kai does the opposite. It runs where your product already lives — the terminal — and gives Claude Code a structured marketing operating system: command routing, strategy documents, platform policies, channel playbooks, QA gates, approval workflows, runtime models, and repeatable growth workflows.

## Product shape

### Kai Runtime

The Claude Code-style product shell:

- workspace profile
- brand memory
- module activation
- local runs
- remote runs

### Kai Marketing OS

The marketing-specific operating system:

- quality gates
- archetype-specific workflows
- campaign and content orchestration
- approvals
- learning loop

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

## 36 public router commands, 40 canonical skills

These commands work through Claude Code's skill system. They load knowledge files and framework instructions for the LLM. They do not invoke the `kai/` Python runtime directly.

The table below reflects the `/kai` router surface. The complete canonical skill inventory lives in the [public skill manifest](docs/skill-manifest/README.md), which includes all 40 `harness/skills/kai-*` directories.

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

### Plan strategy

| Command | What you get |
|---|---|
| `/kai-brief` | Content brief before writing |
| `/kai-growth-plan` | Marketing plan by stage: pre-launch, launch, growth, or scale |
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

- **48 marketing playbook docs** — growth loops, CRO, pricing, competitive intel, content repurposing, lifecycle marketing, launches, retargeting, ABM, partnerships, and more
- **27 frameworks** — SEO rules, AEO/GEO strategy, AI-search optimization, perception engineering, copywriting formulas, quality-rater guidance, query fan-out, and LLM citation tracking
- **32 checklists** — technical SEO, ad launches, content quality, email, PR, website launches, social audits, creative production, and paid acquisition
- **17 channel guides** — SEO content, LinkedIn, Meta ads, TikTok, YouTube, X/Twitter, Instagram, newsletters, podcasts, community, affiliate/referral, and press
- **18 harness references** — ad platform policies, API notes, compliance references, provenance rules, creator disclosure, and analytics query templates
- **8 audience personas** — pains, hooks, objections, emotional drivers, and voice guidance
- **Quality gates** — Four U's, banned-word checks, proof density, specificity, platform compliance, SEO linting, and AI-slop detection

## Core use cases

### For SaaS founders

Use Kai to go from "we need marketing" to a concrete plan: landing page, launch content, lifecycle emails, cold outreach, SEO roadmap, paid campaign angles, and AI-search visibility.

### For agencies

Install Kai inside a client repo and create repeatable strategy, content, campaign, and audit workflows without rebuilding your operating system for every account.

### For indie hackers

Use `/kai-growth-plan`, `/kai-landing-page`, `/kai-cold-outreach`, and `/kai-content-calendar` to create a practical marketing system without hiring a team.

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
