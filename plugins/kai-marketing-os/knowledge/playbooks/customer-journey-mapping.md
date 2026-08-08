# Customer Journey Mapping Playbook

> **Use when:** Mapping the end-to-end customer experience, identifying drop-off points, designing touchpoint strategies, or aligning marketing/sales/product around the buyer path.

---

## The 6-Stage Journey

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│UNAWARE  │──▶│PROBLEM  │──▶│SOLUTION │──▶│PRODUCT  │──▶│CUSTOMER │──▶│ADVOCATE │
│         │   │AWARE    │   │AWARE    │   │AWARE    │   │         │   │         │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
  "I don't     "I have a     "Solutions    "This product  "I'm using    "I tell
   know I      problem"      exist for     could work"    it and it     others
   have a                    this"                        works"        about it"
   problem"
```

### Stage Details

| Stage | Mindset | Content Needed | Channels | Metric |
|-------|---------|---------------|----------|--------|
| **Unaware** | "Everything's fine" | Pattern-interrupt content that names the problem they can't see | Social, display ads, PR, content | Impressions, reach |
| **Problem Aware** | "I have a problem but don't know what to do" | Educational content: "Why this happens" + "What it costs you" | Blog (SEO), YouTube, podcast, social | Engagement, time on page |
| **Solution Aware** | "There are solutions, let me compare" | Comparison guides, alternatives pages, "how to choose" content | Search (SEO), review sites, ads | Traffic to solution pages, clicks |
| **Product Aware** | "This specific product could work" | Landing pages, demos, case studies, pricing, free trial | Retargeting, email, direct, search (branded) | Signups, demo requests |
| **Customer** | "I'm using it, is it working?" | Onboarding, tutorials, check-ins, success stories | In-app, email, community | Activation, retention, NPS |
| **Advocate** | "I love it, others should know" | Referral programs, review prompts, community, UGC | Email, in-app, social | Referrals, reviews, NPS 9-10 |

---

## Journey Map Template

For each stage, map these 5 dimensions:

```
STAGE: [Name]
═══════════════════════════════════════════

WHAT THEY'RE THINKING:
  "{Internal monologue at this stage}"

WHAT THEY'RE DOING:
  - {Action 1 — e.g., "Googling 'why do I keep missing calls'"}
  - {Action 2 — e.g., "Asking peers in Slack/LinkedIn"}
  - {Action 3 — e.g., "Reading comparison articles"}

TOUCHPOINTS:
  - {Where they encounter us — channel + specific asset}

EMOTIONS:
  Frustration: ████████░░ 8/10
  Confidence:  ███░░░░░░░ 3/10
  Urgency:     █████░░░░░ 5/10

FRICTION / DROP-OFF RISKS:
  - {What causes them to abandon at this stage}
  - {What question goes unanswered}
  - {What competitor captures them}

OUR RESPONSE:
  - Content: {What we create for this stage}
  - Channel: {Where we deliver it}
  - CTA: {What we ask them to do next}
  - Automation: {What triggers automatically}
```

---

## Content-to-Stage Mapping

### What Content Goes Where

| Content Type | Best Stage | Why |
|-------------|-----------|-----|
| Blog post (educational) | Problem Aware | They're searching for answers |
| "Best X" comparison | Solution Aware | They're evaluating options |
| Case study | Product Aware | They need proof it works |
| Landing page | Product Aware | They're ready to evaluate you |
| Demo video | Product Aware | They want to see it in action |
| Free trial | Product Aware → Customer | They need hands-on experience |
| Onboarding email sequence | Customer | They need help getting value |
| Tutorial / how-to | Customer | They're learning the product |
| Review request | Customer → Advocate | They've experienced value |
| Referral program | Advocate | They're ready to spread the word |

### The "Wrong Stage" Problem

The #1 marketing mistake: serving the wrong content at the wrong stage.

```
WRONG: Showing a pricing page ad to someone who doesn't know they have a problem
       (Unaware person gets Product Aware content → bounces)

WRONG: Sending educational blog content to someone ready to buy
       (Product Aware person gets Problem Aware content → goes to competitor)

RIGHT: Match content to stage. Use behavior signals to identify stage.
```

---

## Identifying Customer Stage from Behavior

### Digital Behavior Signals

| Behavior | Likely Stage | Response |
|----------|-------------|----------|
| Arrived from broad keyword search | Problem Aware | Show educational content |
| Arrived from comparison keyword | Solution Aware | Show comparison page |
| Visited pricing page | Product Aware | Retarget with case study + trial offer |
| Started signup / trial | Product Aware → Customer | Trigger onboarding sequence |
| Used product 3+ days | Customer (activated) | Feature education emails |
| Hasn't logged in 14 days | Customer (at risk) | Re-engagement campaign |
| Left a review / referred someone | Advocate | Thank, amplify, reward |

### Lead Scoring by Stage

| Stage | Score Range | Marketing Action |
|-------|------------|-----------------|
| Problem Aware | 0-20 | Nurture with educational content |
| Solution Aware | 21-50 | Targeted content + retargeting |
| Product Aware | 51-80 | Demo offer, trial push, case studies |
| Ready to Buy | 81-100 | Sales outreach or self-serve conversion |

---

## Funnel Diagnostics

### Where Are You Leaking?

For each stage transition, measure the conversion rate:

```
STAGE TRANSITIONS              CONVERSION    BENCHMARK    STATUS
═══════════════════════════════════════════════════════════════════
Unaware → Problem Aware        N/A           N/A          (awareness)
Problem Aware → Solution Aware 15%           10-20%       ✓ OK
Solution Aware → Product Aware 8%            5-15%        ✓ OK
Product Aware → Trial/Signup   3%            2-8%         ✓ OK
Trial → Activated Customer     25%           20-40%       ⚠ LOW
Customer → Retained (month 2)  60%           70-85%       ✗ FIX THIS
Customer → Advocate            5%            10-20%       ⚠ LOW
```

### Fix Priority

Fix the stage with the biggest absolute drop-off first, not the lowest percentage.

```
IF: 10,000 visitors → 300 signups (3%) → 75 activated (25%) → 45 retained (60%)

Improving activation from 25% → 40%:  75 → 120 activated = +45 customers
Improving retention from 60% → 80%:   75 → 60 retained  = +15 customers
Improving conversion from 3% → 5%:    500 → 300 signups  = +200 signups → +50 activated

Answer: Fix conversion first (3% → 5%), then activation, then retention.
It depends on where the volume is.
```

---

## Journey Optimization Checklist

### By Stage

**Unaware → Problem Aware:**
- [ ] Do we have content that names problems our audience doesn't know they have?
- [ ] Are we present where they discover problems? (Social, news, industry events)
- [ ] Is our brand visible before they need us?

**Problem Aware → Solution Aware:**
- [ ] Do we rank for problem-stage keywords? ("Why do law firms miss calls")
- [ ] Does our content bridge from problem to solution naturally?
- [ ] Are we building email list at this stage? (Lead magnets, newsletter)

**Solution Aware → Product Aware:**
- [ ] Do we rank for comparison/alternative keywords?
- [ ] Is there a clear page comparing us to alternatives?
- [ ] Are we retargeting blog readers with product-stage content?

**Product Aware → Customer:**
- [ ] Is the trial/signup friction minimal? (< 2 minutes to value)
- [ ] Does the landing page match the traffic source promise?
- [ ] Is there a clear CTA at every touchpoint?
- [ ] Are we running abandoned-signup recovery emails?

**Customer → Activated:**
- [ ] Is onboarding getting users to the "aha moment" in < 5 minutes?
- [ ] Is there a check-in at day 3 and day 7?
- [ ] Are we tracking and improving time-to-value?

**Customer → Advocate:**
- [ ] Are we asking for reviews/referrals at the right moment?
- [ ] Is there a referral program with clear incentives?
- [ ] Are we making it easy to share (templates, one-click, pre-written)?

---

## Tools for Journey Mapping

| Tool | Best For | Cost |
|------|----------|------|
| **Miro / FigJam** | Visual journey maps, team collaboration | Free tier |
| **GA4 funnel reports** | Quantifying stage-to-stage conversion | Free |
| **Hotjar / Clarity** | Seeing where users drop off on pages | Free tier |
| **Mixpanel / Amplitude** | Event-based journey analysis | Free tier |
| **Customer interviews** | Understanding the "why" behind behavior | Time only |
| **Support ticket analysis** | Finding friction points | Existing tool |
