# Kai Harness — Architecture

> A CI/CD pipeline for marketing content. Brief → Write → Gate → Approve → Log → Learn.

---

## Overview

The harness is a Python CLI (`kai_harness.py`) that orchestrates a content production pipeline. It enforces three laws:

1. **No brief, no write** — every run starts with live GSC + GA4 data
2. **No gate pass, no publish** — three blocking scripts run before any human sees the draft
3. **No publish without logging** — every piece is tracked for 30-day performance review

---

## Directory Layout

```
/opt/cmo-analytics/
├── scripts/
│   ├── kai_harness.py          # CLI orchestrator — entry point
│   ├── four_us_score.py        # Gate 1: quality scoring (LLM-graded)
│   ├── banned_word_check.py    # Gate 2: banned word enforcement
│   ├── seo_lint.py             # Gate 3: structural SEO checks
│   ├── content_log.py          # Publish logger + 30d check scheduler
│   ├── performance_check.py    # 30d GSC + GA4 pull, winner grading
│   ├── pattern_extract.py      # Winner analysis → knowledge base
│   ├── harness_defaults_update.py  # Auto-update MARKETING.md from patterns
│   └── harness_discord.py      # Discord command handler (!harness)
├── data/
│   ├── content_log.json        # All published pieces
│   └── pending_checks/         # Per-piece JSON files for 30d performance pulls
└── .env                        # GEMINI_API_KEY, GSC_*, GA4_*, etc.

/root/.openclaw/workspace/
├── MARKETING.md                # Operating config — formats, sites, thresholds, defaults
├── harness/
│   ├── ARCHITECTURE.md         # This file
│   ├── brief-schema.md         # JSON schema for content briefs
│   ├── skill-contracts/        # Per-format YAML specs
│   │   ├── blog-post.yaml
│   │   ├── linkedin-article.yaml
│   │   ├── cold-email.yaml
│   │   ├── email-lifecycle.yaml
│   │   ├── meta-ads.yaml
│   │   └── google-ads.yaml
│   └── references/
│       ├── cold-email-rules.md     # 3-touch structure, TCPA rules
│       └── google-ads-rules.md     # RSA/PMax char limits, quality score rules
└── knowledge/
    ├── frameworks/             # Algorithmic authorship, Four U's, AEO, Meta ads
    ├── channels/               # Format-specific guides (LinkedIn, TikTok, email, etc.)
    ├── personas/               # 8 audience archetypes with pain points and hooks
    ├── playbooks/
    │   └── what-works.md       # Auto-updated from winner patterns
    └── _quick-reference.md     # One-page index

/usr/local/bin/kai-harness      # Symlink → kai_harness.py
```

---

## Pipeline Flow

