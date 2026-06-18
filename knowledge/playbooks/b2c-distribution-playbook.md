# B2C Distribution Playbook

> **Use when:** Sequencing the full channel stack for a B2C / DTC company going from $0 to $5M revenue. This is the motion-specific layer under `playbooks/growth-distribution-engine.md` — read the master first for channel-agnostic strategy, then use this file to pick, order, and stack B2C channels.

---

## Thesis

**B2C distribution is a creative-volume engine wrapped in a paid-organic flywheel.** A consumer company gets to $5M not by finding one clever channel but by producing enough creative that something hits, then putting paid behind the winners while organic and influencer feed the top. The bottleneck is almost never spend. **The bottleneck is creative volume and the discipline to scale only what proves out.**

Three forces drive the B2C engine:

1. **Creative volume** — test many concepts; a small share will carry the account. Volume beats polish early.
2. **The paid↔organic flywheel** — organic finds the hook, paid scales it, paid data sharpens the next organic round.
3. **Retention economics** — acquisition only works if contribution margin and repeat revenue support the CAC. **Ignoring LTV kills more B2C companies than weak ads.**

Margin and AOV set the strategy:

- **Low margin / low AOV** (impulse, sub-$50): organic + UGC must do the heavy lifting; paid only works at scale with tight CAC.
- **High margin / high AOV** ($150+, strong repeat): paid can scale aggressively because each customer absorbs more CAC.

Pick channels by where your product is discovered and whether your margin can fund paid.

---

## B2C Channel Stack — Overview

| Channel | Margin fit | Time-to-signal | Cost to start | Ceiling | Deep guide |
|---------|-----------|----------------|---------------|---------|-----------|
| **AI UGC** | All | 1-3 weeks | Low-Med | High | `channels/ai-ugc.md` |
| **Organic TikTok / Reels / Shorts** | All, esp. low-AOV | 2-8 weeks | Low (time) | Very High | `channels/tiktok-algorithm.md`, `channels/instagram.md`, `channels/youtube.md` |
| **Paid social** | Med-High AOV | 1-2 weeks | Med-High | Very High | `channels/paid-acquisition.md`, `channels/meta-advertising.md` |
| **Events / experiential** | High AOV/brand | 1 cycle | High | Med | `channels/events-experiential.md` |
| **Influencer** | All | 2-6 weeks | Med-High | High | `playbooks/influencer-marketing.md` |
| **Sponsorships** | Brand-led | 1 cycle | Med-High | Med | `channels/sponsorships.md` |
| **Referral / viral loops** | All | 2-8 weeks | Low | High | `playbooks/growth-loops-applied.md` |
| **SEO / AEO** | All | 3-6 months | Low-Med | High | `channels/seo-content.md`, `frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` |
| **Email / SMS lifecycle** | All | 1-4 weeks | Low | High (retention) | `channels/email-lifecycle.md` |
| **Retail / marketplace** | Product-dependent | 1-2 quarters | Med-High | High | `playbooks/growth-distribution-engine.md` |

**Time-to-signal** = how long before a true read, not a vanity spike. **Ceiling** = scale before saturation for one company. Every cell is a directional benchmark; your data replaces it.

---

## Primary Channels — How Each Works

### AI UGC
**What it is:** User-generated-style creative produced with AI (avatars, voiceover, b-roll assembly, scripted hooks) at volume. The creative-volume unlock for B2C in 2026.

- **Right first channel when:** you need many ad/organic concepts fast and can't film dozens of human UGC videos per week. Strong for any margin because it slashes cost-per-concept.
- **Time-to-signal:** 1-3 weeks. Ship 15-30 variations and read hook rate + hold rate.
- **Cost:** low-medium — tooling plus editing time. Far cheaper per concept than studio shoots.
- **How it compounds:** more concepts tested means more winners found; winning hooks template into the next batch. Feeds both organic posting and paid testing.
- **Deep guide:** `channels/ai-ugc.md`. Disclosure: AI content must follow platform AI-disclosure rules — see `harness/references/tiktok-ads-policy-reference.md` and `harness/references/advertising-compliance.md`.

### Organic TikTok / Reels / Shorts
**What it is:** Native short-form video posted organically across TikTok, Instagram Reels, and YouTube Shorts. The cheapest large-scale discovery engine for consumer products.

