# Email & Lifecycle Marketing

> **Use when:** Building email automation flows, selecting email platforms, designing onboarding/retention sequences, or measuring email marketing ROI.

## Quick Reference

- Platform selection depends on business model: Klaviyo (DTC), Braze (Mobile/Fintech), Customer.io (B2B SaaS), HubSpot (SMB)
- Email authentication is a sender requirement surface: SPF/DKIM for all Gmail senders, SPF + DKIM + DMARC for Gmail bulk senders, plus DMARC alignment and one-click unsubscribe for subscribed/marketing mail at Gmail bulk scale.
- IP/domain warming is a gradual volume and reputation process, prioritizing opted-in engaged users and monitoring provider feedback.
- Focus on behavioral-state triggers and measured holdouts over calendar-delay templates.
- Measure Revenue Per Recipient (RPR), not just open rates
- Sunset inactive users through a documented suppression policy; set the inactivity window from lifecycle, purchase cycle, and mailbox-provider feedback.

**Source posture:** Sender requirements come from Google, Yahoo, FTC, and Spamhaus primary guidance retrieved 2026-05-17. Vendor benchmarks from Braze, Customer.io, Klaviyo, Validity, and Litmus are useful for context, but do not replace the account's own baseline, holdout data, or mailbox-provider dashboards.

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

## Lifecycle State Model

Lifecycle email is behavioral-state orchestration. Every send must declare the relationship state, message class, suppression rule, and measurement goal before copy is written.

| State | Permission Basis | Primary Trigger | Allowed Message Types | Suppression Default | Measurement |
|-------|------------------|-----------------|-----------------------|---------------------|-------------|
| **Prospect subscribed** | Opt-in or customer-initiated subscription | Form submit, waitlist, content signup | Welcome, nurture, event invite, preference ask | Unsubscribed, hard bounce, complaint, inactive beyond policy | Activation, qualified action, unsubscribe/complaint |
| **Customer lifecycle** | Customer relationship and subscription preferences | Product event, purchase event, plan state, usage drop | Onboarding, activation, expansion, retention, win-back | Converted event, plan mismatch, role mismatch, frequency cap | Cohort movement, revenue, retention, holdout lift |
| **Transactional** | Transaction or account relationship | Receipt, password reset, security event, service update | Operational message only | Do not suppress for marketing opt-out if legally/service required | Delivery speed, completion, support deflection |
| **Cold outbound** | No prior relationship; risk-assessed business interest only | Named account research, trigger event, referral signal | One-to-one plain-text outreach with opt-out | Prior opt-out, no relevance evidence, high-risk sender state | Positive replies, meetings, complaints, bounces |
| **Suppressed/paused** | User or risk state blocks sending | Unsubscribe, complaint, legal hold, deliverability incident | Required transactional only | All commercial/promotional sends blocked | Suppression accuracy, re-permission outcomes |

**Hard rule:** Do not mix transactional and promotional content in the same message unless counsel, product, and deliverability owners agree that the message's primary purpose remains transactional.

## Event Taxonomy

Use snake_case events and stable properties. Do not invent event names inside flows without adding them to the tracking plan.

| Event | Fires When | Required Properties | Typical Use |
|-------|------------|---------------------|-------------|
| `email_subscribed` | User opts into a list | `source`, `consent_method`, `list_id`, `locale` | Welcome and preference setup |
| `email_unsubscribed` | User opts out | `list_id`, `unsubscribe_scope`, `method` | Global and list suppression |
| `email_complaint_received` | FBL/provider complaint received | `provider`, `campaign_id`, `message_class` | Reputation incident handling |
| `user_signed_up` | Account created | `plan`, `role`, `source`, `utm_*` | Onboarding start |
| `activation_completed` | Product-specific activation event happens | `activation_event`, `time_to_activation`, `workspace_id` | Stop empty-state flow |
| `trial_started` | Trial begins | `plan`, `trial_end_at`, `sales_owner` | Trial education |
| `trial_expiring` | Trial reaches T-minus window | `days_remaining`, `usage_summary`, `plan` | Value summary and handoff |
| `purchase_completed` | Payment or order completes | `order_id`, `value`, `currency`, `items` | Receipt and post-purchase |
| `usage_dropped` | Product activity falls below baseline | `segment`, `baseline_window`, `drop_pct` | Retention rescue |
| `winback_eligible` | Dormant user/customer meets policy | `last_active_at`, `last_purchase_at`, `risk_state` | Re-permission or win-back |

