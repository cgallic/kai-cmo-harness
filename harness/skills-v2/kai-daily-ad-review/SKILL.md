---
name: kai-daily-ad-review
description: Daily ad performance check-in across platforms. Pulls live metrics from Meta, Google, and LinkedIn via deterministic scripts, compares against benchmarks and previous period, flags overspend/underperformers/policy issues, and outputs a quick daily summary with action items. Use when "daily ad review", "how are my ads doing today", "ad check-in", "morning ad report", "daily ad summary", "check ad performance", "ad dashboard", "daily ads", or any request for a recurring or quick-glance ad performance review.
---

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

A scannable daily pulse on live ad performance: today's numbers against the 7-day trend, every problem flagged with its severity, and a short list of specific actions naming the campaign or ad they apply to. Every figure traceable to the morning's pull.

This is not `/kai-ad-campaign`, which builds and evaluates campaigns end to end. This is the fast check that decides whether a deeper audit is needed today.

## Done when

Work type `audit-report` (`also_covers: weekly-audit, monthly-audit` — the daily-cadence member of the same family) — floor **E3/C4/O1** (`harness/eco-floors.yaml`).

- **E3** — the review at `workspace/ads/daily-reviews/[YYYY-MM-DD]-daily-review.md` is the version a named human read and approved before any action is taken from it.
- **C4** — every number in the review resolves to today's pull artifact under `workspace/ads/pulls/YYYY-MM-DD/`. No metric appears that is not in the JSON. Platforms without credentials are reported as not pulled, never estimated. `banned_word_check` passes.
- **O1** — each action item names the metric it should move, that metric's current value from the pull, a threshold, and the date it gets re-read.

## Constraints

**Pull before analyzing.** `python scripts/ads/pull_all.py` auto-detects which platforms have credentials and writes `meta.json`, `google.json`, `linkedin.json`, and `summary.json` to `workspace/ads/pulls/YYYY-MM-DD/`. Scope to one platform with `--platforms meta`. When a platform is skipped, the script logs which env vars are missing — report that, do not fill the gap. At minimum Meta should be configured (`META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` numeric without the `act_` prefix).

**Never write a metric from memory, from yesterday's review, or from an estimate.** If it is not in today's JSON, it is not in the review.

**Mutations require approval.** `scripts/ads/meta.py`, `scripts/ads/google.py`, and `scripts/ads/linkedin.py` expose pause, activate, budget, add-negative, and creation commands. They are dry-run by default and need `--execute` to apply. Live ad-account mutation without recorded human approval is never SHIPPED, whatever the evidence shows — this skill recommends actions and does not take them. Acting on a recommendation crosses into `paid-ad-campaign` (E5/C4/O4, `spend_authority: true`).

**The benchmark table below is a default, not this account's benchmark.** Adjust to the vertical from `MARKETING.md` where it exists, and label any benchmark that has no sourced vertical figure as a default rather than a target.

**Escalation on recurrence.** When the same flag appears 3+ days running, stop re-reporting it and recommend `/kai-ad-campaign` in evaluation mode for a deeper audit.

**Cross-reference PostHog when connected** using `harness/references/posthog-marketing-queries.md` — today's ad traffic with UTM breakdown (query #2), conversion events with campaign attribution (query #8), and bounce on pages receiving ad traffic. This connects spend to on-site behavior; when PostHog is not connected, say so.

**Compare against history.** Diff today's pull against yesterday's under `workspace/ads/pulls/` for precise trends, and against prior files in `workspace/ads/daily-reviews/` for week-over-week spend, recurring flags, and whether yesterday's action items were addressed.

## Context

| Need | Load |
|---|---|
| Unified pull across configured platforms | `scripts/ads/pull_all.py` |
| Meta pull + mutation commands | `scripts/ads/meta.py` |
| Google pull + mutation commands | `scripts/ads/google.py` |
| LinkedIn pull + mutation commands | `scripts/ads/linkedin.py` |
| Ad traffic and conversion queries | `harness/references/posthog-marketing-queries.md` |
| Paid channel checklist for deeper review | `knowledge/checklists/paid-acquisition-checklist.md` |
| Vertical, goals, budget context | `MARKETING.md` (project root) |

**Where the signal lives in each pull:**

