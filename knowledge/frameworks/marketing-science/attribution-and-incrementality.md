# When Attribution Is Lying — Incrementality Doctrine

> **Use when:** A report, audit, or budget recommendation depends on channel-level credit ("Meta drove 40% of revenue"), platform ROAS looks too good, a client asks "which channel truly works," or you are designing a lift/geo/holdout test. This doc is the **skepticism and causal-testing layer** on top of `knowledge/playbooks/analytics-attribution.md` — read that first for the attribution-model comparison table, UTM standards, measurement ladder, GA4 setup, and blended CAC. This doc owns three questions: **why platform-reported numbers inflate, what MTA/MMM/incrementality can and cannot answer, and which measurement method to trust at which spend level.**

---

## Quick Reference — Decision Rules

1. **Platform ROAS is a claim, not a measurement.** Every ad platform grades its own homework using self-attribution (clicks and views it observed). Treat platform ROAS as an upper bound on incremental return, useful for *relative* comparison within one platform, never as causal evidence across platforms.
2. **Sum of platform-claimed revenue > actual revenue is the tell.** When Meta + Google + TikTok dashboards together claim more conversions than the business recorded, credit is being double-counted. Reconcile against the order/CRM system of record before quoting any channel number.
3. **Retargeting and brand search are the two most inflated line items in any account.** Both select audiences already on the way to converting. Test these first — they are cheap to test and most likely to be over-credited (eBay brand-search experiment: no measurable short-term benefit — Blake, Nosko & Tadelis 2015).
4. **Choose the measurement method by spend level** (table below). Under ~$10K/month, formal incrementality tests are usually underpowered — use blended CAC, pulse tests, and self-reported attribution instead of pretending precision.
5. **Design tests with a power analysis first.** If the minimum detectable effect exceeds the plausible lift, do not run the test — you will get noise and someone will act on it (Lewis & Rao 2015: median ROI confidence interval in 25 large experiments was over 100 percentage points wide).
6. **Triangulate, never crown one source.** Software attribution (captures demand) + self-reported attribution (creates demand) + causal tests (settles budget questions) + blended CAC (grounds everything). Disagreement between them is information, not error.
7. **Kai hard rule:** every channel-credit claim in a Kai report, audit, or deck MUST state the measurement method and its known bias inline (template below). A ROAS number with no method label fails review.
8. **Approval doctrine:** every test this doc prescribes touches live channels — pausing spend, holdout audiences, geo dark periods. All of it requires explicit human approval before execution. This doc designs tests; it never launches them.

---

## How Platform ROAS Inflates — The Mechanics

Platform-reported ROAS diverges from incremental ROAS through five stacked mechanisms. Each one only ever pushes the number **up**.

### 1. View-through credit
Meta's default attribution is **7-day click + 1-day view**: a user who scrolled past an ad (an "impression") and bought within 24 hours is counted as a conversion the ad "drove," with engaged-view and view windows crediting video impressions similarly (Jon Loomer, Meta attribution mechanics). The user may have converted from email, organic search, or existing intent — the platform cannot see those paths and does not subtract them. Diagnostic: break out view-through vs click-through conversions in Ads Manager; a large view-through share is a flag to discount reported ROAS and prioritize a lift test, not a finding that the ads work.

### 2. Retargeting credit-claiming
Retargeting targets people selected *because* they already visited, carted, or bought. Baseline conversion probability in that pool is high, so last-touch and view-through credit flows to ads shown to people already converging on purchase. Retargeting is not zero — the ghost-ads experiments measured real lift from retargeting (+17.2% site visits, +10.5% purchases in the studied campaign; Johnson, Lewis & Nubbemeyer 2017) — but measured lift is a fraction of what platform attribution claims for the same campaigns. Rule: never quote retargeting ROAS without a holdout behind it.

### 3. Brand-search cannibalization
Brand keyword ads intercept users already searching for you. eBay's large-scale shutdown experiment found brand-keyword ads had **no measurable short-term benefit** — organic clicks absorbed nearly all the traffic — and overall paid-search returns were a fraction of the non-experimental estimates the dashboards showed (Blake, Nosko & Tadelis, *Econometrica* 2015). State the caveat: eBay is a giant brand with dominant organic presence; small brands with weak organic rank and aggressive competitor conquesting can see real brand-search incrementality. That is an argument for testing it, not for trusting the dashboard.

### 4. Window and dedup asymmetry
Each platform claims 100% of any conversion inside its own window; no platform deduplicates against the others. A buyer who clicked a Meta ad Tuesday and a Google ad Thursday is a full conversion in both dashboards. Longer windows mechanically raise reported ROAS with no change in reality — which is why comparing ROAS across platforms with different window settings is meaningless.

