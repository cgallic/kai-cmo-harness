---
name: kai-data-dashboard
description: Convert Kai workflow data, CSV exports, audit folders, SDR package outputs, and marketing reports into dashboard-ready specs or lightweight static dashboards. Use when "data dashboard", "operator dashboard", "operator room", "HTML operators room", "sales dashboard", "SDR dashboard", "turn this data into a dashboard", "dashboard handoff", "visualize Kai data", or any request to package sourced marketing, sales, audit, or SDR data for a dashboard or presentation surface.
---

# /kai-data-dashboard — Sourced Data As An Operator Surface

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

A dashboard handoff package that a frontend, BI team, or single static HTML file can build from without anyone inventing a number: every metric defined by formula, every metric bound to a named source, every unsupported field visible as a gap. The data already exists — this skill packages it into an operator surface.

This is a companion surface. It does not replace analytics setup, audit analysis, or outbound strategy.

## Done when

Work type `audit-report` — floor **E3/C4/O1** (`harness/eco-floors.yaml`). This package is client- or operator-facing and carries quantitative claims, so it inherits the audit floor rather than the internal default.

- **E3** — a named human approved the exact delivered files, and every number in the spec resolves to a row in `source-map.md` or the source folder's `_data-sources.md`.
- **C4** — the Kai Data Provenance Rule holds. Mode declared, sources cited, gaps written down. For audit source folders, `audit_provenance_lint.py` passes.
- **O1** — every alert threshold names the metric it watches and whether the threshold is sourced or a stated hypothesis. A threshold with no label is not finished.

## Constraints

- **A source is required.** Accept `workspace/sdr-operator/<package-slug>/`, any folder holding `kai-data.json`, `audit-data.json`, `_data-sources.md`, or `_data-gaps.md`, CSV exports from CRM/ESP/sequencer/ads/analytics/sales tools, markdown reports with source-backed findings, or user-provided metrics and targets. If there is no source folder or file, ask for it.
- **No fabricated sample data** unless the output is explicitly labeled `internal_demo`.
- **Declare the data mode** on the artifacts: `sales_external`, `onboarding_connected`, `user_provided`, or `internal_demo`.
- **Read the provenance ledgers before designing anything** — `_data-sources.md`, `_data-gaps.md`, and the available JSON/CSV files. Do not add numbers that are not present in the source. Unsupported fields are listed as gaps.
- For audit source folders, run the blocking lint:
  ```bash
  python scripts/quality_gates/audit_provenance_lint.py <source-folder> --audit-dir
  ```
- **Before handoff:** every number has a source, retrieval date, or `internal_demo` label; every metric has a formula or definition; `_data-gaps.md` / `data-gaps.md` is represented in the surface; no placeholder text remains; sensitive fields are excluded, masked, or explicitly approved. HTML output is readable at desktop and mobile widths.
- **Gaps are a first-class panel**, never hidden or filled in.
- **Do not build a full frontend app** unless the user asks for implementation. For app builds, hand the spec to the relevant frontend skill or repository code.
- **Static HTML rules** when `index.html` is produced: single file unless app integration is requested; tables for dense operator data; restrained styling with readable status colors and responsive layout; critical numbers as text rather than only canvas or images; a source footer or source drawer; empty states for missing metrics.

## Context

| Need | Load |
|---|---|
| Provenance rule, modes, source tiers, gap handling | `harness/references/audit-data-provenance.md` |
| Source-folder ledgers and collected data | `_data-sources.md`, `_data-gaps.md`, `kai-data.json` / `audit-data.json` in the source folder |
| Tracking plan or attribution model instead | `/kai-analytics` |
| Client-ready audit deck instead | `/kai-html-presentation` |
| Durable, white-labeled client product with onboarding wizard and page set | `/kai-client-dashboard` (it calls this skill for the data-contract layer underneath it) |

**Dashboard type** — pick from source and request. Default to `sdr_operator_room` when the source came from `/kai-sdr-operator`.

| Type | Best fit | Primary view |
|---|---|---|
| `sdr_operator_room` | SDR package, lead ledger, reply data | Pipeline state, source quality, next actions |
| `marketing_ops` | Campaign, content, SEO, ad, lifecycle data | Channel performance and bottlenecks |
| `executive_scorecard` | Monthly/weekly report | KPIs, decisions, risks, next steps |
| `audit_delivery` | Audit folder | Findings, scorecards, fixes, data gaps |
| `connector_health` | API sync or integration data | Source freshness, failures, missing credentials |

**Spec contract.** Every dashboard spec carries: audience (executive, operator, SDR, marketer, client, founder, or analyst); jobs to be done; metric definitions with exact formulas; data source per metric; refresh cadence and freshness warning; widgets, filters, drilldowns, empty states, error states; alert thresholds with source or hypothesis label; permissions and sensitive-data handling; handoff notes for frontend, BI, or static HTML build.

**SDR dashboards additionally carry:** status counts by `sourced`, `enriched`, `approved_for_copy`, `queued`, `sent`, `replied`, `meeting_booked`, `disqualified`, `suppressed`, `blocked`; source quality table; fit score distribution; next-action queue; reply triage categories; suppression, bounce, opt-out and complaint warnings; data gaps that block live outreach.

**Output** goes to `<source-folder>/dashboard/`: `dashboard-spec.md`, `metrics-dictionary.md`, `data-contract.json`, `source-map.md`, `data-gaps.md`, plus `index.html` when the user asks for a usable static artifact. Report the folder path, dashboard type, files produced, data gaps, and whether HTML was built or only specified.

## Escalate when

- No source folder or file was given, or the named source contains no retrievable data.
- The user wants a metric the source cannot support — that is a gap, and forcing it needs a human decision.
- Sensitive fields (PII, contact records, call recordings, revenue detail) would appear on a surface whose permissions are undefined.
- The request is a full frontend app build rather than a spec plus optional static file.
- Sample data is requested for a surface that will not be labeled `internal_demo`.
