# Andon Window Cleaning Review Bundle

**Date:** 2026-04-02  
**Generated from:** `ANDON_WINDOW_CLEANING_FIXTURE` + `run_local_service_review_flow()`  
**Source business onboarding:** `/mnt/e/Dev2/CMO_Agent_System/clients/windowcleaning/2026-04-02-andon-window-cleaning-onboarding.md`

---

## Business Profile Summary

- Brand: Andon Window Cleaning
- Archetype: `local-service`
- Service area: Lakewood Ranch, Palmetto, Venice, Bradenton, Sarasota, FL
- Stage: startup, solo operator, about 2 months old
- Core offer: residential window cleaning
- Secondary offer: small commercial jobs, screens, tracks, sills
- Primary KPI: inbound calls
- Current active channels:
  - calls
  - Google Business Profile
  - referrals / word of mouth
- Budget ceiling: `$300/month`
- Current strengths:
  - real service business already operating
  - verified GBP
  - work photos and logo exist
  - owner already thinking in terms of repeat quarterly customers
- Current bottleneck:
  - almost no public visibility or trust infrastructure, so demand cannot compound yet

Unknowns still preserved in the profile:

- owner name
- phone number to use publicly
- email address
- licensing / insurance details
- exact GBP completeness
- payment methods
- after-hours call handling

---

## Audit Summary

- Audit grade: `D`
- Overall score: `41.0 / 100`
- Total findings: `17`
- Critical findings: `3`

Category scorecard:

| Category | Score | Grade | Reading |
|---|---:|---|---|
| Offer Clarity | 100.0 | A | The service itself is understandable. |
| Trust & Proof | 25.0 | F | No review base, thin credibility assets online. |
| Conversion Path | 25.0 | F | No live site, no published phone CTA path. |
| Local SEO & Local Intent | 80.0 | B | Service area and GBP exist conceptually, but the website layer is missing. |
| Speed-to-Lead | 50.0 | D | Call path exists, but no call tracking or after-hours coverage. |
| Reviews & Reputation | 0.0 | F | No active review engine and no review inventory. |
| Channel Presence | 50.0 | D | Basic local presence exists, but almost no supporting channels. |
| Follow-Up Gaps | 50.0 | D | Customer list exists, but no follow-up or repeat engine. |

Interpretation:

This is not a failing business. It is a very early local-service business with real-world traction but almost no compounding marketing infrastructure yet.

The main growth problem is:

- people do not know the business exists
- people have little trust proof when they do find it
- there is no repeatable follow-up engine

---

## Top Prioritized Findings

These are the highest-signal findings from the current application flow.

1. `P0 / critical / website`
   Title: `Website has a live primary destination`
   Why it matters: the business has a domain but no live site, so demand has nowhere credible to convert.

2. `P0 / critical / website`
   Title: `Primary phone number is available`
   Why it matters: calls are the core KPI, but there is no confirmed public phone path in the current system.

3. `P0 / critical / website`
   Title: `Phone CTA is expected to be prominent`
   Why it matters: local-service conversion depends on fast, obvious phone action.

4. `P1 / high / website`
   Title: `Review volume is competitive`
   Why it matters: zero reviews makes the business hard to trust against established competitors.

5. `P1 / high / website`
   Title: `Average review rating is healthy`
   Why it matters: there is no visible rating signal yet.

6. `P1 / high / website`
   Title: `Certifications or guarantees are present`
   Why it matters: there is no explicit trust or risk-reduction layer on the public-facing brand.

7. `P1 / high / website`
   Title: `Call tracking is enabled`
   Why it matters: the business cannot yet measure which actions actually make the phone ring.

8. `P1 / high / website`
   Title: `Lead response SLA is defined`
   Why it matters: fast response is probably a competitive edge, but it is not operationalized.

9. `P1 / high / social`
   Title: `Reviews channel is active`
   Why it matters: there is no review-generation loop.

10. `P1 / high / social`
    Title: `Review count is healthy for a local-service brand`
    Why it matters: the local proof engine has not started yet.

---

## Typed Proposed Actions

These are aligned to the current action system and policy vocabulary.

### 1. Website foundation

- Channel: `website`
- Action type: `update_page_copy`
- Title: `Website has a live primary destination`
- Risk tier: `medium`
- Approval required: `true`
- Intent: launch a basic but credible homepage that explains the service, service area, and call-first conversion path

