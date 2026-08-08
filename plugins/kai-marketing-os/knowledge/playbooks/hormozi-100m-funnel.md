# $100M Funnel Playbook — The Hormozi Operating Sequence

> **Use when:** Standing up or rebuilding a full acquisition system on the Hormozi frameworks (Grand Slam Offer, Core Four, give-away-everything content, money models), or running the five-skill sequence — `/kai-offer-builder` → `/kai-proof-builder` → `/kai-hook-bench` → `/kai-content-batching` → `/kai-funnel-audit` — end to end for a brand.

Grounding: `knowledge/people/alex-hormozi-knowledge.md` (canonical distillation of $100M Offers, $100M Leads, $100M Money Models). Competitor mechanics extraction: `knowledge/playbooks/funnel-hack-offer-architecture.md`.

---

## The Operating Map

Five mechanisms, one dependency chain. Each downstream mechanism inherits the one above it. Get them out of order and the system produces expensive noise.

### 1. The Value Equation (governs the offer)

```
              Dream Outcome × Perceived Likelihood of Achievement
Value  =  ─────────────────────────────────────────────────────────
                    Time Delay × Effort & Sacrifice
```

Raise the numerator (vivid outcome, belief that it works *for them*), shrink the denominator (first win inside 7 days, done-for-you over do-it-yourself). Every offer, hook, and content piece in this playbook is scored against these four variables.

### 2. The Grand Slam Offer (the root artifact)

An offer that cannot be price-compared: attractive promotion + a value stack nothing else matches + premium price + risk-reversing guarantee, sold in a category of one. Built by: market selection (massive pain, purchasing power, easy targeting, growing), listing every problem/obstacle and naming a fix for each, trim-and-stack by value/cost, guarantee design (conditional service guarantee as default), real scarcity/urgency, MAGIC naming (Make, Adjective, Goal, Interval, Container). Full step-by-step lives in the knowledge doc; the skill executes it.

### 3. Client-Financed Acquisition (governs the economics)

Make the front-end offer price high enough that acquisition cost is covered — ideally profited — from day one, then convert to continuity. The generalized form is the money model: **a deliberate sequence of offers that makes customers worth more than their acquisition cost, ideally within 30 days.** Three stages:

| Stage | Job | Mechanism |
|-------|-----|-----------|
| Get Cash | Acquire at or above breakeven | Attraction offer (high-ticket front end, paid challenge, priced diagnostic) |
| Get More Cash | Raise AOV at the moment of maximum intent | Upsell/downsell immediately post-purchase (Unsell → Prescribe → Frame the Choice → Simplify Payment) |
| Get the Most Cash | Compound with recurring revenue | Continuity: membership, retainer, subscription — bonuses worth 2-3 months of payments to join |

The 8× rule: 2× customer value × 2× acquisition volume × 2× payment speed = 8× growth. Multiplicative, not additive.

### 4. The Core Four (governs lead flow)

Every lead comes from exactly one of four channels. Master in this order of feedback speed: **Warm outreach** (people who know you — zero spend, fastest signal) → **Cold outreach** (strangers, 1:1 — compliment, commonality, proof, 15-minute CTA, 5-7 touches minimum) → **Content** (strangers at scale — Hook, Retain, Reward; Give-Give-Give-Ask) → **Paid ads** (bought attention — platform, targeting, hook in first 3 seconds). The Rule of 100 forces consistency: 100 outreaches/day, or 100 minutes of content/day, or $100/day ad spend, for 100 consecutive days.

### 5. Give-Away-Everything Content (governs trust)

Give away the secrets, sell the implementation. Roughly 1% of free-content consumers implement alone; the other 99% are the market. Content is the proof of competence — it converts trust, the actual bottleneck, at scale. Production model: fixed cadence, batch recording, long-form for authority + short-form for reach, 1 recording session → dozens of derivative assets, a lead magnet CTA in every piece. Lead magnets must be narrow, painful, and point at the problem the core offer solves — good enough that you could charge for them.

---

## The Run-in-Sequence Pipeline

Run the five skills in this order. Each stage consumes the artifacts of the previous stage; skipping a stage means the next one runs on assumptions instead of decisions.