```
kai-harness run --task blog --site kaicalls --keyword "law firm answering service"
        │
        ▼
┌─────────────────────────────────┐
│  1. BRIEF GENERATOR             │
│  generate_brief()               │
│                                 │
│  Inputs:                        │
│  · GSC queries + opportunities  │
│  · GA4 session data             │
│  · personas/[name].md           │
│  · SITE_FACTS constants         │
│                                 │
│  Output: brief.json             │
│  {keyword, angle, persona,      │
│   hook_options[3], competitor,  │
│   proof, cta, secondary_kws,    │
│   internal_links, word_count}   │
└──────────────┬──────────────────┘
               │ brief.json
               ▼
┌─────────────────────────────────┐
│  2. CONTENT WRITER              │
│  write_content()                │
│                                 │
│  Inputs:                        │
│  · brief.json                   │
│  · FORMAT_INSTRUCTIONS[fmt]     │
│  · knowledge/frameworks/[fmt]   │
│  · knowledge/playbooks/         │
│    what-works.md (if exists)    │
│  · SITE_FACTS[site]             │
│                                 │
│  Model: Gemini 2.0 Flash        │
│  Output: draft.md               │
└──────────────┬──────────────────┘
               │ draft.md
               ▼
┌─────────────────────────────────┐
│  3. QUALITY GATE                │
│  run_gate() — max 3 attempts    │
│                                 │
│  Gate 1: four_us_score.py       │
│    Grades Unique/Useful/        │
│    Ultra-specific/Urgent 0-4    │
│    Threshold: 12/16 (long-form) │
│               10/16 (ads)       │
│    Per-dim minimum: 2/4         │
│    Model: Gemini 2.0 Flash      │
│                                 │
│  Gate 2: banned_word_check.py   │
│    Tier 1: ~50 words → BLOCK    │
│    Tier 2: flag + replacements  │
│    Tier 3: weak qualifier warn  │
│    Runtime: <2 seconds, no API  │
│                                 │
│  Gate 3: seo_lint.py            │
│    Keyword in title + 100 words │
│    H2 with secondary keyword    │
│    2+ internal links            │
│    Keyword density 1-2%         │
│    Avg sentence < 20 words      │
│    Skipped for ad formats       │
│                                 │
│  On fail: revise_draft()        │
│    Passes only failing dims     │
│    + exact banned word context  │
│    + SEO errors (not warnings)  │
│    Hard constraint: don't       │
│    shorten, don't remove data   │
└──────────────┬──────────────────┘
               │ gated draft.md
               ▼
┌─────────────────────────────────┐
│  4. DISCORD APPROVAL            │
│  post_for_approval()            │
│                                 │
│  Posts to site-specific channel │
│  Preview + gate scores          │
│  ✅ = approve · ❌ = reject     │
└──────────────┬──────────────────┘
               │ approval
               ▼
┌─────────────────────────────────┐
│  5. PUBLISH + LOG               │
│  content_log.py                 │
│                                 │
│  Appends to content_log.json:   │
│  {site, keyword, format, url,   │
│   hook_type, publish_date}      │
│                                 │
│  Creates pending_checks/        │
│  [id].json for 30d pull         │
└──────────────┬──────────────────┘
               │ 30 days later (cron)
               ▼
┌─────────────────────────────────┐
│  6. PERFORMANCE CHECK           │
│  performance_check.py           │
│                                 │
│  Pulls GSC: position, CTR       │
│  Pulls GA4: session duration    │
│                                 │
│  Winner threshold:              │
│    position ≤ 5                 │
│    CTR ≥ 5%                     │
│    avg session ≥ 90s            │
│                                 │
│  On winner → pattern_extract.py │
└──────────────┬──────────────────┘
               │ winner data
               ▼
┌─────────────────────────────────┐
│  7. PATTERN EXTRACTION          │
│  pattern_extract.py (weekly)    │
│                                 │
│  Analyzes winners for:          │
│    hook type, format, word      │
│    count, publish day, persona  │
│                                 │
│  Appends to:                    │
│    knowledge/playbooks/         │
│    what-works.md                │
│                                 │
│  Weekly: surfaces statistical   │
│  patterns (n≥5, Δ≥15% lift)    │
│                                 │
│  On threshold hit →             │
│  harness_defaults_update.py     │
│  rewrites MARKETING.md defaults │
└─────────────────────────────────┘
```

---

## File Contracts

### brief.json schema
```json
{
  "target_site":         "kaicalls",
  "target_keyword":      "law firm answering service",
  "secondary_keywords":  ["legal answering service", "..."],
  "format":              "blog",
  "persona":             "The Overwhelmed Legal Professional",
  "current_rank":        "not ranking",
  "monthly_impressions": 0,
  "current_ctr":         0.0,
  "competitor_url":      "https://...",
  "competitor_weakness": "...",
  "angle":               "...",
  "hook_options":        ["...", "...", "..."],
  "audience_pain":       "...",
  "proof_available":     "...",
  "cta":                 "...",
  "word_count_target":   1400,
  "publish_date":        "2026-03-15",
  "internal_links":      ["https://...", "https://..."]
}
```

Full schema: `harness/brief-schema.md`

### content_log.json entry
```json
{
  "id":            "kaicalls-blog-20260315",
  "site":          "kaicalls",
  "keyword":       "law firm answering service",
  "format":        "blog",
  "url":           "https://kaicalls.com/blog/...",
  "hook_type":     "curiosity_gap",
  "publish_date":  "2026-03-15",
  "four_us_score": 11,
  "performance_30d": null
}
```

