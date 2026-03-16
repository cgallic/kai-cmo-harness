# Email & Lifecycle Marketing

> **Use when:** Building email automation flows, selecting email platforms, designing onboarding/retention sequences, or measuring email marketing ROI.

## Quick Reference

- Platform selection depends on business model: Klaviyo (DTC), Braze (Mobile/Fintech), Customer.io (B2B SaaS), HubSpot (SMB)
- Email authentication triad: SPF + DKIM + DMARC (required for deliverability)
- IP warming: 30-day gradual volume increase, prioritizing engaged users
- Focus on triggered emails (high incrementality) over blast campaigns
- Measure Revenue Per Recipient (RPR), not just open rates
- Sunset inactive users at 90-180 days to maintain sender reputation

---

## Platform Selection Framework

| Feature | Klaviyo | Braze | Customer.io | HubSpot |
|---------|---------|-------|-------------|---------|
| **Best For** | DTC / E-commerce | Mobile App / Fintech | B2B SaaS / Tech | B2B Services / SMB |
| **Data Model** | Catalog & Transaction | Real-Time Stream | Event & Attribute Logic | CRM & Contact |
| **Latency** | Near Real-Time | Real-Time (ms) | Real-Time | Batch / Near RT |
| **Engineering Load** | Low (Plug-and-Play) | High (Dev Resources) | Medium (Logic-Heavy) | Low (All-in-One) |
| **Cost Driver** | Contact Count | Data Points / MAU | Contact Count | Contact Tier & Seat |
| **Limitation** | Complex Non-Retail Logic | Learning Curve & Cost | Visual Editor | Segmentation Depth |

### Selection Guidance

**Choose Klaviyo when:**
- Running a DTC/e-commerce business
- Need pre-built flows (abandoned cart, back-in-stock)
- Small team with limited engineering resources

**Choose Braze when:**
- Mobile-first product
- Require real-time (millisecond) message triggers
- Cross-channel orchestration (email + push + SMS + in-app)
- Have engineering resources for implementation

**Choose Customer.io when:**
- B2B SaaS with complex behavioral triggers
- Need flexible event-based logic trees
- State-change-based automation is critical

**Choose HubSpot when:**
- B2B services or SMB
- Need CRM + email in one platform
- Limited technical resources

---

## Email Authentication Setup

### Required Protocols (2024+ Gmail/Yahoo Standards)

1. **SPF (Sender Policy Framework)**
   - DNS record specifying authorized sending IPs
   - Prevents domain spoofing

2. **DKIM (DomainKeys Identified Mail)**
   - Cryptographic signature verifying message integrity
   - Establishes long-term domain reputation

3. **DMARC (Domain-based Message Authentication)**
   - Unifies SPF and DKIM
   - Progression: `p=none` (monitor) -> `p=quarantine` -> `p=reject` (block unauthorized)

4. **BIMI (Brand Indicators for Message Identification)**
   - Displays verified brand logo in inbox
   - Requires DMARC at `p=quarantine` or `p=reject`
   - Improves open rates through visual recognition

---

## IP Warming Protocol

**Critical insight:** Engagement density matters more than volume. 100 emails with 50% open rate > 1,000 emails with 5% open rate.

| Phase | Days | Daily Volume | Target Audience | Success Metrics |
|-------|------|--------------|-----------------|-----------------|
| **Foundation** | 1-3 | 50-200 | Internal, seed list, clicked last 24h | >40% OR, 0% complaints |
| **Calibration** | 4-7 | 500-1,000 | Opened in last 7 days | >30% OR, <0.1% bounce |
| **Acceleration** | 8-14 | 2,000-5,000 | Opened in last 30 days | >25% OR, <0.1% complaints |
| **Scaling** | 15-21 | 10,000-25,000 | Opened in last 60 days | >20% OR, high delivery |
| **Maturity** | 22-30 | 50,000+ | Full list (exclude 90-180 day inactive) | Stabilized benchmarks |

**Rules:**
- Double volume every 2 days only if metrics hold
- Foundation phase: exclude anyone with questionable engagement
- Pause warming immediately if complaints spike

---

## Team Structure by Stage

### Seed to Series A (<$5M ARR)
- **Model:** Marketing Generalist owns entire stack
- **Tools:** Klaviyo or HubSpot (plug-and-play)
- **Risk:** Technical debt as complexity scales
- **Hiring trigger:** Data integration exceeds technical capability

