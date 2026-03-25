# SaaS Metrics Deep Dive

> **Use when:** Building dashboards, reporting to investors, understanding unit economics, or diagnosing growth problems in a SaaS business.

---

## The 5 Metrics That Matter Most

If you track nothing else, track these:

| Metric | Formula | Why It Matters |
|--------|---------|---------------|
| **MRR** | Sum of all monthly subscription revenue | The pulse of the business |
| **Churn Rate** | Lost customers / total customers (monthly) | The leak in the bucket |
| **CAC** | Total sales+marketing spend / new customers | Cost of growth |
| **LTV** | ARPU × (1 / monthly churn rate) | Value of a customer |
| **LTV:CAC** | LTV / CAC | Unit economics — are you making money? |

---

## Revenue Metrics

### MRR Waterfall

```
START OF MONTH MRR: $100,000
  + New MRR:            $15,000  (new customers)
  + Expansion MRR:       $8,000  (upgrades, add-ons)
  + Reactivation MRR:    $2,000  (returning customers)
  - Contraction MRR:    -$3,000  (downgrades)
  - Churned MRR:        -$7,000  (cancelled)
  ────────────────────────────
END OF MONTH MRR:      $115,000
  Net New MRR:          +$15,000
```

### Key Revenue Metrics

| Metric | Formula | Good | Excellent |
|--------|---------|------|-----------|
| **MRR Growth Rate** | Net new MRR / start MRR | 10-15%/mo (early) | 20%+/mo (early) |
| **ARR** | MRR × 12 | — | — |
| **ARPU** | MRR / total customers | Growing | Accelerating |
| **Net Revenue Retention (NRR)** | (Start MRR + expansion - contraction - churn) / Start MRR | 100-110% | 120%+ |
| **Gross Revenue Retention (GRR)** | (Start MRR - contraction - churn) / Start MRR | 85-90% | 95%+ |
| **Expansion Revenue %** | Expansion MRR / total new MRR | 20-30% | 40%+ |

### NRR — The Magic Number

Net Revenue Retention > 100% means you grow even if you acquire zero new customers. Your existing customers expand faster than they churn.

```
NRR = 80%  → Leaky bucket. Each cohort shrinks 20%/year. Unsustainable.
NRR = 100% → Treading water. No shrinkage, no expansion.
NRR = 120% → Compounding. Each cohort worth 20% more each year.
NRR = 140% → Elite (Slack, Datadog, Snowflake territory).
```

---

## Customer Metrics

### Churn

| Metric | Formula | Good | Concerning |
|--------|---------|------|-----------|
| **Logo churn (monthly)** | Customers lost / start customers | < 3% | > 5% |
| **Logo churn (annual)** | 1 - (1 - monthly churn)^12 | < 30% | > 50% |
| **Revenue churn (monthly)** | MRR lost / start MRR | < 2% | > 4% |
| **Net churn** | (Churned MRR - Expansion MRR) / Start MRR | Negative | Positive |

**Churn benchmarks by segment:**
| Segment | Monthly Churn | Annual Churn |
|---------|-------------|-------------|
| Enterprise ($10K+/mo) | 0.5-1% | 6-12% |
| Mid-market ($1K-10K/mo) | 1-2% | 12-22% |
| SMB ($100-1K/mo) | 3-5% | 30-46% |
| Consumer / prosumer (<$100/mo) | 5-8% | 46-63% |

### Cohort Analysis

Track each monthly cohort's revenue over time:

```
         Month 0  Month 1  Month 2  Month 3  Month 6  Month 12
Jan '26: $10,000  $9,500   $9,200   $9,000   $8,500   $7,800
Feb '26: $12,000  $11,400  $11,000  $10,800  ─        ─
Mar '26: $15,000  $14,500  $14,200  ─        ─        ─

Retention curve:
  Month 1: 95% → 95% → 97%  (improving! ✓)
  Month 3: 90% → 90% → ─
  Month 12: 78% → ─
```

**What to look for:**
- Are newer cohorts retaining better than older ones? (Product-market fit improving)
- Is there a cliff at a specific month? (Indicates an activation/value problem at that point)
- Do cohorts stabilize or keep declining? (Stabilization = found core value segment)

---

## Acquisition Metrics

### CAC Calculation

```
SIMPLE CAC:
  Total sales + marketing spend (month) / New customers (month)
  $50,000 / 100 = $500 CAC

FULLY-LOADED CAC:
  (Sales salaries + marketing salaries + ad spend + tools + overhead)
  / New customers acquired
  ($100,000) / 100 = $1,000 fully-loaded CAC
```

### CAC by Channel

| Channel | Typical SaaS CAC | Notes |
|---------|-----------------|-------|
| Organic SEO | $50-200 | Low CAC, slow to build |
| Content marketing | $100-300 | Compounds over time |
| Paid search (Google) | $200-800 | High intent, expensive |
| Paid social (Meta) | $150-500 | Broad reach, variable intent |
| LinkedIn Ads | $300-1000 | Expensive but targeted B2B |
| Outbound sales (SDR) | $500-2000 | Expensive but controllable |
| Referral/word-of-mouth | $50-150 | Best CAC, hard to scale |
| Partnerships | $100-400 | Leverages others' audiences |

