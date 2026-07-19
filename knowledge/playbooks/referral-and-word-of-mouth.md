# Word-of-Mouth & Referral Engineering Playbook

> **Use when:** Designing a referral program, diagnosing why one underperforms, or engineering a product/content experience so customers share it unprompted.
>
> **Read with:** `knowledge/playbooks/growth-loops-applied.md` — a referral program is an *amplifier* on the Invitation/Network loop archetype, not a loop by itself. If the false-loop test there fails, fix the loop before building the program. Creator/influencer-driven advocacy (paid or gifted) is owned by `knowledge/playbooks/influencer-marketing.md`; this doc covers customer-to-customer sharing.

---

## Why This Channel Is Worth Engineering (evidence base)

- **Trust:** 88% of global consumers say they trust recommendations from people they know more than any other channel (Nielsen 2021 Trust in Advertising, ~40,000 respondents).
- **Referred customers are worth more:** In a ~10,000-customer study at a German bank tracked for nearly three years, referred customers had higher contribution margins, higher retention, and were **at least 16% more valuable** than demographically matched non-referred customers (Schmitt, Skiera & Van den Bulte 2011, *Journal of Marketing*; won the MSI/H. Paul Root Award). The margin gap eroded over time; the retention gap persisted. Follow-up work (Van den Bulte et al. 2018, *JMR*) attributes this to better matching and social enrichment — referrers pre-qualify people like themselves.
- **Scale is possible but rare:** Dropbox's double-sided storage referral is the canonical case — reported 100K→4M users in 15 months, with ~35% of daily signups from referrals at peak. Treat these as an outlier ceiling, not a planning benchmark.

**Planning rule:** model your referral program as a 5–40% amplifier on existing acquisition, not a standalone engine. K-factor above 1 is exceptional (see math below and the K-factor section of `growth-loops-applied.md`).

---

## Part 1 — The Six Researched Drivers of Sharing

Framework: Jonah Berger's STEPPS (*Contagious*, 2013), each element backed by published studies. Use the table as a diagnostic: score your product/content 0–2 on each driver, then engineer the weakest one that's plausibly fixable.

| Driver | The research | Diagnostic question | Engineering move |
|--------|-------------|--------------------|------------------|
| **Social currency** | People share what makes them look smart, early, or high-status; sharing is self-presentation (Berger, *Contagious*, ch. 1) | Does sharing this make the sharer look good — not us? | Give users a result worth bragging about: scores, rankings, "top 1% of users" stats, early access they can gatekeep |
| **Triggers** | Products cued more often by the environment get more word of mouth both immediately and over months; *interesting* products get only an immediate spike (Berger & Schwartz 2011, *JMR*) | What in the customer's daily environment reminds them of us? | Tie the brand to a frequent cue (a day, a task, a phrase). Frequency of the cue beats cleverness of the message |
| **Emotion / arousal** | High-arousal emotions (awe, anger, anxiety, amusement) increase sharing; low-arousal emotions (sadness, contentment) suppress it — held across 7,000 NYT articles plus lab experiments (Berger & Milkman 2012, *JMR*) | Does this activate people, or merely please them? | Lead with the surprising number, the injustice, the awe-inspiring result. "Interesting" is not enough; measure for activation |
| **Public / observability** | Publicly visible products get more WOM immediately *and* ongoing (Berger & Schwartz 2011); private consumption kills transmission | Can anyone tell our customer uses us? | Make usage self-advertising: badges, watermarks, "made with X," shareable artifacts, visible defaults (see Portable Artifact design in `growth-loops-applied.md` Step 4) |
| **Practical value** | Practically useful content is more likely to be shared, independent of emotion (control finding in Berger & Milkman 2012) | Would someone forward this to help a specific friend? | Package genuinely useful, self-contained units: checklists, calculators, templates — addressed to one job, one person |
| **Stories** | Information travels inside narratives; the brand must be integral to the story or it gets dropped in retelling (Berger, *Contagious*, ch. 6) | If a customer retells our story, do we survive the retelling? | Build a "Trojan horse" narrative where the product is the causal hinge of the outcome, not a logo on the slide |

