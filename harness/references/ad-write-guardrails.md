# Ad Write Guardrails

Use these guardrails for every paid-media connector, upload flow, and automation that can change a live ad account.

## Default Mode

Paid media starts read-only. The first useful system should pull account data, validate uploads, flag anomalies, generate recommendations, and produce dry-run payloads without mutating campaigns.

Read-only actions:

- Pull campaign, ad set, ad, search term, audience, budget, and performance snapshots.
- Evaluate ads and produce recommendations.
- Validate ad upload files, copy, tracking, policy fit, and platform field mapping.
- Produce structured draft payloads for human review.

## Write Access Rule

No paid-media write should auto-execute. A human must approve every action that creates, publishes, pauses, activates, changes bids, changes budgets, changes targeting, uploads an asset to a live account, or adds/removes keywords.

New ads and campaigns must be created in `PAUSED` or draft state. Activation is a separate action with its own approval.

## Required Pre-Flight

Every paid-media mutation must include:

- `account_id` or `ad_account_id` from an allowlisted account.
- Platform and entity IDs for the target campaign, ad set, ad group, or ad.
- A dry-run preview or explicit before/after diff.
- Evidence for the recommendation, such as a collector snapshot, reporting export, anomaly record, or policy check.
- Policy compliance result for the target platform.
- Audit log entry linking the proposal, approval, API response, and verification result.

## Spend Guardrails

Bid and budget changes require stricter controls:

- Current value and proposed value.
- Percent increase calculation.
- Per-change cap.
- Daily budget cap.
- Bid increase cap.
- Account/campaign/ad set allowlist.
- Rollback reference or reversal steps.

Default caps:

- Budget increase: max `20%`.
- Bid increase: max `10%`.
- Single budget change: max `$100` unless brand policy sets a lower cap.

Brand policies can tighten these values with `paid_media_guardrails`.

```yaml
paid_media_guardrails:
  allowed_accounts:
    - act_1234567890
  allowed_campaigns:
    - "120000000000001"
  allowed_adsets:
    - "120000000000002"
  allowed_ad_groups:
    - "customers/1234567890/adGroups/987654321"
  max_budget_increase_pct: 20
  max_single_budget_change_usd: 100
  max_daily_budget: 500
  max_bid_increase_pct: 10
  require_rollback_for_activation: true
```

## Blockers

Block the mutation when any of these are true:

- The action is auto-approved.
- The account is not allowlisted.
- A budget or bid change lacks before/after values.
- The diff or dry-run preview is missing.
- Evidence is missing.
- A create/upload action sets status to `ACTIVE`.
- `activate_on_create` is true.
- Activation, launch, pause, bid, or budget changes lack rollback instructions.
- The action exceeds the configured cap.

## Runtime Hook

The executable guard lives in `kai/runtime/policy.py` under `check_paid_media_guardrails()`. The policy result includes the `paid_media_guardrails` dimension and blocks execution before connectors run.
