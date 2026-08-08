---
name: kai-brand
version: 1.0.0
category: strategy
last_updated: 2026-05-18
---

# Kai Brand

### One-line claim
Brand positioning workshop - define messaging framework, voice/tone, differentiation strategy, and taglines.

### Triggers
- brand positioning
- messaging framework
- brand voice
- how should we position ourselves
- differentiation
- tagline

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> messaging framework, voice/tone guidelines, differentiation map, and tagline options.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **PE-001** - "Before persuasion, identify the cached prediction or identity label that explains the subject's current refusal, hesitation, or avoidance." Source: [knowledge/frameworks/content-copywriting/perception-engineering.md](../../knowledge/frameworks/content-copywriting/perception-engineering.md).
- **PE-002** - "Use Perception-layer moves to destabilize the old explanation loop before installing a new action path." Source: [knowledge/frameworks/content-copywriting/perception-engineering.md](../../knowledge/frameworks/content-copywriting/perception-engineering.md).
- **FU-002** - "Unique means the artifact is not interchangeable with competitor content because it contains specific experience, proprietary data, a contrarian frame, brand voice, or a combination others have not connected." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **FU-004** - "Ultra-specific means the artifact contains exact numbers, named tools, real examples, timeframes, outcomes, or other concrete details." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **VG-005** - "Tier 1 banned words and AI slop phrases hard-block publishable content until rewritten. Examples include "leverage", "utilize", "synergy", "in conclusion", and "in today's rapidly evolving"." Source: [scripts/quality_gates/banned_word_check.py](../../scripts/quality_gates/banned_word_check.py).

### Dependencies
- [kai-email-system](./kai-email-system.md)

### Called by
- [kai-product-maker](./kai-product-maker.md)
- [kai-reddit-listen](./kai-reddit-listen.md)

### Quality gates
- Four U's score meets threshold: 12/16 for strategic, SEO, article, and page work; 10/16 for ads and email; any single U below 2 blocks handoff.
- Banned-word, AI-slop, and voice-pattern checks pass with zero hard-blocking hits.
- Perception Engineering checklist passes: old belief, context shift, proof, objection handling, and CTA are explicit.
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
- [launch messaging guide](../../workspace/launch/_messaging-guide.md)
- [growth messaging framework](../../workspace/growth-plan/_messaging-framework.md)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.

### Competitive claim
This skill differs from generic marketing AI by binding strategy to named frameworks, explicit inputs, downstream skill routing, and documented gates instead of producing an isolated brainstorm.
