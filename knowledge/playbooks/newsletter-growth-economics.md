# Newsletter Growth Economics

> **Use when:** Deciding where to spend the next dollar (or hour) of newsletter growth effort, pricing what a subscriber is worth, auditing an existing list's acquisition mix, or diagnosing why a fast-growing list monetizes badly.
>
> **Adjacent docs (cross-link, don't duplicate):** send mechanics, platform selection, suppression, and deliverability monitoring live in `knowledge/channels/email-lifecycle.md`. Edition planning and production live in `harness/skills/kai-newsletter/SKILL.md` (that skill loads this doc for growth strategy). Compliance floor for any outreach-adjacent tactic: `harness/references/cold-email-rules.md`.

---

## Operating Rule: Benchmarks Are Hypotheses

Every number below is either **cited** (source in `## Sources`, mostly vendor-published — treat as Tier-6 evidence per the evidence tiers in `knowledge/checklists/cro-audit-checklist.md`) or **marked HEURISTIC**. Vendor benchmarks size the market; only your own cohort data prices your subscribers. Never quote a benchmark in client-facing work without the source and retrieval date, and never substitute a benchmark for missing account data (Kai Data Provenance Rule applies to any audit using these numbers).

Core identity to keep in view the whole time:

```
Subscriber profit = (Revenue per subscriber per year × retention years) − Cost per subscriber
```

Growth channels differ on BOTH terms. A cheap channel that delivers subscribers who never open loses to an expensive channel that delivers readers. Rank channels on payback, not on cost per subscriber alone.

---

## Part 1: Acquisition Channels Ranked

Ranked by **quality-adjusted cost** — cost per subscriber divided by expected engagement of that cohort. Costs are 2025–2026 vendor-published ranges; your niche will vary.

| Rank | Channel | Typical cost/sub | Cohort quality | Scale ceiling |
|------|---------|------------------|----------------|---------------|
| 1 | **Organic social + content** (posting, SEO, guest appearances) | $0 cash; real time cost | Highest — self-selected intent | Slow; compounds |
| 2 | **Referral program** (existing readers recruit) | Prize/reward cost amortized; often <$1/sub | Near-organic — socially vouched | Capped by list size (Morning Brew: referrals still ~30% of growth at scale — ReferralRock) |
| 3 | **Cross-promo / swaps** (shoutout-for-shoutout with peer newsletters) | $0 cash; costs one editorial slot | High — pre-qualified newsletter readers; cross-promo cohorts are reported at 60–70% open rates vs 30–40% for paid cohorts (Growth In Reverse, vendor claim) | Capped by partner supply; find partners via Lettergrowth-style directories |
| 4 | **Paid social** (Meta/TikTok/X ads to a landing page) | $1–$3/sub when run well (Newsletter Operator) | Medium-high — interest-targeted, but ad-clicker skew | High — budget-limited |
| 5 | **Recommendation networks** (beehiiv Boosts, SparkLoop paid recs) | beehiiv cites a $1.63 average from Boosts early-access results; SparkLoop paid recommendations typically $2–$5/lead | Medium — reader of an adjacent newsletter, but one-click convenience subs; requires quality filtering | Medium-high |
| 6 | **Co-registration** (bundled signup checkboxes, sweepstakes networks) | Often cheapest per raw email | Lowest — multi-list opt-ins show weaker engagement and higher complaint risk (Media Intercept; DeBounce) | High, and that's the trap |

**Decision rules:**

1. **Under ~5,000 subs:** spend zero cash. Organic + swaps + guest appearances. Paid channels waste money before you know your revenue per subscriber.
2. **Add paid channels only after** you can compute allowable cost per subscriber from real revenue data (Part 2 worksheet). Buying subs before you know their value is gambling, not arbitrage.
3. **Recommendation networks:** turn on only with per-source cohort tracking and an engagement-based rejection rule (most networks let you refuse/refund low-quality subs — use it). Budget for a higher sunset rate on these cohorts.
4. **Co-registration:** default NO. Allow only when the economics still work at a pessimistic 50% quality haircut AND deliverability monitoring is in place — a complaint spike from a bad co-reg batch damages inbox placement for your whole list (see deliverability section of `knowledge/channels/email-lifecycle.md`).
5. **Referral program:** launch after ~1,000 engaged subs. Reward with status/content/merch tied to your topic, not generic prizes — referral-based giveaways produce fewer but markedly higher-quality subs than "enter to win" sweepstakes (Grow My Newsletter; see Part 4).
6. Any tactic that emails people who did not opt in is cold outreach, not newsletter growth — it falls under `harness/references/cold-email-rules.md` and its non-negotiables.

---

## Part 2: Unit Economics Worksheet

Work top to bottom. Output: an **allowable cost per subscriber (allowable CPS)** you can hand to any acquisition channel.

### Step 1 — Revenue per subscriber per year (RPSY), by monetization model

**Model A: Ads / sponsorships.**

```
RPSY(ads) = sends/year × open rate × (CPM ÷ 1000) × sellable slots per send × sell-through rate
```

CPM ranges (vendor-published 2025–2026; price on OPENS for engaged-list sales, on sends only if your buyer insists):

| Audience | CPM range | Source |
|----------|-----------|--------|
| Typical overall range | $10–$75 | beehiiv |
| Broad consumer / lifestyle | $15–$35 | beehiiv |
| Specialized B2B | $50–$100+ | beehiiv |
| Finance/fintech (aggressive top end) | up to ~$70–$180 claimed | MailAdx (single vendor — verify before quoting) |

Alternative structures: flat-rate per placement ($50 small lists → $10,000+ established; beehiiv) and CPA deals ($10–$100 per acquisition common; beehiiv).

*Worked example:* 10,000 subs, weekly send, 40% open, $30 CPM on opens, 1 slot, 50% of weeks sold. Per send: 4,000 opens × $0.03 = $120. Per year: 26 sold sends × $120 = $3,120 ÷ 10,000 subs = **$0.31 RPSY**. A $1.50 paid subscriber takes ~5 years to pay back at that rate. Conclusion: single-slot ads at consumer CPMs cannot fund paid acquisition — you need more slots, higher sell-through, premium B2B CPMs, or near-free organic growth.

**Model B: Paid subscriptions.**

```
RPSY(paid) = free→paid conversion rate × annual price × (1 + a share of expected renewal years, discounted)
```

Conversion benchmarks: Substack's own guidance says 5–10%; practitioner data puts the common range at **2–5% with a median near 3%**, and only roughly 1 in 5 publications clears 5% (Simon Owens; Yana G.Y. analysis). Small niche lists run 4–10%; big general lists 1–2%. Use 3% as the planning default unless you have your own data. Lenny's Newsletter runs ~4–5% at scale (Growth In Reverse, reported).

*Worked example:* $100/yr price × 3% conversion = **$3.00 RPSY** from year-one conversion alone, before renewals — roughly 10× the ads example above. This asymmetry is why paid-subscription newsletters can afford paid acquisition channels that ad-only newsletters cannot, and why most mid-size newsletters run hybrid.

Revenue per *paid* subscriber medians by vertical: roughly $83 (community topics) to $230 (investing) per year (beehiiv State of Paid Newsletters 2026).

**Model C: Own product / lead gen (courses, SaaS, services).**

```
RPSY(product) = buyer conversion rate × average order value × purchase frequency ÷ list size ... 
```

No honest public benchmark exists — conversion depends entirely on offer fit. **HEURISTIC:** newsletters selling their own high-ticket product often out-earn Models A and B per subscriber by 3–10×, which is why the allowable CPS for a services firm's newsletter can be far above ad-monetized norms. Compute from your own funnel or mark the plan's revenue line as unvalidated.

**Model D: Recommendation payouts** (you monetize your signup flow by recommending other newsletters): commonly ~$0.50–$3 per referred subscriber via Boosts/SparkLoop (vendor figures). This is a partial acquisition-cost offset, not a business model — and over-recommending at signup is itself an incentive-quality risk (Part 4).

### Step 2 — Allowable CPS

```
Allowable CPS = RPSY × target payback (years) × gross margin on newsletter revenue
```

Decision thresholds:

- **Payback ≤ 6 months:** scale the channel.
- **Payback 6–18 months:** run it, but only with cohort retention data proving subscribers survive that long.
- **Payback > 18 months or unknown RPSY:** cash channels off; organic/swap/referral only.
- Recompute quarterly. RPSY moves with open rates, sell-through, and pricing.

### Step 3 — Blend check

Sum planned monthly spend per channel ÷ expected subs per channel, weight each cohort by its observed 90-day open rate relative to your organic baseline, and confirm the **quality-adjusted blended CPS ≤ allowable CPS**. If the blend only works because a cheap low-quality channel drags the average cost down, the plan fails — low-quality cohorts drag RPSY down too and the model double-counts them as wins.

---

## Part 3: List Hygiene Rules

Deliverability mechanics (SPF/DKIM/DMARC, warming, monitoring thresholds, suppression tables) are owned by `knowledge/channels/email-lifecycle.md` — this section covers only the growth-economics decisions. Compliance floor for anything outreach-shaped: `harness/references/cold-email-rules.md`.

**Double opt-in: default ON for paid and network-sourced cohorts.** The tradeoff is volume vs quality: you lose a chunk of signups at the confirmation step (commonly cited at ~20–30%, HEURISTIC — measure yours), but confirmed lists perform materially better. A 2011 Mailchimp analysis of ~30,000 accounts (old but still the largest public comparison; reported via Litmus/Automateed roundups) found double opt-in lists with ~72% more unique opens, ~114% higher click rates, and sharply lower bounce and unsubscribe rates than single opt-in lists. Bots and mistyped addresses can't click confirmation links, so double opt-in also filters spam traps. Rule: single opt-in is defensible only for organic, high-intent signup surfaces where you verify addresses at capture; any channel where a third party delivers the email address (co-reg, networks, giveaways) gets double opt-in, no exceptions.

**Sunset policy: write it before you scale acquisition.** A subscriber who hasn't opened in N sends is a deliverability liability and an inflated denominator in every metric you sell to sponsors. Default sunset ladder (HEURISTIC — tune N to your cadence and purchase cycle, per the re-permission pattern in `email-lifecycle.md`):

1. No opens in 90 days (weekly cadence) → drop to reduced frequency segment.
2. No opens in 150 days → one re-permission email ("still want this?").
3. No response in 30 more days → suppress. No response IS the answer.

Sunset aggressively when you sell ads on opens: cutting dead weight raises open rate, which raises the CPM you can defend. A 50k list at 25% opens sells the same 12,500 opens as a 20k list at 62% — and the smaller list gets the better CPM story (audience-quality pricing per beehiiv/Paved).

**Hygiene economics rule:** count expected sunset losses as part of channel cost. A $1.50 co-reg subscriber cohort that sunsets 40% within six months costs $2.50 per surviving subscriber — re-rank your channels with post-sunset survivors in the denominator.

**Approval doctrine:** list purges, suppression changes, and re-permission sends are live-channel mutations — human approval required before executing any of them.

---

## Part 4: The Growth–Quality Tension

**The mechanism:** the more the signup was driven by an incentive external to your content (prize, bundled checkbox, one-click convenience), the less the subscriber wanted the content — and engagement decays accordingly. Practitioner data points, all directionally consistent:

- Sweepstakes/"enter to win" giveaways deliver cheap volume with quality that "varies dramatically" and is usually poor unless the prize selects for your exact reader (Grow My Newsletter). Referral-gated giveaways (entries earned by recruiting) deliver fewer subs at much higher quality — Morning Brew's referral engine drove ~80% of growth before paid acquisition and still accounts for almost 30% of growth at scale (ReferralRock; GrowSurf).
- Cross-promo cohorts reportedly open at 60–70% vs 30–40% for paid cohorts (Growth In Reverse).
- Lists grown by referral and organic search show higher recent-cohort engagement than lists inflated by sweepstakes or co-registration traffic (Media Intercept).
- Multi-list co-reg opt-ins correlate with overwhelm, disinterest, and complaint/unsubscribe behavior across all lists involved (DeBounce).

**Operating rules:**

1. **Tag every subscriber with an acquisition source at capture** (`email_subscribed` event with `source` property — the taxonomy already exists in `email-lifecycle.md`). Untagged growth is unauditable growth.
2. **Cohort-report engagement by source at 30/90/180 days.** Kill or renegotiate any paid source whose 90-day open rate is below ~60% of your organic cohort's (HEURISTIC threshold — the principle, comparing each cohort to your own baseline rather than a generic benchmark, is the same evidence rule as `knowledge/checklists/cro-audit-checklist.md`).
3. **Never sell sponsors a subscriber count you wouldn't defend cohort-by-cohort.** Inflated lists produce bad sponsor results, which produce churned sponsors — the decay shows up in revenue with a one-quarter lag.
4. **Incentives should point at the content, not away from it.** Prize = more of what the newsletter already is (premium editions, tools, access), not a MacBook. If the incentive would excite someone who'd never read you, it recruits people who never will.
5. **Watch the vanity-metric spiral:** subscriber count is the one metric that only goes up if you let it. Growth reporting in Kai should always pair list size with 90-day-cohort open rate and quality-adjusted CPS.

---

## How This Maps Into Kai

| Kai surface | Loads this doc for |
|-------------|--------------------|
| `harness/skills/kai-newsletter/SKILL.md` | Growth-strategy questions in Phase 1–2: channel selection, budget sizing, referral/cross-promo planning, list-quality diagnosis |
| `knowledge/channels/email-lifecycle.md` | Owns the send/deliverability/suppression layer this doc's hygiene rules hand off to |
| `harness/references/cold-email-rules.md` | Compliance floor whenever a growth tactic touches non-opted-in recipients |
| Audit workflows (`kai-*-audit`) | Allowable-CPS math and channel ranking when auditing a client newsletter — provenance rule applies: pull the account's real cohort data via the collector, never quote this doc's benchmark ranges as the client's numbers |
| `knowledge/playbooks/growth-loops-applied.md` | Referral-loop design detail beyond the economics treated here |
| `knowledge/playbooks/partnership-comarketing.md` | Cross-promo partner sourcing and deal mechanics |

Anything here that touches a live list — purges, re-permission sends, launching paid acquisition, turning on a recommendation network — goes through human approval first, per the harness approval doctrine.

---

## Sources

Vendor and practitioner sources retrieved 2026-07-16. Treat all benchmark figures as Tier-6 evidence (hypothesis-generating, not account truth).

- beehiiv — How Much Do Newsletter Ads Cost: https://www.beehiiv.com/blog/newsletter-sponsorship-cost
- beehiiv — The State of Paid Newsletters 2026: https://www.beehiiv.com/blog/the-state-of-paid-newsletters-2026
- SparkLoop — Grow on beehiiv (paid recommendation pricing): https://sparkloop.app/grow-on-beehiiv
- Newsletter Supply — beehiiv Boosts explained: https://newsletter.supply/blog/how-does-beehiiv-boosts-work
- Simon Owens — What's a realistic conversion rate for paid newsletters: https://simonowens.substack.com/p/whats-a-realistic-conversion-rate
- Yana G.Y. — Substack free-to-paid conversion rate, what's actually average: https://www.yana-g-y.com/p/substack-free-to-paid-conversion-rate
- Newsletter Operator — Growth tactics tier list: https://www.newsletteroperator.com/p/growth-tier-list
- Newsletter Operator — 26 newsletter growth channels: https://www.newsletteroperator.com/p/26-newsletter-growth-channels
- Growth In Reverse — Doing cross promotions the right way: https://growthinreverse.com/cross-promotions/
- Growth In Reverse — How Lenny Rachitsky gets 18k people to pay (conversion figure): https://growthinreverse.com/lennys-paid-newsletter/
- Lettergrowth — cross-promotion partner directory: https://lettergrowth.com/
- ReferralRock — How the Morning Brew referral program created wild growth: https://referralrock.com/blog/morning-brew-referral-program/
- GrowSurf — How Morning Brew grew to 2.5M subscribers: https://growsurf.com/blog/how-morning-brew-grew-its-subscribers/
- Grow My Newsletter — Giveaways, sweepstakes and competitions: https://www.growmynewsletter.com/growth-methods/giveaways
- Litmus — Single vs double opt-in: https://www.litmus.com/blog/single-opt-in-vs-double-opt-in-case-for-soi
- Automateed — Double opt-in vs single opt-in (Mailchimp study figures): https://www.automateed.com/double-opt-in-vs-single-opt-in
- Mailjet — Double opt-in and deliverability: https://www.mailjet.com/blog/deliverability/double-opt-in-should-i-or-shouldnt-i/
- Media Intercept — Publisher newsletter growth strategies: https://www.mediaintercept.com/post/publisher-newsletter-growth-strategies
- DeBounce — Co-registration glossary (quality risks): https://debounce.com/glossary/co-registration/
- Paved — Newsletter sponsorship rate benchmarks: https://www.paved.com/blog/newsletter-sponsorship-rates/
- MailAdx — Newsletter ad rates and CPM benchmarks 2026: https://www.mailadx.com/blog/newsletter-ad-rates-cpm-benchmarks-2026
- Inbox Collective — The four newsletter growth quadrants: https://inboxcollective.com/the-four-newsletter-growth-quadrants/
