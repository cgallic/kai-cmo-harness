---
name: kai-weekly-audit
description: Weekly marketing audit and operating review. Pulls the last 7 days of source-backed marketing, analytics, content, paid media, lead, watcher, and audit data; compares it to the prior 7 days; flags urgent issues; and produces a weekly scorecard plus action list. Use when "weekly audit", "weekly marketing review", "weekly check-in", "weekly scorecard", "what changed this week", "Friday marketing review", or any request for a recurring 7-day marketing audit.
---

# /kai-weekly-audit — what changed this week, and what someone does about it Monday

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

A sourced weekly operating review: the last 7 complete days measured against the prior 7, every material change scored, and a short action list with owners. This is the cadence layer above `/kai-audit`, `/kai-seo-audit`, `/kai-cro`, `/kai-daily-ad-review`, `/content-report`, and watcher output — it does not re-run those audits, it reads their output and decides what needs a decision this week.

A review that scores a metric it cannot source is worse than a review that reports a gap.

## Done when

Work type `audit-report` (`also_covers: weekly-audit`) — floor **E3/C4/O1** (`harness/eco-floors.yaml`).

- **E3** — a named human approved the exact delivered file, and every quantitative claim resolves to a collector artifact in the week's audit folder.
- **C4** — the Kai Data Provenance Rule: collector run before writing, mode declared, a source cited for every number, missing sources written to `_data-gaps.md`, then `python scripts/quality_gates/audit_provenance_lint.py workspace/audits/weekly/<YYYY-MM-DD> --audit-dir` passes alongside `banned_word_check`.
- **O1** — every P0/P1 action names the metric it targets, its current value, the threshold that counts as fixed, and an owner. Read at 60 days: were the recommendations adopted and did the metric move?

## Constraints

- **Provenance is non-negotiable.** Load `harness/references/audit-data-provenance.md` before writing findings. Declare the mode: `sales_external` for prospect or public-only reviews, `onboarding_connected` when GSC, GA4, GBP, ads, CRM, call tracking, or client exports are connected, `internal_demo` when sample data is used.
- **Never publish a review count, ranking, traffic figure, conversion, call volume, ad metric, Core Web Vital, backlink, or revenue number without source, retrieval date, and artifact path.** Missing sources become `_data-gaps.md` entries, never estimates.
- **Only score metrics present in `audit-data.json`, connected exports, or raw pull artifacts.** Everything else is scored Gray.
- **Every scored item carries its provenance block:**
  ```yaml
  claim: ""
  source_tier: connected | public_observed | user_provided | inferred | missing_data
  source_name: ""
  source_url: ""
  retrieved_at: ""
  evidence_artifact: ""
  score_eligible: true | false
  ```
- **Connected collectors run only when access is confirmed.** If a command cannot run because credentials are missing, record the exact missing source in `_data-gaps.md` rather than substituting another source.
- **Comparison window is fixed:** last 7 complete days against the prior 7 complete days. Partial days are excluded.
- **This skill reads and reports. It does not change ad accounts, pages, or sends.** Recommended fixes route to the skill that owns the change, which carries its own approval gate.

## Context

| Need | Load / run |
|---|---|
| Provenance doctrine and modes | `harness/references/audit-data-provenance.md` |
| Brand, URL, channels, conversion events, connected sources | `MARKETING.md` (project root) |
| Shared collector | `python -m scripts.audit.collect --url "<url>" --mode <mode> --workflow kai-weekly-audit --out workspace/audits/weekly/<YYYY-MM-DD> --pagespeed` |
| Connected pull (access confirmed only) | same command with `--mode onboarding_connected --places --gsc --ga4 --calls --date-from "<YYYY-MM-DD>" --date-to "<YYYY-MM-DD>"` |
| Paid, content, analytics pulls | `python scripts/ads/pull_all.py` · `python -m scripts.content.tracker_cli report --format json` · `python -m scripts.analytics.performance_dashboard weekly` |
| Provenance gate | `python scripts/quality_gates/audit_provenance_lint.py workspace/audits/weekly/<YYYY-MM-DD> --audit-dir` |

**Review areas** — cover each where data exists:

| Area | Weekly question |
|---|---|
| Revenue or pipeline | Did qualified demand, revenue, or pipeline move materially? |
| Website and CRO | Did traffic quality, speed, conversion, or form/call capture degrade? |
| SEO and AEO | Did indexed visibility, crawl health, search queries, or AI-search readiness change? |
| Paid media | Did spend, CPL, ROAS, CPA, CTR, CPC, or frequency drift outside guardrails? |
| Content | Which new or aging pieces need action? |
| Social and community | Did reach, engagement, replies, or audience quality change? |
| Lifecycle and CRM | Did follow-up, reply rate, lead aging, or handoff quality change? |
| Calls and reviews | Did missed calls, after-hours demand, reviews, or reputation signals need action? |
| Watchers | Which alerts repeated or escalated? |

**Scorecard scale:** Green = on track · Yellow = needs attention this week · Red = immediate owner decision or fix · Gray = not scored, data missing.

**Actions** group into three: *Do this week* (P0/P1 with owner and due date), *Watch next week* (trend risk, insufficient evidence), *Needs data* (sources required before the next review). Route each fix:

| Finding | Skill |
|---|---|
| Site or funnel issue | `/kai-cro` or `/kai-landing-page` |
| Search issue | `/kai-seo-audit` or `/kai-surround-sound` |
| Paid issue | `/kai-daily-ad-review` or `/kai-ad-campaign` |
| Content issue | `/content-report`, `/content-retro`, or `/kai-content-calendar` |
| Lifecycle issue | `/kai-email-system` or `/kai-retention` |
| Strategic drift | `/kai-growth-plan` |
| Client-ready deck needed | `/kai-html-presentation` |

**Output** goes to `workspace/audits/weekly/<YYYY-MM-DD>/`: `_data-sources.md`, `_data-gaps.md`, `audit-data.json`, `kai-data.json`, `_weekly-scorecard.md`, `_weekly-findings.md`, `_weekly-actions.md`, `_skill-routing.md`, and `html-presentation/index.html` when the user asks for a client-ready artifact (via `/kai-html-presentation`).

## Escalate when

- The URL, data mode, connected sources, or target conversion event is unknown and the review cannot be sourced.
- A collector fails and the missing source would change a Red/Green call.
- A metric moved sharply and the available data cannot distinguish a real change from a tracking break.
- A finding implies spend, a live-channel change, or a client-facing claim that has not been approved.
