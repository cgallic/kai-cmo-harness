---
name: kai-data-dashboard
version: 1.0.0
category: measurement
last_updated: 2026-05-27
---

# Kai Data Dashboard

### One-line claim
Convert Kai workflow data, CSV exports, audit folders, SDR package outputs, and marketing reports into dashboard-ready specs or lightweight static dashboard surfaces.

### Triggers
- data dashboard
- operator dashboard
- operator room
- HTML operators room
- sales dashboard
- SDR dashboard
- turn this data into a dashboard
- dashboard handoff
- visualize Kai data

### Inputs
- `source_folder` (directory, required) - SDR package, audit folder, report folder, or other Kai workspace data folder.
- `_data_sources` (file, optional) - `_data-sources.md` or equivalent source map.
- `_data_gaps` (file, optional) - `_data-gaps.md` or equivalent gap list.
- `data_files` (files, required) - `kai-data.json`, `audit-data.json`, CSV exports, markdown reports, or user-provided metrics.
- `dashboard_type` (string, optional) - `sdr_operator_room`, `marketing_ops`, `executive_scorecard`, `audit_delivery`, or `connector_health`.
- `delivery_context` (string, optional) - client, internal, sales, onboarding, board, founder, or operator review.

### Outputs
- Artifact -> `<source-folder>/dashboard/dashboard-spec.md`.
- Artifact -> `<source-folder>/dashboard/metrics-dictionary.md`.
- Artifact -> `<source-folder>/dashboard/data-contract.json`.
- Artifact -> `<source-folder>/dashboard/source-map.md`.
- Artifact -> `<source-folder>/dashboard/data-gaps.md`.
- Optional artifact -> `<source-folder>/dashboard/index.html`.
- Quality report -> source coverage, placeholder status, metric definition status, responsive review notes, and data-gap summary.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md).

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-008** - "Missing credentials or unavailable sources must produce `_data-gaps.md` entries. Do not replace missing sources with estimates or placeholder metrics." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **AEO-005** - "Design passages to be retrievable: use self-contained section-answer pairs, descriptive headings, tables, definitions, examples, and visible HTML." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **AEO-010** - "Do not hide critical facts inside images, videos, PDFs, canvases, accordions, modals, or client-side rendering without equivalent visible text." Source: [knowledge/checklists/agent-readiness-checklist.md](../../knowledge/checklists/agent-readiness-checklist.md).
- **TASTE-005** - "For Visual Cohesion, require component grammar, semantic structure before styling, protected affordances, consistent tokens, and generated output that fits the surrounding UI." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).

### Dependencies
- [kai-analytics](./kai-analytics.md)
- [kai-html-presentation](./kai-html-presentation.md)
- [kai-sdr-operator](./kai-sdr-operator.md)
- [kai-gate](./kai-gate.md)

### Called by
- [kai-sdr-operator](./kai-sdr-operator.md)
- [kai-weekly-audit](./kai-weekly-audit.md)
- [kai-monthly-audit](./kai-monthly-audit.md)

### Quality gates
- Every number has a source, retrieval date, or `internal_demo` label.
- Every metric has a definition or formula.
- Data gaps are visible in the dashboard spec and any HTML output.
- Placeholder text is removed.
- Sensitive fields are excluded, masked, or explicitly approved.
- Static HTML, when produced, is readable on desktop and mobile.

### Provenance written
- `skill`
- `version`
- `source_folder`
- `dashboard_type`
- `data_mode`
- `source_files_loaded`
- `metrics_defined`
- `data_gaps`
- `placeholder_status`
- `quality_gate_scores`

### Example artifacts
- No committed example artifact found.

### Failure modes
- Source data may be too thin for a meaningful dashboard.
- Missing `_data-sources.md` or `_data-gaps.md` forces a source-map reconstruction step.
- User-provided metrics may need formulas before they can be dashboarded.
- Static HTML may be deferred when the user only asked for a dashboard handoff spec.

### Competitive claim
This skill differs from generic dashboard generation by preserving source provenance, data gaps, metric definitions, and handoff structure before any UI is built.
