---
name: kai-daily-ad-review
version: 1.0.0
category: measurement
last_updated: 2026-05-18
---

# Kai Daily Ad Review

### One-line claim
Daily ad performance check-in across platforms. Pulls live metrics from Meta, Google, and LinkedIn via deterministic scripts, compares against benchmarks and previous period, flags overspend/underperformers/policy issues, and outputs a quick daily summary with action items.

### Triggers
- daily ad review
- how are my ads doing today
- ad check-in
- morning ad report
- daily ad summary
- check ad performance
- ad dashboard
- daily ads

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `platform_exports` (files, optional) - Meta, Google, LinkedIn, and PostHog pulls from deterministic scripts.
- `date_range` (string, optional) - daily review period and comparison window.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> daily ad summary with metrics, trend flags, issues, and action items.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **POL-001** - "Load the platform policy reference before writing ad copy or creating paid-media payloads for that platform." Source: [harness/skills/kai-ad-campaign/SKILL.md](../../harness/skills/kai-ad-campaign/SKILL.md).
- **POL-005** - "Paid-media evaluation starts read-only. Pull, validate, flag, recommend, and produce dry-run payloads without mutating campaigns." Source: [harness/references/ad-write-guardrails.md](../../harness/references/ad-write-guardrails.md).
- **POL-006** - "No paid-media write action should auto-execute. Human approval is required for creating, publishing, pausing, activating, bid changes, budget changes, targeting changes, asset uploads, and keyword mutations." Source: [harness/references/ad-write-guardrails.md](../../harness/references/ad-write-guardrails.md).
- **POL-007** - "New ads and campaigns must be created in `PAUSED` or draft state. Activation is a separate action with separate approval." Source: [harness/references/ad-write-guardrails.md](../../harness/references/ad-write-guardrails.md).
- **POL-010** - "Block paid-media mutation when evidence, measurement label, rights/disclosures, before/after diff, rollback instructions, account allowlist, or cap compliance is missing. Also block create/upload actions that set status to `ACTIVE`." Source: [harness/references/ad-write-guardrails.md](../../harness/references/ad-write-guardrails.md).
- **FU-006** - "The default publishing threshold is 12/16 for blog, SEO, and article content, and 10/16 for ads and email. Any single U below 2 should block or force revision." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).

### Dependencies
- [kai-ad-campaign](./kai-ad-campaign.md)

### Called by
- No other `kai-*` manifest page declares this skill as a dependency.

### Quality gates
- Four U's score meets threshold: 12/16 for strategic, SEO, article, and page work; 10/16 for ads and email; any single U below 2 blocks handoff.
- Platform policy and paid-media write-access controls pass; live mutation requires human approval.
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
- `policy_references` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `approval_state` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `rights_or_disclosure_evidence` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.

### Example artifacts
- No committed example artifact found.

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.
- Creative production can stop at planning or copy when source assets, channel access, or approval inputs are unavailable.

### Competitive claim
This skill differs from generic marketing AI by separating evidence collection, scoring, data gaps, and recommendations so unsupported claims are visible. It keeps evaluation separate from live channel mutation unless approval and credentials are present.
