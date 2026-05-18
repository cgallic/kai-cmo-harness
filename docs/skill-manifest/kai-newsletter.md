---
name: kai-newsletter
version: 1.0.0
category: production
last_updated: 2026-05-18
---

# Kai Newsletter

### One-line claim
Plan and produce newsletter editions - content selection, subject lines, scheduling, and production with quality gates.

### Triggers
- newsletter
- plan newsletter
- newsletter content
- email newsletter
- weekly digest

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> newsletter edition plan and draft with subject lines, sections, links, CTA, and scheduling notes.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **FU-001** - "Score every publishable content artifact on Unique, Useful, Ultra-specific, and Urgent, with each dimension rated 1-4." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **FU-006** - "The default publishing threshold is 12/16 for blog, SEO, and article content, and 10/16 for ads and email. Any single U below 2 should block or force revision." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **VG-005** - "Tier 1 banned words and AI slop phrases hard-block publishable content until rewritten. Examples include "leverage", "utilize", "synergy", "in conclusion", and "in today's rapidly evolving"." Source: [scripts/quality_gates/banned_word_check.py](../../scripts/quality_gates/banned_word_check.py).
- **VG-006** - "Binary cliche patterns such as "X, not Y", "isn't X - it's Y", "Here's the thing", "I'll be honest", "Let that sink in", and "Hot take" fail the voice-pattern check unless they appear in comments or code fences." Source: [harness/skills/kai-gate/SKILL.md](../../harness/skills/kai-gate/SKILL.md).
- **VG-008** - "When a piece fails quality gates, fix the specific issues and re-score. Stop after two retry cycles and surface remaining failures." Source: [harness/skills/kai-write/SKILL.md](../../harness/skills/kai-write/SKILL.md).

### Dependencies
- [kai-email-system](./kai-email-system.md)

### Called by
- No other `kai-*` manifest page declares this skill as a dependency.

### Quality gates
- Four U's score meets threshold: 12/16 for strategic, SEO, article, and page work; 10/16 for ads and email; any single U below 2 blocks handoff.
- Banned-word, AI-slop, and voice-pattern checks pass with zero hard-blocking hits.
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

### Competitive claim
This skill differs from generic marketing AI by producing channel-shaped artifacts with format constraints, policy checks where applicable, and visible quality gates before handoff.
