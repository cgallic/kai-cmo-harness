# kai-marketing

A marketing team as slash commands. 16 skills, 40 playbooks, 35 quality rules, 153 knowledge files, and ~40,000 lines of Python — all wired together with a self-improvement loop that makes content better over time.

Drop it into Claude Code and type `/marketing-sprint blog mysite "target keyword"`. Three minutes later: a scored, gated, publish-ready blog post.

## What makes this different

This is not a prompt library. It's an **operational marketing system** with real code behind it:

| Layer | What | Lines of Code |
|-------|------|:-------------|
| **Quality Gate Engine** | 35 rules across 5 categories, SQLite audit trail, YAML policies, retry loop | 1,700 |
| **Content Engine** | Brief → write → gate → approve → log, surgical revision on failure | 4,000 |
| **Taste Scoring** | Specificity density, emotional resonance, originality, hook strength, CTA clarity, proof density | 600 |
| **Analytics** | GSC, GA4, Meta Ads, Stripe + scheduled weekly pulls + competitive monitor + degradation alerts | 7,400 |
| **Self-Improvement** | Performance check → pattern extract → defaults update. System learns from its own output | 2,700 |
| **A/B Test Tracker** | SQLite-backed variant tracking with statistical significance (z-test) + sample size estimation | 400 |
| **Ad Policy Freshness** | Tracks 10 platform policies, detects staleness, links to source URLs | 300 |
| **Competitive Monitor** | Fetches competitor pages, detects changes, stores diffs over time | 400 |
| **Brand System** | Design token extraction from tailwind/CSS/config → Remotion brand.ts generation | 300 |
| **Remotion Pipeline** | Scene builder + project scaffolding → rendered MP4 video ads in 4 formats | 500 |
| **Component Library** | 10 reusable modules: scoring, creative, research | 600 |
| **Agent/Scheduler** | Cron parser, 9 task types, heartbeat protocol | 1,700 |
| **Gateway** | FastAPI with 11 routers | 2,800 |

**Total: ~40,000 lines of Python + 153 knowledge files + 16 skills + 6 CLI tools**

## Install (30 seconds)

### As a Claude Code skill (recommended)

Paste this into Claude Code:

> Install kai-marketing: run `git clone https://github.com/cgallic/kai-marketing.git ~/.claude/skills/kai-marketing && cd ~/.claude/skills/kai-marketing && ./setup` then add a kai-marketing section to CLAUDE.md listing the available skills.

### Manual

```bash
git clone https://github.com/cgallic/kai-marketing.git
cd kai-marketing && ./setup
```

Requirements: Git, Python 3.10+, shell. Node.js optional (for Remotion video rendering).

## Skills — 16 Slash Commands

### The Content Sprint

```
/content-brief → /content-write → /content-gate → /content-report → /content-retro
                                                                          │
                                              loop closes ←───────────────┘
```

| Skill | Role | What It Does |
|-------|------|-------------|
| `/content-brief` | CMO | Generate 18-field brief from (format, site, keyword). Auto-resolves persona, pulls GSC data. |
| `/content-write` | Content Director | Write using brief + framework + persona + learned patterns. Auto-runs quality gate. |
| `/content-gate` | Quality Assurance | Score against 35 rules in 5 categories. Auto-retry (max 2). Detailed scorecard. |
| `/content-report` | Analytics Lead | Pull GSC + GA4 performance. Grade each piece: winner / average / underperformer. |
| `/content-retro` | CMO Feedback | Extract winner patterns (n>=5, 15%+ lift). Auto-update defaults for next run. |

### Advertising & Creative

| Skill | Role | What It Does |
|-------|------|-------------|
| `/ad-copy` | Ad Manager | Platform-compliant copy for 9 platforms. TOS loaded automatically. Char counts + preview. |
| `/ad-research` | Competitive Intel | Scrape Meta Ad Library, Google Transparency, TikTok Creative Center. Analyze patterns. |
| `/creative-brief` | Creative Director | Visual concepts, copy variants, video scripts, A/B test matrices. Platform-aware specs. |
| `/ad-render` | Video Producer | Scaffold Remotion project from brand tokens. Render MP4 in vertical/square/landscape. |