### Series B ($10M-$50M ARR)
- **Model:** Head of Lifecycle + Agency hybrid
- **In-House:** Strategy, data operations, segmentation
- **Outsource:** Email design, HTML coding, copywriting
- **Benefit:** Full-stack skills without hiring multiple specialists

### Series C to IPO (>$50M ARR)
- **Model:** In-house studio
- **Team composition:**
  - Head of Lifecycle (owns P&L)
  - Lifecycle Strategists (by segment: Onboarding, Retention, Win-back)
  - Marketing Operations (tech stack, integrations)
  - Technical Marketer (HTML, API triggers)
  - Data Analyst (incrementality testing, cohort analysis)

---

## Sequence Architecture by Business Model

### B2B SaaS: Onboarding Sequence

**Principle:** Trigger by product state changes, not arbitrary time delays.

| Email | Timing | Trigger | Content |
|-------|--------|---------|---------|
| 1. Magic Link | Immediate | Signup | Direct login link + outcome focus + get-started checklist |
| 2. Empty State Solver | Day 1-2 | Has NOT completed activation event | Templates, pre-filled data, video walkthroughs |
| 3. Viral Loop | Day 3-5 | Activated | "Invite your team" - multi-player improves retention |
| 4. Sales Hand-Raiser | Day 7+ | High usage threshold | Plain-text from founder/AE, reference specific feature usage |

**Anti-pattern:** Sending "Empty State Solver" to activated users destroys credibility.

### B2B SaaS: Trial Expiration

| Timing | Focus | Message |
|--------|-------|---------|
| T-3 Days | Value Summary | "Here's what you achieved" with dynamic usage data |
| T-1 Day | Loss Aversion | "Don't lose your work" - emphasize data/project access pause |
| T-0 Day | Grace Period | Offer 48-hour extension if they reply - starts conversation |

---

### DTC: Abandonment Psychology

**Key insight:** Not all abandonment is equal. Tailor response to intent level.

| Type | Intent | Strategy | Discount? |
|------|--------|----------|-----------|
| **Browse Abandonment** | Low | Soft touch: "Saw something you liked?" + 2-3 recommendations | NO - devalues brand |
| **Cart Abandonment** | Medium | Helpful: "Your bag is waiting" + address friction (shipping, returns) | Consider |
| **Checkout Abandonment** | High | Urgent: User hit price shock. Deploy dynamic discount or free shipping | YES |

### DTC: Inventory Triggers (Highest RPR)

**Low Stock Alert:**
- Trigger: Inventory < threshold (e.g., 5 units)
- Subject: "Almost gone"
- Psychology: Genuine FOMO

**Back in Stock:**
- High demand, deploy carefully
- Drip-feed notifications (VIPs first, then general list)
- Prevents site crashes and rewards loyalty

---

### Fintech/Crypto: Trust & Compliance

**Transactional Opportunity:**
- Withdrawal confirmations, deposit alerts see >80% open rates
- "Trojan Horse" marketing: embed feature education in transactional emails
- Example: Suggest "Whitelist Addresses" in withdrawal confirmation
- Constraint: Too much marketing content may legally reclassify as commercial (requires unsubscribe)

**Prohibited Terminology (SEC, FCA, FINRA):**
- "Guaranteed returns"
- "Risk-free yield"
- "Passive income"

**Required Elements:**
- Prominent risk disclaimers
- UK: Standalone box with specific font sizes
- Security alerts (New Device Login, Withdrawal Address Added) must deliver <1 minute

---

## Subject Line Formulas

**Mobile truncation:** Keep under 50 characters, front-load critical keywords.

| Archetype | Formula | Example | Best For |
|-----------|---------|---------|----------|
| Pattern Interrupt | Unexpected statement | "Don't buy this yet" | B2B Nurture |
| Question | + ? | "Ready to double your open rate?" | SaaS Activation |
| Insider | [Name], a quick idea for [Company] | "John, a quick idea for Acme Corp" | Cold Outreach |
| Scarcity | [Number] left in stock | "Only 3 left in your size" | DTC Abandonment |
| Utility | Your [Asset] is inside | "Your Q3 Audit Report is inside" | Content Delivery |
| Personal | [Name], did you see this? | "Sarah, did you see this update?" | Re-engagement |

**Optimization:** "Shipped: Your Order #123" > "Your Order #123 has been Shipped"

