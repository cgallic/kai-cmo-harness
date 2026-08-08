# Creative Test Resolution Protocol

> **Use when:** Reading paid creative tests, deciding whether a result is valid, or converting performance data into kill / iterate / graduate decisions.

---

## Core Thesis

A creative test is not resolved when money is spent. It is resolved when the team can make a decision without guessing.

Every test must define:

- The hypothesis.
- The control or baseline.
- The single variable being tested.
- The data floor.
- The read window.
- The decision states.

No pre-defined read rules means the test becomes opinion theater.

---

## Source Baseline

Load this with:

- `knowledge/playbooks/combinatorial-creative-bench.md`
- `knowledge/playbooks/creative-intelligence-ledger.md`
- `knowledge/playbooks/meta-creative-testing-decision-framework.md`
- `knowledge/checklists/ad-launch-checklist.md`

External reference points:

- ATTN systematic creative testing: uses monthly cycles, controls, historical baselines, single-variable changes, and minimum floors of `$500+ spend`, `1,000+ impressions`, `72+ hours` for initial assessment, and `7+ days` for final performance review.
  Source: https://www.attnagency.com/blog/dtc-creative-testing-systematic-approach
- Motion ad reverse-engineering: diagnoses hook, messaging angle, pain/desire anchor, persona, awareness stage, format, and creative mechanic.
  Source: https://motionapp.com/library/frameworks/creative-analysis
- Google Performance Max asset groups: cover all asset types, create variations, and wait `2-3 weeks` before replacing low-performing assets after edits.
  Source: https://support.google.com/google-ads/answer/14528220

---

## Test Object

Write this before launch:

| Field | Required? | Notes |
|-------|-----------|-------|
| `test_id` | Yes | Use `TEST-{date}-{platform}-{nn}` |
| `concept_id` | Yes | From the P.D.A. bench |
| `hypothesis` | Yes | What should improve, for whom, and why |
| `control` | Yes | Current winner, account average, or historical baseline |
| `variable` | Yes | One changed element |
| `constant_elements` | Yes | What must not change |
| `primary_metric` | Yes | CPA, ROAS, CVR, qualified lead rate, etc. |
| `guardrail_metrics` | Yes | CTR, CPC, CPM, frequency, lead quality, comments |
| `data_floor` | Yes | Spend / impression / conversion / time requirements |
| `read_window` | Yes | Initial and final read dates |
| `decision_states` | Yes | Kill / iterate / graduate / inconclusive / invalid |

---

## Variable Isolation

Change one meaningful thing at a time.

Good variables:

- Hook: first line, opening frame, text overlay, pattern interrupt.
- Proof: review, demo, stat, customer story, founder claim.
- Format: UGC, founder, static, carousel, screen recording.
- Persona: one audience situation.
- Desire: one desired progress state.
- Angle: one story, mechanism, or objection frame.
- Offer: price, guarantee, audit, trial, consultation, bundle.

Bad variables:

- New hook, new offer, new landing page, and new audience at once.
- New creator plus new claim plus new CTA.
- Different products inside the same test cell.
- Comparing a fresh ad against a fatigued control without noting fatigue.

Use multi-variable tests only after single-variable reads have created stable learnings.

---

## Data Floors

Use all applicable floors. Do not declare a winner or loser before the relevant floor is met.

| Floor | Default | Use When |
|-------|---------|----------|
| Spend | `$500+ per variant` or `2 x target CPA` | Conversion tests with enough budget |
| Impressions | `1,000+ per creative` | CTR, hook, or thumb-stop reads |
| Time | `72+ hours` | Initial read on paid social |
| Final window | `7+ days` | Stable CPA / ROAS decision |
| Conversions | `50+ conversions` | CPA confidence and learning-phase judgment |

Low-budget exception:

When budget cannot support conversion floors, state that the test is a signal test. Use an earlier event such as qualified clicks, landing page views, form starts, call clicks, video holds, or lead form opens.

---

## Decision States

### Kill

Use when the concept fails after valid floors.

Examples:

- Spend reaches `2 x target CPA` with 0 conversions.
- CPA is `>1.5 x target` after 72h and 50+ conversions.
- CTR is below account threshold after 1,000 impressions.
- Comments or feedback create account or brand risk.

Required output: one loser lesson.

### Iterate

Use when the concept shows partial signal but the execution is weak.

Examples:

- CTR is strong, but conversion rate is weak.
- Hook rate is strong, but middle retention drops.
- Leads are cheap, but low quality.
- Comments show interest but reveal a missing proof point.

Required output: one variable to change next.

### Graduate

Use when the concept beats the control or account baseline.

Examples:

- CPA is at or below target for 5+ days.
- CPA is 20% better than account average.
- ROAS beats target and quality holds.
- Qualified lead rate holds after sales review.

Required output: winner iteration plan and scaling limit.

### Inconclusive

Use when data floors are not met or the read is too noisy.

Examples:

- Under-spent variant.
- Delivery skewed heavily to one ad.
- Seasonality or promo distorted the read.
- Conversion tracking lag is too high.

Required output: relaunch, extend, or stop.

### Invalid

Use when the test setup broke.

Examples:

- Pixel, CAPI, UTM, lead form, phone tracking, or checkout broke.
- Ads were disapproved for part of the window.
- Landing page changed mid-test.
- Budget or audience changed enough to reset learning.

Required output: fix the setup before reading performance.

---

## Platform Exceptions

### Meta

Evaluate at ad set or campaign level first. Meta can spend more on a creative that appears worse at the ad level because it supports better blended CPA at scale.

Use individual-ad reads only after the ad receives meaningful delivery.

### Google Performance Max

Do not replace low-rated assets too quickly. Google recommends waiting `2-3 weeks` before replacing low-performing assets after edits.

Asset groups should cover text, images, and videos. Missing asset types can make the test about inventory coverage, not creative quality.

### TikTok

Use TikTok Creative Insights before production to identify platform-native patterns, but do not treat Creative Insights metrics as forecasted performance. TikTok says those metrics are approximate and should not be used for benchmarking.

---

## Test Resolution Memo

Save one memo per meaningful test:

```markdown
# Creative Test Resolution Memo

## Test Setup
- Test ID:
- Concept ID:
- Platform:
- Campaign / ad set:
- Hypothesis:
- Control / baseline:
- Variable:
- Constant elements:
- Primary metric:
- Guardrail metrics:

## Data Floors
- Spend:
- Impressions:
- Conversions:
- Time in market:
- Read window:
- Floors met: yes / no

## Result
- Decision: kill / iterate / graduate / inconclusive / invalid
- Performance vs control:
- Performance vs account average:
- Lead / purchase quality:
- Tracking notes:

## Learning
- What worked:
- What failed:
- Why we think it happened:
- Next action:
- Ledger row added: yes / no
```

---

## Weekly Review Loop

1. Check test validity before performance.
2. Mark each row kill / iterate / graduate / inconclusive / invalid.
3. Write a ledger row for every resolved test.
4. Move winners into the 60% bucket.
5. Convert partial winners into adjacent tests.
6. Archive invalid tests separately from true losers.
7. Update the next P.D.A. bench with the strongest lesson.

---

## Anti-Patterns

- Declaring a winner before the control is named.
- Reading CPA before enough conversions exist.
- Killing a concept because one execution variant failed.
- Calling an invalid test a loser.
- Scaling a cheap lead source before sales quality is checked.
- Ignoring comments and call notes because platform CPA looks good.
- Testing the same idea again without writing the prior loser lesson.
