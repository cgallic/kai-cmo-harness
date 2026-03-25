# Retargeting & Remarketing Playbook

> **Use when:** Re-engaging visitors who didn't convert, warming cold audiences, or building multi-touch ad sequences.

---

## Retargeting vs Remarketing

| Term | Channel | How It Works |
|------|---------|-------------|
| **Retargeting** | Paid ads (Meta, Google, TikTok) | Pixel tracks visitors → show ads to them on other sites/platforms |
| **Remarketing** | Email/SMS | Collect email → send automated follow-up sequences |
| **Both** | Combined | Pixel + email working together across channels |

---

## Audience Segmentation

### The Retargeting Funnel

```
SEGMENT 1: ALL SITE VISITORS (last 30 days)
  │  Size: Largest
  │  Intent: Lowest
  │  Ad type: Awareness, social proof, brand story
  │  Frequency cap: 3-5 impressions/week
  │
  ├── SEGMENT 2: PRODUCT/PRICING PAGE VISITORS (last 14 days)
  │    Size: Medium
  │    Intent: Medium-High
  │    Ad type: Feature benefits, comparison, testimonials
  │    Frequency cap: 5-7 impressions/week
  │
  ├── SEGMENT 3: CART/SIGNUP ABANDONERS (last 7 days)
  │    Size: Smallest
  │    Intent: Highest
  │    Ad type: Urgency, incentive, objection handling
  │    Frequency cap: 7-10 impressions/week
  │
  └── SEGMENT 4: PAST CUSTOMERS (exclude from acquisition)
       Size: Variable
       Intent: Upsell/cross-sell
       Ad type: New features, upgrades, loyalty offers
       Frequency cap: 3-5 impressions/week
```

### Audience Rules

| Audience | Window | Size Minimum | Exclude |
|----------|--------|-------------|---------|
| All visitors | 30 days | 1,000+ | Converters |
| Product viewers | 14 days | 500+ | Converters |
| Cart abandoners | 7 days | 100+ | Purchasers |
| Video viewers (50%+) | 30 days | 500+ | Converters |
| Email engagers | 90 days | 500+ | Recent purchasers |
| Past customers | 180 days | 100+ | Active subscribers |

**Critical rule:** Always exclude converted users from conversion-focused retargeting. Showing "Sign up now!" to existing customers is wasted spend and annoying.

---

## Platform-Specific Setup

### Meta Retargeting

**Pixel setup:**
1. Install Meta Pixel on all pages
2. Configure standard events: PageView, ViewContent, AddToCart, InitiateCheckout, Purchase, Lead
3. Verify with Meta Pixel Helper browser extension

**Custom audiences to create:**
```
1. All Website Visitors (30 days)
2. Pricing Page Visitors (14 days)
3. Blog Readers — 3+ pages (30 days)
4. Video Viewers — 50%+ (30 days)
5. Instagram/Facebook Engagers (90 days)
6. Email List Upload (customer match)
7. Lookalike 1% from Purchasers
```

**Campaign structure:**
```
Campaign: RETARGETING
├── Ad Set 1: Product Page Visitors (14d)
│   Budget: 40% of retargeting spend
│   Ads: Testimonials, feature deep-dives, comparison
│
├── Ad Set 2: Cart/Signup Abandoners (7d)
│   Budget: 35% of retargeting spend
│   Ads: Urgency, incentive, "still thinking about it?"
│
└── Ad Set 3: All Visitors (30d, exclude above)
    Budget: 25% of retargeting spend
    Ads: Brand story, social proof, awareness
```

### Google Retargeting

**Audiences:**
- Google Ads remarketing tag (installed with GA4)
- Segment by page visited, time on site, number of visits
- YouTube viewers (if running YouTube ads)
- Customer Match (email list upload)

**Campaign types for retargeting:**
```
1. Display Remarketing
   - Banner ads across Google Display Network
   - Use responsive display ads (not uploaded images)
   - Frequency cap: 5-7 impressions/day

2. RLSA (Remarketing Lists for Search Ads)
   - Bid higher when past visitors search for your keywords
   - Most cost-effective retargeting — they're actively searching
   - Add remarketing audience as "Observation" to search campaigns

3. YouTube Remarketing
   - Show video ads to past visitors
   - Powerful for brand recall
   - Use 15-second non-skippable for high-intent segments

4. Performance Max
   - Automatically retargets across all Google surfaces
   - Add your remarketing audiences as "Signals"
```

### Email Remarketing (Abandoned Cart/Signup)

**Sequence timing:**
```
Email 1: 1 hour after abandonment
  Subject: "You left something behind"
  Content: Show what they were looking at, single CTA to return

Email 2: 24 hours after abandonment
  Subject: "Still thinking about it?"
  Content: Address the top objection, add social proof

Email 3: 72 hours after abandonment
  Subject: "Here's 10% off — just for you" (optional incentive)
  Content: Time-limited offer, urgency

Email 4: 7 days after abandonment (final)
  Subject: "Last chance: your [item] is waiting"
  Content: Scarcity/urgency, final reminder
```

---

## Creative Strategy by Segment

### Cold → Warm (All Visitors)

**Goal:** Build familiarity and trust
**Creatives:**
- Brand story video (30-60s, who we are)
- Customer testimonial carousel
- Social proof stats ("500+ companies trust us")
- Educational content from your blog

### Warm → Hot (Product/Pricing Visitors)

**Goal:** Overcome objections and demonstrate value
**Creatives:**
- Feature comparison (us vs competitor)
- Case study with specific results
- Demo video or product walkthrough
- "3 reasons why [persona] switched to [product]"

### Hot → Convert (Abandoners)

**Goal:** Remove final barrier
**Creatives:**
- Direct "Come back" message with incentive
- Risk reversal: "30-day money-back guarantee"
- Urgency: "Your trial setup is waiting" (if they started signup)
- FAQ format addressing top objections

### Customers → Expand (Past Buyers)

**Goal:** Upsell, cross-sell, retain
**Creatives:**
- New feature announcements
- Upgrade path benefits
- Referral program promotion
- Exclusive customer content/events

---

## Budget Allocation

### Retargeting Budget as % of Total Ad Spend

| Company Stage | Retargeting % | Why |
|--------------|---------------|-----|
| Early (< $5K/mo spend) | 15-20% | Small audience, need cold traffic first |
| Growth ($5K-50K/mo) | 20-30% | Retargeting audiences growing |
| Scale ($50K+/mo) | 25-35% | Large audiences, highest ROAS channel |

### By Segment

| Segment | % of Retargeting Budget | Expected ROAS |
|---------|------------------------|---------------|
| Cart/signup abandoners | 35% | 5-15x |
| Product/pricing visitors | 40% | 3-8x |
| All visitors (awareness) | 25% | 1-3x |

---

## Measurement

### Key Metrics

| Metric | Target | Red Flag |
|--------|--------|----------|
| Retargeting ROAS | 3-10x | < 2x |
| Frequency (Meta) | 3-7/week | > 15/week |
| Click-through rate | 0.5-2% | < 0.3% |
| View-through conversions | Track but don't over-credit | > 50% of total conversions |
| Audience decay | <30% drop-off per week | > 50% drop-off |

### Attribution Note
Retargeting inflates platform-reported ROAS because these users were already warm. Always compare:
- **Platform-reported ROAS** (includes view-through, generous attribution)
- **GA4-reported conversions** (last-click, more conservative)
- **Incrementality** (the true test — did retargeting cause the conversion or would they have converted anyway?)

Run a holdout test quarterly: exclude 10% of your retargeting audience and compare conversion rates. The difference = true retargeting lift.
