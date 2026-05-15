# Combinatorial Creative Bench Discipline

> **Use when:** Turning an ad brief into a paid creative bench, deciding which concepts ship, allocating budget across winners and tests, or setting kill / scale rules before launch.

---

## Core Thesis

A brief defines the market bet. A creative bench turns that bet into a managed portfolio of testable concepts.

Do not count files. Count concepts.

```
concept_count = personas x desires x angles
```

Example: `5 personas x 4 desires x 6 angles = 120 concept possibilities`.

A concept is a distinct `Persona x Desire x Angle` hypothesis. Format, creator, edit, caption, and hook are execution choices unless they materially change the audience promise.

---

## Source Baseline

Load this with:

- `knowledge/playbooks/ad-creative-best-practices.md`
- `knowledge/playbooks/creative-test-resolution-protocol.md`
- `knowledge/playbooks/creative-intelligence-ledger.md`
- `knowledge/playbooks/meta-creative-testing-decision-framework.md` for Meta batch activation decisions
- `knowledge/channels/paid-acquisition.md`
- `knowledge/checklists/ad-launch-checklist.md`
- The platform policy reference before writing ads

External reference points:

- Pilothouse P.D.A. framework: Persona, Desire, and Angle produce combinatorial concept diversity for Meta Andromeda.
  Source: https://www.pilothouse.co/post/the-p-d-a-framework-deep-dive-how-to-generate-conceptual-diversity-that-andromeda-actually-rewards
- ATTN 60/30/10 campaign budget rule: proven performers / scaling tests / new experiments.
  Source: https://www.attnagency.com/blog/meta-campaign-budget-optimization
- ATTN creative process: monthly ideation, production, testing, scaling, and Day 3-5 loser pauses.
  Source: https://www.attnagency.com/blog/ad-creative-strategy
- ATTN benchmark article: 60/30/10 creative allocation, 72-hour underperformer retirement, and fast cross-platform scaling.
  Source: https://www.attnagency.com/blog/2026-roas-benchmarks-industry-vertical-performance-standards
- ATTN audience scaling thresholds: pause when CPA exceeds target by 50%.
  Source: https://www.attnagency.com/blog/lookalike-audiences-vs-broad-targeting
- Motion creative strategy / reverse-engineering: tag concepts by pain or desire, persona, messaging angle, awareness stage, hook, format, and creative mechanic.
  Sources: https://motionapp.com/library/frameworks/creative-strategy-engine and https://motionapp.com/library/frameworks/creative-analysis

The exact `72h + 50 conversions + 1.5x CPA` kill rule below is Kai's default operating rule. Treat it as a decision threshold to calibrate with account history, not platform policy.

---

## P.D.A. Concept Grid

### Persona

Who the message is for.

Good persona rows are psychographic and situational, not broad demographics:

- "Admin Martyr handling missed calls after clinic hours"
- "Founder still answering sales calls personally"
- "Operations lead blamed for slow lead response"

### Desire

What progress the persona wants.

Desires should be written in the customer's language:

- "Stop losing after-hours leads"
- "Qualify callers before staff time gets burned"
- "Look responsive without hiring another receptionist"

### Angle

The argument, story, proof type, or frame that connects persona to desire:

- Loss-aversion: "Every missed call is an invisible CAC leak"
- Social proof: "Teams like yours route calls this way"
- Mechanism: "AI answers, qualifies, and books before staff arrives"
- Contrast: "Voicemail collects problems; receptionist AI routes revenue"
- Time math: "The first 60 seconds decide whether the lead stays yours"

### Optional Fourth Axis: Awareness Stage

Add awareness stage when a batch risks over-indexing on one funnel moment:

- Unaware
- Problem-aware
- Solution-aware
- Product-aware
- Most-aware

Expanded math:

```
concept_count = personas x desires x angles x awareness_stages
```

Use the 3-axis P.D.A. grid for concept supply. Add awareness stage when planning cold vs retargeting, educational vs offer-led, or creative for multiple funnel stages.

### Optional Fifth Axis: Format

Add format after the P.D.A. grid exists:

- Founder direct-to-camera
- UGC problem skit
- Screen recording
- Static proof card
- Customer story
- Call transcript reenactment

