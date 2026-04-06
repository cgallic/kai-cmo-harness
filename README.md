# Kai — Marketing OS built on Claude Code

Kai is a **marketing operating system that runs inside Claude Code**.

It uses Claude Code's operator experience (skills, subagents, hooks, memory) and adds marketing-specific infrastructure:

- **Business profiling** with archetype detection and overlay inference
- **Audit engines** that score businesses across 8 categories with real algorithms
- **Proposal ranking** with 5-factor weighted scoring, dependency resolution, and capacity pruning
- **Approval workflows** with risk-based auto-approval and state machine enforcement
- **Compliance checking** with 100+ rules and regex pattern matching
- **Quality gates** (Four U's scoring, banned word detection, SEO lint)
- **168 marketing knowledge files** (41 playbooks, 27 frameworks, 24 checklists, 12 ad platform policies)

### Current status (v1.0.0, April 2026)

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

**Option 1 — One-liner** (paste into your terminal):

```
curl -fsSL https://raw.githubusercontent.com/cgallic/kai-cmo-harness/main/install.sh | bash
```

**Option 2 — Manual** (paste into Claude Code):

```
git clone https://github.com/cgallic/kai-cmo-harness.git /tmp/kai-install && cp -r /tmp/kai-install/harness/skills/kai* ~/.claude/skills/ && rm -rf /tmp/kai-install && echo "Installed! Type /kai to start."
```

**First run:** Type `/kai-start` for guided setup. It reads your codebase, creates `MARKETING.md`, and recommends your first command.

Or type `/kai` to see all 31 commands.

## Product shape

### Kai Runtime
The clone layer. This is the Claude Code-style product shell:
- workspace profile
- brand memory
- module activation
- local runs
- remote runs

### Kai Marketing OS
The differentiation layer. This is the marketing-specific operating system:
- quality gates
- archetype-specific workflows
- campaign and content orchestration
- approvals
- learning loop

## What can it do?

### Via Claude Code skills (knowledge-driven, LLM-powered)

These work today through Claude Code's skill system. They load marketing knowledge + framework instructions and let the LLM do the work:

**"Write all my emails"** → `/kai-email-system`
Maps every email your product needs, writes them all, checks quality, outputs ready for Loops.

**"Create my ad campaign"** → `/kai-ad-campaign`
Plans ads across Meta, Google, LinkedIn, TikTok with policy compliance.

**"Plan my content for the month"** → `/kai-content-calendar`
Generates a month of content mapped to keywords, personas, and business goals.

**"Audit my marketing"** → `/kai-audit`
Runs checklists across SEO, content, email, ads, social, CRO. Health score + prioritized fixes.

**"Write a landing page"** → `/kai-landing-page`
Full landing page copy using conversion psychology frameworks.

### Via kai/ runtime (programmatic, tested)

These work through the Python runtime with real algorithms:

- **Business profiling**: Load a profile, detect archetype, infer overlays
- **Scored audits**: 8 audit engines with severity-weighted scoring across 40+ checks
- **Proposal ranking**: 5-factor weighted scoring with dedup, dependency resolution, capacity pruning
- **Approval workflows**: Risk-based auto-approval, state machine, batch review
- **Compliance checks**: 100+ rules with regex pattern matching, violation tracking
- **Run persistence**: Atomic JSON writes with lineage tracking and audit log

## How it works

First time you run any `/kai` command in a project, it:

1. **Reads your codebase** — CLAUDE.md, README, package.json, routes, schemas, whatever exists
2. **Builds a runtime profile** — workspace, brand, archetype/module defaults, proof points, channels
3. **Creates `MARKETING.md` as a readable export** — ICP, personas, brand voice, landscape, and operating defaults
4. **Does the work** — writes, audits, plans, scores, and routes outputs through the gate

Every command after that should run from the same workspace/brand/module model. `MARKETING.md` remains useful for humans, but the runtime contract is moving into code.

## Architecture

```text
Kai Marketing OS
  -> outcome engine, quality gate, approvals, archetype modules

Kai Runtime
  -> skills, subagents, hooks, memory, plugins, local/remote runs

Implementation
  -> scripts/content, scripts/quality, gateway, agent, knowledge
```

The new canonical runtime models live in `kai/runtime/`.

## All 31 commands (Claude Code skills)

These commands work through Claude Code's skill system. They load knowledge files and framework instructions for the LLM. They do not invoke the kai/ Python runtime directly.

### Make stuff

| Command | What you get |
|---------|-------------|
| `/kai-write` | One piece of content — blog, email, LinkedIn, ad, press release |
| `/kai-landing-page` | Complete landing page copy |
| `/kai-email-system` | Every email your product needs |
| `/kai-ad-campaign` | Full ad campaign across platforms |
| `/kai-content-calendar` | Month of planned + written content |
| `/kai-social` | Week/month of social posts for all platforms |
| `/kai-video` | Video scripts for TikTok, YouTube, Reels |
| `/kai-cold-outreach` | Cold email sequences |
| `/kai-newsletter` | Newsletter editions |
| `/kai-case-study` | Customer success stories |
| `/kai-repurpose` | 1 piece → 15-25 pieces across platforms |
| `/kai-launch` | Full product launch — emails + ads + PR + content + social |
| `/kai-retarget` | Retargeting campaign setup |
| `/kai-influencer` | Influencer marketing campaigns |
| `/kai-webinar` | Webinar/event marketing |
| `/kai-podcast` | Podcast launch or guest strategy |
| `/kai-abm` | Account-based marketing for enterprise |
| `/kai-partnership` | Co-marketing campaigns |

### Check stuff

| Command | What you get |
|---------|-------------|
| `/kai-gate` | Quality score on any content |
| `/kai-audit` | Full marketing audit with health scores |
| `/kai-seo-audit` | Technical SEO audit with fix list |
| `/kai-cro` | Conversion rate audit for any page |

### Plan stuff

| Command | What you get |
|---------|-------------|
| `/kai-brief` | Content brief before writing |
| `/kai-growth-plan` | Marketing plan for your stage |
| `/kai-brand` | Brand positioning + messaging framework |
| `/kai-budget` | Marketing budget planning |
| `/kai-retention` | Customer retention system |

### Research stuff

| Command | What you get |
|---------|-------------|
| `/kai-competitors` | Competitive teardown + sales battlecards |
| `/kai-surround-sound` | Get mentioned in AI answers |
| `/kai-analytics` | Analytics + attribution setup |

### Help

| Command | What you get |
|---------|-------------|
| `/kai` | See all commands, organized by what you need |

## Where to start

**Just launched?** → `/kai-growth-plan` first, then `/kai-email-system` + `/kai-landing-page`

**Need content?** → `/kai-content-calendar` for the plan, `/kai-write` for individual pieces

**Running ads?** → `/kai-ad-campaign` handles the copy, `/kai-cro` audits your landing page

**Want everything?** → `/kai-launch` orchestrates all of the above into one coordinated campaign

## What's behind it

153 marketing knowledge files that power the commands:

- 41 playbooks (growth loops, CRO, pricing, competitive intel, content repurposing...)
- 27 frameworks (SEO rules, persuasion psychology, copywriting formulas, AI search optimization)
- 24 checklists (technical SEO, ad launch, content quality, email, social media audit...)
- 17 channel guides (every major platform)
- 8 audience personas
- 12 ad platform policies (Google, Meta, TikTok, LinkedIn, and 6 more — 7,600+ lines of TOS so your ads don't get rejected)

Every piece of content gets quality-checked before it ships:
- **Four U's score** — is it Unique, Useful, Ultra-specific, Urgent?
- **Banned word check** — no "leverage", "synergy", or AI slop
- **Platform compliance** — character limits, policy rules, format requirements

## Requirements

- [Claude Code](https://claude.ai/download) (CLI, desktop app, or VS Code extension)
- That's it

## License

MIT — use it however you want.
