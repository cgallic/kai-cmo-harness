# Channel Distribution Checklist

> **Use when:** Picking which distribution channels to test, running a disciplined channel test, or deciding kill vs double-down on the path from $0 to $5M ARR.

This is the operational scorecard for the distribution suite. Pair it with the master playbook: `playbooks/growth-distribution-engine.md`. Route B2B motions through `playbooks/b2b-distribution-playbook.md` and B2C motions through `playbooks/b2c-distribution-playbook.md`. Log every test in `playbooks/experimentation-ledger.md`.

---

## 1. Channel-Market Fit Pre-Screen

Qualify a channel **before** spending a dollar testing it. Score each candidate channel 1-5 per question. Drop any channel scoring below 3 on audience presence or economics.

### Audience Present
- [ ] Confirm the target buyer **already gathers on this channel** in meaningful numbers
- [ ] Name the specific segment, search, hashtag, list, or community where they cluster
- [ ] Verify reach is the right buyer, not a lookalike adjacent audience
- [ ] Reject the channel if the audience is present but **never buys in this context**

### Economics Support The CAC
- [ ] Record ACV (or AOV) and gross margin per customer
- [ ] Estimate the channel's likely CAC from public benchmarks before testing
- [ ] Confirm contribution margin covers CAC with payback under the target window
- [ ] Flag low-ACV products on high-touch channels as **likely economic mismatches**

### Content Capability
- [ ] Confirm the team can produce the **format this channel rewards** (video, long posts, decks, threads)
- [ ] Verify production cadence is sustainable for at least one full test cycle
- [ ] Reject channels needing content the team cannot make or buy reliably

### Time-To-Signal Acceptable
- [ ] Estimate weeks-to-signal for this channel (see section 7)
- [ ] Confirm runway covers the signal window plus one iteration
- [ ] Deprioritize slow-signal channels when cash runway is short

### Team Able To Execute
- [ ] Name the single owner accountable for this channel test
- [ ] Confirm that owner has the skill or budget to run it well
- [ ] Verify founder time is available if the channel is founder-led (sales, LinkedIn, events)

**Pre-screen verdict:** Advance a channel only when it scores **3+ on every dimension** and **4+ on audience and economics**.

---

## 2. Channel Selection (Bullseye)

Pick the **first 3 channels** to test. List every plausible channel, score it, then commit to the top 3 by rank.

### Scoring Matrix Template

Score each channel 1-5 per column. Higher is better. For cost, score **inverse** (cheap = 5, expensive = 1).

| Channel | Reach (1-5) | Cost-efficiency (1-5) | Time-to-signal (1-5) | Confidence (1-5) | Total (/20) |
|---------|:-----------:|:---------------------:|:--------------------:|:----------------:|:-----------:|
| AI outbound | | | | | |
| AI UGC | | | | | |
| LinkedIn organic | | | | | |
| Events | | | | | |
| Sponsorships | | | | | |
| Organic TikTok | | | | | |
| Paid social | | | | | |
| SEO/AEO | | | | | |
| YouTube | | | | | |
| Webinars | | | | | |
| X | | | | | |
| Influencer | | | | | |

### Ranking Rules
- [ ] Score every candidate channel that passed the pre-screen
- [ ] Rank by total, breaking ties toward **faster time-to-signal**
- [ ] Pick the **top 3** as the active test slate
- [ ] Include at least one fast-signal channel so you learn something within weeks
- [ ] Commit the runners-up to a parked list, not the active slate
- [ ] Re-run the matrix after each test cycle with real CAC data replacing estimates

**Selection verdict:** Test exactly **3 channels** per cycle. Test fewer when budget is tight; never test more than you can resource fully.

---

## 3. Channel Test Design

Set up a valid test before launching. A test missing any item below is **not a test, it is spending**.

### Hypothesis Written
- [ ] Write the hypothesis as one sentence: channel, audience, offer, expected result
- [ ] State the belief being tested ("LinkedIn DMs convert founders to demos")
- [ ] Record the hypothesis in `playbooks/experimentation-ledger.md` before launch

### Budget And Time Committed
- [ ] Commit a minimum budget large enough to reach a readable sample
- [ ] Commit a minimum runtime covering the channel's time-to-signal
- [ ] Lock the budget and runtime so the test cannot be killed early on a bad week
- [ ] Cap the budget so a dead channel cannot drain the runway

