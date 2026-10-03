---
name: kai-page-refresh
version: 1.0.0
category: measurement
last_updated: 2026-10-03
---

# Kai Page Refresh

### One-line claim
More search clicks from pages that already rank. Kai triages the portfolio, ranks existing pages by fixable upside from Search Console, drafts the fixes, and grades each shipped fix 28 days later against the rest of the site.

### Triggers
- striking distance / page two
- improve existing pages
- low CTR / rewrite titles
- why is search traffic flat
- which site should we focus on
- before planning a new site or content program

### Inputs
- `gsc_export` (file, required): Search Console query x page rows with a stated window, from `python -m scripts.seo.gsc_data pull` or a CSV export.
- `brand_terms` (list, required): excluded before anything is scored.
- `portfolio` (CSV, optional): `site, clicks, impressions, brand_clicks, conversions, days` for multi-site owners.
- `titles` (CSV, optional): page,title from a crawl, which enables the title-alignment check.
- `approver` (string, required to ship): the person who approves each fix.

### Outputs
- `workspace/seo-refresh/portfolio.md|json`: invest / maintain / freeze per property.
- `workspace/seo-refresh/<site>/refresh-queue.md|json`: pages by estimated upside, with the action, top queries, missing title terms, internal-link sources, and split queries.
- Drafted fixes for the top 5 pages.
- `<data_dir>/seo/refreshes/<id>.json`: one record per shipped fix, baseline included, checks appended.
- `refresh-outcomes.md`: win rate and median lift by fix type.

### Methodology
- [page-refresh-loop.md](../../knowledge/playbooks/page-refresh-loop.md)
- Expected CTR is calibrated on the site's own non-brand data where a position has enough impressions spread across pages, with a labeled heuristic elsewhere.
- Grades compare the page's non-brand clicks with the rest of the site over the same windows, so seasonality is not credited to the fix.
- Provenance follows [audit-data-provenance.md](../../harness/references/audit-data-provenance.md).

### Dependencies
- [kai-gate](./kai-gate.md) for new body copy
- [kai-retro](./kai-retro.md) turns graded fixes into what-works / what-doesnt-work entries

### Called by
- The `/kai` router (AUDIT table)

### Quality gates
- ECO work type `page-refresh` (E3/C3/O3).
- The tracker refuses a baseline window that does not end before the ship date.
- Brand queries are excluded from the queue and from grading.

### Failure modes
- No Search Console access from the working machine: pull on the owner's machine or use a CSV export.
- Page URLs in the export differ from the record (trailing slash, http/https): the check skips them.
- Two changes on one page inside one window make the grade unattributable.

### Competitive claim
Every fix carries its own pre-ship baseline and a control-adjusted grade, so the harness learns which kinds of fixes move clicks instead of assuming they did.
