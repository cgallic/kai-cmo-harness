---
name: kai-landing-page
description: Produce complete landing page copy using perception engineering and conversion frameworks. Generates hero section, value props, social proof blocks, objection handlers, and CTA — all scored against quality gates. Use when "landing page", "sales page", "LP copy", "write a landing page", "hero section", "conversion page", "signup page", or any request to produce persuasive page copy that converts visitors.
---

Produce a complete landing page using perception engineering + CRO principles. Every section scored.

## Phase 0: Load Product Context

Check if `MARKETING.md` exists in the **project root** (same directory as CLAUDE.md, README.md, package.json).

**If it exists:** Read it — skip product discovery questions. It has the product name, ICP, value prop, monetization, brand voice, current channels, and competitive landscape.

**If it does NOT exist:** Auto-explore the codebase to create it in the **project root** (next to CLAUDE.md). Do NOT ask the user what the product is. Read CLAUDE.md, README.md, PROJECT.md, package.json, landing pages, and any project files. Search for email/ad/analytics config. Then create `MARKETING.md` using the template from `/kai-email-system`. Present draft to user for confirmation.

---

## Phase 1: Page Discovery

Read from `MARKETING.md`. Only ask about things not covered there:

1. **Traffic source** — cold (ads), warm (content), hot (referral)? Determines awareness level.
2. **Goal** — signup, demo request, purchase, waitlist?
3. **Existing page** — rewrite or net-new?
4. **Proof available** — testimonials, case studies, metrics, logos?

## Phase 2: Page Architecture

Load these before planning:
- `E:\Dev2\kai-cmo-harness-work\knowledge\frameworks\content-copywriting\perception-engineering.md`
- `E:\Dev2\kai-cmo-harness-work\knowledge\checklists\landing-page-messaging-checklist.md`
- `E:\Dev2\kai-cmo-harness-work\knowledge\playbooks\landing-page-messaging-workflow.md`
- `E:\Dev2\kai-cmo-harness-work\knowledge\playbooks\conversion-rate-optimization.md`

Generate a page wireframe (sections in order) before writing copy:

### Standard SaaS Landing Page Structure

| Section | Purpose | Perception Layer |
|---------|---------|-----------------|
| **Hero** | Hook + promise + CTA | Perception — destabilize cached beliefs |
| **Problem** | Agitate the pain | Perception — re-index virtues as vices |
| **Solution** | Your approach (not features) | Context — shift what feels allowed |
| **How It Works** | 3-step simplification | Context — genre-shift (complex → simple) |
| **Social Proof** | Testimonials, logos, metrics | Permission — remove risk |
| **Features/Benefits** | What they get (outcome-framed) | Context — expand possibility |
| **Objection Handler** | Address top 3 objections | Permission — remove consequences |
| **Pricing/CTA** | Final push + urgency | Permission — future pacing |
| **FAQ** | Catch remaining doubts | Permission — double binds |

Adapt to the product. Not every page needs every section.

### Approval Gate

Present the wireframe before writing copy.

## Phase 3: Copy Production

Write each section following perception engineering layers:

### Hero Rules
- Headline: 6-12 words. State the outcome, not the product.
- Subhead: 15-25 words. Qualify the audience and expand the promise.
- CTA: Action-oriented verb + outcome ("Start closing leads" not "Sign up")
- Above the fold: headline, subhead, CTA, one visual. Nothing else.

### Copy Rules (all sections)
- No banned words (leverage, utilize, synergy, etc.)
- No AI slop ("In today's rapidly evolving...")
- Sentences under 20 words
- Bold the benefit, not the feature name
- Every claim needs proof (stat, testimonial, or specific example)
- One CTA per section (same destination, varied wording)

### Perception Engineering Application
- **Perception layer**: First 2 sections. Destabilize what they think they know.
- **Context layer**: Middle sections. Shift the frame so your solution feels inevitable.
- **Permission layer**: Final sections. Remove every reason NOT to act.

## Phase 4: Quality Gates

Score the full page:

1. **Four U's >= 12/16** (page-level score)
2. **Zero banned words**
3. **Zero AI slop**
4. **Landing page messaging checklist** — run against `landing-page-messaging-checklist.md`
5. **Perception engineering checklist** — run against `knowledge/checklists/perception-engineering-checklist.md`
6. **Single consistent CTA** throughout
7. **Proof in every section** (no unsupported claims)

## Phase 5: Output

```markdown
# Landing Page Copy: [Product Name]

## Meta
- **Target audience:** [persona]
- **Traffic source:** [cold/warm/hot]
- **Goal:** [conversion action]
- **Word count:** [X]

## Hero
[headline, subhead, CTA, supporting text]

## Problem
[copy]

## Solution
[copy]

## How It Works
[3 steps]

## Social Proof
[testimonials, metrics, logos]

## Features/Benefits
[outcome-framed feature blocks]

## Objection Handler
[top 3 objections addressed]

## Final CTA
[closing copy + CTA]

## FAQ
[5-7 questions]

## Quality Gate Results
[scores]
```

Save to `workspace/landing-pages/[product-slug].md`.
