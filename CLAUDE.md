# CLAUDE.md — Kai CMO Harness

Marketing knowledge base + content pipeline with quality gates. Drop into any Claude Code project for instant marketing intelligence.

This file is the entry point. Claude Code reads it automatically and gains access to 30+ frameworks, 17 checklists, 8 audience personas, and a quality gate pipeline that enforces standards before anything ships.

---

## Quick Start

### Path A: Claude Code (5 min)

Copy four things into your project root:

```
your-project/
├── CLAUDE.md                    # This file
├── knowledge/                   # Frameworks, channels, checklists, personas
├── harness/                     # Skill contracts, brief schema, references
└── scripts/quality_gates/       # Automated scoring and linting
```

That's it. Claude Code will read this file on startup and know how to find everything.

### Path B: OpenClaw Autonomous CMO (30 min)

Full autonomous operation with Discord integration, scheduled heartbeats, domain agents, and human-in-the-loop approval. See `docs/OPENCLAW_SETUP.md` for setup instructions.

---

## Framework Map

When you need to create content, find the right framework here. Load the primary framework as context, then validate against the checklist.

| Task | Primary Framework | Checklist |
|------|-------------------|-----------|
| Blog post | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` | `knowledge/checklists/content-checklist.md` |
| LinkedIn article | `knowledge/channels/linkedin-articles.md` | — |
| Email (lifecycle) | `knowledge/channels/email-lifecycle.md` | `knowledge/checklists/email-checklist.md` |
| Email (cold outreach) | `knowledge/channels/email-lifecycle.md` + `harness/references/cold-email-rules.md` | — |
| SEO content | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` + `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` | `knowledge/checklists/seo-checklist.md` |
| Meta ads (FB/IG) | `knowledge/channels/meta-advertising.md` + `harness/references/meta-ads-rules.md` | `knowledge/checklists/meta-advertising-checklist.md` |
| Google ads | `knowledge/channels/paid-acquisition.md` + `harness/references/google-ads-policy-reference.md` | `knowledge/checklists/paid-acquisition-checklist.md` |
| LinkedIn ads | `knowledge/channels/linkedin-articles.md` + `harness/references/linkedin-ads-rules.md` | `knowledge/checklists/paid-acquisition-checklist.md` |
| Microsoft/Bing ads | `knowledge/channels/paid-acquisition.md` + `harness/references/microsoft-ads-rules.md` | `knowledge/checklists/paid-acquisition-checklist.md` |
| Pinterest ads | `harness/references/pinterest-ads-rules.md` | `knowledge/checklists/paid-acquisition-checklist.md` |
| TikTok ads | `knowledge/channels/tiktok-algorithm.md` + `harness/references/tiktok-ads-policy-reference.md` | `knowledge/checklists/tiktok-checklist.md` |
| TikTok Shop | `knowledge/channels/tiktok-shop.md` + `harness/references/tiktok-ads-policy-reference.md` | `knowledge/checklists/tiktok-checklist.md` |
| Snapchat ads | `harness/references/snapchat-ads-policy-reference.md` | `knowledge/checklists/paid-acquisition-checklist.md` |
| Amazon ads | `harness/references/amazon-ads-policy-reference.md` | `knowledge/checklists/paid-acquisition-checklist.md` |
| X/Twitter ads | `harness/references/x-ads-policy-reference.md` | `knowledge/checklists/paid-acquisition-checklist.md` |
| Press release | `knowledge/channels/press-releases.md` | `knowledge/checklists/pr-checklist.md` |
| Sales/landing page | `knowledge/frameworks/content-copywriting/perception-engineering.md` | `knowledge/checklists/perception-engineering-checklist.md` |
| Technical SEO audit | `knowledge/checklists/technical-seo-audit-sop.md` | `knowledge/checklists/seo-checklist.md` |
| Podcast setup | `knowledge/channels/podcast.md` | — |
| Site architecture | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` | `knowledge/checklists/seo-checklist.md` |

For the full framework index with "use when" triggers, see `knowledge/_index.md`.

---

## Quality Gate Rules

These are non-negotiable. Every piece of content must pass before it ships.

### Four U's Score

Score every piece 1-4 on each dimension. **Minimum 12/16 for publishing** (10/16 for ads and email).

| U | Question |
|---|----------|
| **Unique** | Can only WE write this? |
| **Useful** | Can reader take action immediately? |
| **Ultra-specific** | Are there numbers, examples, named tools? |
| **Urgent** | Is there a reason to engage today? |

Run: `python scripts/quality_gates/four_us_score.py <file>`

### Banned Words

Tier 1 words trigger instant rejection. No exceptions.

**Instant reject**: leverage, utilize, synergy, innovative, deep dive, circle back, touch base, moving forward, at the end of the day

Run: `python scripts/quality_gates/banned_word_check.py <file>`

### AI Slop Detection

Never use these phrases. They signal machine-generated filler:

- "In conclusion"
- "It's important to note"
- "In today's rapidly evolving"
- "This comprehensive guide"
- "Without further ado"
- "It's worth noting that"

### Algorithmic Authorship (SEO content)

Applied automatically for any content targeting search. Key rules:

1. Conditions AFTER main clause: "Do X if Y" — not "If Y, do X"
2. Instructions start with verbs: "Whip lightly" — not "Lightly whip"
3. Sentences under 20 words where possible
4. Bold the **answer**, not the query-matching terms

Run: `python scripts/quality_gates/seo_lint.py <file>`

### Gate Pipeline

```
Write content --> four_us_score.py --> banned_word_check.py --> seo_lint.py (if SEO) --> PASS/FAIL
```

Max 2 auto-retry cycles. After 2 failures, surface to a human with the specific failures listed.

### Ad Policy Compliance Gate

**Before writing any ad copy**, load the platform's policy reference. Every ad must pass platform TOS in addition to quality gates.

| Platform | Policy Reference | Key Restrictions |
|----------|-----------------|------------------|
| Google Ads | `harness/references/google-ads-policy-reference.md` | Healthcare certs, financial disclosures, no superlatives without proof |
| Meta (FB/IG) | `harness/references/meta-ads-rules.md` | Special Ad Categories (housing/employment/credit), no before/after images, personal attributes ban |
| TikTok | `harness/references/tiktok-ads-policy-reference.md` | No political ads, weight management restrictions, AI content disclosure required |
| LinkedIn | `harness/references/linkedin-ads-rules.md` | Professional context required, B2B claim substantiation |
| Microsoft/Bing | `harness/references/microsoft-ads-rules.md` | Global gambling bans by country, clinical trials ban |
| Pinterest | `harness/references/pinterest-ads-rules.md` | All weight loss ads banned (narrow GLP-1 exception), strict body image rules |
| Snapchat | `harness/references/snapchat-ads-policy-reference.md` | Young audience protections, EU political ad ban |
| Amazon | `harness/references/amazon-ads-policy-reference.md` | 18-month claim evidence rule, no competitor disparagement |
| X/Twitter | `harness/references/x-ads-policy-reference.md` | Verification tier affects ad access, political ad certification by country |
| **All platforms** | `harness/references/advertising-compliance.md` | FTC disclosures, GDPR consent, CAN-SPAM, COPPA, click-to-cancel rule |

```
Write ad --> Load platform policy --> Quality gate --> Policy compliance check --> PASS/FAIL
```

---

## Key Frameworks

### Algorithmic Authorship — Top 10 Rules

These rules are reverse-engineered from Google's AI Overviews selection patterns. Apply to all SEO content.

1. **Conditions AFTER main clause**: "Do X if Y" not "If Y, do X"
2. **Instructions start with verbs**: "Whip lightly" not "Lightly whip"
3. **Short sentences** — break complex sentences apart
4. **Numeric lists** for steps/methods, **bulleted lists** for types/categories
5. **Name entities twice** before switching to attributes or pronouns
6. **Anchor words** connect sequential sentences (repeat a key term)
7. **Examples follow** every declaration or claim
8. **Bold the ANSWER**, not query-matching terms
9. **No links** in the first sentence of paragraphs
10. **Same part of speech** across all list items

Full framework: `knowledge/frameworks/content-copywriting/algorithmic-authorship.md`

### Perception Engineering — 3 Layers

Use for sales pages, landing pages, and conversion-focused copy.

| Layer | Goal | Key Tactic |
|-------|------|------------|
| **Perception** | Destabilize cached beliefs | Re-index "virtues" as "vices" |
| **Context** | Shift what feels allowed | Genre-shift (Exam to Lab) |
| **Permission** | Remove consequences | Future pacing, double binds |

Full framework: `knowledge/frameworks/content-copywriting/perception-engineering.md`

### Four U's — Content Quality Scoring

| U | Question | Score 1-4 |
|---|----------|-----------|
| **Unique** | Can only WE write this? | |
| **Useful** | Can reader take action? | |
| **Ultra-specific** | Are there numbers/examples? | |
| **Urgent** | Is there reason to engage today? | |

**Target**: 12+/16 for blog/SEO/articles. 10+/16 for ads/email.

Full framework: `knowledge/frameworks/content-copywriting/four-us-framework.md`

---

## 8 Marketing Personas

Every piece targets one of these personas. Pick the right one before writing.

| Persona | Core Hook |
|---------|-----------|
| **Competent Cog** | "The system treats you like a child" |
| **Shock Absorber** | "Accountability without authority" |
| **Ghosted Applicant** | "The game is rigged against you" |
| **Subscription Serf** | "They're betting you won't fight back" |
| **System Manager** | "There is no village, only vendors" |
| **Admin Martyr** | "Death by a thousand tasks" |
| **Obsolescence Anxious** | "Working hard isn't the variable anymore" |
| **Credibility Fighter** | "You're not crazy, this is happening" |

Full profiles with pain points, language patterns, and hooks: `knowledge/personas/_persona-index.md`

---

## Skill Contracts

Every content format has a contract in `harness/skill-contracts/` that defines structure, constraints, and gate thresholds.

| Contract | Format | Min Four U's | SEO Lint |
|----------|--------|:------------:|:--------:|
| `blog-post.yaml` | Blog post | 12/16 | Required |
| `linkedin-article.yaml` | LinkedIn article | 12/16 | Skipped |
| `email-lifecycle.yaml` | Nurture/lifecycle email | 10/16 | Skipped |
| `cold-email.yaml` | Cold outreach email | 10/16 | Skipped |
| `meta-ads.yaml` | Meta/Facebook/Instagram ads | 10/16 | Skipped |
| `google-ads.yaml` | Google Ads copy | 10/16 | Skipped |
| `email.yaml` | General email | 10/16 | Skipped |

Load the relevant contract before writing. It specifies word counts, required sections, tone, and validation rules.

---

## Content Pipeline

The harness enforces this pipeline for every piece of content:

```
Research --> Brief --> Write --> Quality Gate --> Approval --> Publish --> Log --> 30-day Check
```

**Step-by-step:**

1. **Research** — Check `knowledge/_index.md` to find the right framework. Load it.
2. **Brief** — Create a structured brief using `harness/brief-schema.md`. Define persona, angle, keywords, format.
3. **Write** — Apply the framework + quality rules + persona hooks. Follow the skill contract.
4. **Gate** — Run the quality gate scripts. All three must pass:
   - `scripts/quality_gates/four_us_score.py` (score threshold per contract)
   - `scripts/quality_gates/banned_word_check.py` (zero Tier 1 violations)
   - `scripts/quality_gates/seo_lint.py` (SEO content only)
5. **Retry** — Max 2 auto-retry cycles on gate failure. Fix specific issues flagged.
6. **Escalate** — After 2 failures, surface to human with failure details. Do not loop forever.
7. **Publish** — Deliver to the appropriate channel.
8. **Log** — Record what was published, when, and for which persona.
9. **30-day Check** — Revisit performance. Feed learnings back into the pipeline.

---

## Directory Structure

```
kai-cmo-harness/
├── CLAUDE.md                              # This file — start here
│
├── knowledge/                             # Marketing intelligence library
│   ├── _index.md                          # Framework lookup table
│   ├── _quick-reference.md                # One-page cheat sheet
│   ├── _deep-research-prompts.md          # Prompts for generating new frameworks
│   ├── frameworks/
│   │   ├── content-copywriting/           # Writing rules and persuasion (7 files)
│   │   ├── aeo-ai-search/                 # AEO, patents, AI search ranking (12 files)
│   │   └── meta-advertising/              # Meta ad system internals (4 files)
│   ├── channels/                          # Channel-specific guides (11 files)
│   ├── checklists/                        # Validation checklists (17 files)
│   ├── personas/                          # 8 audience personas
│   ├── playbooks/                         # Strategic playbooks
│   ├── design/                            # UI/UX design patterns
│   └── examples/                          # Reference examples
│
├── harness/                               # Content pipeline engine
│   ├── brief-schema.md                    # Content brief template
│   ├── skill-contracts/                   # Per-format contracts (7 YAML files)
│   ├── references/                        # Platform-specific rules & policies
│   │   ├── cold-email-rules.md            # CAN-SPAM, deliverability
│   │   ├── google-ads-rules.md            # Google Ads copy constraints
│   │   ├── google-ads-policy-reference.md # Google Ads full TOS/policies (991 lines)
│   │   ├── meta-ads-rules.md              # Meta/FB/IG full TOS/policies (931 lines)
│   │   ├── tiktok-ads-policy-reference.md # TikTok full TOS/policies (1020 lines)
│   │   ├── linkedin-ads-rules.md          # LinkedIn Ads policies (465 lines)
│   │   ├── microsoft-ads-rules.md         # Microsoft/Bing Ads policies (431 lines)
│   │   ├── pinterest-ads-rules.md         # Pinterest Ads policies (490 lines)
│   │   ├── snapchat-ads-policy-reference.md # Snapchat Ads policies (512 lines)
│   │   ├── amazon-ads-policy-reference.md # Amazon Ads policies (579 lines)
│   │   ├── x-ads-policy-reference.md      # X/Twitter Ads policies (621 lines)
│   │   └── advertising-compliance.md      # FTC/GDPR/CAN-SPAM/COPPA/CCPA (1500 lines)
│   └── ARCHITECTURE.md                    # Harness design docs
│
├── scripts/
│   └── quality_gates/                     # Automated content validation
│       ├── four_us_score.py               # Four U's scorer (12/16 threshold)
│       ├── banned_word_check.py           # Banned word detection
│       └── seo_lint.py                    # SEO rule linter
│
├── agent/                                 # OpenClaw autonomous agent config
├── gateway/                               # Webhook gateway (FastAPI)
├── workspace/                             # Working directory for content output
├── deploy/                                # Deployment scripts
├── docs/                                  # Extended documentation
└── examples/                              # Usage examples
```

---

## AEO & AI Search Quick Reference

Traditional SEO is not enough. AI search engines (Google AI Overviews, Perplexity, ChatGPT) use different ranking signals.

| Traditional SEO | AEO (Answer Engine Optimization) |
|-----------------|----------------------------------|
| Optimize for keywords | Optimize for **entities** |
| Build backlinks | Build **citations** (+115% visibility) |
| Long-form content | **Atomic facts** per sentence |
| Keyword in title | **Information Gain** (novelty over consensus) |
| Generic authority | **Entity Home** + Knowledge Graph |
| Any content | Content with **Experience** evidence |

Key research files:
- Patent analysis: `knowledge/frameworks/aeo-ai-search/patent-information-gain-US12013887B2.md`
- Citation science: `knowledge/frameworks/aeo-ai-search/geo-academic-research-synthesis.md`
- Perplexity internals: `knowledge/frameworks/aeo-ai-search/perplexity-ranking-reverse-engineered.md`
- Full playbook: `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`

---

## Advanced: OpenClaw Autonomous Mode

The harness can run as a fully autonomous marketing agent via OpenClaw. This enables:

- Discord-based command interface for content requests
- Scheduled heartbeats that monitor content performance
- Domain-specific agents (SEO agent, ads agent, email agent) with skill routing
- Human-in-the-loop approval gates before publishing
- Persistent memory across sessions via git-backed state

Setup requires a server, Discord bot token, and OpenClaw runtime. See `docs/OPENCLAW_SETUP.md` for the full walkthrough.

---

## Usage Pattern

```
1. Check this file's Framework Map to find the right framework for your task
2. Load the primary framework file as context
3. Load the skill contract from harness/skill-contracts/
4. Create a brief using harness/brief-schema.md
5. Write the content applying framework rules
6. Run quality gate scripts to validate
7. Fix failures and re-run (max 2 retries)
8. Ship it
```
