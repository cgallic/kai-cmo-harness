# AI UGC (B2C)

> **Use when:** Breaking the creative-volume bottleneck on paid social or organic short-form — mass-producing UGC-style video ad creative and faceless short-form at volume for a DTC/B2C brand chasing 0→$5M ARR.

---

## Quick Reference

- **Creative is the new targeting.** Meta and TikTok auction systems now do the audience work; your only real lever is the volume and quality of creative you feed them.
- **The bottleneck is creative throughput**, not ad spend or targeting. AI UGC exists to break that bottleneck.
- **Cost-per-creative drops ~10-50x** versus filming real UGC (directional benchmark: $150-500/video real creator vs ~$5-30/video AI). That changes the testing math.
- **Win rate stays low.** Expect roughly 1 in 10-20 AI creatives to beat your control, same as human UGC. Volume is the point, not a higher hit rate.
- **Disclosure is mandatory.** Fabricated testimonials and undisclosed synthetic endorsements are PROHIBITED. See `harness/references/creator-disclosure.md`.
- **Slop loses.** Dead eyes, robotic cadence, and non-native framing get skipped in the first 1.5 seconds. Pass-as-native is the quality bar.

---

## What AI UGC Is

**AI UGC is machine-produced video creative that mimics the look, framing, and cadence of real user-generated content.** It spans three production modes:

| Mode | What It Is | Best Use |
|------|------------|----------|
| **Full-synthetic** | AI avatar + AI voice + AI script, no human filmed | High-volume hook testing, faceless channels, localization at scale |
| **Hybrid** | Real human footage + AI editing, AI b-roll, AI hooks, AI variation | Highest pass-as-native rate; scaling a proven real-creator winner |
| **AI-assisted** | Human creator films; AI handles script ideation, captions, cut-downs, translations | Fastest path for brands with an existing creator pipeline |

The distribution thesis is simple. Paid social ROAS is throttled by how many *distinct* creative concepts you can test per week. A brand testing 5 creatives/week and a brand testing 50 are not playing the same game. AI UGC turns creative from a per-unit cost into a near-fixed-cost batch process — the core unlock behind the modern `playbooks/b2c-distribution-playbook.md` and `playbooks/growth-distribution-engine.md`.

---

## Why It Matters In 2026

### Creative is the new targeting

Meta Advantage+ and TikTok Smart+/GMV Max collapsed manual audience targeting into algorithmic optimization. Detailed-targeting levers shrank; broad-plus-creative-signal won. See `channels/meta-advertising.md` and `channels/tiktok-algorithm.md`.

The consequence: **the auction reads your creative as the targeting input.** A scroll-stopping hook tells the algorithm who to find. So the constraint moved upstream — to how fast you can generate, test, and replace creative.

### The volume math

A high-velocity DTC account burns creative. Hooks fatigue in 7-21 days. A single winning concept needs 5-15 fresh variations before it tops out. Run that across 3-4 concepts and you need **30-60 net-new creatives per month** just to hold ROAS flat.

Filming that with real creators costs $5K-30K/month and takes 2-4 weeks of lead time. **AI UGC compresses both** — same volume, a fraction of the cost, same-day turnaround. That is the lever, and it is why AI UGC sits at the center of the 0→$5M ARR paid-social engine.

---

## The Tool Stack (2026)

Pick tools by job, not by hype. Stack three layers: **generation**, **voice**, **assembly**.

### AI avatar / spokesperson

| Tool | Positioning | Best-Fit Use |
|------|-------------|--------------|
| **Arcads** | Purpose-built for ad creative; large library of licensed UGC-style actors, hook-variation workflows | Highest-volume ad testing; native ad feel out of the box |
| **Creatify** | Ad-first; URL-to-video, product-aware avatars, batch hooks | E-commerce product ads, fast concept-to-variant |
| **Captions AI** | Strong lip-sync and editing; AI Ad/AI Creator features, expressive avatars | Creator-style talking-head with better realism |
| **HeyGen** | Broad avatar platform; custom avatars, strong API, translation | Custom-likeness spokesperson, scaled API pipelines |
| **Synthesia** | Enterprise/corporate avatar tool; polished but less "native UGC" | Explainers, B2B, internal — usually too clean for B2C UGC |

