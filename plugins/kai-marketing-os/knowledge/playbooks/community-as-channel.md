# Community as a Growth Channel

> **Use when:** Deciding whether to invest in community as a growth motion, diagnosing a stalled community, or wiring an existing community into pipeline and content loops. This is the strategy layer — when community is the right motion, community-market fit, the member journey, growth loops, and measurement.
>
> **Read alongside:** [`channels/community-building.md`](../channels/community-building.md) (tactics: platform tables, channel architecture, rituals, moderation — that doc owns execution detail), [`playbooks/growth-distribution-engine.md`](./growth-distribution-engine.md) (community is 1 of 19 traction channels — test it like any other), [`playbooks/growth-loops-applied.md`](./growth-loops-applied.md) (loop mechanics), [`playbooks/referral-and-word-of-mouth.md`](./referral-and-word-of-mouth.md) (referral program mechanics).

Community is the slowest channel to compound and the easiest to fake with vanity metrics. It is also one of the few channels a competitor cannot copy in a quarter. The failure mode is symmetric: companies that need community skip it because it's slow, and companies that don't need it launch a Slack because a board member mentioned Notion. This doc is the decision framework for telling those apart — and for running community as a channel with loops and numbers, not as a cost center with vibes.

---

## 1. The Decision: Right Motion vs Money Pit

Community building appears in the 19 traction channels of *Traction* (Weinberg & Mares) — meaning it competes for test budget against every other channel and must win on evidence, not sentiment. Run this gate before any community investment.

### Community is the right motion when ≥2 of these hold

| Fit signal | Why it works | Examples of the pattern |
|------------|--------------|------------------------|
| **Practice-based product** | Users are building a *skill or craft* with the product; peers accelerate mastery and mastery drives retention | Design tools, dev tools, no-code builders, fitness programs, trading platforms, creator tools |
| **Identity-dense niche** | Members see the topic as part of who they are; belonging is the draw, product is the context | Homelab, mechanical keyboards, ultrarunning, indie SaaS founders, specialty coffee |
| **High-touch B2B with a definable role** | Buyers share a job title with real professional loneliness; peer benchmarking is worth more than your content | RevOps, community managers themselves (CMX), CISOs, heads of remote |
| **Template/extension surface** | The product improves when members share artifacts (templates, plugins, configs) — contribution has built-in utility | Notion templates, Figma plugins, game mods |
| **Support-heavy product** | Question volume is high and answers are reusable; peer answers deflect tickets and become searchable content | Complex SaaS, hardware, open source |

### Community is a money pit when

- **The product is transactional or low-frequency.** Nobody joins a community for their tax filing tool or one-time purchase. There is no ongoing practice to discuss.
- **The category is spend-based, not identity-based.** People buy it but don't identify with it. Test: would a user voluntarily put the topic in their social bio? If not, expect a ghost town.
- **You cannot name the non-product conversation.** If every plausible thread is about your product (bugs, feature requests), you want a support forum, not a community. Support forums are fine — just budget them as support, not growth.
- **Leadership wants pipeline in one quarter.** Community pipeline lags quarters behind investment — plan on 6-12 months as a working assumption, not a measured benchmark (see §7 on lag). If the mandate is this-quarter leads, run outbound or paid instead ([`playbooks/demand-generation.md`](./demand-generation.md)).
- **No human owner exists.** See §8. A community with no host is a liability: dead channels are publicly visible negative social proof, worse than no community.
- **A great community already owns the niche.** If a subreddit or independent forum is the acknowledged home, participate there (see social-native strategy, §5) instead of fragmenting it. You will lose a head-to-head against an incumbent community.

**Decision rule:** ≥2 fit signals AND zero money-pit conditions → proceed to a community-market-fit test (§2). Otherwise, put the budget into a channel with faster feedback and revisit at the next stage gate ([`playbooks/marketing-by-stage.md`](./marketing-by-stage.md)).