Format expands production variety. P.D.A. protects conceptual variety.

---

## Bench Row Schema

Every concept row should answer:

| Field | Required? | Notes |
|-------|-----------|-------|
| `concept_id` | Yes | Use `PDA-{persona}-{desire}-{angle}-{nn}` |
| `persona` | Yes | Use a persona slug or short situational label |
| `desire` | Yes | Customer-language desired progress |
| `angle` | Yes | Message frame, proof type, or story route |
| `awareness_stage` | Yes for paid social | Unaware, problem-aware, solution-aware, product-aware, or most-aware |
| `format` | Yes | Video, static, carousel, UGC, founder, demo, etc. |
| `hook` | Yes | First line or first 3 seconds |
| `proof` | Yes | Review, demo, data point, mechanism, example, or "needs proof" |
| `offer` | Yes | The commercial promise attached to the ad |
| `landing_match` | Yes | Page or section that fulfills the ad promise |
| `hypothesis` | Yes | What should happen if this concept is true |
| `portfolio_bucket` | Yes | Winner / adjacent / experiment |
| `budget` | Yes | Planned daily or test budget |
| `kill_rule` | Yes | Named threshold before launch |
| `next_iteration` | Optional | Hook, proof, format, or offer to test next |

---

## Prioritization Score

Score each concept 0-2.

| Factor | 0 | 1 | 2 |
|--------|---|---|---|
| Customer language | Assumed | Light evidence | Reviews, calls, comments, or transcripts |
| Visual distinction | Same as current ads | Some change | Distinct pattern |
| Persona clarity | Generic | Segment implied | Persona obvious in 3 seconds |
| Desire intensity | Nice-to-have | Useful | Urgent business or emotional pressure |
| Awareness-stage fit | Mismatched | Plausible | Right stage for placement |
| Proof availability | None | Indirect | Specific proof ready |
| Landing match | Weak | Acceptable | Same promise and CTA |
| Production speed | Slow | Moderate | Can ship this week |
| Policy risk | High | Needs review | Low |

Default action:

- `13-16`: launch candidate
- `9-12`: adjacent backlog
- `0-8`: hold, rewrite, or kill before production

---

## Portfolio Allocation

Use 60/30/10 once the account has at least one proven concept.

| Bucket | Budget | What Ships | Rule |
|--------|--------|------------|------|
| Winners-iterate | 60% | Variants of concepts already at or below target CPA | Change hook, format, proof, creator, or CTA without changing the core P.D.A. |
| Adjacent | 30% | One-axis moves from winners | Change persona, desire, or angle while holding the other two stable |
| Experimental | 10% | New P.D.A. combinations or new platform-native formats | Make the bet explicit and cap budget |

Stage overrides:

- No winner yet: use `40/40/20` until one concept earns repeatable signal.
- Learning-limited budget: use `70/20/10` and keep only 3-6 active concepts.
- Mature high-volume account: use `60/30/10`, refresh weekly, and keep 6-8 active concept families live.

---

## Budget Adequacy

Use conversion learning math before choosing active count:

```
minimum_weekly_learning_budget = target_cpa x 50
minimum_daily_learning_budget = minimum_weekly_learning_budget / 7
```

If available budget is below learning budget, call the launch a signal test. Optimize for an earlier signal:

- Qualified click
- Landing page view
- Lead form open
- Call click
- Form start
- Video hold

Do not activate a large bench and call it a fair conversion test when the budget cannot fund learning.

---

## Shipping Cadence

Use this weekly loop for active paid social programs:

1. Monday: read winners, fatigued ads, comments, call notes, and landing-page drop-offs.
2. Tuesday: update the P.D.A. grid and score new rows.
3. Wednesday: produce the selected concepts.
4. Thursday: launch or stage ads with UTMs, policy checks, and kill rules.
5. Day 1: verify delivery, links, UTMs, pixels, spend, and approvals.
6. Day 3 / 72h: kill obvious losers only after data floors are met.
7. Day 7: resolve the test, then graduate, iterate, reduce, or archive.
8. After resolution: write the learning to the creative intelligence ledger.

---

## Kill, Graduate, Iterate