### Channels & Operations

| Skill | Role | What It Does |
|-------|------|-------------|
| `/email-sequence` | Email Marketer | Nurture flows with lifecycle marketing + perception engineering. CAN-SPAM compliant. |
| `/seo-audit` | SEO Strategist | 17-point technical audit + algorithmic authorship rules. Uses /browse if available. |
| `/content-ideas` | Research Lead | GSC keyword gaps × persona matching. Topics ranked by opportunity score. |
| `/checklist` | QA Gatekeeper | Surface the right checklist for any task. 23+ checklists indexed by type. |
| `/marketing-sprint` | Full Pipeline | Brief → write → gate → log in one command. The marketing `/ship`. |
| `/kai-upgrade` | Self-Updater | Pull latest, re-register skills, show changelog. Never touches content state. |

## Quality Gate — 35 Rules, 5 Categories

Every piece of content scores against 35 automated rules before shipping:

| Category | Rules | What It Checks |
|----------|:-----:|---------------|
| **Algorithmic Authorship** | 15 | Clause positioning, verb-first instructions, sentence length, entity naming, list consistency |
| **Content Structure** | 9 | Hook presence, heading frequency, paragraph length, active voice, reading level, AI cliché detection |
| **Taste** | 6 | **Specificity density, emotional resonance, originality, hook strength, CTA clarity, proof density** |
| **GEO/AEO Signals** | 4 | Citation density, quotation density, statistics, technical terms |
| **Four U's** | 1 | Unique, Useful, Ultra-specific, Urgent (LLM-scored) |

The **Taste** category is what separates this from every other content tool. It doesn't just check structure — it checks whether content is actually *good*:

- **TS-01 Specificity:** Are claims backed by numbers, names, examples? Or vague adjectives?
- **TS-02 Emotional Resonance:** Does it trigger pain/aspiration/urgency? Or read like a textbook?
- **TS-03 Originality:** Are sentences unique to your brand? Or could any competitor publish them?
- **TS-04 Hook Strength:** Does the first sentence grab attention? Or start with "In today's rapidly evolving..."?
- **TS-05 CTA Clarity:** Does it end with a specific action? Or fade out with "learn more"?
- **TS-06 Proof Density:** Named proof points per 500 words. Claims without proof = trust erosion.

## CLI Tools — 6 Shell Commands

```bash
kai-gate score article.md --no-llm          # Score content against 35 rules
kai-brief --format blog --site x --keyword y # Generate brief from 3 inputs
kai-report --all --format json               # Pull performance data
kai-config get brand.colors.primary          # Read brand config
kai-ab analyze ab-1234abcd                   # A/B test significance analysis
kai-render scaffold --archetype problem-agitation  # Scaffold Remotion video ad project
```

## A/B Test Tracker

Real statistical significance testing, not a playbook:

```bash
kai-ab create "headline-test" --variants "pain-hook,data-hook,social-hook" --metric cvr
kai-ab record ab-1234 --variant pain-hook --impressions 1200 --clicks 54 --conversions 8
kai-ab analyze ab-1234

# Output:
# A/B TEST: headline-test (ab-1234)
# Metric: CVR  |  Status: RUNNING
#
# Variant               Impressions     Clicks      CTR     Conv      CVR
# data-hook                   1,200         78    6.50%       15   19.23%
# pain-hook                   1,200         54    4.50%        8   14.81%
# social-hook                 1,200         42    3.50%        5   11.90%
#
# Confidence: 74.5%  |  Significant: NO
# Recommendation: Need ~1157 impressions per variant. Keep running.
```

## Brand System

Configure once, flows everywhere — to ad copy, Remotion video rendering, content writing, and voice matching:

```bash
kai-config set brand.name "KaiCalls"
kai-config set brand.colors.primary "#6366f1"
kai-config set brand.tagline "AI receptionist that never sleeps"
kai-config get brand.colors.primary   # → #6366f1
```

Extracts design tokens from tailwind.config, CSS variables, and package.json. Generates Remotion `brand.ts` automatically.

## Remotion Video Ad Pipeline

