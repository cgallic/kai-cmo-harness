---
name: kai-sdr-reply-triage
description: >
  Triage SDR replies and turn inbound responses into safe next actions, CRM handoff notes,
  suppression updates, objection responses, referrals, and meeting prep triggers. Use when
  "SDR reply", "triage replies", "outbound replies", "interested reply", "objection reply",
  "not interested", "unsubscribe", "wrong person", "bounce", "sales follow-up", "booked meeting",
  or any request to classify and respond to sales development replies.
---

# kai-sdr-reply-triage — Reply Loop

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

Every inbound reply ends up as a triage record that names exactly one category, the consent and suppression consequence, the next safe action with an owner, and — only where it is allowed — a drafted response. The record makes the state change explicit: what this reply did to consent, suppression, routing, meeting status, objection state, and CRM state.

The risk this skill exists to remove is a reply that gets answered when it should have been suppressed, escalated, or left alone.

## Done when

Work type `internal-research` — floor **E2/C2/O0** (`harness/eco-floors.yaml`). The triage record itself never leaves the workspace.

- **E2** — the reply record exists at its package path and satisfies `harness/skill-contracts/sdr-reply-triage.yaml`.
- **C2** — `banned_word_check` passes; category, risk tier, suppression action, and evidence fields are all populated.
- **O0** — no outcome obligation on the record.

Sending the drafted response is separate work at the `cold-email` floor **E5/C4/O3**: provider send receipt plus suppression-list reconciliation, and CAN-SPAM/GDPR/CASL identity, opt-out, and consent basis verified before send.

## Constraints

- **Missing context means a hold, not a draft.** Without sender identity, suppression list, message history, and source evidence for the contact, write a triage hold note instead of a send-ready response.
- **Honor opt-outs immediately.** Suppress globally; draft nothing beyond an opt-out confirmation where one is required.
- **Do not argue with complaints.** Stop the sequence, suppress, route to a human owner.
- **Do not reply to bounces.** Mark the contact path invalid and block follow-up on that address.
- **No invented context** — no prior relationship, no new claims without evidence.
- **Sensitive, legal, or regulated replies do not get routed without human review.**
- **No CRM mutation.** Notes, tasks, and field changes are proposals.
- **Under 120 words** unless the user asks for a longer sales response. One CTA, one next action.
- **Memory candidates carry a `Do not promote until` condition** and stay unpromoted until it is met.

**Categories** — classify exactly one primary:

| Category | Action |
|---|---|
| `interested` | Prepare meeting handoff and short response. Trigger `/kai-sales-meeting-prep`. |
| `objection` | Identify objection type and draft one respectful response. |
| `referral` | Capture referred person, source, and permission trail. |
| `not_now` | Draft low-pressure close and future reminder task. |
| `wrong_person` | Ask for routing only when appropriate. Do not pressure. |
| `opt_out` | Suppress globally. Do not draft further outreach except opt-out confirmation if required. |
| `bounce` | Mark invalid contact path and block follow-up on that address. |
| `complaint` | Stop sequence, suppress, and route to human owner. |
| `unsubscribe_confirmed` | Record suppression and no further action. |
| `needs_human_review` | Use for legal, regulated, sensitive, hostile, ambiguous, or high-value replies. |

## Context

| Need | Load |
|---|---|
| Record structure, required fields, gate thresholds | `harness/skill-contracts/sdr-reply-triage.yaml` |
| Package schema, ledger status values, memory ledger | `harness/skill-contracts/sdr-package.yaml` |
| Opt-out, sender identity, consent, suppression law | `harness/references/cold-email-rules.md` |
| Account row, contact row, source evidence, message history, suppression state | `workspace/sdr-operator/<package-slug>/` |
| Booked meeting or buying conversation follow-on | `/kai-sales-meeting-prep` |

**Output** goes to `workspace/sdr-operator/<package-slug>/replies/<reply-id>.md`. Same path as v1 — downstream tooling does not branch on version.

Trigger `/kai-sales-meeting-prep` when the reply implies a meeting, demo, call, referral intro, or buying conversation.

## Escalate when

- The reply is legal, regulated, sensitive, hostile, ambiguous, or high-value — category `needs_human_review`, no draft.
- Consent basis or suppression state for the contact cannot be established.
- The reply disputes a claim made in the original outbound message.
- The safe next action requires a live send, CRM mutation, or calendar action and no approver is named.
- Reply content contradicts the source evidence the account was built on.
