# Brand Positioning Playbook

> **Use when:** Defining or refining brand positioning, crafting a value proposition, or differentiating from competitors.

Primary references to check before client-facing work: April Dunford positioning methodology, Forrester B2B buyer messaging cycle, LinkedIn B2B Institute / Ehrenberg-Bass 95-5 rule, Gartner B2B buying journey guidance, 6sense B2B Buyer Experience research, Wynter message testing, and customer interview evidence. Retrieval baseline: 2026-05-17.

---

## The Positioning Stack

```
LAYER 4: TAGLINE / SLOGAN          ← what people remember
LAYER 3: MESSAGING FRAMEWORK       ← what you say at every touchpoint
LAYER 2: VALUE PROPOSITION          ← why you vs alternatives
LAYER 1: POSITIONING STATEMENT      ← the strategic foundation
```

Work bottom-up. Most companies start at Layer 4 (tagline) and wonder why their messaging is inconsistent. Start at Layer 1.

---

## Evidence-Backed Positioning Workflow

Positioning starts with alternatives and customer language, not a clever tagline.

1. **Name the best-fit customer.** Define who gets urgent value, who can buy, who can block, and who should be excluded.
2. **List real alternatives.** Include spreadsheets, agencies, manual process, internal hires, doing nothing, incumbent tools, and "ask AI" substitutes.
3. **Inventory unique capabilities.** Keep only capabilities competitors cannot credibly claim or copy quickly.
4. **Translate capabilities into value.** Tie each capability to a buyer outcome, risk reduction, cost avoidance, revenue path, or workflow relief.
5. **Attach proof.** Use product data, named customer evidence, third-party validation, interviews, demos, screenshots, certifications, or support records.
6. **Mine customer language.** Pull exact phrases from interviews, sales calls, reviews, support tickets, message tests, and community posts.
7. **Choose the category frame.** Pick the market context that makes the value obvious to the best-fit customer.
8. **Test comprehension.** Run a five-second test, message test, sales-call review, or landing-page experiment before scaling.

### Positioning Evidence Ledger

| Field | Requirement |
|-------|-------------|
| `customer_segment` | The segment this claim is for |
| `alternative` | What they would use without this product |
| `unique_capability` | Capability the product can prove |
| `value` | Buyer outcome created by the capability |
| `proof_source` | Interview, call, product data, customer artifact, or third-party source |
| `confidence` | `evidence_backed`, `directional`, or `hypothesis` |

Do not use `hypothesis` positioning as final website, sales, ad, or investor copy without a test plan.

## Layer 1: Positioning Statement

### The Formula

```
For [TARGET CUSTOMER]
who [HAS THIS PROBLEM / NEED]
[PRODUCT] is a [CATEGORY]
that [KEY BENEFIT / DIFFERENTIATION].
Unlike [ALTERNATIVE],
we [UNIQUE DIFFERENTIATOR].
```

### Example

```
For small law firms
who lose clients because calls go to voicemail after hours,
KaiCalls is an AI receptionist
that answers after-hours calls and captures intake details.
Unlike traditional answering-service workflows that can create delay and handoff gaps,
we route intelligently and summarize each call for follow-up.
```

### The 5-Second Test

Your positioning passes if a stranger can answer these 3 questions in 5 seconds:
1. **What is this?** (Category recognition)
2. **Who is it for?** (Target customer)
3. **Why should I care?** (Key benefit)

---

## Layer 2: Value Proposition

### Jobs-to-Be-Done (JTBD) Framework

Don't position on features. Position on the job the customer is hiring you to do.

```
WHEN I [situation/trigger]
I WANT TO [motivation/job]
SO I CAN [desired outcome]
```

**Example:**
```
WHEN I leave the office at 6pm
I WANT TO know every call is being answered professionally
SO I CAN stop worrying about lost clients and enjoy my evening
```

### Value Proposition Canvas

```
┌──────────────────────────┬──────────────────────────┐
│    CUSTOMER PROFILE       │    VALUE MAP              │
├──────────────────────────┼──────────────────────────┤
│ Jobs (what they do):      │ Products/services:        │
│ • Answer client calls     │ • AI receptionist         │
│ • Schedule appointments   │ • Call routing             │
│ • Qualify potential clients│ • 24/7 availability       │
│                          │                           │
│ Pains (frustrations):    │ Pain relievers:           │
│ • Missed calls → lost $  │ • Call summaries          │
│ • Can't afford night staff│ • Lower-cost coverage path│
│ • Answering service sucks │ • No hold time            │
│                          │                           │
│ Gains (desires):         │ Gain creators:            │
│ • Never miss a client    │ • 99.7% answer rate       │
│ • Look professional 24/7 │ • Professional AI voice   │
│ • Focus on legal work    │ • Full CRM integration    │
└──────────────────────────┴──────────────────────────┘
```

---

## Layer 3: Messaging Framework

### The Messaging Matrix

Every touchpoint (website, ads, email, sales calls) should pull from this matrix:

| Audience | Primary Message | Proof Point | CTA |
|----------|---------------|-------------|-----|
| **Office manager** (end user) | "Never miss another client call" | "[observed answer-time or call-log evidence]" | "Start free trial" |
| **Managing partner** (decision maker) | "Stop losing qualified calls to voicemail" | "[client-specific missed-call and close-rate evidence]" | "See ROI calculator" |
| **IT / Operations** (influencer) | "Sets up in 2 minutes, integrates with your PMS" | "Works with Clio, MyCase, PracticePanther" | "View integration docs" |

