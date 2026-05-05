---
name: kai
description: Kai CMO Harness router — shows all 33 marketing skills organized by workflow, business stage, and frequency. Use when "kai help", "what marketing skills are available", "how do I use the harness", "marketing help", or any general marketing question where the right skill isn't obvious.
---

# Kai CMO Harness — 33 Marketing Skills

**First time?** Run `/kai-start` — it reads your codebase, creates MARKETING.md, and recommends your first command.

## Data Rule

Any Kai workflow that uses review counts, ratings, rankings, traffic, conversions, calls, backlinks, Core Web Vitals, schema findings, local pack claims, ad metrics, or other quantitative client-facing claims must run the shared source-backed collector first:

```bash
python -m kai.source_data.collect --url "<url>" --workflow "<workflow>" --out "workspace/<workflow>-data"
```

Use `--third-party-sources all` or a comma list such as `serpapi,similarweb,builtwith,wappalyzer,yelp,meta-ads` when licensed vendor data is needed. Third-party API data is labeled `third_party_estimate`; user exports are labeled `user_provided`.

Use `kai-data.json` for general Kai workflows. Audit/deck workflows also get the identical `audit-data.json` alias. `python -m scripts.audit.collect` remains supported for existing audit automations. Missing credentials are data gaps, never estimates.

## PRODUCE (make stuff)

| Skill | What It Does |
|-------|-------------|
| `/kai-write` | Write one piece of content (any format) |
| `/kai-landing-page` | Complete landing page with perception engineering |
| `/kai-email-system` | All lifecycle + transactional emails (Loops-ready) |
| `/kai-ad-campaign` | Full paid campaign across platforms + funnel stages |
| `/kai-content-calendar` | Month/quarter of blog + SEO content |
| `/kai-social` | Batch social posts across IG, X, TikTok, LinkedIn, YouTube |
| `/kai-video` | Video scripts + clipping plans for short/long-form |
| `/kai-cold-outreach` | Cold email outreach sequences |
| `/kai-reddit-listen` | Monitor subreddits + draft replies to Discord (profile-driven) |
| `/kai-newsletter` | Newsletter editions — content, subject lines, scheduling |
| `/kai-case-study` | Customer case studies from interview/data |
| `/kai-product-maker` | Ship a Gumroad-ready digital product — ebook, card deck, flipbook |
| `/kai-repurpose` | 1 pillar → 15-25 assets across all channels |
| `/kai-launch` | Full product launch (orchestrates everything above) |
| `/kai-retarget` | Retargeting/remarketing campaigns |
| `/kai-influencer` | Influencer/creator marketing campaigns |
| `/kai-webinar` | Webinar/event marketing + follow-up |
| `/kai-podcast` | Podcast launch or guest strategy |
| `/kai-abm` | Account-based marketing for enterprise |
| `/kai-partnership` | Co-marketing / partnership campaigns |

## AUDIT (check stuff)

| Skill | What It Does |
|-------|-------------|
| `/kai-gate` | Quality gate — Four U's, banned words, SEO lint |
| `/kai-audit` | Full marketing audit — all checklists at once |
| `/kai-seo-audit` | Technical SEO audit with prioritized fixes |
| `/kai-cro` | Conversion rate audit — 5-layer optimization stack |

## PLAN (think stuff)

| Skill | What It Does |
|-------|-------------|
| `/kai-brief` | Create a content brief before writing |
| `/kai-growth-plan` | Stage-appropriate marketing plan ($0 → $100K+ MRR) |
| `/kai-brand` | Brand positioning + messaging framework |
| `/kai-budget` | Marketing budget planning + forecasting |
| `/kai-retention` | Customer retention system design |

## ANALYZE (research stuff)

| Skill | What It Does |
|-------|-------------|
| `/kai-competitors` | Competitive teardown + sales battlecards |
| `/kai-surround-sound` | LLM brand manipulation — get into AI answers |
| `/kai-analytics` | Analytics + attribution setup |

## By Business Stage

### Pre-Launch ($0)
`/kai-growth-plan` → `/kai-landing-page` → `/kai-cold-outreach` → `/kai-reddit-listen` → `/kai-brand`

### Launch ($0-$10K MRR)
`/kai-launch` → `/kai-email-system` → `/kai-ad-campaign` → `/kai-social`

### Growth ($10K-$100K MRR)
`/kai-content-calendar` → `/kai-seo-audit` → `/kai-surround-sound` → `/kai-video` → `/kai-newsletter` → `/kai-influencer`

### Scale ($100K+ MRR)
`/kai-audit` → `/kai-abm` → `/kai-competitors` → `/kai-retention` → `/kai-budget` → `/kai-partnership`

## When In Doubt

- **"I need one thing"** → `/kai-write`
- **"I need a system"** → orchestrator skill (email-system, ad-campaign, content-calendar, launch)
- **"What's wrong?"** → `/kai-audit` or `/kai-cro`
- **"What should I do?"** → `/kai-growth-plan`
- **"Multiply what I have"** → `/kai-repurpose`
- **"Get into AI answers"** → `/kai-surround-sound`
