---
name: kai-growth-hacker
version: 1.0.0
category: strategy
last_updated: 2026-06-17
---

# Kai Growth Hacker

### One-line claim
Build a first-growth-hire distribution operating system across B2B and B2C channels, with channel scoring, specialist fan-out, test cards, approval gates, and routing into the Kai skill graph.

### Triggers
- growth hacker
- first growth hire
- distribution hire
- cover every channel
- channel hacking
- growth operator
- growth hacker OS
- fan out channel operators

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `business_type` (string, optional) - B2B, B2C, marketplace, local service, ecommerce, creator, or mixed.
- `stage` (string, optional) - pre-launch, first revenue, early growth, growth, or scale.
- `source_evidence` (files or URLs, optional) - analytics exports, CRM notes, screenshots, customer proof, policies, examples, or source packets.

### Outputs
- Artifact -> `workspace/growth-hacker/` brief, channel map, prioritization scorecard, 90-day sprint, agent fan-out plan, B2B/B2C test cards, asset backlog, creative ledger, outbound approval plan, creator/partner shortlist, metrics dashboard, decision log, data sources, data gaps, and quality report.
- Quality report -> pass/fail status for relevant gates, blocked live actions, missing access, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `business_type`, `stage`, `channels_scored`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **FU-004** - "Ultra-specific means the artifact contains exact numbers, named tools, real examples, timeframes, outcomes, or other concrete details." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **POL-001** - Platform policy references must be loaded before ad, creator, sponsorship, affiliate, or platform-bound social execution.

### Dependencies
- [kai-growth-plan](./kai-growth-plan.md)
- [kai-social](./kai-social.md)
- [kai-write](./kai-write.md)
- [kai-content-calendar](./kai-content-calendar.md)
- [kai-topical-map](./kai-topical-map.md)
- [kai-surround-sound](./kai-surround-sound.md)
- [kai-sdr-operator](./kai-sdr-operator.md)
- [kai-cold-outreach](./kai-cold-outreach.md)
- [kai-influencer](./kai-influencer.md)
- [kai-ad-campaign](./kai-ad-campaign.md)
- [kai-retarget](./kai-retarget.md)
- [kai-webinar](./kai-webinar.md)
- [kai-partnership](./kai-partnership.md)
- [kai-email-system](./kai-email-system.md)
- [kai-analytics](./kai-analytics.md)
- [kai-gate](./kai-gate.md)

### Called by
- [kai](./README.md)
- [kai-start](./kai-start.md)
- [kai-growth-plan](./kai-growth-plan.md)

### Quality gates
- Banned-word check passes on customer-facing markdown.
- Four U's score meets threshold: 12/16 for strategic, content, page, and channel-test work; 10/16 for ads, email, and outreach.
- SEO lint passes for SEO/AEO pages.
- Agent-readiness lint runs before AEO/surround-sound execution.
- Platform policy and advertising compliance references are loaded before ad, sponsorship, affiliate, creator, or paid-social assets.
- Provenance lint applies to audit-like reports and quantitative client-facing claims.
- Live actions remain blocked until explicit approval is recorded.

### Provenance written
- `skill` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `version` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `frameworks_loaded` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `rule_ids_evaluated` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `business_type` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `stage` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `channels_scored` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `quality_gate_scores` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `source_files_loaded` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `data_gaps` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `data_mode` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `source_tiers` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `retrieval_dates` - written into the artifact, quality report, or run sidecar when the workflow is saved.
- `blocked_live_actions` - written into the artifact, quality report, or run sidecar when the workflow is saved.

### Example artifacts
No committed example artifact found.

### Failure modes
- Missing `MARKETING.md` causes the channel map to rely on assumptions.
- Missing analytics or CRM access limits prioritization to hypotheses.
- Platform policy uncertainty blocks paid, creator, sponsorship, affiliate, and outbound execution.
- AEO recommendations cannot promise citation, ranking, or answer inclusion.
- Creator and UGC plans are blocked when rights, disclosure, or AI/synthetic-media status is unclear.
- Outbound plans are blocked when lead source, suppression, sender, or lawful-basis fields are missing.

### Competitive claim
This skill differs from generic growth brainstorming by turning channel ideas into a scored operating system with specialist queues, explicit live-action gates, and downstream Kai skill routing.