| # | Skill | Consumes | Produces | Gate to next stage |
|---|-------|----------|----------|--------------------|
| 1 | `/kai-offer-builder` | `MARKETING.md`, market/competitor evidence (run `knowledge/playbooks/funnel-hack-offer-architecture.md` workflow for competitor mechanics) | `workspace/offer-builder/` — offer document: dream outcome, value stack, price, guarantee, MAGIC name, money-model sketch | Human approves the offer (price, guarantee exposure, claims). No downstream work on an unapproved offer. |
| 2 | `/kai-proof-builder` | Approved offer from `workspace/offer-builder/`; real testimonials, results, reviews, case data | `workspace/proof-library/` — sourced proof assets mapped to offer claims; `_data-gaps.md` for missing proof | Every offer claim has a cited proof asset or a logged gap. Provenance rules below apply in full. |
| 3 | `/kai-hook-bench` | Offer + proof library; persona from `knowledge/personas/_persona-index.md` | `workspace/hook-bench/` — scored hook variants per channel (Hook-Retain-Reward openers) | Hooks pass `four_us_score.py` at 10/16 and `banned_word_check.py`. Hooks may only promise what the proof library supports. |
| 4 | `/kai-content-batching` | Winning hooks from `workspace/hook-bench/`; give-away-everything pillar topics | `workspace/content-batch/` — batched pillar + derivative content with lead-magnet CTAs | Publishing assets pass 12/16 (10/16 for ads/email), banned-word check, and human approval before anything goes live. |
| 5 | `/kai-funnel-audit` | 30+ days of live runtime data: `data/content_log.json`, ad/analytics pulls, money-model performance | `workspace/funnel-audit/` — stage-by-stage funnel scorecard, CPL/CLV:CAC readout, loop-back directives | Findings route back to the stage they implicate (see loop-back table). Then re-audit quarterly. |

**Why offer comes first:** hooks advertise the offer, content earns trust *toward* the offer, proof substantiates the offer's claims, and the audit measures the offer's economics. Change the offer and every downstream artifact is stale. This is the "Starving Crowd > Offer Strength > Persuasion Skills" hierarchy operationalized — the sequence invests in the higher-order variable before the lower one.

### Gate commands (run at every stage boundary)

```bash
python scripts/quality_gates/four_us_score.py --file <file>      # 12/16 publishing, 10/16 ads/email/hooks
python scripts/quality_gates/banned_word_check.py --file <file>  # instant reject on any hit
```

Max 2 retry cycles per asset, naming the specific failing dimension. After 2 failures, escalate to a human and log the diagnosis in `memory/lessons.md`.

### Data provenance (stages 2 and 5 especially)

Any quantitative or client-facing claim — review counts, conversion rates, CPL, "top pains," testimonial results — must come from a real collected source. Load `harness/references/audit-data-provenance.md` and run:

```bash
python -m scripts.audit.collect --url <url> --mode <mode> --workflow <workflow> --out <data-folder>
```

Missing data goes in `_data-gaps.md`. Never invent proof, stats, or testimonials — a proof library with three real assets beats one with thirty imagined ones. Before the stage-5 audit hands off, run `python scripts/quality_gates/audit_provenance_lint.py workspace/funnel-audit --audit-dir`.

### Approval doctrine

Nothing publishes or mutates a live channel (site, ad account, social profile, email list) without explicit human approval. The pipeline produces approved-and-staged artifacts; a human ships them.

---

## Decision Points: Skips and Loop-Backs

### When to skip or shorten a stage