**Sequencing rule:** Triggers and observability compound over months; emotion spikes and decays. For sustained WOM, fix triggers/observability first, use high-arousal content for launches.

---

## Part 2 — Referral Program Design

### 2.1 Prerequisite gate (do not skip)

A referral program multiplies existing advocacy; it cannot create it. Before designing incentives, verify:

1. **Activation is healthy** — a meaningful share of new users reach the value moment (compare against your own baseline; see the loop metrics table in `growth-loops-applied.md`).
2. **Organic referral exists** — some customers already refer with zero incentive. If nobody refers for free, an incentive buys low-quality invites, not advocacy.
3. **Unit economics survive the reward** — reward cost per converted invitee must come in under blended CAC, including fraud leakage.

### 2.2 Incentive structure: both-sides vs one-side

The controlling research is Ryu & Feick 2007 (*Journal of Marketing*, "A Penny for Your Thoughts"): four experiments showing rewards increase referral likelihood overall, but **who should get the reward depends on tie strength and brand strength**:

| Situation | What the research says | Design decision |
|-----------|------------------------|-----------------|
| Weak ties, weaker/unknown brand | Rewards matter most here; rewarding the **sender** is what moves behavior | Sender-weighted or both-sided; sender reward does the work |
| Strong ties, strong brand | Sender rewards add little (they'd refer anyway) and can feel mercenary; giving at least part of the reward to the **receiver** works better | Receiver-weighted or both-sided; the receiver's gift is the sender's social cover |
| Default when you can't segment | Both-sided splits capture both effects and protect the sender's self-image | Both-sided (Dropbox: 500MB each; Airbnb: credit each) |

Two field results to apply on top:

- **Frame the offer as a gift, not a bounty.** Airbnb A/B-tested "invite your friends, get $25" against "give your friends $25 to travel." The altruistic framing performed better globally (Airbnb Engineering, "Hacking Word-of-Mouth"). The sender is spending social capital; give them generosity to spend, not a commission to explain.
- **Prefer in-kind product currency over cash where the product allows.** Dropbox's storage reward cost marginal pennies, deepened product commitment on both sides, and selected for people who actually wanted the product. Cash selects for people who want cash.

### 2.3 Timing of the ask

Ask **after a value peak, never before value delivery**. Concrete decision rules:

- Trigger the ask on a *success event* (report generated, first result achieved, milestone hit, 5-star support resolution) — not on signup, not on a calendar schedule.
- Embed the ask where the value is visible (on the results screen), not in a settings page. Airbnb's rebuilt program moved referrals into the product's natural flow and reported signups and bookings up over 300%/day vs. their old bolt-on version, with bookings up 25%+ in some markets.
- Suppress the ask for users who haven't activated, have open support tickets, or just churn-signaled. An ask delivered into dissatisfaction converts badly and burns the channel.
- One re-ask per subsequent value peak is fine; recurring nag campaigns are not.

### 2.4 K-factor and cycle-time math

```
K = i × c
  i = invites sent per user (across the WHOLE user base, not just participants)
  c = conversion rate of invitees to activated users

New users after n cycles from seed N₀ (K < 1):
  Total ≈ N₀ × (1 + K + K² + ... + Kⁿ)  →  N₀ × 1/(1−K) as n → ∞
```

**Worked example.** Base of 10,000 active customers. Participation 15% → 1,500 senders. Senders average 4 invites → 6,000 invites → i = 0.6 invites per base user. Invitee activation c = 10%.

- K = 0.6 × 0.10 = **0.06** → cycle 1 yields 600 new customers, cycle 2 yields 36, cycle 3 yields ~2. Steady-state amplification ≈ 1/(1−0.06) → **~6.4% extra acquisition**. Real, but an amplifier.
- Double participation to 30% (better placement + timing): K = 0.12 → ~13.6% amplification.
- Also lift invitee activation to 15% (better invitee landing experience): K = 0.18 → ~22% amplification.
- **Cycle time sets compounding speed:** if signup→referral takes 7 days, those cycles play out in weeks; at 60 days, the same K delivers its total over quarters. Instrument median time from signup to first sent invite and shorten it (see the cycle-time table in `growth-loops-applied.md`).

**Lever priority from the math:** participation rate and invitee conversion multiply; invites-per-participant has diminishing (and spammy) returns. Never optimize invite volume first.

---

## Part 3 — Why Most Referral Programs Fail

1. **Asking before value delivery.** The ask lands at signup or day 3, before the user has experienced anything worth vouching for. Referral is spent trust; users won't spend what they haven't earned. Fix: gate the ask on a success event (2.3).
2. **Misaligned incentive.** Cash bounties for strong-tie referrals trigger impression-management concerns — the sender looks paid, not helpful (Ryu & Feick 2007). Or the reward is generous to the sender and empty for the receiver, so invites feel like exploitation (the exact failure Airbnb's give-framing fixed). Fix: match structure to tie/brand strength (2.2 table), gift-frame, both-sided default.
3. **Amplifying a loop that doesn't exist.** Product isn't better with more people, produces no shareable artifact, and has no organic referral — the program is a coupon engine bolted onto nothing. See "False Loop Detection" in `growth-loops-applied.md`. Fix: build one STEPPS driver into the product first (Part 1).
4. **Friction at the handoff.** Invite buried in settings, invitee lands on a generic homepage, account required before any value is visible. Every extra step taxes both i and c. Fix: audit the share→activation path click by click (`growth-loops-applied.md` Step 6).
5. **Reward leakage and fraud.** Self-referrals, disposable emails, reward farming. Pay the sender only on invitee *activation* (a real value event), not on signup; cap total rewards per account (Dropbox capped earned storage).
6. **Set-and-forget.** No owner, no dashboard, stale reward. Programs decay as the offer becomes wallpaper. Fix: quarterly review of the Part 4 metrics with one lever experiment per quarter.

---

## Part 4 — Measurement

Compare every metric to your own baseline and prior period — not to public case-study numbers (evidence doctrine: `knowledge/playbooks/conversion-rate-optimization.md`, Tier rules). Program data comes from your own instrumentation; per the Kai Data Provenance Rule, never report these numbers to a client without a collector source.

| Metric | Formula | What it diagnoses |
|--------|---------|-------------------|
| **Referral rate** | referred new customers ÷ total new customers (period) | Overall channel contribution (Dropbox's reported peak: 35%) |
| **Participation rate** | users who sent ≥1 invite ÷ eligible users | Ask placement, timing, and offer appeal |
| **Invites per participant** | invites sent ÷ participants | Motivation depth; watch for spam if incentives over-reward volume |
| **Invitee conversion** | invitees activated ÷ invites sent | Landing experience, gift value, sender targeting quality |
| **K-factor** | (invites ÷ all users) × invitee conversion | Whole-system health; trend matters more than level |
| **Cycle time** | median days, signup → first sent invite | Compounding speed |
| **Referred-customer quality** | referred cohort retention/LTV vs. matched non-referred cohort | Whether incentives are attracting real customers (expect referred ≥ non-referred per Schmitt et al. 2011; if referred < baseline, the incentive is buying junk) |
| **Cost per referred activation** | total rewards paid ÷ referred activations | Must beat blended CAC with margin for fraud |

**Instrumentation minimum:** unique referral links/codes, sender-invitee join keys, activation event (not signup) as the payout trigger, and cohort tags in the analytics store so referred-vs-baseline LTV is queryable.

---

## Ethics Rules (hard constraints)

- **No fake scarcity or fake social proof.** No invented "only 2 referral spots left," no fabricated "X friends already joined" counts. Real caps and real counts only.
- **No undisclosed incentivized endorsements.** A referral reward is a material connection. If the program asks customers to post publicly (reviews, social posts, testimonials), disclosure is required under the FTC Endorsement Guides — load `harness/references/creator-disclosure.md` and apply its per-surface disclosure formats. Never condition a reward on the review being positive, and never incentivize reviews on platforms that prohibit it (most do).
- **Incentivize the referral action, not the opinion.** Pay for a converted invite; never pay for sentiment.
- **No purchased or automated amplification** — no bought accounts, no astroturfed threads seeding "organic" recommendations (Instruction Contract stop-conditions apply).
- **Approval doctrine:** launching a program, sending referral emails, or changing live incentives is a live-channel mutation — human approval required before anything ships. Publishing stays OFF by default.

---

## How This Maps Into Kai

| Kai surface | Loads this doc for |
|-------------|--------------------|
| Growth planning (`knowledge/playbooks/growth-loops-applied.md`, `growth-hacker-first-hire-os.md`) | Deciding whether/when a referral program amplifies an existing loop; K-factor and cycle-time sizing |
| Campaign planning (`knowledge/playbooks/campaign-orchestration.md`, `scripts/campaigns/campaign_planner.py`) | Referral-ask email/in-product copy timing, incentive framing (gift vs. bounty), both-sides split |
| CRO and marketing audits (`knowledge/playbooks/conversion-rate-optimization.md`, `/kai` audit workflows) | Auditing an existing referral program against Part 3 failure modes and Part 4 metrics; provenance rules apply to every number reported |
| Content briefs for shareable assets (`harness/brief-schema.md` + skill contracts) | STEPPS scoring of drafts — which sharing driver the asset engineers, and the activation check (arousal, not just interest) |
| Influencer/creator work (`knowledge/playbooks/influencer-marketing.md`) | Boundary call: paid/gifted creators route there; customer referral incentives route here; both route disclosure through `harness/references/creator-disclosure.md` |

---

## Sources

- Berger, J. & Milkman, K. (2012). "What Makes Online Content Viral?" *Journal of Marketing Research* 49(2). https://journals.sagepub.com/doi/10.1509/jmr.10.0353
- Berger, J. & Schwartz, E. (2011). "What Drives Immediate and Ongoing Word of Mouth?" *Journal of Marketing Research* 48(5). https://journals.sagepub.com/doi/10.1509/jmkr.48.5.869
- Berger, J. (2013). *Contagious: Why Things Catch On*. Simon & Schuster. (STEPPS framework.)
- Schmitt, P., Skiera, B. & Van den Bulte, C. (2011). "Referral Programs and Customer Value." *Journal of Marketing* 75(1). https://journals.sagepub.com/doi/abs/10.1509/jm.75.1.46 · PDF: https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Schmitt-Skiera-vandenBulte-2011-Referral-Programs-Customer-Value.pdf
- Van den Bulte, C., Bayer, E., Skiera, B. & Schmitt, P. (2018). "How Customer Referral Programs Turn Social Capital into Economic Capital." *Journal of Marketing Research* 55(1). https://journals.sagepub.com/doi/10.1509/jmr.14.0653
- Ryu, G. & Feick, L. (2007). "A Penny for Your Thoughts: Referral Reward Programs and Referral Likelihood." *Journal of Marketing* 71(1). https://journals.sagepub.com/doi/10.1509/jmkg.71.1.084
- Airbnb Engineering. "Hacking Word-of-Mouth: Making Referrals Work for Airbnb." https://medium.com/airbnb-engineering/hacking-word-of-mouth-making-referrals-work-for-airbnb-46468e7790a6
- GrowSurf. "The Dropbox Referral Program: 3900% Growth in 15 Months" (secondary source for Dropbox figures, originally from Drew Houston's 2010 startup-lessons talk). https://growsurf.com/blog/dropbox-referral-program/
- Nielsen (2021). *Trust in Advertising Study*. https://www.nielsen.com/insights/2021/beyond-martech-building-trust-with-consumers-and-engaging-where-sentiment-is-high/ · Sell sheet: https://develop.nielsen.com/wp-content/uploads/sites/2/2022/02/2021-Nielsen-Trust-In-Advertising-U.S.-sell-sheet.pdf
- FTC. *Endorsement Guides: What People Are Asking*. https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking
