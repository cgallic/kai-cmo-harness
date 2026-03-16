# Paid Acquisition Framework

> **Use when:** Planning, executing, or optimizing paid media campaigns across search, social, display, and programmatic channels. Apply when scaling customer acquisition, allocating budgets, building creative strategies, or measuring incrementality.

## Quick Reference

- **Primary Goal:** Incremental customer acquisition at sustainable unit economics
- **Key Metrics:** iCAC, Contribution Margin, CAC Payback, LTV:CAC, Magic Number
- **Core Principle:** Creative is the new targeting lever in algorithmic environments
- **Measurement:** Triangulate using MTA + MMM + Incrementality Testing
- **Anti-Pattern:** Avoid ROAS Illusion (high attributed ROAS, flat revenue)

---

## 1. Unit Economics Framework

### B2B SaaS Benchmarks

| Metric | Definition | Target | Implication |
|--------|------------|--------|-------------|
| **CAC Payback** | Time to recover CAC via Gross Profit | < 12 months | >18 months = heavy capital reliance |
| **LTV:CAC** | Lifetime Value / CAC | > 3:1 (ideal 4:1+) | <3:1 = not scalable; >5:1 = under-invested |
| **New CAC Ratio** | S&M Spend / New ARR | $1.00-$1.50 | >$1.50 is inefficient |
| **Magic Number** | (New ARR x 4) / Previous Q S&M | > 0.75 | >0.75 = invest more; <0.5 = fix funnel |
| **NRR** | Net Revenue Retention | 100-110%+ | High NRR reduces acquisition pressure |

### eCommerce Contribution Margin Hierarchy

1. **CM1 (Product Margin):** Revenue - COGS
2. **CM2 (Order Margin):** CM1 - Variable Logistics (shipping, packaging, transaction fees)
3. **CM3 (Contribution Margin):** CM2 - Variable Marketing (CAC)

**Target:** 15-25% CM3 on first order for sustainability. Subscriptions can tolerate lower/negative CM3 if 60-90 day LTV is strong.

### Variable ROAS by Margin

- **High-Margin Products (80% GM):** Can sustain 1.5x ROAS
- **Low-Margin Products (25% GM):** Require 5.0x ROAS to break even

---

## 2. Audience Architecture

### The New Targeting Paradigm

**Old Model:** Hyper-segmentation (demographics, interests)
**2025 Model:** Broad targeting + Audience Signals + Let creative do the targeting

### First-Party Data Strategy

**Data Clean Rooms (DCRs):**
- Secure environment for matching hashed identifiers (SHA-256)
- Use cases: Audience overlap analysis, suppression, advanced attribution
- Middleware: Snowflake, LiveRamp, InfoSum

### B2B Account-Based Marketing Tiers

| Tier | Accounts | Strategy | Approach |
|------|----------|----------|----------|
| **Tier 1 (1:1)** | <50 | Must-Win | Bespoke creative, executive outreach |
| **Tier 2 (1:Few)** | 50-500 | Industry clusters | Segment-specific content |
| **Tier 3 (1:Many)** | 500+ | Programmatic | Firmographic targeting |

**Intent Layering:** Activate campaigns only when accounts show "Surging Intent" (pricing page visits, competitor research).

---

## 3. Creative Engine

### The 7-Hook Framework

| Hook Type | Mechanism | Example |
|-----------|-----------|---------|
| **Curiosity Gap** | Brain's desire for closure | "We fixed this disaster in 2 hours..." |
| **Negative/Fear** | Loss aversion | "3 mistakes killing your SaaS growth" |
| **Transformation** | Visual before/after | Split screen: messy spreadsheet vs. clean dashboard |
| **Us vs. Them** | Tribal alignment | "Why we ditched Spreadsheets for..." |
| **Specificity/Data** | Precise numbers = credibility | "How we generated $4,203 in 7 days" |
| **Story/Vulnerability** | Authenticity builds trust | "I almost shut down my business until..." |
| **Pattern Interrupt** | Physical scroll stop | ASMR, glitch effects, sudden movement |

### 3:2:2 Creative Testing Method

**Structure:**
- 3 Creatives (videos/images)
- 2 Primary Texts (short punchy + long story)
- 2 Headlines (direct benefit + curiosity)

**Execution:**
1. Use DCO to test combinations (12 variations)
2. Winner = highest platform spend allocation, not CTR
3. Move winning post ID to Scaling campaign
4. Reset test campaign with new variables

### Direct Response Copy Framework (PAS)

1. **Problem:** Identify the pain point
2. **Agitation:** Make it visceral - what happens if unsolved?
3. **Solution:** Product as the only logical answer

**Best Practices:**
- Front-load critical info (mobile truncation)
- Headlines under 40 characters
- Specific CTAs ("Get Your Free Audit" > "Submit")

---

## 4. Platform Playbooks

### Google Ads

**Hagakure/STAG Method:**
- Consolidate account structure for data density
- Need 30-50 conversions/month/campaign for optimization
- Use Broad Match + Smart Bidding (tCPA/tROAS)
- Group keywords by landing page theme

