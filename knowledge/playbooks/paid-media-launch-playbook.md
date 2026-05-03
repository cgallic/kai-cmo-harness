# Paid Media Launch Playbook

**Source:** Brandon's TikTok breakdown of belly MD launch (2026)
**Use case:** Brand new brand launching paid ads from zero
**Applicable to:** Meta + Google Ads for e-commerce/DTC

---

## Overview

Complete framework for launching a paid media program for a new brand. This is the exact sequence a one-person paid media operator used to launch a supplement brand (belly MD) from scratch.

**Key principle:** Infrastructure → Creative → Launch → Measure (in that order)

---

## Phase 1: Infrastructure (Before Spending $1)

### Measurement Stack

**Required tools:**
1. **Triple Whale** (or similar MTA platform)
   - Multi-touch attribution
   - Post-purchase surveys (qualitative data on traffic sources)
   - Real-time performance dashboards

2. **Reverse ETL** (Sonar or similar)
   - Better tracking than standard Shopify pixel
   - Passes data back to Meta/Google
   - Increases match rates for optimization
   - Feeds campaigns more conversion data

3. **Post-Purchase Survey**
   - Built into Triple Whale
   - Asks: "Where did you first hear about us?"
   - Qualitative validation of attribution data

**Why this matters:**
- Standard Shopify tracking misses 20-30% of conversions
- Better data = better optimization = lower CPA
- Post-purchase surveys catch what pixels miss

---

## Phase 2: Creative Assets

### Landing Pages

**Don't just use PDPs.** Build dedicated landing pages for ads.

**Why:**
- Higher conversion rates (focused on one product/offer)
- Better message match (ad → landing page consistency)
- A/B test without breaking site navigation

### Ad Creative Generation

**Use AI, but don't just download and upload.**

**Process:**
1. Use Brandon's free prompt (Claude/GPT)
2. AI asks questions about your business
3. AI scripts multiple ad variations
4. **Send to client to remake in their brand voice**
5. Client sends back final ads ready to upload

**Why this works:**
- AI generates creative diversity (needed for testing)
- Client ensures brand consistency
- Faster than doing it all manually
- More variations than doing it manually

**Brandon's prompt:** Link in bio (not provided in transcript, but framework is clear)

---

## Phase 3: Meta Campaign Structure

### Campaign Setup

**Structure:** 1 campaign per product (not one big campaign)

**Example (belly MD - 3 products):**
1. Campaign 1: Product A (broad audience, 1 ad set)
2. Campaign 2: Product B (broad audience, 1 ad set)
3. Campaign 3: Product C (broad audience, 1 ad set)
4. Campaign 4: DPA (dynamic product ads - all 3 products)

**Ad sets:**
- 1 ad set per campaign (keep it simple at launch)
- All broad audiences (no detailed targeting)
- Different ads per product

**Retargeting:**
- DPA campaign targeting add-to-carts who didn't purchase
- All 3 products in one campaign

### Budget Formula

**Don't guess. Use math.**

**Formula:** `Target CPA × 50 = Minimum Budget`

**Example (belly MD):**
- Product price: $60
- Conservative CPA estimate: $40 (67% of product price)
- Minimum budget: $40 × 50 = $2,000

**Why 50 conversions:**
- Meta needs 50 conversions to exit learning phase
- Below that, campaign can't optimize properly
- Most failed campaigns are underfunded, not bad creative

**Common mistake:**
- Running ads with budgets too low to exit learning
- "We tried ads, they didn't work" = spent $500 on a $40 CPA product

### Engagement Ratio

**Brandon's formula:** (not specified in transcript, but mentioned as "highest I've ever seen")

Likely: `(Reactions + Comments + Shares) / Reach`

Track this as a leading indicator of creative quality.

---

## Phase 4: Google Campaign Structure

### What NOT to do

**Don't launch Performance Max immediately.**

