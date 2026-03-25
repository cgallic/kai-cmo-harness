# Marketing Automation Playbook

> **Use when:** Building automated marketing workflows, lead nurture sequences, triggered campaigns, or lifecycle marketing programs.

---

## Automation Architecture

### The 4 Automation Layers

```
LAYER 1: TRIGGERS
  What starts the automation?
  - Form submission, page visit, purchase, email open
  - Time-based (30 days after signup, birthday)
  - Behavior-based (visited pricing 3x, abandoned cart)

LAYER 2: CONDITIONS
  Who qualifies?
  - Lead score threshold
  - Segment membership
  - Tag/property match
  - Negative conditions (NOT purchased, NOT opened)

LAYER 3: ACTIONS
  What happens?
  - Send email, SMS, push notification
  - Add/remove tag, update property
  - Move to different workflow
  - Create task for sales team
  - Update CRM record
  - Webhook to external tool

LAYER 4: EXITS
  When does the automation stop?
  - Goal achieved (purchased, booked demo)
  - Unsubscribed
  - Timeout (no engagement after X days)
  - Manual removal
```

---

## Essential Automation Workflows

### 1. Welcome Sequence (Post-Signup)

**Trigger:** New account creation or email signup

```
Day 0:  Welcome email — what to expect, quick-win resource
Day 1:  Quick-start guide — get value from the product in 5 minutes
Day 3:  Social proof — customer story relevant to their use case
Day 5:  Feature highlight — the one feature that drives retention
Day 7:  Check-in — "How's it going?" with link to support/community
Day 10: Advanced tip — power-user feature they haven't tried
Day 14: Trial ending / upgrade nudge (if applicable)
```

**Exit:** User converts to paid, or completes onboarding milestone

### 2. Lead Nurture (Marketing-Qualified Leads)

**Trigger:** Downloaded resource, attended webinar, visited pricing page

```
Day 0:  Deliver the resource + set expectations
Day 2:  Related content — deeper dive on the topic
Day 5:  Case study — someone like them who succeeded
Day 8:  Problem agitation — cost of not solving the problem
Day 12: Objection handling — FAQ format
Day 15: Social proof — testimonial + data
Day 20: Direct offer — demo, trial, or consultation CTA
Day 25: Last call — urgency or alternative lower-commitment CTA
```

**Exit:** Books demo, starts trial, or replies to email

### 3. Abandoned Cart / Signup Recovery

**Trigger:** Started checkout/signup, didn't complete

```
Hour 1:   "You left something behind" — show what they were doing
Hour 24:  Address top objection — FAQ or guarantee
Hour 72:  Incentive (if applicable) — 10% off, extended trial
Day 7:    Final reminder — "Still thinking about it?" + social proof
```

**Exit:** Completes purchase/signup, or 7 days elapsed

### 4. Re-Engagement (Inactive Users)

**Trigger:** No login/email open for 30 days

```
Day 30:  "We miss you" — show what's new since they left
Day 37:  Value reminder — best content/feature they haven't seen
Day 44:  Incentive — special offer to come back
Day 51:  Breakup email — "Should we stop emailing you?"
```

**Exit:** User re-engages, or unsubscribes. If no action after breakup email, reduce email frequency or suppress.

### 5. Post-Purchase / Onboarding

**Trigger:** First purchase or subscription start

```
Hour 0:  Order confirmation + next steps
Day 1:   Getting started guide
Day 3:   "How to get the most out of [product]"
Day 7:   Check-in — "How's your experience so far?"
Day 14:  Power-user tip + community invite
Day 21:  Review request — "How would you rate us?" (NPS or review)
Day 30:  Cross-sell or upsell (if appropriate)
```

**Exit:** Onboarding complete, or churns

### 6. Event / Webinar Nurture

**Trigger:** Registered for event

```
Immediately:  Confirmation + calendar invite
Day -3:      Reminder — "3 days until [event]"
Day -1:      "Tomorrow! Here's what to expect"
Hour -1:     "Starting soon! Join here: [link]"
Hour +1:     Recording + resources (even if they attended)
Day +2:      Follow-up — key takeaways + CTA
Day +5:      Related resource — deeper dive on event topic
Day +7:      Offer — product/service connected to event topic
```

**Exit:** Converts, or 7 days post-event

---

## Lead Scoring

### Scoring Model

Assign points based on behavior and demographics:

| Signal | Points | Category |
|--------|--------|----------|
| **Demographic** | | |
| Job title matches target (VP, Director, C-Suite) | +20 | Fit |
| Company size matches target | +15 | Fit |
| Industry matches target | +10 | Fit |
| **Behavioral** | | |
| Visited pricing page | +25 | Intent |
| Requested demo/trial | +50 | Intent |
| Downloaded resource | +10 | Engagement |
| Opened 3+ emails | +5 | Engagement |
| Clicked email CTA | +10 | Engagement |
| Attended webinar | +15 | Engagement |
| Visited 5+ pages in one session | +15 | Intent |
| Returned to site 3+ times | +20 | Intent |
| **Negative** | | |
| Unsubscribed from email | -30 | Disengagement |
| No activity for 30 days | -15 | Decay |
| Competitor email domain | -50 | Disqualify |
| Student email (.edu) | -20 | Disqualify |

### Score Thresholds

| Score | Status | Action |
|-------|--------|--------|
| 0-20 | Cold lead | Nurture sequence |
| 21-50 | Warm lead | Targeted content + email |
| 51-80 | Marketing Qualified Lead (MQL) | Sales outreach or demo offer |
| 81+ | Sales Qualified Lead (SQL) | Immediate sales follow-up |

---

## Segmentation Strategy

### Core Segments

| Segment | Criteria | Use For |
|---------|----------|---------|
| New subscribers | Signed up < 7 days | Welcome sequence |
| Engaged | Opened 2+ emails in 30 days | Feature announcements, offers |
| At-risk | No open in 30+ days | Re-engagement campaign |
| Power users | Daily login + high feature usage | Upsell, advocacy, referral |
| Trial users | Active trial, no purchase | Conversion sequence |
| Churned | Cancelled in last 90 days | Win-back campaign |

### Dynamic Tags

Apply tags automatically based on behavior:
```
content-interest-seo     → Visited 3+ SEO articles
product-interest-premium → Viewed pricing page 2+ times
engagement-high          → Email CTR > 5% last 30 days
engagement-low           → No open in 30+ days
lifecycle-trial          → Active trial
lifecycle-customer       → Paid customer
lifecycle-churned        → Cancelled
```

---

## Tool Selection

### By Company Stage

| Stage | Budget | Recommended | Why |
|-------|--------|-------------|-----|
| Pre-revenue | Free | Mailchimp Free, MailerLite Free | Basic automation, free tier |
| Early ($0-1M ARR) | $50-200/mo | ConvertKit, MailerLite, Brevo | Good automation, affordable |
| Growth ($1-10M) | $200-1K/mo | ActiveCampaign, Customer.io, Klaviyo | Advanced automation, CRM |
| Scale ($10M+) | $1K+/mo | HubSpot, Iterable, Braze | Enterprise features, integrations |

### Feature Comparison

| Feature | Must Have | Nice to Have |
|---------|----------|-------------|
| Email sequences | Yes | — |
| Trigger-based automation | Yes | — |
| Segmentation/tags | Yes | — |
| A/B testing | Yes | — |
| Landing page builder | — | Yes |
| CRM integration | Yes (at growth stage) | — |
| SMS/push | — | Yes |
| Lead scoring | — | Yes |
| Reporting/analytics | Yes | — |
| API/webhooks | Yes (for custom integrations) | — |

---

## Automation Hygiene

### Monthly Maintenance
- [ ] Review automation performance (open rates, CTR, conversion)
- [ ] Pause underperforming workflows (< 10% open rate)
- [ ] Update content in evergreen sequences (stale data, outdated screenshots)
- [ ] Clean email list: remove hard bounces, suppress 6-month inactive
- [ ] Check deliverability: spam score, inbox placement rate
- [ ] Review lead scoring thresholds (are MQLs actually converting?)

### Deliverability Checklist
- [ ] SPF, DKIM, DMARC configured for sending domain
- [ ] Dedicated sending domain (not personal email)
- [ ] Warm-up new sending domains (start slow, increase volume over 2-4 weeks)
- [ ] List hygiene: remove bounces immediately, suppress complaints
- [ ] Unsubscribe link in every email (CAN-SPAM requirement)
- [ ] Physical address in every email (CAN-SPAM requirement)
- [ ] Monitor bounce rate (< 2% is healthy, > 5% is critical)
- [ ] Monitor spam complaint rate (< 0.1% is healthy)

---

## Metrics

| Metric | Benchmark | Action If Below |
|--------|-----------|----------------|
| Email open rate | 20-30% | Subject line testing, list cleaning |
| Email CTR | 2-5% | Copy/CTA testing, segmentation |
| Automation conversion rate | 5-15% (depends on goal) | Sequence optimization, timing |
| Unsubscribe rate | < 0.5% per email | Reduce frequency, improve targeting |
| Bounce rate | < 2% | List cleaning, domain verification |
| Lead-to-MQL rate | 15-30% | Lead scoring calibration |
| MQL-to-SQL rate | 20-40% | Nurture quality, ICP alignment |
