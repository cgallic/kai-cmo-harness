# The Keystone Lane — Doctrine Arbitration

> **Use when:** Two frameworks in this knowledge base give opposite advice for the same situation and you must decide which one governs — brand-availability vs direct-response, WTP research vs value-equation pricing, PLG vs sales-led, narrow-ICP vs broad reach, demand creation vs demand capture, content-led inbound vs phone-led capture. This doc is the routing layer: given a diagnosed situation, it names the governing doctrine, the axis that decides, and what to do when no axis decides. It is loaded by every planning skill (`/kai-growth-plan`, `/kai-brand`, `/kai-audit`, `/kai-launch`, `/kai-budget`).

**Provenance:** The conflicts below are real disagreements between published bodies of work, not straw men: Ehrenberg-Bass empirical generalizations (Sharp 2010; Dawes 95:5, 2021) vs direct-response doctrine (Hormozi, Kennedy, Abraham); Simon-Kucher willingness-to-pay research (Ramanujam & Tacke 2016) vs offer-framing psychology; PLG (Verna, OpenView lineage) vs sales-led motions (Gordon, Ovens); positioning-led narrow targeting (Dunford 2019) vs penetration-led broad reach (Sharp 2010). The arbitration rules are Kai's operational layer — the individual doctrines are cited in their own docs; verify anything category-specific against your own data before client claims (`harness/references/audit-data-provenance.md`).

