# Creator Commerce Ops Playbook

> Use when you need a fixture-testable creator commerce workflow without requiring live platform APIs.

---

## Outcome

Run creator partnerships like a governed channel with explicit rights, disclosures, affiliate tracking, and GMV evidence.

This playbook aligns with:

- `kai/audits/creator_commerce.py`
- `harness/references/creator-disclosure.md`
- `kai/memory/schemas.py` (`creator_performance` layer)

---

## OSS-first workflow

1. Build a creator fixture pack.
2. Run the creator commerce audit.
3. Review findings and score.
4. Fill disclosure and rights gaps.
5. Log creator performance memory entries.
6. Generate the next action queue.

Run locally:

```bash
python -m pytest tests/test_creator_commerce_audit.py
python -m pytest tests/test_creator_memory_schemas.py
```

---

## Fixture pack minimum schema

Use local JSON/YAML fixture data with these sections:

- `creators[]`: `creator_id`, `platform`, `follower_count`, `engagement_rate`
- `rate_cards[]`: `creator_id`, `deliverables`, `rate_usd`, `usage_rights_days`, `whitelisting_allowed`
- `rights_policy`: `usage_rights_required`, `platform_disclosure_required`, `ftc_disclosure_template`
- `affiliate`: `enabled`, `tracking_template`, `payout_terms`
- `sku_economics[]`: `sku`, `gross_margin`, `commission_rate`, `sample_cost`, `shipping_cost`, `refund_rate`, `inventory_on_hand`
- `performance`: `attributed_gmv`, `order_count`, `attribution_window_days`, `organic_baseline`, `incrementality_method`

If live account data is missing, record it as a data gap. Do not guess.

---

## Channel-specific use cases (no live credentials required)

### TikTok Shop

- Track creator post type, SKU mentions, and offer codes in fixtures.
- Require explicit disclosure language and in-video disclosure signal.
- Capture `usage_rights_days` before approving whitelisting.
- For GMV Max, record authorized affiliate posts, product IDs, same-day attribution window, organic baseline, and whether affiliate/organic orders are included in dashboard GMV.
- Do not call GMV Max-reported GMV incremental unless a holdout, geo split, or matched baseline supports it.

### YouTube Shopping

- Track creator integration type (dedicated video, mid-roll mention, Shorts cut).
- Require affiliate link disclosure near the first visible links.
- Capture per-asset reuse rights for paid cutdowns.

### Amazon creator programs

- Track storefront or associate-style referral IDs in fixture URLs.
- Require affiliate disclosure at the first product recommendation.
- Record SKU-level GMV and payout assumptions as traceable fixture values.

### Generic affiliate programs

- Use deterministic UTM and affiliate ID templates.
- Store payout terms and attribution windows in the fixture.
- Flag any campaign without a matching disclosure template.

---

## Rights and disclosure gate

A creator campaign is blocked until all are true:

- `usage_rights_required` is true.
- `platform_disclosure_required` is true.
- `ftc_disclosure_template` is present.
- Every active rate card has explicit usage-rights duration.
- Each creator or UGC asset has a planned usage surface: organic, Spark/Partnership ad, paid cutdown, landing page, email, or marketplace listing.
- Each AI-generated, avatar, voice clone, or materially edited asset has platform disclosure status recorded.

Pre-publish requirement:

- Run the checklist in `harness/references/creator-disclosure.md` and hold launch on any failure.

---

## Contract and SOW clause templates

Use these starter clauses in creator agreements:

1. Disclosure duty:
   "Creator must disclose all material connections clearly and conspicuously in each sponsored or affiliate asset, including platform-native paid-partnership labels where available."
2. Usage-rights window:
   "Brand may reuse approved assets for {{usage_rights_days}} days in approved channels only."
3. Whitelisting scope:
   "Paid whitelisting/boosting requires explicit written approval per asset and is limited to the agreed campaign period."
4. Affiliate attribution:
   "Creator must use provided affiliate/UTM links exactly; modified links void attribution credit."
5. Compliance remediation:
   "Missing or non-compliant disclosures must be corrected before publication; repeated non-compliance pauses deliverables."

Add these fields to each statement of work:

- `jurisdiction_preset` (`us_ftc`, `uk_asa`, `eu_ucpd`)
- `disclosure_template`
- `usage_rights_days`
- `whitelisting_allowed`
- `affiliate_tracking_template`
- `ai_synthetic_media_allowed`
- `paid_amplification_surfaces`
- `asset_approval_required`

