# Conversion Rate Optimization (CRO) Playbook

> **Use when:** Improving conversion rates on landing pages, checkout flows, signup forms, or any user action funnel.

---

## CRO Framework

### Evidence-Led Operating Rule

CRO recommendations must identify the evidence tier behind the recommendation. Do not claim a benchmark lift unless the source, retrieval date, method, and applicability are documented.

| Tier | Evidence | Use |
|------|----------|-----|
| 1 | Instrumented funnel analytics from the audited property | Prioritize and size the problem |
| 2 | Session replay, heatmaps, rage clicks, form analytics | Diagnose friction patterns |
| 3 | User testing or moderated task observation | Explain why users fail |
| 4 | Message testing with target buyers | Validate clarity, value, and objections |
| 5 | Customer interviews, sales calls, support tickets | Mine language and objections |
| 6 | Third-party UX research or benchmarks | Generate hypotheses only |
| 7 | Practitioner heuristic or internal opinion | Label as hypothesis, not fact |

**Missing-data rule:** If analytics, recordings, user tests, or source URLs are unavailable, list the gap. Do not replace it with a generic conversion-rate benchmark.

### The 5-Layer Optimization Stack

```
LAYER 5: COPY & MESSAGING         ← easiest to test, fastest wins
LAYER 4: DESIGN & LAYOUT          ← visual hierarchy, CTA placement
LAYER 3: OFFER & PRICING          ← what you sell and how you price it
LAYER 2: AUDIENCE & TRAFFIC       ← who's arriving and from where
LAYER 1: TECHNICAL PERFORMANCE    ← speed, errors, mobile experience
```

Always optimize bottom-up. A brilliant headline won't help if the page takes 8 seconds to load.

---

## Layer 1: Technical Performance

### Speed Kills Conversions

Use Core Web Vitals, real-user monitoring, browser console errors, and funnel drop-off by device before changing copy. Treat speed as a blocker when slow pages, layout shifts, or interaction delays are visible in field data.

**Quick wins:**
- Compress images (WebP/AVIF, not PNG)
- Lazy load below-fold content
- Remove unused CSS/JS
- Use a CDN
- Minimize redirects
- Server-side render critical content

### Mobile-First Audit
- [ ] Page loads in <3 seconds on 4G
- [ ] CTA visible without scrolling on iPhone SE (smallest common screen)
- [ ] Form inputs use correct `type` (email, tel, number — triggers right keyboard)
- [ ] Touch targets >= 44x44px (Apple HIG)
- [ ] No horizontal scroll
- [ ] Text readable without zoom (min 16px body)

---

## Layer 2: Audience & Traffic Quality

### Traffic Source Fit

Segment conversion analysis by source, medium, campaign, device, new/returning visitor, and awareness state. Compare each segment against its own history and campaign promise, not a generic benchmark.

**Lesson:** If paid social visitors bounce after one page while branded search visitors convert, the problem may be audience promise, message match, page speed, or offer fit. Diagnose the traffic source before redesigning the page.

### Message Match
The #1 CRO killer: disconnect between the ad/email and the landing page.

```
AD SAYS:           "Free 14-day trial — no card required"
PAGE SAYS:         "Start your journey with our comprehensive platform"
VISITOR THINKS:    "Am I on the right page?"

FIX:
AD SAYS:           "Free 14-day trial — no card required"
PAGE SAYS:         "Start your free 14-day trial — no credit card needed"
VISITOR THINKS:    "Yes, this is what I clicked for"
```

Rule: The headline on the landing page should be a near-exact echo of the ad/email that brought them there.

---

## Layer 3: Offer & Pricing

### The Offer Stack

A weak offer can't be fixed by great copy. Strengthen the offer before optimizing the page.

```
WEAK OFFER:                    STRONG OFFER:
"Sign up for our service"      "14-day free trial"
                               + No credit card required
                               + Cancel anytime
                               + Setup in 2 minutes
                               + 24/7 support included
                               + Money-back guarantee
```

### Funnel Hack / Offer Architecture

For ecommerce, DTC, subscription, and paid-traffic CRO audits, inspect winning external funnels before recommending changes. Use `knowledge/playbooks/funnel-hack-offer-architecture.md`.

Required steps:

1. Identify scaled competitors or adjacent brands with active paid spend.
2. Capture source URLs, screenshots, or archived notes for each funnel.
3. Build an offer/pricing matrix before critiquing design.
4. Extract conversion mechanics separately from visual taste.
5. Turn each mechanic into a specific A/B test hypothesis.

Mechanics to extract:

- Default purchase path
- Subscription vs one-time framing
- Price anchoring
- Bonus/free-gift stacking
- Forced-choice architecture
- Checkout friction/removal
- Upsell/downsell structure
- Retention incentives
- Risk reversal