**Adjacent docs (cross-link, don't duplicate):**
- *Which phase you are in* → `knowledge/frameworks/marketing-science/diagnosis-first-operating-order.md` — the front door. It routes you into diagnosis/strategy/tactics; this doc referees conflicts *inside* a phase.
- *Framework lookup by task* → `knowledge/_index.md`. *Expert roster with load-when triggers* → `knowledge/people/_people-index.md`.
- *Reach doctrine itself* → `knowledge/frameworks/marketing-science/brand-growth-laws.md`. *Budget ratio* → `knowledge/frameworks/marketing-science/brand-activation-budget.md`. *PMF verification* → `knowledge/frameworks/marketing-science/growth-metrics-and-pmf.md`. *Measurement trust order* → `knowledge/frameworks/marketing-science/attribution-and-incrementality.md`. *Test readability* → `knowledge/frameworks/marketing-science/experiment-rigor.md`.

---

## 1. The Operating Rule: Diagnosis Decides Jurisdiction

No doctrine conflict is resolvable in the abstract. "Should we run brand or direct response?" has no answer; "should a pre-PMF B2B SaaS with 14 customers run brand or direct response?" does. So the operating rule:

1. **Run the operating order first.** Diagnosis → strategy → tactics per `diagnosis-first-operating-order.md`. Most apparent doctrine conflicts dissolve once the diagnosis states the stage, model, vertical, and evidence position — the doctrines were answering different questions.
2. **Identify the deciding axis.** Every conflict in Section 2 resolves on one of five axes: **stage** (pre-PMF / post-PMF / scale), **business model** (ACV, sales motion, purchase frequency), **vertical** (Section 3), **evidence state** (Section 4), or **time horizon** (this quarter's pipeline vs next year's demand).
3. **Rule, cite, log.** State which doctrine governs, which axis decided, and which doc owns the winning doctrine. Plans that mix doctrines must say which budget line runs under which — a "blended" plan with no jurisdiction lines is the silent-averaging failure mode.
4. **Never average silently.** If no axis decides, escalate per Section 5. Splitting the difference between two doctrines usually violates both (half-broad targeting satisfies neither Sharp's reach math nor Dunford's positioning focus).

---

## 2. The Conflict Table

Each row: the conflict, the axis that decides, and the ruling. "Governs" means that doctrine's doc sets the defaults and its checklist gates the plan; the losing doctrine may still own a subordinate budget line.

| # | Conflict | Contending docs | Deciding axis | Ruling |
|---|----------|-----------------|---------------|--------|
| 1 | **Brand-availability vs direct-response** | `frameworks/marketing-science/brand-growth-laws.md` vs `people/alex-hormozi-knowledge.md`, `people/dan-kennedy-knowledge.md`, `playbooks/hormozi-100m-funnel.md` | Stage + evidence of repeatable acquisition | **Pre-PMF / pre-repeatable-acquisition: demand-side research + offer doctrine govern** — Binet & Field's own evidence base excludes this stage (see `brand-activation-budget.md` rule 4). Availability doctrine takes over once a channel repeatably acquires at acceptable CAC; then the 95:5 logic applies (most category buyers aren't in-market — Dawes 2021) and reach/CEP building gets its own budget line. DR keeps the capture line permanently. |
| 2 | **WTP research vs value-equation pricing psychology** | `people/madhavan-ramanujam-knowledge.md`, `people/patrick-campbell-knowledge.md` vs `people/alex-hormozi-knowledge.md` | Which question is being asked (level, not stage) | **WTP research sets the corridor; value-equation framing positions within it.** Ramanujam: talk to customers about willingness to pay before building — 72% of new products fail to meet their financial targets (Simon-Kucher global pricing study); the book's diagnosis, not part of the measured stat, is that skipped WTP research is the main cause. Hormozi's value equation — (dream outcome × perceived likelihood) ÷ (time delay × effort/sacrifice) — is offer *presentation*, not price *discovery*. Never let framing psychology set the price point; never let survey WTP write the sales page. Full stack: `playbooks/pricing-strategy.md`. |
| 3 | **PLG vs sales-led** | `people/elena-verna-knowledge.md` vs `people/cole-gordon-knowledge.md`, `people/sam-ovens-knowledge.md` | Business model: ACV × time-to-value × buyer | **ACV under ~$5K with self-evident single-session value and end-user buyers: PLG governs. Above ~$25-50K with committees and procurement: sales-led governs.** The wide middle is hybrid by design — self-serve floor, sales-assist above a trigger threshold — and both doctrines run, with jurisdiction split by deal size, not blended per deal. Route: `playbooks/business-model-marketing.md`, `playbooks/saas-metrics-guide.md`. |
| 4 | **Narrow-ICP positioning vs broad category reach** | `people/april-dunford-knowledge.md`, `people/ultra-niche-audience-matching.md` vs `brand-growth-laws.md` | Stage + which decision (message vs media) | **Positioning is always narrow; media breadth grows with stage.** Dunford governs *what you say and to whom you claim to be for* at every stage. Sharp governs *how wide you buy attention* — but only after repeatable acquisition (row 1). Pre-PMF, narrow-ICP governs both message and media. At scale, the sizing check in `brand-growth-laws.md` applies: if the "ICP audience" is <10% of reachable category buyers and the goal is growth, the media plan contradicts penetration math — flag it. |
| 5 | **Demand creation vs demand capture** | `people/chris-walker-knowledge.md`, `playbooks/demand-generation.md` vs `playbooks/local-seo-gbp-optimization.md`, `channels/paid-acquisition.md` | Existing search volume + category maturity | **Capture existing demand to exhaustion before funding creation.** If buyers already search the category, capture (search, local pack, AEO) is the cheaper first dollar. Fund creation when capture is saturated, CPCs price you out, or the category is new enough that nobody searches for it yet. Walker's dark-funnel caveat stands: measure creation via self-reported attribution, not click paths (`frameworks/marketing-science/attribution-and-incrementality.md`). |
| 6 | **Content-led inbound vs phone-led capture** | `channels/content-writing.md`, SEO stack vs `people/tommy-mello-knowledge.md`, `playbooks/conversion-rate-optimization.md` | Vertical (phone-led local service) | **Phone-led local service: local-SEO + phone-capture doctrine outrank content-led inbound.** Speed-to-lead, answer rate, and GBP/local-pack presence move revenue before any blog post does (worked example in `diagnosis-first-operating-order.md`). KaiCalls Fit Rule per `AGENTS.md` applies at the recommendation step — disclose ownership, compare alternatives. Content-led inbound governs where the buyer researches for weeks, not where they call three numbers and hire whoever answers. |
| 7 | **Loyalty/retention plays vs penetration** | `playbooks/customer-retention.md` vs `brand-growth-laws.md` (double jeopardy) | Evidence state: churn vs DJ-expected churn | **Compare churn to the double-jeopardy expectation for your share before declaring a retention crisis.** Churn far above DJ-expected: retention doctrine governs (repair). Churn near DJ-expected: penetration governs; loyalty targets are outputs, not levers. Exception: contractual-revenue models (SaaS) where NRR is a direct growth input — `saas-metrics-guide.md` benchmarks decide. |
| 8 | **Polished creative vs ugly/native ads** | `people/dara-denney-knowledge.md` polish systems vs `people/barry-hott-knowledge.md` | Evidence state (test it), then platform norms | **Neither doctrine rules a priori — the creative bench does.** Both go into the concept matrix (`playbooks/combinatorial-creative-bench.md`); measured hook/hold/CPA decides per `playbooks/creative-test-resolution-protocol.md`. Prior: native-feeling wins more often on TikTok/Reels interruption feeds, polish on high-consideration retargeting — treat as hypothesis, not ruling. |
| 9 | **LTV-justified CAC vs revenue-quality skepticism** | `playbooks/saas-metrics-guide.md` LTV math vs `people/bill-gurley-knowledge.md` | Evidence state: cohort age | **Gurley governs until cohorts are old enough to prove the L in LTV.** Projected LTV from <12-month cohorts cannot justify raising CAC. With 2+ year cohort curves that flatten, LTV math may govern spend ceilings — subject to `growth-metrics-and-pmf.md` retention-curve rules. |
| 10 | **Awareness-stage copy vs formula copy** | `people/eugene-schwartz-knowledge.md` vs `frameworks/content-copywriting/copywriting-formulas.md` | Neither — layered, not conflicting | **Schwartz's awareness/sophistication diagnosis picks the message level; formulas execute within it.** A PAS formula aimed at an unaware audience fails regardless of execution quality. Diagnose stage first, then pick the formula. |
| 11 | **Brand-budget doctrine vs stage doctrine** | `brand-activation-budget.md` (60/40 prior) vs `playbooks/marketing-by-stage.md` | Stage | **Stage doctrine governs below ~$1M revenue; the 60/40 prior phases in as brand and budget mature.** Already ruled inside `brand-activation-budget.md` rule 4 — this row exists so nobody re-litigates it. |