### 5. Attribution fraud (mostly mobile/affiliate)
Click spamming and click injection fire fake "clicks" so networks claim credit for organic installs. Uber's canonical case: after suspecting fraud, it shut off roughly **$100M of a ~$150M performance budget and saw no measurable change in rider acquisition**; some partner apps showed more ad clicks than Uber had users, and Uber sued its agency and five networks (WARC interview with Kevin Frisch; CHEQ settlement analysis). Lesson: the strongest fraud detector was not a tool — it was turning spend off and watching the baseline.

**Academic ground truth on the gap:** comparing 15 large US advertising RCTs at Facebook against standard observational/attribution methods, Gordon, Zettelmeyer, Bhargava & Chapsky (*Marketing Science* 2019) found observational estimates commonly diverged severely from experimental lift — often overstating it by multiples — even with rich user-level data. The 2023 follow-up across 663 experiments ("Close Enough?", Gordon, Moakler & Zettelmeyer) found even sophisticated double-ML observational methods still missed experimental benchmarks by economically significant margins, especially for purchase outcomes. This is the published basis for the doctrine: **no attribution model, however clever, substitutes for an experiment.**

---

## MTA vs MMM vs Incrementality — What Each Can and Cannot Answer

Full model-by-model bias table: `knowledge/playbooks/analytics-attribution.md`. This table is the causal-question view.

| | Multi-touch attribution (MTA) | Marketing mix modeling (MMM) | Incrementality testing |
|---|---|---|---|
| **What it is** | Assigns fractional credit across observed digital touchpoints | Regression/Bayesian model of outcome vs spend + seasonality + external factors (Meridian, Robyn) | Randomized or quasi-experiment: exposed vs holdout |
| **Can answer** | Which observed paths co-occur with conversion; in-flight creative/audience comparison within a channel | Long-run channel contribution incl. offline/brand; budget reallocation direction; diminishing-returns curves | "Did this spend cause conversions that would not otherwise have happened?" — the only method that answers it |
| **Cannot answer** | Causality (correlational credit-splitting); anything untracked — view-through TV, dark social, word of mouth; anything post-ATT/cookie-loss | Fast tactical questions; campaign-level or creative-level effects; small channels (signal drowns); causality without experimental calibration | Everything at once — one test answers one channel/geo/period; long-term brand effects inside a short window |
| **Time to answer** | Real-time | Quarterly refresh typical; needs ~2-3 years of weekly history (Meridian/Robyn practitioner guidance) | 2–8 weeks per test |
| **Known bias** | Inherits every platform inflation mechanism above; digital-only tunnel vision | Model-specification risk; wide priors on collinear channels; analyst degrees of freedom | Power problems at low volume (Lewis & Rao 2015); geo spillover; novelty effects |
| **Trust for budget moves** | Never alone | Yes, when calibrated against lift tests | Yes — gold standard where powered |

Modern practice is triangulation: MMM as strategic backbone, incrementality tests to calibrate it, attribution for day-to-day steering only. Long-term brand effects are invisible to all short-window methods — that measurement trap is owned by `knowledge/frameworks/marketing-science/brand-activation-budget.md` (decay curves, 6-month minimum brand windows).

---

## Incrementality Test Design

### Platform conversion-lift tests (audience holdout, platform-run)
Meta/Google lift studies randomize users into exposed vs holdout using the ghost-ads pattern — identify the users who *would have been served* the ad in the control group, so the comparison is unbiased and intent-to-treat (Johnson, Lewis & Nubbemeyer 2017; the older PSA-holdout design is biased because delivery systems optimize PSAs differently). Cheapest first step for large accounts; the caveat is the platform runs the experiment on itself, and eligibility requires meaningful conversion volume. Cross-check results against your CRM system of record, not the platform's conversion count.

### Geo-holdout design (the workhorse)
Geo tests randomize markets, not users — immune to cookie loss, ATT, and cross-device tracking gaps. Meta's open-source **GeoLift** (augmented synthetic control) and Google's geo-experiment methodology are the standard free stacks.

