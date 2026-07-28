---
name: kai-content-calendar
description: Plan and produce a content calendar — a month (or quarter) of blog posts, LinkedIn articles, and SEO content mapped to business goals, personas, and keywords. Generates briefs for each piece, optionally batch-produces all content with quality gates. Use when "content calendar", "plan blog content", "monthly content", "quarterly content plan", "what should we publish", "content strategy", "editorial calendar", or any request to plan multiple pieces of content over time.
---

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

An approved editorial calendar covering a month or a quarter, where every slot has a scored reason to exist, a named persona, a keyword target, and a brief specific enough to write from. Content grouped into pillars and clusters so the calendar builds topical authority rather than accumulating unrelated posts. Optionally, the pieces themselves, produced and gated.

The kill list is part of the deliverable. A calendar that kept every idea was not a plan.

## Done when

Work type `strategy-plan` (`also_covers: content-calendar`) — floor **E3/C3/O1** (`harness/eco-floors.yaml`).

- **E3** — a named human approved the exact calendar: topics, angles, keyword targets, persona assignments, dates, and formats.
- **C3** — `banned_word_check` passes on the plan, and a named non-producer read it end to end. Every calendar row traces to a scored row in `_idea-eval.md` with a source location.
- **O1** — the calendar names the first piece it spawns, the metric that piece targets (organic clicks or impressions from Search Console), a baseline, a threshold, and an owner. Read at 30 days. A calendar nobody publishes from is not CLOSED.

**When batch production runs**, each produced piece carries its own floor, not the plan's: `blog-post` E5/C3/O3 with `four_us_score` ≥ 12/16, `banned_word_check`, and `seo_lint`; `linkedin-article` against `harness/skill-contracts/linkedin-article.yaml` at 12/16 with SEO lint skipped. Max 2 retries per piece, fixing only the named failing dimension.

## Constraints

**Idea eval is mandatory and visible.** Score every candidate in `workspace/content-calendar/_idea-eval.md` before the calendar is presented — one row per idea with persona, source, score, decision, and reason.

| Dimension (1–5 each) | Passes when |
|---|---|
| Business fit | Supports a real goal in `MARKETING.md` |
| Audience pain | Speaks to a named persona problem |
| Proof available | Has source locations, data, a quote, a demo, or an example |
| Channel fit | Fits the intended format and cadence |
| Novelty | Adds information gain beyond generic advice |

**20–25 keep · 15–19 hold** until proof or angle improves · **0–14 kill.** The killed ideas stay visible in the file.

- Every idea needs a source location or an explicit note that it came from internal strategy.
- Do not fill the calendar with unsupported claims just to hit cadence. A short honest calendar beats a full invented one.
- Treat the calendar as a dry run until the user approves topics, dates, and formats.
- Rotate across the 8 personas in `knowledge/personas/_persona-index.md`. A calendar addressing one persona is a campaign, not a calendar.
- Group into pillars (broad topics) and clusters (specific subtopics that link back) — this is what builds topical authority. Architecture: `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md`.
- Recommended cadence is 2–3 pieces per week for SEO traction; state it as a recommendation, not a mandate.
- Search volumes, traffic estimates, and competitor figures are sourced or omitted. Never estimate a volume to justify a keyword.
- All paths resolve relative to the repo root (the directory containing `CLAUDE.md`).

**Every brief** (schema: `harness/brief-schema.md`, output `workspace/content-calendar/briefs/[week]-[slug].json`) carries 3 hook variants, a specific angle that does more than restate the keyword, a named proof or data source, and a clear CTA.

**Parallelization.** Pieces in different pillars can be written in parallel. Pieces in the same cluster are written sequentially — internal linking and angle differentiation depend on knowing what the sibling piece said.

**Know these before mapping anything** (read `MARKETING.md` from the project root first; ask only for what it does not answer): the time horizon, the publishing cadence, which content types are in scope, the primary goal (SEO traffic, thought leadership, lead gen, product education), any keyword research already done, and what is already published that this should build on.

## Context

| Need | Load |
|---|---|
| Pillar/cluster topical architecture | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` |
| The 8 personas and selection tables | `knowledge/personas/_persona-index.md` |
| Brief schema | `harness/brief-schema.md` |
| Blog/SEO writing rules | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` + `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` |
| LinkedIn article rules | `knowledge/channels/linkedin-articles.md` |
| Format contracts | `harness/skill-contracts/blog-post.yaml` · `harness/skill-contracts/linkedin-article.yaml` |
| Goals, ICP, voice, existing channels | `MARKETING.md` (project root) |

**Output** goes to `workspace/content-calendar/`:

```
workspace/content-calendar/
├── _content-map.md              # pillars, clusters, and the full calendar table
├── _idea-eval.md                # scored ideas, decisions, kill list
├── briefs/                      # w1-slug-1.json, ...
├── drafts/                      # w1-slug-1.md, ...  (batch production only)
├── _quality-report.md
└── _distribution.md
```

`_content-map.md` carries the calendar table: week, date, title, format, pillar, keyword, persona, priority.

`_quality-report.md` carries totals (planned, produced, passed all gates, average Four U's), a per-piece results row for each piece (title, format, persona, Four U's, banned words, SEO lint, status), the internal linking map showing the pillar/cluster structure, and SEO coverage — keywords targeted, volumes where a source exists, and content gaps.

`_distribution.md` covers which pieces cross-post to LinkedIn, the email newsletter inclusion schedule, the per-piece social promotion plan, and internal linking instructions for the blog.

## Escalate when

- Fewer ideas survive the eval than the requested cadence needs — surface the shortfall rather than promoting killed ideas.
- The keyword targets require research nobody has done and no research tool is available.
- The requested cadence exceeds what the team can produce or the proof inventory can support.
- The user wants a topic whose only support would be an invented statistic.
- A piece fails its gates twice for the same reason during batch production.
- The calendar's goals in `MARKETING.md` conflict with the topics being requested.