| Situation | Adjustment |
|-----------|------------|
| Offer already exists and converts profitably | Skip stage 1's build; run `/kai-offer-builder` in review mode only — score the existing offer against the Value Equation and confirm the money model covers CAC within 30 days. If it passes, proceed. |
| Proof-poor early-stage business (no clients yet) | Do not fabricate around the gap. Shrink stage 2 to founder-credibility assets plus a conditional service guarantee (risk reversal substitutes for social proof), and start warm outreach (Core Four #1) to generate the first documentable results. Loop back to `/kai-proof-builder` after the first 3-5 client outcomes. |
| Service business (agency, consulting, coaching) | Full sequence. Weight stage 1 toward guarantee + scarcity design (capacity is real), stage 3-4 toward long-form authority content and the free-book/lead-magnet funnel pattern. |
| Product/ecommerce business | Insert the competitor-mechanics teardown from `knowledge/playbooks/funnel-hack-offer-architecture.md` before stage 1; weight the money model toward upsell path and subscription attach. Hand page-level conversion work to `/kai-cro` and `/kai-landing-page`. |
| Established content engine already running | Keep the engine; stages 3-4 re-point existing cadence at the new offer and hooks rather than rebuilding. Hand derivative production to `/kai-repurpose`. |
| One-off asset needed mid-sequence | Do not fork the pipeline — hand off to `/kai-write` (single pieces), `/kai-case-study` (proof assets), `/kai-social` (posts), or `/kai-brief` (briefs). |

### Evidence that forces a loop-back

| Signal (from `/kai-funnel-audit` or live data) | Loop back to |
|---|---|
| Leads arrive but do not buy; price objections dominate; CLV:CAC below 3:1 | Stage 1 — offer. Rework the value stack, guarantee, or price. Do not answer an offer problem with more traffic. |
| Prospects ask "will this work for someone like me?"; guarantee claims spike; testimonials feel thin on sales calls | Stage 2 — proof. Collect fresh sourced results; check `_data-gaps.md` for what was never substantiated. |
| Impressions healthy but CTR/hook-rate poor; cost per click climbing on unchanged targeting | Stage 3 — hooks. Bench new variants; retire fatigued ones. |
| Hooks earn the click but engagement dies mid-piece; list growth flat despite volume | Stage 4 — content. Fix Retain/Reward: the pieces promise and don't deliver, or the lead magnet is a vitamin, not a painkiller. |
| Winners unclear because tracking is broken or logs are sparse | Stage 5 itself — fix instrumentation before drawing any conclusion. Log the gap; never estimate. |
| A piece grades `underperformer` at the 30-day check | Diagnose via `/kai-retro` into `memory/what-doesnt-work.md`; winners feed `knowledge/playbooks/what-works.md`. |

---

## Operating Cadence

| Cadence | Actions |
|---------|---------|
| **Daily** | Rule of 100 on the chosen Core Four channel (100 outreaches, 100 content minutes, or $100 ad spend). No exceptions — compounding starts after the flat part of the curve. |
| **Weekly** | Ship the content batch (post-approval). Review hook-bench scores against live CTR; promote winners, bench replacements. Capture any new client result into `workspace/proof-library/` while it is fresh. Run gate scripts on everything staged. |
| **Monthly** | 30-day checks on published pieces (`data/content_log.json`). Money-model pulse: front-end cash collected vs. acquisition spend — still client-financed? Re-score the offer against the Value Equation if win-rate or objections shifted. Run `/kai-retro` after any sprint with 5+ gated pieces. |
| **Quarterly** | Full `/kai-funnel-audit` → `workspace/funnel-audit/`. Act on loop-back table above. Refresh competitor offer mechanics per `knowledge/playbooks/funnel-hack-offer-architecture.md`. Re-confirm market criteria (pain, purchasing power, targetability, growth) still hold. |
| **First cycle only** | Run stages 1-4 in sequence, then let the funnel run 30 days before the first `/kai-funnel-audit`. Auditing before real runtime data exists produces opinions, not findings. |

---

## Anti-Patterns

- Running hooks or content before the offer is approved — persuasion polish on a weak offer is the most expensive mistake in the system.
- Buying traffic to fix a conversion problem (loop back to offer/proof instead).
- Inventing proof, review counts, or "typical results" — provenance rules exist because this is the fastest way to destroy the trust the content model is building.
- Fake scarcity or fake deadlines — real constraints only; discovered fakery poisons the guarantee too.
- Discounting the main offer instead of adding bonuses.
- Quitting the content cadence at month 3 — the model prices in a 6-12 month compounding delay.
- Auditing weekly — funnel-level signals need runtime; 30 days minimum, quarterly thereafter.

---

## Related

- `knowledge/people/alex-hormozi-knowledge.md` — full framework definitions and tactical playbooks
- `knowledge/playbooks/funnel-hack-offer-architecture.md` — competitor offer-mechanics extraction
- `knowledge/playbooks/conversion-rate-optimization.md` + `knowledge/checklists/cro-audit-checklist.md` — page-level conversion work
- `knowledge/playbooks/campaign-orchestration.md` — multi-channel launch execution once assets exist
- `knowledge/frameworks/content-copywriting/four-us-framework.md` — scoring rubric behind the gates
- `harness/brief-schema.md` — brief structure for every content asset in stage 4