1. **Pick the geo unit.** DMA or city for US; regions elsewhere. Units must have separable media delivery and minimal commuting/shipping spillover.
2. **Assemble pre-period history.** GeoLift's walkthrough does not fix a minimum; **heuristic: 6–12 months of daily/weekly geo-level KPI data, one full year when seasonality is material** (practitioner guidance — Lifesight, Triple Whale; marked heuristic).
3. **Select markets by simulation, not by hand.** Run `GeoLiftMarketSelection()` power simulations to find the test/control combination with the lowest minimum detectable effect (MDE) — the tool sweeps 2, 3, 4+ test-market combinations and holdout shares (GeoLift walkthrough). Manual "NY vs LA" matching is an anti-pattern.
4. **Check power before launching.** If simulated MDE exceeds the lift you plausibly expect (for most paid channels, a plausible true lift is single-digit to low-double-digit percent), redesign — bigger geos, longer test, bigger spend delta — or do not run. **Heuristic floor: ~100+ conversions per cell per analysis period; below that, expect noise** (unsourced heuristic, consistent with Lewis & Rao's power findings).
5. **Set duration ≥ one full purchase cycle** (GeoLift rule of thumb); **heuristic: 4–6 weeks for most DTC/lead-gen, longer for considered purchases**, plus a cooldown period to catch delayed conversions.
6. **Pre-register the decision.** Before launch, write down: metric (business KPI from the system of record, not platform conversions), test window, and the action at each outcome ("if incremental CPA > 2x blended CAC, cut channel 50%"). Post-hoc rationalization is how dead channels survive.
7. **Analyze with synthetic control, report the confidence interval,** never the point estimate alone. A "12% lift, CI −3% to +27%" is not a green light; it is an underpowered test.

**Dark test vs scale test:** turning spend *off* in holdout geos (dark test) measures the incrementality of existing spend and is free — the savings fund the analysis. Scaling spend *up* in test geos measures marginal return at higher budgets. Run dark tests on suspected-inflated channels (retargeting, brand search) first.

### Audience-holdout (DIY, owned channels + retargeting)
Randomly suppress 5–10% of the eligible audience (CRM list, site visitors) from email/SMS/retargeting for 4–8 weeks; compare purchase rate of held-out vs targeted in your own database (split size is a heuristic — larger holdout = faster answer, more short-term revenue at risk). This is the honest way to measure retargeting and lifecycle email, because randomization happens on your list before the platform's delivery optimization can select. Requires stable customer IDs and human approval before suppressing any live audience.

### The power reality (read before promising precision)
Lewis & Rao (*QJE* 2015), across 25 large advertiser experiments (~$2.8M spend, millions of users): individual sales volatility is so high relative to ad effects that the **median confidence interval on ROI exceeded ±50 points (over 100 points wide)**, and a well-powered ROI experiment can require tens of millions of person-weeks. Consequences: (a) small advertisers cannot measure channel ROI precisely — decide on cruder but honest signals (blended CAC trend, on/off pulses); (b) measure lift on conversions, not revenue-ROI, when volume is thin; (c) anyone selling you per-campaign incremental ROAS at $5K/month spend is selling noise.

---

## Self-Reported Attribution — The Triangulation Input

"How did you hear about us?" (HDYHAU) on high-intent forms catches what tracking cannot: dark social, word of mouth, podcasts, communities, AI-assistant recommendations. The published study that quantifies the gap is Refine Labs' 12-month comparison (620 declared-intent conversions, $21.5M closed-won ARR): software attribution credited **79% of conversions to web search** (direct/organic/paid), while customers named those sources only **~3%** of the time — self-reported answers pointed **98% of closed-won revenue to dark social** (social, podcast, word of mouth, community); podcasts alone self-reported at 53% of revenue vs 0% in software. Refine Labs calls this a ~90% measurement gap. Caveat: vendor-published, one company's pipeline — treat as directional evidence of the gap's existence and rough size, not a universal constant. The reconciliation: **software measures what captured demand; self-report measures what created it.** Both are true; they answer different questions.

Implementation rules:
- **Open text field first**, optional dropdown second — dropdowns anchor answers to the options you already believe in (Refine Labs self-reported-attribution implementation guidance).
- Place on the **highest-intent form** (signup, demo request, checkout), required or near-required; response rates collapse on post-purchase emails.
- **Known biases, state them when reporting:** recency bias (people name the last memorable touch), brand-salience bias (people name the famous channel — "Google" — over the actual source), and channel illiteracy ("I saw it online"). Self-report systematically *under*-credits retargeting and *over*-credits memorable content — roughly the mirror image of software bias, which is exactly why the pair triangulates.
- **Structural limits (SparkToro/Fishkin whiteboard):** HDYHAU only ever surfaces channels that already worked (it cannot find new ones), respondents don't know which "hear about us" moment you mean (first exposure vs final trigger), and it never reaches the people you failed to reach. Use it to triangulate, never as the sole planning input.
- Log to the CRM as a first-class field; report it side by side with software attribution, never averaged into it.

Dark-social pitfall context lives in `knowledge/playbooks/analytics-attribution.md` (Common Analytics Pitfalls).

---

## Decision Rules — Which Method at Which Spend Level

Heuristic synthesis (spend bands are judgment calls, not published thresholds — adjust for conversion volume, which matters more than dollars):

| Monthly paid spend | Primary measurement | Add | Do NOT |
|---|---|---|---|
| **< $10K** | Blended CAC trend + last-click UTMs + HDYHAU on every form | Crude on/off pulse tests (pause a channel 2–4 weeks, watch blended metrics) | Buy MTA software; quote per-channel ROAS as fact; run underpowered "lift tests" |
| **$10K–$50K** | Everything above + platform conversion-lift tests where volume qualifies | Brand-search shutoff test (cheapest high-value test in marketing); audience holdout on retargeting/email | Trust view-through conversions; compare ROAS across platforms |
| **$50K–$250K** | Geo-holdout program: 1–2 GeoLift tests per quarter on the largest channels, dark tests on suspected-inflated line items | Written experiment calendar; incrementality factors per channel (measured lift ÷ platform-claimed) applied to dashboards | Rebuild budget from an MTA model; leave retargeting untested for more than 2 quarters |
| **$250K+ (~$3M+/yr)** | MMM (Meridian/Robyn) refreshed quarterly, **calibrated against the incrementality test log** | Continuous test rotation across channels/geos; MMM-vs-experiment reconciliation as a standing review item | Run MMM without experimental calibration; let any single vendor own the truth |

The ~$3M+/yr MMM threshold aligns with practitioner guidance that below roughly $5–10M annual multi-channel spend the statistical signal for reliable MMM is often thin (Improvado/Matchbox MMM guides — vendor guidance, marked as such); teams with strong data and 2–3 years of weekly history can start lower.

---

## Kai Hard Rule — Channel-Credit Claims Must Carry Method + Bias

**Non-negotiable for every Kai report, audit, deck, or recommendation:** any statement crediting a channel with conversions, revenue, ROAS, CAC, or "performance" must name **(a) the measurement method and window, and (b) that method's known bias direction.** A bare "Meta ROAS: 3.2" fails quality review.

Required inline format:

```
Meta ROAS 3.2 [platform-reported, 7-day click + 1-day view; self-attributed —
overstates incremental return, does not dedupe against other channels]

Email drove 214 orders [last-touch UTM; captures demand capture, blind to
demand creation and dark social]

Geo test: brand search incremental conversions ≈ 0 [GeoLift dark test,
4 wks, 3 test DMAs, CI −4% to +6%; underpowered below 5% lift]
```

Companion rules:
- Numbers themselves follow the **Kai Data Provenance Rule** (collector-sourced, `harness/references/audit-data-provenance.md`); this rule adds the method-and-bias label on top.
- Recommendations to reallocate budget based on platform-attributed numbers alone are **blocked** — either cite a causal test or label the recommendation "directional, untested."
- When methods disagree (platform vs self-reported vs test), report the disagreement as a finding. Do not average, do not pick the flattering one.

---

## Anti-Patterns

- **ROAS shopping:** switching attribution settings or vendors until the number justifies the budget. The Gordon et al. results exist precisely because every observational method offers a different wrong answer.
- **Retargeting as proof-of-performance:** presenting the account's highest-ROAS line (retargeting) as the success story. It is the most credit-inflated line by construction.
- **The underpowered lift test:** running a 2-week geo test on a low-volume channel, getting a CI spanning zero, and reporting the point estimate as truth. Pre-launch power simulation or no test.
- **MMM as oracle:** quoting model coefficients without experimental calibration or intervals. An uncalibrated MMM is regression-flavored opinion.
- **Killing a channel on last-click alone:** top-of-funnel channels lose last-click credit structurally; the eBay lesson cuts both ways — test before scaling *and* before killing.
- **Ignoring the Uber tell:** if pausing a channel changes nothing in blended metrics after a fair window, the dashboard was lying, whatever the vendor says.

---

## How This Maps Into Kai

- **`kai-audit` / marketing audits, CRO audits, growth plans:** load this doc whenever channel performance claims appear; apply the Kai Hard Rule label format to every credited number; flag view-through share, retargeting ROAS, and brand-search spend as standard inflation-risk findings.
- **Reporting** (`scripts/reporting/weekly_report.py`, `ceo_deck.py`, campaign retrospectives via `scripts/campaigns/campaign_tracker.py`): channel tables must carry method-and-bias labels; the dashboard's "Revenue (attributed)" line in `analytics-attribution.md` templates inherits this rule.
- **Budget recommendations** (`agent/tasks/cmo_review.py` goal decomposition, campaign planning): reallocation across channels requires a causal source (lift test, geo test, calibrated MMM) or an explicit "directional, untested" label; brand/activation window doctrine comes from `brand-activation-budget.md`.
- **Test design requests:** use the geo-holdout and audience-holdout sequences above; every proposed test ships with a power statement and pre-registered decision rule; launching any test (pausing spend, suppressing audiences, dark geos) requires human approval per the approval doctrine.
- **Owned elsewhere:** attribution-model mechanics, UTM standards, GA4 setup, blended CAC, measurement ladder → `knowledge/playbooks/analytics-attribution.md`. Long/short measurement windows and ESOV → `knowledge/frameworks/marketing-science/brand-activation-budget.md`. Data provenance for client-facing numbers → `harness/references/audit-data-provenance.md`.

---

## Sources

- Gordon, Zettelmeyer, Bhargava & Chapsky — *A Comparison of Approaches to Advertising Measurement: Evidence from Big Field Experiments at Facebook* (Marketing Science, 2019): https://pubsonline.informs.org/doi/10.1287/mksc.2018.1135 (PDF: https://gwern.net/doc/statistics/causality/2019-gordon.pdf)
- Gordon, Moakler & Zettelmeyer — *Close Enough? A Large-Scale Exploration of Non-Experimental Approaches to Advertising Measurement* (2023): https://www.researchgate.net/publication/365364030_Close_Enough_A_Large-Scale_Exploration_of_Non-Experimental_Approaches_to_Advertising_Measurement
- Blake, Nosko & Tadelis — *Consumer Heterogeneity and Paid Search Effectiveness: A Large-Scale Field Experiment* (Econometrica, 2015): https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA12423 (NBER WP: https://www.nber.org/papers/w20171)
- Lewis & Rao — *The Unfavorable Economics of Measuring the Returns to Advertising* (QJE, 2015): https://academic.oup.com/qje/article-abstract/130/4/1941/1914592 (PDF: https://gwern.net/doc/economics/advertising/2015-lewis.pdf)
- Johnson, Lewis & Nubbemeyer — *Ghost Ads: Improving the Economics of Measuring Online Ad Effectiveness* (Journal of Marketing Research, 2017): https://journals.sagepub.com/doi/10.1509/jmr.15.0297 (SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2620078)
- WARC — *Uber's former performance chief charts extent of ad fraud* (Kevin Frisch): https://www.warc.com/newsandopinion/news/ubers-former-performance-chief-charts-extent-of-ad-fraud/44527
- CHEQ — *10 Crucial Lessons from the $6m Uber Ad Fraud Settlement*: https://cheq.ai/blog/10-crucial-lessons-from-the-6m-uber-ad-fraud-settlement/
- Refine Labs — *Study Confirms Measurement Gap in Software-Based Attribution* (12-month study: 79% vs ~3% web search, 98% dark social, podcast 53% vs 0%): https://www.refinelabs.com/article/hybrid-attribution-framework
- SparkToro (Fishkin) — *The 3 Big Problems with Asking "How Did You Hear About Us?"* (structural limits of HDYHAU — no gap statistics in this post): https://sparktoro.com/blog/the-3-big-problems-with-asking-how-did-you-hear-about-us-5-minute-whiteboard/
- Jon Loomer — *How Meta Ads Attribution Works in 2026*: https://www.jonloomer.com/meta-ads-attribution-2026/
- Meta Open Source — GeoLift walkthrough (market selection, power simulation, purchase-cycle duration rule): https://github.com/facebookincubator/GeoLift/blob/main/vignettes/GeoLift_Walkthrough.md
- Recast — *Open-Source Geo-Experiment Tools: A Head-to-Head Simulation Study*: https://research.getrecast.com/geolift-sim-study
- Lifesight — *Geo-Based Incrementality Testing: Marketer's Guide*: https://lifesight.io/blog/geo-based-incrementality-testing/
- Triple Whale — *GeoLift 101: Guide to Geo-Based Incrementality Testing*: https://www.triplewhale.com/blog/geolift-geo-based-incrementality-testing
- Improvado — *Marketing Mix Modeling Guide* (spend/history thresholds, vendor guidance): https://improvado.io/blog/what-is-marketing-mix-modeling-complete-guide
- The Matchbox — *Marketing Mix Modeling Guide* (MMM minimum-spend guidance): https://www.thematchbox.inc/resources/marketing-mix-modeling-guide
- Digital Applied — *MMM vs Attribution Playbook* (triangulation practice): https://www.digitalapplied.com/blog/marketing-mix-modeling-2026-mmm-vs-attribution-playbook
