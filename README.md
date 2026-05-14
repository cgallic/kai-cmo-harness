# Kai CMO Harness — AI Marketing OS for Claude Code

**Kai CMO Harness turns Claude Code into an AI marketing team:** 33 slash commands plus a tested marketing runtime for SEO, content, email, paid ads, landing pages, product launches, lifecycle marketing, competitive research, CRO, and AI-search/GEO strategy.

If you searched for **AI marketing agent**, **Claude Code marketing skills**, **AI CMO**, **marketing automation for startups**, **SEO content agent**, **GEO / AEO agent**, **LLM citation strategy**, or **AI growth marketing assistant**, this is the repo you wanted.

## Related links

- [MeetKai](https://meetkai.xyz) — the operator layer behind Kai CMO workflows.
- [KaiCalls](https://kaicalls.com) — AI voice agents for small-business phone answering and lead capture.
- [Connor Gallic](https://connorgallic.com) — founder building Kai, KaiCalls, and AI automation systems.
- [AI-powered paid media system](docs/AI_POWERED_ADS_SYSTEM.md) — plain-English explanation of how Kai lowers the operating cost around paid acquisition.

## What Kai is

Kai is a **marketing operating system that runs inside Claude Code**.

It uses Claude Code's operator experience — skills, subagents, hooks, memory, and terminal-native workflows — and adds marketing-specific infrastructure:

- **Business profiling** with archetype detection and overlay inference
- **Audit engines** that score businesses across 8 categories with real algorithms
- **Proposal ranking** with 5-factor weighted scoring, dependency resolution, and capacity pruning
- **Approval workflows** with risk-based auto-approval and state machine enforcement
- **Compliance checking** with 100+ rules and regex pattern matching
- **Quality gates**: Four U's scoring, banned-word detection, SEO linting, proof density, and AI-slop checks
- **168 marketing knowledge files**: playbooks, frameworks, checklists, channel guides, personas, and ad platform policies
- **Claude Code marketing skills** for content, ads, lifecycle, SEO, GEO/AEO, audits, launches, and growth planning

It is built for founders, indie hackers, SaaS teams, agencies, and product engineers who want Claude Code to help with actual growth work instead of generic copy generation.

## Current status (v1.0.0, April 2026)

| Layer | Status | Notes |
|-------|--------|-------|
| Runtime models + persistence | Built | Atomic writes, thread-safe, audit log |
| Audit engines (8 categories) | Built | Real scoring algorithms, 239 tests passing |
| Proposal ranking + bundling | Built | 5-factor weighted, dependency-aware |
| Approval + action lifecycle | Built | State machine enforced, tested |
| Compliance engine | Built | 100+ rules, 50+ regex patterns |
| Content pipeline + quality gates | Built | LLM-backed via `scripts/content/engine.py` |
| Knowledge base | Built | 168 files, production-grade marketing intelligence |
| Connector business logic | Partial | Request construction complete, HTTP transport not wired |
| Creative module | Partial | Generates briefs/templates, not final content |
| Watchers/monitoring | Partial | Threshold logic real, data feeds not connected |
| Agent loop / subagent orchestration | Planned | Scaffolding only |
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

Or type `/kai` to see all 33 commands.

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
| "Get us into ChatGPT answers" | `/kai-surround-sound` | AI-search visibility and LLM citation strategy |
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

## All 33 commands (Claude Code skills)

These commands work through Claude Code's skill system. They load knowledge files and framework instructions for the LLM. They do not invoke the `kai/` Python runtime directly.

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
| `/kai-seo-audit` | Technical SEO and semantic SEO audit with prioritized fixes |
| `/kai-cro` | Conversion-rate audit for landing pages and funnels |

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
| `/kai-surround-sound` | AEO/GEO strategy to get mentioned in ChatGPT, Perplexity, Gemini, Claude, and AI Overviews |
| `/kai-analytics` | Analytics and attribution setup |
| `/kai` | Command router and help menu |

## What is included

Kai ships with a real marketing knowledge base, not just prompts:

- **41 marketing playbooks** — growth loops, CRO, pricing, competitive intel, content repurposing, lifecycle marketing, launches, retargeting, ABM, partnerships, and more
- **27 frameworks** — SEO rules, AEO/GEO strategy, AI-search optimization, perception engineering, copywriting formulas, quality-rater guidance, query fan-out, and LLM citation tracking
- **24 checklists** — technical SEO, ad launches, content quality, email, PR, website launches, social audits, creative production, and paid acquisition
- **17 channel guides** — SEO content, LinkedIn, Meta ads, TikTok, YouTube, X/Twitter, Instagram, newsletters, podcasts, community, affiliate/referral, and press
- **12 ad platform policies** — Google, Meta, TikTok, LinkedIn, Microsoft, Pinterest, Snapchat, Amazon, X, and more
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
kai/runtime/                 Runtime models, state, profiles, approvals, and action lifecycle
scripts/quality/             Content quality gate and scoring rules
scripts/content/             Briefing, writing, reporting, and content workflow scripts
scripts/analytics/           Search Console, GA4, Stripe, Meta, and competitive monitoring utilities
harness/references/          Ad policy and compliance references
harness/skill-contracts/     Output contracts for common marketing assets
workspace/                   Example CMO-agent operating workspace
tools/docker/                Modal and RunPod media-generation worker templates
```

## Where to start

- **Just launched:** `/kai-growth-plan` → `/kai-email-system` → `/kai-landing-page`
- **Need organic growth:** `/kai-content-calendar` → `/kai-write` → `/kai-gate`
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
