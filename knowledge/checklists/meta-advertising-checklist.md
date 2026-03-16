# Meta Advertising Checklist (2026)

Use this checklist before launching, during optimization, and for auditing Meta ad campaigns.

---

## Pre-Launch Checklist

### Tracking Setup

- [ ] Meta Pixel installed and firing correctly
- [ ] Conversions API (CAPI) implemented server-side
- [ ] Event deduplication configured (matching event_id)
- [ ] Standard events mapped (ViewContent, AddToCart, Purchase, Lead)
- [ ] Custom conversions created for specific business goals
- [ ] Attribution window set appropriately (7-day click default)
- [ ] Test events verified in Events Manager

### Account Structure

- [ ] Consolidated campaigns (one per objective, per funnel stage)
- [ ] Sufficient budget for 50+ weekly conversions per ad set
- [ ] No overlapping audiences between ad sets
- [ ] Existing customer exclusions in prospecting campaigns
- [ ] Value Rules configured only if data supports assumptions

### Creative Preparation

- [ ] Minimum 5-10 genuinely diverse creative concepts
- [ ] Multiple format variants (1:1, 4:5, 9:16)
- [ ] Video versions (6-15 seconds for Stories/Reels)
- [ ] Four creative archetypes represented:
  - [ ] Problem-Agitation
  - [ ] Social Proof
  - [ ] Product Demo
  - [ ] Lifestyle/Aspiration
- [ ] All text under character limits (125 primary, 27 headline)
- [ ] No text covering >20% of image (legacy guideline, still impacts quality)

---

## Campaign Launch Checklist

### Advantage+ Sales (ASC+) Campaigns

- [ ] Campaign objective set to Sales
- [ ] Advantage+ campaign type selected
- [ ] Product catalog connected (if applicable)
- [ ] Country-level targeting confirmed
- [ ] Existing customer segment defined for exclusion
- [ ] Maximum 150 total ads across all ad sets
- [ ] Creative diversity verified (not just iterations)

### Standard Campaigns

- [ ] Correct optimization event selected
- [ ] Budget supports learning phase exit ($CPA × 50 ÷ 7 days)
- [ ] Broad targeting unless specific need for restrictions
- [ ] All Advantage+ placements enabled (recommended)
- [ ] Bid strategy matches business goal:
  - [ ] Highest Volume: Max conversions, no cost control
  - [ ] Cost Per Result: Target CPA maintenance
  - [ ] ROAS Goal: Value optimization for e-commerce
  - [ ] Bid Cap: Strict cost ceiling

---

## Learning Phase Management

### Entering Learning Phase

- [ ] Expected timeline: 7 days to exit
- [ ] Monitoring: No edits during learning
- [ ] Budget: Sufficient for 50+ weekly events

### Stuck in Learning Limited

- [ ] Option 1: Increase budget by 20%+ increments
- [ ] Option 2: Broaden audience targeting
- [ ] Option 3: Optimize for higher-funnel event
- [ ] Option 4: Consolidate underperforming ad sets
- [ ] Assessment: Learning Limited ≠ failure; evaluate true performance

### Actions That Reset Learning

Avoid these during learning phase:
- [ ] Budget changes >20%
- [ ] Audience targeting changes
- [ ] Bid strategy changes
- [ ] Creative additions/removals
- [ ] Pausing and restarting

---

## Optimization Checklist (Weekly)

### Performance Review

- [ ] Evaluate at ad set/campaign level (not individual ads)
- [ ] Check blended ROAS across all ad sets
- [ ] Monitor CPM trends (rising = fatigue signal)
- [ ] Review frequency by placement (<3 for prospecting)
- [ ] Check Creative Similarity score in reporting

### Breakdown Effect Awareness

- [ ] Avoid pausing high-spend ads that appear "worse"
- [ ] Understand: Low CPA often = low scale ceiling
- [ ] Trust: Algorithm allocates for best blended result
- [ ] Action: If overall CPA too high, reduce budget incrementally

### Creative Health

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| CPM change | <10% | 10-30% | >30% |
| CTR change | >-10% | -10-20% | <-20% |
| Frequency | <2 | 2-3 | >3 |

### Actions Based on Signals

- [ ] Rising CPMs: Introduce new creative concepts
- [ ] Declining CTR: Test new hooks and angles
- [ ] High Frequency: Expand audience or refresh creative
- [ ] High Creative Similarity: Radically different concepts needed