- **Right first channel when:** the product is visual, demonstrable, or impulse-driven, and AOV is low enough that paid CAC is tight. The default first channel for low-AOV DTC.
- **Time-to-signal:** 2-8 weeks of consistent posting (1-2/day) to find a format that travels.
- **Cost:** low in dollars, high in volume discipline. The cost is consistency, not spend.
- **How it compounds:** an organic hit costs nothing and finds the message paid will scale. The algorithm rewards consistency. Winning organic clips become paid ads.
- **Deep guides:** `channels/tiktok-algorithm.md`, `channels/instagram.md`, `channels/youtube.md` (Shorts section).

### Paid social
**What it is:** Meta, TikTok, and increasingly other social ad platforms, run on the creative your organic and UGC engine produces. The primary scale lever once a message proves out.

- **Right first channel when:** margin/AOV can fund CAC ($100+ AOV or strong repeat), and you already have a proven hook to scale. Rarely the literal first move — it scales winners, it doesn't find them cheaply.
- **Time-to-signal:** 1-2 weeks per creative test once pixels have data.
- **Cost:** medium-high. Budget for creative testing, not just media — the creative is the variable that moves CAC.
- **How it compounds:** paid data reveals which audiences and hooks convert, sharpening the next organic round. Spend scales linearly with winning creative supply.
- **Deep guides:** `channels/paid-acquisition.md`, `channels/meta-advertising.md`. Policy floor: `harness/references/meta-ads-rules.md`, `harness/references/meta-ads-api-reference.md`. Checklist: `checklists/meta-advertising-checklist.md`.

### Events / experiential
**What it is:** Pop-ups, sampling, activations, and IRL experiences that create memorable brand moments and content.

- **Right first channel when:** AOV/brand value is high, the product benefits from physical trial (food, beauty, apparel), or local density matters. A brand and content lever, not a first acquisition channel.
- **Time-to-signal:** one event cycle (4-8 weeks with content follow-on).
- **Cost:** high per event. The return is brand lift and content, harder to attribute directly.
- **How it compounds:** activations generate UGC and organic content that outlives the event. Builds brand affinity that lifts conversion everywhere.
- **Deep guide:** `channels/events-experiential.md`. Sponsorship mechanics: `channels/sponsorships.md`.

### Influencer
**What it is:** Paid and gifted partnerships with creators whose audiences match your buyer — from nano to mid-tier, run at portfolio volume.

- **Right first channel when:** your category trusts creators (beauty, wellness, food, apparel, gadgets) and you need fast social proof plus reach. Often a strong first or second channel for B2C.
- **Time-to-signal:** 2-6 weeks per cohort. Run many small creators to find the few that convert.
- **Cost:** medium-high. Mix gifting (low cost, high volume) with paid placements for winners.
- **How it compounds:** creator content becomes whitelisted paid ads (often the best-performing creative); repeated partnerships build associative trust; winning creator hooks template into AI UGC.
- **Deep guide:** `playbooks/influencer-marketing.md`.

### Sponsorships
**What it is:** Podcast, newsletter, and event sponsorships to reach owned audiences at scale with a brand message.

- **Right first channel when:** you have a brand message that resonates and a margin that can absorb mid-funnel spend. A scale and brand layer, not a cold-start channel.
- **Time-to-signal:** one cycle (2-6 weeks) per placement with promo-code attribution.
- **Cost:** medium-high per placement.
- **How it compounds:** repeated placements compound recall; trusted-host read transfers credibility. Promo codes give cleaner attribution than most paid.
- **Deep guide:** `channels/sponsorships.md`.

---

## Supporting Channels

| Channel | Role in the B2C stack | Deep guide |
|---------|----------------------|-----------|
| **Referral / viral loops** | Turn customers into a distribution channel via referral, sharing, and built-in loops. Lowers blended CAC. | `playbooks/growth-loops-applied.md` |
| **SEO / AEO** | Compounding inbound for considered purchases and branded/category search. Cites you in AI answers. | `channels/seo-content.md`, `frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` |
| **Email / SMS lifecycle** | The retention engine — welcome, abandoned cart, post-purchase, winback. Where margin is actually made. | `channels/email-lifecycle.md` |
| **Retail / marketplace** | Amazon, shelf, and marketplace distribution. Adds reach but compresses margin and data. | `playbooks/growth-distribution-engine.md` |

**Retention rule:** Stand up email/SMS lifecycle EARLY, even before scaling paid. Repeat revenue is what funds acquisition. A leaky retention bucket makes every paid dollar lose money.

---

## Pick Your First 2-3 Channels