### Messaging Hierarchy

For every piece of content, choose ONE level:

```
LEVEL 1: CATEGORY MESSAGE (broadest)
  "The AI receptionist for law firms"

LEVEL 2: VALUE MESSAGE (differentiation)
  "Answer after-hours calls and capture intake details"

LEVEL 3: FEATURE MESSAGE (specific)
  "Smart call routing sends personal injury calls to Partner A, family law to Partner B"

LEVEL 4: PROOF MESSAGE (evidence)
  "Acme Law went from 40% missed calls to 0.3% in the first week"
```

**Rule:** Ads use Levels 1-2. Landing pages use Levels 2-3. Sales conversations use Levels 3-4. Do not claim cross-channel consistency lifts unless the source and context are documented.

---

## Layer 4: Competitive Positioning

### The Positioning Map

Plot yourself and competitors on two axes that matter to your customer:

```
                      PREMIUM EXPERIENCE
                            │
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          │  Answering      │  KaiCalls ★     │
          │  Services       │  (AI-assisted,  │
 LOW ─────┤  (human handoff)│   fit-specific) ├───── HIGH
 TECH     │                 │                 │  TECH
          │                 │                 │
          │  Voicemail      │  Big AI         │
          │  (free, missed  │  (expensive,    │
          │   calls)        │   enterprise)   │
          └─────────────────┼─────────────────┘
                            │
                      BASIC EXPERIENCE
```

### Competitive Differentiation Strategies

| Strategy | How | Example |
|----------|-----|---------|
| **Category creation** | Define a new category you own | "AI receptionist" vs "answering service" |
| **Material advantage on one dimension** | Be meaningfully better on one thing customers care about | "Faster after-hours response than voicemail" |
| **Underserved segment** | Own a segment competitors ignore | "Law firms under 20 attorneys" |
| **Price disruption** | Lower-cost path to the same job | "AI receptionist vs staffed after-hours coverage" |
| **Integration moat** | Deep integration with ecosystem | "Built for Clio, MyCase, PracticePanther" |
| **Authenticity** | Real customer stories, transparency | Named case studies, public metrics |

### 2026 Positioning Shift: Third-Party Validation

**The trust problem:** Buyers no longer trust what companies say about themselves. They trust what authoritative sources say about them.

**Implications:**
- Reviews (G2, Capterra, TrustRadius) matter more than marketing copy
- Case studies with named customers beat anonymous testimonials
- Press mentions and analyst reports provide credibility marketing can't buy
- Community/peer recommendations outperform brand messaging
- AI search visibility can be useful discovery evidence, but it is sampled and volatile. Do not equate it to a guaranteed ranking or stable demand source.

## Customer-Language Mining

Use customer language when it is observed, dated, and traceable.

| Source | What To Extract | Risk |
|--------|-----------------|------|
| Sales calls | Trigger events, objections, buying committee language | Seller-led calls can bias wording |
| Customer interviews | Alternatives, stakes, current workaround, decision criteria | Leading questions create false positives |
| Support tickets | Repeated friction and feature confusion | Existing customers may not represent prospects |
| Reviews/community | Competitor complaints and category expectations | Public comments can be non-representative |
| Message tests | Clarity, relevance, trust, missing proof | Panel quality and targeting matter |

Interview prompts should ask about past behavior and concrete examples. Avoid asking whether someone "would buy" a future idea; compliments and hypotheticals are weak evidence.

---

## Brand Voice

### Voice Definition Template

```
BRAND VOICE ATTRIBUTES:
  1. [Attribute 1] but not [anti-pattern]
     Example: "Direct but not harsh"
     We say: "Your calls are going to voicemail. Here's the fix."
     We don't say: "Many businesses face communication challenges..."

  2. [Attribute 2] but not [anti-pattern]
     Example: "Confident but not arrogant"
     We say: "We capture the intake details voicemail loses."
     We don't say: "We believe we may offer a competitive solution..."

  3. [Attribute 3] but not [anti-pattern]
     Example: "Technical but not jargon-heavy"
     We say: "The AI understands context — it routes injury calls to you, billing questions to your admin."
     We don't say: "Our NLP-powered IVR system leverages..."
```

### Voice Consistency Checklist

- [ ] Voice attributes defined (3-5 attributes with anti-patterns)
- [ ] Writing examples for each attribute (do/don't)
- [ ] Voice profile loaded into quality gate (`~/.kai-marketing/voice.md`)
- [ ] All customer-facing copy reviewed against voice attributes
- [ ] Sales team trained on messaging framework
- [ ] Support team uses same voice in responses

---

## Positioning Audit Checklist

- [ ] Can a stranger understand what you do in 5 seconds? (Landing page test)
- [ ] Is your positioning consistent across website, ads, email, and sales? (Cross-channel check)
- [ ] Do you position on outcomes, not features? ("Save 12 hours/week" not "AI-powered")
- [ ] Is your differentiation defensible? (Not just "better UI" which anyone can claim)
- [ ] Does your positioning map correctly against competitors? (Check quarterly)
- [ ] Do customers describe you the way you describe yourself? (Survey/interview)
- [ ] Is the positioning reflected in your pricing? (Premium positioning + low price = confused market)
- [ ] Have you validated the positioning with real customers? (Not just internal consensus)
- [ ] Does every proof claim link to a source, date, and confidence label?