---

## Creative Refresh Checklist (Every 30-45 Days)

### Creative Audit

- [ ] Identify top 3 performing ads (keep running)
- [ ] Identify fatigued ads (CPM up, CTR down)
- [ ] Analyze winning elements from top performers

### New Creative Development

- [ ] Develop 5-10 new concepts based on winners
- [ ] Ensure genuine variation (not just iterations):
  - [ ] Different visual style
  - [ ] Different emotional angle
  - [ ] Different format (video vs static vs carousel)
  - [ ] Different hook/opening
- [ ] Include at least one "wild card" concept

### Launch Protocol

- [ ] Add new creative to existing ad sets (don't create new ones)
- [ ] Don't remove old creative until new has data
- [ ] Monitor for learning phase impact

---

## Attribution & Measurement Checklist

### Data Integrity

- [ ] Pixel + CAPI both active with deduplication
- [ ] Attribution window matches business reality:
  - [ ] High-consideration purchase: 7-day click
  - [ ] Impulse purchase: 1-day click
  - [ ] View attribution: 1-day only (7/28-day deprecated)
- [ ] Event match quality score >7/10

### Reporting Accuracy

- [ ] Using breakdown reporting appropriately
- [ ] Aware of 13-month limit for unique-count breakdowns
- [ ] Aware of 6-month limit for frequency breakdowns
- [ ] Not relying on deprecated view-through windows

### Incrementality Validation

- [ ] Running conversion lift studies quarterly
- [ ] A/B testing creative and audience variations
- [ ] Cross-referencing with GA4/external analytics
- [ ] Using holdout groups for true incremental measurement

---

## Advantage+ Audit Checklist

### Catalog Health (E-commerce)

- [ ] Product inventory updated (no out-of-stock items promoted)
- [ ] Pricing accurate and current
- [ ] Product images high quality (1080×1080 minimum)
- [ ] Descriptions clear and detailed
- [ ] Categories correctly mapped

### ASC+ Settings

- [ ] Not relying on demographic targeting (AI handles this)
- [ ] Budget sufficient for scale
- [ ] Existing customer budget allocation reviewed
- [ ] Multiple ad sets only if testing specific hypotheses

---

## Red Flags Requiring Immediate Action

### Stop and Investigate If:

- [ ] CPA suddenly doubles with no changes made
- [ ] Account disabled or ads rejected
- [ ] Conversion tracking shows 0 events
- [ ] Creative receiving negative feedback flags
- [ ] Policy violations in ad review

### Optimization Blockers:

- [ ] Spending <$10/day (insufficient signal)
- [ ] <10 weekly conversions (can't learn)
- [ ] 100% frequency reach (audience exhausted)
- [ ] All creative marked similar (Andromeda penalty)

---

## Quarterly Review Checklist

### Account Health

- [ ] Review overall account structure vs Performance 5
- [ ] Audit tracking setup for accuracy
- [ ] Check for audience overlap between campaigns
- [ ] Review Value Rules performance (if used)
- [ ] Assess incrementality via lift studies

### Strategy Alignment

- [ ] Funnel budget allocation appropriate (70/20/10)
- [ ] Creative strategy supporting Andromeda needs
- [ ] Testing velocity sufficient (new concepts monthly)
- [ ] Measurement stack providing accurate data

### Performance Benchmarks

| Metric | Your Result | Industry Benchmark |
|--------|-------------|-------------------|
| ROAS | | 3-5x (e-commerce) |
| CPA | | Varies by industry |
| CTR | | 0.9-1.5% (Feed) |
| Frequency | | <3 (prospecting) |

---

## Emergency Troubleshooting

### Performance Drop Playbook

1. **Check tracking first** - Is Pixel/CAPI still working?
2. **Review recent changes** - Did something reset learning?
3. **Check auction insights** - Is competition up?
4. **Audit creative fatigue** - CPM/CTR trends?
5. **Verify audiences** - Overlap or saturation?

### When to Kill vs. Optimize

| Situation | Action |
|-----------|--------|
| CPA 2x target, learning active | Wait 7 days |
| CPA 2x target, learning complete | Reduce budget 20% |
| CPA 3x+ target | Pause, audit creative |
| Zero conversions after 7 days | Audit tracking, kill if tracking works |
