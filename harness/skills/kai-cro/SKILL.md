---
name: kai-cro
description: Conversion rate optimization audit — analyze a landing page, signup flow, or checkout funnel using the 5-layer CRO stack (technical performance, traffic quality, offer/pricing, design/layout, copy/messaging). Produces prioritized fix list with expected impact. Use when "CRO audit", "conversion audit", "why isn't this converting", "improve conversion rate", "landing page not converting", "optimize funnel", "signup flow audit", or any request to diagnose and fix conversion problems.
---

Run a CRO audit using the 5-layer optimization stack. Produces a prioritized fix list.

## Phase 1: Page/Funnel Input

Ask the user:

1. **URL(s)** — what page or flow are we auditing?
2. **Current conversion rate** — if known
3. **Conversion goal** — signup, purchase, demo request, download?
4. **Traffic source** — where do visitors come from? (affects awareness level)
5. **Known friction points** — anything they've already identified?

## Phase 2: Audit Execution

Load these before starting:
- `E:\Dev2\kai-cmo-harness-work\knowledge\playbooks\conversion-rate-optimization.md`
- `E:\Dev2\kai-cmo-harness-work\knowledge\checklists\cro-audit-checklist.md`
- `E:\Dev2\kai-cmo-harness-work\knowledge\checklists\landing-page-messaging-checklist.md`

### 5-Layer CRO Stack (audit bottom-up)

**Layer 1: Technical Performance** (fix first)
- Page load time (target: < 2 seconds)
- Mobile responsiveness
- Broken elements, JS errors
- Form functionality
- Payment flow reliability

**Layer 2: Traffic & Audience Quality**
- Is the right audience arriving? (message-market match)
- Ad → landing page consistency (scent trail)
- Awareness level match (cold traffic needs more education than warm)

**Layer 3: Offer & Pricing**
- Is the offer clear in 5 seconds?
- Value prop vs price — is it a no-brainer?
- Risk reversal (guarantee, free trial, money-back)
- Urgency — any reason to act now?

**Layer 4: Design & Layout**
- Visual hierarchy — does the eye flow to the CTA?
- CTA visibility and contrast
- Above-the-fold content — does it sell or just describe?
- Social proof placement
- Form length (minimize fields)
- Distractions — anything pulling attention from the goal?

**Layer 5: Copy & Messaging** (highest leverage)
- Headline — does it state the outcome, not the product?
- Specificity — numbers, examples, named results?
- Objection handling — are the top 3 concerns addressed?
- CTA copy — action verb + outcome ("Start saving time" not "Submit")
- Proof — is every claim supported?

Use the browse/gstack skill to actually view and screenshot the page if available.

## Phase 3: Scoring

Score each layer 1-10:

| Layer | Score | Key Issue | Fix |
|-------|-------|-----------|-----|
| Technical | /10 | [main issue] | [specific fix] |
| Traffic | /10 | | |
| Offer | /10 | | |
| Design | /10 | | |
| Copy | /10 | | |
| **Overall** | **/50** | | |

## Phase 4: Prioritized Fixes

| Priority | Fix | Layer | Expected Impact | Effort |
|----------|-----|-------|----------------|--------|
| P0 | [fix] | [layer] | High | Low |
| P1 | [fix] | [layer] | High | Medium |
| P2 | [fix] | [layer] | Medium | Medium |

## Phase 5: Output

Save to `workspace/cro-audit/[page-slug].md`.

Include:
- Overall health score (/50)
- Layer-by-layer analysis
- Prioritized fix list
- Before/after copy suggestions for the top 3 copy fixes
- A/B test recommendations (what to test first)
