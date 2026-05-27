---
name: kai-sdr-reply-triage
version: 1.0.0
category: lifecycle
last_updated: 2026-05-27
---

# Kai SDR Reply Triage

### One-line claim
Classify SDR replies and turn inbound responses into safe next actions, CRM handoff notes, suppression updates, objection responses, referrals, meeting prep triggers, and outcome memory candidates.

### Triggers
- SDR reply
- triage replies
- outbound replies
- interested reply
- objection reply
- not interested
- unsubscribe
- wrong person
- bounce
- sales follow-up
- booked meeting

### Inputs
- `sdr_package` (directory, required) - package folder produced by `kai-sdr-operator`.
- `original_message` (object, required) - message or sequence touch that generated the reply.
- `reply` (object, required) - inbound reply, bounce, complaint, referral, opt-out, or interested response.
- `contact` (object, required) - contact row with source and suppression fields.
- `account` (object, required) - account row with score and evidence fields.
- `suppression_status` (string, required) - current suppression state.
- `claim_evidence_log` (array, optional) - proof for any claims in a response.

### Outputs
- Artifact -> `workspace/sdr-operator/<package-slug>/replies/<reply-id>.md`.
- Quality report -> category, risk tier, next action, suppression action, CRM handoff, meeting trigger, and approval status.
- Sidecar fields -> `skill`, `version`, `reply_id`, `message_id`, `contact_id`, `account_id`, `category`, `suppression_action`, `crm_handoff_id`, `meeting_id`, and `memory_candidate_id`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md).

- **POL-002** - "All advertising claims must be truthful, non-misleading, and evidence-based before the ad runs." Source: [harness/references/advertising-compliance.md](../../harness/references/advertising-compliance.md).
- **POL-006** - "No paid-media write action should auto-execute. Human approval is required for creating, publishing, pausing, activating, bid changes, budget changes, targeting changes, asset uploads, and keyword mutations." Source: [harness/references/ad-write-guardrails.md](../../harness/references/ad-write-guardrails.md).
- **VG-007** - "Format-specific quality gates from the relevant skill contract must be applied after Four U's, banned-word, AI-slop, and voice-pattern checks." Source: [harness/skills/kai-write/SKILL.md](../../harness/skills/kai-write/SKILL.md).
- **VG-008** - "When a piece fails quality gates, fix the specific issues and re-score. Stop after two retry cycles and surface remaining failures." Source: [harness/skills/kai-write/SKILL.md](../../harness/skills/kai-write/SKILL.md).

### Dependencies
- [kai-sdr-operator](./kai-sdr-operator.md)
- [kai-sales-meeting-prep](./kai-sales-meeting-prep.md)
- [kai-gate](./kai-gate.md)

### Called by
- [kai-sdr-operator](./kai-sdr-operator.md)

### Quality gates
- `harness/skill-contracts/sdr-reply-triage.yaml` checks pass or blockers are listed.
- Opt-outs and complaints suppress follow-up.
- Bounces do not get response drafts.
- New claims require evidence.
- CRM updates are proposed only. Live mutation requires approval.

### Provenance written
- `skill`
- `version`
- `reply_id`
- `message_id`
- `contact_id`
- `account_id`
- `category`
- `suppression_action`
- `crm_handoff_id`
- `meeting_id`
- `memory_candidate_id`

### Example artifacts
- No committed example artifact found.

### Failure modes
- Missing original message or reply context blocks send-ready response.
- Opt-out, complaint, legal, or regulated replies require hold or human review.
- Unsupported claims are removed or held for review.
- CRM mutation stays blocked until approved.

### Competitive claim
This skill differs from generic reply drafting by preserving suppression, approval, source evidence, CRM handoff, meeting prep, and memory candidates inside the sales loop.
