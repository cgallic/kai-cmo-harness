---
name: kai-email-system
version: 1.0.0
category: lifecycle
last_updated: 2026-05-18
---

# Kai Email System

### One-line claim
Plan and batch-produce an entire email system for a product. Maps every lifecycle touchpoint (onboarding, activation, conversion, retention, transactional, win-back), generates all emails with quality gates, outputs Loops-ready copy.

### Triggers
- create all emails
- email system
- build email sequences
- lifecycle emails
- onboarding sequence
- set up transactional emails
- plan all the emails for [product]

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `segments` (array, required) - lifecycle, user, buyer, or behavior segments.
- `email_types` (array, optional) - onboarding, activation, conversion, retention, transactional, win-back, or sales.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> `workspace/emails/` email map, Loops-ready lifecycle emails, setup notes, and quality report.
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
- None declared. This skill can run as an entry workflow.

### Called by
- [kai-abm](./kai-abm.md)
- [kai-ad-campaign](./kai-ad-campaign.md)
- [kai-analytics](./kai-analytics.md)
- [kai-audit](./kai-audit.md)
- [kai-brand](./kai-brand.md)
- [kai-brief](./kai-brief.md)
- [kai-budget](./kai-budget.md)
- [kai-case-study](./kai-case-study.md)
- [kai-cold-outreach](./kai-cold-outreach.md)
- [kai-competitors](./kai-competitors.md)
- [kai-content-calendar](./kai-content-calendar.md)
- [kai-cro](./kai-cro.md)
- [kai-growth-plan](./kai-growth-plan.md)
- [kai-influencer](./kai-influencer.md)
- [kai-landing-page](./kai-landing-page.md)
- [kai-launch](./kai-launch.md)
- [kai-newsletter](./kai-newsletter.md)
- [kai-partnership](./kai-partnership.md)
- [kai-podcast](./kai-podcast.md)
- [kai-product-maker](./kai-product-maker.md)
- [kai-repurpose](./kai-repurpose.md)
- [kai-retarget](./kai-retarget.md)
- [kai-retention](./kai-retention.md)
- [kai-seo-audit](./kai-seo-audit.md)
- [kai-social](./kai-social.md)
- [kai-start](./kai-start.md)
- [kai-surround-sound](./kai-surround-sound.md)
- [kai-topical-map](./kai-topical-map.md)
- [kai-video](./kai-video.md)
- [kai-video-production](./kai-video-production.md)
- [kai-webinar](./kai-webinar.md)
- [kai-write](./kai-write.md)

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
- [Northstar email system map](../../workspace/demo-clients/northstar-media-lab/emails/_email-system-map.md)
- [quality report](../../workspace/demo-clients/northstar-media-lab/emails/_quality-report.md)
- [demo deck](../../workspace/demo-clients/northstar-media-lab/presentation/output/northstar-email-system-demo.pptx)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.

### Competitive claim
This skill differs from generic marketing AI by mapping messages to lifecycle state, compliance requirements, and follow-up logic rather than drafting disconnected copy.
