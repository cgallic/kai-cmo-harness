---
name: kai-marketing
description: Marketing team as slash commands. 100+ frameworks, quality gates, self-improvement loop, ad management, creative direction, competitive intelligence. Full marketing ops from brief to publish with automated scoring.
---

# kai-marketing

A marketing team as slash commands. Drop into any Claude Code project for instant marketing intelligence with quality gates that enforce standards before anything ships.

## The Marketing Sprint

```
/content-brief → /content-write → /content-gate → /content-report → /content-retro
                                                                          │
                                              loop closes ←───────────────┘
```

Each skill reads what the previous one wrote. The system learns from its output.

## Skills — 15 Slash Commands

### Content Sprint (the core loop)

| Skill | Your Specialist | What They Do |
|-------|----------------|--------------|
| `/content-brief` | **CMO** | Generate a strategic brief from (format, site, keyword). Auto-resolves persona, pulls GSC data, generates hooks and angles. |
| `/content-write` | **Content Director** | Write the piece using the brief, framework rules, persona hooks, and learned patterns from past winners. Quality gate runs automatically. |
| `/content-gate` | **Quality Assurance** | Score any content against 28+ rules across 4 categories. Auto-retry on failure (max 2). Detailed scorecard with fix suggestions. |
| `/content-report` | **Analytics Lead** | Pull performance data for published content. GSC position + CTR, GA4 session duration. Grades: winner / average / underperformer. |
| `/content-retro` | **CMO (Feedback)** | Analyze what worked. Extract winner patterns (n>=5, 15%+ lift). Auto-update learned defaults for next run. |

### Advertising & Creative

| Skill | Your Specialist | What They Do |
|-------|----------------|--------------|
| `/ad-copy` | **Ad Manager** | Write platform-compliant ad copy. Loads TOS rules for 9 platforms (Meta, Google, TikTok, LinkedIn, Pinterest, Snapchat, Amazon, X, Microsoft). Shows char counts and format preview. |
| `/ad-research` | **Competitive Intel** | Research competitor ads via Meta Ad Library, Google Ads Transparency, TikTok Creative Center. Analyze creative patterns, hooks, offers, and longevity. |
| `/creative-brief` | **Creative Director** | Generate visual concepts, copy variants, video scripts, image specs, and structured A/B test matrices. Platform-aware with exact format specs. |

### Channel Specialists

| Skill | Your Specialist | What They Do |
|-------|----------------|--------------|
| `/email-sequence` | **Email Marketer** | Build email nurture flows using lifecycle marketing + perception engineering frameworks. CAN-SPAM compliant. |
| `/seo-audit` | **SEO Strategist** | Audit any URL against 17-point technical SEO checklist + algorithmic authorship rules. Uses /browse if available. |
| `/content-ideas` | **Research Lead** | Scrape GSC for keyword opportunities. Cross-reference with personas. Suggest topics ranked by opportunity score. |
| `/checklist` | **QA Gatekeeper** | Surface the right checklist for any marketing task. 20+ checklists indexed by task type — content, SEO, ads, email, PR, launches, creatives. |

### Pipeline & Operations

| Skill | Your Specialist | What They Do |
|-------|----------------|--------------|
| `/marketing-sprint` | **Full Pipeline** | Run the entire content chain in one command: brief → write → gate → log. Progress updates between steps. The marketing `/ship`. |
| `/kai-upgrade` | **Self-Updater** | Pull latest version, re-register skills, show changelog. Safe — never touches content state. |

## Quality Gates

Every piece of content passes automated quality gates before shipping:

- **28+ scoring rules** across Algorithmic Authorship, GEO/AEO Signals, Content Structure, Four U's, Voice Consistency
- **Banned word detection** — 50+ instant-reject words (leverage, synergy, innovative...)
- **AI slop detection** — catches "in conclusion", "it's important to note", "in today's rapidly evolving"
- **SEO linting** — keyword density, internal links, sentence length, heading structure
- **Voice consistency** — compares draft against brand voice profile
- **Platform compliance** — 9 ad network TOS policies (Meta, Google, TikTok, LinkedIn, etc.)

