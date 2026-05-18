---
name: kai-landing-page
version: 1.0.0
category: production
last_updated: 2026-05-18
---

# Kai Landing Page

### One-line claim
Produce complete landing page copy using perception engineering and conversion frameworks. Generates hero section, value props, social proof blocks, objection handlers, and CTA - all scored against quality gates.

### Triggers
- landing page
- sales page
- LP copy
- write a landing page
- hero section
- conversion page
- signup page

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `conversion_goal` (string, required) - signup, demo, purchase, waitlist, or phone call.
- `traffic_source` (string, optional) - cold, warm, hot, paid, organic, referral, or mixed.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> `workspace/landing-pages/<product-slug>.md` page copy with hero, problem, solution, proof, objections, FAQ, CTA, and gate scores.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **PE-002** - "Use Perception-layer moves to destabilize the old explanation loop before installing a new action path." Source: [knowledge/frameworks/content-copywriting/perception-engineering.md](../../knowledge/frameworks/content-copywriting/perception-engineering.md).
- **PE-005** - "Shift the context genre when facts alone will not change behavior. Move the interaction from Exam, Boardroom, or Crisis into a more useful genre such as Lab when experimentation is needed." Source: [knowledge/frameworks/content-copywriting/perception-engineering.md](../../knowledge/frameworks/content-copywriting/perception-engineering.md).
- **PE-007** - "Use Permission-layer moves to reduce imagined penalties through future pacing, authority framing, or double binds that keep choices inside the desired action path." Source: [knowledge/frameworks/content-copywriting/perception-engineering.md](../../knowledge/frameworks/content-copywriting/perception-engineering.md).
- **FU-006** - "The default publishing threshold is 12/16 for blog, SEO, and article content, and 10/16 for ads and email. Any single U below 2 should block or force revision." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **VG-005** - "Tier 1 banned words and AI slop phrases hard-block publishable content until rewritten. Examples include "leverage", "utilize", "synergy", "in conclusion", and "in today's rapidly evolving"." Source: [scripts/quality_gates/banned_word_check.py](../../scripts/quality_gates/banned_word_check.py).

### Dependencies
- [kai-email-system](./kai-email-system.md)

### Called by
- [kai-audit](./kai-audit.md)
- [kai-growth-plan](./kai-growth-plan.md)
- [kai-launch](./kai-launch.md)
- [kai-product-maker](./kai-product-maker.md)

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
- [launch landing page copy](../../workspace/launch/landing-page/copy.md)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.

### Competitive claim
This skill differs from generic marketing AI by producing channel-shaped artifacts with format constraints, policy checks where applicable, and visible quality gates before handoff.