Choose by margin, AOV, and product type. Commit 90 days. Do not start more than three.

### Low margin / low AOV ($0-$50, impulse)

```
PRIMARY    Organic TikTok / Reels    (free discovery; paid CAC is too tight to lead with)
SECONDARY  AI UGC                     (creative volume to feed organic + later paid)
THIRD      Email / SMS lifecycle      (repeat revenue is the only path to margin)
```

Add paid only once organic finds a hook with real conversion, then scale carefully.

### High margin / high AOV ($150+, considered or repeat)

```
PRIMARY    Paid social               (margin funds CAC; scale a proven hook)
SECONDARY  Influencer                (social proof + whitelisted ad creative)
THIRD      Email / SMS lifecycle      (high AOV rewards strong post-purchase flows)
```

Layer SEO/AEO for considered purchases where buyers research first.

### Mid margin / mid AOV ($50-$150)

```
PRIMARY    AI UGC + Organic short-form  (find the message cheaply)
SECONDARY  Paid social                  (scale the winners; watch payback)
THIRD      Influencer + referral        (borrowed reach + viral lift)
```

### Quick selector

| If your product is... | Start with |
|-----------------------|-----------|
| Visual, impulse, sub-$50 | Organic TikTok/Reels + AI UGC |
| Considered, researched before buying | SEO/AEO + paid social |
| Trusted via creators (beauty/wellness/food) | Influencer + AI UGC |
| High AOV with strong margin | Paid social + email/SMS |
| Built to be shared or invite-driven | Referral loops + organic |
| Physical-trial dependent (food/beauty) | Events/sampling + influencer |

---

## How the Flywheel Works Together

B2C distribution is a loop, not a funnel. **Organic and UGC find the message; paid scales it; the data sharpens the next round; influencer and email amplify both ends.**

```
        ┌─────────────────────────────────────────────┐
        │                                              │
        ▼                                              │
   AI UGC + ORGANIC   →  find winning hooks cheaply     │
        │                                              │
        ▼                                              │
   PAID SOCIAL        →  scale winning hooks; reveal     │
        │                converting audiences            │
        ▼                                              │
   INFLUENCER         →  borrowed reach + whitelisted    │
        │                ad creative (often the best)    │
        ▼                                              │
   EMAIL / SMS        →  convert + retain; fund the CAC  │
        │                                              │
        ▼                                              │
   REFERRAL LOOPS     →  customers recruit customers ────┘
                         (lowers blended CAC)
```

How the pieces feed each other:

- **Organic/UGC → paid:** the organic hit is your next ad. Never launch paid creative that hasn't shown signal organically when you can avoid it.
- **Paid → organic:** paid audience and hook data tells the content team what to make next.
- **Influencer → paid:** whitelisted creator content is frequently the highest-ROAS ad creative you'll run.
- **Email/SMS → everything:** retention revenue raises the CAC you can profitably pay, which unlocks more paid scale.
- **Referral → blended CAC:** every referred customer drops blended CAC and buys you room to scale paid.

---

## Sequenced Build Order

### $0 → $1M (find the creative engine + first paid winners)

```
WEEKS 1-4    Stand up organic short-form (TikTok/Reels): 1-2 posts/day.
             Build the AI UGC pipeline: 15-30 concept variations/week.
             Install email/SMS basics (welcome, abandoned cart, post-purchase).
WEEKS 4-8    Read organic: which hooks travel? Which formats convert?
             Launch small influencer cohort (gifting + a few paid) to find converters.
WEEKS 8-12   Take proven organic/influencer hooks into paid social as creative.
             Start small ($50-150/day); judge on CAC vs contribution margin, not ROAS alone.
WEEKS 12-20  Scale only creatives that hold CAC. Kill the rest fast.
             Tighten lifecycle flows — repeat revenue funds the next push.
WEEKS 20-24  Lock the creative-volume cadence. Read blended CAC and MER weekly.
             Document which hooks and audiences win. Cut dead channels.
```

**Exit test:** a repeatable creative engine produces winners, paid holds CAC against contribution margin, and retention/repeat revenue is measured. (See `playbooks/marketing-by-stage.md` Early→Growth checklist.)

### $1M → $5M (scale paid on creative supply + compound retention)