```bash
kai-render scaffold --archetype problem-agitation --format vertical
# Generates complete Remotion project:
#   src/config/brand.ts    — Your brand colors/fonts
#   src/config/scenes.json — Scene-by-scene composition
#   src/templates/         — Remotion React components
#   package.json           — npm run build:all → MP4

cd ~/.kai-marketing/renders/20260325 && npm install && npm run build:all
# → out/vertical.mp4 (1080x1920, Reels/Stories/TikTok)
# → out/square.mp4   (1080x1080, Feed)
# → out/landscape.mp4 (1920x1080, YouTube)
```

4 archetypes: **Problem-Agitation** (cold), **Social Proof** (warm), **Product Demo** (retargeting), **Lifestyle** (brand).

## Knowledge Base — 153 Files

| Category | Count | Highlights |
|----------|:-----:|-----------|
| **Playbooks** | 40 | Ad creative, campaign management, CRO, pricing, customer journey, growth loops, brand positioning, retention, demand gen, ABM, partnerships, launches, budgeting, link building, tracking/GTM, content repurposing, podcast, newsletter, social media, video, influencer, PR, competitive intel, SaaS metrics, e-commerce, marketing by stage, automation, retargeting, internal linking |
| **Frameworks** | 24 | Algorithmic authorship, AEO/AI search (12 files), perception engineering, headline formulas, copywriting formulas (50 formulas), loop mechanics, Meta advertising (4 deep dives) |
| **Checklists** | 23 | Content, SEO, technical SEO, Meta ads, Google ads, LinkedIn ads, paid acquisition, TikTok, email, PR, landing page, CRO, website launch, social media audit, creative production, ad launch |
| **Channel Guides** | 16 | Blog, LinkedIn, Email, Press, TikTok, TikTok Shop, Meta, Paid, SEO, Podcast, YouTube, Instagram, X/Twitter, Affiliate, Community, Newsletter |
| **Personas** | 8 | Competent Cog, Shock Absorber, Ghosted Applicant, Subscription Serf, System Manager, Admin Martyr, Obsolescence Anxious, Credibility Fighter |
| **Ad Policies** | 12 | Google, Meta, TikTok, LinkedIn, Microsoft, Pinterest, Snapchat, Amazon, X + FTC/GDPR/CAN-SPAM/COPPA |

## Operational Tools (Real Code, Not Playbooks)

| Tool | What It Does | Command |
|------|-------------|---------|
| **Scheduled Analytics Pull** | Weekly GSC + GA4 + Meta Ads data snapshots | `python -m scripts.analytics.scheduled_pull --all` |
| **Policy Freshness Checker** | Detects stale ad platform policies, links to update sources | `python -m scripts.ads.policy_freshness check` |
| **Competitive Monitor** | Tracks competitor website changes, pricing shifts, content updates | `python -m scripts.analytics.competitive_monitor check --all` |
| **Performance Dashboard** | Weekly summary, 12-week trends, ranking degradation alerts | `python -m scripts.analytics.performance_dashboard weekly` |
| **A/B Test Tracker** | Statistical significance with z-test, sample size estimation | `kai-ab analyze <test-id>` |

## Component Library

Reusable Python modules in `lib/components/`:

| Module | What It Does |
|--------|-------------|
| `creative/brand_tokens.py` | Extract design tokens from tailwind/CSS/config, generate Remotion brand.ts |
| `creative/format_specs.py` | Platform char limits, image dimensions, video durations for all 12 placements |
| `creative/scene_builder.py` | Convert brief + copy into Remotion scene compositions (4 archetypes) |
| `creative/copy_variants.py` | Generate N variants of any copy block for A/B testing |
| `scoring/specificity.py` | Count specific vs vague claims in text (reusable outside quality gate) |
| `research/keyword_scorer.py` | Score keyword opportunity (0-100) from position, impressions, CTR gap |

## Self-Improvement Loop

```
Day 0:   Write → gate → publish → log
Day 30:  performance_check.py pulls GSC + GA4, grades each piece
Weekly:  pattern_extract.py identifies winners (n>=5, 15%+ lift)
Weekly:  harness_defaults_update.py writes patterns into MARKETING.md
Day 31+: Next content run reads updated defaults → quality improves
```

