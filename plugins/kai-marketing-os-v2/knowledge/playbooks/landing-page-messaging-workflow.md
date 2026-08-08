# Landing Page Messaging Workflow

> **Use when:** Creating or optimizing landing pages for any client. This workflow systematically tests messaging against personas using Perception Engineering to find copy that converts.

## Overview

This is a 7-phase workflow that takes you from AI-powered persona research to tested, winning landing page copy deployed via Facebook Ads. Each phase builds on the previous.

**Time to complete:** 3-5 hours for full analysis + copy generation + ad setup

**Deliverables:**
- AI-researched persona profiles with real market data
- Cached prediction analysis
- Test matrix (headlines, subheadlines, CTAs)
- 3-4 landing page variants
- HTML prototype
- Facebook/Meta ad creatives
- Winning messaging synthesis

---

## Phase 0: AI-Powered Persona Research

### Objective
Use AI tools to gather REAL persona data from the market before creating landing page copy.

### Research Sources (Use AI to Analyze)

| Source | What to Extract | AI Tool |
|--------|-----------------|---------|
| **Reddit** | Pain points in r/[industry] threads | WebSearch + WebFetch |
| **Twitter/X** | Complaints, wishes, reactions to competitors | WebSearch |
| **G2/Capterra Reviews** | What users love/hate about competitors | WebFetch |
| **YouTube Comments** | Questions under tutorial videos | WebFetch |
| **Quora** | Questions people ask about the problem | WebSearch |
| **Amazon Reviews** | For physical product adjacents | WebFetch |
| **Facebook Groups** | Community discussions | Manual or API |
| **LinkedIn Posts** | B2B pain points and discussions | WebSearch |

### Research Prompts

**Pain Point Discovery:**
```
Search: "[product category] frustrated" OR "[product category] hate" OR "[product category] problem" site:reddit.com
```

**Competitor Sentiment:**
```
Search: "[competitor name] review" OR "[competitor name] alternative" OR "switched from [competitor]"
```

**Wish List Discovery:**
```
Search: "[product category] wish" OR "[product category] should" OR "why doesn't [product category]"
```

**Objection Mining:**
```
Search: "[product category] scam" OR "[product category] worth it" OR "[product category] vs"
```

### AI Research Workflow

1. **Run 5-10 searches** using WebSearch for each research type
2. **Fetch top results** using WebFetch to extract verbatim quotes
3. **Compile pain points** - exact language people use
4. **Identify patterns** - recurring themes across sources
5. **Extract objections** - what stops people from buying
6. **Find desires** - what they wish existed

### Output Format

```markdown
## AI Persona Research: [Client Name]

### Pain Point Evidence
| Source | Verbatim Quote | Frequency |
|--------|---------------|-----------|
| Reddit | "[exact quote]" | 12 mentions |

### Objection Evidence
| Objection | Source | Quote |
|-----------|--------|-------|
| "Too expensive" | G2 Review | "[exact quote]" |

### Desire Evidence
| Desire | Source | Quote |
|--------|--------|-------|
| "I wish it could..." | Twitter | "[exact quote]" |

### Language Patterns
- Words they use: [list]
- Phrases that resonate: [list]
- Emotional triggers: [list]
```

### Why This Matters

**Without AI research:** You guess at pain points
**With AI research:** You use their exact words → 2-3x higher conversion

---

## Phase 1: Persona Extraction

### Objective
Synthesize AI research into 3-4 distinct buyer personas with REAL pain points from actual market data.

### Process

1. **Synthesize AI research data:**
   - Group pain points by persona type
   - Match objections to persona segments
   - Extract exact language for each persona

2. **Supplement with existing data:**
   - Client interviews / founder notes
   - Customer support tickets
   - Social media comments (Twitter, Discord, Reddit)
   - Competitor reviews
   - Sales call recordings

2. **For each persona, document:**

```markdown
## Persona: [Name]

**Profile:** [One-line description]
**Volume/Value:** [Transaction size, LTV, or equivalent]
**Audience Size:** [Followers, reach, or equivalent]

### Demographics
- Age range
- Professional status
- Platform behavior
- Current tools/solutions

### Pain Points
| Pain | Emotional Impact | Business Impact |
|------|------------------|-----------------|
| [Specific problem] | [How it makes them feel] | [Measurable consequence] |

### Goals
- [What they want to achieve]
- [What success looks like]

### Decision Process
- **Discovery:** How they find solutions
- **Evaluation:** How they assess options
- **Conversion Trigger:** What makes them act
- **Objections:** What stops them

### Hook
> "[Single sentence that would stop them scrolling]"

### Messaging Angle
[2-3 sentences on what to emphasize for this persona]
```

