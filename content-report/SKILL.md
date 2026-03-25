---
name: content-report
description: Pull performance data for published content. Shows GSC position + CTR, GA4 session duration. Grades each piece as winner, average, or underperformer.
---

# /content-report — The Analytics Lead

Pull performance data for your published content. Cross-references GSC (search position, CTR) with GA4 (session duration) to grade each piece.

## Preamble

```bash
source "$(dirname "$0")/../lib/preamble.sh"
```

## Arguments

Optional:
- **--site**: Filter by site key (e.g., kaicalls)
- **--all**: Show all published content (default if no args)

Example: `/content-report --site kaicalls`
Example: `/content-report`

## The Skill

### Step 1: Load Content Log

Run:
```bash
kai-report --all --format json
```

If no published content found, tell user: "No published content in the log. Content is logged automatically when it passes `/content-gate`."

### Step 2: Display Performance Overview

Present the data:

```
CONTENT PERFORMANCE REPORT
══════════════════════════════════════════

Total pieces: {N}
  Winners:         {green} {count} ({pct}%)
  Average:         {yellow} {count} ({pct}%)
  Underperformers: {red} {count} ({pct}%)
  Pending (< 30d): {gray} {count}

WINNER THRESHOLD:
  Position ≤ 5  |  CTR ≥ 5%  |  Session ≥ 90s

RECENT CONTENT:
  [+] kaicalls-blog-20260316  "AI receptionists"    pos:3  CTR:7.2%  90s+  WINNER
  [~] kaicalls-blog-20260310  "law firm answering"  pos:12 CTR:2.1%  45s   AVERAGE
  [-] abp-blog-20260308       "backyard design"     pos:28 CTR:0.4%  22s   UNDER
  [?] kaicalls-blog-20260322  "virtual receptionist" (pending — 8 days old)
```

### Step 3: Insights

If there are 3+ graded pieces, provide insights:
- Which **format** performs best (blog vs linkedin vs email)
- Which **persona** performs best
- Which **hook type** performs best (if tracked)
- Average quality gate score of winners vs underperformers

Example:
```
INSIGHTS:
  Best performing format:  blog (3/4 winners)
  Best performing persona: Shock Absorber (2/2 winners)
  Avg gate score winners:  82/100  vs  underperformers: 61/100
```

### Step 4: Recommend Next Actions

Based on the data:
- If pieces are pending 30-day review: "3 pieces ready for 30-day review. Performance data will be pulled on next check."
- If underperformers exist: "Consider revising underperformers or running `/content-retro` to extract patterns."
- If no recent content: "No content published in the last 14 days. Run `/content-ideas` for topic suggestions."

## Error Handling

- **No content log**: Direct to `/content-write` to publish first piece
- **GSC/GA4 API unavailable**: Show content log without performance grades, note "Performance data unavailable — showing log only"

## Chain State

**Reads from:** `~/.kai-marketing/content-log.jsonl`
**Feeds into:** `/content-retro` (weekly pattern analysis)