The system gets better the more you use it. No manual tuning required.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      KNOWLEDGE BASE (153 files)                  │
│  frameworks/  channels/  checklists/  personas/  playbooks/      │
│  40 playbooks, 24 frameworks, 23 checklists, 16 channels        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ loaded per task type
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SKILL LAYER (16 slash commands)                │
│  content-brief → content-write → content-gate → content-report  │
│  ad-copy, ad-research, ad-render, creative-brief, email-seq     │
│  seo-audit, content-ideas, checklist, marketing-sprint          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ calls via bin/ CLI tools
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ENGINE LAYER (~40,000 lines Python)            │
│  Quality Gate (35 rules)  │  Content Engine  │  Analytics        │
│  A/B Tracker              │  Self-Improvement │  Competitive Mon  │
│  Brand Tokens             │  Scene Builder    │  Policy Freshness │
│  Component Library        │  Gateway (11 API routes)             │
└──────────────────────────┬──────────────────────────────────────┘
                           │ persistent state
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STATE (~/.kai-marketing/)                      │
│  config.yaml  │  briefs/  │  drafts/  │  gates/  │  reports/    │
│  content-log.jsonl  │  ab_tests.db  │  competitive/  │  renders/│
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
kai-marketing/
├── SKILL.md                    # Root skill: system overview + index
├── VERSION                     # 0.1.0
├── CHANGELOG.md
├── setup                       # One-command installer
├── bin/                        # 6 CLI tools
│   ├── kai-gate                # Quality gate scoring
│   ├── kai-brief               # Brief generation
│   ├── kai-report              # Performance reporting
│   ├── kai-config              # Config management + brand system
│   ├── kai-ab                  # A/B test tracking
│   └── kai-render              # Remotion video ad scaffolding
│
├── content-brief/SKILL.md      # 16 skill definitions
├── content-write/SKILL.md
├── content-gate/SKILL.md
├── content-report/SKILL.md
├── content-retro/SKILL.md
├── ad-copy/SKILL.md
├── ad-research/SKILL.md
├── ad-render/SKILL.md
├── creative-brief/SKILL.md
├── email-sequence/SKILL.md
├── seo-audit/SKILL.md
├── content-ideas/SKILL.md
├── checklist/SKILL.md
├── marketing-sprint/SKILL.md
├── kai-upgrade/SKILL.md
│
├── knowledge/                  # 153 marketing knowledge files
│   ├── _index.md               # Full index with "use when" triggers
│   ├── frameworks/             # 24 frameworks (SEO, copywriting, ads, AEO)
│   ├── channels/               # 16 channel guides
│   ├── checklists/             # 23 validation checklists
│   ├── personas/               # 8 audience personas
│   ├── playbooks/              # 40 strategic playbooks
│   └── design/                 # UI/UX design patterns
│
├── harness/                    # Pipeline config
│   ├── skill-contracts/        # Per-format YAML contracts
│   └── references/             # 12 ad platform TOS policies (7,600+ lines)
│
├── scripts/                    # Python engine (~40K lines)
│   ├── quality/                # 35-rule quality scorer
│   │   └── rules/              # AA, CS, GEO, FU, VC, TS rules
│   ├── content/                # Engine, brief gen, A/B tracker, intent parser
│   ├── analytics/              # GSC, GA4, Meta, scheduled pull, competitive monitor, dashboard
│   ├── self_improvement/       # Performance check, pattern extract, defaults update
│   └── ads/                    # Meta ads, ad loop, policy freshness
│
├── lib/                        # Shared utilities
│   ├── preamble.sh             # Skill preamble
│   ├── find-python.sh          # Cross-platform Python detection
│   └── components/             # Reusable component library
│       ├── creative/           # Brand tokens, format specs, scene builder, copy variants
│       ├── scoring/            # Specificity scorer (reusable outside gate)
│       └── research/           # Keyword opportunity scorer
│
├── agent/                      # Autonomous agent loop (optional)
├── gateway/                    # FastAPI webhook gateway (optional)
├── workspace/                  # OpenClaw workspace templates
├── deploy/                     # VPS deployment
└── docs/                       # Extended documentation
```

## License

MIT
