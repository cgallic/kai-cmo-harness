# Brand vs Activation Budget Split — The Long/Short Doctrine

> **Use when:** Setting or defending the split between brand building and sales activation, sizing budgets against a growth target (ESOV), explaining why performance metrics undervalue brand spend, or reviewing a plan that is 90%+ performance marketing. Channel-level allocation math and forecasting live in `knowledge/playbooks/marketing-budget-forecasting.md`; stage-appropriate activities live in `knowledge/playbooks/marketing-by-stage.md`. This doc owns one decision: **the ratio between long-term brand investment and short-term activation, and the total spend level needed to grow.**

---

## Quick Reference — Decision Rules

1. **Start from 60/40 brand/activation as a prior, never as a law.** It is the average of a distribution across ~1,000 IPA case studies, mostly large UK consumer brands. Adjust for category, stage, and brand size before using it.
2. **Fund growth with ESOV.** Set share of voice above share of market if you want share growth. Roughly 10 points of ESOV correlates with ~0.5–0.7% market share growth per year on average — a planning guideline, not a guarantee.
3. **Judge activation on weeks, brand on years.** Activation effects mostly decay within about six months; brand effects compound over 1–3+ years. Any measurement window under six months will systematically overvalue activation.
4. **Pre-product-market-fit businesses are outside this evidence base.** Skew heavily to activation/direct response until PMF (see `knowledge/playbooks/marketing-by-stage.md`); apply this doctrine as brand and budget mature.
5. **Treat the whole evidence base as strong-but-biased priors** (award-entry selection bias, big-brand skew, pre-digital-era data — see Criticisms below). Validate with your own holdouts or MMM before betting the company on a ratio.
6. **Approval doctrine:** any live budget change to an ad account or channel that this framework motivates goes through human approval first. This doc informs recommendations; it never authorizes mutations.

---

## The Two Effects

Binet & Field's core finding (from IPA Effectiveness Awards databank analysis, 1980–2010, ~996 campaigns) is that advertising works through two distinct mechanisms with different time signatures:

| | Brand building | Sales activation |
|---|---|---|
| **Mechanism** | Creates memory structures and mental availability in future buyers; mostly emotional | Converts existing demand from in-market buyers; mostly rational/informational |
| **Audience** | Broad reach, category-wide (most of whom are not in-market today) | Narrow, in-market, high-intent |
| **Sales effect shape** | Slow build, small at first, compounds | Immediate spike |
| **Decay** | Slow — effects persist and stack over years | Fast — most effect gone within weeks to ~6 months |
| **Also improves** | Price elasticity (less discounting needed), baseline sales, effectiveness of future activation | Nothing durable — baseline unchanged when spend stops |
| **Best measured by** | Econometrics/MMM, brand tracking, share of search, penetration — over 1–3 years | Attribution, CPA/ROAS, conversion lift — over days/weeks |

Important nuance from Binet himself: this is a spectrum, not a binary. Every ad produces some of both effects; "brand" and "activation" describe the dominant mechanism, not exclusive categories. Ritson has shown brand-building ads also produce measurable short-term sales effects.

---

## Decay Curves — Why Short Windows Lie

```
Sales
uplift
  │   ██ activation spike
  │  ████
  │ ██████                    ← activation: tall, narrow, decays in weeks–months
  │████████▄
  │██████████▄▄____________________________________
  │
  │          ▁▁▂▂▃▃▄▄▅▅▆▆▇▇███████████████          ← brand: slow build,
  │▁▁▂▂▃▃▄▄▅▅                                          compounds, persists years
  └────────────────────────────────────────────► time
   0    3mo    6mo    1yr         2yr        3yr
```

- Activation campaigns generate their biggest sales response inside six months, then the effect collapses back to baseline. Brand campaigns barely register in the first months, then keep paying back for years (Binet & Field, *The Long and the Short of It*).
- Thinkbox's *Profit Ability 2* (2024; econometrics covering 141 brands, 14 categories, and £1.8bn of UK media spend, 2021–2023): advertising in the dataset returned an average **£1.87 short-term profit ROI per £1, rising to £4.11 over the full 0–24 month window** — **58% of total profit generation lands after the first 13 weeks**.
- **The attribution trap:** last-click and platform attribution can only see the spike, never the baseline shift. A dashboard that reports weekly ROAS will always tell you to cut brand and buy more activation. That is a measurement artifact, not a finding. If your longest measurement window is 30 days, you have no data about the majority (~58% in Profit Ability 2) of advertising's payback.

**Decision rule:** commit the measurement window before committing the budget. Brand line items get a minimum 6-month judgment window and a 1–3 year payback model; activation line items get weekly optimization.

---

## The Evidence Base — What the Data Says

