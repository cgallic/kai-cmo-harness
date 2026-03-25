# Changelog

## v0.2.0 — 2026-03-25

### Taste, Creative Production & Component Architecture

**Taste Scoring (6 new quality rules)**
- `TS-01` Specificity density — catches vague claims without numbers/names/examples
- `TS-02` Emotional resonance — catches flat, clinical language that doesn't trigger action
- `TS-03` Originality score — catches AI clichés, buzzwords, and template language
- `TS-04` Hook strength — catches weak openings ("In today's rapidly evolving...")
- `TS-05` CTA clarity — catches missing or generic calls-to-action ("learn more")
- `TS-06` Proof density — catches claims without named evidence
- New "Taste" category at 20% weight. Total rules: 28 → 35 across 5 categories.

**Brand System**
- `kai-config get/set brand.*` — design tokens stored in config
- Brand section in `~/.kai-marketing/config.yaml` (colors, fonts, voice, assets)
- `lib/components/creative/brand_tokens.py` — extract from tailwind/CSS/package.json
- Auto-generates Remotion `brand.ts` from config

**Remotion Video Ad Pipeline**
- New skill: `/ad-render` — scaffold Remotion projects from brand config + creative brief
- New CLI: `kai-render scaffold/render/archetypes`
- `lib/components/creative/scene_builder.py` — converts brief → scene compositions
- 4 archetypes: Problem-Agitation, Social Proof, Product Demo, Lifestyle
- Renders to MP4 in vertical (9:16), square (1:1), landscape (16:9)

**Component Library (`lib/components/`)**
- `creative/brand_tokens.py` — extract + convert design tokens
- `creative/format_specs.py` — char limits, dimensions, durations for 12 platform placements
- `creative/scene_builder.py` — Remotion scene composition generator
- `creative/copy_variants.py` — generate N copy variants for A/B testing
- `scoring/specificity.py` — reusable specificity scorer
- `research/keyword_scorer.py` — keyword opportunity scoring (0-100)

### Operational Edge (Real Code)

**A/B Test Tracker**
- `kai-ab create/record/analyze/list` — SQLite-backed variant tracking
- Two-proportion z-test for statistical significance
- Sample size estimation for planning
- Winner detection at 95% confidence threshold

**Scheduled Analytics Pull**
- `scripts/analytics/scheduled_pull.py` — cron-compatible weekly GSC/GA4/Meta data pull
- Timestamped JSONL snapshots in `~/.kai-marketing/analytics/snapshots/`

**Ad Policy Freshness Checker**
- `scripts/ads/policy_freshness.py` — tracks 10 platform policy files for staleness
- Reports age, source URLs for updates, changelog links

**Competitive Monitor**
- `scripts/analytics/competitive_monitor.py` — track competitor website changes
- Pricing signal extraction, content hash diffing, archived snapshots

**Performance Dashboard**
- `scripts/analytics/performance_dashboard.py` — weekly summary, 12-week trends, degradation alerts
- Ranking drop detection, CTR decline flagging

### Knowledge Base Expansion (153 total files)

**New Playbooks (+22)**
- Ad creative best practices, Ad campaign management, Social media strategy
- Video content creation, Product launch, Influencer marketing
- PR & communications, CRO / conversion optimization, Analytics & attribution
- Retargeting & remarketing, Marketing automation, Growth loops (applied)
- Brand positioning, Pricing strategy, Customer journey mapping
- Marketing by company stage, SEO link building, Technical marketing / tracking
- Content repurposing, Competitive intelligence, SaaS metrics deep dive
- Demand generation, Account-based marketing, Partnership / co-marketing
- Customer retention, Event & webinar marketing, E-commerce marketing
- Marketing budget & forecasting, SEO internal linking, Podcast marketing

**New Channel Guides (+5)**
- YouTube, Instagram, X/Twitter, Affiliate & referral, Community building, Newsletter strategy

**New Checklists (+6)**
- Ad launch, Creative production, Website launch, Social media audit
- CRO audit, Google Ads launch, LinkedIn Ads launch

**New Frameworks (+2)**
- 50 copywriting formulas (PAS, AIDA, BAB, + 47 more)
- Loop mechanics (12 loop types, 7 thinking personas, viral diagnostics)

---

## v0.1.0 — 2026-03-24

Initial release as a skill-based marketing platform.

### Skills (11 slash commands)
- `/content-brief` — Generate strategic briefs from (format, site, keyword)
- `/content-write` — Write content using brief + framework + persona + learned patterns
- `/content-gate` — Score content against quality rules with auto-retry
- `/content-report` — Pull GSC + GA4 performance data for published content
- `/content-retro` — Extract winner patterns and auto-update learned defaults
- `/ad-copy` — Platform-compliant ad copy with TOS rules for 9 platforms
- `/email-sequence` — Email nurture flows with lifecycle + perception engineering
- `/seo-audit` — Technical SEO audit with 17-point checklist
- `/content-ideas` — Keyword gap analysis + persona matching
- `/marketing-sprint` — Full pipeline in one command
- `/kai-upgrade` — Self-updater

### Infrastructure
- `bin/` CLI tools: kai-gate, kai-brief, kai-config, kai-report
- `setup` script with multi-platform detection (Claude Code, Codex, Gemini)
- `~/.kai-marketing/` persistent state directory
- Voice consistency quality gate rule (VC-01)

### Knowledge Base
- 100+ marketing frameworks
- 17 validation checklists
- 8 audience personas
- 9 ad platform TOS policies + cross-platform compliance
- 12 AEO/AI search files