3. **Create persona summary matrix:**

| Persona | Core Pain | Primary Value | Volume | Monetization Intent |
|---------|-----------|---------------|--------|---------------------|
| [Name] | [Pain] | [What they get] | [Size] | [High/Medium/Low] |

### Template File
Save to: `clients/{client}/outputs/target-personas.md`

---

## Phase 2: Cached Prediction Analysis

### Objective
Identify the subconscious belief blocking each persona from converting. This is the core of Perception Engineering.

### The Framework

Every prospect has a **cached prediction** - a mental shortcut that governs behavior:
- "I don't need another tool"
- "This is probably a scam"
- "I'm already doing fine"

They also have a **legitimizing label** - a virtue they use to justify inaction:
- "I'm being careful" (caution = wisdom)
- "I prefer to stay in control" (control = competence)
- "I keep things simple" (simplicity = intelligence)

### Process

For each persona, complete this analysis:

```markdown
## [Persona Name] - Cached Prediction Analysis

**Cached Prediction:**
"[What they believe that stops them from acting]"

**Legitimizing Label:**
"[The virtue they claim]" ([virtue] = [positive trait])

**Actual Reality:**
[What's really happening - the cost of their inaction]

**Destabilization Statement:**
"[Statement that re-indexes their virtue as a vice]"
```

### Example

```markdown
## Crypto Influencer - Cached Prediction Analysis

**Cached Prediction:**
"Sharing my actual positions will expose me. Copy trading platforms are scammy."

**Legitimizing Label:**
"I'm protecting my reputation" (Caution = Wisdom)

**Actual Reality:**
Can't monetize calls. Credibility constantly questioned. Same DMs 100x/day.

**Destabilization Statement:**
"You tell yourself you're protecting your reputation. In reality, you're leaving money on the table while your followers guess at your actual positions."
```

### Template File
Add to: `clients/{client}/outputs/target-personas.md` (append to persona definitions)

---

## Phase 3: Headline Generation

### Objective
Generate 10+ headlines using different destabilization tactics.

### Headline Types

| Type | Pattern | Example |
|------|---------|---------|
| **Re-indexing** | Turn their virtue into a vice | "You're not being careful. You're being blind." |
| **Behavior Attack** | Name their current action as wrong | "Stop screenshot-ing your PnL." |
| **Chaos Recognition** | Name their messy reality | "30 tokens. Zero clarity." |
| **Fear Anchor** | Name what they're afraid of | "FTX. Celsius. Copy trading." |
| **Opportunity Framing** | Show what they're missing | "Turn your chaos into a product." |
| **Status Positioning** | Compare to aspirational group | "The traders you follow post calls. We post results." |
| **Uncertainty Attack** | Create doubt in current belief | "Your AI thesis is up 40%. Or is it?" |
| **Question Hook** | Ask what they secretly wonder | "What if your skill had leverage beyond your own capital?" |
| **Aspiration Unlock** | Show the future state | "Your trading finally has receipts." |
| **Social Proof** | Reference others' success | "234 traders stopped guessing." |

### Process

1. Generate 2-3 headlines per type
2. Tag each with target persona
3. Score for memorability (1-4)
4. Select top 10 for testing

### Headline Matrix Template

| ID | Headline | Target Persona | Type | Memorability |
|----|----------|----------------|------|--------------|
| H1 | [Headline] | [Persona] | [Type] | [1-4] |

### Template File
Save to: `clients/{client}/outputs/landing-page-test-matrix.md`

---

## Phase 4: Subheadline & CTA Generation

### Objective
Create subheadlines (context shifts) and CTAs (permission mechanisms) that pair with headlines.

### Subheadline Types (Context Shifts)

| Shift | Before → After | Example |
|-------|----------------|---------|
| **Data-Driven** | Guessing → Measuring | "See what's actually working." |
| **Proof Culture** | Hidden → Visible | "All on-chain. All verifiable." |
| **Identity Shift** | User → Creator | "Build a track record. Earn fees." |
| **Safety First** | Risk → Security | "Self-custody. Your keys." |
| **Simplicity** | Complex → Easy | "One dashboard. Full clarity." |

