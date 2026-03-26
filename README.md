# Kai CMO Harness

A marketing team as slash commands. 31 skills, 41 playbooks, 24 checklists, 27 frameworks, 17 channels, 8 personas, 12 ad platform policies — all wired into Claude Code with auto-discovery and quality gates.

Drop it into any project. Type `/kai-email-system`. It reads your codebase, builds a `marketing.md` product bible with full ICP and personas, then batch-produces every lifecycle email your product needs — scored, gated, Loops-ready.

## How It Works

```
First run in any project:
  /kai-anything → auto-explores codebase → creates marketing.md → does the work

Every subsequent run:
  /kai-anything → reads marketing.md → skips questions → does the work
```

**marketing.md** is your product marketing bible. Created once by auto-exploration, read by all 31 skills. Contains: product details, full ICP profiles (primary + secondary + anti-ICP), custom personas with language patterns and objections, brand voice, competitive landscape, business stage, current channels, and metrics.

## Install (30 seconds)

### Claude Code (recommended)

Copy the `harness/skills/` directories into `~/.claude/skills/`:

```bash
git clone https://github.com/cgallic/kai-cmo-harness.git
cp -r kai-cmo-harness/harness/skills/kai* ~/.claude/skills/
```

That's it. Type `/kai` to see all 31 commands.

### Manual (use from any project)

Clone the repo anywhere. Skills reference the knowledge base by absolute path — update the paths in each SKILL.md if your clone location differs from `E:\Dev2\kai-cmo-harness-work`.

## 31 Slash Commands

### PRODUCE — Make Stuff

| Command | What It Does |
|---------|-------------|
| `/kai-write` | Write one piece of content (blog, email, LinkedIn, ad, press release, TikTok script) |
| `/kai-landing-page` | Complete landing page with perception engineering + CRO |
| `/kai-email-system` | All lifecycle + transactional emails for a product (Loops-ready) |
| `/kai-ad-campaign` | Full paid campaign across 9 platforms + funnel stages (TOF/MOF/BOF) |
| `/kai-content-calendar` | Month/quarter of blog + SEO content with briefs |
| `/kai-social` | Batch social posts across IG, X, TikTok, LinkedIn, YouTube |
| `/kai-video` | Video scripts + clipping plans for short-form and long-form |
| `/kai-cold-outreach` | 3-touch cold email sequences with CAN-SPAM compliance |
| `/kai-newsletter` | Newsletter editions — content selection, subject lines, scheduling |
| `/kai-case-study` | Customer case studies (Problem → Solution → Results) |
| `/kai-repurpose` | 1 pillar → 15-25 assets across all channels |
| `/kai-launch` | Full product launch package — orchestrates everything above |
| `/kai-retarget` | Retargeting/remarketing campaign architecture |
| `/kai-influencer` | Influencer/creator marketing campaigns |
| `/kai-webinar` | Webinar/event marketing + follow-up sequences |
| `/kai-podcast` | Podcast launch or guest strategy |
| `/kai-abm` | Account-based marketing for enterprise targets |
| `/kai-partnership` | Co-marketing / partnership campaigns |

### AUDIT — Check Stuff

| Command | What It Does |
|---------|-------------|
| `/kai-gate` | Quality gate — Four U's score, banned words, AI slop, SEO lint |
| `/kai-audit` | Full marketing audit — runs all 24 checklists at once |
| `/kai-seo-audit` | Technical SEO audit with prioritized fix list |
| `/kai-cro` | Conversion rate audit — 5-layer optimization stack |

### PLAN — Think Stuff

| Command | What It Does |
|---------|-------------|
| `/kai-brief` | Structured content brief with persona and angle selection |
| `/kai-growth-plan` | "I'm at $X MRR — what do I do?" Stage-appropriate marketing plan |
| `/kai-brand` | Brand positioning workshop — messaging, voice, differentiation |
| `/kai-budget` | Marketing budget planning + channel allocation |
| `/kai-retention` | Customer retention system design |

### ANALYZE — Research Stuff

| Command | What It Does |
|---------|-------------|
| `/kai-competitors` | 5-layer competitive teardown + sales battlecards |
| `/kai-surround-sound` | Get your brand into ChatGPT/Perplexity/Claude answers |
| `/kai-analytics` | Analytics + attribution setup guide |

### ROUTER

| Command | What It Does |
|---------|-------------|
| `/kai` | Shows all skills organized by business stage and workflow |

## By Business Stage

**Pre-Launch ($0):**
`/kai-growth-plan` → `/kai-landing-page` → `/kai-cold-outreach` → `/kai-brand`

**Launch ($0–$10K MRR):**
`/kai-launch` → `/kai-email-system` → `/kai-ad-campaign` → `/kai-social`

**Growth ($10K–$100K MRR):**
`/kai-content-calendar` → `/kai-seo-audit` → `/kai-surround-sound` → `/kai-video` → `/kai-newsletter`

**Scale ($100K+ MRR):**
`/kai-audit` → `/kai-abm` → `/kai-competitors` → `/kai-retention` → `/kai-budget`

## Quality Gates

Every piece of content passes automated quality checks before shipping:

### Four U's Score (min 12/16 for content, 10/16 for ads/email)

| U | Question |
|---|----------|
| **Unique** | Can only WE write this? |
| **Useful** | Can the reader take action immediately? |
| **Ultra-specific** | Numbers, named tools, concrete examples? |
| **Urgent** | Reason to engage today? |

### Instant Rejection

