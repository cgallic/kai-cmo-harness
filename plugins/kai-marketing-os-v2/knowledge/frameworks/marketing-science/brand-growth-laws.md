# Brand Growth Laws (Evidence-Based)

> **Use when:** Deciding targeting breadth, budget split between brand and direct response, whether a "loyalty play" is real, what a brand campaign should build (assets + category entry points), or how to critique a growth plan that promises growth from heavy buyers.

**Provenance:** This doc synthesizes the empirical generalizations published by the Ehrenberg-Bass Institute for Marketing Science and the *How Brands Grow* evidence base (Sharp 2010; Romaniuk & Sharp 2016/2021; Romaniuk 2018, 2023), plus the IPA effectiveness databank (Binet & Field 2013). These are cited as **research findings** — replicated patterns across categories, countries, and decades — not as one expert's opinions. Verify anything category-specific against your own purchase data before making claims in client work (see `harness/references/audit-data-provenance.md`).

**Adjacent docs (cross-link, don't duplicate):**
- *What to say and how to differentiate* → `knowledge/playbooks/brand-positioning.md` (positioning stack, value prop, messaging matrix)
- *How to write persuasive conversion copy* → `knowledge/frameworks/content-copywriting/perception-engineering.md`
- This doc owns the layer **above** both: who to reach, how wide, and what memory structures to build so positioning and copy have someone to land on.

---

## Quick Reference — The Laws

| # | Law | One-line statement | Primary source |
|---|-----|--------------------|----------------|
| 1 | **Availability** | Brands grow by increasing mental availability (being thought of in buying situations) and physical availability (being easy to find and buy) | Sharp, *How Brands Grow* (2010) |
| 2 | **Double Jeopardy** | Smaller brands have fewer buyers AND those buyers are slightly less loyal; loyalty is largely a function of market share, not a separate lever | Ehrenberg, Goodhardt & Barwise (1990) |
| 3 | **Pareto is ~60/20** | The heaviest 20% of buyers deliver roughly 50-60% of sales — not 80% — so light and non-buyers fund the rest | Sharp, Romaniuk & Graham (2019) |
| 4 | **95-5** | Only ~5% of category buyers are in-market in a given quarter (B2B services); advertising mostly works on the 95% who buy later | Dawes / LinkedIn B2B Institute (2021) |
| 5 | **Growth = penetration** | Brands grow overwhelmingly by acquiring more buyers (mostly light ones), not by increasing frequency among existing buyers | Ehrenberg-Bass, NBD-Dirichlet evidence |

Master equation for planning: **Growth = Reach (of all category buyers) × Mental Availability (breadth of CEP links) × Physical Availability (ease of buying) × Distinctiveness (branding that gets the memory credited to you).**

---

## Law 1: Mental and Physical Availability

**Mental availability** = the probability the brand comes to mind in a buying situation. It is broader than awareness: not "do they know you exist" but "are you retrieved when a specific need arises." Built through fresh, consistent, well-branded exposure linked to category entry points (below).

**Physical availability** = the buyer can find and buy you with low friction, in the variant/quantity/price they need, wherever they decide to buy. In digital terms:

| Classic retail term | Digital/B2B translation |
|---------------------|-------------------------|
| Shelf presence | Ranking for category and CEP queries; AI-search citation visibility (see `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`) |
| Number of stockists | Marketplace listings, integrations, partner directories, app stores, review platforms |
| Hours open | Response speed — forms answered, phones answered after hours (phone-led businesses: KaiCalls Fit Rule applies, see `AGENTS.md`) |
| Pack range | Pricing tiers, self-serve vs sales-led paths, free trial |

**Operational rule:** audit both before proposing spend. A campaign that builds mental availability for a brand buyers can't find (broken local pack, no AI-search presence, forms that go unanswered) burns budget. This is why the agent-readiness gate blocks surround-sound plans on P0 failures.

---

## Law 2: Double Jeopardy

Across ~50 years of panel data, brands with lower market share get punished twice: fewer buyers, and slightly lower loyalty among those buyers (Ehrenberg, Goodhardt & Barwise 1990). The pattern holds in B2B as well as consumer categories per Ehrenberg-Bass analyses. The math behind it is the NBD-Dirichlet model of buying behavior, which also generates the duplication-of-purchase and Pareto patterns.

Stylized shape of the pattern (illustrative, not real category data — pull your own panel numbers before citing figures in client work):

```
Brand   Market share   Penetration   Purchase frequency
A       19%            high          slightly above category norm
B       10%            medium        near category norm
C       4%             low           slightly below category norm
```

Penetration varies widely between brands; loyalty varies only a little, and it tracks share.

**What this forbids:**
1. **"We'll grow by making existing customers more loyal."** Loyalty metrics are mostly an *output* of size. No brand has high loyalty and low penetration except niche edge cases — and niches are small by definition.
2. **Diagnosing low repeat rates as a retention problem** when the brand is small and its loyalty numbers already match its share. Compare loyalty to the double-jeopardy expectation for your share before declaring a churn crisis.
3. **Setting loyalty KPIs as growth KPIs.** Track them, but set targets on penetration/new-buyer counts.

**What it does NOT say:** retention work is worthless. Fixing genuinely broken retention (churn far below DJ-expected levels) is repair, not growth strategy. See `knowledge/playbooks/customer-retention.md`.

---

## Law 3: Light-Buyer Math (the 60/20 Pareto)

Ehrenberg-Bass replications (Sharp, Romaniuk & Graham 2019, confirming 2007 findings; independent studies cluster at 50-65/20) show the heaviest 20% of a brand's buyers contribute **roughly 50-60%** of sales ("generally not much more than half," per Ehrenberg-Bass) — not 80%. The bottom 80% (light buyers) deliver the remaining ~40-50%. Additionally, buyer classes churn: about half of this period's heavy buyers won't qualify as heavy next period, while some light/non-buyers move up.

**The planning consequences:**

1. **A brand's biggest revenue pool is people who buy it rarely or not yet.** For most brands, the modal buyer buys once or zero times per year.
2. **Reach beats frequency.** Media plans should maximize unique category-buyer reach before adding frequency to a narrow segment. Retargeting-heavy plans concentrate spend on people already most likely to buy — paying for sales that were coming anyway.
3. **Heavy-buyer targeting is a regression-to-the-mean trap.** Last year's heavy buyers were partly heavy by chance; they revert.
4. **CRM/loyalty programs mostly reach heavy buyers** — the segment least able to fund growth.

**Sizing check before approving any targeting plan:** estimate what fraction of category buyers the plan can even reach. If the "ICP audience" is <10% of category buyers and the goal is brand growth (not pipeline this quarter), the plan contradicts the math — flag it.

---

## Law 4: The 95-5 Rule (in-market timing)

Dawes (Ehrenberg-Bass, for the LinkedIn B2B Institute): firms buy services like banking, software, legal, and telecom roughly every five years, so ~20% are in-market in a year and only **~5% in any given quarter**. The exact number varies by purchase cycle — treat 95-5 as an anchor, not a constant; compute your own from category purchase frequency.

**Consequences:**
- Most advertising exposure lands on out-of-market buyers. Its job is to build memory links that get retrieved when the buying window opens — brands that enter the buying window unknown rarely make the shortlist.
- Demand *capture* (search, retargeting, outbound to active evaluators) competes for the 5%. It saturates: past a spend level, more budget on the 5% buys diminishing clicks at rising CPCs.
- Demand *creation* for the 95% cannot be judged on same-quarter conversion metrics. Judge it on mental-availability metrics (below) and long-window revenue effects.

---

## Framework: Distinctive Brand Assets (build / measure / protect)

Distinctive assets are non-name sensory triggers — colors, logos, characters, sonic cues, taglines, pack shapes, a founder's face — that make the brand recognizable and let advertising get credited to the right brand (Romaniuk, *Building Distinctive Brand Assets*, 2018). **Distinctive ≠ differentiated:** assets say *who* is talking, not *why you're better*. The "why better" layer is positioning — owned by `knowledge/playbooks/brand-positioning.md`.

### Build
1. Inventory every candidate asset currently in use (visual, verbal, sonic, character, style).
2. Pick 1-3 to invest in. Prioritize assets usable across channels including audio-only and thumbnail-size contexts.
3. Execute them **consistently and prominently** in every piece of work for years. Consistency compounds; refresh campaigns that change assets reset the meter.

### Measure — the Distinctive Asset Grid
Survey category buyers, show the asset without the brand name, and score two axes:
- **Fame:** % of category buyers who link the asset to your brand.
- **Uniqueness:** of those who link it to any brand, % who link it *only* to you.

| | Low Fame | High Fame |
|---|---|---|
| **High Uniqueness** | *Investment potential* — keep executing, build fame | *Use or lose* — deploy everywhere, anchor branding on it |
| **Low Uniqueness** | *Ignore/test* — weak candidate | *Avoid solo use* — famous but shared with competitors; always pair with brand name |

Practitioner benchmark: assets clearing ~50% fame and ~50% uniqueness are strong enough to carry branding weight. Below that, always co-present the brand name.

### Protect
- Trademark what clears the grid; monitor competitor creep on your codes.
- Write assets into the brand voice/creative checklist so every gate-checked ad and post carries them (this is a line item in ad reviews under `harness/references/ad-write-guardrails.md`).
- Never let a rebrand discard a high-fame/high-uniqueness asset without measuring what's being destroyed.

---

## Framework: Category Entry Points (identify → rank → cover)

CEPs are the situations, needs, and occasions that bring a category to mind — the retrieval cues buying starts from (Romaniuk & Sharp; codified in Romaniuk, *Better Brand Health*, 2023). Mental availability = how many CEPs your brand is linked to, across how many category buyers.

### Step 1 — Identify (elicit with the W's)
Interview/survey category buyers using Romaniuk's W prompts. For each recent purchase occasion ask:

| W | Prompt | Example (AI receptionist category) |
|---|--------|------------------------------------|
| **Why** | motive/benefit sought | "stop losing after-hours callers" |
| **When** | timing | "after hiring freeze", "tax season crunch" |
| **Where** | location/context | "reviewing missed-call log" |
| **While** | co-occurring activity | "while in court all day" |
| **With/for Whom** | others involved | "office manager pushing for it" |
| **With What** | co-purchased/co-used | "alongside new CRM rollout" |
| **hoW feeling** | emotional state | "embarrassed a lead went to voicemail" |

Aim for 15-30 candidate CEPs from ~20+ buyer conversations or a structured survey. Mine sales-call recordings and reviews for the same cues (method shared with the Customer-Language Mining section in `knowledge/playbooks/brand-positioning.md`).

### Step 2 — Rank
Score each CEP on: (a) **prevalence** — how many category buyers experience it, (b) **frequency** — how often, (c) **competitive linkage** — which brands already own it. Prioritize common, frequent CEPs where no competitor dominates. A niche CEP you own outright is worth less than a share of a giant CEP.

### Step 3 — Cover
- Assign priority CEPs to campaigns, content clusters, and landing pages: each asset should depict one CEP vividly and brand it heavily with distinctive assets.
- Breadth over depth: linking the brand to *more* CEPs across *more* buyers beats deepening one link.
- Track with Romaniuk's mental-availability metrics: **mental penetration** (% of buyers linking you to ≥1 CEP), **network size** (average # of CEPs linked among those aware), **mental market share** (your share of all brand-CEP links in the category — the metric that tracks sales share), **share of mind**.

CEPs also drive SEO/AEO topic selection: each high-priority CEP is a query cluster and an AI-search prompt situation. Map CEPs → page architecture via `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md`.

---

## Targeting Breadth vs Narrow Personas

The evidence points to **sophisticated mass marketing**: reach all category buyers, with creative sharp enough to be noticed and branded enough to be credited. Narrow ICP targeting is a *media efficiency* tool for capture-mode budgets, not a growth theory — restricting reach to a "high-value persona" caps penetration, and Law 3 says the excluded light/non-buyers are half the revenue pool.

**How this squares with Kai's 8 personas (`knowledge/personas/_persona-index.md`):** personas here are **creative devices** — they make one buyer's tension vivid so the ad gets attention — not audience filters. Write *to* the Competent Cog; *buy media* against the whole category. A vivid specific scenario is processed by broad audiences fine (the "empathy vs targeting" distinction). Only narrow the actual media audience when the decision table below says DR doctrine applies.

---

## Decision Table: DR Doctrine vs Availability Doctrine

Both doctrines are correct **in their lane**. Binet & Field's IPA databank analysis (~1,000 effectiveness cases) found the profit-maximizing mix averages ~60% brand building / 40% activation — i.e., you run both, and the ratio shifts with context. **Treat 60/40 as contested-as-a-universal:** it is the average of a wide distribution, and Binet & Field's own follow-up (*Effectiveness in Context*, IPA 2018) shows the optimum shifts with category, brand size, price, and channel mix (online-led categories sit nearer 50/50; Binet has said publicly "60/40 is not an iron rule"). Use this table to pick the operating doctrine for a given budget line:

| Signal | DR doctrine (narrow ICP, immediate response, tight attribution) | Availability doctrine (broad reach, CEP + asset building) |
|---|---|---|
| **Buyer state** | In-market now (the ~5%): active search, demo requests, cart abandoners | Out-of-market (the ~95%): will buy in 1-60 months |
| **Objective** | Pipeline/revenue this quarter | Market share growth over 1-3 years |
| **Business stage** | Pre-PMF, survival cash-flow, <~monthly repurchase validation | Post-PMF with retention holding at DJ-expected levels |
| **Category size vs budget** | Budget too small to reach the category meaningfully — concentrate on highest-intent slice | Budget can achieve real reach of category buyers |
| **Channel economics** | Search/marketplace demand capture NOT yet saturated | Capture channels saturated: rising CPCs, flat volume on more spend |
| **Offer type** | Promos, launches, seasonal windows, event deadlines | Always-on presence; no expiry on the message |
| **Measurement** | Direct response metrics valid (short lag, trackable) | Judge on mental penetration, mental market share, share of search, distinctive-asset fame — not same-quarter ROAS |
| **Creative brief** | Perception-engineering conversion copy, urgency, specific offer (→ `knowledge/frameworks/content-copywriting/perception-engineering.md`) | CEP-situation storytelling, heavy distinctive-asset branding, emotional, broad-processable |
| **Targeting** | Narrow: intent signals, retargeting, named accounts | Broad: all category buyers; personas as creative lens only |

**Default split:** anchor near 60/40 brand/activation for established brands; shift toward activation for early-stage, small-budget, or highly seasonal businesses; shift toward brand when capture channels saturate. Re-derive per client — the 60/40 figure is a databank average, not a law.

**Common misapplication to flag in audits:** a scale-up spending 95% on retargeting + branded search, reporting great ROAS, with flat new-customer counts. ROAS is high *because* the spend targets people already buying. Prescription: cap capture spend at saturation, move the excess to reach.

---

## Anti-Patterns (reject these in plans and audits)

1. **"Focus on your best customers to grow"** — contradicts Laws 2, 3. Growth is penetration.
2. **Loyalty program as growth engine** — reaches heavy buyers; DJ says their loyalty tracks share anyway.
3. **Rebranding away famous assets** for aesthetic freshness — destroys measured fame; demand grid scores first.
4. **Judging brand spend on last-click ROAS** — 95% of the audience buys outside the attribution window.
5. **Differentiation messaging doing distinctiveness' job** — a clever USP nobody attributes to you builds the category, or a competitor. Brand the work.
6. **Persona-as-audience-filter** on availability-doctrine budgets — caps reach at a fraction of category buyers.
7. **Quoting "80/20" for buyer concentration** — the replicated figure is ~50-60/20.

Live-channel actions this doc motivates (media buys, budget reallocations, rebrand rollouts, survey launches to client lists) require human approval per the approval doctrine — nothing here authorizes mutation of live accounts.

---

## How This Maps Into Kai

| Kai surface | Decision this doc informs |
|---|---|
| `/kai-audit`, CRO/marketing audits (`scripts/audit/`) | Diagnose ROAS-looks-great-but-flat-growth accounts; check loyalty complaints against DJ expectation; flag capture-saturation. All quantitative claims still require collector provenance (`harness/references/audit-data-provenance.md`) |
| Campaign planning (`knowledge/playbooks/campaign-orchestration.md`, `scripts/campaigns/campaign_planner.py`) | Budget split (brand vs activation), targeting breadth, CEP assignment per asset |
| Media/ads skills (Meta, Google, LinkedIn ads maps in `AGENTS.md`) | Reach-first audience settings for brand-objective lines; narrow intent audiences only when the decision table says DR |
| Brand strategy work (`knowledge/playbooks/brand-positioning.md`) | Positioning defines what to say; this doc defines who to reach and which memory structures (assets, CEPs) carry it |
| SEO/AEO planning (`knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`, QDP/QDH/QDS) | CEP list → query clusters and page architecture; AI-search visibility as digital physical availability |
| Persona selection (`knowledge/personas/_persona-index.md`) | Personas = creative lens, not media filter, on availability-doctrine work |
| Reporting (`scripts/reporting/weekly_report.py`, CEO decks) | Report mental-availability metrics alongside DR metrics; never grade brand lines on same-quarter ROAS |

---

## Sources

- Ehrenberg-Bass Institute — books and research index (Sharp, *How Brands Grow*; Romaniuk & Sharp, *How Brands Grow Part 2*): https://marketingscience.info/learn-with-us/books
- Ehrenberg-Bass — "How do you measure 'How Brands Grow'?" (availability metrics): https://marketingscience.info/news-and-insights/how-do-you-measure-how-brands-grow
- Ehrenberg-Bass — "The Double Jeopardy Law in B2B shows the way to grow": https://marketingscience.info/the-double-jeopardy-law-in-b2b-shows-the-way-to-grow/
- Graham, Bennett, Franke, Henfrey & Nagy-Hamada (2017) — "Double Jeopardy – 50 Years On," *Australasian Marketing Journal* 25(4): https://www.sciencedirect.com/science/article/abs/pii/S1441358217301519
- Sharp, Romaniuk & Graham (2019) — "Marketing's 60/20 Pareto Law" (SSRN): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3498097
- Ehrenberg-Bass — "The value of Pareto's bottom 80%": https://marketingscience.info/value-paretos-bottom-80/
- Ehrenberg-Bass — "95% of B2B buyers are not in the market for your products" (Dawes): https://marketingscience.info/news-and-insights/ehrenberg-bass-95-of-b2b-buyers-are-not-in-the-market-for-your-products
- Ehrenberg-Bass — "The 95:5 Rule: Why B2B Growth Starts Long Before the Purchase": https://marketingscience.info/news-and-insights/the-955-rule-why-b2b-growth-starts-long-before-the-purchase
- LinkedIn B2B Institute — 95-5 Rule research page: https://business.linkedin.com/advertise/resources/b2b-institute/b2b-research/trends/95-5-rule
- Romaniuk, *Building Distinctive Brand Assets* (Oxford University Press, 2018): https://global.oup.com/academic/product/building-distinctive-brand-assets-9780190311506
- Distinctive Asset Grid explainer (fame/uniqueness scoring, quadrants): https://www.the-brand-algorithm.com/distinctive-asset-grid/
- Ehrenberg-Bass — Romaniuk on *Better Brand Health* (CEPs, W's, mental-availability metrics): https://marketingscience.info/news-and-insights/jenni-romaniuk-on-better-brand-health
- Quantilope — Category Entry Points guide (7Ws summary): https://www.quantilope.com/resources/category-entry-points
- IPA — Binet & Field, *The Long and the Short of It* (60/40 brand/activation) and *Effectiveness in Context* (2018; optimum varies by category): https://ipa.co.uk/knowledge/effectiveness-research-analysis/les-binet-peter-field
- Binet interview (PHD Media) — "60/40 is not an iron rule": https://www.phdmedia.com/exclusive-interview-for-phd-les-binet-speaks-to-tomas-lilja-strategy-director/
