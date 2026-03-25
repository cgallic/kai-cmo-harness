# Competitive Intelligence Playbook

> **Use when:** Researching competitors, building battlecards for sales, monitoring competitive moves, or positioning against alternatives. For ad-specific competitive research, see `/ad-research` skill.

---

## CI Framework — The 5 Intelligence Layers

```
LAYER 5: STRATEGY        What are they betting on long-term?
LAYER 4: POSITIONING     How do they describe themselves vs us?
LAYER 3: PRODUCT         What do they build, ship, and price?
LAYER 2: MARKETING       What channels, messages, and tactics do they use?
LAYER 1: SIGNALS         What observable actions indicate future moves?
```

---

## Layer 1: Signal Monitoring (Ongoing)

### What to Track

| Signal | Source | What It Means |
|--------|--------|--------------|
| **Job postings** | LinkedIn, careers page | Hiring AI engineers = building AI features. Hiring enterprise sales = moving upmarket. |
| **Pricing changes** | Website checks | Price increase = confidence. Price decrease = desperation or repositioning. |
| **Feature launches** | Product Hunt, changelog, blog | Where they're investing development effort. |
| **Funding rounds** | Crunchbase, TechCrunch | More money = more marketing spend coming. |
| **Executive hires** | LinkedIn | New CMO = marketing strategy shift. New CRO = going enterprise. |
| **Patent filings** | Google Patents | What technology they're building that isn't shipped yet. |
| **Content themes** | Blog, social media | Shifting messaging = shifting positioning. |
| **Ad spend changes** | Meta Ad Library, Google Transparency | Increased spend = they found something that works. |
| **Review sentiment** | G2, Capterra, TrustRadius | Repeated complaints = their weakness, your opportunity. |
| **Partnership announcements** | Press releases, blog | New integrations = new target segments. |

### Monitoring Tools

| Tool | What It Tracks | Cost |
|------|---------------|------|
| **Visualping** | Website changes (pricing, features, messaging) | Free tier |
| **Google Alerts** | Mentions across the web | Free |
| **Crunchbase** | Funding, acquisitions, leadership changes | Free tier |
| **SpyFu** | SEO keywords, PPC keywords, ad copy | $39+/mo |
| **SimilarWeb** | Traffic estimates, traffic sources | Free tier |
| **BuiltWith** | Tech stack detection | Free tier |
| **Meta Ad Library** | All active ads for any page | Free |
| **G2 / Capterra alerts** | New reviews mentioning competitors | Free |

### Weekly CI Routine (15 min)

1. Check competitor websites for pricing/feature changes (Visualping alerts)
2. Scan Google Alerts for mentions
3. Check Meta Ad Library for new ad creatives
4. Skim top competitor's blog for new content themes
5. Check LinkedIn for hiring signals

---

## Layer 2: Marketing Intelligence

### Content & SEO Analysis

| Dimension | How to Analyze | Tools |
|-----------|---------------|-------|
| **Organic keywords** | What do they rank for that you don't? | Ahrefs, SEMrush |
| **Content gaps** | Topics they cover that you don't | Ahrefs Content Gap |
| **Backlink profile** | Who links to them? Can you get those links too? | Ahrefs, Moz |
| **Content frequency** | How often do they publish? | Manual check or Ahrefs |
| **Top performing pages** | Which pages get the most traffic? | SimilarWeb, Ahrefs |

### Paid Ads Analysis

See `/ad-research` skill for detailed ad library research. Key questions:
- What platforms are they running on?
- How many active ads? (more = bigger budget)
- What hooks/offers are they testing?
- How long have their longest-running ads been active? (long = profitable)
- What landing pages do their ads point to?

### Social & Community

- What's their most engaged content on LinkedIn/X/Instagram?
- Do they have a community? How active is it?
- What influencers/partners do they work with?
- What events/webinars do they run?

---

## Layer 3: Product Intelligence

### Feature Comparison Matrix