### pending_checks/[id].json
```json
{
  "id":           "kaicalls-blog-20260315",
  "url":          "https://kaicalls.com/blog/...",
  "check_after":  "2026-04-14",
  "status":       "pending"
}
```

---

## Gate Thresholds

| Format | Four U's min | SEO lint | Banned words |
|--------|-------------|----------|--------------|
| blog, seo, press | 12/16 | ✅ required | ✅ required |
| linkedin | 12/16 | ✅ required | ✅ required |
| meta-ads, google-ads | 10/16 | ⏭ skipped | ✅ required |
| cold-email | 10/16 | ⏭ skipped | ✅ required |
| email-lifecycle | 10/16 | ⏭ skipped | ✅ required |
| tiktok | 10/16 | ⏭ skipped | ✅ required |

Short-form detection is heuristic: if draft contains `VARIANT A`, `Touch 1`, `Subject:`, or `HOOK (0-3s)` → ad/short-form thresholds apply.

`--threshold N` overrides the long-form default. Use `--threshold 11` for commercial SaaS posts without published case study data.

---

## Cron Schedule

| Time | Script | Purpose |
|------|--------|---------|
| `0 2 * * *` | `performance_check.py --all` | 30d performance pulls |
| `0 14 * * 1` | `pattern_extract.py --weekly --site all` | Weekly pattern aggregation |
| `30 14 * * 1` | `harness_defaults_update.py` | Update MARKETING.md defaults (fires 30min after pattern extract) |

---

## Discord Commands

Handler: `harness_discord.py`

| Command | What it does |
|---------|-------------|
| `!harness run <format> <site> <keyword>` | Full pipeline in background, pings on complete |
| `!harness brief <site> <keyword>` | Brief only, posts JSON to channel |
| `!harness gate <keyword>` | Re-gates `/tmp/harness_draft.md` |
| `!harness report <site>` | 30d performance summary |
| `!harness patterns <site>` | Winner patterns from last 90 days |
| `!harness queue` | Drafts pending approval |
| `!harness status` | System health card |
| `!harness help` | Command list |

---

## MARKETING.md

Operating config loaded by the write agent on every run. Contains:

- **Format registry** — which formats exist, default word counts, thresholds
- **Site registry** — which sites are tracked, their Discord channels, their GSC/GA4 keys
- **Three laws** — enforced, not suggested
- **Skill contracts** — path to each format's YAML spec
- **Learned defaults** — auto-updated by `harness_defaults_update.py` when n≥5 patterns reach 15%+ lift

MARKETING.md is to the write agent what CLAUDE.md is to a coding agent. Without it, the model invents defaults. With it, the model executes with institutional context.

---

## Adding a New Format

1. Add the format name to `FORMATS` in `kai_harness.py`
2. Add format instructions to `FORMAT_INSTRUCTIONS` dict in `kai_harness.py`
3. Create `harness/skill-contracts/[format].yaml`
4. Add framework path mapping to `framework_map` in `write_content()`
5. Decide threshold: long-form (12/16) or short-form (10/16)
6. Add to gate's short-form detection heuristic if needed
7. Update `MARKETING.md` format registry

## Adding a New Site

1. Add site key to `SITES` in `kai_harness.py`
2. Add Discord channel ID to `DISCORD_CHANNELS`
3. Add verified facts to `SITE_FACTS` (price, proof points, verticals)
4. Verify GSC + GA4 keys exist in `.env` for that site
5. Update `MARKETING.md` site registry

---

## What the Harness Does Not Do

- **Publish automatically** — every draft requires human approval in Discord before publish
- **Manage CMS** — publishing to WordPress/Webflow/etc. is manual after Discord approval
- **Generate images** — image generation is a separate `ocx image` tool
- **Handle social scheduling** — drafted LinkedIn/TikTok content is output as markdown; scheduling is manual
- **Train on client data** — SITE_FACTS are manually maintained; no automatic CRM pull into briefs (yet)
