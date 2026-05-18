---
name: kai-seo-audit
version: 1.0.0
category: measurement
last_updated: 2026-05-18
---

# Kai SEO Audit

### One-line claim
One-click technical SEO audit of a website. Runs the full technical SEO audit SOP - crawlability, indexation, Core Web Vitals, schema markup, internal linking, mobile UX, and content quality. Outputs a prioritized fix list.

### Triggers
- SEO audit
- technical SEO
- site audit
- crawl issues
- indexation problems
- why aren't we ranking
- SEO health check

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `audit_mode` (enum, required) - `sales_external`, `onboarding_connected`, or `internal_demo`.
- `target_url` (URL, required) - site or section to crawl and evaluate.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> `workspace/seo-audit/` health score, findings, data sources, data gaps, prioritized fixes, and provenance lint result.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-005** - "Run `python -m scripts.audit.collect --url <url> --mode <mode> --workflow <workflow> --out <data-folder>` before using numbers in data-backed workflows." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-008** - "Missing credentials or unavailable sources must produce `_data-gaps.md` entries. Do not replace missing sources with estimates or placeholder metrics." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-010** - "Run `python scripts/quality_gates/audit_provenance_lint.py <audit-folder> --audit-dir` before audit or deck handoff." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).

### Dependencies
- [kai-email-system](./kai-email-system.md)

### Called by
- [kai-audit](./kai-audit.md)
- [kai-growth-plan](./kai-growth-plan.md)
- [kai-start](./kai-start.md)
- [kai-topical-map](./kai-topical-map.md)

### Quality gates
- Provenance lint passes; quantitative/client-facing claims include mode, source tier, retrieval date, and data-gap handling.
- After two failed retry cycles, remaining failures are surfaced instead of hidden.

### Provenance written
- `skill` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `version` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `frameworks_loaded` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `rule_ids_evaluated` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `persona_or_audience` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `quality_gate_scores` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `source_files_loaded` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `data_gaps` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `data_mode` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `source_tiers` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `retrieval_dates` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `collector_paths` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `blocked_claims` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.

### Example artifacts
- [SEO check-in report](../SEO_CHECKIN_2026-03-29.md)
- [agent-readiness audit](../AGENT_READINESS_AUDIT.md)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.
- Creative production can stop at planning or copy when source assets, channel access, or approval inputs are unavailable.

### Competitive claim
This skill differs from generic marketing AI by separating evidence collection, scoring, data gaps, and recommendations so unsupported claims are visible. It does not claim guaranteed AI Overview, ChatGPT, Perplexity, or ranking lifts.
