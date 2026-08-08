# Pricing Strategy Playbook

> **Use when:** Setting prices, designing packaging/tiers, running pricing experiments, or repositioning against competitors.

---

## Pricing Psychology — The 9 Principles

### 1. Anchor High, Offer Lower
Show the expensive option first. Everything after feels reasonable.
```
ENTERPRISE: $499/mo    ← anchor
PRO:        $99/mo     ← feels like a steal
STARTER:    $29/mo     ← feels like nothing
```

### 2. Charm Pricing ($X9)
$99 feels categorically different from $100. $29 vs $30. The left digit changes the mental category. Use for consumer products and lower-tier SaaS. Skip for enterprise (signals discount).

### 3. The Decoy Effect
Add a "bad deal" tier that makes the target tier look better.
```
BASIC:  10 users,  5GB,  $29/mo       ← value play
PRO:    25 users, 20GB,  $79/mo       ← target tier (best value per user)
TEAM:   15 users, 10GB,  $69/mo       ← decoy (worse than Pro in every way)
```
Nobody picks Team. But its existence pushes people from Basic to Pro.

### 4. Price on Value, Not Cost
Your cost to serve is irrelevant to the customer. Price based on the outcome they get.
```
COST-BASED:  "It costs us $5/call to process, so we charge $8/call"
VALUE-BASED: "Each answered call is worth $200 in potential revenue. We charge $99/mo for unlimited calls."
```

### 5. Show Savings in Dollars, Not Percentages (for big numbers)
"Save $1,200/year" > "Save 20%/year" when the dollar amount is impressive.
"Save 50%" > "Save $5" when the dollar amount is small.

### 6. Bundle to Obscure Comparison
When competitors can match your price on individual features, bundle them so the comparison is impossible.

### 7. Remove the Dollar Sign
Studies show removing the "$" from menus increases spending. In SaaS, this translates to: emphasize the value number, not the price number.
```
WEAK:  "$99/month"
STRONG: "99/mo — pays for itself in 3 missed calls"
```

### 8. Annual = Default
Show annual pricing by default. Show monthly as the alternative. Annual pricing:
- Reduces churn (commitment)
- Improves cash flow (upfront payment)
- Anchors to a lower monthly rate
```
"$79/mo billed annually ($948/year)"  ← save $240/year
"$99/mo billed monthly"               ← costs more
```

### 9. Free Tier as Acquisition
Free removes the biggest purchase barrier: risk. But free users must eventually convert or they're just cost.
```
FREE:     Limited features, drives adoption
PAID:     Unlocks the feature that makes free insufficient
UPGRADE:  Trigger = user hits the free ceiling naturally
```

---

## Packaging — The 3-Tier Model

### The Formula

| | Starter | Pro (Target) | Enterprise |
|---|---------|-------------|-----------|
| **Who** | Individuals, tryouts | Growing teams, core market | Large orgs, custom needs |
| **Price** | $0-29/mo | $49-199/mo | $500+/mo or custom |
| **Features** | Core product, limited | Full product, most features | Everything + custom |
| **Support** | Self-serve | Email + chat | Dedicated CSM |
| **Purpose** | Acquisition | Revenue | High LTV |
| **% of users** | 60-70% | 25-35% | 2-5% |
| **% of revenue** | 5-10% | 40-60% | 30-50% |

### Feature Gating Strategy

| Gate Type | How | Example | Best For |
|-----------|-----|---------|----------|
| **Usage limits** | Free up to X, then pay | 100 emails/mo free | Volume-based products |
| **Feature gates** | Core free, premium features paid | Analytics free, A/B testing paid | Feature-rich products |
| **Seat limits** | Free for 1 user, pay for team | Solo free, 5+ seats paid | Collaboration tools |
| **Support level** | Community free, priority paid | Docs free, live chat paid | Complex products |
| **Integrations** | Basic free, advanced paid | CSV export free, API paid | Platform products |

### The Value Metric

The single unit you charge on. Choosing the right one is the most important pricing decision.

| Value Metric | Example | Pro | Con |
|-------------|---------|-----|-----|
| Per seat/user | Slack, Figma | Predictable, scales with adoption | Discourages adding users |
| Per usage | Twilio (per API call) | Aligns cost with value | Unpredictable bills |
| Per feature tier | HubSpot | Simple to understand | Arbitrary boundaries |
| Per outcome | Performance marketing (per lead) | Direct value alignment | Hard to measure/control |
| Flat rate | Basecamp | Simple, no surprises | Doesn't scale with value |

