# Experiment Rigor: Statistical Rules for Marketing Tests

> **Use when:** Sizing a test before launch, deciding whether a result is readable, judging a surprising win, reading segment breakdowns, choosing what to do when traffic can't support an A/B test, or scoring a backlog with ICE/RICE.
>
> This is the **stats layer** underneath three operational playbooks. Process and ledger fields live there, not here:
> - `knowledge/playbooks/experimentation-ledger.md` — how experiments get logged, promoted, and approved.
> - `knowledge/playbooks/creative-test-resolution-protocol.md` — kill/iterate/graduate decisions and media data floors.
> - `knowledge/playbooks/meta-creative-testing-decision-framework.md` — Meta budget reality checks and creative counts.

---

## Core Thesis: Your Prior Should Be "This Idea Fails"

Published data from companies running thousands of controlled experiments says most ideas do not work. At Microsoft, roughly one-third of well-built experiments improved their key metric, one-third made no statistically significant difference, and one-third made things worse. At Bing, only about 10–20% of proposed ideas produced positive results (Kohavi & Thomke, HBR 2017; Kohavi, Tang & Xu, *Trustworthy Online Controlled Experiments*, Cambridge 2020).

Two consequences:

1. **A "winner" claim carries the burden of proof.** With a 10–33% base rate of true wins, weak evidence plus enthusiasm mostly produces false positives.
2. **The system's value is the losers it catches.** An experiment program that never reports losses is not rigorous; it is broken. Use the ledger's "inconclusive" and "invalid" labels generously.

---

## Rule 1 — Fix the Read Before the Run (Sample Floors)

Declare before launch: hypothesis, primary metric, minimum detectable effect (MDE), sample floor, and read date. These become the `sample_floor` and `planned_read_date` fields in the experimentation ledger. A test without a pre-declared floor is opinion theater.

### The sizing formula