```
| Feature           | Us    | Competitor A | Competitor B | Gap? |
|-------------------|-------|-------------|-------------|------|
| Core Feature 1    | ✓ Yes | ✓ Yes       | ✗ No        | —    |
| Core Feature 2    | ✓ Yes | ✓ Yes       | ✓ Yes       | —    |
| Feature 3         | ✗ No  | ✓ Yes       | ✓ Yes       | GAP  |
| Feature 4         | ✓ Yes | ✗ No        | ✗ No        | ADV  |
| Pricing           | $99   | $199        | $149        | ADV  |
| Free trial        | 14d   | 7d          | No          | ADV  |
| Integrations      | 5     | 12          | 3           | GAP  |
```

### Pricing Intelligence

| Competitor | Lowest | Target | Enterprise | Model |
|-----------|--------|--------|-----------|-------|
| Competitor A | $49/mo | $149/mo | Custom | Per seat |
| Competitor B | $29/mo | $99/mo | $499/mo | Per usage |
| Us | $29/mo | $99/mo | Custom | Flat rate |

---

## Layer 4: Positioning Analysis

### Message Mapping

For each competitor, capture:

```
COMPETITOR: {Name}
═══════════════════

TAGLINE: "{Their tagline}"
CATEGORY CLAIM: "{How they describe what they are}"
TARGET AUDIENCE: "{Who they say they serve}"
KEY DIFFERENTIATOR: "{What they claim is unique}"
PROOF POINTS: "{Numbers, logos, awards they cite}"
PRICING POSITION: {Premium / Mid-market / Budget}

HOMEPAGE FIRST IMPRESSION:
  H1: "{Their headline}"
  Sub: "{Their subheadline}"
  CTA: "{Their primary CTA}"

TONE: {Professional / Casual / Technical / Aspirational}

OUR COUNTER-POSITION:
  "{How we position against them specifically}"
```

### Win/Loss Analysis

After every lost deal or churned customer, capture:
- Who did they choose instead?
- Why? (features, price, relationship, timing)
- What would have changed the outcome?

Aggregate quarterly. Patterns reveal positioning gaps.

---

## Layer 5: Strategic Intelligence

### Porter's Five Forces (Quick Assessment)

| Force | Question | Impact |
|-------|----------|--------|
| **Rivalry** | How many direct competitors? How aggressive? | High/Med/Low |
| **New entrants** | How easy is it for new players to enter? | High/Med/Low |
| **Substitutes** | What non-competitors solve the same problem? | High/Med/Low |
| **Buyer power** | Can customers easily switch? | High/Med/Low |
| **Supplier power** | Do we depend on key vendors/platforms? | High/Med/Low |

### Competitor Strategic Bets

For each major competitor, hypothesize:
- What are they betting on in the next 12 months?
- What signals support this hypothesis?
- What would it mean for us if they succeed?
- What should we do about it?

---

## Sales Battlecard Template

One page per competitor. Sales team carries these into every deal.

```
BATTLECARD: {Competitor Name}
═══════════════════════════════

WHEN YOU'RE COMPETING AGAINST THEM:
  They win when: {scenarios where they're strong}
  We win when: {scenarios where we're strong}

THEIR STRENGTHS (acknowledge honestly):
  1. {Strength}
  2. {Strength}

THEIR WEAKNESSES (exploit respectfully):
  1. {Weakness} → Our response: "{What we say}"
  2. {Weakness} → Our response: "{What we say}"

COMMON OBJECTIONS FROM THEIR CUSTOMERS:
  "But {Competitor} has {feature}..."
  → Response: "{Our counter}"

  "But {Competitor} is cheaper..."
  → Response: "{Our value argument}"

TRAP QUESTIONS (ask the prospect these):
  1. "{Question that exposes competitor's weakness}"
  2. "{Question that highlights our advantage}"

PROOF POINTS:
  - {Customer who switched from them to us + result}
  - {Head-to-head metric where we win}

PRICING COMPARISON:
  Them: {price + model}
  Us: {price + model}
  Net: {where we're cheaper/better value}
```

---

## CI Calendar

| Frequency | Activity | Output |
|-----------|----------|--------|
| **Weekly** | Signal monitoring (15 min) | Alert if anything changed |
| **Monthly** | Ad library scan + content gap check | Updated competitive brief |
| **Quarterly** | Full competitive review (pricing, positioning, features) | Updated battlecards |
| **Semi-annual** | Strategic assessment (Five Forces, market shifts) | Strategy memo |
| **Per lost deal** | Win/loss analysis | Pattern tracking |
