---
name: kai-sales-meeting-prep
version: 1.0.0
category: lifecycle
last_updated: 2026-05-27
---

# Kai Sales Meeting Prep

### One-line claim
Prepare sales meetings from SDR replies, account dossiers, CRM notes, call notes, or transcripts with account brief, buyer map, pain hypotheses, discovery questions, objection plan, follow-up email, CRM handoff, and outcome memory.

### Triggers
- sales meeting prep
- prep this demo
- discovery call
- booked meeting
- SDR handoff
- post-call follow-up
- call notes
- sales transcript
- meeting brief

### Inputs
- `meeting_type` (string, required) - `first_discovery`, `demo_prep`, `referral_intro`, `revival_call`, or `post_call_follow_up`.
- `sdr_package` (directory, required) - package folder produced by `kai-sdr-operator`.
- `account` (object, required) - account row or account dossier.
- `contact` (object, required) - buyer, champion, referral, or stakeholder context.
- `offer` (string, required) - call, demo, audit, proposal, quote, or next step.
- `source_evidence` (array, required) - sourced facts, trigger evidence, role evidence, and claim evidence.
- `reply_triage` (object, optional) - reply classification and next action.
- `call_notes_or_transcript` (string, optional) - post-meeting source material.

### Outputs
- Artifact -> `workspace/sdr-operator/<package-slug>/meetings/<meeting-id>.md`.
- Quality report -> known/inferred/missing status, unsupported claims, CRM mutation status, and approval blockers.
- Sidecar fields -> `skill`, `version`, `meeting_id`, `account_id`, `contact_id`, `reply_id`, `evidence_ids`, `crm_handoff_id`, and `memory_candidate_id`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md).

- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **FU-003** - "Useful means the reader can take action immediately through steps, templates, checklists, tools, resources, or clear "do this, then this" guidance." Source: [knowledge/frameworks/content-copywriting/four-us-framework.md](../../knowledge/frameworks/content-copywriting/four-us-framework.md).
- **VG-007** - "Format-specific quality gates from the relevant skill contract must be applied after Four U's, banned-word, AI-slop, and voice-pattern checks." Source: [harness/skills/kai-write/SKILL.md](../../harness/skills/kai-write/SKILL.md).

### Dependencies
- [kai-sdr-operator](./kai-sdr-operator.md)
- [kai-sdr-reply-triage](./kai-sdr-reply-triage.md)
- [kai-gate](./kai-gate.md)

### Called by
- [kai-sdr-operator](./kai-sdr-operator.md)
- [kai-sdr-reply-triage](./kai-sdr-reply-triage.md)

### Quality gates
- `harness/skill-contracts/sales-meeting-prep.yaml` checks pass or blockers are listed.
- Known, inferred, and missing facts are separated.
- Hypotheses are labeled.
- New claims require evidence.
- CRM and calendar mutations are proposed only unless approved.

### Provenance written
- `skill`
- `version`
- `meeting_id`
- `account_id`
- `contact_id`
- `reply_id`
- `evidence_ids`
- `crm_handoff_id`
- `memory_candidate_id`

### Example artifacts
- No committed example artifact found.

### Failure modes
- Thin account context limits the brief to hypotheses and questions.
- Transcripts can contain unverified claims; speaker context must be preserved.
- Pricing, legal, contract, regulated, or sensitive follow-ups require human review.
- CRM and calendar mutations stay blocked until approved.

### Competitive claim
This skill differs from generic sales-call prep by tying discovery, follow-up, CRM handoff, and learning memory back to the SDR package's source evidence and approval state.
