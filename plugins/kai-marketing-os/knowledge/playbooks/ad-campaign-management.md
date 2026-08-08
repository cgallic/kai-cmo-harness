# Ad Campaign Management — Operations Playbook

> **Use when:** Setting up, managing, optimizing, or scaling ad campaigns across any platform. Covers campaign structure, audience strategy, optimization cadence, and scaling frameworks.

---

## Campaign Architecture

### The STAG Structure (Single Theme Ad Groups)

Every campaign follows this hierarchy:
```
CAMPAIGN (budget, objective, schedule)
  └── AD SET / AD GROUP (audience, placement, bid)
       └── ADS (creative, copy, CTA)
```

**Rules:**
1. One theme per ad set. "AI receptionist for law firms" and "AI receptionist for dentists" = two ad sets, not one.
2. 3-5 ad variations per ad set minimum. Let the algorithm find the winner.
3. Never mix cold and warm audiences in the same ad set. Different intent = different messaging.

### Campaign Naming Convention
```
{PLATFORM}_{OBJECTIVE}_{AUDIENCE}_{DATE}

Examples:
  META_CONV_COLD-LAWYERS_20260324
  GOOGLE_SEARCH_BRAND_20260324
  TIKTOK_REACH_LOOKALIKE-1PCT_20260324
```

This makes reporting, filtering, and troubleshooting instant across platforms.

---

## Audience Strategy

### The Funnel Framework

```
┌─────────────────────────────────┐
│          COLD (Top)              │  Don't know you exist
│   Broad interests, lookalikes   │  Objective: Awareness/Reach
│   Estimated: 500K-10M           │  Budget: 60-70% of spend
├─────────────────────────────────┤
│         WARM (Middle)            │  Know you, haven't bought
│   Site visitors, engagers       │  Objective: Consideration
│   Video viewers, email list     │  Budget: 20-30% of spend
├─────────────────────────────────┤
│          HOT (Bottom)            │  Ready to buy
│   Cart abandoners, past buyers  │  Objective: Conversion
│   Free trial users              │  Budget: 10-15% of spend
└─────────────────────────────────┘
```

### Audience Sizing Rules
- **Too small** (< 50K): Algorithm can't optimize. Combine audiences.
- **Sweet spot** (100K-2M): Enough data, specific enough to target well.
- **Too broad** (> 10M): Fine for cold/awareness, bad for conversion campaigns.

### Lookalike / Similar Audience Best Practices
- Source audience: minimum 1,000 users (ideally 5K+)
- Best source: purchasers or high-LTV customers (not just site visitors)
- Start with 1% lookalike (closest match), test up to 3-5%
- Refresh the source audience monthly (stale seeds = stale lookalikes)

### Exclusion Strategy (Critical)
Always exclude:
- Existing customers from cold campaigns (waste of budget)
- Recent purchasers from retargeting (annoying, not helpful)
- Converted users from conversion campaigns (they already converted)
- Employees/team from all campaigns

---

## Optimization Cadence

### Daily (5 minutes)
- Check for disapproved ads (fix or appeal immediately)
- Check budget pacing (are campaigns spending? over/under?)
- Kill any ad with 2x CPA target and 0 conversions after 1000 impressions

### Weekly (30 minutes)
- Review performance by ad set: CPA, ROAS, CTR, frequency
- Pause underperformers (CPA > 1.5x target for 7+ days)
- Refresh creative for ad sets with frequency > 2.5
- Adjust budgets: +20% to winners, -20% to losers (never more than 20%/day)
- Check search terms report (Google) — add negative keywords

### Biweekly (1 hour)
- Creative refresh: new hooks, new angles, new formats
- Audience analysis: which segments convert best?
- Landing page review: bounce rate, conversion rate by source
- Competitor check: are their ads changing?

### Monthly (2 hours)
- Full performance report: ROAS, CAC, LTV/CAC ratio
- Budget reallocation across platforms (shift to best performers)
- New audience testing (10-20% of budget)
- Creative strategy refresh (new angles, not just new ads)

---

## Scaling Framework

### The 4 Stages of Scaling

```
STAGE 1: VALIDATION ($20-50/day)
  Goal: Prove the offer converts
  Duration: 1-2 weeks
  Success: CPA < target, 10+ conversions
  Key metric: Cost per acquisition

STAGE 2: LEARNING ($50-200/day)
  Goal: Find winning audiences and creatives
  Duration: 2-4 weeks
  Success: 3+ profitable ad sets, creative winners identified
  Key metric: ROAS or CPA consistency

STAGE 3: SCALING ($200-1000/day)
  Goal: Increase volume while maintaining efficiency
  Duration: Ongoing
  Rules: Never increase budget >20% per day
  Key metric: Marginal CPA (cost of each additional conversion)

STAGE 4: DIVERSIFICATION ($1000+/day)
  Goal: Multi-platform, multi-format expansion
  Duration: Ongoing
  Strategy: Take winning creative/audiences to new platforms
  Key metric: Blended CAC across all channels
```

