# Mutation Risk Checklist

> **Use when:** A workflow may send, publish, upload, enroll, activate, update, delete, spend, schedule, redirect, edit, or otherwise change a live system.

---

## Mutation Verbs

Flag any output, script, connector action, or recommendation that includes these verbs. Approval required before live use:

- [ ] Send.
- [ ] Publish.
- [ ] Schedule.
- [ ] Upload.
- [ ] Import.
- [ ] Enroll.
- [ ] Activate.
- [ ] Pause.
- [ ] Delete.
- [ ] Update.
- [ ] Edit.
- [ ] Redirect.
- [ ] Approval required before any live spend action.
- [ ] Change budget or bid.
- [ ] Add contacts.
- [ ] Sync CRM.
- [ ] Push to CMS.
- [ ] Launch campaign.

Flagging does not block planning. It requires a dry run and approval before live action.

---

## Dry-Run Requirements

- [ ] Show exactly what would change.
- [ ] Identify destination system.
- [ ] Identify affected audience, URL, campaign, account, or record count.
- [ ] List source refs behind the action.
- [ ] Declare privacy scan result.
- [ ] Declare policy checks that apply.
- [ ] Declare rollback or pause plan when relevant.
- [ ] Include approval owner and approval state.
- [ ] Save the dry-run artifact before mutation.

---

## Risk Tiers

| Tier | Examples | Approval |
|------|----------|----------|
| Low | Draft artifact, local report, internal note | Operator review |
| Medium | CMS draft, CRM field proposal, scheduled social draft | Named owner approval |
| High | Live send, contact upload, budget change, redirect, public pricing change | Explicit human approval |
| Critical | Deletion, legal/health/finance claims, regulated targeting, account-wide automation | Escalation required |

---

## Required Checks

- [ ] Privacy sanitizer passed.
- [ ] Data provenance is declared.
- [ ] Data gaps are listed.
- [ ] Platform or channel policy is loaded when applicable.
- [ ] No fabricated proof, fake expert authority, or unsupported testimonial is present.
- [ ] Suppression or consent checks are complete for outreach.
- [ ] Spend, audience, URL, and account names are verified.
- [ ] The action is reversible or the irreversible risk is acknowledged.

---

## Blockers

Do not proceed when:

- [ ] Approval is missing.
- [ ] Consent or suppression status is unknown.
- [ ] The dry-run artifact does not show the exact mutation.
- [ ] The output relies on unsupported quantitative claims.
- [ ] The action would evade platform policy or disclosure rules.
- [ ] The action would expose private data.
- [ ] The rollback plan is missing for a high-risk change.