| Platform | Fields that carry the diagnosis |
|---|---|
| Meta | `account_insights.last_7d` (spend, impressions, reach, frequency, ctr, cpc) · `campaigns[].insights_7d` · `adsets[].audience_type` (LAL / custom / interest / advantage+ / broad) · `adsets[].insights_daily` for fatigue · `ads[].insights_7d` incl. `quality_ranking` (ABOVE_AVERAGE_35 / AVERAGE / BELOW_AVERAGE_35), engagement and conversion rate rankings · `breakdowns.age_gender` · `breakdowns.platform_position` (FB Feed vs IG Reels vs Stories) |
| Google | `campaigns[].insights_daily` for CPC/CPA trend · `search_terms` for wasted spend · `keyword_quality` (flag quality score < 5) · `audience_segments` |
| LinkedIn | `campaigns[].insights_7d` engagement rate (higher baseline than Meta/Google) · `breakdowns.industry` + `breakdowns.job_function` · `campaigns[].audience_type` (matched audience vs professional targeting) |

**Benchmarks** (default grid — adjust to vertical):

| Metric | Poor | OK | Good | Great |
|--------|------|----|------|-------|
| CTR | < 0.5% | 0.5–1% | 1–2% | > 2% |
| CPC | > $5 | $3–5 | $1.50–3 | < $1.50 |
| CPL | > $50 | $30–50 | $15–30 | < $15 |
| ROAS | < 1x | 1–2x | 2–4x | > 4x |
| Frequency | > 4.0 | 3.0–4.0 | 1.5–3.0 | 1.0–1.5 |

**Trend detection** — today vs the 7-day average: spend pace > 120% of daily average is overspend · CTR < 70% of the 7-day average is creative fatigue · CPC > 130% is a competition spike or audience saturation · conversions < 50% of the daily average means a broken funnel or tracking · frequency > 3.0 means fatigue is coming · any BELOW_AVERAGE_35 diagnostic dimension is a flag.

**Issue detection:**

| Issue | Trigger | Severity |
|-------|---------|----------|
| Overspend | Daily spend pace > 120% of budget | HIGH |
| Zero impressions | Active ad with 0 impressions today | HIGH |
| CTR crash | CTR < 50% of 7-day avg | HIGH |
| CPC spike | CPC > 150% of 7-day avg | MEDIUM |
| No conversions | Spend > $50 today with 0 conversions | MEDIUM |
| Creative fatigue | CTR declining 3+ consecutive days | MEDIUM |
| Frequency overload | Frequency > 3.5 on any ad set | MEDIUM |
| Quality warning | Any ad with BELOW_AVERAGE quality ranking | MEDIUM |
| Wasted search spend | Google search term with > $20 spend, 0 conversions | MEDIUM |
| Budget underspend | < 50% of daily budget used by midday | LOW |
| Learning phase | Ad set in learning phase > 7 days | LOW |
| LAL underperform | LAL CPL > broad/interest CPL | LOW |

**Audience reading** (from `audience_type` tagging): lookalikes should show lower CPL than broad · custom retargeting audiences should show the highest CTR · note when Advantage+ beats manual targeting · flag LAL underperforming interest targeting for investigation.

**Output** goes to `workspace/ads/daily-reviews/[YYYY-MM-DD]-daily-review.md`, scannable in under a minute, carrying:

- **Snapshot** — today vs 7-day average vs trend direction for spend, impressions, reach, frequency, clicks, CTR, CPC, conversions, CPL.
- **Flags** — one line each, severity-prefixed, naming the campaign or ad set and the number that triggered it.
- **Audience performance** — ad sets, spend, leads, CPL, and CTR per audience type.
- **Campaign breakdown** — spend, clicks, CTR, CPC, conversions, CPL, status per campaign.
- **Top performers and underperformers** — each underperformer with what is wrong and the specific action (pause, adjust, replace creative).
- **Quality diagnostics** — only the non-ABOVE_AVERAGE entries.
- **Action items** — checkbox list, each naming the campaign or ad it applies to.

This skill is built to run every morning. Recommend `/schedule` for a recurring trigger.

## Escalate when

- No platform is configured and the pull returns nothing — report the missing env vars; a review with no data is a failure record, not an empty report.
- The same flag has appeared 3+ days running.
- Spend is pacing far past budget and the fix requires a live mutation.
- Conversions dropped to zero across platforms at once — suspect tracking, not creative, and say so.
- The account's numbers contradict what `MARKETING.md` says the budget or goal is.
- A recommended action would change budget, targeting, or creative on a live account without a recorded human approval.