### The 20% Rule
Never increase daily budget by more than 20% at once. Larger increases reset the algorithm's learning phase and spike CPA. If you need to double budget, take 4-5 days of 20% increases.

### Horizontal vs Vertical Scaling

**Vertical scaling** = more budget on existing winners
- Pros: Simple, proven performance
- Cons: Diminishing returns, audience saturation
- Limit: Usually tops out at 3-5x the validation budget

**Horizontal scaling** = new audiences, new creatives, new platforms
- Pros: Avoids saturation, discovers new pockets of demand
- Cons: More management overhead, testing costs
- Strategy: Take winning creative → test on new audience/platform

---

## Platform-Specific Campaign Setup

### Meta Ads — Campaign Setup Checklist
- [ ] Campaign objective matches actual goal (don't use Traffic when you want Conversions)
- [ ] Conversion event set up and firing (test with Pixel Helper)
- [ ] Advantage+ Campaign Budget (CBO) enabled for multi-ad-set campaigns
- [ ] Ad set audience defined (cold/warm/hot)
- [ ] Placement: Advantage+ Placements (let algorithm decide) unless testing specific placements
- [ ] Creative: 3-5 variations per ad set
- [ ] Landing page matches ad promise
- [ ] UTM parameters set
- [ ] Frequency cap: not available in standard campaigns — monitor manually

### Google Ads — Campaign Setup Checklist
- [ ] Campaign type selected (Search, PMax, Display, Video)
- [ ] Conversion tracking verified (tag fires on thank-you page)
- [ ] Keyword match types intentional (broad vs phrase vs exact)
- [ ] Negative keywords added (competitors, irrelevant terms, jobs)
- [ ] Ad extensions: sitelinks, callouts, structured snippets, call
- [ ] Geographic targeting set (not "presence or interest" — use "presence" only)
- [ ] Device bid adjustments if needed
- [ ] Search partners: off for most campaigns (lower quality traffic)

### TikTok Ads — Campaign Setup Checklist
- [ ] TikTok Pixel installed and events configured
- [ ] Campaign objective: usually Website Conversions
- [ ] Ad group targeting: broad or lookalike (TikTok's algorithm is strong)
- [ ] Creative: native TikTok style, not repurposed Meta creative
- [ ] Spark Ads: consider boosting existing organic posts first
- [ ] AI content disclosure added (TikTok TOS requirement)
- [ ] Sound/music licensing checked for commercial use

---

## Reporting Template

### Weekly Report Format
```
WEEKLY AD REPORT — {dates}
═══════════════════════════

SUMMARY:
  Total spend:      ${amount}
  Total conversions: {N}
  Blended CPA:      ${amount}
  Blended ROAS:     {X}x

  vs. last week:    CPA {up/down} {%}, ROAS {up/down} {%}

BY PLATFORM:
  ┌──────────┬─────────┬───────┬─────────┬────────┐
  │ Platform │  Spend  │ Conv  │   CPA   │  ROAS  │
  ├──────────┼─────────┼───────┼─────────┼────────┤
  │ Meta     │ $X,XXX  │  XX   │  $XX    │  X.Xx  │
  │ Google   │ $X,XXX  │  XX   │  $XX    │  X.Xx  │
  │ TikTok   │ $X,XXX  │  XX   │  $XX    │  X.Xx  │
  └──────────┴─────────┴───────┴─────────┴────────┘

TOP PERFORMERS:
  1. {ad name} — CPA: ${X}, ROAS: {X}x
  2. {ad name} — CPA: ${X}, ROAS: {X}x
  3. {ad name} — CPA: ${X}, ROAS: {X}x

ACTIONS TAKEN:
  - Paused: {ad sets paused and why}
  - Scaled: {ad sets scaled and by how much}
  - New: {new tests launched}

NEXT WEEK:
  - {planned tests}
  - {budget changes}
  - {creative refreshes}
```

---

## Key Metrics Reference

| Metric | Formula | Good | Excellent | Red Flag |
|--------|---------|------|-----------|----------|
| CTR (Meta) | Clicks / Impressions | 1-2% | 3%+ | < 0.5% |
| CTR (Google Search) | Clicks / Impressions | 3-5% | 8%+ | < 1% |
| CTR (TikTok) | Clicks / Impressions | 0.5-1.5% | 2%+ | < 0.3% |
| CPC (Meta) | Spend / Clicks | $0.50-2 | < $0.50 | > $3 |
| CPC (Google) | Spend / Clicks | $1-5 | < $1 | > $10 |
| Conversion Rate | Conversions / Clicks | 2-5% | 8%+ | < 1% |
| Frequency (Meta) | Impressions / Reach | 1-2 | 1-1.5 | > 3 |
| ROAS | Revenue / Spend | 3x | 5x+ | < 1.5x |
| Quality Score (Google) | Google's rating | 7+ | 9-10 | < 5 |