### Leading Indicator Defined
- [ ] Pick **one leading indicator** that predicts the channel will work (see section 7)
- [ ] Choose an indicator that moves **before revenue does** (reply rate, watch time, CTR)
- [ ] Avoid vanity metrics that never connect to pipeline

### Success Threshold Pre-Registered
- [ ] Write the pass threshold **before** launch, not after seeing data
- [ ] Define the kill threshold at the same time
- [ ] Record both numbers in the ledger so results cannot be rationalized later

### Single-Variable Discipline
- [ ] Change **one variable per test** (channel, audience, offer, or creative)
- [ ] Hold everything else constant for the test window
- [ ] Avoid stacking three changes and losing the read

### Tracking And Attribution In Place
- [ ] Install tracking before launch, not after
- [ ] Confirm UTMs, source tags, or unique links route correctly
- [ ] Verify the conversion event fires end to end with a test submission
- [ ] Document any attribution gaps as **known gaps**, not guesses

**Design verdict:** Launch only when **every box above is checked**.

---

## 4. Test Health Mid-Flight

Read a test in progress without killing it prematurely. Check weekly.

### Enough Volume
- [ ] Confirm impressions, sends, or views have reached a readable sample
- [ ] Compare actual volume against the volume the test was designed to reach
- [ ] Pause judgment if volume is still **too thin to read**

### Leading Indicators Trending
- [ ] Track the pre-registered leading indicator week over week
- [ ] Note whether the indicator is rising, flat, or falling
- [ ] Look for **early signs of pull** even when revenue lags

### Under-Resourced vs Genuinely Dead
- [ ] Ask whether weak results come from **too little spend or effort**, not the channel itself
- [ ] Check execution quality: was content on-format, cadence consistent, targeting correct?
- [ ] Diagnose a flat test as **under-resourced** before declaring the channel dead
- [ ] Increase resourcing once before killing when the leading indicator shows any life

**Health verdict:** Continue when volume is sufficient and the leading indicator trends up; investigate execution before any kill.

---

## 5. Kill / Iterate / Double-Down Decision

Decide at the end of the committed window using the pre-registered thresholds. Use directional benchmark ranges, then anchor to **your own pre-registered numbers**.

### Kill The Channel When
- [ ] The leading indicator stayed **below the kill threshold** across the full window
- [ ] Volume was sufficient, so the read is real, not thin
- [ ] Execution quality was sound, so the channel itself failed
- [ ] Projected CAC sits **above contribution margin** with no clear path down
- [ ] Record the kill, the diagnosis, and the evidence in the ledger

### Iterate The Channel When
- [ ] The leading indicator landed **between kill and pass thresholds**
- [ ] One clear variable plausibly explains the gap (offer, creative, audience, hook)
- [ ] Change **one variable** and re-run for one more committed window
- [ ] Cap iterations at **2-3 cycles**, then kill if no break-through

### Double-Down When
- [ ] The leading indicator cleared the **pass threshold** with readable volume
- [ ] Early CAC sits **inside** the economic envelope from section 1
- [ ] A plausible path exists to spend more without CAC collapsing
- [ ] Advance the channel to the Scale Readiness gate (section 6)

**Decision verdict:** Kill, iterate, or scale based on the **pre-registered thresholds** plus an execution-quality check. Never extend a dead test on hope.

---

## 6. Scale Readiness

Gate every winning channel **before** pouring budget in. A channel that works at $5k/month can break at $50k/month.

### Unit Economics Gate
- [ ] Confirm **CAC payback** sits inside the target window (commonly **under 12 months** for B2B SaaS; faster for B2C)
- [ ] Confirm **LTV:CAC** clears a healthy ratio (a **3:1 or better** range is a common floor)
- [ ] Confirm **contribution margin** stays positive after fully loaded channel costs
- [ ] Use real test CAC, not the pre-screen estimate

### Ceiling Check
- [ ] Estimate the channel's **addressable ceiling** (audience size, inventory, search volume)
- [ ] Confirm the ceiling supports the revenue target before over-investing
- [ ] Model how CAC moves as spend rises, since cheap early CAC often **rises with scale**

### Operational Capacity
- [ ] Confirm sales, onboarding, or fulfillment can absorb the added volume
- [ ] Confirm content or creative production scales without quality collapse
- [ ] Name the owner and headcount needed at the higher spend level