Suggested payload:

```yaml
page: /
section: homepage_foundation
focus: launch_core_offer_and_local_service_message
```

### 2. Trust block

- Channel: `website`
- Action type: `update_page_section`
- Title: `Review volume is competitive`
- Risk tier: `medium`
- Approval required: `true`
- Intent: add an early trust section that can later house reviews, work photos, and proof signals

Suggested payload:

```yaml
page: /
section: trust_block
assets:
  - Business logo exists on owner phone
  - Work photos exist on owner phone
  - Owner says the team does a really great job and works quickly
```

### 3. Call tracking / CTA system

- Channel: `website`
- Action type: `update_cta`
- Title: `Call tracking is enabled`
- Risk tier: `medium`
- Approval required: `true`
- Intent: make the phone path measurable and obvious

Suggested payload:

```yaml
page: /
cta_type: call_now
phone_number: null
```

### 4. Review proof cadence

- Channel: `social`
- Action type: `schedule_social_post`
- Title: `Reviews channel is active`
- Risk tier: `medium`
- Approval required: `true`
- Intent: create visible proof-of-work content using before/after photos and customer outcomes

Suggested payload:

```yaml
campaign: social_proof
theme: customer_outcomes_and_reviews
review_platform: Google
```

### 5. Local coverage layer

- Channel: `website`
- Action type: `update_page_section`
- Title: `Local SEO channel is active`
- Risk tier: `medium`
- Approval required: `true`
- Intent: establish service-area credibility and local-intent relevance

Suggested payload:

```yaml
page: /service-areas
section: local_coverage
locations:
  - city: Palmetto
    state: FL
  - city: Venice
    state: FL
  - city: Bradenton
    state: FL
  - city: Sarasota
    state: FL
```

### 6. Follow-up sequence

- Channel: `email`
- Action type: `launch_email_sequence`
- Title: `Post-job follow-up sequence is active`
- Risk tier: `medium`
- Approval required: `true`
- Intent: turn one-off jobs into reviews, referrals, and quarterly repeat business

Suggested payload:

```yaml
sequence_type: post_job_follow_up
goals:
  - review_request
  - referral_ask
  - quarterly_repeat_offer
```

### 7. Basic social proof presence

- Channel: `social`
- Action type: `schedule_social_post`
- Title: `Core acquisition channels are active`
- Risk tier: `medium`
- Approval required: `true`
- Intent: make the business look alive and credible even with a very small operator footprint

Suggested payload:

```yaml
campaign: proof_of_presence
theme: local_tips_and_service_proof
cadence: weekly
```

### 8. Call-first hero CTA

- Channel: `website`
- Action type: `update_cta`
- Title: `Primary phone number is available`
- Risk tier: `medium`
- Approval required: `true`
- Intent: move the business from “invisible” to “callable”

Suggested payload:

```yaml
page: /
cta_type: call_now
phone_number: null
```

---

## First 30 Days

This should be run as a compounding sequence of small actions, not one big launch.

### Week 1: Get findable and callable

- publish a one-page website with:
  - service summary
  - service areas
  - call-first CTA
  - logo
  - work photos
- confirm the public phone number to use everywhere
- tighten GBP profile basics:
  - service list
  - categories
  - service areas
  - business description

### Week 2: Start trust compounding

- upload before/after work photos to GBP and social
- create a review-request workflow after every completed job
- publish first 3 social proof posts
- add trust section and “why choose us” language to the site

### Week 3: Start simple repeat and referral systems

- create a post-job follow-up sequence
- ask every happy customer for:
  - Google review
  - referral
  - quarterly repeat booking
- turn the customer list into a basic structured contact list

### Week 4: Add small-budget demand capture

- if the website and GBP basics are live, test a bounded paid-search campaign
- keep the budget extremely tight and local
- focus on:
  - high-intent local terms
  - direct call conversion
  - only the highest-value service area

---

## Why This Should Compound

This business does not need a complicated funnel yet.

It needs:

- a destination
- a phone path
- proof
- reviews
- repeat follow-up
- visible local presence

Those are all small actions. But if run continuously, they compound:

- more visibility -> more calls
- more jobs -> more reviews
- more reviews -> higher trust
- higher trust -> better conversion
- more customers -> more repeat / referral volume

That is the right early-stage growth loop for Andon Window Cleaning.
