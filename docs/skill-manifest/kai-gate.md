---
name: kai-gate
version: 1.0.0
category: measurement
last_updated: 2026-05-18
---

# Kai Gate

### One-line claim
Run Kai CMO Harness quality gates on content. Scores Four U's (Unique/Useful/Ultra-specific/Urgent), checks for banned words and AI slop, runs SEO lint for search content.

### Triggers
- score this
- quality check
- run quality gates
- check this content
- four u's score
- banned word check
- SEO lint

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> quality gate report with Four U score, banned-word result, voice-pattern check, SEO lint when applicable, and pass/fail status.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **FU-001** - "Score every publishable content artifact on Unique, Useful, Ultra-specific, and Urgent, with each dimension rated 1-4." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **FU-006** - "The default publishing threshold is 12/16 for blog, SEO, and article content, and 10/16 for ads and email. Any single U below 2 should block or force revision." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **VG-005** - "Tier 1 banned words and AI slop phrases hard-block publishable content until rewritten. Examples include "leverage", "utilize", "synergy", "in conclusion", and "in today's rapidly evolving"." Source: [scripts/quality_gates/banned_word_check.py](../../scripts/quality_gates/banned_word_check.py).
- **VG-006** - "Binary cliche patterns such as "X, not Y", "isn't X - it's Y", "Here's the thing", "I'll be honest", "Let that sink in", and "Hot take" fail the voice-pattern check unless they appear in comments or code fences." Source: [harness/skills/kai-gate/SKILL.md](../../harness/skills/kai-gate/SKILL.md).
- **AA-005** - "Keep sentences short and split compound explanations into separate sentences when the average sentence length exceeds roughly 20 words." Source: [knowledge/frameworks/content-copywriting/algorithmic-authorship.md](../../knowledge/frameworks/content-copywriting/algorithmic-authorship.md).
- **AA-010** - "Bold the answer span, not the query-matching term, when emphasis is used for search-oriented content." Source: [knowledge/frameworks/content-copywriting/algorithmic-authorship.md](../../knowledge/frameworks/content-copywriting/algorithmic-authorship.md).

### Dependencies
- None declared. This skill can run as an entry workflow.

### Called by
- [kai-product-maker](./kai-product-maker.md)
- [kai-reddit-listen](./kai-reddit-listen.md)

### Quality gates
- Four U's score meets threshold: 12/16 for strategic, SEO, article, and page work; 10/16 for ads and email; any single U below 2 blocks handoff.
- Banned-word, AI-slop, and voice-pattern checks pass with zero hard-blocking hits.
- SEO lint passes when the artifact targets search or answer extraction.
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
- [launch quality report](../../workspace/launch/_quality-report.md)
- [Northstar email quality report](../../workspace/demo-clients/northstar-media-lab/emails/_quality-report.md)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.

### Competitive claim
This skill differs from generic marketing AI by separating evidence collection, scoring, data gaps, and recommendations so unsupported claims are visible.
