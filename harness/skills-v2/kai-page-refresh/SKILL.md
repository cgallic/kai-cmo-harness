---
name: kai-page-refresh
description: Grow search clicks by fixing pages that already rank instead of making new ones. Triages the portfolio (invest / maintain / freeze), builds a refresh queue from Search Console (CTR gaps at positions 1-7, striking distance at 8-20, split queries), drafts the fixes, and grades every shipped fix 28 days later against a site-level control. Use when "striking distance", "page two", "refresh pages", "improve existing pages", "low CTR", "rewrite titles", "why is traffic flat", "which site should we focus on", "more clicks from search", or before planning any new site or content program.
---

# /kai-page-refresh — More Clicks From Pages That Already Rank

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

More non-brand search clicks on the properties that already earn them, from approved fixes to existing pages, each one recorded with a pre-ship baseline so it is graded rather than assumed. The owner ends with a ranked queue, drafted fixes for the top pages, tracker records for whatever ships, and a clear statement of which properties get no new work.

Doctrine: `knowledge/playbooks/page-refresh-loop.md`.

## Done when

Work type `page-refresh` — floor **E3/C3/O3** (`harness/eco-floors.yaml`).

- **E3** — the owner approved the exact fixes; for each shipped one a tracker record exists whose baseline window ends before the ship date.
- **C3** — the queue excludes brand queries, cites its export and window, labels upside as an estimate; new body copy passes `/kai-gate`.
- **O3** — `refresh_tracker check` read Search Console 28+ days after ship and graded the fix against the site-level control. O4 when the grade is `won`.

## Constraints

- **Kai Data Provenance.** Load `harness/references/audit-data-provenance.md`. Every number comes from a Search Console export with a stated window and retrieval date; missing data (no GSC access, no conversions, no titles) goes in `_data-gaps.md`. No export, no queue: ask for one rather than estimating.
- **Existing pages first.** Run `python -m scripts.seo.portfolio` for multi-site owners. A `freeze` property gets no new pages or sibling sites in this run; say so when a plan proposes one.
- **Brand terms are always excluded** (`--brand`); brand clicks cannot be won by editing a page.
- **Baseline before ship.** `python -m scripts.seo.refresh_tracker record` must run before or on the ship date with a window that ends before it. A fix recorded late is reported as unmeasured, not graded.
- **No live mutation.** This skill drafts; the owner publishes.
- **Never self-grade.** The tracker's Search Console read issues the grade; feed it to `/kai-retro`, which decides what reaches `what-works.md`.

## Context

- Data: `python -m scripts.seo.gsc_data pull --site <property> --out <file>` where the credentials live (often the owner's machine), or a CSV export with query, page, clicks, impressions, CTR and position.
- Queue: `python -m scripts.seo.striking_distance --data <file> --brand "<terms>" --titles <crawl.csv> --out workspace/seo-refresh/<site>`. Actions: `rewrite_title_meta` (ranks 1-7, under half the expected CTR), `align_title_to_query`, `expand_depth` (5+ page-two queries), `internal_links` (from the `link_from` pages, query as anchor).
- Drafting rules: titles under 60 characters with the top query first; new sections answer first per `knowledge/frameworks/content-copywriting/algorithmic-authorship.md`.
- Grading: `refresh_tracker check --data <post-ship export>` then `refresh_tracker report`. Grades `won / flat / lost / insufficient_data` against the rest of the site over the same windows.

## Escalate when

- No Search Console export can be produced from any reachable machine.
- The top queue pages are noindexed, redirected, or scheduled for removal.
- Two pages split a query and choosing one means removing or merging a page.
- The owner wants a new property while an `invest` property still has an unworked queue.