**Use Arcads or Creatify for ad volume.** Use Captions for realism. Reserve Synthesia for corporate explainers — its polish reads as a brand ad, not as UGC, and that hurts native feel.

### AI video generation (b-roll, scenes, motion)

| Tool | Positioning | Best-Fit Use |
|------|-------------|--------------|
| **Google Veo** | Top-tier realism, audio-aware generation, long coherence | Hero b-roll, lifestyle scenes, product-in-context shots |
| **Runway** | Mature creative suite; Gen-class models, video-to-video, editing tools | Stylized b-roll, motion edits, controllable iteration |
| **Sora-class** | Long, coherent generative scenes from prompt | Concept films, dream-sequence hooks, scene b-roll |
| **Pika** | Fast, cheap, fun; effects and quick clips | Pattern-interrupt cutaways, meme-style inserts |

Treat generative video as **b-roll and pattern-interrupt fuel**, not as your talking spokesperson. Full generative humans still trip the uncanny-valley filter in close-up.

### AI voice

| Tool | Positioning | Best-Fit Use |
|------|-------------|--------------|
| **ElevenLabs** | Best-in-class voice realism, emotion, multilingual, voice cloning | Voiceover for faceless edits, localization, avatar dub |

Voice quality is where most AI UGC dies. **Use ElevenLabs, tune stability and style, and add natural pauses** — flat cadence is the #1 robotic tell. Clone a voice only with documented consent (see Disclosure).

### Scripts, faceless pipelines, batch tooling

- **AI script tools** (Claude, ChatGPT): generate hook variations, angle matrices, persona-mapped scripts. Pair with `knowledge/personas/_persona-index.md`.
- **Faceless-channel pipelines** (e.g. submagic-style caption/editing tools, auto-cutters): script → voice → stock/AI b-roll → captions → export, no face on camera.
- **Batch creative tools** (Arcads/Creatify batch modes): one script → many avatars/hooks in a single render job.

---

## Hybrid Workflows (Highest Win Rate)

Full-synthetic is cheapest. **Hybrid converts best.** Combine real human signal with AI scale.

| Pattern | How It Works | Why It Wins |
|---------|--------------|-------------|
| **Real creator + AI variants** | Film 1 strong real UGC, then AI-generate 20+ hook/edit variations | Native authenticity of real footage, volume of AI |
| **AI b-roll under real VO** | Real founder/customer voice, AI-generated supporting scenes | Trust of real voice, cost of synthetic visuals |
| **AI translation/localization** | Take one winning ad, dub + lip-sync into 10 languages | One winner → global reach without re-filming |
| **AI hooks on real footage** | Swap only the first 3 seconds with AI-generated hook variants | Tests the highest-impact 3 seconds cheaply |

**Localization is the most underrated lever.** A proven English winner dubbed into Spanish, Portuguese, German, and French via ElevenLabs + HeyGen can 4-5x addressable reach for near-zero marginal cost — the fastest geographic expansion path in the 0→$5M distribution engine.

---

## Production Pipeline

The pipeline turns one idea into a batch. Run it as an assembly line, not as one-off edits.

```
Script → Hook variations → Avatar/Voice render → Edit/b-roll → Caption → Batch export → Naming → Ad-account ingestion
```

### Concrete batch workflow: 1 script → 20-50 variants

1. **Write 1 core script** mapped to one persona and one angle (problem-led, testimonial, etc.).
2. **Generate 10-15 hook variations** of only the first sentence (the first 3 seconds carry most of the win).
3. **Render across 3-5 avatars** in the batch tool — different age/gender/setting reads.
4. **Layer 2-3 voice takes** (pace, tone) on the strongest avatars.
5. **Add 2 edit treatments** — captioned talking-head vs talking-head + b-roll cutaways.
6. **Export** at 9:16, 1080×1920, platform-safe (no cross-platform watermark — a TikTok suppression trigger per `channels/tiktok-algorithm.md`).
7. **Name and ingest** into Meta/TikTok ad accounts as distinct ads in one ad set or campaign.

