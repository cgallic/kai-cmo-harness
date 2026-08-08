---
name: kai-budget
version: 1.0.0
category: strategy
last_updated: 2026-05-18
---

# Kai Budget

### One-line claim
Marketing budget planning and forecasting - channel allocation, CAC targets, ROI projections, and spend optimization.

### Triggers
- marketing budget
- budget planning
- channel allocation
- marketing spend
- CAC forecast
- budget forecast
- how much should I spend
- allocate budget

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `stage` (string, required) - pre-launch, launch, growth, or scale.
- `unit_economics` (object, optional) - CAC, LTV, payback, MRR, margin, pipeline, or conversion inputs.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> budget allocation model, ROI scenarios, spend ramp plan, and optimization recommendations.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **FU-004** - "Ultra-specific means the artifact contains exact numbers, named tools, real examples, timeframes, outcomes, or other concrete details." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).

### Dependencies
- [kai-email-system](./kai-email-system.md)

### Called by
- No other `kai-*` manifest page declares this skill as a dependency.

### Quality gates
- Four U's score meets threshold: 12/16 for strategic, SEO, article, and page work; 10/16 for ads and email; any single U below 2 blocks handoff.
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
- [growth budget allocation](../../workspace/growth-plan/_budget-allocation.md)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.

### Competitive claim
This skill differs from generic marketing AI by binding strategy to named frameworks, explicit inputs, downstream skill routing, and documented gates instead of producing an isolated brainstorm.