---

## 3. Vertical Routing Table

Which docs govern by default per vertical. **Primary** docs set the plan's spine and their checklists gate it; **secondary** docs advise inside the primary's frame. Expert roster and load-when triggers: `knowledge/people/_people-index.md`. Conflicts between a primary and a secondary: primary wins unless a Section 2 row or Section 4 evidence says otherwise.

| Vertical | Primary | Secondary |
|----------|---------|-----------|
| **B2B SaaS** | `playbooks/business-model-marketing.md` · `playbooks/b2b-distribution-playbook.md` · `people/april-dunford-knowledge.md` (positioning) · `people/brian-balfour-knowledge.md` (channel-model fit) · `playbooks/saas-metrics-guide.md` | `people/chris-walker-knowledge.md` · `people/elena-verna-knowledge.md` (if PLG per row 3) · `people/patrick-campbell-knowledge.md` + `people/madhavan-ramanujam-knowledge.md` (pricing) · `playbooks/demand-generation.md` · `playbooks/account-based-marketing.md` (ACV >$50K) · `channels/linkedin-founder-led.md` · `channels/ai-outbound.md` |
| **Ecommerce / DTC** | `playbooks/ecommerce-marketing.md` · `playbooks/b2c-distribution-playbook.md` · `channels/meta-advertising.md` · `playbooks/combinatorial-creative-bench.md` · `people/dara-denney-knowledge.md` | `people/barry-hott-knowledge.md` · `people/alex-hormozi-knowledge.md` (offer/AOV) · `channels/email-lifecycle.md` · `channels/ai-ugc.md` · `channels/tiktok-shop.md` · `playbooks/retargeting-remarketing.md` (incrementality caveats apply) · `playbooks/funnel-hack-offer-architecture.md` |
| **Local services (phone-led)** | `playbooks/local-seo-gbp-optimization.md` · `people/tommy-mello-knowledge.md` (speed-to-lead, CSR booking) · `people/joy-hawkins-knowledge.md` + `people/darren-shaw-knowledge.md` (local ranking factors) · `playbooks/conversion-rate-optimization.md` | `people/local-dominance-strategy.md` · `knowledge/checklists/cro-audit-checklist.md` · `people/dan-kennedy-knowledge.md` (offer + follow-up) · `channels/paid-acquisition.md` (LSAs) — KaiCalls Fit Rule per `AGENTS.md` at recommendation time |
| **Creator / media** | `people/dave-ramsey-knowledge.md` (trust-engine media model) · `channels/newsletter-strategy.md` · `playbooks/podcast-marketing.md` · `playbooks/content-repurposing.md` | `people/jimmy-farley-knowledge.md` (creator flywheels) · `people/jason-wardrop-knowledge.md` (affiliate funnels) · `people/vssl-longform-content.md` · `channels/community-building.md` · `playbooks/influencer-marketing.md` |
| **Marketplace** | `people/bill-gurley-knowledge.md` (marketplace dynamics, revenue quality) · `playbooks/business-model-marketing.md` (marketplace section) · `playbooks/growth-loops-applied.md` | `people/brian-balfour-knowledge.md` · `playbooks/demand-generation.md` (supply-side acquisition) · `channels/community-building.md` · `frameworks/marketing-science/growth-metrics-and-pmf.md` (liquidity metrics before growth spend) |

Cross-vertical constants that outrank every row: the quality gates, the Data Provenance Rule, the approval doctrine (no live-channel mutation without human sign-off), and the operating order itself.