Minimum scores: 12/16 Four U's for long-form, 10/16 for ads/email. Max 2 auto-retries with surgical revision.

## Knowledge Base — 120+ Files

### Frameworks (30+)
- **Algorithmic Authorship** — reverse-engineered from Google AI Overviews selection patterns
- **AEO/AI Search** — Answer Engine Optimization for ChatGPT, Perplexity, Google AI Mode
- **Perception Engineering** — cognitive persuasion for sales pages and landing pages
- **Meta Advertising** — Andromeda, GEM, Lattice, Breakdown Effect deep dives
- **Headline Formulas** — proven headline patterns for any content type

### Channels (11)
- Blog, LinkedIn, Email, Press, TikTok, TikTok Shop, Meta Ads, Paid Acquisition, SEO, Podcast

### Playbooks (12+)
- Ad Creative Best Practices — copy formulas, testing framework, format specs
- Ad Campaign Management — structure, audiences, optimization cadence, scaling
- Social Media Strategy — LinkedIn, Instagram, X, TikTok, YouTube
- Video Content Creation — scripts, production, editing, repurposing
- Product Launch Playbook — pre-launch, launch day, post-launch optimization
- Influencer Marketing — tiers, briefs, contracts, ROI measurement
- PR & Communications — pitching, media lists, thought leadership, crisis comms
- Semantic SEO Methodology — topical maps, quality/trending nodes
- Local SEO/GBP Optimization — proximity, naming, multi-location
- Landing Page Messaging — 7-phase workflow
- Content Publication Velocity — briefs, velocity monitoring

### Checklists (20+)
- Content, SEO, Technical SEO, Meta Ads, Paid Acquisition, TikTok, Email, PR, Landing Page, Perception Engineering, Fintech Design, Patent Research, Business Model, 2026 Readiness, Ad Launch, Creative Production

### Personas (8)
- Competent Cog, Shock Absorber, Ghosted Applicant, Subscription Serf, System Manager, Admin Martyr, Obsolescence Anxious, Credibility Fighter

### Ad Platform Policies (12)
- Google, Meta, TikTok, LinkedIn, Microsoft/Bing, Pinterest, Snapchat, Amazon, X/Twitter
- Cross-platform: FTC, GDPR, CAN-SPAM, COPPA, CCPA, Click-to-Cancel

## Quick Start

```bash
# Generate a content brief
/content-brief blog mysite "target keyword"

# Write the content (reads the brief automatically)
/content-write

# Score it against quality gates
/content-gate

# Research competitor ads
/ad-research "CompetitorName" meta

# Generate ad creative with compliance check
/ad-copy meta mysite "free trial offer"

# Full pipeline in one command
/marketing-sprint blog mysite "target keyword"

# Find the right checklist for any task
/checklist launch meta ads
```

## Self-Improvement Loop

The system learns from its own output:
1. Content published → logged with metadata
2. 30 days later → GSC + GA4 performance pulled automatically
3. Weekly → winner patterns extracted (hook types, formats, personas that work)
4. Patterns above threshold (n>=5, 15%+ lift) → promoted to learned defaults
5. Next content run reads updated defaults → quality improves over time

No manual tuning required. The system gets better the more you use it.

## Install

```bash
git clone https://github.com/cgallic/kai-marketing.git ~/.claude/skills/kai-marketing
cd ~/.claude/skills/kai-marketing && ./setup
```

Then add to your project's CLAUDE.md:
```
## kai-marketing
Available skills: /content-brief, /content-write, /content-gate, /content-report,
/content-retro, /ad-copy, /ad-research, /creative-brief, /email-sequence,
/seo-audit, /content-ideas, /checklist, /marketing-sprint, /kai-upgrade
```
