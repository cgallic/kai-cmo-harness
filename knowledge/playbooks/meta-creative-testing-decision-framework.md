# Meta Creative Testing Decision Framework

## Use When

Use this playbook before launching or pushing Meta ads when the request involves:

- 10 or more new creatives.
- A small daily budget relative to the target CPA.
- Existing winners that could be diluted by new tests.
- A choice between "push everything," "launch a subset," or "hold for review."
- API creation of many ads, especially video ads.

This is the decision layer for Meta creative testing. It sits between strategy and API execution.

## Source Baseline

Load this with:

- `knowledge/channels/meta-advertising.md`
- `knowledge/playbooks/combinatorial-creative-bench.md`
- `knowledge/playbooks/ad-creative-best-practices.md`
- `knowledge/playbooks/ad-campaign-management.md`
- `knowledge/checklists/meta-advertising-checklist.md`
- `harness/references/meta-ads-rules.md`
- `harness/references/meta-ads-api-reference.md` if creating ads by API

External source checks:

- Meta Performance 5: account simplification, fewer ad sets, creative diversification, data quality, and results validation.
  Source: https://www.facebook.com/business/ads/performance-marketing
- Meta ad auction guidance: objective, budget, duration, audience, and creative all shape auction performance.
  Source: https://www.facebook.com/business/ads/ad-auction
- Meta budget guidance: set enough budget for at least seven days so delivery can learn; broader audiences often improve efficiency.
  Source: https://www.facebook.com/business/ads/pricing
- Meta Advantage+ creative: varied creative helps Meta tailor message and format to each viewer.
  Source: https://www.facebook.com/business/ads/meta-advantage-plus/creative
- Meta Advantage+ app campaigns: Meta explicitly supports testing up to 50 creatives when creative variety and budget are sufficient.
  Source: https://www.facebook.com/business/ads/meta-advantage-plus/app-campaigns

## Core Principle

Do not confuse upload volume with test volume.

It is fine to create many ads paused for review. It is usually weak testing to activate many ads in one underfunded ad set. Meta will allocate spend to a few likely winners, and most creatives will get too little data to prove anything.

## Budget Reality Check

Use this test before recommending a launch structure:

```
minimum_weekly_learning_budget = target CPA x 50
minimum_daily_learning_budget = minimum_weekly_learning_budget / 7
```

If the budget is below the daily learning budget, say so plainly and move the campaign to an earlier signal:

- Lead form opens.
- Landing page views.
- Calls.
- Qualified clicks.
- Video holds.
- Form starts.

If the target CPA is unknown, infer it from recent account data when available. Otherwise mark the recommendation as a low-budget signal test, not a conversion-learning test.

## Creative Count Rules

| Situation | Active Creative Count | Structure |
|-----------|----------------------|-----------|
| Budget below target CPA per day | 3-6 active ads | One ad set, strongest distinct hooks |
| Budget supports one conversion every 1-2 days | 6-9 active ads | One ad set, diverse angles |
| Budget supports learning target | 10-20 active ads | Consolidated ad set or Advantage+ setup |
| Mature account with strong data and real variety | Up to 50 active creatives | Advantage+ or consolidated campaign |
| Bulk asset staging or client review | Any count paused | Create all ads paused, activate only the test set |

These are defaults, not laws. Override them only with account evidence.

## Decision Tree

1. Check the goal.
   - Use leads or purchases only when conversion volume is plausible.
   - Use an earlier event when the budget cannot fund learning.

2. Check existing winners.
   - Keep proven ad sets intact when they are producing target CPA.
   - Do not inject a large batch into a winner unless the goal is creative refresh and the budget supports it.

3. Check creative diversity.
   - Count ideas, not files.
   - Different captions over similar footage are iterations, not distinct tests.
   - Tag each candidate with Persona, Desire, and Angle when the batch is concept-heavy.
   - Prioritize different hooks, visual openings, proof types, personas, and offers.

4. Pick the launch mode.
   - **Staged review:** create all ads paused with tracking and naming complete.
   - **Signal test:** activate 3-6 strongest ads when budget is tight.
   - **Learning test:** activate 6-20 ads when budget and events are sufficient.
   - **Scale refresh:** add new creative to the existing winning structure only when the account is stable.

5. Write a decision memo before spending.
   - Include the rejected alternative.
   - Include the budget tradeoff.
   - Include which ads go active now and which stay paused.

## Required Decision Memo

Before activating a Meta batch with 10 or more creatives, write:

```markdown
# Meta Creative Testing Decision Memo

## Situation
- Existing winner(s):
- New creatives:
- Objective:
- Budget:
- Target CPA or recent CPA:
- Landing page:

## Recommendation
- Create:
- Activate:
- Keep paused:
- Ad set/campaign status:

## Why
- Learning/budget:
- Creative diversity:
- Winner protection:
- Measurement:

## Rejected Option
- Option:
- Reason rejected:

## First Review
- Day 1:
- Day 3:
- Day 7:
- Kill criteria:
```

Save it as `workspace/ads/_meta-creative-testing-decision.md` when writing workspace artifacts.

## Default For 24 Owner-Voice Videos At $6/Day

If there are 24 owner-voice clips, an existing winner near target CPA, and a $6/day test budget:

1. Create all 24 ads paused if the user wants them staged in Ads Manager.
2. Do not activate all 24 at once.
3. Protect the existing winner in its current ad set.
4. Launch the strongest 3-6 distinct clips in a new ad set.
5. Strip organic "comment keyword" CTAs and hashtags from paid primary text.
6. Use the first hook as the headline or title when it fits character limits.
7. Use `utm_content` set to the clip slug.
8. Review after enough spend for signal, not after a fixed clock interval alone.

Reason: $6/day cannot fairly test 24 ads for conversion learning. It can stage assets or run a narrow signal test.

## Creative Selection Score

Score each candidate 0-2 on each factor:

| Factor | 0 | 1 | 2 |
|--------|---|---|---|
| Hook clarity | Generic | Clear but slow | Clear in first 3 seconds |
| Visual distinction | Same as others | Some distinction | Obvious new pattern |
| Persona match | Vague | Partial | Direct pain or desire |
| Proof | None | Implied | Specific proof or mechanism |
| CTA fit | Organic-only | Usable with edits | Paid-native and direct |
| Landing match | Weak | Acceptable | Tight promise match |

Activate the highest-scoring set with maximum angle diversity.

## Review Rules

Evaluate the ad set first, then individual ads.

- Day 1: confirm spend, approvals, links, UTMs, and event firing.
- Day 3: remove obvious dead creative only if it has spend and no useful signal.
- Day 7: compare CPA, CTR, CPC, hook retention, and lead quality.
- Kill an ad after it spends 2x target CPA with no conversion, or after 1,000 impressions with CTR below the account threshold.
- For high-volume tests, kill a concept when CPA is more than 1.5x target after 72 hours and 50+ conversions.
- Keep high-spend ads that support the best blended CPA, even when another ad has a lower isolated CPA at tiny spend.

## Anti-Patterns

- Activating 20+ ads in one low-budget ad set and calling it a fair test.
- Adding a large unproven batch into a proven winner's ad set.
- Splitting each creative into its own ad set without enough budget.
- Treating organic captions as paid copy without editing.
- Judging individual ads before they receive meaningful delivery.
- Making large edits during the learning period unless tracking or compliance is broken.
