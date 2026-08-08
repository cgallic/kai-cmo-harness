# Funnel Hack / Offer Architecture Playbook

> **Use when:** Running ecommerce, DTC, CRO, pricing, landing-page, or checkout audits where the page may convert because of commercial mechanics rather than visual taste.

---

## Source Note

This module was added from issue #12 after Connor dropped the IM8 teardown for ingestion.

- TikTok source: `https://www.tiktok.com/@brendenbuilds/video/7639399895471901966`
- Brain wiki note: `http://agent:8770/page/im8-ecommerce-funnel-hacking-pattern`
- Brain event: `1072339`

Core lesson: do not copy the brand aesthetic first. Extract the offer mechanics that make the buying path feel obvious, lower-risk, and economically tilted.

---

## When This Is Required

Run this module before recommending landing-page, product-page, pricing, or checkout changes for:

- Ecommerce stores
- DTC products
- Subscription products
- Supplement, beauty, food, fitness, pet, home, and creator products
- CRO audits where paid traffic is part of the growth plan
- Any funnel where the current critique starts with "this page is ugly"

Ugly can convert. Pretty can stall. The audit has to prove which mechanic is doing the work.

---

## Required Workflow

1. Identify scaled competitors or adjacent brands with active paid spend.
2. Inspect Meta Ads Library, Google ads, TikTok Shop, Amazon, Pinterest, or creator ads where available.
3. Archive the landing page, offer stack, pricing selector, checkout path, upsells, post-purchase hooks, and retention incentives.
4. Separate conversion mechanics from visual taste.
5. Convert the mechanics into explicit A/B test hypotheses.

Do not write recommendations until steps 1-4 are complete or listed as data gaps.

---

## Source Evidence Standard

Every teardown needs at least one source artifact per inspected funnel:

- Landing-page URL
- Meta Ads Library URL
- Google ad evidence
- TikTok / TikTok Shop URL
- Screenshot path
- Archived notes with date and observer
- Checkout recording or step notes

Client-facing claims must cite the source artifact. Missing data goes in `_data-gaps.md`.

---

## Offer / Pricing Matrix

Create one row per purchase path.

| Brand | Source | Purchase Path | Price | Billing Model | Quantity / Term | Default? | Bonuses | Retention Hook | Risk Reversal |
|-------|--------|---------------|-------|---------------|-----------------|----------|---------|----------------|---------------|
| IM8 | TikTok + archived page | 90-day subscription | TBD | Subscription | 90-day supply | Yes | Free gifts stacked | Continued subscription unlocks more gifts | TBD |
| IM8 | TikTok + archived page | One-time purchase | TBD | One-time | TBD | No | Fewer/no gifts | None observed | TBD |

Use `TBD` only when the artifact does not show the field. Do not guess.

---

## Mechanics To Extract

For each competitor, label the mechanics explicitly:

- Default purchase path
- Subscription vs one-time purchase framing
- Price anchoring
- Bonus/free-gift stacking
- Forced-choice architecture
- Checkout friction/removal
- Upsell/downsell structure
- Retention incentives
- Risk reversal

Write mechanics in this format:

```text
Mechanic: Subscription default
Observed evidence: 90-day subscription is visually and commercially primary.
Why it may work: It makes the higher-LTV path feel like the normal choice.
What not to copy: Exact styling, colors, or page clutter unless the artifact proves those elements matter.
Testable version: Preselect subscription with visible savings and cancel-anytime copy.
```

---

## IM8 Example Pattern

The IM8 teardown points at these mechanics:

- Subscription is the primary path.
- 90-day subscription supply gets stacked free gifts.
- Continued subscription unlocks more gifts.
- One-time purchase is minimized and priced high, anchoring subscription as the better choice.
- The page may violate design instincts while still converting.

The test is not "make our page look like IM8." The test is "does this offer architecture improve subscription attach rate, AOV, and purchase conversion without increasing refunds?"

---

## A/B Test Hypothesis Template

Use one mechanic per test.

```text
We believe that [mechanic change]
for [audience segment]
will [expected KPI movement]
because [mechanic reasoning].
We will measure [primary metric] and guardrail [risk metric]
over [time window].
Success = [specific threshold].
```

Examples:

1. Test subscription as the default against one-time as the default. Measure subscription attach rate, checkout conversion, AOV, and refund rate.
2. Test a 90-day supply bonus stack against the current offer. Measure AOV, conversion rate, and support complaints.
3. Test a high one-time anchor beside a lower subscription price. Measure subscription attach rate and total revenue per visitor.
4. Test a continuity gift unlocked on shipment two. Measure subscription retention through 60 days.

---

## Audit Output Requirements

Every ecommerce/CRO audit using this module must include:

- Source URLs, screenshots, or archived notes for inspected funnels
- Offer/pricing matrix
- Extracted mechanics, not generic inspiration
- Visual taste vs conversion mechanic notes
- A/B test recommendations with primary metric and guardrail metric
- Data gaps for missing source evidence, checkout access, ad visibility, or pricing

---

## Anti-Patterns

- Copying the page design before extracting the mechanic
- Calling a competitor "best practice" with no source artifact
- Reporting a price, review count, ad spend, or conversion claim without source data
- Recommending a subscription default without checking refund, churn, or complaint risk
- Running multi-variable tests that change offer, design, copy, and checkout all at once

---

## Handoff Checklist

- [ ] At least 2 competitor or adjacent funnels inspected
- [ ] Active paid spend or peer imitation signal noted
- [ ] Source artifact saved for each funnel
- [ ] Offer/pricing matrix complete or gaps listed
- [ ] Mechanics extracted with evidence
- [ ] Visual taste separated from commercial mechanics
- [ ] A/B tests written as hypotheses
- [ ] Metrics include purchase conversion, AOV, subscription attach rate, refund rate, and retention where relevant
