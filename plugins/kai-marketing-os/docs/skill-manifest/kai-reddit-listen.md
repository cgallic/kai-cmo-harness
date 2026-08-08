---
name: kai-reddit-listen
version: 2.0.0
category: measurement
last_updated: 2026-05-18
---

# Kai Reddit Listen

### One-line claim
Build and operate a brand-neutral Reddit intelligence system from approved read-only monitoring through scoring, dashboard review, alerts, weekly digests, and content briefs.

### Triggers
- reddit monitor
- reddit listener
- reddit outreach
- watch subreddits
- find reddit opportunities
- listen on reddit
- community listening
- reddit intelligence
- content ideas from reddit

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `request` (string, required) - natural-language task that triggered this skill.
- `persona_or_audience` (string, optional) - Kai persona, ICP segment, buyer, user, or stakeholder group.
- `source_evidence` (files or URLs, optional) - proof, analytics, transcripts, examples, policies, exports, or screenshots used by the skill.

### Outputs
- Artifact -> validated profile, normalized opportunity bank, dashboard, Sheet-row preview, urgent-alert preview, weekly digest, content briefs, and human-only response drafts.
- Quality report -> pass/fail status for relevant gates, blockers, and retry notes.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **POL-003** - "Disclose material connections before or alongside endorsements. Disclosures must be clear, conspicuous, and visible in the medium where the endorsement appears." Source: [harness/references/advertising-compliance.md](../../harness/references/advertising-compliance.md).
- **VG-005** - "Tier 1 banned words and AI slop phrases hard-block publishable content until rewritten. Examples include "leverage", "utilize", "synergy", "in conclusion", and "in today's rapidly evolving"." Source: [scripts/quality_gates/banned_word_check.py](../../scripts/quality_gates/banned_word_check.py).
- **VG-006** - "Binary cliche patterns such as "X, not Y", "isn't X - it's Y", "Here's the thing", "I'll be honest", "Let that sink in", and "Hot take" fail the voice-pattern check unless they appear in comments or code fences." Source: [harness/skills/kai-gate/SKILL.md](../../harness/skills/kai-gate/SKILL.md).
- **FU-001** - "Score every publishable content artifact on Unique, Useful, Ultra-specific, and Urgent, with each dimension rated 1-4." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).

### Dependencies
- [kai-brand](./kai-brand.md)
- [kai-competitors](./kai-competitors.md)
- [kai-gate](./kai-gate.md)
- [kai-start](./kai-start.md)
- [kai-write](./kai-write.md)

### Runtime and contracts

- Engine and dashboard: `scripts/reddit_monitor/intelligence/`
- Artifact contract: `harness/skill-contracts/reddit-intelligence.yaml`
- Harness configuration: `config.yaml` under `reddit_intelligence`
- Installed with both `kai-marketing-os` plugin variants and `install.sh`
- External effects default OFF; the module exposes no Reddit write operation

### Called by
- No other `kai-*` manifest page declares this skill as a dependency.

### Quality gates
- Four U's score meets threshold: 12/16 for strategic, SEO, article, and page work; 10/16 for ads and email; any single U below 2 blocks handoff.
- Banned-word, AI-slop, and voice-pattern checks pass with zero hard-blocking hits.
- Platform policy and paid-media write-access controls pass; live mutation requires human approval.
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
- `policy_references` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `approval_state` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `rights_or_disclosure_evidence` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.

### Example artifacts
- No committed example artifact found.

### Failure modes
- Missing product context or approved subreddit coverage blocks activation instead of causing brand inference.
- Unavailable source access limits the workflow to public or user-provided evidence.
- Submission RSS does not provide complete Reddit or comment coverage and must not be described that way.
- Sheet and email activation fails closed until an approved provider adapter, destination, and explicit activation are present.
- Gate failures after two retries require human review instead of silent publication.
- Platform policy, regulated-industry, or consent constraints can block copy or activation.
- Quantitative claims are blocked when collector data, analytics access, or source citations are missing.

### Competitive claim
This skill differs from generic marketing AI by separating evidence collection, scoring, data gaps, and recommendations so unsupported claims are visible.