**Performance Max Optimization:**
- Create specific Asset Groups per product category
- Use Brand Exclusion lists (prevent branded cannibalization)
- Feed-Only PMax for eCommerce (forces Shopping placements)
- Enable New Customer Acquisition (NCA) goals

### Meta (Facebook/Instagram)

**Advantage+ Shopping Campaigns (ASC):**
- Hybrid structure: ASC for scaling + Manual for testing
- Set Customer Budget Cap (max 10% on existing customers)
- Scale 10-20% every few days if CPA holds

**Remix Strategy:** Combat fatigue by creating 5 variations of first 3 seconds while keeping video body the same.

### TikTok

- **Spark Ads:** 134% higher completion rates, 142% higher engagement
- **TikTok Shop:** Direct in-app purchase for impulse categories
- **Search Ads Toggle:** Capture Gen Z search intent

**Principle:** "Don't Make Ads, Make TikToks"

### LinkedIn

- **Thought Leader Ads:** 1.7x higher CTR (sponsor employee posts)
- **Content Funnel:**
  - TOFU: Ungated video + Thought Leader ads
  - MOFU: Document Ads (whitepapers in-feed)
  - BOFU: Conversation Ads + Lead Gen Forms

### Twitter/X

- Vertical video (9:16) underpriced vs. LinkedIn
- Reply Strategy: Target influencer/trending topic replies for contextual placement

### Programmatic/DSPs

**Selection Criteria:**
- Supply Path Optimization (SPO)
- Inventory quality and fraud protection

**CTV Metrics:**
- Video Completion Rate (VCR)
- Cost Per Completed View (CPCV)
- Household graph matching for cross-device attribution

---

## 5. Measurement Framework

### Triangulation Model

| Method | Use Case | Limitation |
|--------|----------|------------|
| **Multi-Touch Attribution (MTA)** | Day-to-day optimization | Signal loss, last-click bias |
| **Marketing Mix Modeling (MMM)** | Quarterly budget allocation | Requires historical data |
| **Incrementality Testing** | Proving causality (gold standard) | Resource intensive |

### Geo-Lift Testing Methodology

1. **Define:** Objective and metric (sales, installs)
2. **Select Regions:** Use statistical tools for correlation matching
3. **Design:** Assign Test and Control regions
4. **Execute:** Run ads only in Test region (4 weeks)
5. **Analyze:** Compare actual vs. counterfactual performance

**Formula:**
```
Incremental ROAS = Incremental Revenue / Ad Spend in Test Region
```

### MMM Implementation

1. Gather weekly data: Spend by channel, Revenue, Control Variables
2. Fit model using Robyn (Meta) or Meridian (Google)
3. Calibrate with Incrementality Test results

---

## 6. Scaling Roadmap

### B2B SaaS (0-$10M ARR)

| Stage | ARR | Focus | Paid Strategy | Key Metric |
|-------|-----|-------|---------------|------------|
| **Stage 1** | $0-$1M | PMF | Retargeting, competitor keywords | Lead quality |
| **Stage 2** | $1-$3M | Repeatable motion | Non-brand search, LinkedIn/Meta TOFU | CAC Payback, Magic Number |
| **Stage 3** | $3-$10M | Scale | ABM, content syndication, sponsorships | LTV:CAC, NRR |

### eCommerce Seasonal Tactics

- **Q4 Peak:** Lower ROAS targets if CVR rises (volume > efficiency)
- **Q5 (January):** Exploit low CPMs for list building

---

## 7. Business Model Variations

| Dimension | B2B SaaS | DTC eCommerce | Fintech/Crypto |
|-----------|----------|---------------|----------------|
| **Goal** | Lead/Demo | Immediate Purchase | App Install + KYC |
| **Cycle** | 3-9 months | Minutes-Days | Medium (trust barrier) |
| **Key Metric** | CAC Payback, NRR | CM, ROAS | Cost Per Funded Account |
| **Top Channel** | LinkedIn, Google Search | Meta, Google Shopping, TikTok | Affiliate, Programmatic |
| **Creative** | Educational, trust | Emotional, impulse | Credibility, incentive |

**Fintech Note:** Optimize for "Funded Account" or "First Transaction" - not app installs.

---

## 8. Anti-Patterns to Avoid

### ROAS Illusion
- **Symptom:** 10x ROAS but flat revenue
- **Cause:** Over-investing in branded search/retargeting
- **Fix:** Measure Incremental ROAS, use Brand Exclusions

### Over-Segmentation
- **Symptom:** Hundreds of ad groups with fragmented data
- **Cause:** Manual interest targeting preventing algorithm learning
- **Fix:** Account consolidation (STAGs, Broad targeting)

### Set-and-Forget
- **Symptom:** Slow performance degradation
- **Cause:** Creative fatigue, algorithm drift to low-quality inventory
- **Fix:** Creative refresh every 2-4 weeks, weekly search term audits

### Post-Click Mismatch
- **Symptom:** High CTR, low CVR, high CAC
- **Cause:** Ad promise differs from landing page experience
- **Fix:** Dedicated landing pages matching ad hook/offer

---

## Checklist

See: `/marketing-knowledge/checklists/paid-acquisition-checklist.md`