**Best practice:** Charge on the metric most correlated with customer success. If more seats = more value, charge per seat. If more usage = more value, charge per usage.

---

## Pricing Page Best Practices

### Layout
- [ ] 3 tiers displayed (Good/Better/Best)
- [ ] Target tier visually highlighted ("Most Popular" badge, larger card, different color)
- [ ] Annual pricing shown by default with monthly toggle
- [ ] Dollar savings for annual shown explicitly ("Save $240/year")
- [ ] Feature comparison table below tier cards
- [ ] FAQ section addressing pricing objections
- [ ] "Talk to sales" option for enterprise (don't hide pricing behind sales)

### Copy
- [ ] Tier names reflect the customer, not the product ("Starter" not "Basic v1.2")
- [ ] Feature descriptions are benefits, not specs ("Answer unlimited calls" not "Unlimited SIP channels")
- [ ] CTA buttons differ per tier ("Start Free" / "Start Pro Trial" / "Contact Sales")
- [ ] Social proof near pricing ("Trusted by 500+ law firms")
- [ ] Risk reversal near CTA ("30-day money-back guarantee")

### Anti-Patterns to Avoid
- Too many tiers (>4 causes analysis paralysis)
- Hidden fees revealed at checkout
- Forcing sales calls for pricing info (for products under $500/mo)
- Comparing yourself to competitors on the pricing page (looks defensive)
- Per-seat pricing shown as "per user per month" buried in footnotes

---

## Pricing Experiments

### What to Test (Priority Order)

1. **Price level** — are you underpriced? (Most SaaS startups are)
2. **Tier structure** — 2 vs 3 vs 4 tiers
3. **Value metric** — per seat vs per usage vs flat
4. **Annual discount** — 10% vs 20% vs 2 months free
5. **Free tier limits** — where the ceiling sits
6. **Feature packaging** — which features gate which tier

### How to Test

| Method | Speed | Confidence | Risk |
|--------|-------|-----------|------|
| **Customer interviews** | 1 week | Medium | None |
| **Van Westendorp survey** | 1 week | Medium | None |
| **A/B test pricing page** | 2-4 weeks | High | Low (test on new visitors only) |
| **Grandfather existing, new price for new** | Immediate | High | Medium |
| **Raise prices and measure churn** | 1-3 months | Very high | Medium |

### Van Westendorp Questions
Ask customers (or prospects):
1. At what price is this so cheap you'd question quality?
2. At what price is this a bargain — great deal?
3. At what price is it starting to get expensive — but you'd still consider it?
4. At what price is it too expensive — you'd never buy it?

Plot the curves. The intersection of "too cheap" and "too expensive" = optimal price range.

---

## Competitive Pricing

### When to Price Higher
- You have a clear differentiation (10x on one dimension)
- Your target market values quality over cost
- You serve enterprise or professional segments
- Your brand has established trust/authority
- Switching costs are high (integrations, data lock-in)

### When to Price Lower
- You're entering a market with established players
- Your product is simpler/narrower (fewer features, focused use case)
- You serve SMB or individuals
- You need volume to reach network effects
- You can sustain lower margins through efficiency

### Price Positioning Map

```
                    HIGH PRICE
                        │
          Premium ──────┼────── Enterprise
          (fewer features,      (all features,
           premium experience)  white-glove service)
                        │
LOW VALUE ──────────────┼────────────────── HIGH VALUE
                        │
          Discount ─────┼────── Value Leader
          (avoid this   │      (most features,
           quadrant)    │       best price)
                        │
                    LOW PRICE
```

You want to be in the top-right (Enterprise) or bottom-right (Value Leader). Never bottom-left (Discount — no differentiation + low price = race to zero).

---

## Key Metrics

| Metric | Formula | Healthy | Concerning |
|--------|---------|---------|-----------|
| ARPU (Avg Revenue Per User) | MRR / Total customers | Growing MoM | Flat or declining |
| LTV (Lifetime Value) | ARPU × avg lifetime (months) | > 3× CAC | < 3× CAC |
| LTV:CAC Ratio | LTV / CAC | 3:1 to 5:1 | < 3:1 (inefficient) or > 5:1 (underinvesting) |
| Expansion revenue % | Upsell revenue / Total revenue | 20-40% | < 10% |
| Price sensitivity | % who cite price as churn reason | < 15% | > 30% |
| Net Revenue Retention | (Start MRR + expansion - churn) / Start MRR | > 100% | < 90% |