The standard rule of thumb for sample size per variant at 80% power and α = 0.05 (van Belle's rule, used throughout Kohavi, Tang & Xu):

```
n per variant ≈ 16 × σ² / δ²
```

where δ is the absolute effect you want to detect and σ² is the metric's variance. For a conversion rate p, σ² = p(1−p).

**Worked example.** Baseline landing-page CVR = 5%, you want to detect a 10% relative lift (δ = 0.005):

```
n ≈ 16 × (0.05 × 0.95) / 0.005² = 30,400 visitors per variant
```

At 2,000 visitors/week split two ways, that read is 30+ weeks away — this test should not run as an A/B test (see Rule 6).

### Conversion floor shortcut

Substituting δ = (relative lift × p) into the formula, the visitors cancel and you get an approximate **conversions-per-variant** floor that barely depends on the baseline rate (for small p):

```
conversions per variant ≈ 16 / (relative lift)²
```

| Relative lift you want to detect | Conversions needed per variant (approx.) |
|---|---|
| 50% | ~65 |
| 30% | ~180 |
| 20% | ~400 |
| 10% | ~1,600 |
| 5% | ~6,400 |

Decision rules:

- Read the table backwards: with the conversions you can realistically collect, what lift is detectable? If the answer is "only a 50%+ lift," say so in the ledger and design a bigger swing or an earlier signal metric.
- The creative-test protocol's `50+ conversions` floor is a **directional media floor**, not a significance floor — at 50 conversions per variant you can only statistically resolve lifts around 55–60% relative. Treat sub-floor reads as signal tests, per that protocol.
- **Run whole weeks.** Day-of-week and weekend effects cycle; Kohavi, Tang & Xu recommend a minimum of one full week and typically two, in full-week multiples, even when the sample floor is met earlier.

---

## Rule 2 — Peeking Invalidates Fixed-Horizon Stats

Classical p-values assume the sample size was fixed in advance. Checking the dashboard daily and stopping the moment p < 0.05 breaks that assumption: Evan Miller's simulations show stop-at-first-significance monitoring can push a nominal 5% false-positive rate above 25% (Miller 2010). Johari, Koomen, Pekelis & Walsh formalized this at KDD 2017: under realistic "check every day" behavior, fixed-horizon inference is severely inflated and unreliable (Johari et al. 2017).

**Bayesian dashboards do not automatically fix this.** Vendor marketing often claims Bayesian tests are peeking-immune; this is contested, and simulations show that stopping on a Bayesian "probability to be best" threshold is still optional stopping and still inflates false-positive rates in repeated use (Molas 2025). Posteriors stay interpretable under monitoring; a fixed stop-when-favorable threshold does not control error rates.

### What sequential testing actually requires

Legitimate early stopping needs a method built for it, chosen **before launch**:

| Method | What it is | Cost |
|---|---|---|
| Always-valid p-values (mSPRT) | p-values that hold at every moment; Optimizely's Stats Engine implements this (Johari et al., arXiv:1512.04922) | Wider intervals; needs more data than a fixed test for the same effect |
| Group-sequential / alpha spending | Pre-declared interim looks (e.g., at 25/50/75/100% of sample) with adjusted thresholds per look | Must fix the look schedule in advance |
| Fixed horizon | One read at the pre-declared sample floor | No early stop except for guardrail harm |

Decision rules:

- **Know what your platform computes.** If the testing tool uses fixed-horizon stats (most ad platforms and homegrown dashboards do), the only valid reads are (a) the pre-declared read date and (b) an early kill for guardrail harm — which you accept may be a false alarm.
- If the tool documents a sequential method (Optimizely, several modern engines), early calls at its stated confidence are legitimate. Log which regime applied in the ledger row.
- Never extend a finished test "to see if it reaches significance." That is peeking in reverse and has the same inflation problem.

---

## Rule 3 — Novelty and Primacy Effects

Both are threats to external validity (Kohavi, Tang & Xu, ch. 3; Sadeghi et al., arXiv:2102.12893):

- **Novelty effect:** a change is initially intriguing — engagement spikes, then decays as users return to habit. First-week wins on visible UI changes, subject-line gimmicks, and new ad formats are the classic case. Note this is distinct from paid-social **creative fatigue**, which the creative-test protocol handles as a control-validity problem.
- **Primacy effect:** the mirror image — experienced users initially do worse with a change (relearning cost), then improve. First-week losses on navigation, checkout-flow, and workflow changes may reverse.

Detection and decision rules:

1. **Plot the treatment effect by day.** A trending effect (up or down) means the point estimate at read time does not represent the long-run effect.
2. **Compare early cohorts over time.** Take users first exposed on day 1–2 and track their treatment effect across the window; decay indicates novelty (Kohavi, Tang & Xu).
3. Do not read habit-sensitive changes in under two full weeks.
4. For changes intended to alter long-run behavior (pricing display, subscription flows, major redesigns), keep a **long-term holdout** — a small control group held for weeks or months — before promoting the lesson to memory (Sadeghi et al. 2021).
5. New-user segments are novelty-immune (they have no prior habit): if the lift exists only for returning users and decays, suspect novelty.

---

## Rule 4 — Twyman's Law: Surprising Results Are Usually Errors

"Any figure that looks interesting or different is usually wrong." Kohavi's teams found that extreme or shocking results were far more often instrumentation and design bugs than breakthroughs (Kohavi & Longbotham, *Unexpected Results in Online Controlled Experiments*, SIGKDD Explorations 2010; Kohavi, Tang & Xu, ch. 1).

Before believing any surprising result — good or bad — run this checklist:

1. **Sample ratio mismatch (SRM).** If the split was designed 50/50, check the actual counts with a chi-square test. Even a small skew (e.g., 50.2/49.8 at scale) signals broken assignment, redirects, or bot filtering, and **invalidates the experiment** (Kohavi, Tang & Xu).
2. **Instrumentation.** Did tracking fire equally in both arms? Pixel/CAPI changes, consent banners, ad blockers, and redirect latency routinely create fake lifts.
3. **Bots and outliers.** Robot traffic and a single whale order can flip a mean-based metric (Kohavi et al., *Seven Pitfalls*, KDD 2009). Re-read with bots excluded and revenue capped.
4. **Attribution window and lag.** Conversions arriving after the read window undercount the newer arm.
5. **Replicate.** The cheapest cure for an unbelievable win is rerunning the test. A true effect replicates; a bug or fluke usually does not.

Ledger tie-in: surprising results enter the ledger as `retest` or `invalid` until this checklist passes — never straight to `win`.

---

## Rule 5 — Simpson's Paradox in Segment Reads

A treatment can win in every segment yet lose overall — or win overall yet lose in every segment — whenever traffic is unevenly split across segments with different baseline rates. Kohavi documented this in real experiments, especially during **ramp-up**: results pooled across a 1%-traffic phase and a 50%-traffic phase weight the phases wrongly and can reverse the true winner (Kohavi & Longbotham, *Unexpected Results*, SIGKDD Explorations 2010).

Decision rules:

1. **Never pool across ramp phases.** Read only the data from the final allocation, or analyze phases separately.
2. **Segments generate hypotheses, not shipping decisions** (Optimizely guidance). A post-hoc "it won on mobile!" read is both multiple-comparison-inflated and Simpson-vulnerable.
3. Pre-register at most 2–3 segments that have a causal story. With 10 unplanned segments at α = 0.05, expect at least one false "significant" segment by chance alone.
4. A segment finding ships only after a follow-up experiment targeted at that segment confirms it.

---

## Rule 6 — When A/B Testing Is Impossible (Low Traffic)

Run the Rule 1 math first. **If the required sample takes more than ~8 weeks to collect, do not run the A/B test** — seasonality, fatigue, and drift will corrupt the read before it matures. Switch methods instead of lowering standards (CXL, *A/B Testing Alternatives*):

| Method | What it is | Use when | Weakness |
|---|---|---|---|
| **Bigger swings** | Test radical page/offer changes, not button colors — larger true effects need far fewer conversions (Rule 1 table) | Always the first move on low traffic | Can't attribute the win to one element |
| **Earlier signal metrics** | Read qualified clicks, form starts, call clicks instead of purchases | Conversion volume too low; see the Meta framework's budget reality check | Proxy may not correlate with revenue — validate periodically |
| **Painted-door test** | Ship the button/link/offer promise only; measure clicks on the not-yet-built thing | Demand validation before building | Measures interest, not satisfaction; brief user apology/waitlist required |
| **Sequential cohorts (pre/post)** | Run A for a period, then B; compare cohorts | Site-wide changes that can't be split | Time confounds (seasonality, promos, news) — never compare across a holiday boundary |
| **Pre/post with controls (diff-in-diff / interrupted time series)** | Model the pre-period trend with an untouched control series (another page, region, or product line); measure deviation after the change | You have stable history and a comparable control | Needs multiple pre-period data points and a truly untouched control (ITS methodology: Hudson et al. 2019) |
| **Geo experiments** | Assign matched regions to treatment/control; measure incrementality between them | Offline channels, brand spend, channels without user-level splits (Wayfair tech blog) | Needs enough comparable geos; spillover between regions |
| **Qualitative + heuristic review** | Moderated user tests, session recordings, five-second tests | Understanding *why* before betting the traffic | Not a quantitative read; feeds hypotheses, not verdicts |

Log all of these in the experimentation ledger with `confidence: low/medium` — quasi-experimental reads never earn the confidence of a randomized read, and their limitations field must name the confound risks.

---

## Rule 7 — Prioritization Scoring (ICE/RICE) and Its Failure Modes

**ICE** (Sean Ellis): score Impact × Confidence × Ease, each 1–10. **RICE** (Sean McBride, Intercom): (Reach × Impact × Confidence) / Effort — adds Reach so a change on a high-traffic page outranks the same change on a dead page (Growth Method; Railsware).

Known failure modes — correct for each explicitly:

| Failure mode | What happens | Kai correction |
|---|---|---|
| Feelings dressed as integers | Three scorers, three different Impact/Confidence numbers | One named scorer per batch; score definitions written down; re-score quarterly |
| Confidence inflation | Enthusiasm becomes a 9/10 confidence | Tie confidence to evidence tier: 10 = our own prior experiment; 7 = strong published evidence; 5 = qualitative signal; ≤3 = opinion. Opinion-only ideas cap at 3 |
| Reach ignores intensity | One-time reach of 1M scores over daily reach of 1K power users | Score reach as exposures per quarter, not unique users |
| No cost of delay | A time-sensitive idea scores the same as an evergreen one | Add a deadline flag outside the score; deadline items bypass rank order with owner approval |
| Score worship | The spreadsheet decides; nobody re-examines inputs | Scores order the backlog; a human approves the run order (approval doctrine applies) |
| Low-traffic blindness | Ease-heavy small tests win the ranking but can never reach a read | On low-traffic properties, weight Impact and Confidence over Ease — each test slot is expensive (CXL) |

Given the base rates in the Core Thesis, Confidence is the highest-information input: calibrate it against your own ledger's historical win rate, not gut feel.

---

## Anti-Patterns (Quick Reject List)

- Calling a test at p < 0.05 on day 2 of a planned 14-day run (Rule 2).
- Shipping a first-week engagement spike on a visible UI change without a decay check (Rule 3).
- Believing a 40% lift without an SRM and instrumentation check (Rule 4).
- Shipping to mobile because a post-hoc mobile segment "won" (Rule 5).
- Running a 30-week A/B test instead of switching methods (Rule 6).
- A backlog where every idea has Confidence 8+ (Rule 7).
- Pooling ramp-up data with full-allocation data (Rule 5).

---

## How This Maps Into Kai

| Kai surface | Loads this doc for |
|---|---|
| `knowledge/playbooks/experimentation-ledger.md` | The statistical meaning of `sample_floor`, `confidence`, and when `result` may be read as win/loss vs. inconclusive |
| `knowledge/playbooks/creative-test-resolution-protocol.md` | Why its data floors are directional, and what lift sizes those floors can actually resolve (Rule 1 table) |
| `knowledge/playbooks/meta-creative-testing-decision-framework.md` | Statistical grounding for the budget reality check and earlier-signal downgrade (Rules 1, 6) |
| `kai-cro` / CRO recommendations | Whether a proposed test is readable on the site's traffic; which Rule 6 alternative to recommend instead |
| `kai-retro` / 30-day content checks | Twyman screening and novelty screening before a winner feeds `knowledge/playbooks/what-works.md` |
| Campaign planning / goals review | RICE scoring with the corrected confidence tiers when decomposing behind-pace goals into test backlogs |

Approval doctrine: every live-channel action this doc informs — launching, stopping, extending, or scaling a test on a real ad account, site, or email list — requires human approval first. Statistical validity is necessary, never sufficient, to ship.

---

## Sources

- Kohavi, Tang & Xu, *Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing* (Cambridge, 2020) — https://assets.cambridge.org/97811087/24265/frontmatter/9781108724265_frontmatter.pdf
- Kohavi & Thomke, "The Surprising Power of Online Experiments," *Harvard Business Review* (2017) — https://hbr.org/2017/09/the-surprising-power-of-online-experiments
- Kohavi & Longbotham, "Unexpected Results in Online Controlled Experiments," *SIGKDD Explorations* 12(2) (2010) — https://kdd.org/exploration_files/v12-02-8-UR-Kohavi.pdf
- Crook, Frasca, Kohavi & Longbotham, "Seven Pitfalls to Avoid when Running Controlled Experiments on the Web," KDD 2009 — https://www.exp-platform.com/Documents/2009-ExPpitfalls.pdf
- Kohavi et al., "Trustworthy Online Controlled Experiments: Five Puzzling Outcomes Explained," KDD 2012 — https://exp-platform.com/Documents/puzzlingOutcomesInControlledExperiments.pdf
- Johari, Koomen, Pekelis & Walsh, "Peeking at A/B Tests: Why It Matters, and What To Do About It," KDD 2017 — https://doi.org/10.1145/3097983.3097992
- Johari, Pekelis & Walsh, "Always Valid Inference: Bringing Sequential Analysis to A/B Testing," arXiv:1512.04922 — https://arxiv.org/abs/1512.04922
- Miller, "How Not To Run an A/B Test" (2010) — https://www.evanmiller.org/how-not-to-run-an-ab-test.html
- Molas, "Bayesian A/B testing is not immune to peeking" (2025) — https://www.alexmolas.com/2025/10/30/bayesian-ab-test-peeking.html
- Sadeghi et al., "Novelty and Primacy: A Long-Term Estimator for Online Experiments," arXiv:2102.12893 — https://arxiv.org/pdf/2102.12893
- Optimizely, "Simpson's Paradox: Discover possibilities with your segments, not shipping decisions" — https://support.optimizely.com/hc/en-us/articles/18208725352589-Simpson-s-Paradox-Discover-possibilities-with-your-segments-not-shipping-decisions
- CXL, "A/B Testing Alternatives for Low-Traffic Websites" — https://cxl.com/blog/ab-testing-alternatives/
- Wayfair Tech Blog, "How Wayfair Uses Geo Experiments to Measure Incrementality" — https://www.aboutwayfair.com/careers/tech-blog/how-wayfair-uses-geo-experiments-to-measure-incrementality
- Hudson, Fielding & Ramsay, "Methodology and reporting characteristics of studies using interrupted time series design in healthcare," *BMC Medical Research Methodology* (2019) — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6609377/
- Growth Method, "ICE Framework" and "RICE Framework" — https://growthmethod.com/ice-framework/ · https://growthmethod.com/rice-framework/
- Railsware, "How to Prioritize with the RICE Framework" — https://railsware.com/blog/rice-framework/
