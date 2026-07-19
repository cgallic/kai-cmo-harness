# Growth Metrics & PMF: Instrumentation, North Star Selection, and Fit Verification

> **Use when:** Setting up measurement for a new product or channel, choosing a North Star Metric, deciding whether a business has product-market fit before recommending growth spend, reading a retention curve or cohort table, or building a stage-appropriate dashboard.
>
> This is the **measurement-architecture layer** underneath two operational playbooks. Metric formulas, SaaS benchmarks, and dashboard templates live there, not here:
> - `knowledge/playbooks/saas-metrics-guide.md` — MRR waterfall, churn/NRR/CAC/LTV formulas, benchmarks by funding stage, board dashboard.
> - `knowledge/playbooks/growth-loops-applied.md` — loop archetypes and loop-health measurement.

---

## Core Thesis: Measure Fit Before You Fund Growth

Most growth-metric mistakes are sequencing mistakes: teams optimize acquisition metrics on a product that does not retain, or pick a revenue North Star that lags the customer value creating it. The correct order is (1) instrument the full funnel, (2) verify fit with behavior (retention curves), triangulated with sentiment (PMF survey), (3) only then select a North Star and scale the loops that feed it. Spending against a leaky product just measures the leak faster.

---

## 1. Pirate Metrics (AARRR) — Per-Stage Instrumentation

Dave McClure introduced AARRR in his 2007 "Startup Metrics for Pirates" talk as an antidote to vanity metrics — five customer-lifecycle stages, each with its own conversion question (McClure 2007; Mind the Product).

| Stage | Question | Example metrics | Instrument (events to log) | Classic failure |
|---|---|---|---|---|
| **Acquisition** | How do people find us? | Visits by channel, CTR, CPC, signup rate by source | UTM-tagged landing event, `signup_started`, `signup_completed` with source attribution | Reporting blended signups; channel mix hides which source retains |
| **Activation** | Do they reach first value? | % of signups completing the key action within a timeframe (see activation examples in `saas-metrics-guide.md`) | `activation_event` — one named action, one deadline (e.g., "first project created within 24h") | Defining activation as "logged in" instead of a value moment |
| **Retention** | Do they come back? | Cohort retention at the product's natural frequency, DAU/MAU, resurrection rate | Recurring `key_action` event with user + cohort date; never rely on logins | Measuring at the wrong frequency (daily retention for a monthly-use product) |
| **Referral** | Do they bring others? | Invite rate, invite→signup conversion, viral/loop cycle metrics (owned by `growth-loops-applied.md`) | `invite_sent`, `invite_accepted`, artifact-share events | Counting shares without tracking whether shared artifacts convert |
| **Revenue** | Do they pay? | Trial→paid, ARPU, expansion (formulas in `saas-metrics-guide.md`) | `checkout_started`, `subscription_created`, `upgrade`, `downgrade`, `cancel` | Celebrating top-line MRR while cohort revenue decays |

Decision rules:

1. **One metric per stage on the operating dashboard.** AARRR's job is diagnosis, not exhaustiveness — when growth slows, walk the stages in order using the diagnostic tree in `saas-metrics-guide.md` ("Growth is slowing").
2. **Instrument before you optimize.** Every stage needs a named event with a timestamp and an attribution property. A stage you cannot segment by cohort is a stage you cannot diagnose.
3. **Order of optimization is not the order of the acronym.** The RARRA critique (Mind the Product) holds: fix Retention and Activation before scaling Acquisition. Acquisition spend on an unretentive product buys churn.
4. **Conversion rates between stages, not absolute counts.** Absolute counts are vanity by default; McClure's original point was that stage-to-stage conversion is what you can act on.

---

## 2. North Star Metric Selection

A North Star Metric (NSM) is the single metric the whole company aligns on — defined in Amplitude's North Star Playbook (Cutler & Scherschligt) as a metric that (a) expresses the value customers get, (b) sits within the team's sphere of influence, and (c) leads revenue rather than reporting it.

### The three-test selection method

Run every candidate through all three. Two of three is a supporting metric, not a North Star.

**Test 1 — Value proxy.** If this number goes up, did customers necessarily receive more value? "Weekly active users" fails for a product whose value is output, not visits; "messages sent" (Slack), "nights booked" (Airbnb), "weekly learners completing a lesson" pass because the metric *is* the value event, counted.

