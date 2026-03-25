---
name: kai-marketing
description: Marketing team as slash commands. 35-rule quality gate with taste scoring, Remotion video ad rendering, A/B test tracking with statistical significance, brand system, competitive monitoring, 40 playbooks, 153 knowledge files. Full marketing ops from brief to publish.
---

# kai-marketing

A marketing team as slash commands. 16 skills, 35 quality rules (including taste enforcement), Remotion video ad rendering, A/B testing with real statistical significance, and a self-improvement loop that makes content better over time.

## The Marketing Sprint

```
/content-brief → /content-write → /content-gate → /content-report → /content-retro
                                                                          │
                                              loop closes ←───────────────┘
```

Each skill reads what the previous one wrote. The system learns from its output.

## Skills — 16 Slash Commands

### Content Sprint

| Skill | Your Specialist | What They Do |
|-------|----------------|--------------|
| `/content-brief` | **CMO** | Generate 18-field brief from (format, site, keyword). Auto-resolves persona, pulls GSC data. |
| `/content-write` | **Content Director** | Write using brief + framework + persona + learned patterns. Auto-runs quality gate. |
| `/content-gate` | **Quality Assurance** | Score against **35 rules in 5 categories** including taste. Auto-retry (max 2). |
| `/content-report` | **Analytics Lead** | Pull GSC + GA4 performance. Grade: winner / average / underperformer. |
| `/content-retro` | **CMO (Feedback)** | Extract winner patterns (n>=5, 15%+ lift). Auto-update learned defaults. |

### Advertising & Creative

| Skill | Your Specialist | What They Do |
|-------|----------------|--------------|
| `/ad-copy` | **Ad Manager** | Platform-compliant copy for 9 platforms. TOS loaded. Char counts + preview. |
| `/ad-research` | **Competitive Intel** | Scrape Meta Ad Library, Google Transparency, TikTok Creative Center. |
| `/creative-brief` | **Creative Director** | Visual concepts, copy variants, video scripts, A/B test matrices. |
| `/ad-render` | **Video Producer** | Scaffold Remotion project → render MP4 in vertical/square/landscape. 4 archetypes. |

### Channels & Operations

| Skill | Your Specialist | What They Do |
|-------|----------------|--------------|
| `/email-sequence` | **Email Marketer** | Nurture flows with lifecycle + perception engineering. CAN-SPAM compliant. |
| `/seo-audit` | **SEO Strategist** | 17-point technical audit + algorithmic authorship. Uses /browse if available. |
| `/content-ideas` | **Research Lead** | GSC keyword gaps × persona matching. Topics ranked by opportunity score. |
| `/checklist` | **QA Gatekeeper** | 23+ checklists indexed by task type — content, SEO, ads, email, PR, launches. |
| `/marketing-sprint` | **Full Pipeline** | Brief → write → gate → log in one command. The marketing `/ship`. |
| `/kai-upgrade` | **Self-Updater** | Pull latest, re-register skills, show changelog. |

## Quality Gate — 35 Rules, 5 Categories

| Category | Rules | What It Checks |
|----------|:-----:|---------------|
| **Algorithmic Authorship** | 15 | Clause positioning, verb-first, sentence length, entity naming |
| **Content Structure** | 9 | Hooks, headings, paragraphs, active voice, AI cliché detection |
| **Taste** | 6 | Specificity, emotional resonance, originality, hook strength, CTA, proof density |
| **GEO/AEO Signals** | 4 | Citations, quotations, statistics, technical terms |
| **Four U's** | 1 | Unique, Useful, Ultra-specific, Urgent (LLM-scored) |

**Taste rules** (the edge): TS-01 catches vague claims. TS-02 catches flat, clinical language. TS-03 catches AI-generated clichés. TS-04 catches weak openings. TS-05 catches missing CTAs. TS-06 catches claims without proof.

## Operational Tools (Real Code)

| Tool | Command |
|------|---------|
| **A/B Test Tracker** (statistical significance) | `kai-ab create/record/analyze` |
| **Scheduled Analytics** (weekly GSC/GA4/Meta pull) | `python -m scripts.analytics.scheduled_pull --all` |
| **Policy Freshness** (10 platform TOS staleness check) | `python -m scripts.ads.policy_freshness check` |
| **Competitive Monitor** (website change detection) | `python -m scripts.analytics.competitive_monitor check --all` |
| **Performance Dashboard** (trends + degradation alerts) | `python -m scripts.analytics.performance_dashboard weekly` |
| **Remotion Video Ads** (scaffold + render) | `kai-render scaffold --archetype problem-agitation` |
| **Brand System** (design tokens in config) | `kai-config set brand.colors.primary "#6366f1"` |

## Knowledge Base — 153 Files

- **40 playbooks** — ads, CRO, pricing, retention, growth loops, ABM, demand gen, launches, budgeting, and more
- **24 frameworks** — algorithmic authorship, AEO, perception engineering, 50 copywriting formulas, loop mechanics
- **23 checklists** — content, SEO, Google Ads, LinkedIn Ads, CRO, website launch, social audit, creative production
- **16 channel guides** — blog, LinkedIn, email, TikTok, Meta, YouTube, Instagram, X, affiliate, community, newsletter, podcast
- **12 ad policies** — Google, Meta, TikTok, LinkedIn, Microsoft, Pinterest, Snapchat, Amazon, X + FTC/GDPR
- **8 personas** — with pain points, hooks, and voice profiles

## Quick Start

```bash
/content-brief blog mysite "target keyword"     # Generate strategic brief
/content-write                                   # Write + auto-gate
/content-gate                                    # Detailed 35-rule scorecard
/ad-copy meta mysite "free trial"                # Platform-compliant ad copy
/ad-render problem-agitation                     # Scaffold Remotion video ad
/marketing-sprint blog mysite "target keyword"   # Full pipeline, one command
/checklist launch meta ads                       # Right checklist for any task
```

## Self-Improvement Loop

The system learns from its own output:
1. Content published → logged with metadata
2. 30 days later → GSC + GA4 performance pulled automatically
3. Weekly → winner patterns extracted (hook types, formats, personas that work)
4. Patterns above threshold (n>=5, 15%+ lift) → promoted to learned defaults
5. Next content run reads updated defaults → quality improves over time

## Install

```bash
git clone https://github.com/cgallic/kai-marketing.git ~/.claude/skills/kai-marketing
cd ~/.claude/skills/kai-marketing && ./setup
```

Then add to your project's CLAUDE.md:
```
## kai-marketing
Available skills: /content-brief, /content-write, /content-gate, /content-report,
/content-retro, /ad-copy, /ad-research, /creative-brief, /ad-render, /email-sequence,
/seo-audit, /content-ideas, /checklist, /marketing-sprint, /kai-upgrade
```
