---
name: kai-page-refresh
description: Grow search clicks by fixing pages that already rank instead of making new ones. Triages the portfolio (invest / maintain / freeze), builds a refresh queue from Search Console (CTR gaps at positions 1-7, striking distance at 8-20, split queries), drafts the fixes, and grades every shipped fix 28 days later against a site-level control. Use when "striking distance", "page two", "refresh pages", "improve existing pages", "low CTR", "rewrite titles", "why is traffic flat", "which site should we focus on", "more clicks from search", or before planning any new site or content program.
---

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

Improve the pages that already earn impressions, then prove each fix worked. Doctrine: `knowledge/playbooks/page-refresh-loop.md`. ECO work type: `page-refresh` in `harness/eco-floors.yaml`.

## Non-Negotiable: Kai Data Provenance

Load `harness/references/audit-data-provenance.md`. Every number in the queue, the drafts, and the report comes from a Search Console export with a stated window and retrieval date. Upside figures are labeled estimates. Missing data (no conversions, no titles, no GSC access) goes in `_data-gaps.md`, not into a guess.

## Phase 1 — Get the data

Search Console is often reachable only from the owner's machine. Pull there, then work anywhere:

```bash
python -m scripts.seo.gsc_data pull --site sc-domain:<domain> --out data/seo/<site>-<YYYYMMDD>.json
```

Default window: the 90 days ending 3 days ago. A CSV export with query, page, clicks, impressions, CTR and position columns also works; pass `--start/--end` with it. If neither is available, stop and ask for one. Do not estimate rankings.

## Phase 2 — Triage the portfolio (multi-site owners)

```bash
python -m scripts.seo.portfolio --data <portfolio.csv> --out workspace/seo-refresh
```

Columns: `site, clicks, impressions, brand_clicks, conversions, days`. Work only `invest` properties in this run. A `freeze` property gets no new pages or sibling sites; say so plainly when a plan proposes one.

## Phase 3 — Build the refresh queue

```bash
python -m scripts.seo.striking_distance --data data/seo/<site>-<date>.json --brand "<brand terms>" --site <site> --titles <crawl.csv> --out workspace/seo-refresh/<site>
```

Always pass brand terms; brand clicks inflate CTR and cannot be won by editing a page. `--titles` (page,title CSV from a crawl) enables the title-alignment check. Read `refresh-queue.md` and confirm the top pages are real, indexable, and still on the site.

## Phase 4 — Draft the fixes (top 5 pages)

Per page, by `primary_action`:

| Action | Draft |
|---|---|
| `rewrite_title_meta` | 3 title options (under 60 characters, top query first, a concrete reason to click) + 1 meta description |
| `align_title_to_query` | Title and H1 that include the missing terms |
| `expand_depth` | One H2 section or table per query cluster, answer first (Algorithmic Authorship rules, `knowledge/frameworks/content-copywriting/algorithmic-authorship.md`) |
| `internal_links` | 3-5 links from the `link_from` pages, anchor text = the query |

For split queries, pick one page per query and propose a link or merge for the other. Run `/kai-gate` on any new body copy before handoff. Drafts go to the owner for approval; nothing is published by this skill.

## Phase 5 — Record before it ships

For every approved fix, on or before the ship date:

```bash
python -m scripts.seo.refresh_tracker record --queue workspace/seo-refresh/<site>/refresh-queue.json --page <url> --change <action> --shipped-on <YYYY-MM-DD> --owner <name> --eco-evidence workspace/seo-refresh/<site>/eco-<slug>.json
```

The baseline window must end before the ship date; the tracker refuses otherwise. Pass `--conversions` when GA4 key events for the page are tracked.

## Phase 6 — Grade

28+ days after shipping, pull a fresh export whose window starts on or after the ship date, then:

```bash
python -m scripts.seo.refresh_tracker check --data data/seo/<site>-<later-date>.json
python -m scripts.seo.refresh_tracker report --out workspace/seo-refresh/refresh-outcomes.md
```

Grades: `won`, `flat`, `lost`, `insufficient_data`, each against the rest of the site's non-brand clicks over the same windows. Feed the report into `/kai-retro`: fix types that keep winning go to `knowledge/playbooks/what-works.md`, losers to `memory/what-doesnt-work.md`.

## Report

```
## Page refresh: [site], [window]
Portfolio: [invest list] · frozen: [count]
Queue: [N] pages, ~[X] clicks estimated upside (estimate)
Drafted: [page]: [action] ...
Recorded for grading: [ids], due [dates]
Graded this run: [won/flat/lost]
Data gaps: [conversions not tracked, titles missing, ...]
```