---

## List Hygiene & Spam Traps

### Spam Trap Types

| Type | Cause | Consequence |
|------|-------|-------------|
| **Pristine** | Scraping websites or buying lists | Immediate blocklisting |
| **Recycled** | Old abandoned addresses reactivated | Gradual reputation degradation |

### Remediation Protocol

1. **Sunset Policy:** Auto-suppress users with no opens/clicks in 90-180 days
2. **Re-engagement Campaign:** Final "Do you still want to hear from us?" before suppression
3. **Real-Time Validation:** Use NeverBounce/ZeroBounce at signup to catch typos

---

## Measurement Framework

### The Attribution Problem

Last-click attribution undervalues email by crediting only the final touchpoint. A user may read 5 newsletters before clicking a retargeting ad to purchase - last-click credits only the ad.

### Incrementality Testing (Gold Standard)

**Methodology:**
1. Identify target audience for campaign/flow
2. Randomly withhold 10-20% (Control Group)
3. Send to remaining 80-90% (Test Group)
4. Compare conversion rates

**Formula:** Incrementality Lift = (Test CR - Control CR) / Control CR

**Insight:** Blast emails often show lower incrementality (customers would buy anyway). Triggered emails (Abandoned Cart) show high incrementality.

### Email Marketing P&L Model

| Line Item | Calculation |
|-----------|-------------|
| **Gross Revenue** | Last Click Revenue + View Through Revenue |
| **(-)** COGS | Revenue x (1 - Gross Margin %) |
| **(-)** Channel Costs | ESP Fees + SMS Costs + Data Warehouse Fees |
| **(-)** Production Costs | Agency Fees + Internal Salaries + Creative Costs |
| **(=) Contribution Margin** | Revenue - (COGS + Channel + Production) |
| **ROI** | Contribution Margin / Total Costs |

### Metrics Hierarchy

| Avoid (Vanity) | Track (Value) |
|----------------|---------------|
| Total Emails Sent | Revenue Per Recipient (RPR) |
| Total Opens (inflated by Apple MPP) | Conversion Rate |
| Open Rate alone | Unsubscribe Rate per Campaign |
| Click Rate alone | Contribution Margin |

---

## Anti-Patterns to Avoid

### 1. Blast Culture
- **Pattern:** Generic newsletters to entire database under revenue pressure
- **Consequence:** List fatigue, declining engagement, spam folder placement
- **Correction:** Segment by engagement level; full-list only for major announcements

### 2. Measurement Theater
- **Pattern:** Reporting impressive but actionable metrics (Total Sent, Total Opens)
- **Consequence:** Optimizing for volume, not value; increased costs
- **Correction:** Report RPR, Conversion Rate, Unsubscribe Rate per Campaign

### 3. Buying/Scraping Lists
- **Pattern:** Purchasing leads or scraping emails
- **Consequence:** Pristine spam traps, immediate blocklisting, GDPR/CCPA/CASL liability
- **Correction:** Organic acquisition only (inbound, content, paid to landing pages)

---

## Checklist

### Pre-Launch Infrastructure
- [ ] Platform selected based on business model
- [ ] SPF, DKIM, DMARC configured
- [ ] DMARC policy progression planned (none -> quarantine -> reject)
- [ ] IP warming schedule created (if dedicated IP)
- [ ] List validation tool integrated at signup

### Sequence Design
- [ ] Triggers based on behavioral state changes (not just time delays)
- [ ] Abandonment flows differentiated by intent level
- [ ] Onboarding sequence adapts based on activation status
- [ ] Trial expiration includes value summary + loss aversion + grace period
- [ ] Re-engagement campaign before sunset suppression

### Compliance (Fintech/Crypto)
- [ ] No prohibited terminology (guaranteed returns, risk-free, passive income)
- [ ] Risk disclaimers prominently displayed
- [ ] Transactional emails remain primarily transactional
- [ ] Security alerts deliver < 1 minute

### List Hygiene
- [ ] Sunset policy defined (90-180 day threshold)
- [ ] Re-engagement campaign configured
- [ ] Real-time email validation at point of signup
- [ ] Regular spam trap monitoring

### Measurement
- [ ] Incrementality testing methodology established
- [ ] Holdout groups configured for major flows
- [ ] P&L tracking implemented (not just revenue)
- [ ] Reporting focused on RPR, conversion rate, contribution margin
