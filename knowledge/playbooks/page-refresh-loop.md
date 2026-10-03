---
title: Page Refresh Loop
type: playbook
created: 2026-10-03
updated: 2026-10-03
---

# Page Refresh Loop

> **Use when:** a property already earns search impressions and the goal is more clicks, or before anyone proposes a new site, a new content program, or a satellite network. Skill: `/kai-page-refresh`.

## Why this comes first

The harness's own record across a 62-property portfolio (Kai CMO evidence file, Search Console, 2026-10-02): about 640 search clicks a month, 93% of them from four established properties. 52 properties earned under 2 clicks a month. The wins shared one recipe: an established local business with deep pages for each service and town. Newly built satellite sites without history did not catch up.

So the default order is: improve what already ranks, measure it, and only then make something new.

## The loop

1. **Triage the portfolio** (`python -m scripts.seo.portfolio`). `invest` = the few properties carrying most non-brand clicks; `maintain` = real but minor; `freeze` = no new work until a fix on an existing page shows clicks.
2. **Queue** (`python -m scripts.seo.striking_distance`). From a Search Console query x page export, brand excluded:
   - *CTR gap*: ranks 1-7 but earns under half the expected CTR for that position. Fix the title and meta description.
   - *Striking distance*: ranks 8-20 with real impressions. Align the title to the query, add the missing section, add internal links from the site's strongest pages.
   - *Split queries*: two pages share a query's impressions. Pick one.
   Expected CTR is calibrated on the site's own data where a position has enough impressions spread across pages, and falls back to a labeled heuristic elsewhere. Upside is an ordering tool, not a forecast.
3. **Draft and approve** the top 5 fixes. One page, one primary change, so the grade means something.
4. **Record before ship** (`refresh_tracker record`). The baseline window must end before the ship date.
5. **Grade at 28 days** (`refresh_tracker check`). The page's non-brand clicks are compared with the rest of the site over the same windows, so a seasonal swing is not credited to the fix.
6. **Learn** (`refresh_tracker report` into `/kai-retro`). Fix types that keep winning become defaults in `knowledge/playbooks/what-works.md`; losers go to `memory/what-doesnt-work.md` with a diagnosis.

## Rules

- Exclude brand queries before anything else.
- Never claim a ranking or click number without the export and window it came from.
- Clicks are not revenue. When a property records no conversions, the first fix is instrumentation (GA4 key events or CRM source on the lead form), and the report says revenue is unknown.
- Do not change more than one thing on a page inside one grading window.