That is **1 script → ~30 testable creatives in a single afternoon.** Repeat across 3 scripts and the account has 90 fresh creatives per cycle.

### Naming convention

Deterministic names make winner attribution possible. Bake the variables into the filename.

```
{brand}_{persona}_{angle}_{hook##}_{avatar}_{edit}_{lang}_{date}_v{n}.mp4

# Examples
acme_admin-martyr_problem-led_h03_av-female-32_talkinghead_en_20260617_v1.mp4
acme_admin-martyr_problem-led_h07_av-male-45_broll_es_20260617_v1.mp4
```

| Field | Meaning |
|-------|---------|
| `persona` | Target persona from the persona index |
| `angle` | Script framework (problem-led, testimonial, POV…) |
| `hook##` | Hook variation number — the key test variable |
| `avatar` | Avatar identity/read |
| `edit` | Treatment (talkinghead, broll, greenscreen) |
| `lang` | Locale for localized variants |

When the account dashboard shows `h07` winning across avatars, you know the *hook* won — not the actor — and you scale that hook. Naming is what makes the testing engine learn.

---

## Hook & Script Frameworks That Convert

Hooks decide everything. The first 1.5 seconds determine distribution (see `channels/tiktok-algorithm.md`). Bold the pattern, then write to it.

| Framework | Opening Move | Best For |
|-----------|--------------|----------|
| **Problem-led** | Name the pain in sentence one | Direct-response, high-intent |
| **3 reasons** | "3 reasons I stopped doing X" | Educational, listicle pacing |
| **Unboxing** | Hands-on product reveal | Physical DTC, tactile products |
| **POV** | "POV: you finally found…" | Relatable, scroll-native |
| **Testimonial** | Result-first statement of change | Social proof, conversion |
| **Founder-story** | "I built this because…" | Brand trust, premium positioning |
| **Green-screen react** | Talking head over a screenshot/article | Commentary, trend-jacking |

### Script template (problem-led, 20-30s)

```
[0-2s]  HOOK: "{Name the exact pain}. Here's what fixed it."
[2-5s]  AGITATE: "{Why the usual fix fails}"
[5-15s] REVEAL: "{Product as the mechanism — show, don't claim}"
[15-22s] PROOF: "{Specific, true result — no fabricated numbers}"
[22-28s] CTA: "{Single concrete action}"
```

### Hook-variation matrix

```
Core claim: "{Product} fixed {problem} in {timeframe}."

h01  Question:     "Still {doing painful thing}?"
h02  Contrarian:   "Everyone's wrong about {category}."
h03  Result-first: "I {achieved result} in {timeframe}."
h04  POV:          "POV: you just found {product}."
h05  Callout:      "If you {trait}, watch this."
h06  Curiosity:    "This {object} changed how I {action}."
h07  Number:       "3 reasons I switched to {product}."
```

Apply algorithmic-authorship rules to spoken scripts too: **conditions after the main clause, verbs first, short sentences.** "Save this if you run ads" — not "If you run ads, save this."

---

## Creative Testing Integration

AI UGC only pays off when it feeds a disciplined testing engine. Volume without structure is just noise.

### The velocity loop

```
Batch render (30-50) → Ingest as distinct ads → Run on broad + algorithmic targeting
        → Read hook rate / hold rate / CPA at 2-3 days
        → Kill bottom, scale winners, generate 10 variants of each winner
        → Repeat weekly
```

This mirrors the **iterate-don't-diversify** logic in `channels/tiktok-algorithm.md`: find the winner, then make many variations of *that*, not ten unrelated new ideas.

### Metrics that gate decisions

| Metric | What It Measures | Read As |
|--------|------------------|---------|
| **Thumbstop / 3-sec rate** | Hook strength | Below ~30% = hook is dead, kill fast |
| **Hold rate (avg % watched)** | Body strength | Low hold = script/pacing problem |
| **Hook rate** | 3-sec views ÷ impressions | The single best leading indicator |
| **CPA by creative** | Bottom-line efficiency | The decision metric |
| **Win rate** | Creatives that beat control | ~5-10% is normal; volume compensates |

Directional benchmarks (2026, treat as ranges, not guarantees): **thumbstop 25-40%, hold rate 15-30%, AI-creative win rate 5-10%.** Your account's control sets the real bar.