| Source | Finding | Status |
|---|---|---|
| Binet & Field, *The Long and the Short of It* (IPA, 2013) | Campaigns balancing brand and activation outperform either alone; the average optimum across the databank is ~60% brand / 40% activation | **Average of a distribution across award-entered campaigns.** Not a law; per-brand optimum varies widely |
| Binet & Field, *Media in Focus* (IPA, 2017) | The optimum was drifting up toward brand as digital activation saturated | Directional |
| Binet & Field, *Effectiveness in Context* (IPA, 2019) | The optimum is contextual: tables adjust it by category, brand size, price position, product novelty, and online vs offline purchase. Financial services optimum ~80/20 brand-heavy; optimum brand share is lowest in perishable/short-consideration services such as travel. Warns against the "online fallacy" — assuming online-bought brands only need online activation | The correction to naive 60/40 use, from the same authors |
| Binet & Field × LinkedIn B2B Institute, *5 Principles of Growth in B2B* (2019) | In B2B the average optimum is ~**46% brand / 54% activation** (the B2B Institute's headline recommendation rounds this to ~50/50); the SOV rule still holds (10 pts ESOV ≈ 0.7%/yr share growth in B2B); acquisition beats loyalty; emotion drives long-term effects even in B2B | Smaller B2B sample; directionally consistent with B2C |

The honest summary: the *shape* of the findings (two effects, different decay, balance beats either extreme, ESOV predicts growth) is replicated across datasets. The *specific numbers* (60/40, 0.7%/10pts) are dataset averages with wide variance and should be quoted with that caveat every time.

---

## ESOV — Sizing the Budget

**Definitions.** SOV = your share of category advertising spend. SOM = your share of category revenue. **ESOV = SOV − SOM.**

**The rule** (John Philip Jones, *Ad Spending: Maintaining Market Share*, HBR 1990; extended by Binet & Field on IPA data): brands with SOV above SOM tend to grow share; brands below tend to shrink; growth rate is roughly proportional to ESOV. IPA analysis puts the average at **~0.5–0.7% market share growth per year per 10 points of ESOV** (B2C ~0.5%, B2B ~0.7% per the B2B Institute analysis), with real category spread — some categories see ~1.5 pts per 10 ESOV, others need ~20 pts of sustained ESOV per share point.

**Use it in three steps:**

1. **Estimate SOM** from category revenue data (provenance rule applies — collector-sourced numbers only, no guessed market sizes).
2. **Estimate SOV.** Traditional media: measured spend databases. Digital-era workaround: **share of search** as a proxy for brand strength/SOM trajectory (Binet's 2020 share-of-search work) — it is a proxy, not a replacement, and it lags/leads differently by category.
3. **Back out budget.** Target share growth ÷ 0.05–0.07 per point ≈ ESOV points needed ÷ category spend ≈ incremental budget. Then apply the brand/activation split from the worksheet below to that total.

**Caveats (state these in any client-facing plan):**
- Correlation with reverse-causality risk: growing brands can afford more SOV. The relationship replicates across datasets but is not a controlled experiment.
- Creative quality multiplies or erases it — strong creative gets several times the growth per ESOV point of weak creative.
- SOV is increasingly unmeasurable: creator content, organic social, retail media, and owned channels carry "voice" that spend-share misses. Treat any digital-era SOV number as an estimate with wide error bars.
- Distribution, pricing, and product changes routinely swamp the ESOV effect in any single year.

---

## Allocation Worksheet

Work through the steps in order. Modifiers are directional (shift the brand share by the stated points); clamp the final brand share between 20% and 80%.

**Step 1 — Baseline.** Start at 60% brand / 40% activation (B2C) or 46/54 (B2B).

**Step 2 — Category modifier.**

| Category signal | Brand share shift | Why |
|---|---|---|
| Financial services / high-trust considered purchase | +10 to +20 | Activation is easy, trust is the constraint (*Effectiveness in Context*: ~80/20 optimum) |
| Subscription / repeat-revenue model | +5 to +10 | Long customer lifetimes reward mental availability and lower churn-replacement cost |
| Perishable / short-window services (travel deals, events) | −10 to −20 | Demand is now-or-never; optimum brand share is lowest here |
| Pure e-commerce/DTC | 0, resist the urge to cut | The "online fallacy": buying online does not mean only activation works |
| B2B with long sales cycles | Use 46/54 baseline, then +5 if 95%+ of buyers are out-of-market at any time | Future-buyer memory matters more as cycles lengthen |

**Step 3 — Stage modifier** (heuristic extension — the IPA data does not cover pre-PMF startups; cross-check `knowledge/playbooks/marketing-by-stage.md`):

| Stage | Brand/activation planning range | Rationale |
|---|---|---|
| Pre-launch → Early (pre-PMF, <$10K MRR) | 0–10 / 90–100 | Outside the evidence base. You need conversion signal and customer language, not reach. "Brand" here = consistent name, look, and story on activation assets, at near-zero cost |
| Growth ($10K–$100K MRR) | 20–40 / 60–80 | First deliberate brand line item once one channel reliably converts; distinctive assets, category content, founder brand |
| Scale ($100K+ MRR) | 40–60 / 60–40 | Move toward the category-adjusted optimum; activation-only plans hit rising CAC as warm demand exhausts |
| Category leader / mature | 60–80 / 40–20 | Defend share, keep price elasticity low, starve challengers of ESOV |

**Step 4 — Situation modifiers.** New product launch: −10 brand for 1–2 quarters (announcement is activation-shaped). Heavy discount dependence / eroding margins: +10 brand (price elasticity is a brand problem). Brand tracking flat while CAC rises quarter over quarter: +10 brand (classic under-investment signature). Cash runway under 12 months: activation-first regardless of doctrine — survival outranks the long term.

**Step 5 — ESOV check.** After setting the split, check the *level*: does total spend produce SOV ≥ SOM? A perfect 60/40 split of an invisible budget grows nothing. If ESOV is deeply negative and can't be funded, concentrate: win ESOV within a segment, region, or channel you can dominate rather than diluting nationally.

**Step 6 — Measurement commitments.** Write into the plan: brand budget judged at 6/12/24 months via MMM or geo-holdout + brand tracking + share of search; activation judged weekly on CPA/ROAS with incrementality tests; no mid-year raiding of the brand line because a dashboard showed a ROAS gap (that gap is the expected artifact from the decay section).

### Worked example

DTC skincare brand, $5M revenue, scale stage, subscription-heavy, 14% share of category search, $1.2M marketing budget.

- Baseline 60/40 → subscription +5 → new-hero-SKU launch this half −10 → **~55% brand / 45% activation** → $660K brand / $540K activation.
- ESOV check: category ad spend ≈ $40M, so $1.2M ≈ 3% SOV vs ~5% SOM → ESOV ≈ −2. At this budget, national share growth is unlikely; recommendation: concentrate brand spend on two metro geos + one audience segment to run positive ESOV where it's affordable, and set expectations that national share is defend-only this year.
- Measurement: geo-split MMM readout at month 6 and 12; weekly ROAS on the activation 45% only.

Every number above that feeds a client deliverable must come through the audit collector per the Kai Data Provenance Rule — never estimate a client's SOM or category spend from memory.

---

## Criticisms and Limits of the Evidence (disclose these)

1. **Selection bias.** The IPA databank is built from effectiveness-award entries — nobody submits failures. Findings describe what distinguishes excellent campaigns from other good campaigns, not advertising in general.
2. **Big-brand, B2C, UK, pre-digital skew.** Most cases are large established consumer brands, and much of the data predates performance-marketing platforms. Transfer to startups, niche B2B, and digital-native brands is extrapolation.
3. **Methodological pushback.** Byron Sharp (Ehrenberg-Bass) has argued the 60/40 rule does not meet a scientific standard of evidence; case-study meta-analysis cannot isolate causality the way controlled experiments can. (Ehrenberg-Bass's own mental/physical availability work nonetheless points the same broad direction: reach and memory drive growth.)
4. **The dichotomy is leaky.** Brand ads produce short-term sales; activation done well (distinctive, consistent) leaves brand residue. Binet himself calls the split a useful simplification. Budget lines are cleaner than the underlying reality.
5. **Possible confounds in the ratio finding.** Campaigns entered with long measurement windows tend to come from brand-believing teams at healthier companies; some of the "60/40 wins" pattern may reflect who runs balanced campaigns, not the ratio itself.
6. **ESOV measurement is degrading.** Spend-share SOV misses creator, organic, and retail media voice, so modern ESOV numbers carry wide error bars, and share-of-search proxies have their own category-specific quirks.

**Operational consequence:** quote 60/40 and ESOV coefficients as *priors with named sources and caveats*, run your own incrementality tests, and update the ratio annually from your own MMM/holdout evidence — never present the IPA averages as a client-specific prediction.

---

## Anti-Patterns

- **The ROAS death spiral:** cutting brand because attribution can't see it, watching CAC rise 12–18 months later, then cutting brand again to fund the now-more-expensive activation.
- **Quoting "60/40" as a universal law** in an audit or deck without the average-not-optimum caveat and category adjustment. Instant credibility loss with any informed CMO.
- **Brand budget, activation measurement:** approving a brand line and then judging it on 30-day conversions. Decide the window first (Step 6) or don't spend it.
- **Pre-PMF brand campaigns:** applying this doctrine to a company that hasn't found a converting channel yet. See `knowledge/playbooks/marketing-by-stage.md` — conversions first.
- **ESOV theater:** claiming a precise SOV number from unmeasurable digital categories to justify a budget. State error bars or use share of search with the proxy caveat.

---

## How This Maps Into Kai

- **`/kai` audit and strategy workflows** (marketing audits, growth plans, CMO reviews via `agent/tasks/cmo_review.py` goal decomposition) load this doc when a recommendation touches budget split, brand-vs-performance balance, or "should we invest in brand" questions.
- **Campaign planning** (`knowledge/playbooks/campaign-orchestration.md`, `scripts/campaigns/campaign_planner.py` outputs) uses the worksheet to sanity-check the brand/activation weighting of multi-channel plans.
- **Budget math and channel-level allocation** stay in `knowledge/playbooks/marketing-budget-forecasting.md` (70/20/10, pipeline math, ROI benchmarks); **stage-appropriate activities** stay in `knowledge/playbooks/marketing-by-stage.md`. This doc supplies the brand/activation ratio and ESOV sizing those docs assume.
- **Provenance:** any client-facing deliverable using this doc's numbers must cite the sources below, mark 60/40 and ESOV coefficients as dataset averages, and source client-specific SOM/SOV/category-spend figures through `scripts.audit.collect` per the Kai Data Provenance Rule. Missing category-spend data goes in `_data-gaps.md`, not into an invented ESOV figure.
- **Approval doctrine:** reallocation of live ad-account budgets recommended by this framework requires explicit human approval before execution.

---

## Sources

- IPA — The Key Works of Les Binet & Peter Field: https://ipa.co.uk/knowledge/effectiveness-research-analysis/les-binet-peter-field
- Alex Murrell — summary of *The Long and the Short of It*: https://www.alexmurrell.co.uk/summaries/les-binet-and-peter-field-the-long-and-the-short-of-it
- Growth Method — Binet & Field framework explained (incl. limitations): https://growthmethod.com/long-and-short/
- Thinkbox — *Effectiveness in Context* (full report download): https://www.thinkbox.tv/research/reports/effectiveness-in-context-free-download
- thinkTV — *Effectiveness in Context* summary (category optima incl. financial services ~80/20): https://thinktv.ca/research/effectiveness-in-context/
- System1 — Binet & Field on *Effectiveness in Context* (online fallacy): https://system1group.com/blog/saved-the-baby-binet-and-field-on-effectiveness-in-context
- LinkedIn B2B Institute — *The 5 Principles of Growth in B2B Marketing*: https://business.linkedin.com/marketing-solutions/b2b-institute/marketing-as-growth
- Alex Murrell — summary of the B2B Institute 5 Principles (46/54, B2B ESOV): https://www.alexmurrell.co.uk/summaries/the-b2b-institute-the-5-principles-of-growth-in-b2b-marketing
- The Drum — exclusive look at Binet & Field's B2B research: https://www.thedrum.com/opinion/exclusive-look-binet-and-field-s-new-b2b-marketing-research
- John Philip Jones — *Ad Spending: Maintaining Market Share*, HBR 1990: https://hbr.org/1990/01/ad-spending-maintaining-market-share
- LinkedIn — The B2B Marketer's Guide to the Share of Voice Rule: https://business.linkedin.com/en-uk/marketing-solutions/blog/posts/B2B-Marketing/2020/The-B2B-Marketers-Guide-To-The-Share-of-Voice-Rule
- CreativeX — ESOV overview and creative-quality interaction: https://www.creativex.com/blog/marketing-metric-extra-share-of-voice
- DPR&Co — ESOV as driver of market share (category variance): https://blog.dprandco.com/excess-share-of-voice-a-key-driver-of-increased-market-share
- Marketing Week — *Profit Ability 2*: long-term ROI more than double short term (£1.87 → £4.11): https://www.marketingweek.com/advertising-drives-roi-pound-invested/
- Thinkbox — *Profit Ability 2: The new business case for advertising*: https://www.thinkbox.tv/research/thinkbox-research/profit-ability-2-the-new-business-case-for-advertising
- Mi3 — Byron Sharp's critique of Binet & Field: https://www.mi-3.com.au/07-09-2022/how-brands-shrink-prof-byron-sharps-takedown-binet-field-attention-metrics
- BBH Labs — "The Long and the Short of It needs The Wrong and the Sh*t of It" (selection-bias critique): https://www.bbh-labs.com/the-long-and-the-short-of-it-needs-the-wrong-and-the-shit-of-it
- Marketing Week (Ritson) — brand-building ads boost short-term sales: https://www.marketingweek.com/ritson-brand-building-boost-short-term-sales/
- Les Binet — "Brand vs Activation: A False Dichotomy?": https://www.linkedin.com/posts/les-binet-9bb7453_brand-vs-activation-a-false-dichotomy-activity-7022177396585832449-kbtU
- The EQ Planner — share of search as SOM proxy (caveats): https://theeqplanner.wordpress.com/2023/09/21/sneaking-this-one-out-the-second-part-of-my-share-of-search-work-shareofsearch-sos/