### LTV:CAC Ratio

```
LTV:CAC < 1:1  → Losing money on every customer. Fix retention or reduce CAC.
LTV:CAC = 1-2:1 → Barely sustainable. Need improvement.
LTV:CAC = 3:1   → Healthy. Standard target for funded SaaS.
LTV:CAC = 5:1   → Very efficient. Could invest more in growth.
LTV:CAC > 5:1   → Underinvesting in acquisition. Spend more!
```

### CAC Payback Period

```
CAC Payback = CAC / (ARPU × Gross Margin)

Example: $600 CAC / ($100/mo × 80% margin) = 7.5 months

Target: < 12 months (funded SaaS), < 6 months (bootstrapped)
```

---

## Engagement Metrics

| Metric | Formula | What It Predicts |
|--------|---------|-----------------|
| **DAU/MAU** | Daily active / Monthly active | Stickiness. >25% is strong. |
| **Time to value** | Signup to first "aha" moment | Activation rate |
| **Activation rate** | Users who complete key action / signups | Future retention |
| **Feature adoption** | Users of feature X / total users | Product-market fit for that feature |
| **Session frequency** | Avg sessions per user per week | Habit formation |
| **Support ticket rate** | Tickets / active users | Product quality / UX issues |

### The Activation Metric

The single most important leading indicator of retention. Define it as:

```
ACTIVATION = User completes [key action] within [timeframe]

Examples:
  Slack:    "Send 2,000 messages" (team-level)
  Dropbox:  "Upload first file"
  KaiCalls: "First call answered by AI"
  Figma:    "Invite a collaborator"
```

Measure what % of signups activate. Improve this number and everything downstream improves.

---

## The SaaS Dashboard

### Board-Level Dashboard (Monthly)

```
SaaS METRICS — {Month} {Year}
═══════════════════════════════

REVENUE:
  MRR:           ${X}K     ({+/-}% MoM)
  ARR:           ${X}K     ({+/-}% YoY)
  Net New MRR:   ${X}K     (New: ${X}K + Expansion: ${X}K - Churn: ${X}K)
  NRR:           {X}%

CUSTOMERS:
  Total:         {N}       ({+/-} net new)
  New:           {N}       (from {channels})
  Churned:       {N}       ({X}% logo churn)

UNIT ECONOMICS:
  ARPU:          ${X}/mo   ({+/-}%)
  CAC:           ${X}      ({+/-}%)
  LTV:           ${X}
  LTV:CAC:       {X}:1
  Payback:       {X} months

EFFICIENCY:
  Burn multiple: {X}       (net burn / net new ARR)
  Magic number:  {X}       (net new ARR / prior quarter S&M)
  Rule of 40:    {X}%      (growth rate + profit margin)
```

### The Rule of 40

```
Growth Rate % + Profit Margin % ≥ 40%

Examples:
  50% growth + -10% margin = 40% ✓ (high growth, acceptable losses)
  20% growth + 20% margin  = 40% ✓ (moderate growth, profitable)
  10% growth + 5% margin   = 15% ✗ (neither growing fast nor profitable)
```

### The Magic Number

```
Magic Number = Net New ARR (this quarter) / Sales & Marketing Spend (last quarter)

> 1.0  → Very efficient. Spend more.
0.5-1.0 → Healthy. Sustainable growth.
< 0.5  → Inefficient. Fix unit economics before spending more.
```

---

## Diagnostic Framework

### "Growth is slowing" — Where to look

```
Is the problem ACQUISITION?
  ├── CAC rising? → Channel saturation, test new channels
  ├── Conversion dropping? → Message-market fit, landing page, competitive
  └── Pipeline shrinking? → Top-of-funnel problem, increase reach

Is the problem ACTIVATION?
  ├── Signup-to-active dropping? → Onboarding broken, time-to-value too long
  └── Trial-to-paid dropping? → Value not demonstrated, pricing issue

Is the problem RETENTION?
  ├── Month-1 churn high? → Activation problem (they never got value)
  ├── Month-3+ churn high? → Product problem (they got value then lost it)
  └── Enterprise churning? → Account management, competitor displacement

Is the problem EXPANSION?
  ├── No upsell revenue? → No expansion path in pricing, or value not growing
  └── Contraction increasing? → Customers pulling back, economy or product fit
```

---

## Benchmarks by Stage

| Metric | Seed ($0-1M ARR) | Series A ($1-5M) | Series B ($5-20M) | Scale ($20M+) |
|--------|------------------|-------------------|--------------------|--------------|
| MRR growth | 15-25%/mo | 8-15%/mo | 5-10%/mo | 3-5%/mo |
| Logo churn | 5-8%/mo | 3-5%/mo | 2-3%/mo | 1-2%/mo |
| NRR | 90-100% | 100-110% | 110-130% | 120-140% |
| LTV:CAC | 2-3:1 | 3-4:1 | 3-5:1 | 4-6:1 |
| CAC payback | 12-18 mo | 8-12 mo | 6-10 mo | 4-8 mo |
| Gross margin | 60-70% | 70-80% | 75-85% | 80-90% |