### Data Floors

Do not kill for performance before the row has enough signal, unless tracking, policy, or page function is broken.

Minimum floors:

- Spend floor: `2 x target CPA` for no-conversion tests.
- Impression floor: `1,000 impressions` for CTR reads.
- Conversion floor: `50+ conversions` for CPA confidence.
- Time floor: `72 hours` for early high-volume judgment.

For a full decision protocol, use `knowledge/playbooks/creative-test-resolution-protocol.md`.

### Kill Rules

Name the kill rule in the bench before launch.

| Rule | Kill When | Action |
|------|-----------|--------|
| `tracking-broken` | Pixel, CAPI, UTM, checkout, lead form, or phone tracking is broken | Stop spend, fix tracking, relaunch clean |
| `zero-conversion-spend` | Spend reaches `2 x target CPA` with 0 conversions | Kill ad or move to earlier signal test |
| `low-ctr-meta` | CTR is below account threshold after 1,000 impressions | Kill or rewrite hook |
| `high-cpa-72h` | CPA is `>1.5 x target` after 72h and 50+ conversions | Kill or reduce 50% if strategic learning remains |
| `fatigue` | Frequency is >3, CTR falls 30% from peak, or CPA rises 20% week-over-week | Refresh or archive |
| `negative-feedback` | Comments, hides, reports, or review risk threatens account health | Stop and rewrite |

### Graduate Rules

Move a concept to the winner bucket when:

- CPA is at or below target for 5+ days, or 20% better than account average.
- CTR and conversion rate are stable.
- Lead or purchase quality is acceptable.
- The landing page fulfills the ad promise.
- The account can scale without breaking learning.

Scale by increasing budget 20-30% every 2-3 days while CPA holds.

### Iterate Rules

Iterate winners by changing one execution variable at a time:

- Hook: first line, opening frame, or first 3 seconds.
- Proof: review, demo, data point, founder claim, customer story.
- Format: UGC, founder, static, carousel, screen recording.
- Awareness stage: cold education, problem framing, product proof, offer close.
- CTA: quote, demo, call, trial, audit, shop.
- Creator: customer, employee, founder, expert, operator.

Use adjacent tests when the winner seems real but capped. Change one P.D.A. axis while holding the other two stable.

---

## Example Bench Math

For KaiCalls:

| Axis | Count | Example Values |
|------|-------|----------------|
| Personas | 4 | Admin Martyr, System Manager, local business owner, office manager |
| Desires | 5 | capture missed calls, qualify leads, reduce admin load, book appointments, sound responsive |
| Angles | 6 | loss math, after-hours proof, staff relief, mechanism demo, owner story, voicemail contrast |
| Awareness stages | 3 | problem-aware, solution-aware, product-aware |

```
4 personas x 5 desires x 6 angles = 120 possible concepts
4 personas x 5 desires x 6 angles x 3 awareness stages = 360 possible staged concepts
```

Ship a first batch from the highest-scoring 8-12 rows. Do not produce all 120 or 360. The grid creates options; the bench chooses work.

---

## Pre-Launch Gate

Before a paid creative batch ships:

- [ ] P.D.A. grid exists.
- [ ] Each ad has a `concept_id`.
- [ ] Awareness stage is tagged for paid social batches.
- [ ] Selected concepts include real conceptual diversity, not only caption or crop changes.
- [ ] Portfolio bucket is assigned: winner, adjacent, or experiment.
- [ ] Budget can support the active count.
- [ ] Kill rule is named for each active row.
- [ ] Test resolution memo has a control, variable, data floor, and read window.
- [ ] Landing page matches the concept promise.
- [ ] Platform policy reference has been checked.
- [ ] UTMs identify concept, format, and hook.

---

## Anti-Patterns

- Treating 20 edits of the same idea as 20 concepts.
- Producing every grid combination before scoring.
- Giving experimental concepts winner-level budget.
- Letting a winner die because there is no adjacent backlog.
- Killing ads by clock time before the data floor is met.
- Scaling an ad with cheap leads but poor lead quality.
- Repeating a loser because the lesson was never written to a ledger.
- Testing new concepts against a landing page that does not match the promise.
