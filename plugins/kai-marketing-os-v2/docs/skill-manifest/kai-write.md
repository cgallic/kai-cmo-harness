---
name: kai-write
version: 1.0.0
category: production
last_updated: 2026-05-18
---

# Kai Write

### One-line claim
Write a single piece of marketing content using Kai CMO Harness frameworks and quality gates. Supports blog posts, LinkedIn articles, emails, cold outreach, press releases, ad copy, and TikTok scripts. Automatically loads the right framework, skill contract, and persona.

### Triggers
- write a blog post
- draft an email
- LinkedIn article
- cold outreach
- write ad copy
- press release
- TikTok script

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `format` (string, required) - blog, SEO article, LinkedIn article, email, ad, press release, or script.
- `brief` (file or string, optional) - structured brief from `kai-brief` or equivalent request context.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> single publishable content draft plus visible quality gate scores.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **FU-001** - "Score every publishable content artifact on Unique, Useful, Ultra-specific, and Urgent, with each dimension rated 1-4." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **FU-006** - "The default publishing threshold is 12/16 for blog, SEO, and article content, and 10/16 for ads and email. Any single U below 2 should block or force revision." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **VG-005** - "Tier 1 banned words and AI slop phrases hard-block publishable content until rewritten. Examples include "leverage", "utilize", "synergy", "in conclusion", and "in today's rapidly evolving"." Source: [scripts/quality_gates/banned_word_check.py](../../scripts/quality_gates/banned_word_check.py).
- **VG-006** - "Binary cliche patterns such as "X, not Y", "isn't X - it's Y", "Here's the thing", "I'll be honest", "Let that sink in", and "Hot take" fail the voice-pattern check unless they appear in comments or code fences." Source: [harness/skills/kai-gate/SKILL.md](../../harness/skills/kai-gate/SKILL.md).
- **VG-008** - "When a piece fails quality gates, fix the specific issues and re-score. Stop after two retry cycles and surface remaining failures." Source: [harness/skills/kai-write/SKILL.md](../../harness/skills/kai-write/SKILL.md).
- **AA-001** - "Put condition clauses after the main clause. Write "Do X if Y" and "X happens because Y" instead of opening with "If" or "Because" when the sentence still reads naturally." Source: [knowledge/frameworks/content-copywriting/algorithmic-authorship.md](../../knowledge/frameworks/content-copywriting/algorithmic-authorship.md).
- **AA-005** - "Keep sentences short and split compound explanations into separate sentences when the average sentence length exceeds roughly 20 words." Source: [knowledge/frameworks/content-copywriting/algorithmic-authorship.md](../../knowledge/frameworks/content-copywriting/algorithmic-authorship.md).
- **AA-009** - "Follow each declaration with an example, evidence note, or concrete instance." Source: [knowledge/frameworks/content-copywriting/algorithmic-authorship.md](../../knowledge/frameworks/content-copywriting/algorithmic-authorship.md).

### Dependencies
- [kai-email-system](./kai-email-system.md)

### Called by
- [kai-brief](./kai-brief.md)
- [kai-content-calendar](./kai-content-calendar.md)
- [kai-launch](./kai-launch.md)
- [kai-product-maker](./kai-product-maker.md)
- [kai-reddit-listen](./kai-reddit-listen.md)
- [kai-topical-map](./kai-topical-map.md)

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
- [announcement blog post](../../workspace/launch/blog/announcement.md)
- [launch deep-dive post](../../workspace/launch/blog/deep-dive.md)
- [LinkedIn article](../../workspace/launch/linkedin/article.md)

### Failure modes
- Missing product context causes the skill to infer too much from repository files.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.
- AI-search visibility recommendations cannot promise citation, ranking, or answer inclusion.

### Competitive claim
This skill differs from generic marketing AI by producing channel-shaped artifacts with format constraints, policy checks where applicable, and visible quality gates before handoff.
