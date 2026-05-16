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
- `performance`: `attributed_gmv`, `order_count`, `attribution_window_days`

If live account data is missing, record it as a data gap. Do not guess.

---

## Channel-specific use cases (no live credentials required)

### TikTok Shop

- Track creator post type, SKU mentions, and offer codes in fixtures.
- Require explicit disclosure language and in-video disclosure signal.
- Capture `usage_rights_days` before approving whitelisting.

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

---

## Creator performance memory writeback

Persist each campaign slice to `creator_performance` entries with:

- `creator_id`, `platform`, `campaign_id`
- `spend_usd`, `attributed_revenue_usd`, `gmv_usd`
- `disclosure_compliant`
- `usage_rights_expires_at`
- `whitelisting_enabled`

Use this layer to surface:

- expiring usage rights in the next 14 days
- non-compliant disclosure records
- top creators by ROAS

---

## Example action queue

1. Pause creators missing disclosure compliance.
2. Refresh rights for creators expiring within 14 days.
3. Standardize affiliate link templates by platform.
4. Reallocate spend toward highest-ROAS creators with valid rights.
5. Re-run audit after updates and record deltas.