---

## SKU economics and GMV Max caveats

Run this calculation before creator scale:

```text
contribution_after_creator =
  sku_revenue
  - cogs
  - shipping
  - platform_fee
  - creator_commission
  - sample_cost_allocated
  - refund_reserve
  - paid_media_spend
```

Required decision fields:

| Field | Decision Use |
|-------|--------------|
| `organic_baseline` | Detect cannibalization from paid amplification |
| `creator_authorization_state` | Confirms Spark/Shop/Partnership ad permission |
| `rights_expires_at` | Prevents expired assets from staying live |
| `disclosure_evidence_url` | Proves material connection disclosure |
| `sku_margin_after_commission` | Caps bids and commission tiers |
| `incrementality_method` | Separates platform attribution from causal lift |

GMV Max caveat: TikTok states Product GMV Max can attribute orders for promoted products, including organic and affiliate orders, in the GMV Max dashboard. Report it as TikTok-attributed channel GMV until a causal read exists.

---

## Creator performance memory writeback

Persist each campaign slice to `creator_performance` entries with:

- `creator_id`, `platform`, `campaign_id`
- `spend_usd`, `attributed_revenue_usd`, `gmv_usd`
- `incrementality_method`
- `contribution_after_creator_usd`
- `disclosure_compliant`
- `usage_rights_expires_at`
- `whitelisting_enabled`

Use this layer to surface:

- expiring usage rights in the next 14 days
- non-compliant disclosure records
- top creators by platform-attributed ROAS and by margin-adjusted contribution, labeled separately

---

## Example action queue

1. Pause creators missing disclosure compliance.
2. Refresh rights for creators expiring within 14 days.
3. Standardize affiliate link templates by platform.
4. Reallocate spend toward creators with valid rights, clear disclosures, and margin-adjusted contribution.
5. Re-run audit after updates and record deltas.

---

## Sources (Verified 2026-05-16)

### US legal baseline

- FTC, Disclosures 101 for Social Media Influencers: https://www.ftc.gov/influencers
- FTC, Endorsement Guides FAQ: https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides
- 16 CFR 255.5, Disclosure of material connections: https://www.law.cornell.edu/cfr/text/16/255.5
- FTC, Consumer Reviews and Testimonials Rule Q&A (effective Oct 21, 2024): https://www.ftc.gov/business-guidance/resources/consumer-reviews-testimonials-rule-questions-answers
- FTC, CAN-SPAM compliance guide: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business

### Platform policy and creator program references

- YouTube paid promotions disclosure workflow: https://support.google.com/youtube/answer/154235?hl=en-GB
- YouTube Partner Program eligibility: https://support.google.com/youtube/answer/72851?hl=en
- TikTok branded/commercial disclosure setting: https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/promoting-a-brand-product-or-service
- TikTok Creator Rewards Program context: https://support.tiktok.com/en/business-and-creator/tiktok-creator-fund-us/where-can-i-view-my-funds-us
- X Paid Partnerships policy: https://help.x.com/en/rules-and-policies/paid-partnerships-policy.html
- X Creator Monetization Standards: https://help.x.com/en/rules-and-policies/content-monetization-standards
- Twitch branded content policy: https://help.twitch.tv/s/article/branded-content-policy?language=en_US
- Pinterest paid partnerships for creators: https://help.pinterest.com/en/business/article/paid-partnerships-for-creators
- Snapchat monetization program: https://help.snapchat.com/hc/en-us/articles/14669003687444-About-Snapchat-s-Monetization-Program
- Snapchat paid partnership labeling flow: https://help.snapchat.com/hc/en-us/articles/18418085836948-How-do-I-label-my-sponsored-content-as-a-Paid-Partnership
- Amazon Associates Operating Agreement disclosure language: https://affiliate-program.amazon.com/help/operating/agreement

### UK / EU reference points

- ASA/CAP social media ad-recognition guidance: https://www.asa.org.uk/advice-online/recognising-ads-social-media.html
- EU Unfair Commercial Practices Directive overview: https://commission.europa.eu/law/law-topic/consumer-protection-law/unfair-commercial-practices-and-price-indication/unfair-commercial-practices-directive_en
