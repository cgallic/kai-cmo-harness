---
name: kai-html-presentation
version: 1.0.0
category: production
last_updated: 2026-05-22
---

# Kai HTML Presentation

### One-line claim
Client-ready HTML presentation builder for Kai audit and report folders. Converts weekly audits, monthly audits, marketing reports, scorecards, findings, data-source notes, and action plans into a polished single-file HTML deck with sourced metrics, executive slides, speaker notes, and delivery-ready styling.

### Triggers
- HTML presentation
- HTML deck
- client-ready audit deck
- turn this audit into slides
- present the weekly audit
- present the monthly audit
- deliver Kai reports as HTML slides

### Inputs
- `source_folder` (directory, required) - audit or report folder containing source-backed findings.
- `_data_sources` (file, required) - `_data-sources.md`.
- `_data_gaps` (file, required) - `_data-gaps.md`.
- `audit_data` (file, optional) - `audit-data.json` or `kai-data.json`.
- `report_files` (files, required) - executive summary, scorecard, findings, action plan, or equivalent.
- `delivery_context` (string, optional) - client, internal, sales, onboarding, board, or team review.

### Outputs
- Artifact -> `<source-folder>/html-presentation/index.html`.
- Optional artifact -> `<source-folder>/html-presentation/notes.md`.
- Quality report -> provenance lint status, placeholder check, source-footer check, and responsive review notes.
- Sidecar fields -> `skill`, `version`, `source_folder`, `data_mode`, `source_files_loaded`, `slides_generated`, `data_gaps_included`, and `placeholder_status`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md).

- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-010** - "Run `python scripts/quality_gates/audit_provenance_lint.py <audit-folder> --audit-dir` before audit or deck handoff." Source: [scripts/quality_gates/audit_provenance_lint.py](../../scripts/quality_gates/audit_provenance_lint.py).
- **AEO-005** - "Design passages to be retrievable: use self-contained section-answer pairs, descriptive headings, tables, definitions, examples, and visible HTML." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **AEO-010** - "Do not hide critical facts inside images, videos, PDFs, canvases, accordions, modals, or client-side rendering without equivalent visible text." Source: [knowledge/checklists/agent-readiness-checklist.md](../../knowledge/checklists/agent-readiness-checklist.md).
- **TASTE-005** - "For Visual Cohesion, require component grammar, semantic structure before styling, protected affordances, consistent tokens, and generated output that fits the surrounding UI." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).

### Dependencies
- [kai-audit](./kai-audit.md)
- [kai-weekly-audit](./kai-weekly-audit.md)
- [kai-monthly-audit](./kai-monthly-audit.md)
- [kai-seo-audit](./kai-seo-audit.md)
- [kai-cro](./kai-cro.md)

### Called by
- [kai-weekly-audit](./kai-weekly-audit.md)
- [kai-monthly-audit](./kai-monthly-audit.md)

### Quality gates
- Audit provenance lint passes when the source folder is an audit.
- No placeholder tokens remain in `index.html`.
- Every slide with a number includes a source footer.
- `_data-gaps.md` is represented in the deck.
- Desktop and mobile layouts remain readable.

### Provenance written
- `skill`
- `version`
- `source_folder`
- `data_mode`
- `source_files_loaded`
- `slides_generated`
- `data_gaps_included`
- `placeholder_status`
- `quality_gate_scores`

### Example artifacts
- No committed example artifact found.

### Failure modes
- Source artifacts may lack enough evidence for a client-ready deck.
- Missing `_data-sources.md` or `_data-gaps.md` blocks delivery.
- Placeholder text can survive if the deck is copied but not filled.
- Long tables may need pruning or splitting for mobile readability.

### Competitive claim
This skill differs from generic slide generation by preserving audit provenance inside the presentation. The deck is not allowed to invent a story; it must inherit the evidence, data gaps, and decisions already present in the source folder.

