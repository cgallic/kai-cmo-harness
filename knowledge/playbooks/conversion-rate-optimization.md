# Conversion Rate Optimization (CRO) Playbook

> **Use when:** Improving conversion rates on landing pages, checkout flows, signup forms, or any user action funnel.

---

## CRO Framework

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

| Load Time | Conversion Impact |
|-----------|------------------|
| 0-2 seconds | Baseline |
| 2-3 seconds | -7% conversions |
| 3-5 seconds | -20% conversions |
| 5-8 seconds | -40% conversions |
| 8+ seconds | -50%+ abandonment |

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

### Traffic Source → Conversion Expectation

| Source | Expected CVR | Why |
|--------|-------------|-----|
| Email (warm list) | 5-15% | High intent, knows you |
| Google Search (branded) | 8-20% | Actively looking for you |
| Google Search (non-branded) | 2-5% | Looking for a solution |
| Meta Ads (retargeting) | 3-8% | Already visited |
| Meta Ads (cold) | 0.5-2% | Doesn't know you yet |
| Organic social | 1-3% | Casual interest |
| Referral/partner | 3-8% | Pre-qualified trust |
| Display ads | 0.1-0.5% | Low intent interruption |

**Lesson:** If cold ad traffic converts at 0.5% and you need 2%, the problem might be the traffic source, not the page. Fix the audience before fixing the page.

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

### Pricing Page Best Practices
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

### CTA Best Practices
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

---

## Layer 5: Copy & Messaging

### Headline Formula That Converts

```
[Specific outcome] + [Timeframe] + [Without common objection]

Examples:
  "Get 3x more demo calls in 30 days — without hiring an SDR team"
  "Answer every call in 0.4 seconds — without a single employee"
  "Rank on page 1 in 60 days — without link building"
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

| Traffic/Month | Min Test Duration | Min Sample Per Variant |
|--------------|-------------------|----------------------|
| < 5K visitors | Don't A/B test — make best-judgment changes | — |
| 5K-20K | 2-4 weeks | 1,000+ per variant |
| 20K-100K | 1-2 weeks | 2,500+ per variant |
| 100K+ | 3-7 days | 5,000+ per variant |

**Rules:**
- Never call a test before reaching statistical significance (95% confidence)
- Don't peek at results daily — set the duration upfront and wait
- Test one variable at a time (not headline + CTA + image simultaneously)
- Run the test through a full business week (weekday vs weekend behavior differs)
- Document every test: hypothesis, variant, result, learning

### Test Hypothesis Template

```
We believe that [change]
for [audience segment]
will [expected outcome]
because [reasoning]
We'll measure [metric] over [timeframe]
Success = [specific threshold]
```

---

## CRO Metrics

| Metric | Formula | Benchmark | Great |
|--------|---------|-----------|-------|
| Conversion Rate | Conversions / Visitors | 2-5% | 8%+ |
| Bounce Rate | Single-page visits / Total visits | 40-60% | <35% |
| Exit Rate (key page) | Exits from page / Views of page | 30-50% | <25% |
| Time on Page | Avg time before next action | 1-3 min | 3+ min |
| Scroll Depth | % who scroll to CTA | 50-70% | 80%+ |
| Form Start Rate | Users who start form / Page views | 10-30% | 30%+ |
| Form Completion Rate | Submissions / Form starts | 40-70% | 75%+ |
| Cart Abandonment | Abandoned carts / Total carts | 65-75% | <60% |

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
