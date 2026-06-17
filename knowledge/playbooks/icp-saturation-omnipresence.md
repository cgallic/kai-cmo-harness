# ICP Saturation and Omnipresence Playbook

> **Use when:** You want a defined set of buyers to feel like your brand "sprang up out of nowhere and is suddenly everywhere." Best for a narrow, nameable ICP (a few hundred to a few thousand accounts/people) where you can saturate cheaply rather than buy mass reach. Pairs with `account-based-marketing.md`, `demand-generation.md`, and `surround-sound-llm-manipulation.md`.

This playbook is executable: every channel section gives the exact targeting controls, minimum audience sizes, current budget floors, and the break-even where the tactic stops working. Platform specs are current as of **mid-2026** and drift fast — verify each number in-product before you commit budget (see Data Provenance, last section).

---

## The Honest Thesis (read this before you spend a dollar)

"Omnipresence" for a tight ICP is mostly a **perception you manufacture**, not reach you buy. Three psychology effects do the work, and they are cheap precisely because the audience is small:

| Effect | What it does | Citation |
|--------|--------------|----------|
| **Mere-exposure** | Repeated exposure raises liking with no other input. Stronger when the viewer does not consciously notice the repetition. | Zajonc 1968; Bornstein 1989 meta-analysis (r ≈ 0.26, larger under low awareness) |
| **Illusory-truth** | Repetition raises *believed* truth — even for claims the person knows are shaky ("knowledge neglect"). | Hasher/Goldstein/Toppino 1977; Fazio et al. 2015 |
| **Frequency illusion** | Once noticed, a brand *seems* to be everywhere though its real visibility never changed. Retargeting weaponizes this. | Zwicky 2005 ("frequency illusion" / Baader-Meinhof) |

The mechanic that makes it affordable: **Impressions = Reach × Frequency.** Shrink reach and the same budget buys more frequency per person. A $500 spend at a $5 CPM buys 100,000 impressions. Against 50,000 people that is a frequency of 2. Against 5,000 people it is a frequency of 20 — for the same money. Narrow the pool and "everywhere" becomes free.

**Be unmistakable in one place, adequately findable in two or three others.** Your ICP lives on maybe two platforms. Saturating those reads as "everywhere"; buying every channel at once is how small brands waste budgets.

---

## Adversarial Pre-Mortem — why this backfires

Run this list before planning. Each item is a documented failure mode with the number that triggers it.

