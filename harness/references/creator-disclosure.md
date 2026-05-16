# Creator Disclosure Reference

**Purpose:** Local policy reference for creator commerce audits and briefs in OSS mode.

This document is a practical execution reference. It does not replace legal review.

---

## Core rules

1. Disclose material relationships clearly and early.
2. Keep disclosure visible where the endorsement appears.
3. Match disclosure format to the channel surface (video, caption, description, livestream, story).
4. Record disclosure compliance in campaign evidence and creator performance memory.

---

## Required minimum disclosure components

- Sponsorship or compensation signal (`Ad`, `Sponsored`, or equivalent clear language)
- Affiliate relationship signal where affiliate links/codes are present
- Brand name or partnership context where platform tools do not provide a native label

---

## Platform implementation notes

### TikTok Shop

- Use clear sponsored labeling in caption and/or native paid-partnership tools.
- If affiliate links or codes are used, include affiliate disclosure in the visible post context.
- Keep disclosure visible before users must expand long captions.

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
- Tracking link template or affiliate ID
