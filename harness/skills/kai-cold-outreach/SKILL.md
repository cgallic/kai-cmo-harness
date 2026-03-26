---
name: kai-cold-outreach
description: Build a complete cold email outreach system — ICP definition, sequence architecture, personalization strategy, and batch-produced email sequences with CAN-SPAM/deliverability compliance. Use when "cold outreach", "cold email sequence", "outbound campaign", "prospecting emails", "sales outreach", "build outreach sequence", or any request to create systematic cold email campaigns for lead generation.
---

Build a complete cold outreach system — from ICP definition through batch-produced sequences with compliance checks.

## Phase 1: Outreach Discovery

Ask the user:

1. **Product/service** — what are we selling?
2. **ICP (Ideal Customer Profile)** — job titles, company size, industry, pain points
3. **Offer** — what's the ask? (demo, call, free trial, content download)
4. **Sending infrastructure** — what tool? (Instantly, Smartlead, Loops, etc.)
5. **Volume** — how many prospects per day/week?
6. **Existing sequences** — anything running already?

## Phase 2: Sequence Architecture

Generate `workspace/outreach/_sequence-map.md`.

### Standard 3-Touch Structure

| Touch | Timing | Goal | Hook Type |
|-------|--------|------|-----------|
| **Touch 1** | Day 0 | Open + reply | Personalized pain hook |
| **Touch 2** | Day 3 | Social proof / value add | Case study or insight |
| **Touch 3** | Day 7 | Breakup / soft close | Last chance framing |

Each touch: max 150 words. Single CTA. One personalization token minimum.

### Variant Strategy

Produce 3 variants (A/B/C) of the full sequence for split testing. Each variant uses a different hook archetype:
- **Variant A:** Pain-first (lead with the problem)
- **Variant B:** Insight-first (lead with a surprising fact)
- **Variant C:** Social proof-first (lead with a result)

### Approval Gate

Present sequence map + variant strategy before writing.

## Phase 3: Production

Load these before writing:
- `E:\Dev2\kai-cmo-harness-work\harness\skill-contracts\cold-email.yaml`
- `E:\Dev2\kai-cmo-harness-work\harness\references\cold-email-rules.md`
- `E:\Dev2\kai-cmo-harness-work\knowledge\channels\email-lifecycle.md` (subject line formulas)

### Per-Touch Output

```markdown
# Touch [1/2/3] — Variant [A/B/C]

**Subject:** [max 50 chars]
**Preview text:** [40-90 chars]

**Body:**
[Max 150 words. Personalization tokens in {{double_braces}}.]

**CTA:** [Single ask]

## Quality Gate Results
- Word count: [X]/150
- Subject length: [X]/50
- Personalization token: PASS/FAIL
- First line not generic: PASS/FAIL
- Single CTA: PASS/FAIL
- Banned words: PASS/FAIL
- CAN-SPAM compliant: PASS/FAIL
```

### Quality Gates (per touch)

1. **Word count <= 150**
2. **Subject line <= 50 chars**
3. **Has personalization token** ({{company}}, {{name}}, {{pain_point}}, etc.)
4. **First line is NOT generic** (no "I hope this finds you well", "I came across your profile")
5. **Single CTA per touch**
6. **Zero banned words**
7. **CAN-SPAM compliance** — physical address, unsubscribe mechanism (handled by sending tool)

### Compliance Rules (from cold-email-rules.md)

- No misleading subject lines
- Sender identity must be clear
- Physical mailing address required (in footer/signature)
- Opt-out mechanism must work within 10 business days
- No purchased/scraped lists
- GDPR: legitimate interest basis required for EU prospects

### Batch Output

```
workspace/outreach/
├── _sequence-map.md
├── variant-a/
│   ├── touch-1.md
│   ├── touch-2.md
│   └── touch-3.md
├── variant-b/
│   ├── touch-1.md
│   ├── touch-2.md
│   └── touch-3.md
├── variant-c/
│   └── ...
├── _personalization-guide.md    # How to research and fill tokens
└── _quality-report.md
```

## Phase 4: Personalization Guide

Generate `workspace/outreach/_personalization-guide.md`:
- Which tokens to use and where to find the data
- Research workflow per prospect (LinkedIn, company site, recent news)
- Examples of good vs bad personalization
- Tokens: {{first_name}}, {{company}}, {{role}}, {{pain_point}}, {{recent_trigger}}

## Phase 5: Deliverability Notes

Generate `workspace/outreach/_deliverability.md`:
- Domain warming schedule (if new domain)
- Sending volume ramp
- SPF/DKIM/DMARC requirements
- Spam word avoidance list
- Reply rate benchmarks by industry