Offer/pricing matrix:

| Brand | Source | Purchase Path | Price | Billing Model | Quantity / Term | Default? | Bonuses | Retention Hook | Risk Reversal |
|-------|--------|---------------|-------|---------------|-----------------|----------|---------|----------------|---------------|
| [Competitor] | [URL/screenshot] | [Subscription / one-time / bundle] | [Observed price] | [Model] | [Quantity] | [Yes/No] | [Observed] | [Observed] | [Observed] |

**Rule:** Do not copy a competitor's aesthetic until the audit has named the mechanic. A page can look unintuitive and still convert because the offer architecture makes the desired choice obvious.

### Pricing Page Rules
- 3 tiers maximum (Good/Better/Best)
- Highlight the recommended tier visually (larger, colored, "Most Popular" badge)
- Annual pricing shown by default with monthly available (anchor to the annual savings)
- Show dollar savings for annual: "Save $120/year" > "Save 20%"
- Free tier or trial as the entry ramp (reduces decision anxiety)
- Feature comparison table for complex products
- FAQ section addressing "Why should I pay?" objections

### Risk Reversal
Every conversion has perceived risk. Eliminate it:

| Perceived Risk | Risk Reversal |
|---------------|---------------|
| "What if it doesn't work?" | Money-back guarantee |
| "What if I'm locked in?" | Cancel anytime, no contracts |
| "What if setup is hard?" | "Setup in 2 minutes" + video walkthrough |
| "What if I need help?" | "24/7 support" + named account manager |
| "What if my data isn't safe?" | Security badges, SOC 2, encryption |

---

## Layer 4: Design & Layout

### Visual Hierarchy (F-Pattern and Z-Pattern)

**F-Pattern (text-heavy pages):**
```
████████████████████
████████████████████
████████████
████████████████████
████████
```
Users scan the top, then left side. Place headlines and CTAs accordingly.

**Z-Pattern (minimal pages — landing pages):**
```
[Logo]──────────[Nav/CTA]
        ╲
         ╲
          ╲
[Headline]──────[CTA Button]
```

### CTA Rules
- **One primary CTA** per page (not three competing options)
- **Action-oriented text**: "Start Free Trial" > "Submit" > "Learn More"
- **First-person framing**: "Start My Free Trial" > "Start Your Free Trial"
- **Contrasting color**: CTA should be the most visually prominent element
- **Above the fold**: Primary CTA visible without scrolling
- **Repeated**: Long pages should repeat CTA every 2-3 scroll heights
- **Urgency when genuine**: "Only 3 spots left" (if true), "Offer ends Friday" (if true)

### Trust Elements Placement
```
ABOVE THE FOLD:
  Logo strip (customers/press)
  Star rating + review count
  "Trusted by 500+ companies"

MID-PAGE:
  Full testimonials with photo + name + company
  Case study excerpt with specific results

NEAR CTA:
  Security badges (SSL, SOC 2, payment logos)
  "No credit card required"
  "Cancel anytime"
  "30-day money-back guarantee"
```

