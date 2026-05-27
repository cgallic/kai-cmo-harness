# SDR Operating Loop

The SDR system is a loop. Each pass improves source quality, trigger quality, message quality, meeting quality, and CRM quality.

## Loop Stages

1. **Define** - Load product context, pick vertical pack, set offer, ICP, and disqualifiers.
2. **Source** - Collect accounts from approved sources only.
3. **Enrich** - Add only needed fields with field-level provenance.
4. **Score** - Rank accounts and contacts with a 100-point scoring model.
5. **Approve** - Request approval for live connector, CRM, sequencer, phone, SMS, or email actions.
6. **Draft** - Produce sequence briefs and copy after source and suppression gates pass.
7. **Test** - Run a tiny approved test cohort before broad activation.
8. **Send Or Handoff** - Prepare approved imports or manual tasks. Do not auto-send.
9. **Triage** - Classify replies, bounces, objections, referrals, opt-outs, and interested responses.
10. **Meet** - Prep meetings, write follow-ups, and update proposed CRM actions.
11. **Brief** - Produce a daily operator briefing with approvals, blocked rows, reply queue, and meeting prep.
12. **Learn** - Promote patterns from real outcomes into memory.

## Role Separation

Keep the SDR loop separate from closing and account management:

- **SDR loop**: source, enrich, score, draft, triage, book, and hand off.
- **AE loop**: discovery, demo, proposal, negotiation, close, and commercial commitments.
- **CSM loop**: onboarding, adoption, renewal, expansion, and customer proof.

The SDR package can prepare handoff notes for AE or CSM work, but it should not negotiate, quote, or commit terms unless the user explicitly asks for a sales-closing workflow with human approval.

## Qualification Layer

Add a qualification snapshot before meeting handoff:

| Field | Description |
|---|---|
| `problem_fit` | Does the prospect appear to have the problem? |
| `persona_fit` | Is the contact likely to own or influence the problem? |
| `timing_signal` | Why now? |
| `impact_hint` | What cost, risk, or opportunity is plausible? Label hypotheses. |
| `next_step` | Meeting, referral, nurture, no fit, suppress, or human review. |

Use BANT, MEDDICC, SPICED, or a user-provided framework only when it matches the sales motion. Do not force enterprise qualification onto small founder-led sales.

## Daily Operator Loop

Run daily when outbound is active:

- Review blocked rows.
- Review approval queue.
- Review replies and opt-outs.
- Prepare next actions for interested and referral replies.
- Update meeting prep for booked calls.
- Review test cohort status before broad activation.
- Summarize pipeline alerts and stale tasks.
- Record source and message quality notes.

## Weekly Learning Loop

Run weekly:

- Compare sources by approved rows, blocked rows, replies, meetings, and objections.
- Compare trigger types by positive replies and meetings.
- Compare personas by reply quality.
- Compare objections by frequency and deal stage.
- Retire weak sources or triggers.
- Promote only source-backed learnings.

## Monthly Strategy Loop

Run monthly:

- Re-score ICP assumptions.
- Revisit vertical pack defaults.
- Review deliverability and complaint risk.
- Review meetings-to-opportunity handoff.
- Archive stale evidence.
- Refresh connector docs and approval rules.

## Memory Promotion Rule

Do not promote a learning from one anecdote unless the user explicitly marks it as a strategic decision. Default promotion thresholds:

- `signal`: at least 10 comparable outcomes.
- `strong_signal`: at least 25 comparable outcomes.
- `strategic_default`: at least 50 comparable outcomes or human approval.

When volume is low, keep the learning as a hypothesis.

## Output Files By Loop Stage

| Stage | Files |
|---|---|
| Define | `_brief.md`, `_icp-scorecard.md`, `vertical-pack.md` |
| Source | `_lead-source-plan.md`, `connector-plan.md`, `_data-sources.md` |
| Enrich | `lead-ledger-template.csv`, `_data-gaps.md` |
| Score | `_account-scoring-model.md`, `account-dossier-template.md` |
| Approve | `approval-plan.md` |
| Draft | `sequence-brief.md`, `/kai-cold-outreach` outputs |
| Test | `test-cohort-plan.md` |
| Triage | `reply-triage.md`, `/kai-sdr-reply-triage` outputs |
| Meet | `meeting-prep.md`, `/kai-sales-meeting-prep` outputs |
| Brief | `daily-briefing-template.md` |
| CRM | `crm-handoff.md` |
| Learn | `memory-ledger.md`, `_evaluation-report.md` |