**Why:**
- PMax is a black box (no visibility into what's working)
- Need baseline data first (what keywords convert? what products?)
- Can't optimize what you can't see

### Campaign Structure

**1. Non-Branded Search (4 campaigns)**
- 1 campaign per product (same as Meta)
- Multiple ad groups per campaign
- Segment by user intent/keyword theme
- Very specific ad copy per segment

**Example ad group structure:**
```
Campaign: Product A (IBS Relief)
  Ad Group 1: Symptom keywords ("IBS pain relief")
  Ad Group 2: Solution keywords ("probiotics for IBS")
  Ad Group 3: Competitor keywords ("Culturelle alternative")
```

**2. Branded Search (1 campaign)**
- Budget: $50/day (protect your brand)
- Low CPA (people already searching for you)
- Prevents competitors from bidding on your brand

**3. Shopping Campaign (1 campaign)**
- All products included
- 1 ad group per product
- Feed optimization critical (titles, images, descriptions)

### Ad Copy Relevance

**Google's goal:** Show the most relevant result (ad or organic) to the user.

**Your goal:** Be the most relevant ad.

**How:**
- Specific ad copy per ad group (match the keyword intent)
- Keyword in headline (signals relevance to Google)
- Landing page matches ad copy (Quality Score boost)

**Why this matters:**
- Higher Quality Score = lower CPC
- Better ad rank = more impressions
- More relevant = higher CTR = better performance

---

## Phase 5: Automation (The Secret Weapon)

### Claude Projects (One Per Client)

**What Brandon built:**

**For Google Ads:**
- Custom bulk upload/download templates
- Works with Google Ads Editor
- Claude generates the spreadsheets
- Upload to Editor, launch campaigns

**For Meta Ads:**
- Uses Marketfeed (bulk uploader tool)
- Claude builds Google Sheet with all ads
- Bulk upload single images or videos
- Dramatically faster than manual creation

**Why this matters:**
- "I'm a one-man show" = no team to delegate to
- Automation makes 1 person as productive as 5
- Launching new campaigns takes hours, not days

**Process:**
1. Describe campaign structure to Claude
2. Claude generates bulk upload sheets
3. Upload via Google Ads Editor or Marketfeed
4. Launch campaigns

---

## Launch Checklist

### Pre-Launch (Week 1)
- [ ] Install Triple Whale (or similar MTA)
- [ ] Set up reverse ETL (Sonar or similar)
- [ ] Add post-purchase survey to checkout
- [ ] Build landing pages for each product
- [ ] Generate AI ad scripts (Claude/GPT)
- [ ] Client remakes ads in brand voice
- [ ] Calculate budget (CPA × 50)
- [ ] Build Claude project for bulk operations

### Meta Launch (Week 2)
- [ ] Create 1 campaign per product (broad audience)
- [ ] Create DPA campaign (retargeting)
- [ ] Upload ads via Marketfeed bulk upload
- [ ] Set budget to hit 50 conversions
- [ ] Track engagement ratio daily

### Google Launch (Week 2)
- [ ] Build non-branded search campaigns (1 per product)
- [ ] Build branded search campaign ($50/day)
- [ ] Build shopping campaign (all products)
- [ ] Optimize feed (titles, images, descriptions)
- [ ] Upload via Google Ads Editor
- [ ] Monitor Quality Scores

### Post-Launch (Week 3+)
- [ ] Watch Triple Whale MTA data
- [ ] Check post-purchase survey responses
- [ ] Monitor engagement ratio (Meta)
- [ ] Monitor Quality Score (Google)
- [ ] Optimize based on performance
- [ ] Scale winners, pause losers

---

## Expected Results

**Timeline:**
- Week 1: Sales start coming in (slow at first)
- Week 2-3: Exit learning phase, optimization kicks in
- Week 4+: Performance stabilizes, scale winners

**Metrics to watch:**
- **Meta:** Engagement ratio (leading indicator), CPA, ROAS
- **Google:** Quality Score, CTR, CPA, ROAS
- **Overall:** Post-purchase survey data (validate attribution)

---

## Common Mistakes to Avoid

1. **Starting with too low a budget**
   - Can't exit learning phase
   - Campaigns never optimize
   - Declare "ads don't work" prematurely

2. **Launching Performance Max first on Google**
   - No visibility into what's working
   - Can't optimize (black box)
   - Need baseline data first

3. **Uploading AI-generated ads without brand review**
   - Doesn't match brand voice
   - Loses trust with customers
   - AI is for diversity, not final output

4. **No measurement infrastructure before spending**
   - Can't attribute sales accurately
   - Can't optimize based on real data
   - Wasted spend on guessing

5. **Using only PDPs instead of landing pages**
   - Lower conversion rates
   - Can't A/B test offers
   - Poor message match

---

## Tools Mentioned

| Tool | Purpose | Cost |
|------|---------|------|
| **Triple Whale** | Multi-touch attribution | ~$150-300/mo |
| **Sonar** | Reverse ETL (better tracking) | ~$100-200/mo |
| **Claude** | Bulk ad/campaign generation | $20/mo (Pro) |
| **Google Ads Editor** | Bulk campaign uploads | Free |
| **Marketfeed** | Meta bulk uploader | Unknown |

---

## When to Use This Playbook

**Good fit:**
- Brand new brand (no historical data)
- E-commerce/DTC products
- Multiple products to promote
- Solo operator or small team
- Need to launch fast and iterate

**Not a good fit:**
- Established brands (use different strategy)
- B2B/lead gen (different funnel)
- Service businesses (local SEO first)
- Very low budget (<$2,000/mo)

---

## Source

**Speaker:** Brandon (TikTok/Twitter/LinkedIn paid media creator)
**Example brand:** belly MD (IBS supplement, 3 products, ~$60 price point)
**Context:** "I just launched an entire paid media program for a brand new brand. This is exactly what I did."

---

## Related Harness Skills

- `/kai-ad-campaign` — Generate ad copy for Meta/Google (uses similar AI process)
- `/kai-landing-page` — Build high-converting landing pages
- `/kai-cro` — Optimize conversion funnel
- `/kai-analytics` — Set up tracking infrastructure

---

*Added to harness: 2026-04-03*
