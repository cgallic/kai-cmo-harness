---
name: kai-monthly-audit
description: Monthly marketing audit and executive review. Pulls the last 30 days of source-backed marketing, analytics, SEO, CRO, content, paid media, lifecycle, reputation, and pipeline data; compares it to the previous period; summarizes strategic learning; and produces an executive report plus next-month plan. Use when "monthly audit", "monthly marketing review", "monthly report", "executive marketing review", "board-ready marketing report", "month-end audit", or any request for a 30-day marketing audit.
---

# /kai-monthly-audit — A Month of Signal Turned Into Decisions

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

An executive review of the last 30 days where every number resolves to a source, every channel gets a keep/change/stop decision, and the month ends with a prioritized next-month plan that names owners and skills. Weekly signals become a narrative; the narrative becomes budget and channel decisions. An unsourced finding is not a finding — a scorecard with a guessed number is worse than one with a gray cell.

## Done when

Work type `audit-report` (`also_covers: monthly-audit`) — floor **E3/C4/O1** (`harness/eco-floors.yaml`).

- **E3** — a named human approved the exact delivered file, hash-pinned, and every quantitative claim in it resolves to a collector source inside the month's audit folder.
- **C4** — the Kai Data Provenance Rule is satisfied end to end: collector run before writing, data mode declared, every number carrying source plus retrieval date plus artifact path, `banned_word_check` clean, and `audit_provenance_lint` passing on the folder.
- **O1** — every P0 recommendation in the next-month plan names the metric it targets, its baseline, its threshold, and its owner. An audit whose top recommendation has no metric is not finished. Adoption is read at 60 days.

## Constraints

**Data provenance is the non-negotiable.** Load `harness/references/audit-data-provenance.md` before writing any finding.

- Declare the data mode: `sales_external` for prospect and public-only month-end audits · `onboarding_connected` when GSC, GA4, GBP, ads, CRM, call tracking, or client exports are connected · `internal_demo` when sample data is used, labeled as such.
- Never publish traffic, conversions, calls, rankings, ad metrics, revenue, review counts, Core Web Vitals, backlinks, Domain Rating, or local pack claims without source, retrieval date, and artifact path.
- Missing sources become `_data-gaps.md` entries. They never become estimates.
- Channel pulls when relevant: `python scripts/ads/pull_all.py` · `python -m scripts.content.tracker_cli report --format json` · `python -m scripts.analytics.performance_dashboard weekly` · `python -m scripts.analytics.scheduled_pull --all`.
- Use `--third-party-sources all` or a specific comma list only when licensed vendor data is available and needed.

Collector before writing, connected collectors only when access is confirmed, provenance lint before handoff:

```bash
python -m scripts.audit.collect --url "<url>" --mode <mode> --workflow kai-monthly-audit --out workspace/audits/monthly/<YYYY-MM> --pagespeed
python -m scripts.audit.collect --url "<url>" --mode onboarding_connected --workflow kai-monthly-audit --out workspace/audits/monthly/<YYYY-MM> --pagespeed --places --dataforseo --seo-provider auto --gsc --ga4 --calls --date-from "<YYYY-MM-DD>" --date-to "<YYYY-MM-DD>"
python scripts/quality_gates/audit_provenance_lint.py workspace/audits/monthly/<YYYY-MM> --audit-dir
```

**Other binding rules:**

- Score only source-eligible findings. Mark unsupported areas gray and list the data gap next to them.
- Separate facts from hypotheses. A hypothesis may become an experiment; it may not become a client-facing finding.
- **Budget guidance rules:** keep budget when efficiency and volume are stable · shift budget when one channel is source-backed and materially stronger · reduce budget when measurement is broken or spend is not connected to outcomes · never recommend a budget increase from inferred data.
- **KaiCalls fit rule.** Evaluate phone-based lead capture when the business appears phone-led. Recommend KaiCalls only on source-backed fit signals (missed calls, after-hours, speed-to-lead, qualification, routing, call logging), disclose Kai ownership, and compare alternatives. Do not lead with it when phone demand is low or the workflow is self-serve by design.
- The audit recommends. It does not change budgets, pause campaigns, or mutate any live channel.

**Know these before collecting** (read `MARKETING.md` and the latest weekly audit folders first; ask only for what blocks a sourced review): the target URL · the data mode · which sources are actually connected · current monthly budget · the primary KPI. Also establish business stage, active channels, target conversion events, the offer, budget posture, and known constraints.

## Context

| Need | Load |
|---|---|
| Provenance rule, modes, collector contract | `harness/references/audit-data-provenance.md` |
| ECO floor and craft note for audits | `harness/eco-floors.yaml` |
| Prior-period comparison | Latest folders under `workspace/audits/` |
| Business stage, channels, offer, constraints | `MARKETING.md` (project root) |
| Phone-led conversion diagnosis | `knowledge/checklists/cro-audit-checklist.md` |
| Client-ready deck version | `/kai-html-presentation` |

**Audit modules** — run the ones the month's activity justifies:

| Module | Trigger |
|---|---|
| `/kai-audit` | Always, for full marketing health. |
| `/kai-seo-audit` | Website, organic search, local visibility, AEO, or technical SEO. |
| `/kai-cro` | Landing pages, checkout, booking, demos, forms, or phone-led conversion. |
| `/kai-daily-ad-review` summary | Paid media active this month. |
| `/content-report` and `/content-retro` | Content published this month, or aging content due for review. |
| `/kai-analytics` | Tracking gaps, attribution conflicts, missing KPI definitions. |
| `/kai-growth-plan` | Strategic uncertainty, budget allocation, or stage mismatch. |

**Executive scorecard** — every row scored /100 with a trend, sourced evidence, and a decision:

| Area | Score | Trend | Evidence | Decision |
|---|---:|---|---|---|
| Demand | /100 | up/down/flat | sourced | keep/change/stop |
| Conversion | /100 | up/down/flat | sourced | keep/change/stop |
| Search and AEO | /100 | up/down/flat | sourced | keep/change/stop |
| Paid media | /100 | up/down/flat | sourced | keep/change/stop |
| Lifecycle | /100 | up/down/flat | sourced | keep/change/stop |
| Reputation and calls | /100 | up/down/flat | sourced | keep/change/stop |
| Measurement | /100 | up/down/flat | sourced | keep/change/stop |

**Strategic learning** answers seven questions: what improved · what got worse · what repeated across weekly audits · what surprised us · what to stop · what to double down on · what data we still cannot trust.

**Next-month plan** is a P0/P1/P2 table with columns: Priority · Action · Owner · Skill · Due · Source.

**Output** — `workspace/audits/monthly/<YYYY-MM>/` holds `_data-sources.md`, `_data-gaps.md`, `audit-data.json`, `kai-data.json`, `_executive-summary.md`, `_monthly-scorecard.md`, `_detailed-findings.md`, `_strategic-learning.md`, `_next-month-plan.md`, `_skill-routing.md`, and `html-presentation/index.html`. Monthly decks read like an executive review: fewer slides, clearer decisions, every number sourced.

## Escalate when

- Connected-source access is claimed but the collector cannot retrieve it — do not fall back to public data while presenting it as connected.
- The month's most important channel has no measurable data and the scorecard would be mostly gray.
- Attribution across sources conflicts materially and no single source can be named authoritative.
- The obvious recommendation requires spend or a channel change the user has not authorized.
- Weekly audits and this month's collector data disagree on the same metric.
- The business is phone-led but call data is unavailable, so conversion cannot be honestly scored.