The base rates justify caution: in CMX's 2025 Community Industry Report, ROI remains the #1 reported challenge for community professionals, and only 24% can quantify their community's value in financial terms — though nearly half of those who can report over $1M in impact ([CMX 2025](https://www.cmxhub.com/community-industry-report)). Community pays, but mostly for teams that picked the right motion and instrumented it.

---

## 2. Community-Market Fit

Community-market fit is the community analog of product-market fit: a specific group of people repeatedly shows up, talks to *each other* (not just to you), and would object loudly if you shut it down. David Spinks (*The Business of Belonging*, CMX founder) frames the method as **constraining the group first**: run the smallest viable community for one tight segment, iterate cheaply until it self-sustains, and only then spend on growth ([Spinks](https://www.amazon.com/Business-Belonging-Community-Competitive-Advantage/dp/1119766125)).

### The constrained pilot (8-12 weeks)

1. **Pick one segment, not "our users."** One role, one skill level, one use case. 20-40 hand-picked people, personally invited.
2. **Declare the business objective before launch.** Use Spinks' SPACES taxonomy — Support, Product (feedback/ideation), Acquisition, Contribution, Engagement/retention, Success — and pick **one** primary driver. A community asked to do all six does none.
3. **Run minimum programming** (§4) with the founder or a senior operator hosting. No paid tooling, no public launch, no logo contest.
4. **Measure member-to-member ratio weekly** (conversations not involving staff / total conversations).

### Verdicts at week 8-12

| Signal | Verdict |
|--------|---------|
| Member-to-member ratio >50% and rising; members start threads unprompted; someone organizes something you didn't plan | **Fit.** Open the doors, add programming, assign the owner. |
| Activity exists but every thread starts with staff; ratio <30% | **No fit yet.** Change the segment or the format (maybe this audience wants events, not chat) before spending more. |
| Silence within 2 weeks of staff stepping back | **No fit.** Archive gracefully, tell the pilot members why, log the lesson. Do not "relaunch" the same design. |

Treat this exactly like a Bullseye middle-ring channel test ([`playbooks/growth-distribution-engine.md`](./growth-distribution-engine.md)): cheap, time-boxed, with a kill criterion written down before you start.

---

## 3. The Member Journey: Lurker → Contributor → Leader

Participation inequality is a law, not a bug. Nielsen's 90-9-1 rule: in most online communities ~90% of members lurk, ~9% contribute occasionally, ~1% produce most of the activity ([NN/g](https://www.nngroup.com/articles/participation-inequality/)). You cannot repeal it — Nielsen's own guidance is to *shift* the curve slightly, not fight it. Design one ladder rung per tier:

| Stage | Who they are | What moves them up one rung | What kills the move |
|-------|--------------|----------------------------|---------------------|
| **Lurker** (~90%) | Reads, gets value silently, may still buy | Zero-effort participation: polls, emoji reactions, "reply with one word" prompts; direct @-welcome within 48h of joining | Walls of text, "introduce yourself with your full story" as first ask, guilt-tripping lurkers |
| **Contributor** (~9%) | Answers questions, shares occasionally | Recognition within hours of first post (named, specific); being *asked* for their take on a thread in their wheelhouse | First post ignored (the single biggest drop-off); pedantic moderation of early attempts |
| **Leader** (~1%) | Starts threads, welcomes others, organizes | Real responsibility: mod status, event hosting, early access, direct founder line; public credit | Treating them as free labor with no input on direction; hiring a stranger over them |

Two operating rules from the distribution:

- **First-reply SLA is the highest-ROI intervention.** A first-time poster who gets a substantive reply within hours is the contributor pipeline; one who gets silence lurks forever. Staff the SLA (target <4h, see metrics in [`channels/community-building.md`](../channels/community-building.md)) before staffing anything else.
- **Count lurkers as reached, not failed.** Lurkers read, learn, and buy. Measure their consumption (readers per thread) separately from contribution.

For teams that want a finer-grained model, the open-source **Orbit Model** formalizes this as orbit levels (observers → users → contributors → advocates) with "love" (involvement) and "reach" (influence) per member ([Orbit Model](https://github.com/orbit-love/orbit-model)). Useful for instrumenting who is drifting inward vs outward.

---

## 4. Programming Cadence

Programming is the schedule of things that happen whether or not conversation happens organically. Communities die from irregularity faster than from small size.

**The minimum viable cadence (pilot through ~500 members):**

| Cadence | Item | Owner |
|---------|------|-------|
| Daily | Welcome new members; enforce first-reply SLA | Community owner (human) |
| Weekly | One recurring anchor ritual (wins thread, weekly question) — same day, same format, every week | Owner hosts; Kai drafts |
| Biweekly-monthly | One live event: AMA, workshop, member spotlight call | Owner or member-leader hosts |
| Monthly | One contribution ask (challenge, template swap, feedback thread mapped to your SPACES objective) | Owner |

Rules:

1. **Consistency beats volume.** One ritual that fires 52 weeks straight builds more habit than five that fire sporadically. Add a second ritual only when the first runs without staff prompting.
2. **Programming is a hypothesis.** Each ritual serves a journey transition (§3) or the SPACES objective (§2). A ritual nobody engages with for 4 consecutive runs gets redesigned or cut — log it in the experimentation ledger ([`playbooks/experimentation-ledger.md`](./experimentation-ledger.md)).
3. **Kai drafts, humans host.** Kai can generate the full programming calendar, prompt copy, event run-of-show, and recap posts. A human posts and hosts them (§8). Full ritual menu with formats: [`channels/community-building.md`](../channels/community-building.md).

---

## 5. Platform Selection

The per-platform comparison table (Discord vs Slack vs Circle vs Facebook Groups vs Discourse, size sweet spots, effort) lives in [`channels/community-building.md`](../channels/community-building.md). This section owns the *strategic* axis that table doesn't: what each platform class does for growth.

| Class | Growth property | Trade-off | Choose when |
|-------|----------------|-----------|-------------|
| **Owned forum** (Discourse, Circle w/ public spaces) | Threads are **indexable** — every answered question becomes a permanent SEO/AEO asset feeding the UGC loop (§6) | Slower-feeling, higher setup effort, needs critical mass to not look dead | Support-heavy or practice-based products with high question volume; long-horizon SEO strategy |
| **Real-time chat** (Discord, Slack) | Highest intimacy and speed; best for belonging and identity-dense niches | Content is **unindexed and evaporates** — knowledge created today is unfindable in a month; zero SEO value | Community whose value is relationships and real-time help, not a knowledge base |
| **Social-native** (subreddit, Facebook Group, LinkedIn Group) | Built-in discovery — the platform brings members | Rented land: algorithm and policy risk, limited data, weak ownership | Existing niche gravity is on that platform; or participating in an incumbent community instead of building (§1) |

Decision rules:

- **If the UGC → SEO loop is part of the thesis, you need an indexable surface.** Chat-only communities forfeit that loop entirely. A common hybrid: Discord for belonging + a public forum or docs-integrated Q&A for the searchable layer.
- **Rented vs owned is a stage decision, not a religion.** Early: go where the audience already is. Once community-market fit is proven and the member list is an asset, migrate the core to an owned surface — and plan for most nominal members not to cross (only the engaged migrate; that is the point — size the new home on engaged-member count, not the total roster).
- **Never split a small community across platforms.** One home until the single home is unambiguously active.

---

## 6. Community-Led Growth Loops

A community that doesn't feed an acquisition or revenue loop is a retention amenity — sometimes worth it, but budget it honestly. Three loops turn community into a channel. Loop mechanics and modeling: [`playbooks/growth-loops-applied.md`](./growth-loops-applied.md).

### Loop 1: UGC → SEO/AEO

```
Member asks question → community answers → indexable thread ranks in search
and gets cited by answer engines → searcher lands on thread → joins community
(or enters product funnel) → asks/answers more questions
```

Requirements: indexable platform (§5), question-shaped demand in the niche, moderation that keeps answer quality high. Compounding is slow (quarters) but the asset is durable and, unlike your blog, scales with member count instead of headcount. Distill top threads into proper articles via the content pipeline — community threads are Information Gain raw material ([`frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`](../frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md)).

### Loop 2: Member referral

```
Member gets value → invites a peer ("you should be in here") → peer joins →
peer gets value → invites their peer
```

The strongest version is unincentivized — the invite is a gift, not a commission. Instrument "how did you hear about us?" on join. Amplifiers: member-only artifacts worth sharing (templates, benchmarks, salary surveys), public member wins, invite-a-peer prompts after high-value moments. Formal incentive mechanics belong to [`playbooks/referral-and-word-of-mouth.md`](./referral-and-word-of-mouth.md).

### Loop 3: Events → content → members

```
Community hosts event (AMA, workshop) → recording + recap become public
content → content distributed on social/SEO → viewers join community
→ larger community attracts better speakers/attendees
```

This is the loop where community and the events channel compound each other — event mechanics: [`channels/events-experiential.md`](../channels/events-experiential.md); repurposing mechanics: [`playbooks/transcript-to-content-ops.md`](./transcript-to-content-ops.md).

**Loop discipline:** pick ONE loop as primary, matched to your SPACES objective and platform class. Instrument it end to end before adding a second.

---

## 7. Measurement

Two tiers: health metrics (is the community alive?) and business metrics (is it a channel?). Health metrics with thresholds — DAM, member-to-member ratio, first-reply time, 30-day retention — live in [`channels/community-building.md`](../channels/community-building.md). This section owns the channel tier.

### Engaged-member rate (the denominator that matters)

```
engaged_member_rate = members with ≥1 contribution or event attendance in 30d / total members
```

Total member count is the vanity metric of community — it only ever goes up. Report engaged members as the real size, and expect the 90-9-1 distribution (§3) when setting targets: for a general community, ~10% engaged is normal, not failure. Track the *trend*; a falling engaged rate with rising totals means you're filling a leaky room.

### Community-sourced and community-influenced pipeline

- **Community-sourced:** first identifiable touch was the community (joined before any other tracked touch). Requires joining community identity to CRM — by email match, or with signal tooling such as [Common Room](https://www.commonroom.io/solutions/community/) that merges community activity with pipeline data.
- **Community-influenced:** account had ≥1 engaged community member active before or during the deal cycle. Always report sourced and influenced as separate numbers; influenced will be several times larger and mixing them destroys credibility.
- Add **self-reported attribution** ("how did you hear about us?") as a third lens — it consistently surfaces community/word-of-mouth touches that click-based attribution misses.

Secondary value lines, mapped to SPACES: support deflection (tickets answered by peers × cost per ticket), retention delta, product feedback shipped, content produced from community threads.

### Attribution caveats (state these in every report)

1. **Selection effect ≠ causal effect.** Community members who buy more may have joined *because* they were already high-intent. Comparing member vs non-member conversion or retention without controlling for intent overstates the effect. Present these as correlations; a holdout or cohort-matched comparison is the honest upgrade.
2. **Community is multi-touch by nature.** A member who lurked for 8 months then converted via a paid ad is invisible to last-click. Use sourced/influenced/self-reported side by side; never let one model be "the" number ([`playbooks/analytics-attribution.md`](./analytics-attribution.md)).
3. **Lag makes early reads worthless.** Do not judge community pipeline before ~2 quarters of data; do not extrapolate from the first enthusiastic cohort.
4. **The industry mostly fails at this** — ROI is the #1 challenge in CMX's 2025 report and most practitioners cannot quantify impact ([CMX 2025](https://www.cmxhub.com/community-industry-report)). Instrument sourced pipeline from day one of the pilot, or accept that the channel will lose every budget fight.

**Kai Data Provenance Rule applies:** any client-facing community report must run the collector, declare its mode, and source every number. Engaged-member rates and pipeline figures come from platform exports and CRM joins, never from estimates.

---

## 8. Staffing Reality: Kai Drafts, Humans Host

Community is the one channel in this repo that cannot be run by the agent. Belonging requires a person members recognize; an obviously synthetic host reads as astroturfing and poisons trust — and undisclosed automated personas violate the Instruction Contract outright.

**Division of labor:**

| Kai does (drafting, analysis) | Human owner does (live channel) |
|-------------------------------|--------------------------------|
| Programming calendars, ritual prompts, event run-of-shows | Posts them, hosts events, is present daily |
| Welcome-message and recap drafts | Sends/personalizes them; builds actual relationships |
| Thread → article distillation through the content pipeline + gates | Approves and attributes correctly |
| Engagement analytics, journey-stage reports, pipeline joins | Judgment calls: moderation, conflicts, member disputes |
| Member-leader candidate lists from activity data | The ask, the trust, the ongoing leader relationship |

Rules:

- **No community without a named human owner** who has hours budgeted for it (near-daily presence pre-scale; the scaling ratios and mod structure live in [`channels/community-building.md`](../channels/community-building.md)). "Marketing owns it" is not an owner.
- **Approval doctrine:** every message Kai drafts for a live community surface is a live-channel action — human approval required before posting, per repo doctrine and [`harness/references/social-automation-rules.md`](../../harness/references/social-automation-rules.md). Automated posting into a community without disclosure is a Stop condition.
- **Budget honestly:** the true cost of community is the owner's salary-hours, not the platform fee. If those hours don't exist, the answer to §1 is "not yet" regardless of fit signals.

---

## How This Maps Into Kai

- **`kai-growth-plan` / channel selection** (`playbooks/growth-distribution-engine.md` flow) — loads §1-2 when community appears in the Bullseye outer ring: fit gate, pilot design, kill criteria.
- **`kai-launch` / `campaign-orchestration.md`** — loads §4 and §6 when a launch or campaign includes a community component: programming calendar drafts, loop selection, event-repurposing chain.
- **`kai-write` / `kai-social` content tasks** — community prompt and recap drafts follow §8 division of labor; every draft is gated and human-approved before it touches a live surface (`harness/skill-contracts/social-post.yaml`).
- **`kai-weekly-audit` / `kai-monthly-audit` reviews** — load §7 for engaged-member rate and sourced-vs-influenced pipeline definitions, with the attribution caveats stated verbatim; provenance rules apply to every number.
- **`kai-audit` / growth audits** — §1 money-pit conditions are the checklist for flagging an existing community as a cost sink; §2 verdict table for relaunch-vs-archive recommendations.
- Tactical execution (platform setup, channel architecture, moderation, ritual formats) always defers to [`channels/community-building.md`](../channels/community-building.md).

---

## Sources

- Jakob Nielsen — "Participation Inequality: The 90-9-1 Rule for Social Features," Nielsen Norman Group: https://www.nngroup.com/articles/participation-inequality/
- CMX — 2025 Community Industry Trends Report: https://www.cmxhub.com/community-industry-report (landing page now serves the latest edition; 2025 PDF: https://43963373.fs1.hubspotusercontent-na1.net/hubfs/43963373/2025%20CMX%20Community%20Industry%20Report.pdf)
- David Spinks — *The Business of Belonging* (SPACES model, community-market fit via constrained groups): https://www.amazon.com/Business-Belonging-Community-Competitive-Advantage/dp/1119766125
- CMX — "SPACES Framework in Action": https://www.cmxhub.com/blog/spaces-framework-in-action-match-your-community-work-to-business-goals
- Gabriel Weinberg & Justin Mares — *Traction* (community building as 1 of 19 channels, Bullseye Framework): https://www.amazon.com/Traction-Startup-Achieve-Explosive-Customer/dp/1591848369
- The Orbit Model (open-source member-journey framework: orbit levels, love, reach): https://github.com/orbit-love/orbit-model
- Common Room — community signals to pipeline (tooling for community-CRM joins): https://www.commonroom.io/solutions/community/