### CTA Types (Permission Mechanisms)

| Type | Mechanism | Example |
|------|-----------|---------|
| **Low Commitment** | Minimize perceived effort | "Create Your First Stack" |
| **Zero Commitment** | Just looking | "See How It Works" |
| **Social Proof Entry** | Follow others first | "Browse Top Stacks" |
| **Self-Interest** | Calculate benefit | "Calculate Your Earnings" |
| **Trivial Cost** | Minimize investment | "Start With $1" |
| **Procedural** | Step-by-step | "Connect Wallet → Start" |
| **FOMO** | Join the crowd | "Join 234 Traders" |

### Process

1. Generate 6+ subheadlines
2. Generate 6+ CTAs
3. Map which headlines pair best with which subheadlines
4. Map which CTAs work for which persona intent level

### Combination Matrix Template

| Combo ID | Headline | Subheadline | CTA | Target Persona | Four U's Score |
|----------|----------|-------------|-----|----------------|----------------|
| C1 | H1 | S1 | CTA1 | [Persona] | [/16] |

---

## Phase 5: Landing Page Variants

### Objective
Create 3-4 complete landing page wireframes, each optimized for a different entry angle.

### Recommended Variants

1. **Trust Anchor** - Lead with fear of alternatives, position as safe solution
2. **Monetization** - Lead with revenue opportunity
3. **Proof/Credibility** - Lead with verification, attack fake claims
4. **Simplifier** - Lead with organization, reduce chaos

### Page Section Blueprint

Each landing page should follow this structure:

```
1. HERO (Above the fold)
   - Headline (destabilizer)
   - Subheadline (context shift + safety)
   - Primary CTA + Secondary CTA
   - Social proof stats

2. PROBLEM (Agitation)
   - Name 3-4 specific pains
   - Attack alternatives
   - Create urgency through recognition

3. SOLUTION (Product Introduction)
   - 3 core value props (icons + copy)
   - Key differentiator statement

4. HOW IT WORKS
   - 3-4 simple steps
   - Time framing ("Live in 5 minutes")
   - CTA after

5. SOCIAL PROOF
   - Testimonials (1 per persona type)
   - Stats reinforcement

6. MONETIZATION / CALCULATOR (if applicable)
   - Interactive calculator
   - Specific numbers

7. OBJECTION HANDLING
   - FAQ accordion
   - Direct, confident answers

8. FINAL CTA
   - Repeat headline theme
   - Both CTAs
   - Permission statement ("Start with $1")
```

### Template File
Save each variant to: `clients/{client}/outputs/landing-page-v{N}-{name}.md`

---

## Phase 6: Scoring & Synthesis

### Objective
Identify the winning combination and create final deliverables.

### Four U's Scoring

Score each combination 1-4 on each dimension:

| U | Question | 1 | 2 | 3 | 4 |
|---|----------|---|---|---|---|
| **Unique** | Can only THIS product claim this? | Generic | Somewhat | Mostly | Only us |
| **Useful** | Can reader take immediate action? | Vague | Some action | Clear action | Urgent action |
| **Ultra-specific** | Numbers, examples, specifics? | None | Few | Several | Many |
| **Urgent** | Reason to act today? | None | Weak | Moderate | Strong |

**Target: 12+/16**

### Perception Engineering Scoring

| Layer | Tactic Present? | Score |
|-------|-----------------|-------|
| **Perception** | Destabilizes cached belief | 0-3 |
| **Context** | Shifts what feels allowed | 0-3 |
| **Permission** | Removes imagined consequences | 0-3 |

**Target: 7+/9**

### Final Synthesis Document

Create a `WINNING-MESSAGING-FINAL.md` that includes:

1. **The Winning Hero** (headline + subheadline + CTA)
2. **Persona-Specific Hooks** (one for each persona)
3. **Value Props Ranked by Impact**
4. **CTAs Ranked by Conversion Potential**
5. **Objection Handling Table**
6. **The Conversion Formula** (step-by-step psychology)
7. **Traffic Source Mapping** (which version for which channel)
8. **A/B Test Priority** (what to test first)

---

## File Structure

After completing this workflow, the client folder should contain:

