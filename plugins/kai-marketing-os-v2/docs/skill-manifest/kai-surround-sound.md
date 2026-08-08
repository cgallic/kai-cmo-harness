---
name: kai-surround-sound
version: 1.0.0
category: measurement
last_updated: 2026-05-18
---

# Kai Surround Sound

### One-line claim
LLM brand manipulation - build a consensus web so ChatGPT, Claude, Perplexity, and Google AI Overviews mention your brand when people ask about your category. Uses surround sound methodology, entity SEO, and LLM citation science.

### Triggers
- get mentioned in AI
- LLM brand presence
- surround sound
- AI search visibility
- Perplexity ranking
- ChatGPT mentions
- AI Overview inclusion
- entity authority
- brand mentions in AI

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `brand_or_entity` (string, required) - entity to evaluate across AI-search and citation surfaces.
- `category_queries` (array, required) - prompts/searches used to test consensus and visibility.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> AI-search visibility and consensus-web plan with provider matrix, citations/mentions observed, agent-readiness notes, and caveats.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **AEO-001** - "Attach an evidence tier to every AEO recommendation. Use Tier 1 for official requirements, Tier 2 for official guidance, Tier 3 for academic research, Tier 4 for patents or system disclosures, Tier 7 for internal measurement, Tier 8 for hypothesis, and Tier 9 for missing data." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **AEO-002** - "Treat AI visibility as multi-engine. Build a provider matrix for Google, ChatGPT/OpenAI, Claude/Anthropic, Perplexity, Bing/Copilot, and Grok/X before changing crawl policy." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **AEO-003** - "Treat Google AI Overview and AI Mode work as SEO grounded in normal crawlability, indexability, snippet eligibility, and quality systems. Do not present `llms.txt`, special AI schema, or forced chunking as Google requirements." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **AEO-005** - "Design passages to be retrievable: use self-contained section-answer pairs, descriptive headings, tables, definitions, examples, and visible HTML." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **AEO-008** - "Agent-readiness audits must pass all P0 crawler, machine-readable docs, and non-JS content checks before site-level AEO or surround-sound planning proceeds." Source: [knowledge/checklists/agent-readiness-checklist.md](../../knowledge/checklists/agent-readiness-checklist.md).
- **AEO-009** - "Publish product capabilities, ICP, primary actions, integration surface, auth model, pricing model, approval flow, and run lifecycle in plain text where agents can read them." Source: [knowledge/checklists/agent-readiness-checklist.md](../../knowledge/checklists/agent-readiness-checklist.md).
- **PROV-008** - "Missing credentials or unavailable sources must produce `_data-gaps.md` entries. Do not replace missing sources with estimates or placeholder metrics." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).

### Dependencies
- [kai-content-calendar](./kai-content-calendar.md)
- [kai-email-system](./kai-email-system.md)

### Called by
- [kai-audit](./kai-audit.md)
- [kai-growth-plan](./kai-growth-plan.md)
- [kai-start](./kai-start.md)
- [kai-topical-map](./kai-topical-map.md)

### Quality gates
- Provenance lint passes; quantitative/client-facing claims include mode, source tier, retrieval date, and data-gap handling.
- AEO or agent-readiness checks pass where applicable; AI visibility claims stay probabilistic and sourced.
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
- [agent-readiness audit](../AGENT_READINESS_AUDIT.md)
- [agentic world gap plan](../../workspace/agentic-world-gap-plan-2026-05-15.md)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.
- Creative production can stop at planning or copy when source assets, channel access, or approval inputs are unavailable.
- AI-search visibility recommendations cannot promise citation, ranking, or answer inclusion.

### Competitive claim
This skill differs from generic marketing AI by binding strategy to named frameworks, explicit inputs, downstream skill routing, and documented gates instead of producing an isolated brainstorm. It does not claim guaranteed AI Overview, ChatGPT, Perplexity, or ranking lifts.