### Fatigue

Hooks fatigue fast — frequency climbs, hook rate decays in 7-21 days. **Rotate before CPA spikes, not after.** AI UGC's whole value is having the next 20 variants already rendered when fatigue hits. Pre-render the bench.

---

## Quality Bar & The Slop Risk

Cheap creative that gets skipped is worse than no creative — it spends budget and teaches the algorithm nothing. **The bar is pass-as-native.**

### What makes AI UGC flop

| Tell | Fix |
|------|-----|
| **Dead eyes / frozen gaze** | Pick avatars with micro-movement; cut away before the stare sets in |
| **Robotic voice cadence** | ElevenLabs with tuned style + manual pauses; vary pace mid-script |
| **Too-clean framing** | Add handheld shake, real-room lighting, imperfect framing |
| **Mismatched lip-sync** | Use top lip-sync tools (Captions/HeyGen); keep takes short |
| **Generic stock feel** | Real b-roll or AI b-roll with product actually in frame |
| **No native opener** | Open the way real users do — mid-thought, casual, vertical |

### Pass-as-native checklist

- [ ] Works on MUTE (visual hook in first 0.7s)
- [ ] Opens mid-thought, not with a brand intro
- [ ] Voice has natural pauses and pace variation
- [ ] Vertical, slightly imperfect framing
- [ ] No cross-platform watermark
- [ ] Captions are native-style, not corporate lower-thirds

### When to use real creators instead

Use real UGC when **trust is the bottleneck**: high-ticket purchases, health/finance claims, ingestibles, or anything where a viewer must believe a *real person* used it. AI UGC tests angles cheaply; real creators close trust-heavy categories. The best programs use AI to *find* the winning angle, then re-shoot the winner with a real creator (see `playbooks/influencer-marketing.md`).

---

## Disclosure & Compliance (Non-Negotiable)

**Read `harness/references/creator-disclosure.md` before shipping any synthetic creative.** AI UGC creates real legal exposure. These rules are hard blocks, not guidance.

### Prohibited — stop here

- **Fabricated testimonials.** A synthetic person stating a customer experience that no real customer had is a deceptive testimonial. PROHIBITED.
- **Invented people implying real customers.** An AI avatar presented as a named, real customer who does not exist is deceptive endorsement. PROHIBITED.
- **Undisclosed synthetic endorsements** where disclosure is required. PROHIBITED.
- **Unauthorized likeness or voice cloning.** Cloning a real person's face or voice without documented consent. PROHIBITED.
- **Deepfaking real individuals** (founders, celebrities, customers) without explicit written consent. PROHIBITED.

### FTC exposure

The FTC Endorsement Guides and the Consumer Reviews and Testimonials Rule treat **fake and AI-generated endorsements as deceptive.** Key constraints:

- An endorsement must reflect a **real experience by a real endorser.** A synthetic spokesperson may not state or imply personal use it never had.
- Claims voiced by an avatar must still be **substantiated** — the avatar does not launder an unproven claim.
- **Material connections** must be disclosed clearly and early (16 CFR 255.5).

### Platform AI-content disclosure

| Platform | Requirement |
|----------|-------------|
| **TikTok** | Toggle the AI-generated content label on realistic synthetic media. Unlabeled AI content is a suppression trigger (`channels/tiktok-algorithm.md`). |
| **Meta (FB/IG)** | Apply AI-disclosure labeling on photorealistic AI content per Meta policy; see `channels/meta-advertising.md` and `channels/instagram.md`. |
| **All** | Disclosure does not cure deception — labeling a *fake testimonial* still leaves it a fake testimonial. |

### Likeness, voice, and consent

- Use **licensed avatar libraries** (Arcads/Creatify/HeyGen stock actors come with usage rights) for synthetic spokespeople.
- Clone a real voice or face **only with a signed release** specifying paid usage, platforms, and duration.
- Record AI/synthetic-media status per asset in campaign evidence, per the creator-disclosure evidence checklist.

### Pre-ship gate

