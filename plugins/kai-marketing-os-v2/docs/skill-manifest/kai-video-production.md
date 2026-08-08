---
name: kai-video-production
version: 1.0.0
category: production
last_updated: 2026-05-18
---

# Kai Video Production

### One-line claim
Full-stack video production from script to rendered video. Combines script generation (optimized for TikTok/YouTube/Reels) with AI-powered video rendering using Remotion, AI voiceovers (Qwen3-TTS/ElevenLabs), music generation (ACE-Step), and browser-based demo recording. Multi-session project tracking with automatic intent reconciliation.

### Triggers
- create video
- produce video
- demo video
- product video

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `script_or_brief` (file or string, required) - approved video script, demo brief, or production concept.
- `assets` (array, optional) - screenshots, product media, voice, music, brand tokens, demo URL, or captions.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> rendered-video production package or production plan with script, assets, voice/music/render path, project state, and verification notes.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **TASTE-001** - "Treat taste as a control system that converts stochastic model output into reliable user outcomes with minimal correction cost. Taste remains subordinate to function." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).
- **TASTE-005** - "For Visual Cohesion, require component grammar, semantic structure before styling, protected affordances, consistent tokens, and generated output that fits the surrounding UI." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).
- **TASTE-010** - "Instrument taste as a feedback loop and pair every optimization metric with a counter-metric to avoid metric gaming." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).
- **VG-005** - "Tier 1 banned words and AI slop phrases hard-block publishable content until rewritten. Examples include "leverage", "utilize", "synergy", "in conclusion", and "in today's rapidly evolving"." Source: [scripts/quality_gates/banned_word_check.py](../../scripts/quality_gates/banned_word_check.py).
- **FU-006** - "The default publishing threshold is 12/16 for blog, SEO, and article content, and 10/16 for ads and email. Any single U below 2 should block or force revision." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).

### Dependencies
- [kai-analytics](./kai-analytics.md)
- [kai-content-calendar](./kai-content-calendar.md)
- [kai-email-system](./kai-email-system.md)
- [kai-repurpose](./kai-repurpose.md)
- [kai-social](./kai-social.md)
- [kai-video](./kai-video.md)

### Called by
- [kai-product-maker](./kai-product-maker.md)

### Quality gates
- Four U's score meets threshold: 12/16 for strategic, SEO, article, and page work; 10/16 for ads and email; any single U below 2 blocks handoff.
- Banned-word, AI-slop, and voice-pattern checks pass with zero hard-blocking hits.
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
- [KaiCalls demo video test script](../../workspace/video-test-script.md)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.
- Video production can stop at script or scene plan when rendering dependencies or media assets are unavailable.

### Competitive claim
This skill differs from generic marketing AI by producing channel-shaped artifacts with format constraints, policy checks where applicable, and visible quality gates before handoff.