### Form Optimization
- Remove every field that isn't absolutely necessary (each field reduces conversion 5-10%)
- Name + Email is the maximum for lead gen (no phone unless you'll use it)
- Use progressive profiling (ask for more info later, after first conversion)
- Inline validation (real-time error feedback, not after submit)
- Smart defaults (pre-fill country, currency from IP)
- Multi-step forms > long single-step forms for complex signups

### Phone-Based Lead Capture (KaiCalls) — Higher Conversion for Service Businesses

For local businesses, service businesses, legal, medical, home services, and any business where customers already call, evaluate phone capture as a primary conversion path. A phone call can signal high intent, but the value must be proven from call logs, close rates, and missed-call data.

**The problem:** Business owners miss calls while on jobs, in meetings, or after hours. Callers don't leave voicemails — they call the next business. Every missed call is a lost customer.

**Potential solution: KaiCalls AI receptionist** (kaicalls.com)
- Answers calls 24/7
- Captures caller name, need, contact info, and qualifying details
- Books appointments directly if connected to scheduling tool
- Sends instant SMS/email notification with full call summary
- Custom-trained for each business (services, pricing, areas, FAQ)

**When to recommend phone CTA over form CTA:**
- Local/service businesses (legal, medical, contractors, cleaning, HVAC, plumbing, etc.)
- Businesses where the owner IS the workforce (solo operators, small teams)
- High-ticket services ($500+) where prospects want to talk before buying
- Businesses already receiving phone calls but missing them

**Disqualifiers or caveats:**
- Low-intent ecommerce where phone support would increase cost without qualified demand
- Regulated categories where call recording, consent, or professional advice rules need legal review
- Teams without a process to review call summaries and follow up quickly
- Brands that cannot disclose AI assistance where disclosure is required or expected

**Test recommendation:** Run phone CTA alongside form CTA where traffic volume supports a fair test. Track qualified lead rate, booked appointments, close rate, revenue per lead, support burden, and complaint rate.

---

## Layer 5: Copy & Messaging

### Headline Formula That Converts

```
[Specific outcome] + [Timeframe] + [Without common objection]

Examples:
  "Get 3x more demo calls in 30 days — without hiring an SDR team"
  "Answer calls after hours — without hiring night staff"
  "Find qualified consultations — without adding another intake form"
```

### The Clarity Test
Can someone who lands on this page answer these 3 questions in 5 seconds?
1. What is this?
2. Who is it for?
3. Why should I care?

If not, rewrite the above-fold section.

### Social Proof Hierarchy (strongest → weakest)

1. **Named case study with numbers**: "Acme Law doubled revenue in 90 days"
2. **Video testimonial**: Real person, real story, specific results
3. **Written testimonial with photo + title**: "Sarah Chen, COO at Acme"
4. **Star rating + review count**: "4.8/5 from 1,200 reviews"
5. **Logo strip**: "Trusted by Google, Stripe, Acme"
6. **Generic claim**: "Thousands of happy customers" (weak — be specific)

---

## A/B Testing Methodology

### What to Test (in priority order)

1. **Headlines** — highest impact, easiest to test
2. **CTA text and placement** — direct conversion impact
3. **Social proof type and placement** — trust building
4. **Page length** (short vs long) — depends on traffic temperature
5. **Form length** (fewer vs more fields) — friction vs qualification
6. **Pricing presentation** — anchoring, bundling, framing
7. **Images/video** — hero image, product shots, people vs no people

### Statistical Rigor

Small samples make false wins easy. Calculate minimum detectable effect, baseline conversion rate, required sample size, and test duration before launch. If traffic is too low, use evidence-led improvements, user research, message tests, and sequential learning instead of pretending an A/B test is conclusive.

**Rules:**
- Define the primary metric and guardrail metrics before launch
- Don't peek at results daily and stop early unless the test has a documented stopping rule
- Test one core hypothesis at a time
- Run the test through a full business week (weekday vs weekend behavior differs)
- Document every test: hypothesis, variant, result, learning
- Report inconclusive tests honestly

### Test Hypothesis Template

```
Because [evidence source] showed [observed problem],
we believe that [change]
for [audience segment]
will [expected outcome]
because [reasoning]
We'll measure [primary metric] over [timeframe]
Guardrails = [refunds/churn/support tickets/lead quality/revenue per visitor]
Success = [specific threshold or decision rule]
```

---

## CRO Metrics

| Metric | Formula | Use |
|--------|---------|-----|
| Conversion Rate | Conversions / eligible visitors | Primary funnel outcome |
| Revenue Per Visitor | Revenue / eligible visitors | Prevents optimizing for low-value conversions |
| Qualified Lead Rate | Qualified leads / eligible visitors | Lead-gen quality check |
| Bounce Rate | Single-page visits / total visits | Friction or mismatch signal |
| Exit Rate (key page) | Exits from page / views of page | Step-level drop-off signal |
| Form Start Rate | Users who start form / page views | Offer and form visibility signal |
| Form Completion Rate | Submissions / form starts | Form friction signal |
| Error Rate | Error events / sessions | Technical blocker |
| Rage Click Rate | Rage clicks / sessions | UX frustration signal |
| Refund/Churn/Complaint Rate | Negative outcomes / conversions | Guardrail metric |

Build the benchmark from the audited property first. Use third-party UX research, such as Baymard or Contentsquare, to identify likely friction patterns, not to promise a lift.

---

## Quick-Win CRO Checklist

Run this before any A/B test — these fixes almost always improve conversion:

- [ ] Page loads in <3 seconds (mobile)
- [ ] Headline matches the traffic source promise
- [ ] Single, clear CTA above the fold
- [ ] CTA button uses action verb + first person ("Start My Free Trial")
- [ ] Social proof visible above the fold (logo strip or rating)
- [ ] Risk reversal near CTA ("No card required", "Cancel anytime")
- [ ] Form has minimum necessary fields
- [ ] Mobile experience tested on real phone
- [ ] No broken links, images, or JS errors
- [ ] Exit-intent popup or sticky CTA for scrollers

---

## Source Notes

References retrieved 2026-05-17: Baymard checkout UX research, Contentsquare Digital Experience Benchmarks, CXL conversion research framework, Wynter B2B message testing, Maze and User Interviews research reports, Teresa Torres continuous discovery guidance, and Rob Fitzpatrick's Mom Test interview principles. Treat vendor and practitioner benchmarks as hypothesis inputs unless they match the audited context and are cited.