**Banned words:** leverage, utilize, synergy, innovative, deep dive, circle back, touch base, moving forward, at the end of the day

**AI slop:** "In conclusion", "It's important to note", "In today's rapidly evolving", "This comprehensive guide", "Without further ado", "It's worth noting that"

### SEO Content (additional)

Algorithmic Authorship rules: conditions after main clause, verb-first instructions, sentences under 20 words, bold the answer not the query.

### Ad Compliance

Every ad loads the platform's TOS before writing. 10 platform policies (Google, Meta, TikTok, LinkedIn, Microsoft, Pinterest, Snapchat, Amazon, X) + FTC/GDPR/CAN-SPAM/COPPA compliance.

## Knowledge Base

| Category | Count | Highlights |
|----------|:-----:|-----------|
| **Playbooks** | 41 | Ad creative, CRO, pricing, growth loops, brand positioning, retention, demand gen, ABM, partnerships, launches, budgeting, competitive intel, content repurposing, surround sound/LLM manipulation, and more |
| **Frameworks** | 27 | Algorithmic authorship, AEO/AI search (12 files including patent analysis + Perplexity reverse-engineering), perception engineering, headline formulas, copywriting formulas, loop mechanics, Meta advertising (4 deep dives) |
| **Checklists** | 24 | Content, SEO, technical SEO, Meta ads, Google ads, LinkedIn ads, TikTok, email, PR, landing page, CRO, website launch, social media audit, creative production, ad launch |
| **Channel Guides** | 17 | Blog, LinkedIn, Email, Press, TikTok, TikTok Shop, Meta, Paid, SEO, Podcast, YouTube, Instagram, X/Twitter, Affiliate, Community, Newsletter |
| **Personas** | 8 | Competent Cog, Shock Absorber, Ghosted Applicant, Subscription Serf, System Manager, Admin Martyr, Obsolescence Anxious, Credibility Fighter |
| **Ad Policies** | 12 | Google, Meta, TikTok, LinkedIn, Microsoft, Pinterest, Snapchat, Amazon, X + FTC/GDPR/CAN-SPAM/COPPA (7,600+ lines) |
| **Skill Contracts** | 7 | Blog post, email, email lifecycle, cold email, Meta ads, Google ads, LinkedIn article |

## marketing.md — The Product Bible

When any `/kai-*` skill runs for the first time in a project, it:

1. **Auto-explores** — reads CLAUDE.md, README, package.json, routes, schemas, landing pages, existing marketing
2. **Creates marketing.md** with:
   - Product details + value prop + activation moment
   - **Full ICP profiles** — primary, secondary, anti-ICP with trigger events, pain severity, current solutions
   - **Custom personas** — mapped to harness archetypes with language patterns, objections, decision triggers, trusted channels
   - User segments
   - Business model + stage + pricing
   - Brand voice with examples
   - Competitive landscape
   - Current channels + metrics
3. **Presents for confirmation** — you review, tweak, save

Every subsequent skill reads `marketing.md` and gets straight to work. No more answering the same discovery questions across 31 skills.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE BASE (153 files)                      │
│  41 playbooks · 27 frameworks · 24 checklists · 17 channels      │
│  8 personas · 12 ad policies · 7 skill contracts                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │ loaded per task type
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SKILL LAYER (31 slash commands)                 │
│                                                                    │
│  PRODUCE: write, landing-page, email-system, ad-campaign,         │
│           content-calendar, social, video, cold-outreach,         │
│           newsletter, case-study, repurpose, launch, retarget,    │
│           influencer, webinar, podcast, abm, partnership          │
│                                                                    │
│  AUDIT:   gate, audit, seo-audit, cro                             │
│  PLAN:    brief, growth-plan, brand, budget, retention            │
│  ANALYZE: competitors, surround-sound, analytics                  │
│  ROUTER:  kai                                                      │
└─────────────────────────┬────────────────────────────────────────┘
                          │ reads on first run
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│               marketing.md (per-project product bible)            │
│  Product · ICP · Personas · Brand Voice · Competitive · Metrics   │
└──────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
kai-cmo-harness/
├── CLAUDE.md                    # Entry point — Claude Code reads this
├── README.md                    # This file
│
├── knowledge/                   # Marketing intelligence (153 files)
│   ├── _index.md                # Framework lookup table
│   ├── frameworks/              # 27 frameworks (SEO, copywriting, AEO, ads)
│   ├── channels/                # 17 channel guides
│   ├── checklists/              # 24 validation checklists
│   ├── personas/                # 8 audience personas
│   ├── playbooks/               # 41 strategic playbooks
│   └── design/                  # UI/UX design patterns
│
├── harness/                     # Pipeline config
│   ├── skill-contracts/         # 7 per-format YAML contracts
│   ├── references/              # 12 ad platform policies (7,600+ lines)
│   └── skills/                  # 31 slash command skills
│       ├── kai/                 # Router — shows all skills
│       ├── kai-write/           # Write one piece
│       ├── kai-email-system/    # All emails for a product
│       ├── kai-ad-campaign/     # Full ad campaign
│       ├── kai-landing-page/    # Landing page copy
│       ├── kai-surround-sound/  # LLM brand manipulation
│       └── ... (26 more)
│
├── scripts/                     # Quality gate engine
│   └── quality_gates/           # Four U's scorer, banned words, SEO lint
│
├── workspace/                   # Output directory for generated content
├── agent/                       # OpenClaw autonomous agent (optional)
├── gateway/                     # FastAPI webhook gateway (optional)
└── docs/                        # Extended documentation
```

## License

MIT
