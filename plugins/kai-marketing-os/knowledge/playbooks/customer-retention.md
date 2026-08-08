# Customer Retention & Churn Reduction Playbook

> **Use when:** Reducing churn, improving retention, building loyalty programs, or diagnosing why customers leave. Cutting churn by 5% can boost profits by up to 95%.

Sources: [Baremetrics Churn Reduction](https://baremetrics.com/blog/proven-ways-reduce-saas-churn-rate), [SaaSCity Churn Playbook](https://saascity.io/blog/saas-churn-playbook-2026-15-tactics-guide), [Paragon Reducing Churn](https://www.useparagon.com/blog/reducing-churn-the-8-step-b2b-saas-playbook)

---

## Churn Benchmarks

| Segment | Monthly Logo Churn | Annual Logo Churn | Target |
|---------|-------------------|-------------------|--------|
| Enterprise ($10K+/mo) | 0.5-1% | 6-12% | < 5% annual |
| Mid-market ($1K-10K/mo) | 1-2% | 12-22% | < 15% annual |
| SMB ($100-1K/mo) | 3-5% | 30-46% | < 35% annual |
| Consumer (<$100/mo) | 5-8% | 46-63% | < 50% annual |

**Two types of churn to track separately:**
- **Voluntary churn** (60-80%): Customer actively cancels. Fixable with value delivery.
- **Involuntary churn** (20-40%): Failed payment, expired card. Fixable with dunning.

---

## The 8-Layer Retention Stack

```
LAYER 8: ADVOCACY          Turn retained customers into referrers
LAYER 7: EXPANSION         Grow revenue from existing customers
LAYER 6: HEALTH SCORING    Predict churn before it happens
LAYER 5: ENGAGEMENT        Keep customers actively using the product
LAYER 4: SUCCESS           Ensure customers achieve their goals
LAYER 3: SUPPORT           Resolve issues fast and well
LAYER 2: ONBOARDING        Get to value in minutes, not weeks
LAYER 1: PAYMENT RECOVERY  Stop involuntary churn (failed cards)
```

---

## Layer 1: Payment Recovery (Quick Win — 20-40% of churn)

Involuntary churn = failed payments. Fix this first. It's the easiest churn to recover.

**Dunning sequence:**
```
Day 0:  Payment fails → automated retry + email: "Payment failed, updating your card takes 30 seconds"
Day 3:  Second retry + email: "Your account is at risk — update payment to avoid disruption"
Day 7:  Third retry + email: "Last chance — service will pause tomorrow"
Day 10: Pause account (not delete) + email: "We've paused your account. Re-activate anytime."
Day 30: Final email: "We miss you. Your data is safe. Come back anytime."
```

**Tools:** Baremetrics Recover, Churnkey, ProfitWell Retain, Stripe Smart Retries

**Impact:** Recovers 20-40% of involuntary churn. This alone can reduce total churn by 10-15%.

---

## Layer 2: Onboarding (The Make-or-Break)

86% of customers stick around when onboarding is clear. Onboarding excellence boosts retention by up to 50%.

**The activation checklist:**

Define your "aha moment" — the single action that predicts long-term retention:
| Product Type | Activation Event | Target |
|-------------|-----------------|--------|
| SaaS tool | First successful use of core feature | Within 24 hours |
| Collaboration | Invite a teammate | Within 48 hours |
| Analytics | Connect data source + see first report | Within 1 hour |
| Content | Publish first piece | Within 7 days |
| Communication | Answer first call / send first message | Within 1 hour |

**Onboarding sequence:**
```
Minute 0:   Welcome + single next step (not a feature tour)
Minute 5:   Guide to "aha moment" (interactive walkthrough)
Hour 1:     Check — did they activate? If no → nudge email
Day 1:      "Quick win" email — show what they can do next
Day 3:      Feature highlight they haven't tried
Day 7:      Check-in: "How's it going?" + offer help
Day 14:     Power-user tip + case study from similar customer
```

**Measure:** Activation rate = users who complete aha moment / total signups. Target: 40-60%.

---

## Layer 3: Support Excellence

Every support interaction is a retention moment. Bad support = churn. Great support = loyalty.

| Metric | Good | Excellent | Red Flag |
|--------|------|-----------|----------|
| First response time | < 4 hours | < 1 hour | > 24 hours |
| Resolution time | < 24 hours | < 4 hours | > 72 hours |
| CSAT (satisfaction) | 85%+ | 92%+ | < 75% |
| First-contact resolution | 70%+ | 85%+ | < 50% |

**Rules:**
- Respond within 1 hour during business hours (set expectations for off-hours)
- Resolve on first contact whenever possible
- Follow up after resolution: "Is this fully fixed?"
- Track repeat issues — recurring support tickets = product problem, not support problem

---

## Layer 4: Customer Success

Proactive, not reactive. Don't wait for customers to complain — ensure they succeed.

**Success milestones by stage:**
```
WEEK 1:   Activated (completed aha moment)
MONTH 1:  Habitual use (used product 3+ days/week for 2+ weeks)
MONTH 3:  Value realized (can articulate the ROI or benefit)
MONTH 6:  Embedded (integrated into workflow, team using it)
YEAR 1:   Advocate (willing to refer or provide testimonial)
```

**Quarterly Business Review (for high-value accounts):**
1. Review their usage data and outcomes
2. Show ROI achieved (quantified)
3. Identify opportunities to get more value
4. Share product roadmap relevant to their needs
5. Ask: "What would make this a 10/10 for you?"

---

## Layer 5: Engagement Monitoring

Track engagement to predict churn before it happens.

**Red flag behaviors:**
| Signal | Churn Risk | Action |
|--------|-----------|--------|
| Login frequency dropped 50%+ | High | Outreach: "We noticed you haven't been in recently..." |
| Key feature usage stopped | High | Email: "Did you know you can [feature] to [benefit]?" |
| Support tickets spiking | Medium | Escalate: something's broken for them |
| No login for 14+ days | Very High | Direct outreach (email + call for high-value) |
| Downgraded plan | Medium | Understand why: cost? feature mismatch? |
| Team members removed | Very High | Immediate outreach: are they shrinking or leaving? |

---

## Layer 6: Health Scoring

Combine signals into a single customer health score:

```
HEALTH SCORE = weighted sum of:
  Product usage frequency:     30% weight
  Feature adoption depth:      20% weight
  Support ticket sentiment:    15% weight
  NPS / satisfaction score:    15% weight
  Contract/payment status:     10% weight
  Engagement with content:     10% weight

SCORE RANGES:
  80-100: Healthy (green)    → Upsell opportunity
  60-79:  At risk (yellow)   → Proactive check-in
  40-59:  Unhealthy (orange) → Intervention needed
  0-39:   Critical (red)     → Immediate outreach, save attempt
```

AI-powered churn prediction in 2026 can identify at-risk accounts with 85% accuracy 3 months out. Tools: Gainsight, ChurnZero, Totango, Vitally.

---

## Layer 7: Expansion (Negative Churn)

The goal: grow revenue from existing customers faster than you lose it.

**Expansion levers:**
| Lever | How | When |
|-------|-----|------|
| **Upsell** | Move to higher tier | When they hit plan limits |
| **Cross-sell** | Add complementary product | When they express adjacent need |
| **Seat expansion** | Add more users | When adoption grows within org |
| **Usage growth** | Increase consumption | Natural usage growth |
| **Annual upgrade** | Monthly → annual billing | At renewal or with incentive |

**Rule:** Never upsell a customer who isn't healthy. Fix value delivery first.

**Target:** Net Revenue Retention > 110% (expansion outpaces churn)

---

## Layer 8: Advocacy

Retained, happy customers are your best acquisition channel.

- **Referral program** at the right moment (after value realized, not at signup)
- **Case study** request at success milestones
- **Review request** after positive support interaction or NPS 9-10
- **Community membership** for peer-to-peer value
- See `channels/affiliate-referral.md` for referral program design

---

## The Cancellation Flow

When they do cancel, make it count:

```
USER CLICKS "CANCEL"
  │
  ├── Survey: "Why are you leaving?" (required, 4-5 options + free text)
  │
  ├── Based on reason, offer:
  │   ├── "Too expensive" → Offer downgrade or discount
  │   ├── "Missing feature" → Show roadmap + timeline
  │   ├── "Not using it enough" → Offer free month to re-engage
  │   ├── "Switching to competitor" → Ask which one + why
  │   └── "Other" → Offer call with success team
  │
  ├── If they still cancel:
  │   ├── Confirm cancellation (don't make it hard — builds trust)
  │   ├── Remind them: "Your data is saved for 90 days"
  │   └── Set re-engagement email for 30 days later
  │
  └── Log reason in CRM for churn analysis
```

**Never:** Make cancellation hard to find. It destroys trust and generates negative reviews.

---

## Churn Analysis Framework

### Monthly Churn Review

```
CHURN REPORT — {Month}
═══════════════════════

Total churned: {N} accounts, ${X} MRR

BY REASON:
  Price:           {N} ({X}%)
  Missing feature: {N} ({X}%)
  Competitor:      {N} ({X}%)
  Not using:       {N} ({X}%)
  Involuntary:     {N} ({X}%)
  Other:           {N} ({X}%)

BY SEGMENT:
  Enterprise: {N} ({X}% churn rate)
  Mid-market: {N} ({X}% churn rate)
  SMB:        {N} ({X}% churn rate)

BY TENURE:
  < 3 months: {N}  ← onboarding problem
  3-6 months: {N}  ← value delivery problem
  6-12 months: {N} ← competitive/needs change
  > 12 months: {N} ← market/strategic shift

ACTIONS:
  1. {Top churn reason → specific fix}
  2. {Second reason → specific fix}
  3. {Involuntary → dunning improvement}
```

---

## Retention Metrics Dashboard

| Metric | Formula | Good | Excellent |
|--------|---------|------|-----------|
| Logo retention (monthly) | 1 - (churned / total) | 95%+ | 98%+ |
| Revenue retention (net) | (Start + expansion - churn) / Start | 100%+ | 115%+ |
| NPS | Promoters - Detractors | 40+ | 60+ |
| Customer health score | Weighted engagement composite | 70+ avg | 80+ avg |
| Time to value | Signup → activation | < 1 day | < 1 hour |
| DAU/MAU ratio | Daily / monthly active | 20%+ | 40%+ |
| Support CSAT | Satisfaction after ticket | 85%+ | 92%+ |
| Expansion rate | Expansion MRR / start MRR | 5%+/mo | 10%+/mo |
