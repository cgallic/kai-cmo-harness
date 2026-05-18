---
name: kai-cro
version: 1.0.0
category: measurement
last_updated: 2026-05-18
---

# Kai CRO

### One-line claim
Conversion rate optimization audit - analyze a landing page, signup flow, or checkout funnel using the 5-layer CRO stack (technical performance, traffic quality, offer/pricing, design/layout, copy/messaging). Produces prioritized fix list with expected impact.

### Triggers
- CRO audit
- conversion audit
- why isn't this converting
- improve conversion rate
- landing page not converting
- optimize funnel
- signup flow audit

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `page_or_funnel` (URL or path, required) - landing page, signup flow, checkout, or conversion path.
- `conversion_goal` (string, required) - signup, demo, purchase, call, waitlist, or lead.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> CRO audit with 5-layer diagnosis, scores, prioritized fixes, and test ideas.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-005** - "Run `python -m scripts.audit.collect --url <url> --mode <mode> --workflow <workflow> --out <data-folder>` before using numbers in data-backed workflows." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-008** - "Missing credentials or unavailable sources must produce `_data-gaps.md` entries. Do not replace missing sources with estimates or placeholder metrics." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-010** - "Run `python scripts/quality_gates/audit_provenance_lint.py <audit-folder> --audit-dir` before audit or deck handoff." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PE-005** - "Shift the context genre when facts alone will not change behavior. Move the interaction from Exam, Boardroom, or Crisis into a more useful genre such as Lab when experimentation is needed." Source: [knowledge/frameworks/content-copywriting/perception-engineering.md](../../knowledge/frameworks/content-copywriting/perception-engineering.md).

### Dependencies
- [kai-email-system](./kai-email-system.md)

### Called by
- No other `kai-*` manifest page declares this skill as a dependency.

### Quality gates
- Perception Engineering checklist passes: old belief, context shift, proof, objection handling, and CTA are explicit.
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
- [Andon Window Cleaning review bundle](../superpowers/specs/2026-04-02-andon-window-cleaning-review-bundle.md)
- [launch landing page copy](../../workspace/launch/landing-page/copy.md)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.

### Competitive claim
This skill differs from generic marketing AI by separating evidence collection, scoring, data gaps, and recommendations so unsupported claims are visible.
