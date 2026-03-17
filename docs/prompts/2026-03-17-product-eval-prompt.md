# Kai Harness — Full Product Evaluation Prompt

## What You Are Evaluating

The **Kai Harness** is an agentic marketing CMO. It's a product — not a library, not a plugin, not a framework. It sits on top of AI coding tools (Claude Code, Codex, Cursor, etc.) the same way Claude Code sits on top of VS Code. Users install it, authenticate, and get an autonomous marketing department that generates content, enforces quality, learns from performance, and improves over time.

The goal: **become the defacto marketing agent.**

---

## Current State (as of 2026-03-17)

### What exists today

**Knowledge Base (30+ files)**
- 7 content/copywriting frameworks (Algorithmic Authorship, Perception Engineering, Four U's, etc.)
- 12 AEO/AI search optimization files (patent analysis, citation science, Perplexity reverse-engineering)
- 11 channel-specific guides (blog, LinkedIn, email, TikTok, Meta ads, Google ads, press, podcast, etc.)
- 17 quality checklists (SEO, content, meta ads, TikTok, paid acquisition, technical SEO audit, etc.)
- 8 audience personas with pain points, language patterns, and hooks
- 10 platform ad policy references (Google, Meta, TikTok, LinkedIn, Microsoft, Pinterest, Snapchat, Amazon, X, plus FTC/GDPR/CAN-SPAM compliance)

**Outcome Engine (just built)**
- `generate(format, site, keyword)` — collapses 28 content decisions to 3 inputs
- Auto-resolves persona from site+keyword signals
- Auto-generates 18-field content briefs using GSC data + LLM inference
- Writes content using format-specific frameworks + skill contracts
- Runs unified quality gate (scoring, banned words, SEO lint) with max 2 auto-retries
- Applies configurable approval policy (auto/hold/reject_only per format+site)
- Logs everything for 30-day performance tracking

**Quality Gate System**
- Unified scorer with per-format policies (blog-publish, meta-ad, cold-email, etc.)
- Four U's scoring (Unique, Useful, Ultra-specific, Urgent) — 12/16 minimum for publishing
- Banned word detection (50+ tier-1 instant-reject words)
- SEO linting (keyword placement, sentence length, internal links, heading structure)
- Surgical revision: only fix what failed, protect what passed
- Human escalation after 2 failed retries

**Self-Improvement Loop**
- 30-day performance checks (GSC position, CTR, GA4 session duration)
- Weekly pattern extraction from winners (hook type, format, word count, persona, publish day)
- Auto-updates MARKETING.md learned defaults — next content run uses new patterns
- Statistical thresholds: n>=5 samples, 15%+ lift required before patterns promote

**Surfaces (4 today)**
- CLI: `kai-harness generate --format blog --site kaicalls --keyword "..."`
- Discord: `!kai blog kaicalls "AI receptionists"`
- HTTP API: `POST /generate` with async job queue
- (planned) Native integration with Claude Code / Codex / Cursor

**Infrastructure**
- FastAPI gateway with 11 routers, 30+ endpoints
- SQLite-backed async job queue
- API key authentication
- Analytics integrations: GSC, GA4, Supabase, Stripe, Meta Ads, Instantly, Loops
- OpenClaw autonomous agent mode with Discord-based command interface, scheduled heartbeats, and domain-specific agents

**Config**
- `CLAUDE.md` as entry point — Claude Code reads it and gains marketing intelligence
- `MARKETING.md` as operating config — thresholds, framework map, learned defaults
- `config.yaml` for site mappings, persona defaults, approval policies
- Skill contracts (YAML) per content format define word counts, gate thresholds, required sections
- `harness/references/` for platform-specific ad policy compliance

### What does NOT exist yet

- No user authentication (OAuth, accounts, multi-tenancy)
- No billing / subscription system
- No onboarding flow
- No web dashboard or UI
- No native integration with Claude Code / Codex / Cursor (currently CLI + Discord + HTTP only)
- No marketplace or distribution mechanism
- No client isolation (all sites share one config)
- No real-time analytics dashboard
- No A/B testing infrastructure
- No direct publishing integrations (WordPress, Webflow, Shopify, etc.)
- No team collaboration features
- No audit trail / content versioning
- No brand voice training / fine-tuning
- No competitive monitoring automation
- No multi-language support

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE BASE                           │
│  30+ frameworks, 17 checklists, 8 personas, 10 ad policies │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTCOME ENGINE                            │
│  generate(format, site, keyword) → content + gate + status  │
│                                                             │
│  persona_resolver → brief_generator → _writer → gate →     │
│  approval_policy → content_log                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    QUALITY GATES                             │
│  Unified scorer + per-format policies + surgical revision   │
│  Max 2 retries → human escalation                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  SELF-IMPROVEMENT LOOP                        │
│  30-day performance check → pattern extraction →             │
│  learned defaults → next run uses new patterns              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      SURFACES                                │
│  CLI | Discord | HTTP API | (planned: native AI tool auth)  │
└─────────────────────────────────────────────────────────────┘
```

---

## The Question

Evaluate the Kai Harness as a product. Be brutally honest. Cover:

### 1. Product-Market Fit
- Who is the actual customer? Solo founders? Agencies? Enterprise marketing teams?
- What's the job-to-be-done that no existing tool does well enough?
- Is "agentic marketing CMO" a real category or are we creating one?
- What's the wedge — the first use case that gets people in the door?

### 2. Competitive Landscape
- What exists today in AI marketing agents? (Jasper, Copy.ai, Writer, Typeface, etc.)
- How do they distribute? What's their moat?
- What does the Kai Harness do that none of them do?
- What do they do that the Kai Harness doesn't?
- Where are the gaps in the market?

### 3. Technical Architecture Assessment
- Is the current architecture sound for a multi-tenant product?
- What needs to change to go from "one team's tool" to "product anyone can use"?
- How should authentication and user management work?
- How should the harness connect to Claude Code / Codex / Cursor natively?
- What's the right distribution model? (CLI install, VS Code extension, SaaS, marketplace?)

### 4. Moat Analysis
- What's defensible about this?
- Is the knowledge base a moat or a commodity?
- Is the self-improvement loop a moat?
- Is the quality gate system a moat?
- What would it take for Jasper/Copy.ai to replicate this?

### 5. What's Missing — Priority Stack
- Rank the missing pieces by impact and effort
- What are the 3 things that would make this a real product people pay for?
- What are the 3 things that are nice-to-have distractions?
- What's the fastest path to first paying customer?

### 6. Distribution Strategy
- How do people discover this?
- How do people try it?
- How do people pay for it?
- What's the pricing model? (Per-seat? Per-content-piece? Per-site? Usage-based?)
- How does it integrate with the tools marketers already use?

### 7. Go-to-Market
- What's the launch strategy?
- What's the narrative? ("Your AI marketing department" vs "Content quality gates" vs "Self-improving content engine" vs something else?)
- Who are the first 10 customers and how do you reach them?
- What's the proof point that makes people say "I need this"?

### 8. Roadmap Recommendation
- Given everything above, what should be built next?
- What's the 30-day plan?
- What's the 90-day plan?
- What should be killed or deprioritized?

---

## Context for Your Evaluation

- The builder is a technical founder who runs multiple sites (KaiCalls, BuildWithKai, MeetKai, etc.)
- The harness was originally built for internal use — managing content across 6 sites
- The transition from "internal tool" to "product" is the current inflection point
- Budget is bootstrapped — no VC, no big team
- The AI coding tool ecosystem (Claude Code, Codex, Cursor) is growing fast and these tools support extensions/plugins/integrations
- The marketing AI space is crowded but mostly focused on "generate text" — not on quality gates, self-improvement loops, or agentic workflows
- The knowledge base represents real institutional knowledge (reverse-engineered Google patents, platform ad policies, proven frameworks) — not generic AI training data

Be specific. Give concrete recommendations, not platitudes. If something should be killed, say so. If the product thesis is wrong, say that too.