### Tracking Integrity
- [ ] Re-verify attribution holds at higher volume
- [ ] Confirm dashboards report CAC, payback, and margin in near-real time
- [ ] Set guardrail alerts for CAC creep and margin erosion

**Scale verdict:** Scale only when **economics, ceiling, capacity, and tracking all pass**. Hold spend flat if any gate fails.

---

## 7. Per-Channel Quick-Reference Gate

For each channel, watch the **one leading indicator** that predicts it will work, and give it the rough time-to-signal below. Treat these as **directional benchmark ranges for 2026**, not guarantees. Confirm current platform behavior with live data before relying on any number.

| Channel | One leading indicator that predicts it works | Rough time-to-signal |
|---------|----------------------------------------------|----------------------|
| AI outbound | Positive reply rate per sequence | 2-4 weeks |
| AI UGC | Hook-rate / 3-second view-through | 2-4 weeks |
| LinkedIn organic | Profile-driven inbound replies and DMs | 4-8 weeks |
| Events | Qualified conversations booked per event | 1-2 events |
| Sponsorships | Tracked clicks and code redemptions per drop | 2-4 weeks per placement |
| Organic TikTok | Average watch time and saves per post | 3-6 weeks |
| Paid social | Cost per qualified lead at stable CTR | 2-4 weeks |
| SEO/AEO | Indexed pages ranking + AI-citation appearances | 3-6 months |
| YouTube | Average view duration and subscriber-per-view | 2-4 months |
| Webinars | Registration-to-attend and attend-to-demo rate | 1-3 webinars |
| X | Reply-driven profile visits and DMs | 4-8 weeks |
| Influencer | Tracked clicks and conversions per partner | 2-4 weeks per drop |

**Quick-reference rule:** Pick the row's indicator as your pre-registered leading metric in section 3. Give the channel **at least** its time-to-signal before any kill decision.

---

## 8. Compliance Gate

Clear every item before a channel goes live. Load `harness/references/creator-disclosure.md` for the full disclosure rules.

### Disclosure (FTC)
- [ ] Disclose paid relationships clearly on **influencer, UGC, and sponsorship** content
- [ ] Place disclosures where the audience sees them before engaging, not buried
- [ ] Confirm creators use platform disclosure tools plus plain-language tags
- [ ] Reject content that hides a material connection

### Deliverability And ToS (Outbound)
- [ ] Confirm outbound complies with **CAN-SPAM**, GDPR, and platform terms (`harness/references/cold-email-rules.md`)
- [ ] Verify sending-domain warmup, SPF, DKIM, and DMARC are in place
- [ ] Honor opt-outs and include required sender identification
- [ ] Avoid scraped lists or sending volumes that trigger ToS bans

### Consent (Events And Data Capture)
- [ ] Capture explicit consent before adding event contacts to marketing lists
- [ ] State at capture how the data will be used
- [ ] Store consent records so they can be produced on request

### No Fake Engagement Or Testimonials
- [ ] Use **no bought followers, fake reviews, or fabricated testimonials**
- [ ] Confirm every testimonial reflects a real customer with permission to use it
- [ ] Confirm every metric and claim in distribution content is sourced, not invented
- [ ] Stop and escalate when any channel asks for deception or platform-rule evasion

**Compliance verdict:** A channel **fails this gate on any single violation**. Fix it before launch — there is no partial pass.

---

## Final Scorecard

Rate each section 1-5 for how cleanly this channel cleared it:

| Section | Score (1-5) | Notes |
|---------|:-----------:|-------|
| 1. Channel-Market Fit Pre-Screen | | |
| 2. Channel Selection (Bullseye) | | |
| 3. Channel Test Design | | |
| 4. Test Health Mid-Flight | | |
| 5. Kill / Iterate / Double-Down | | |
| 6. Scale Readiness | | |
| 7. Per-Channel Quick-Reference | | |
| 8. Compliance Gate | | |
| **TOTAL** | **/40** | |

**Interpretation:**
- 34-40: **Disciplined** — this channel is being tested and scaled by the book
- 27-33: **Solid** — close 2-3 gaps before raising spend
- 20-26: **Loose** — tighten test design and thresholds before trusting results
- < 20: **Spending, not testing** — stop and rebuild the test before committing more budget

**Hard rule:** Section 8 is **pass/fail regardless of total**. Any compliance violation blocks launch even with a perfect score elsewhere.
