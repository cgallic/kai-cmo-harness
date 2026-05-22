---
name: kai-weekly-audit
version: 1.0.0
category: measurement
last_updated: 2026-05-22
---

# Kai Weekly Audit

### One-line claim
Weekly marketing audit and operating review. Pulls the last 7 days of source-backed marketing, analytics, content, paid media, lead, watcher, and audit data; compares it to the prior 7 days; flags urgent issues; and produces a weekly scorecard plus action list.

### Triggers
- weekly audit
- weekly marketing review
- weekly check-in
- weekly scorecard
- what changed this week
- Friday marketing review
- recurring 7-day marketing audit

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context.
- `url` (string, required) - target website or primary domain.
- `data_mode` (enum, required) - `sales_external`, `onboarding_connected`, or `internal_demo`.
- `connected_sources` (files or credentials, optional) - GSC, GA4, GBP, ads, CRM, call tracking, or exports.
- `date_range` (string, optional) - last 7 complete days and prior 7-day comparison.
- `weekly_artifacts` (files, optional) - watcher state, ad pulls, content report, analytics snapshots, or prior audit files.

### Outputs
- Artifact -> weekly scorecard, findings, action list, data sources, data gaps, and skill routing.
- Quality report -> provenance lint status, blockers, and unresolved data gaps.
- Optional delivery -> HTML presentation generated through `kai-html-presentation`.
- Sidecar fields -> `skill`, `version`, `data_mode`, `source_tiers`, `retrieval_dates`, `collector_paths`, `blocked_claims`, and `recommended_next_skills`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md).

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-005** - "Run `python -m scripts.audit.collect --url <url> --mode <mode> --workflow <workflow> --out <data-folder>` before using numbers in data-backed workflows." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-010** - "Run `python scripts/quality_gates/audit_provenance_lint.py <audit-folder> --audit-dir` before audit or deck handoff." Source: [scripts/quality_gates/audit_provenance_lint.py](../../scripts/quality_gates/audit_provenance_lint.py).
- **POL-005** - "Paid-media evaluation starts read-only. Pull, validate, flag, recommend, and produce dry-run payloads without mutating campaigns." Source: [harness/references/ad-write-guardrails.md](../../harness/references/ad-write-guardrails.md).

### Dependencies
- [kai-audit](./kai-audit.md)
- [kai-seo-audit](./kai-seo-audit.md)
- [kai-cro](./kai-cro.md)
- [kai-daily-ad-review](./kai-daily-ad-review.md)
- [kai-analytics](./kai-analytics.md)
- [kai-html-presentation](./kai-html-presentation.md)

### Called by
- [kai-monthly-audit](./kai-monthly-audit.md)

### Quality gates
- Provenance lint passes before client-facing handoff.
- Quantitative claims include mode, source tier, retrieval date, and artifact path.
- Inference and missing-data findings are excluded from health scores.
- Paid-media recommendations remain read-only unless a separate approved mutation workflow exists.
- Remaining source gaps are surfaced in `_data-gaps.md`.

### Provenance written
- `skill`
- `version`
- `data_mode`
- `source_tiers`
- `retrieval_dates`
- `collector_paths`
- `blocked_claims`
- `data_gaps`
- `recommended_next_skills`
- `quality_gate_scores`

### Example artifacts
- No committed example artifact found.

### Failure modes
- Missing connected data limits the audit to public or user-provided evidence.
- Partial ad, CRM, call, or analytics access can create a scorecard with gray sections.
- Weekly noise can look like a trend when sample size is low.
- Live channel changes are blocked unless separately approved.

### Competitive claim
This skill differs from generic weekly reports by separating source-backed facts, urgent flags, unsupported hypotheses, and next-step skill routing. It is designed for operating cadence, not vanity reporting.