## Suppression, Preferences, And Holdouts

Suppression logic is part of the campaign, not a final send-step checkbox.

| Control | Required Behavior |
|---------|-------------------|
| **Global suppression** | Block commercial sends after unsubscribe, hard bounce, spam complaint, legal request, or manual account hold. |
| **Preference center** | Let subscribers choose topic, channel, and frequency where the platform supports it. Offer global unsubscribe as a visible option. |
| **Frequency cap** | Cap by message class and audience state. Override only for required transactional or security messages. |
| **Mutual exclusion** | Exclude users from lower-intent flows when a higher-intent or conversion event fires. |
| **Holdout group** | Keep a stable control group for high-volume lifecycle flows where business risk is acceptable. Do not hold out legally required transactional notices. |
| **Re-permission** | Ask inactive subscribers whether they still want mail before long-term suppression. Treat no response as a signal to suppress. |

## Deliverability Monitoring

| Monitor | Source | Action Threshold |
|---------|--------|------------------|
| Gmail spam rate | Google Postmaster Tools | Investigate immediately as complaint rate approaches Gmail's published ceiling. |
| Domain/IP reputation | Google Postmaster Tools, ESP dashboards, blocklist checks | Pause volume increases when reputation drops or delivery errors spike. |
| DMARC alignment | DMARC aggregate reports | Fix unauthorized senders and misaligned vendor domains before scaling. |
| Yahoo complaints | Yahoo Sender Hub complaint feedback where available | Suppress complainers and audit the triggering campaign. |
| Inbox placement | Seed tests plus real engagement by domain | Use as directional evidence, not a guarantee of inboxing. |
| Link and rendering checks | Litmus/Validity/ESP QA | Block launch for broken links, malformed headers, or missing unsubscribe. |

## Email Authentication Setup

### Required Protocols (Gmail/Yahoo Bulk Sender Standards)

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
   - Treat as brand trust infrastructure, not a guaranteed open-rate lift

5. **One-click unsubscribe (marketing/subscribed mail)**
   - Required for Gmail bulk senders sending marketing or subscribed messages
   - Use `List-Unsubscribe` plus `List-Unsubscribe-Post: List-Unsubscribe=One-Click`
   - Also include a visible unsubscribe link in the body

---

## IP Warming Protocol

**Critical insight:** Engagement density, complaints, authentication, and provider feedback matter more than raw send volume.

| Phase | Days | Daily Volume | Target Audience | Success Evidence |
|-------|------|--------------|-----------------|-----------------|
| **Foundation** | 1-3 | Low | Internal, seed list, recent clickers or purchasers | Passing SPF/DKIM/DMARC, no complaints, no unusual deferrals |
| **Calibration** | 4-7 | Controlled increase | Recently engaged subscribers | Stable delivery, low bounce, healthy replies/clicks |
| **Acceleration** | 8-14 | Controlled increase | Broader engaged segment | Provider reputation stable, complaints below published thresholds |
| **Scaling** | 15-21 | Controlled increase | Engaged and recent customers | No domain-specific delivery failures |
| **Maturity** | 22+ | Normal operating volume | Full eligible list after suppression policy | Stable reputation and documented incident response |

**Rules:**
- Increase volume only when provider dashboards and ESP delivery logs are stable
- Foundation phase: exclude anyone with questionable engagement
- Pause warming immediately if complaints, bounces, deferrals, or blocklist signals spike

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