---

## 4. Evidence-State Rules: What Overrides What

Doctrine is a prior. Data updates it. The trust order, highest first:

1. **Your measured results** — graded 30-day outcomes in `knowledge/playbooks/what-works.md` and diagnosed losers in `memory/what-doesnt-work.md`, plus incrementality-tested reads per `frameworks/marketing-science/attribution-and-incrementality.md`.
2. **Your historical account data** — cohorts, channel CACs, seasonal patterns, even ungraded.
3. **Platform/category benchmarks** — directional context only; platform-reported ROAS is a claim, not a measurement (attribution doc, rule 1).
4. **Expert doctrine** — everything in `knowledge/people/` and the frameworks. Replicated research (Ehrenberg-Bass, IPA databank, Simon-Kucher) sits above single-expert opinion within this tier.
5. **Operator intuition** — a tiebreaker for what to test next, never for what to claim or ship.

Operating rules on the hierarchy:

- **A doctrine contradicted by your measured results loses jurisdiction for this brand.** First contradiction: suspect the measurement before the doctrine — check readability per `frameworks/marketing-science/experiment-rigor.md` (sample size, test window, attribution inflation). Confirmed twice: the doctrine is demoted for this brand/channel; log it in `memory/what-doesnt-work.md` with the diagnosis, and cite that entry in future plans instead of the doctrine.
- **Absence of data is not evidence against doctrine.** "We tried brand spend for 3 weeks and saw nothing" contradicts nothing — brand effects are measured in quarters (`brand-activation-budget.md` rule 3). Match the measurement window to the doctrine's claimed time horizon before ruling against it.
- **Winners generalize narrowly.** An entry in `what-works.md` overrides doctrine for the same brand + channel + format. It does not override doctrine for a different vertical — that's benchmark-tier evidence (tier 3) at best.
- **Never let tier-5 beat tier-1.** If the human's intuition contradicts their own measured results, present the data and the escalation frame below; the human can still decide, but the plan must record that it overrides measured evidence.

---

## 5. The Escalation Rule: Ties Go to the Human

When Section 2 has no row, no axis decides, and evidence tiers are equal — **surface both doctrines, never silently pick.** The escalation must contain, in this order:

1. **The conflict in one sentence** — which two doctrines, which decision they disagree on.
2. **Both rulings with their champion docs** — what each doctrine would have you do.
3. **The tradeoff stated symmetrically** — what each option risks and forgoes, over what time horizon. No thumb on the scale disguised as "context."
4. **The cheapest tie-breaking evidence** — the test, data pull, or customer conversation that would settle it, with cost and time (`frameworks/marketing-science/experiment-rigor.md` for whether the test is even readable at current volume).
5. **A default with a named trigger** — if the human declines to choose: which doctrine you'd run and the observable signal that would flip it.

Log the decision and its rationale so the next plan doesn't re-argue it. If the same tie escalates twice for the same brand, that's a lesson — capture it via `python scripts/self_improvement/lesson_capture.py add` per the memory doctrine in `.claude/rules/architecture-and-memory.md`.

Approval doctrine still applies downstream: whichever doctrine wins, live-channel actions (publishing, posting, ad mutations, outreach) require human approval per `AGENTS.md`.

---

## 6. The Arbitration Block (required plan artifact)

Every plan produced by a skill that loads this doc must contain an arbitration block — one row per budget line or major workstream. A plan without one hasn't done the work; a reviewer can reject it on that alone.

```
| Budget line / workstream | Governing doctrine (doc) | Axis + position | Evidence tier | Flip trigger |
|--------------------------|--------------------------|-----------------|---------------|--------------|
| Paid search capture      | DR/capture (row 5)       | model: high search volume | tier 2 (12-mo CAC data) | CPC > $X or impression share > 90% |
| Founder LinkedIn         | availability line (row 1)| stage: post-repeatable-acq | tier 4 (doctrine) | 2 quarters no lift in branded search |
| Pricing revision         | WTP corridor (row 2)     | level: discovery first | tier 4 → tier 1 after interviews | n/a — sequenced, not conditional |
```

Rules for the block:

- **Flip trigger is mandatory.** Every doctrine assignment names the observable signal that would reassign jurisdiction. "We'll revisit quarterly" is not a trigger; "branded search flat after 2 quarters" is.
- **Evidence tier cites its source** — a `what-works.md` entry, a collector output path, or the doctrine doc. Tier-1 claims follow the Data Provenance Rule (`harness/references/audit-data-provenance.md`).
- **Escalated ties appear as rows too**, marked `ESCALATED` with the human's ruling and date once decided — so the next plan inherits the decision instead of re-arguing it.