```
clients/{client}/outputs/
├── target-personas.md              # Phase 1-2
├── landing-page-test-matrix.md     # Phase 3-4
├── landing-page-v1-trust-anchor.md # Phase 5
├── landing-page-v2-monetization.md # Phase 5
├── landing-page-v3-proof.md        # Phase 5
├── landing-page-v4-simplifier.md   # Phase 5
├── landing-page-prototype.html     # Phase 5 (optional)
└── WINNING-MESSAGING-FINAL.md      # Phase 6
```

---

## Quick Reference: The Psychology

### Why People Don't Convert

1. **Cached Prediction:** "I already have a solution" (even if it's bad)
2. **Legitimizing Label:** "I'm being smart by waiting" (virtue protects inaction)
3. **Fear of Change:** "What if this is worse?" (status quo bias)
4. **Trust Deficit:** "How do I know this works?" (skepticism)

### How to Break Through

1. **Destabilize:** Name their virtue as a vice
2. **Shift Context:** Change what feels normal/allowed
3. **Grant Permission:** Remove imagined consequences
4. **Create Urgency:** Show cost of inaction

### The One Sentence That Converts

```
"You think you're [virtue]. You're actually [vice]. Here's the fix. [Specific benefit]. [Safety assurance]. [Low-friction CTA]."
```

---

## Example: Applying to New Client

### Input Required
- Product description (what it does)
- Target audience (who buys)
- Competitors (what they're switching from)
- Key differentiator (why this is different)
- Pricing (what it costs)

### Prompt Template

```
I need to create landing page messaging for [CLIENT].

**Product:** [What it does]
**Audience:** [Who buys]
**Competitors:** [Alternatives]
**Differentiator:** [Why us]
**Pricing:** [Cost]

Please run the full landing page messaging workflow:
1. Extract 3-4 personas with cached predictions
2. Generate headline/subhead/CTA test matrix
3. Create 3-4 landing page variants
4. Score and synthesize winning messaging
5. Deliver HTML prototype
```

---

## Phase 7: Facebook/Meta Ads Testing

### Objective
Deploy winning messaging through Facebook Ads to validate conversion in real traffic.

### Ad Creative Matrix

For each landing page variant, create matching ad creatives:

| Ad Type | Format | Best For |
|---------|--------|----------|
| **Primary Text Ad** | Image + copy | Cold traffic testing |
| **Carousel** | Multi-image story | Feature showcase |
| **Video (UGC style)** | 15-30 sec | Warm audiences |
| **Collection** | Product showcase | E-commerce |

### Ad Copy Structure

Each ad should follow the landing page's Perception Engineering:

```
[HOOK - Destabilizer from headline]

[AGITATE - 1-2 sentences on pain]

[SOLUTION - What the product does]

[CTA - Match landing page CTA]
```

### Ad Copy Templates by Variant

**Trust Anchor Ad:**
```
FTX. Celsius. Copy trading.

What do they have in common?
Someone else held your keys.

[Product] is different:
✓ Self-custody (you control funds)
✓ On-chain transparency
✓ No middleman risk

[CTA: See How It Works]
```

**Monetization Ad:**
```
You're already [doing the activity].
Why aren't you getting paid for it?

[Product] turns your [skill] into income:
→ Create [thing]
→ Share with audience
→ Earn up to X% on [metric]

[CTA: Calculate Your Earnings]
```

**Proof/Credibility Ad:**
```
"Fake [claim]" accusations are exhausting.

What if you could just... prove it?

[Product] puts your [metric] on-chain:
• Verifiable by anyone
• Permanent track record
• No more screenshots

[CTA: Start Proving It]
```

**Simplifier Ad:**
```
30 [items]. Zero clarity.
Sound familiar?

[Product] organizes your [thing]:
📊 See what's working
📁 Group by [category]
🎯 Make informed decisions

[CTA: Get Organized]
```

### Campaign Structure

```
Campaign: [Client] - Landing Page Test
├── Ad Set 1: Interests (Cold)
│   ├── Trust Anchor creative
│   ├── Monetization creative
│   └── Proof creative
├── Ad Set 2: Lookalikes
│   ├── Trust Anchor creative
│   ├── Monetization creative
│   └── Proof creative
└── Ad Set 3: Retargeting (Warm)
    └── Monetization creative (highest intent)
```

### Budget Allocation

| Phase | Daily Budget | Duration | Goal |
|-------|-------------|----------|------|
| **Learning** | $20-50/day | 3-5 days | Find winning creative |
| **Scaling** | $50-200/day | 7-14 days | Optimize CPL/CPA |
| **Maintenance** | Variable | Ongoing | Sustain performance |

### Key Metrics to Track

| Metric | Target | What It Tells You |
|--------|--------|-------------------|
| CTR | >1.5% | Hook is working |
| CPC | <$1-3 | Targeting is efficient |
| Landing Page CVR | >3% | Messaging resonates |
| CPL/CPA | Industry benchmark | Overall funnel health |
| Scroll Depth | >60% to CTA | Content is engaging |

### A/B Test Protocol

**Week 1: Creative Test**
- Run all ad variants with same audience
- Winner = lowest CPA or highest CVR
- Kill losers after 1000 impressions each

**Week 2: Audience Test**
- Take winning creative
- Test across 3-4 audience segments
- Winner = lowest CPA at scale

**Week 3: Landing Page Test**
- Take winning creative + audience
- Split traffic to 2-3 landing page variants
- Winner = highest conversion rate

### Andromeda Optimization Tips

Reference: `frameworks/meta-advertising/meta-andromeda-deep-dive.md`

1. **Broad targeting** - Let Andromeda find your audience
2. **Advantage+ placements** - Don't restrict placements
3. **Multiple creatives** - 3-6 per ad set minimum
4. **Value-based optimization** - If possible, optimize for purchase value not just conversions
5. **Creative refresh** - New creatives every 2-3 weeks

### Output Files

```
clients/{client}/outputs/
├── fb-ad-copy-trust-anchor.md
├── fb-ad-copy-monetization.md
├── fb-ad-copy-proof.md
├── fb-ad-copy-simplifier.md
└── fb-campaign-structure.md
```

---

## File Structure (Complete)

After completing all phases, the client folder should contain:

```
clients/{client}/outputs/
├── persona-research-ai.md           # Phase 0
├── target-personas.md               # Phase 1-2
├── landing-page-test-matrix.md      # Phase 3-4
├── landing-page-v1-trust-anchor.md  # Phase 5
├── landing-page-v2-monetization.md  # Phase 5
├── landing-page-v3-proof.md         # Phase 5
├── landing-page-v4-simplifier.md    # Phase 5
├── landing-page-prototype.html      # Phase 5 (optional)
├── WINNING-MESSAGING-FINAL.md       # Phase 6
├── fb-ad-copy-trust-anchor.md       # Phase 7
├── fb-ad-copy-monetization.md       # Phase 7
├── fb-ad-copy-proof.md              # Phase 7
├── fb-ad-copy-simplifier.md         # Phase 7
└── fb-campaign-structure.md         # Phase 7
```

---

## Quick Start Prompt

Copy this to start the workflow for any client:

```
Run the full Landing Page Messaging Workflow for [CLIENT]:

**Product:** [What it does in 1-2 sentences]
**Target Audience:** [Who buys - be specific]
**Competitors:** [Top 3 alternatives they'd consider]
**Key Differentiator:** [Why choose this over alternatives]
**Pricing:** [Cost or pricing model]
**Current Traffic:** [Where traffic comes from now]
**Budget:** [Monthly ad spend available]

Execute all 7 phases:
0. AI-powered persona research (WebSearch + WebFetch)
1. Persona extraction with cached predictions
2. Headline/subhead/CTA test matrix
3-4. Create 4 landing page variants
5. Score and synthesize winning messaging
6. Create Facebook ad copy for each variant
7. Build campaign structure

Deliver all output files to clients/[client]/outputs/
```

---

## Related Frameworks

| Framework | When to Use |
|-----------|-------------|
| `frameworks/content-copywriting/perception-engineering.md` | Deep persuasion psychology |
| `frameworks/content-copywriting/four-us-framework.md` | Content quality scoring |
| `frameworks/content-copywriting/headline-formulas.md` | Additional headline patterns |
| `frameworks/meta-advertising/meta-andromeda-deep-dive.md` | Facebook ad optimization |
| `frameworks/meta-advertising/meta-gem-deep-dive.md` | Creative optimization |
| `channels/meta-advertising.md` | Meta ads channel guide |
| `checklists/meta-advertising-checklist.md` | Ad launch checklist |
| `checklists/content-checklist.md` | Final copy validation |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-13 | Initial version created from Indexify landing page project |
| 2026-01-13 | Added Phase 0 (AI-powered persona research) and Phase 7 (Facebook Ads testing) |

