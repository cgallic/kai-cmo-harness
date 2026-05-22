---
issue: 12
title: "Add ecommerce funnel-hack offer architecture module"
state: OPEN
labels: [enhancement]
assignees: []
created: 2026-05-14T01:08:59Z
updated: 2026-05-14T01:08:59Z
author: cgallic
url: https://github.com/cgallic/kai-cmo-harness/issues/12
comments_count: 0
reactions_count: 0
---

# #12: Add ecommerce funnel-hack offer architecture module

## Description

## Context

Connor dropped this TikTok for ingestion: https://www.tiktok.com/t/ZP8pUCBKq/

Canonical source: https://www.tiktok.com/@brendenbuilds/video/7639399895471901966
Brain wiki note: http://agent:8770/page/im8-ecommerce-funnel-hacking-pattern
Brain event: `1072339`

The video points at IM8 as a current ecommerce conversion pattern that brands are trying to copy. The important lesson is not the brand aesthetic. It is that IM8 appears to convert because of offer architecture and subscription/default-choice mechanics, even though the page may look unintuitive or ugly to a designer.

## Pattern to add

Add a **Funnel Hack / Offer Architecture** module to Kai CMO Harness CRO/ecommerce workflows.

The agent should inspect winning external funnels before recommending landing-page changes, especially brands with visible paid spend or peer imitation.

## Required workflow

For ecommerce/CRO audits, require agents to:

1. Identify scaled competitors or adjacent ecommerce brands with active paid spend.
2. Inspect Meta Ads Library and Google ads where available.
3. Archive the landing page, pricing/offer stack, checkout path, upsells, post-purchase hooks, and retention incentives.
4. Separate **conversion mechanics** from **visual taste**.
5. Convert the mechanics into explicit A/B test hypotheses.

## Mechanics to extract

- Default purchase path
- Subscription vs one-time purchase framing
- Price anchoring
- Bonus/free-gift stacking
- Forced-choice architecture
- Checkout friction/removal
- Upsell/downsell structure
- Retention incentives
- Risk reversal

## IM8-specific example mechanics

- Subscription is visually and commercially the primary path.
- 90-day subscription supply gets stacked free gifts.
- Continued subscription unlocks more gifts.
- One-time purchase is minimized and priced high, anchoring subscription as the better choice.
- The page may violate aesthetic instincts while still converting.

## Acceptance criteria

- [ ] CRO/ecommerce audit workflow includes a competitor funnel-hack step.
- [ ] Output includes source URLs/screenshots or archived notes.
- [ ] Output includes an offer/pricing matrix.
- [ ] Output includes extracted conversion mechanics, not generic competitor inspiration.
- [ ] Output includes concrete A/B test recommendations.
- [ ] Documentation references the Brain wiki note above.