**Test 2 — Leading, not lagging.** Revenue, MRR, and LTV are lagging outcomes — they confirm value that was delivered months ago. A good NSM predicts revenue ahead of time. Cutler's inversion test: "If you can move your North Star directly, it's probably not a good North Star" (Amplitude) — teams should move it only through **input metrics** (3–5 drivers they can act on directly, e.g., breadth × frequency × depth of the value action).

**Test 3 — Counter-metric pairing.** Every NSM gets at least one paired metric measuring the damage its pursuit could cause. This is Andy Grove's paired-indicators principle from *High Output Management*: indicators steer attention like a bicycle steers where you look, so pair effect with counter-effect (Grove; Holistics).

| North Star candidate | Gaming risk | Counter-metric to pair |
|---|---|---|
| Weekly active users | Notification spam inflates opens | Unsubscribe/notification-disable rate |
| Content published per week | Volume over quality | 30-day winner rate (`what-works.md` feed) |
| Trials started | Junk trials from broad ads | Trial→paid conversion |
| Messages/actions per user | Dark-pattern engagement | Session-level task completion, churn |
| Leads captured | Form-gating everything | Lead→qualified rate, bounce rate |

### Disqualified candidates

- **Revenue as NSM** — lagging (fails Test 2); acceptable only as the outcome the NSM is validated against.
- **Cumulative anything** ("total registered users") — can never go down, so it cannot inform decisions; classic vanity metric (Amplitude, Cutler).
- **Averages across mixed populations** — hide segment decay; use cohorted medians or rates.

**Worked example.** A phone-led local-services client (KaiCalls fit profile): candidate NSM "calls answered" fails Test 1 (an answered spam call is not value). "Qualified calls converted to booked jobs per week" passes all three — it is the value event (Test 1), it leads revenue by weeks (Test 2), and it pairs with counter-metrics "missed-call rate" and "caller complaint rate" (Test 3). Inputs: call-answer rate, after-hours coverage, qualification accuracy.

---

## 3. The PMF Survey (Sean Ellis Test)

### Protocol

1. Ask users one question: **"How would you feel if you could no longer use [product]?"** — answers: *Very disappointed / Somewhat disappointed / Not disappointed*.
2. Survey people who have **experienced the core product recently** (used it at least twice, within the last two weeks) — not raw signups, not only power users.
3. Read the % answering "very disappointed." Rahul Vohra's Superhuman team treated ~40 responses as the floor for a meaningful read (First Round Review).
4. Re-run quarterly and segment the result (by persona, plan, acquisition channel) — a blended score hides which segment has fit.

### The 40% benchmark — origin

Sean Ellis developed the method by running the question across the many startups he advised and benchmarked (roughly a hundred, per First Round) and observing a dividing line: companies above roughly **40% "very disappointed"** grew relatively easily with strong word-of-mouth; those below struggled to grow regardless of tactics (Ellis, pmfsurvey.com; Fitsignal). Superhuman is the canonical application: they started at 22%, segmented on why "somewhat disappointed" users held back, rebuilt the roadmap around the high-expectation user's objections, and reached 58% (Vohra, First Round Review 2019).

### The critics — and how to use the test anyway

The 40% rule is contested. Treat these as real limits, not footnotes:

- **Response bias.** Only engaged users answer surveys; the disengaged already left. Buffer surveyed an ultra-engaged group, scored 78%, and the broader base still retained poorly (Fitsignal). Mitigation: sample by cohort, not by newsletter list, and report the response rate next to the score.
- **The threshold is a heuristic, not a law.** 40% came from one practitioner's benchmark set; categories sit naturally higher (daily-use tools) or lower (infrequent-purchase products). A 38% is not failure and a 42% is not proof (Fitsignal; Learning Loop).
- **Self-report vs behavior.** People overstate attachment. A 45% score with a retention curve declining to zero is a false positive — behavior wins (Lenny's Newsletter; leanb2bbook).
- **It can lag segment shifts.** Scores routinely drop as a company broadens beyond its early-adopter niche — that is a targeting signal, not necessarily product decay (Fitsignal).

**Kai decision rule:** the survey is a cheap **leading, directional** instrument — use it pre-retention-data and for segment discovery (the Superhuman "somewhat disappointed" mining move). Never certify PMF on the survey alone; certify on the retention curve below. If survey and retention disagree, trust retention.

---

## 4. Retention-Curve Reading

Plot, per acquisition cohort, the % of users still doing the **key value action** at its **natural frequency** over time. Both choices matter: measuring logins instead of the value action, or daily retention for a weekly-use product, produces unreadable curves.

### The three shapes

| Shape | Reading | Action |
|---|---|---|
| **Declines toward zero** | No PMF — nobody finds durable value | Stop scaling acquisition; return to activation and product work |
| **Flattens at a plateau** | PMF for the segment on the plateau — a group finds long-term value (Balfour) | Identify who plateaus; concentrate acquisition on lookalikes of that segment |
| **Newer cohorts flatten higher than older ones** | Fit is improving — product/onboarding changes are working | Keep shipping; protect whatever changed between cohorts |

Brian Balfour's rule: a retention curve that flattens means you have probably found product-market fit *for some market* — the plateau height tells you how big the fit is (brianbalfour.com). Casey Winters sharpens it into a two-part test: **PMF = a flattened retention curve of the key action at its natural frequency, plus month-over-month growth in new users** (caseyaccidental.com). The second clause matters — a flat curve over a shrinking top of funnel is a lifestyle niche, not fit that supports growth.

Decision rules:

1. **Where the curve flattens is the fit boundary.** A curve flattening at 30% means 70% of acquisitions were mis-targeted or mis-activated — that is the acquisition-quality and activation backlog.
2. **A cliff at a specific period is an event, not a trend.** Month-3 cliffs often map to billing renewals or onboarding-credit expiry; diagnose the event before touching the product.
3. **Wait for the curve to mature.** Early points on a young cohort's curve are noisy; do not call flattening until at least 2–3× the natural frequency has elapsed. Novelty effects inflate early points (see `experiment-rigor.md`, Rule 3).

---

## 5. Cohort Analysis Basics

The revenue-cohort worked example and "what to look for" list live in `saas-metrics-guide.md` — this section owns the reading method.

- **Cohort types.** Acquisition cohorts (grouped by start date) answer *when* retention changed; behavioral cohorts (grouped by an action taken, e.g., "invited a teammate in week 1") answer *why* — compare a behavior cohort's curve against the baseline to find candidate activation levers (Amplitude). Behavior cohorts generate hypotheses; confirm causality with an experiment (`experiment-rigor.md`).
- **N-day vs unbounded retention.** N-day (bounded) retention counts a user as retained only if active in period N exactly — right for products with an expected usage rhythm (most SaaS) and for onboarding reads. Unbounded retention counts a user as retained if they return *at any point after* period N — right for infrequent, transactional, or consumer products (Amplitude; Lenny's Newsletter/Berezovsky). Declare which one a chart uses; the two are not comparable.
- **Reading the triangle.** In the standard cohort table (rows = cohorts, columns = periods): read **across a row** to see one cohort age (find the flattening point); read **down a column** to compare cohorts at the same age (find whether the product is improving); the **diagonal** is calendar time (find seasonality and one-off events).
- **Pitfalls.** (1) Partial periods — the newest cohort's latest cell is incomplete; grey it out. (2) Small cohorts — percentage swings on a 12-user cohort are noise; set a minimum cohort size before reading. (3) Mixed populations — a "stable" blended curve can hide a decaying segment offset by a growing one; segment before concluding. (4) Averaging across cohorts of different ages weights old cohorts arbitrarily.

---

## 6. Which Metrics Matter by Stage

Stage benchmarks (growth rates, churn, LTV:CAC by funding stage) live in `saas-metrics-guide.md`; this table is about **which instruments to even look at**.

| | Pre-PMF | Growth (post-PMF) | Scale |
|---|---|---|---|
| **Primary question** | Does anyone need this repeatedly? | Which loops compound fastest? | Is the machine efficient and durable? |
| **Metrics that matter** | Retention curve of the key action; activation rate; PMF survey score by segment; qualitative "why" | North Star + input metrics; per-stage AARRR conversion; loop cycle metrics (`growth-loops-applied.md`); CAC payback by channel | NRR, LTV:CAC, burn multiple, Rule of 40 (`saas-metrics-guide.md`); counter-metrics; brand/category share |
| **Metrics to ignore** | Revenue growth, CAC optimization, share of voice — premature | Blended vanity totals; board-only lagging metrics as daily steering | Raw signup counts; any un-cohorted average |
| **PMF instruments** | Survey (leading) + early cohort curves | Curve flattening confirmed; watch newer-cohort plateaus as segments broaden | Per-segment retention — PMF erodes segment by segment, and NRR is the early warning |
| **Failure mode** | Scaling spend on an unflattened curve | North Star gaming without counter-metrics | Optimizing lagging metrics while leading indicators decay |

---

## Anti-Patterns (Quick Reject List)

- Recommending acquisition spend before seeing a retention curve (Core Thesis).
- A North Star the team can move directly, or with no counter-metric paired (Section 2).
- Certifying PMF from a survey score alone, or from a survey sent only to fans (Section 3).
- Calling a curve "flat" before 2–3 natural-frequency periods have elapsed (Section 4).
- Comparing an N-day retention chart against an unbounded one (Section 5).
- A single blended dashboard number where a cohorted, segmented read exists (Sections 4–5).
- Stage mismatch: Rule-of-40 talk pre-PMF, or PMF-survey theater at scale (Section 6).

---

## How This Maps Into Kai

| Kai surface | Loads this doc for |
|---|---|
| `knowledge/playbooks/saas-metrics-guide.md` users (dashboards, investor reporting) | The framework layer above the formulas: NSM selection, stage-appropriate metric choice, cohort reading method |
| `knowledge/playbooks/growth-loops-applied.md` / growth-loop design | Verifying fit (Sections 3–4) before designing loops; NSM + inputs as the loop's output metric |
| `kai-audit` / marketing audits, growth plans | The stage table (Section 6) to match recommendations to the client's actual stage; refusing acquisition recommendations pre-fit |
| `kai-cro` / CRO work | Activation-metric definition (Section 1) and behavior-cohort hypothesis generation (Section 5) |
| Goals & weekly CMO review (`scripts/harness_cli.py goals`) | Choosing goal KPIs that pass the three NSM tests and carry a counter-metric |
| `knowledge/playbooks/growth-hacker-first-hire-os.md` | What the first growth hire should instrument, in what order |
| Audit provenance rule | Every retention %, survey score, or cohort figure in client-facing work must come from collected data (`harness/references/audit-data-provenance.md`) — never from this doc's examples |

Approval doctrine: this doc informs analysis and recommendations only. Any live-channel action it motivates — launching surveys to a client's user base, changing ad spend, modifying tracking on a production site — requires human approval first.

---

## Sources

- Dave McClure, "Startup Metrics for Pirates: AARRR!" (2007 talk) — https://www.youtube.com/watch?v=irjgfW0BIrw
- Mind the Product, "AARRR vs RARRA: Pirate Metrics Explained" — https://www.mindtheproduct.com/aarrr-vs-rarra-pirate-metrics-explained/
- Amplitude, *The North Star Playbook* (John Cutler & Jason Scherschligt) — https://info.amplitude.com/rs/138-CDN-550/images/Amplitude-The-North-Star-Playbook.pdf
- Amplitude, "What Makes a Good vs Bad North Star Metric" — https://amplitude.com/blog/good-bad-north-star-metric
- Amplitude, "About the North Star Framework" — https://amplitude.com/books/north-star/about-north-star-framework
- Andrew Grove, *High Output Management* — paired-indicators principle; summary: Holistics, "Beware What You Measure: The Principle of Pairing Indicators" — https://www.holistics.io/blog/beware-what-you-measure-the-principle-of-pairing-indicators/
- Sean Ellis & GoPractice, Product/Market Fit survey — https://pmfsurvey.com/
- First Round Review, "How Superhuman Built an Engine to Find Product-Market Fit" (Rahul Vohra, 2019) — https://review.firstround.com/how-superhuman-built-an-engine-to-find-product-market-fit/
- Fitsignal, "The Sean Ellis 40% Test: The Ultimate Guide" (origin, Buffer 78% case, threshold critique) — https://www.fitsignal.com/blog/sean-ellis-40-percent-test
- Learning Loop, "Product-Market Fit Survey Guide" — https://learningloop.io/plays/product-market-fit-survey
- Brian Balfour, "The Never Ending Road To Product Market Fit" — https://brianbalfour.com/essays/product-market-fit
- Casey Winters, "Casey's Guide to Finding Product/Market Fit" — https://www.caseyaccidental.com/p/caseys-guide-to-finding-product-market-fit
- Lenny's Newsletter, "How to know if you've got product-market fit" — https://www.lennysnewsletter.com/p/how-to-know-if-youve-got-productmarket
- Olga Berezovsky (Lenny's Newsletter), "How to measure cohort retention" (N-day vs unbounded) — https://www.lennysnewsletter.com/p/measuring-cohort-retention
- Amplitude, "What Is Cohort Retention Analysis" — https://amplitude.com/explore/analytics/cohort-retention-analysis
- Lean B2B, "How to Evaluate Product/Market Fit by Analyzing Retention Cohorts" — https://leanb2bbook.com/blog/retention-cohorts-product-market-fit/