```
QUARTER 1    Scale paid on the proven creative engine. Hire/contract creative volume.
             Expand lifecycle: segmentation, winback, loyalty, SMS flows.
QUARTER 2    Build an influencer portfolio (many creators, whitelist the winners).
             Launch referral / viral loop to lower blended CAC.
QUARTER 3    Add a brand layer: sponsorships, events/experiential for high-AOV brands.
             Stand up SEO/AEO for considered purchases and branded search capture.
QUARTER 4    Diversify paid beyond one platform. Add retail/marketplace if it fits margin.
             Rebalance spend to MER and contribution margin, not channel ROAS vanity.
```

**Exit test:** creative supply, not spend, is the only constraint on paid; blended CAC is stable; retention and referral materially lower it. (See Growth→Scale checklist.)

---

## Weekly Operating Cadence

```
MONDAY     Review: blended CAC, MER, contribution margin, payback by cohort.
           Decide which creatives scale, which die. Brief the week's concepts.
TUE-THU    Ship 15-30 new AI UGC / organic concepts. Post organic daily.
           Launch new paid creative tests. Brief influencer cohort.
FRIDAY     Read creative performance: hook rate, hold rate, CAC by creative.
           Promote winners to scale; log to `knowledge/playbooks/what-works.md`.
           Log losers + diagnosis to `memory/what-doesnt-work.md`.
WEEKLY     Audit lifecycle flow performance (open, click, revenue per send).
MONTHLY    Run /kai-retro. Rebalance budget by MER. Verify channel-distribution-checklist.
```

Run every ad and creative through the quality + policy gates before it ships: `four_us_score.py` (10/16 for ads), `banned_word_check.py`, plus the platform policy reference. Validate the full plan against `checklists/channel-distribution-checklist.md`.

---

## Measurement

Measure blended economics and margin, not platform-reported ROAS alone. Every quantitative client-facing claim follows the Kai Data Provenance Rule — collect first, cite the source.

| Metric | What it tells you | Evidence needed |
|--------|-------------------|-----------------|
| **Blended CAC** | True acquisition cost across all spend and customers | Total spend / new customers |
| **MER (marketing efficiency ratio)** | Total revenue / total marketing spend — the honest scale gauge | Revenue + spend source |
| **Contribution margin** | Revenue after COGS, shipping, fees, returns | Unit economics by SKU |
| **Contribution-margin CAC payback** | Months until a customer's margin repays acquisition | CM per order + repeat rate |
| **First-order vs blended CAC** | Whether repeat revenue is carrying the model | Cohort repeat data |
| **LTV (contribution-margin LTV)** | Total margin a customer returns over time | Cohort retention curves |
| **Repeat / retention rate** | Whether acquisition compounds or leaks | Order history by cohort |
| **Hook rate / hold rate (creative)** | Creative-market fit; what to scale | Platform creative analytics |

Benchmark ranges are local calibration, not universal truth. Directionally, B2C aims for **CM-CAC payback inside the first 1-3 orders** and **CM-LTV:CAC above 3:1** — but replace these with the company's real unit economics before any recommendation.

---

## Failure Modes

| Failure | What it looks like | Fix |
|---------|-------------------|-----|
| **Scaling paid before the creative engine exists** | Spend up, CAC up, no winning creative | Build creative volume first; scale proven hooks only. |
| **Ignoring retention / LTV** | Profitable first order, unprofitable business | Stand up lifecycle early; price CAC against CM-LTV, not first order. |
| **Optimizing platform ROAS, not blended margin** | Platform says winning, bank account says losing | Steer by MER and contribution margin. |
| **Too few creative concepts** | One ad fatigues, no replacement | Ship 15-30 concepts/week; treat creative as the core asset. |
| **Polishing instead of testing** | Months on one hero video | Volume beats polish early; let the algorithm pick winners. |
| **Single-platform dependency** | 90% spend on one ad platform | Diversify once a winner is proven; platform shocks are existential. |
| **Buying followers/fake UGC** | Hollow vanity metrics, no conversion, policy risk | Earn real engagement; disclose AI/sponsored content per platform rules. |
| **No attribution discipline** | Can't tell which channel works | Use promo codes, post-purchase surveys, and MER as ground truth. |
| **Skipping retention math at launch** | CAC looks fine until repeat fails to materialize | Model cohort retention before scaling spend. |

---

## See Also

- Master strategy: `playbooks/growth-distribution-engine.md`
- B2B motion: `playbooks/b2b-distribution-playbook.md`
- Stage sequencing: `playbooks/marketing-by-stage.md`
- Growth loops: `playbooks/growth-loops-applied.md`
- Channel selection checklist: `checklists/channel-distribution-checklist.md`
