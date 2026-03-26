---
name: kai-email-system
description: Plan and batch-produce an entire email system for a product. Maps every lifecycle touchpoint (onboarding, activation, conversion, retention, transactional, win-back), generates all emails with quality gates, outputs Loops-ready copy. Use when "create all emails", "email system", "build email sequences", "lifecycle emails", "onboarding sequence", "set up transactional emails", "plan all the emails for [product]", or any request to systematically produce a complete set of emails for a platform.
---

Build a complete email system for a product — from lifecycle mapping through batch production with quality gates. All emails target Loops (lifecycle + transactional).

## Phase 1: Product Discovery

Before mapping emails, understand the product. Ask the user (or read project files):

1. **What does the product do?** (one sentence)
2. **Key user actions** — what are the 3-5 things users do in the product?
3. **Monetization** — free tier? trial? paid plans? what triggers upgrade?
4. **Current emails** — any emails already set up in Loops?
5. **User segments** — are there distinct user types (admin vs member, buyer vs seller)?

If the user points to a codebase or project, read it to infer these answers instead of asking.

## Phase 2: Lifecycle Map

Generate a complete email map organized by stage. Output as a markdown table in `workspace/email-system-map.md`.

### Standard B2B SaaS Stages

| Stage | Trigger Type | Emails |
|-------|-------------|--------|
| **Welcome** | Transactional | Welcome + getting started |
| **Onboarding** | Behavioral | Setup incomplete, first value moment, invite team |
| **Activation** | Behavioral | Feature discovery, usage milestone |
| **Conversion** | Time + behavioral | Trial expiring (T-3, T-1, T-0), upgrade prompt |
| **Engagement** | Behavioral + scheduled | Weekly digest, new feature announcement |
| **Retention** | Behavioral | Usage drop, re-engagement, churn risk |
| **Win-back** | Time-based | Churned user sequence (D+7, D+14, D+30) |
| **Transactional** | Event-driven | Password reset, invoice, plan change, security alert |
| **Referral** | Milestone | Referral ask after value moment |

Adapt this map to the actual product. Remove irrelevant stages, add product-specific ones.

For each email in the map, specify:
- **Email name** (becomes the Loops template name)
- **Trigger** (Loops event name, e.g. `user.signed_up`, `trial.expiring_3d`)
- **Stage** (lifecycle stage)
- **Priority** (P0 = launch blocker, P1 = week 1, P2 = month 1)
- **Segment** (which users receive this)

### Approval Gate

Present the email map to the user. Get approval before producing any emails. Ask:
- "Anything missing?"
- "Any emails you definitely don't need?"
- "Which priority tier should I produce first?"

## Phase 3: Batch Production

Produce emails in priority order (P0 first). For each email:

### 3a. Load Context

Read these harness files before writing:
- `E:\Dev2\kai-cmo-harness-work\knowledge\channels\email-lifecycle.md` — lifecycle patterns, subject line formulas, anti-patterns
- `E:\Dev2\kai-cmo-harness-work\harness\skill-contracts\email-lifecycle.yaml` — quality gates and output format
- `E:\Dev2\kai-cmo-harness-work\harness\skill-contracts\email.yaml` — general email contract

For cold outreach emails, also load:
- `E:\Dev2\kai-cmo-harness-work\harness\skill-contracts\cold-email.yaml`
- `E:\Dev2\kai-cmo-harness-work\harness\references\cold-email-rules.md`

### 3b. Write Each Email

Output format per email (matches Loops template structure):

```markdown
# [Email Name]

**Trigger:** `event.name` (Loops event)
**Segment:** [who receives this]
**Stage:** [lifecycle stage]
**Send timing:** [immediate | delay | time-of-day preference]

## Subject Line
Primary: [subject]
Variant A: [subject]
Variant B: [subject]

## Preview Text
[40-90 chars shown before open]

## Body
[Email body in markdown — 200-500 words max]

## CTA
[Single primary CTA — text and destination]

## Quality Gate Results
- Four U's: [score]/16 (min 10)
- Banned words: [PASS/FAIL]
- Subject length: [chars]/50
- Preview text length: [chars]/90
- Word count: [count]/500
- Single CTA: [PASS/FAIL]
```

### 3c. Quality Gates (per email)

Run these checks. Every email must pass ALL gates:

1. **Four U's score >= 10/16** — Score each U (Unique, Useful, Ultra-specific, Urgent) 1-4
2. **Zero banned words** (Tier 1: leverage, utilize, synergy, innovative, deep dive, circle back, touch base, moving forward, at the end of the day)
3. **Zero AI slop** ("In conclusion", "It's important to note", "In today's rapidly evolving", "This comprehensive guide", "Without further ado", "It's worth noting that")
4. **Subject line <= 50 chars** (mobile truncation)
5. **Preview text 40-90 chars**
6. **Body <= 500 words**
7. **Single primary CTA** (one action per email)
8. **First line not generic** (no "I hope this email finds you well")

If an email fails: fix the specific issue and re-check. Max 2 retries per email. After 2 failures, flag it and move to the next.

### 3d. Batch Output

Write all produced emails to `workspace/emails/[stage]/[email-name].md`.

```
workspace/emails/
├── _email-system-map.md          # The full lifecycle map
├── welcome/
│   └── welcome-getting-started.md
├── onboarding/
│   ├── setup-incomplete.md
│   ├── first-value-moment.md
│   └── invite-team.md
├── conversion/
│   ├── trial-expiring-3d.md
│   ├── trial-expiring-1d.md
│   └── trial-expired-grace.md
├── retention/
│   ├── usage-drop.md
│   └── re-engagement.md
├── transactional/
│   ├── password-reset.md
│   ├── invoice.md
│   └── plan-change.md
└── _quality-report.md            # Gate results for all emails
```

## Phase 4: Quality Report

After all emails are produced, generate `workspace/emails/_quality-report.md`:

```markdown
# Email System Quality Report

## Summary
- Total emails: [N]
- Passed all gates: [N]
- Failed (flagged for human review): [N]
- Average Four U's score: [X]/16

## Per-Email Results
| Email | Stage | Four U's | Banned | Slop | Subject | CTA | Status |
|-------|-------|----------|--------|------|---------|-----|--------|
| ...   | ...   | .../16   | PASS   | PASS | XX/50   | PASS| PASS   |

## Flagged for Review
[List any emails that failed after 2 retries with specific failure reasons]
```

## Phase 5: Loops Implementation Notes

After producing all emails, generate `workspace/emails/_loops-setup.md` with:

1. **Events to create in Loops** — list every trigger event name
2. **Segments/groups needed** — user segments referenced by emails
3. **Sequence flows** — which emails chain together (onboarding sequence, trial expiration sequence, win-back sequence) with delays between them
4. **Transactional vs marketing** — which emails are transactional (no unsubscribe needed) vs marketing (require unsubscribe)

## Parallelization

When producing emails, use parallel agents for independent emails. Emails within the same sequence should be written sequentially (tone must flow). Emails in different stages can be written in parallel.

## Persona Application

If the product has defined personas in the harness (`E:\Dev2\kai-cmo-harness-work\knowledge\personas/`), load the relevant persona before writing. Match email tone to the persona's language patterns and pain points. If no persona applies, write in a direct, helpful tone — no corporate filler.
