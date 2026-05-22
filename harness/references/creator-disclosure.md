# Creator Disclosure Reference

**Purpose:** Local policy reference for creator commerce audits and briefs in OSS mode.

This document is a practical execution reference. It does not replace legal review.

---

## Core rules

1. Disclose material relationships clearly and early.
2. Keep disclosure visible where the endorsement appears.
3. Match disclosure format to the channel surface (video, caption, description, livestream, story).
4. Record disclosure compliance in campaign evidence and creator performance memory.
5. Re-check disclosure and rights before paid amplification, not only before organic posting.

---

## Required minimum disclosure components

- Sponsorship or compensation signal (`Ad`, `Sponsored`, or equivalent clear language)
- Affiliate relationship signal where affiliate links/codes are present
- Brand name or partnership context where platform tools do not provide a native label
- AI-generated, synthetic media, avatar, or voice-clone status where platform policy requires it

---

## Platform implementation notes

### TikTok Shop

- Use clear sponsored labeling in caption and/or native paid-partnership tools.
- If affiliate links or codes are used, include affiliate disclosure in the visible post context.
- Keep disclosure visible before users must expand long captions.
- For Spark Ads, Shop Ads, affiliate creatives, or GMV Max usage, record creator authorization and commercial-content label status per asset.
- For Symphony or other AI-generated assets, record AI-generated label status and human review.

### YouTube Shopping

- Include paid partnership disclosure in the video and description.
- Put affiliate disclosure near the first affiliate link block.
- Reuse edits for ads only if usage rights are explicitly granted.

### Amazon creator/associate workflows

- Use affiliate disclosure adjacent to product recommendation sections.
- Avoid ambiguous language that hides compensation.
- Maintain fixture evidence for referral IDs and payout terms.

### Generic affiliate channels

- Place disclosure in the first meaningful content block, not buried at the end.
- Use deterministic templates so audit checks can detect compliance.

---

## Approved template examples

- `Paid partnership with {{brand}}.`
- `This post includes affiliate links. I may earn a commission from qualifying purchases.`
- `Sponsored by {{brand}}. Some links are affiliate links.`

---

## Audit mapping

The creator audit marks a high-severity finding when any of these are missing:

- `rights_policy.usage_rights_required = true`
- `rights_policy.platform_disclosure_required = true`
- `rights_policy.ftc_disclosure_template` is not empty

Rate cards should also include:

- `usage_rights_days`
- `whitelisting_allowed`

---

## Evidence checklist per creator asset

- Asset ID and platform
- Disclosure text used
- Sponsorship or affiliate status
- Usage-rights duration and expiration date
- Whitelisting permission state
- Paid amplification surface and authorization method
- AI/synthetic-media status and disclosure label
- Tracking link template or affiliate ID

---

## Pre-publish gate checklist

Do not publish until every item below is true:

- Material connection is present in-post (`Ad`, `Sponsored`, paid partnership label, or equivalent).
- Disclosure is visible before truncation/expand actions.
- Affiliate links/codes include affiliate disclosure language.
- Platform-native paid partnership toggle/label is enabled where available.
- Rights window allows this usage (organic, paid whitelist, or repurposed edit).
- AI/synthetic-media labels are enabled where required.
- Evidence row is captured in fixture/log (`platform`, `asset_id`, `disclosure_text`, `toggle_state`).

Gate result:

- `pass`: all items true
- `hold`: one or more missing

---

## Jurisdiction presets

Use these presets as default operating modes:

| Preset | Required baseline |
|---|---|
| `us_ftc` | Clear material-connection disclosure, in-context, per-post; affiliate disclosure when links/codes exist. |
| `uk_asa` | Upfront ad recognition label (commonly `#ad`) that is immediately obvious. |
| `eu_ucpd` | Commercial intent must be transparent; hidden advertising prohibited. |

Machine-readable preset file:

- `harness/references/creator-disclosure-presets.json`

---

## Sources (Verified 2026-05-16)

### Core legal references

- FTC influencer disclosure guide: https://www.ftc.gov/influencers
- FTC Endorsement Guides FAQ: https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides
- 16 CFR 255.5 (material connection disclosures): https://www.law.cornell.edu/cfr/text/16/255.5
- FTC Consumer Reviews/Testimonial Rule Q&A: https://www.ftc.gov/business-guidance/resources/consumer-reviews-testimonials-rule-questions-answers
- FTC CAN-SPAM compliance guide: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business

### Platform disclosure references

- YouTube paid promotion declarations: https://support.google.com/youtube/answer/154235?hl=en-GB
- TikTok content disclosure setting: https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/promoting-a-brand-product-or-service
- X paid partnerships disclosure policy: https://help.x.com/en/rules-and-policies/paid-partnerships-policy.html
- Twitch branded content disclosure tool: https://help.twitch.tv/s/article/branded-content-policy?language=en_US
- Pinterest paid partnership label flow: https://help.pinterest.com/en/business/article/paid-partnerships-for-creators
- Snapchat paid partnership label flow: https://help.snapchat.com/hc/en-us/articles/18418085836948-How-do-I-label-my-sponsored-content-as-a-Paid-Partnership
- Amazon Associates required affiliate disclosure statement: https://affiliate-program.amazon.com/help/operating/agreement

### UK / EU enforcement context

- ASA/CAP influencer ad recognition guidance: https://www.asa.org.uk/advice-online/recognising-ads-social-media.html
- EU unfair commercial practices baseline: https://commission.europa.eu/law/law-topic/consumer-protection-law/unfair-commercial-practices-and-price-indication/unfair-commercial-practices-directive_en
