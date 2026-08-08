---
name: kai-topical-map
version: 1.0.0
category: strategy
last_updated: 2026-05-18
---

# Kai Topical Map

### One-line claim
Build an AEO-first topical map optimized for AI search citation - entity clusters, query fan-out coverage, information gain scoring, and multi-platform distribution. Produces entity map, content node architecture, schema blueprint, and 90-day publishing calendar.

### Triggers
- topical map
- content architecture
- site structure
- topic clusters
- pillar content plan
- AEO map
- AI search architecture
- entity map
- what content should we build

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `topic_space` (string, required) - domain, category, or entity set to map.
- `seed_entities` (array, optional) - products, problems, competitors, methods, people, and categories.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> `workspace/topical-map/` entity map, fan-out matrix, content nodes, schema blueprint, information-gain audit, distribution plan, and 90-day calendar.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **QDQ-001** - "Classify a topic as QDP, QDH, or QDS before assigning URL, heading, or sentence treatment." Source: [knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md](../../knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md).
- **QDQ-002** - "Use QDP when a topic meets at least three of four query criteria and index criteria support a dedicated page." Source: [knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md](../../knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md).
- **QDQ-003** - "Use QDH when demand or intent exists but the topic does not justify a dedicated URL. Place it as a clear section under the stronger parent page." Source: [knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md](../../knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md).
- **QDQ-004** - "Use QDS when the topic is needed for completeness but has minimal independent search signal. Cover it in a sentence or short passage." Source: [knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md](../../knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md).
- **AEO-004** - "Add non-commodity value through original data, expert review, firsthand experience, public datasets, local/product details, or clearer synthesis. Do not publish longer paraphrases of the top results." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **AEO-007** - "Report AI visibility as probabilistic. Measure citations, mentions, answer absorption, referrals, clicks, and conversions with method notes and confidence. Do not guarantee inclusion or ranking in AI assistants." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **AEO-001** - "Attach an evidence tier to every AEO recommendation. Use Tier 1 for official requirements, Tier 2 for official guidance, Tier 3 for academic research, Tier 4 for patents or system disclosures, Tier 7 for internal measurement, Tier 8 for hypothesis, and Tier 9 for missing data." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **AEO-005** - "Design passages to be retrievable: use self-contained section-answer pairs, descriptive headings, tables, definitions, examples, and visible HTML." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).

### Dependencies
- [kai-content-calendar](./kai-content-calendar.md)
- [kai-email-system](./kai-email-system.md)
- [kai-seo-audit](./kai-seo-audit.md)
- [kai-surround-sound](./kai-surround-sound.md)
- [kai-write](./kai-write.md)

### Called by
- No other `kai-*` manifest page declares this skill as a dependency.

### Quality gates
- AEO or agent-readiness checks pass where applicable; AI visibility claims stay probabilistic and sourced.
- QDP/QDH/QDS classification is explicit before assigning page, heading, or sentence treatment.
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
- No committed example artifact found.

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.
- Creative production can stop at planning or copy when source assets, channel access, or approval inputs are unavailable.

### Competitive claim
This skill differs from generic marketing AI by binding strategy to named frameworks, explicit inputs, downstream skill routing, and documented gates instead of producing an isolated brainstorm. It does not claim guaranteed AI Overview, ChatGPT, Perplexity, or ranking lifts.