1. **You confuse perceived ubiquity with growth.** The rigorous growth science (Ehrenberg-Bass mental availability; Binet & Field ESOV; LinkedIn's 95-5 rule — ~95% of category buyers are out-market at any moment) says real revenue growth comes from *broad reach into out-market buyers*, not stacked frequency on a tiny pool. Narrow-ICP saturation manufactures brand-*feel* and trust inside a segment. Sell it internally as exactly that. Do not promise it will grow the category footprint.
2. **Frequency fatigue inverts the gains.** Retargeting CPM inflates ~25%+ once average frequency passes ~3.5. On CTV, more than ~10 exposures *reduces* purchase intent. On LinkedIn, swap creative when weekly frequency clears 4-5 or CTR falls. Saturation without creative rotation reads as desperation.
3. **Account-level budget pools on the wrong 20%.** LinkedIn caps frequency only per *person* (2/day), with no account-level control — so ~80% of budget hits ~20% of accounts and the rest never see you. Without account-capping tooling, 75-85% of your target list is invisible while a handful get spammed.
4. **Outbound saturation burns your domains.** Past ~30 cold emails/inbox/day, or spam complaints above 0.3%, you torch sender reputation. Saturation outbound needs separate domains, warmup, and rotation — not volume on your primary domain.
5. **The vanity billboard.** A single static board near one HQ hits everyone who passes; for a 200-person ICP, 99% of impressions are waste. Geofence-retargeting needs ~2,000 captured devices to be usable and breaks down (CPMs 2-3x, delivery 15-20%) below ~10,000 reachable users. One mid-size office rarely clears that floor.
6. **CTV's account targeting is mostly probabilistic guessing.** Independent benchmarking (CIMM/Truthset) put IP-to-household links at ~13-16% accuracy; FreeWheel warned IP targeting can miss up to 87% of households. A $1 media buy can be worth $0.09 once that error corrupts downstream matching. Only deterministic ISP-matched inventory (~95%) escapes this, and it is a smaller, pricier subset.
7. **Audio cannot target firmographics and cannot be clicked.** Self-serve audio targets genre/demographics, never job title or company. Conversions surface as direct/organic. It is a brand layer, not lead-gen, and only pays back above ~$2-3K ACV with working attribution.
8. **Attribution self-deception.** Self-reported attribution is *directional, not causal*. It is the best dark-funnel signal you have, but treating "how did you hear about us" answers as incremental proof will mislead budget decisions.

If two or more of these apply and you cannot mitigate them, narrow the plan rather than widen the spend.

---

## The Saturation Equation (quick reference)

```
PERCEIVED OMNIPRESENCE = (tight ICP) × (few channels they trust) × (high frequency) × (consistent creative)

  Step 1  Define + tier the ICP            → smallest viable, highest-intent pool
  Step 2  Pick 1 hub + 2-3 support channels → where THIS ICP already is
  Step 3  Concentrate spend (burst, daypart, geo, account-cap) → frequency rises for free
  Step 4  Run ONE pillar → atomize to all channels → consistent, recognizable creative
  Step 5  Orchestrate trigger → play across ads + outbound + social, simultaneously
  Step 6  Measure the dark funnel (self-reported + engaged accounts), not last-touch
```

Budget math you will reuse:
- **Burst to threshold:** 5,000 reach × frequency 6 = 30,000 impressions × $40 CPM = **$1,200**. The same reach at frequency 2 (always-on) buys 10,000 impressions ($400) and never crosses the effective-frequency line. Burst wins on small, finite audiences.
- **ABM per-account:** 100 accounts × 8 buying-committee contacts × frequency 6/week × 4 weeks = 19,200 impressions × $45 CPM = **$864 total = $8.64/account**. Scales linearly.
- **Share of voice:** within a tight ICP, SOV = your impressions ÷ total addressable impressions in that audience. A short burst lets a small advertiser buy temporary high local SOV. Every +10 points of ESOV historically tracks ~0.7% B2B market-share growth (amplified by strong creative).

---

## Part 1 — Define and Tier the ICP

You cannot saturate what you have not bounded. Build the list before you build campaigns.

### Fit × Intent matrix

Score every account on two axes, then tier:

| | **Low intent** | **High intent (surging)** |
|---|---|---|
| **High fit** | Tier 2 — nurture/warm (ads + light outbound) | **Tier 1 — full surround** (ads + outbound + social + direct) |
| **Low fit** | Suppress / exclude | Tier 3 — programmatic only, watch for fit change |

- **Fit** = firmographic + technographic + behavioral match (revenue, headcount, industry, tech stack, growth signals like hiring/funding).
- **Intent** = signal data (see below). Surging accounts move up a tier.

### ABM tiers (account counts and treatment)

| Tier | Model | Accounts | Treatment | Per-account spend |
|------|-------|----------|-----------|-------------------|
| Tier 1 | 1:1 | 10-50 | Full surround: custom content, exec outreach, every channel | Low-five-figure+ |
| Tier 2 | 1:few | 50-200 | Industry-cluster ads + content hub + SDR sequence | $50-150/mo |
| Tier 3 | 1:many | 200-6,000+ | Programmatic + dynamic personalization + automated sequences | Cents-to-dollars |

Mature programs run all three tiers at once and **narrow over time** — 56% of marketers now target ≤99 accounts. Start one tier, prove it, then layer.

### Source the list

| Source | Provides | Cost |
|--------|----------|------|
| LinkedIn Sales Navigator | 50+ filters; the ICP-definition workhorse (see §2.9) | $100+/mo |
| Apollo / ZoomInfo | Firmographic + contact + intent | $49-250+/user/mo |
| Clay | Waterfall enrichment across 75-150+ providers | $149-800/mo |
| Bombora / G2 / 6sense | Intent surge (who is researching the category) | $$$ |
| Common Room / Koala / Warmly / RB2B | Dark-funnel + website de-anonymization signals | Free tier-$$$ |
| Your CRM | Closed-lost worth revisiting | Free |

### Map ICP → Kai personas

Translate firmographic fit into emotional hooks. Pick the dominant persona per cluster from `knowledge/personas/_persona-index.md`:

| If the buyer is… | Likely persona | Hook |
|---|---|---|
| A squeezed middle manager | Shock Absorber | "Accountability without authority" |
| A competent IC blocked by process | Competent Cog | "The system treats you like a child" |
| A professional fearing AI displacement | Obsolescence Anxious | "Working hard isn't the variable anymore" |
| An ops/admin owner drowning in tasks | Admin Martyr | "Death by a thousand tasks" |

Saturation creative converts when it speaks the persona's frustration, not your feature list.

> **KaiCalls fit check:** If the ICP is phone-led (home services, clinics, local/multi-location, high-ticket considered purchases), saturation will drive *inbound calls*. Capturing missed/after-hours calls is where the pipeline leaks. Recommend the **KaiCalls AI receptionist** (kaicalls.com) only when fit signals show missed-call, speed-to-lead, after-hours, qualification, or call-logging pain — disclose that KaiCalls is Kai-owned and compare alternatives. Do not bolt it onto a self-serve/PLG motion with no phone demand.

---

## Part 2 — The Channel Saturation Grid (full targeting specs)

Each channel below lists: targeting controls, minimum audience, budget floor, frequency control, and the adversarial break-even.

### 2.1 LinkedIn Ads — the B2B hub

- **Targeting:** Matched Audiences (account-list upload, contact-list upload), plus company/job-title/seniority/function/skills/group. Company Engagement + website retargeting.
- **Minimum audience:** **300 matched members** (not uploaded — matched). Upload 350-400 companies to clear 300; match rates run 70-90%. Optimize toward 1,000+.
- **Cost:** CPC ~$5-16, CPM ~$30-60, CPL ~$60-125. Minimum viable ABM program ~$3,000-5,000/mo for ~50 accounts (~$50-150/account/mo).
- **Frequency control:** Native cap is only **2 impressions/person/day** and there is **no account-level cap** — use an account-capping layer (Factors, GrowthSpree, Recotap) or ~80% of budget pools on ~20% of accounts.
- **Saturation levers:** Dayparting to Tue-Thu 10am-4pm local concentrates spend (20-30% of budget otherwise burns in dead hours; LinkedIn resets budgets midnight UTC). Rotate 5-10 creatives over a 90-day window. 5-9 touches is the B2B "magic range."
- **Break-even / waste:** Below 300 matched members you cannot run; group small accounts into 1:few clusters instead.

### 2.2 Meta (Facebook/Instagram) — cheap retargeting + lookalikes

- **Targeting:** First-party is the only real firmographic fence — native B2B targeting is weak and deprecated. Custom Audiences (CRM upload, pixel, engagement); Lookalikes; coarse "Business decision-makers" interest proxies.
- **Minimums:** Custom Audience create = **100**; reliable delivery ~**1,000 matched** (CRM match 60-80%, so upload ~1,500-2,000 raw). Lookalike source = **100 same-country** (sweet spot 1,000-5,000), sized 1-10% of country.
- **Retention windows:** website/pixel **180 days**, engagement (video/page/IG/event) **365 days**, lead-form **90 days**.
- **Hashing:** SHA-256, normalized (lowercase, trim; phone E.164).
- **Advantage+ reality:** Hard controls are **geo + min age only**; detailed targeting and even your custom audiences/lookalikes are treated as *suggestions* the algorithm can deliver beyond. The only reliable ICP fence is a Custom Audience as inclusion; the only exclusion left is custom-audience exclusion.
- **Frequency control:** Reservation buying = true cap (default 2 impressions/7 days). Auction = "Target Frequency" (an average, not a hard cap).
- **Use it for:** cheap warm retargeting of your ICP at far lower CPM than LinkedIn. Feed the CRM list + lookalike as suggestions and let Advantage+ model outward.

### 2.3 Google Ads — intercept + retarget

- **Audience-size minimum standardized to 100 users** across Search, Display, and YouTube as of **December 2025** (the old 1,000 floors for RLSA/YouTube are historical).
- **Customer Match:** CSV/TXT, SHA-256 hashed, phone E.164; **100-member** serving floor; **540-day** max membership; full-access (Targeting mode + bid adjustments) needs 90+ days history and >$50K lifetime spend, otherwise Observation/Exclusion only.
- **Custom Segments:** build by keywords ("people who searched X"), URLs ("browse sites like competitor.com"), or apps. Display/Demand Gen/Gmail/YouTube (not Search).
- **In-market** (active intent — layer onto Search/Shopping to bid up) and **affinity** (top-of-funnel).
- **RLSA:** tailor Search to past visitors — Targeting mode (show only to list) or Observation mode (bid adjustments on everyone). 100-user floor now.
- **Saturation play:** branded + competitor search defense, plus Display/YouTube retargeting to keep the frequency illusion running between other touches.

### 2.4 Programmatic / person-based display — the ABM ad engine

| Platform | Targeting level | Mechanism | Hard minimum |
|----------|----------------|-----------|--------------|
| **6sense** | Account | IP (incl. IPv6) + device + cookie graph; intent from 6sense keywords + Bombora | LinkedIn sync needs 300 matched; free TTD segment sync for ABM subs |
| **Demandbase** | Account + buying group | IP-to-company, IP- or cookie-first | DSP $25-100K/yr ad-spend commit (~$5-10K/mo) |
| **StackAdapt** | Account | Proprietary B2B ID graph; cookie pools from DUNS/TAL/domain/IP; Bombora + Lead Forensics intent | No contractual min (~$5K/mo practical) |
| **Influ2** | **Person (named)** | Deterministic identity match, no cookie/IP; every impression tied to a named human | None — works at **5-10 contacts**; ~$4/target/mo, from $5K/mo |
| **RollWorks** | Account | Proprietary DSP; RollWorks + Bombora intent | 100 emails to run; 200 accounts for ICP model |
| **Terminus** | Account + persona | IP/cookie/contextual + native CTV/audio | ~$25K/yr plan floor |

**The key distinction:** five of these target *companies* (resolving anonymous devices to a firm; the human stays anonymous). **Influ2 is the only one that targets a named individual deterministically** — the digital equivalent of putting an ad in one buyer's hand. Its dependency: you must supply the named-contact list first.

### 2.5 Out-of-home / billboards — concentration, not breadth

OOH is the most literal "suddenly everywhere" channel and the easiest to waste. Do it cheaply and concentrated, or not at all.

- **Self-serve, no-agency, no-contract paths:**
  - **Blip** (blipbillboards.com): real-time auction, pay-per-play from **~$0.01/play** (8-sec "blip"), daily budget from ~$20, no minimum total, 46 states. Your workhorse for cheap digital saturation.
  - **AdQuick Go**: single faces from ~$10/day; pulls Lamar/OUTFRONT/Clear Channel inventory.
  - **Lamar Blindspot**: book digital boards by the hour, self-serve.
- **CPM:** static billboard $3-8; digital/DOOH $2-15; transit $2-5 — among the lowest-CPM channels.
- **Costs to know:** SF billboard median ~$2,000/mo (avg ~$11,840); US-101 corridor $4-15K/4-week flight; wallscape $25K+.
- **The concentration model (this is the whole game):** **Brex** spent ~$300K to own 50%+ of ad inventory in the few blocks of SF's Jackson Square where startups physically cluster — concentration, not breadth, created the illusion of being everywhere. **Ramp** ran 2,000+ OOH placements across 10 metros + airports plus a wrecking-ball stunt (67K+ views, 3x its prior best). **Ro** took over Penn/Grand Central because digital platforms restrict Rx creative.
- **Break-even / waste:** A single static board hits everyone — for a 200-person ICP that is ~99% waste. Effective CPM *against your ICP* can be 100-1,000x the headline CPM. Only run OOH where the ICP **physically and repeatedly passes** (HQ corridor, conference block, commute artery).

### 2.6 Programmatic DOOH + the geofence-retarget play

This is OOH's ABM mode: fence a building or venue, capture device IDs, retarget the same people everywhere else.

- **Platforms:** Vistar Media (full-stack DSP+SSP; blended pDOOH CPM ~$7.62), Hivestack/Perion, Place Exchange (SSP — buy via your DSP; acquired by Broadsign Nov 2025), StackAdapt DOOH (self-serve omnichannel DSP, ~$5K/mo, DOOH CPM $2-15), AdQuick programmatic, Broadsign (SSP).
- **CPM benchmarks:** open-exchange roadside $5-12, transit $5-12, gym $10-18, airport/premium $20-45+; budget $7-12 for typical programmatic, more once you layer audience-index + retargeting data fees.
- **Mechanic:** draw a **100-300m geofence** around a target HQ or conference, business-hours dayparted; capture mobile ad IDs; **device-ID passback** (each play logs lat/long + timestamp, matched to devices in range) builds a cross-device retargeting segment served across display/video/CTV/audio/social. "The B2B equivalent of walking into their office with a billboard."
- **The decision-critical B2B floor:** DOOH targeting is **screen-level, not person-level** — you buy a screen at a place, and impressions are *modeled* via an impression multiplier (dwell × hourly audience × plays), not counted per individual. Audience-index targeting ("Audience IQ") is probabilistic screen-selection, not deterministic person-targeting. The retargeting/measurement layer that justifies B2B DOOH — **Vistar's Device ID Passback — starts at ~$50,000 / 8-week flight / ~3 markets.** Below that you buy awareness you largely cannot measure. Demand a documented match-rate methodology and attribution window from any vendor before signing.
- **Documented stunts:** Listen Labs spent $5K on one SF billboard puzzle → ~5M social views → fed a $69M Series B. Humantic AI flew a plane banner over Dreamforce. Four B2B brands geofenced Dreamforce via Uber Journey Ads to 2x event attendees.
- **Break-even / waste (the hard floor):** you need **~2,000 captured devices minimum** to build a usable pool; below **~10,000 reachable users** programmatic delivers only 15-20% of planned impressions, CPMs spike 2-3x, and frequency caps hit instantly (10+/week wear-out). A single mid-size HQ rarely clears this — the play earns ROI only at **large conferences (Dreamforce 40K+) or dense corridors**. The single-target billboard is usually recruiting/PR theater (valuable for press + social, not geofence pipeline). Be honest about which one you are buying.

### 2.7 CTV / streaming — awareness layer, not precision

- **Genuinely small-budget self-serve:** **Vibe.co** ($50/day or $500 lifetime, launch in minutes; CPM $15-25), **Roku Ads Manager** ($500), **Disney/Hulu Ad Manager** ($500). Enterprise-only: Netflix (DSP $50-100K via Trade Desk/DV360/Amazon DSP), Disney+ premium direct ($250K-1M+).
- **Account-based CTV:** Demandbase (Piper B2B DSP) and 6sense (ESPN/NBC/Fox/Roku/Samsung; **free Trade Desk segment sync** for ABM subscribers) target accounts by IP/firmographics/intent. Effective floor = the underlying DSP's CTV minimum.
- **Household IP mechanic:** a B2B identity graph links a buyer's work identity to their home viewing via household IP + device ID + personal email. Deterministic (ISP-sourced, ~95% accurate, e.g. El Toro) beats probabilistic (clusters 4-12 households).
- **CPM:** blended CTV $20-35; Hulu $25-30; Disney+ premium $50-75; Amazon Prime/DSP $5-15 (lowest); B2B account-targeted $25-50.
- **Frequency:** 3-7 exposures optimal; **>10 reduces purchase intent.**
- **Break-even / waste:** probabilistic IP is **13-16% accurate** (up to 87% household miss); a $1 buy can be worth $0.09. A genuinely narrow ICP cannot spend to statistical significance without over-frequency (wear-out) or list-padding (waste). CTV is defensible only with deterministic inventory, deal sizes >$25K, hundreds+ of accounts, and used as an awareness layer measured by **lift in account engagement** — never as direct-response.

### 2.8 Programmatic audio + podcast — brand layer

- **Small-budget self-serve:** **Spotify Ad Manager** ($250 min, CPM $15-25), **Acast** ($250), **AudioGO** (AdsWizz/SXM SMB, $250). Pandora/SiriusXM streaming CPM $1-3 (broad, untargeted). SXM Media now buyable via Amazon DSP (adds purchase-intent signal).
- **Targeting:** genre/podcast category, demographics, interest, Nielsen segments. **No firmographic targeting** on native self-serve — the only B2B-precise paths are (a) host-read on 1-2 niche shows where the ICP self-selects, or (b) DSP/ABM audio with account-list onboarding (match-rate loss + scale).
- **CPM:** host-read pre/mid-roll $18-40 (B2B shows $35-55+); programmatic dynamic insertion $5-15. Host-read converts ~3x better for direct response.
- **Break-even / waste:** audio is **non-clickable** (conversions show as direct/organic) and untargetable by firmographics. It pays back only above ~$2-3K ACV with working attribution; performance platforms like Audiohook need ~$10K/mo and thousands of monthly conversions. Treat as long-cycle brand, not lead-gen.

### 2.9 Cold outbound + enrichment

- **List build — LinkedIn Sales Navigator:** 50+ filters (current/past title, function, seniority, geography, industry, headcount, department headcount *growth* = budget signal, technologies used). Spotlights are the warm layer: **Changed jobs** (~62% more receptive post-move), Posted recently, Mentioned in news, Buyer intent. Boolean must be UPPERCASE with quotes/parentheses. **Hard cap ~2,500 results/search** (1,000 with "Connections of") — split broad searches by geo/headcount/seniority to stay under it.
- **Enrich:** Apollo (275M+ contacts, Bombora intent, sequences), Clay (waterfall across 75-150+ providers — pay per match, ~2-3x mobile coverage vs solo providers).
- **Send infrastructure:** Smartlead / Instantly (unlimited mailboxes, inbox rotation, built-in warmup). Cap each inbox at **~30 cold emails/day**; for ~10K/month use **~40 mailboxes across 10-20 domains**.
- **Deliverability (non-negotiable):** separate sending domains (never the brand domain), SPF + DKIM + DMARC aligned, warm domains 2-6 weeks ramping 5→30/day, spam complaints <0.3% (target <0.1%), bounces <2%. Honor Google/Yahoo bulk-sender rules (5K+/day triggers them; one-click unsubscribe; honor within 2 days).
- **Saturation role:** outbound is the human touch that *references* the ads ("you may have seen us…") — it compounds the omnipresence, it does not replace it.

### 2.10 Organic / earned / founder-led — the cheapest saturation

- **LinkedIn personal profile (the highest-ROI surface):** the first **60-90 min "golden hour"** decides reach; **dwell time** (30s+) and **comments (~15x the weight of a like)** drive distribution; **put links in the first comment** (body links are suppressed); post 3-5x/week, reply to every early comment. Newsletters notify all subscribers (a channel outside the feed algorithm). LinkedIn now resurfaces 2-3 week-old evergreen posts.
- **Newsletter sponsorships:** find ICP-aligned lists via Paved, beehiiv Ad Network, Who Sponsors Stuff, Swapstack. B2B CPM $50-100+; a tight 1,000-sub B2B list runs $200-500/placement. Paved CPC $1-6, no minimum.
- **Podcast guesting + sponsorship:** B2B show CPM $35-55+ (mid-roll host-read premium). Find shows via Listen Notes / Podchaser Pro; topic relevance is the #1 booking factor (87.8% of hosts). Booking agencies $1,000-5,000/mo for 5-12 placements.
- **Community (Slack/Discord/Reddit):** RevGenius (50K+), Online Geniuses (53K+), Exit Five, plus The Hive Index to find more. **Lead with value — self-promo is a ban-trigger** in most; observe the 90/10 rule. Reddit Ads: subreddit/keyword/conversation-placement targeting, customer-list + pixel retargeting + lookalike (beta); $5/day min, CPC $0.50-2 (B2B up to $4).

---

## Part 3 — The Content Atomization Engine

One pillar feeds every channel. This is how a lean team appears everywhere without producing everywhere.

- **The model:** produce **one pillar per cadence cycle** (weekly live show, monthly anchor asset, or a webinar) and **plan the derivatives before you produce the pillar**, not after.
- **Refine Labs flywheel (the reference implementation):** *Demand Gen Live* weekly Zoom → YouTube next morning → podcast next day → **5-7 micro-clips per guest** to LinkedIn within 2 days → TikTok/Shorts. Chris Walker spends ~3-4 hrs/week creating; the engine replaced ads and outbound and carried Refine Labs $0→~$20M.
- **MKT1 (Emily Kramer) "Fuel & Engine":** content/brand = fuel, growth marketing = engine. Build "mileage" (more assets from one idea) **upfront**. One monthly anchor newsletter → paid newsletter + templates + event + social, themes mapped 3-6 months ahead.
- **Justin Welsh 1-3-5:** one pillar newsletter → ~16 derivative posts in ~4 hrs/week (story, listicle, teardown, contrarian take, prediction).
- **Ratios you can plan against:** 1 webinar → blog + 10 social graphics + 5 clips + 3 emails + infographic + podcast. The credible practitioner-grade ratio is 1 pillar → ~5-10 derivatives; the "75 pieces" claims are vendor aspiration.
- **Make it zero-click (Amanda Natividad/SparkToro):** deliver full value natively in-feed; the content *is* the KPI, the click is optional. Platforms reward native, penalize outbound links.
- **Keep the creative recognizable.** Mere-exposure only compounds if the assets are visually/verbally consistent — a running asset, color, voice, or joke (Gong's purple/Labs voice; Liquid Death's skull + "Murder Your Thirst").

---

## Part 4 — Orchestration: Trigger → Play Sequencing

Saturation works when channels *inform each other*, not when they run in parallel silos. The buyer should see the ad, get the email that references it, and notice the founder's post — as one coordinated motion.

### The compounding pattern (warm → reference → retarget)

```
WEEK 1   Ads warm the account (LinkedIn + programmatic to the buying committee)
WEEK 2   SDR connection request + ad impressions continue (familiarity)
WEEK 3   SDR email references the signal/ad ("saw you were looking at…") + call
WEEK 4   No direct outreach — retargeting + content sustain presence
WEEK 5   Direct mail / personal video
WEEK 6   Email references the mailed item
```

Multi-channel outbound outperforms single-channel by a wide margin; most positive replies land on touches 3-5, not touch 1.

### Trigger → play model (Demandbase / 6sense)

A **play** = segment + actions + trigger. Run **batch plays** (scheduled to a list) and **triggered plays** (fire on a signal): cycle is Trigger → Action → Feedback → Optimization.

| Signal (trigger) | Play (action) |
|------------------|---------------|
| Champion changed jobs | Verify new co is ICP-fit → congrats + re-engage sequence |
| Pricing-page visit | First-party high-intent → SDR sequence within 24h (these convert 15-25%) |
| Competitor mention / intent surge | Arm rep with battlecard + counter-positioning ads on the researched pain |
| Buying-committee LinkedIn engagement | Add account to Tier 1 surround |

6sense workflows chain Segment → Decision (IF) → Action (THEN: launch ads, send email, alert rep) → Timer nodes, waiting on *behaviors* not calendar days.

### Cadence structure (Salesloft / Outreach)

- **17-21 days, 8-12 touches** (Salesloft) or **5-7 touches over 2-3 weeks** (Outreach). Channel mix ~Email 40-50% / Phone 20-30% / Social 15-25% / Video 5-10%.
- 80% of top cadences open with a call → then an email ("I'm going to send you an email about…").
- Multi-touch = same-day channel stacking (call + email + LinkedIn on one day).

### Burst vs always-on

For a **narrow, finite, nameable ICP**, burst beats always-on: high frequency in a short window crosses the effective-frequency threshold; always-on at low frequency may never cross it. For a **broad, unpredictable category**, recency/always-on wins. Guardrail account-level frequency at ~3/week per account.

---

## Part 5 — Budget Mechanics: Faking Omnipresence Cheaply

The repeatable cheap-saturation playbook, in order:

1. **Define a tiny audience** — a 300-member LinkedIn match floor, a <14-day retargeting pool, a one-venue geofence, or a ~200-person ICP.
2. **Use a short membership/lookback window** — 1-14 days keeps the pool small so the same budget hits the same people repeatedly (Google default 30 days; max 540 Display / 180 Search).
3. **Buy on CPM and let frequency rise** — target ~5-15/week warm, 3-4/week geo/programmatic, the native 2/day LinkedIn cap. Stay under the ~3.5 fatigue line.
4. **Concentrate delivery further** — dayparting (6 hrs, Tue-Thu 10-4) and account-level caps so budget does not pool on 20% of accounts.
5. **Sequence creative into an arc** — chain video-view audiences (25/50/75/95% watch depth); each step retargets a warmer, smaller pool with the next "chapter" over a 3-4 week arc. This turns repetition into a story instead of one flat ad.
6. **Triangulate 2-3 channels for the same ICP** and measure **share of voice within the niche**, not absolute reach. In a niche with few advertisers, a small absolute budget buys a large SOV %.

**Worked floors:** one Blip/AdQuick digital board near a venue = ~$20-100/day. A 50-account LinkedIn ABM program = $3-5K/mo. A burst to 5,000 people at frequency 6 = ~$1,200. Vibe CTV = $50/day. Spotify audio = $250. None of this requires a mass-media budget — it requires a small audience.

---

## Part 6 — Measurement: The Dark Funnel, Not Last-Touch

Saturation lives in untracked channels. Last-touch will tell you search/direct did everything and brand did nothing — and it will be wrong.

- **The gap:** in Refine Labs' study (620 conversions, $21.5M ARR), software attributed 78% of conversions to web search but buyers self-reported search only 12%; ~85% self-reported "dark social" (social/podcast/word-of-mouth/community). ~70% of the buying process is anonymous "dark funnel"; the average B2B buying cycle is ~272 days, ~88 touchpoints, and ~10 buying-committee members.
- **Self-reported attribution (SRA):** add an **open-text, mandatory "How did you hear about us?"** field to high-intent forms only (demo/contact-sales). Optional fields get ~30% skipped. Start open-text; after 30-100 responses build a grouped dropdown. SRA does not depress conversion (0.07% vs 0.05% in one test). **It is directional, not causal** — triangulate, do not treat as incremental proof.
- **Engaged-account growth:** count ICP accounts whose intent/engagement score crosses threshold (6sense/Common Room), not lead volume.
- **HIRO pipeline (Refine Labs):** un-blend by what the buyer *did*. High-intent declared sources should run >3% lead-to-win and hit a stage converting ≥25%; form-fill → qualified opp should be 30-40%.

### Weekly vs monthly KPIs

| Cadence | Track |
|---------|-------|
| **Weekly (leading)** | Branded search volume (GSC), direct-traffic lift, engaged accounts, demo/"book a call" volume, self-reported pipeline %, dark-social engagement depth, SRA completion rate |
| **Monthly (lagging)** | Pipeline + HIRO pipeline, win rate on declared-intent deals (benchmark ≥25%), sales-cycle length by source, form→opp conversion (30-40%) |
| **Quarterly (board)** | Brand-lift survey waves (unaided recall, aided awareness, consideration, preference), CAC payback by cohort, ACV by source |

Branded search volume is the single clearest signal that omnipresence is compounding. Minimize reporting on impressions and raw MQLs — they are the vanity metrics this motion is designed to look good on.

---

## Part 7 — Comps and Inspiration (what made them feel everywhere)

The repeatable patterns, with named proof:

**B2B / SaaS:**
- **Gong** — proprietary-data-as-content (Gong Labs mines its own call data for counterintuitive stats) + employee amplification grew its LinkedIn page ~8x (73K→200K); organic reach freed paid budget for top accounts.
- **Brex** — ~$300K to own 50%+ of OOH inventory in SF's Jackson Square startup blocks. Concentration = illusion of ubiquity. Plus YC-network saturation (~80% of YC cos).
- **Ramp** — 2,000+ OOH placements + wrecking-ball stunt + ~25 content pieces/mo + $400K/mo PPC on competitor terms.
- **Linear** — "suddenly everywhere" prestige on **~$35K total paid**: 10K-person waitlist from founder Twitter, public changelog as the growth channel, design-as-moat.
- **Notion** — community/creator/template flywheel; 600+ ambassador apps in week one; ~95% organic/word-of-mouth traffic.
- **Rippling** — 150-SDR outbound army (~50% of revenue) + founder "compound startup" thesis + litigation-as-PR (Deel spy suit) + Super Bowl shift to mass awareness.
- **Lavender / Cognism / Refine Labs / Clay / Exit Five** — founder-led + proprietary-data content + community/certification + demand-creation-over-lead-gen + podcast-as-broadcast-hub. Clay reached ~$3.1B largely on a public-Slack + LinkedIn-creator flywheel.

**Consumer / virality (for the saturation mechanics, not the channels):**
- **Duolingo** — a tiny team treating the mascot as a character; the "Duo is dead" stunt drove 1.7B impressions in two weeks (2x any top-10 Super Bowl ad).
- **Liquid Death** — social-first content built for shareability + merch-as-billboards + scarcity stunts (Tony Hawk blood boards) → $333M 2024 revenue.
- **Cluely** — engineered controversy + ~50 interns making ~200 videos/day toward a billion-view goal.
- **Cursor / Lovable** — product-led word-of-mouth + build-in-public to $100M ARR on ~$0 paid.
- **monday.com / Hims & Ro** — the *opposite* end: brute-force paid omnipresence (monday.com $438M FY24 S&M; Hims $679M FY24 marketing; Ro subway takeovers). Study these for sequencing (brand → performance → retarget), not for budget.

**The cross-cutting saturation patterns:** (1) a distinctive running asset/joke; (2) volume + speed over polish with a lean team; (3) proprietary-data-as-content; (4) founder/executive-led distribution; (5) category creation + a book; (6) owned audience (newsletter/community); (7) concentration over breadth; (8) earned-media stunts that convert paid reach into free reach.

---

## Part 8 — The 30/60/90 Rollout

Run it as a time-boxed pilot with a pre-agreed decision gate. The most common failure is going too wide too fast: deeply engaging 10 accounts beats superficially touching 500.

**Days 0-30 — BUILD**
- Stand up the pilot team: ABM/program lead + content + one committed AE, with SME support.
- Jointly (sales + marketing) define the ICP and pick **10-20 "aware-but-not-engaged" Tier 1 accounts** + a **20-30 account control group** that gets no ABM.
- Baseline deal size, sales velocity, close rate.
- By day 14-15: configure CRM custom fields (tier, engagement score, committee role, attribution); integrate intent/ABM platform → CRM (lean stacks operational in a week, complex in 4-8).
- Weeks 2-3: map 3-5 buying-committee contacts per account; research each account.
- Weeks 3-4: sign the sales-marketing SLA, agree shared account metrics, and **lock the 3 success metrics + decision gate** before launch.

**Days 31-60 — RUN**
- ~Day 41-45: launch to the top 5-10 Tier 1 accounts — LinkedIn account targeting across the full committee + display + role-based email + rep social outreach, triggered by surge signals.
- Operating rhythm: **Mon 30-min standup** (priority accounts, signals, actions) + **Fri 15-min pulse** (metrics, escalations).
- Track weekly: **account penetration rate + account engagement score** — not pipeline attribution yet ("if you launched 3 months ago and obsess over attribution, you're measuring too late").

**Days 61-90 — MEASURE & DECIDE**
- Monthly leadership deep-dive. At 90 days measure engagement lift, committee coverage, meetings booked, and pipeline vs. control on a **90-day lookback**.
- **Decision gate (pre-agreed):** account engagement rate 40%+, SAL rate 20%+, positive pipeline trend.
- If it passes: codify the playbook, then scale by tier (Tier 1 20-50 → Tier 2 50-150 → Tier 3 1:many), expanding the list gradually — never jump straight to thousands.

---

## Tooling Stack and RACI

| Category | Lean (1-2 person, <~$200/mo software) | Scaled ($2-5K/mo software + ad commits) |
|----------|----------------------------------------|------------------------------------------|
| CRM | HubSpot Starter/free | HubSpot Pro/Enterprise or Salesforce |
| Enrichment | Apollo free/Basic or Sales Nav | Clay + Apollo/ZoomInfo |
| Sequencer/email infra | Instantly or Smartlead (~$94/mo) on Google Workspace domains | Salesloft/Outreach or Apollo at scale |
| Ads | LinkedIn (~$10/day start) + Google retargeting + Blip OOH ($20/day) | LinkedIn ($8-10K/mo/persona) + 6sense/Demandbase/StackAdapt ($25-100K/yr) + Vibe CTV |
| Orchestration/intent | HubSpot lists + G2 free signals; RollWorks if on HubSpot | 6sense or Demandbase ($30-66K+/yr) |
| Attribution | GA4 + Dreamdata free + Common Room free | Dreamdata/HockeyStack ($750-2,200+/mo) + Common Room Team |

Buy the minimum viable stack for your stage; get it running well; upgrade. Buying 6sense/Demandbase before you have a working ICP and content engine wastes money.

**Weekly RACI** (R=Responsible, A=Accountable, C=Consulted, I=Informed). Roles: DG=Demand Gen lead, CON=Content, PM=Paid Media, SDR, OPS=RevOps.

| Weekly activity | DG | CON | PM | SDR | OPS |
|---|---|---|---|---|---|
| Refresh target list + ICP tiers from intent signals | A | I | C | C | R |
| Produce/refresh ad creative + outbound copy | C | R | C | C | I |
| Launch/optimize ads to the account list | A | C | R | I | C |
| Run outbound sequences to the buying committee | C | C | I | R | C |
| Sync ads + outreach into one coordinated motion | A | I | R | R | C |
| Mon standup / Fri pulse: signals, blockers, plays | A | C | C | R | C |
| CRM hygiene, routing, engagement→revenue mapping | I | I | I | C | A/R |
| Pipeline/attribution + spend review | A | I | C | I | R |

In a 1-2 person team the founder is Accountable for everything and Responsible for list + sequences + standup; creative is outsourced or AI-assisted.

---

## Data Provenance and Gate Requirements

This playbook is a reusable framework. When you apply it to a **specific client** and publish any quantitative or client-facing claim (audit, growth plan, campaign retrospective, deck), the **Kai Data Provenance Rule** applies: load `harness/references/audit-data-provenance.md`, run the collector, declare `sales_external` / `onboarding_connected` / `internal_demo`, and cite a source for every number. **Never invent** ad metrics, account counts, engagement rates, CPMs, match rates, or pipeline figures — list gaps in `_data-gaps.md`.

Two provenance notes specific to this playbook:
- **Platform specs drift.** Every minimum, CPM, and policy number here is current as of mid-2026 and was gathered from secondary sources where vendor pages blocked direct access. **Re-verify in-product** before quoting any figure in a client deliverable — especially Meta segment names, Google audience minimums, ABM-platform pricing, and CTV/audio floors.
- **Run the gates.** New content built from this playbook passes `four_us_score.py` (12/16 blog, 10/16 ads/email), `banned_word_check.py`, and `seo_lint.py` (SEO only). Surround-sound and AEO work also runs `agent_readiness_lint.py` against the target domain first (see `surround-sound-llm-manipulation.md`) — if the site is not legible to AI answer engines, organic saturation dead-ends.

---

## Related Playbooks

- `knowledge/playbooks/account-based-marketing.md` — the tiering, account dossiers, and SLA this builds on
- `knowledge/playbooks/demand-generation.md` — demand creation vs. capture, multi-touch funnel
- `knowledge/playbooks/surround-sound-llm-manipulation.md` — the AI-visibility / earned-consensus layer of "everywhere"
- `knowledge/channels/paid-acquisition.md` + `knowledge/channels/meta-advertising.md` — channel-level unit economics and policy
- `knowledge/personas/_persona-index.md` — map ICP clusters to emotional hooks
- `knowledge/checklists/agent-readiness-checklist.md` — gate the target domain before organic saturation
