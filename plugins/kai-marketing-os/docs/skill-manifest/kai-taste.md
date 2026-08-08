---
name: kai-taste
version: 1.0.0
category: measurement
last_updated: 2026-05-18
---

# Kai Taste

### One-line claim
Audit or design generative AI interfaces against three diagnostic pillars (deterministic-stochastic balance, interaction density, visual cohesion). Treats taste as a measurable control system, not subjective preference. Use when: 'taste audit', 'score this UI', 'design quality', 'interaction density', 'visual cohesion', 'refiner layer', 'correction cost', 'why does this feel off', 'polish this', 'design review', or building any user-facing AI product.

### Triggers
- Direct request for the workflow named by this skill.

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `subject` (URL, path, or description, required) - UI, AI product, flow, or generated output to audit/design.
- `mode` (enum, required) - `audit` or `design`.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> taste audit or design scorecard with three-pillar scores, failure modes, metrics, and prioritized fixes.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **TASTE-001** - "Treat taste as a control system that converts stochastic model output into reliable user outcomes with minimal correction cost. Taste remains subordinate to function." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).
- **TASTE-002** - "Score generative AI interfaces on three pillars: Deterministic-Stochastic Balance, Interaction Density, and Visual Cohesion." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).
- **TASTE-006** - "Scan every taste audit for the eight failure modes: stochastic over-constraint, density paralysis, cohesion rigidity, oracle polish, affordance collapse, interaction ceremony, trust distortion, and metric gaming." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).
- **TASTE-008** - "In audit mode, identify the subject, score each pillar from 1-10, scan failure modes, measure available metrics, output a scorecard, and prioritize fixes as P0/P1/P2." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).
- **TASTE-010** - "Instrument taste as a feedback loop and pair every optimization metric with a counter-metric to avoid metric gaming." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).

### Dependencies
- None declared. This skill can run as an entry workflow.

### Called by
- No other `kai-*` manifest page declares this skill as a dependency.

### Quality gates
- Taste scorecard covers deterministic-stochastic balance, interaction density, visual cohesion, failure modes, and measured fixes.
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

### Example artifacts
- No committed example artifact found.

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.
- AI-search visibility recommendations cannot promise citation, ranking, or answer inclusion.

### Competitive claim
This skill differs from generic marketing AI by separating evidence collection, scoring, data gaps, and recommendations so unsupported claims are visible.