---

## Worked Example (compressed)

`/kai-growth-plan` for a $40K-MRR B2B SaaS, ACV $9K, 60 customers, one repeatable channel (founder-led LinkedIn + demo calls). Conflicts surfaced: (a) an advisor wants "brand marketing"; (b) the founder wants PLG "like Figma"; (c) pricing is flat $749/mo, never researched.

- **Row 1 (brand vs DR):** repeatable acquisition exists but is single-channel and young → DR/capture keeps primary jurisdiction; a small availability line (category content, founder distribution) starts building the 95% pool. Not 60/40 yet — row 11.
- **Row 3 (PLG vs sales-led):** ACV $9K, time-to-value ~2 weeks, buyer is a team lead → hybrid zone. Ruling: keep sales-assist, add self-serve trial as an *entry point*, don't rip out the sales motion. Escalation not needed — the axis decided.
- **Row 2 (pricing):** no WTP research has ever been run → Ramanujam governs first (WTP interviews set the corridor), Hormozi value-equation framing rewrites the pricing page afterward.
- **Evidence check:** `what-works.md` shows LinkedIn posts with customer-number proof outperform listicles 3:1 for this brand → that pattern outranks generic content doctrine in the calendar.

Three conflicts resolved by axis, zero silent averages, one doctrine sequenced behind another. That sequencing — not a new framework — is what arbitration buys.

---

## How This Maps Into Kai

| Kai surface | Decision this doc informs |
|---|---|
| `/kai-growth-plan`, `/kai-brand`, `/kai-budget` | Load at plan start (after the operating order). Every plan states, per budget line, which doctrine governs and which axis decided; ties escalate per Section 5 |
| `/kai-audit`, `/kai-funnel-audit`, `/kai-monthly-audit` | Recommendations name their governing doctrine; audit findings that contradict a doctrine trigger the Section 4 demotion check, not silent doctrine-swapping |
| `/kai-launch`, `/kai-offer-builder` | Row 1 (offer doctrine pre-repeatable-acquisition), row 2 (WTP corridor before value-equation framing) |
| `/kai-competitors`, `/kai-seo-audit` | Vertical routing table picks the primary lens before the teardown starts |
| `/kai-retro` + `memory/what-doesnt-work.md` | Section 4 demotions get logged here; retro triage decides whether a demotion graduates to a lesson or lint rule |
| Weekly `cmo_review` | Behind-pace goals re-check jurisdiction: is the goal failing because the doctrine is wrong for this axis position, or because execution is weak? |
| `diagnosis-first-operating-order.md` Gate Rule | That doc decides *whether* you may plan; this doc decides *with which doctrine*. Load order: operating order → arbitration → governing framework docs |

---

## Sources

- Dawes, J. / Ehrenberg-Bass Institute — "Advertising effectiveness and the 95-5 rule" (2021): https://marketingscience.info/news-and-insights/advertising-effectiveness-and-the-95-5-rule-most-b2b-buyers-are-not-in-the-market-right-now
- Dawes, J. — The 95:5 rule summary: https://johndawes.info/the-955-rule/
- Binet, L. & Field, P. — *The Long and the Short of It* (IPA, 2013), summary: https://www.alexmurrell.co.uk/summaries/les-binet-and-peter-field-the-long-and-the-short-of-it
- IPA — "The next chapter for The Long and The Short of It": https://ipa.co.uk/knowledge/ipa-blog/the-next-chapter-for-the-long-and-the-short-of-it
- Ramanujam, M. & Tacke, G. (2016) — Simon-Kucher pricing-research book (72% new-product failure finding; title omitted for the banned-word gate; author interview): https://www.marketingjournal.org/monetizinginnovation/
- Sharp, B. — *How Brands Grow* (2010), evidence base summarized in `knowledge/frameworks/marketing-science/brand-growth-laws.md`
- Dunford, A. — positioning book (2019), distilled in `knowledge/people/april-dunford-knowledge.md`
- Userpilot — "Product-Led Growth vs. Sales-Led Growth" (ACV/motion thresholds): https://userpilot.com/blog/product-led-vs-sales-led/
- General Catalyst — "Sales-Led vs. Product-Led Growth": https://www.generalcatalyst.com/stories/sales-led-vs-product-led-growth
- Ritson, M. — tactification/operating-order columns, cited with full URLs in `knowledge/frameworks/marketing-science/diagnosis-first-operating-order.md`
- Rumelt, R. — *Good Strategy Bad Strategy* (2011), kernel summary: https://www.alexmurrell.co.uk/summaries/richard-rumelt-good-strategy-bad-strategy