- [ ] No fabricated testimonial or invented "real customer"
- [ ] Every claim independently substantiated
- [ ] Platform AI label enabled where required
- [ ] Likeness/voice rights documented for any cloned identity
- [ ] Material connection disclosed in-context
- [ ] Synthetic-media status logged in asset evidence

If any box is unchecked, **hold the asset** — do not ship.

---

## Measurement

AI volume changes the unit economics of creative. Track the new math.

| Metric | Formula / Definition | Why It Changes With AI |
|--------|----------------------|------------------------|
| **Cost per creative** | Total creative cost ÷ creatives produced | Drops 10-50x; testing becomes near-free |
| **Cost per winner** | Creative cost ÷ winning creatives | The metric that actually matters at volume |
| **Win rate** | Winners ÷ creatives tested | Stays ~5-10%; you buy wins with volume |
| **Hook rate** | 3-sec views ÷ impressions | Leading indicator; read at 1-2 days |
| **Hold rate** | Avg watch % | Body-strength diagnostic |
| **Thumbstop** | 3-sec/2-sec view rate | Scroll-stop power of the hook |
| **CPA by creative** | Spend ÷ conversions, per ad | The kill/scale decision metric |

**The key shift: optimize cost-per-winner, not cost-per-creative.** Cheap creative is the means; a steady supply of winners is the end. When cost-per-creative approaches zero, testing more is almost always correct — the only ceiling is the algorithm's learning capacity and your compliance capacity.

---

## Cold-Start Runbook (First 30 AI UGC Ads)

1. **Pick 1 persona** from `knowledge/personas/_persona-index.md` and 1 product angle.
2. **Write 3 core scripts** — problem-led, testimonial, POV.
3. **Generate 10 hook variants** across the 3 scripts.
4. **Render in one batch tool** (Arcads or Creatify): 3-5 avatars × hooks = ~30 ads.
5. **Run pass-as-native + disclosure gates** on every asset. Label AI content.
6. **Name deterministically** and ingest as 30 distinct ads into broad/algorithmic campaigns.
7. **Spend to ~50-100 impressions/creative minimum**, then read hook rate and CPA at 2-3 days.
8. **Kill the bottom half. Keep 3-5 with the best hook rate.**
9. **Log winners and losers** — feed losers to `memory/what-doesnt-work.md`, winners to `knowledge/playbooks/what-works.md`.

Goal of cold start: **find 2-3 hooks that beat your control.** Not scale — signal.

---

## Scale Runbook

1. **Take each proven hook** and render 10-15 fresh variations (new avatars, edits, b-roll).
2. **Localize winners** — dub the top 3 into your top non-English markets via ElevenLabs + HeyGen.
3. **Pre-render the fatigue bench** — keep the next 20 variants ready before CPA climbs.
4. **Re-shoot the single biggest winner with a real creator** for trust-heavy scaling (`playbooks/influencer-marketing.md`).
5. **Run the weekly velocity loop**: ingest → read at 2-3 days → kill/scale → re-batch.
6. **Hold compliance discipline** — every new asset re-clears the disclosure gate. Scale multiplies legal exposure, so the gate is not optional.
7. **Feed the learning loop** — diagnose recurring losers, graduate repeat lessons into checklist lines per the harness learning loop.

At scale, the brand runs a **creative factory**: a fixed weekly batch cadence feeding the paid-social auction more tested concepts than any competitor relying on filmed UGC. That throughput advantage is the engine behind the 0→$5M ARR B2C distribution thesis (`playbooks/b2c-distribution-playbook.md`, `playbooks/growth-distribution-engine.md`).

---

## Cross-References

- `channels/tiktok-algorithm.md` — hook/retention mechanics, iterate-don't-diversify, AI-label suppression
- `channels/meta-advertising.md` — Advantage+ creative signal, AI disclosure labeling
- `channels/instagram.md` — Reels distribution and native feel
- `playbooks/influencer-marketing.md` — when to use real creators, UGC rights and contracts
- `harness/references/creator-disclosure.md` — FTC, platform labels, evidence per asset
- `playbooks/b2c-distribution-playbook.md` — where AI UGC sits in the B2C channel mix
- `playbooks/growth-distribution-engine.md` — the creative-volume engine for 0→$5M ARR
