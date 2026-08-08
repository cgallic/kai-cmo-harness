# The Diagnosis-First Operating Order (Diagnosis → Strategy → Tactics)

> **Use when:** Starting any marketing engagement, plan, campaign, or content batch; deciding whether Kai has enough evidence to produce assets; reviewing a plan that jumps straight to channels; or diagnosing why a marketing program keeps shipping work that doesn't move numbers. This doc owns one thing: **the order of operations** — what must exist before what. It is the front door to `knowledge/_arbitration.md`, which resolves conflicts *between* frameworks once the operating order has told you which phase you are in.

**Provenance:** The three-phase operating order is Mark Ritson's codification of classic marketing management (diagnosis → strategy → tactics, Marketing Week columns and the Mini MBA curriculum), structurally identical to Richard Rumelt's strategy kernel (*Good Strategy Bad Strategy*, 2011: diagnosis → guiding policy → coherent action). The evidence that diagnosis pays is the market-orientation literature: Narver & Slater (1990, 140 business units) found a positive effect of market orientation on profitability; Kohli & Jaworski (1990) formalized the construct as intelligence generation → dissemination → responsiveness; Kirca, Jayachandran & Bearden's 2005 *Journal of Marketing* meta-analysis confirmed a positive market orientation → performance relationship across the pooled studies, mediated by innovativeness, customer loyalty, and quality. SMART objectives trace to Doran (1981). Waste numbers come from the BetterBriefs/IPA study (2021). Cite these as research findings; verify anything category-specific against your own data before client claims (`harness/references/audit-data-provenance.md`).

**Adjacent docs (cross-link, don't duplicate):**
- *Which framework wins when two disagree* → `knowledge/_arbitration.md` (this doc routes you into a phase; arbitration referees inside it)
- *Who to reach and how wide* (strategy phase) → `knowledge/frameworks/marketing-science/brand-growth-laws.md`
- *Budget ratio brand vs activation* (strategy phase) → `knowledge/frameworks/marketing-science/brand-activation-budget.md`
- *Positioning stack and messaging* (strategy phase) → `knowledge/playbooks/brand-positioning.md`
- *Macro/category context for 2026 diagnosis* → `knowledge/playbooks/2026-marketing-playbook.md`
- *The tactical entry ticket per piece of content* → `harness/brief-schema.md` (a brief is a Phase-3 artifact; it cannot substitute for Phases 1-2)

---

## Quick Reference — The Operating Order

```
PHASE 1: DIAGNOSIS   →   PHASE 2: STRATEGY   →   PHASE 3: TACTICS
"What is going on?"      "Where do we play,      "What do we ship,
                          how do we win?"          on which channels?"
market orientation        targeting                channel selection
category/competitor map   positioning              creative + briefs
funnel evidence           objectives (SMART,       calendar, budget lines
customer research         sequenced)               execution + gates
```

Three rules that make it an operating order rather than a diagram:

1. **Sequence is mandatory.** No strategy decision before diagnosis exits its checklist. No tactic (channel, format, campaign, post) before targeting, positioning, and objectives are written down. Ritson: there is no "digital strategy" or "Facebook strategy" — there is one strategy, which then feeds tactical choices.
2. **Each phase produces a named artifact.** Diagnosis → `MARKETING.md` + evidence folder. Strategy → the targeting/positioning/objectives block inside `MARKETING.md`. Tactics → briefs (`harness/brief-schema.md`), calendars, campaigns. An artifact missing = the phase didn't happen, whatever the meeting notes say.
3. **Kai enforcement:** no PRODUCE skill runs before diagnosis inputs exist. Full rule below ("The Kai Gate Rule").

Why the order pays: Rumelt names failure to face the challenge (absent or weak diagnosis) and mistaking goals for strategy among his four hallmarks of bad strategy. The BetterBriefs/IPA study (1,700+ marketers and agency staff, 70+ countries, 2021) found respondents estimate **a third of marketing budget is wasted** through poor briefs and misdirected work — and the gap is diagnostic blindness: 78% of marketers believe their briefs give clear strategic direction; 5% of creative agencies agree.

---

## Phase 1: Diagnosis — Executable Checklist

Purpose: comprehend the situation before deciding anything. Every item lists its minimum evidence bar and where the output lands. Run items in parallel; exit only when all four blocks pass. Time-box the phase (1-2 weeks solo operator, 4-6 weeks agency engagement) — diagnosis that never ends is a failure mode too.

### D1. Market orientation research (the intelligence base)

Market orientation has three behavioral components (Kohli & Jaworski 1990): generate intelligence about customers and competitors, spread it, respond to it. (Narver & Slater 1990 frame the same construct as customer orientation, competitor orientation, and interfunctional coordination.) Block D1 is the generation step.

- [ ] **Customer intelligence:** ≥10 customer/prospect conversations OR a structured survey OR mined primary text (sales-call transcripts, support tickets, reviews, Reddit/community threads). Label every input with `source_type` and date per `harness/brief-schema.md` evidence fields.
- [ ] **Competitor intelligence:** run `/kai-competitors` or `python scripts/intel/competitor_monitor.py --check`; capture who the buyer names as alternatives (ask them — the real consideration set often differs from the founder's list).
- [ ] **Internal intelligence:** what sales/support/founders know that marketing doesn't — churn reasons, objection log, win/loss notes.
- **Blocks exit if:** zero primary customer inputs. Third-party reports alone do not clear D1.

### D2. Category and competitor mapping

- [ ] **Category definition and size:** what category does the *buyer* think they're shopping? Approximate purchase frequency (drives the in-market % — see the 95-5 logic in `brand-growth-laws.md`).
- [ ] **Share and growth picture:** your penetration vs the leaders'; is the category growing, flat, shrinking? Sourced numbers only — collector output or a cited report, never memory.
- [ ] **Competitor teardown:** top 3-5 by the buyer's consideration set — their positioning claim, price point, distribution, observable spend. Framework: `knowledge/playbooks/competitive-intelligence.md`.
- [ ] **Macro context scan:** regulation, platform shifts, AI-search changes relevant to the category — load `knowledge/playbooks/2026-marketing-playbook.md`, don't rebuild it.
- **Blocks exit if:** category is defined only in company-internal language ("we're the AI-powered X for Y" is positioning, not a category map).

### D3. Current funnel evidence

- [ ] **Collector run:** `python -m scripts.audit.collect --url <url> --mode <mode> --workflow diagnosis --out <data-folder>` (Kai Data Provenance Rule — applies because diagnosis feeds client-facing claims).
- [ ] **Traffic and conversion baselines:** GSC queries/impressions, GA4 pages, conversion counts, by stage. Unknown numbers go in `_data-gaps.md`, not estimates.
- [ ] **Lead-capture reality check:** forms, phones, chat — response time, after-hours coverage, missed-call volume where phone-led (KaiCalls Fit Rule per `AGENTS.md` applies at the *recommendation* step later, but the evidence is collected now).
- [ ] **Existing content/asset audit:** what exists, what ranks, what converted. `/kai-funnel-audit` covers this in depth.
- **Blocks exit if:** no analytics access and no collector output — you cannot diagnose a funnel you haven't seen.

### D4. Customer research synthesis

- [ ] **Persona selection with evidence label:** pick from `knowledge/personas/` and tag `evidence_backed`, `directional`, or `hypothesis` per `harness/brief-schema.md`. A `hypothesis` persona cannot anchor strategy claims.
- [ ] **Category entry points:** elicit 15-30 candidate CEPs via the W-prompts (method owned by `brand-growth-laws.md`).
- [ ] **Jobs, pains, objections in customer language:** verbatim quotes filed with sources — these feed positioning and copy later.
- **Blocks exit if:** every persona is `hypothesis`-labeled and no plan exists to upgrade at least one.

### Diagnosis exit gate

All four blocks pass → write the diagnosis summary into `MARKETING.md` (created by `/kai-start` if absent): 5-10 sentences stating what is going on, the 1-3 critical obstacles (Rumelt: a good diagnosis simplifies overwhelming complexity by identifying certain aspects of the situation as critical), and the evidence folder path. If you cannot state the critical obstacle in one sentence, diagnosis isn't done.

---

## Phase 2: Strategy — Three Decisions, In Order

Strategy is choice, not aspiration. Exactly three decisions, made from the diagnosis, written into `MARKETING.md`.

### S1. Targeting — who (and how wide)

Decide which buyers the plan pursues and at what breadth. The breadth decision (broad category reach vs narrow ICP) is owned by the DR-vs-availability decision table in `brand-growth-laws.md` — apply it, don't re-derive it. Segmentation inputs come from D1/D4. Output: a named target with size estimate and the doctrine (DR or availability) each budget line runs under.

### S2. Positioning — what we stand for against whom

One positioning statement per target: frame of reference, point of difference, reasons to believe — built from D2 (competitor claims) and D4 (customer language). Full stack: `knowledge/playbooks/brand-positioning.md` and `/kai-brand`. Output: the statement plus the 2-3 proof points that survive the provenance rule.

### S3. Objectives — how much, by when, in what order

SMART per Doran (1981): Specific, Measurable, Assignable, Realistic, Time-related — Doran himself noted not every objective will hit all five; treat them as guidelines, not a ritual. Kai-specific additions:

1. **Few:** 1-3 objectives. More than three means choices weren't made.
2. **Sequenced:** order objectives by funnel dependency — awareness/mental availability targets before acquisition targets before revenue/retention targets, each with its own date. A revenue objective with no upstream objective is a wish.
3. **Derived, not decorative:** each objective must trace to a diagnosis finding ("missed 41% of after-hours calls → objective: answer rate ≥95% by Q4"). One of Rumelt's bad-strategy hallmarks is goals mistaken for strategy — an objective without a diagnosis behind it is exactly that.
4. **Registered:** `python scripts/harness_cli.py goals add --brand <brand> --name "<goal>" --kpi <kpi> --target <value> --deadline YYYY-MM-DD` so the weekly CMO review can pace it.

### Strategy exit gate

`MARKETING.md` contains: target(s) + doctrine, positioning statement(s), 1-3 SMART sequenced objectives with registered goals. Only now may anyone say the word "channel."

---

## Phase 3: Tactics — Now, and Only Now

Tactics = the full 4P surface, not promotion alone: product/offer changes (`/kai-offer-builder`), pricing (`knowledge/playbooks/pricing-strategy.md`), distribution/physical availability, and communication. For each objective:

1. Pick channels from the Framework Map in `AGENTS.md` — channel choice follows target media behavior and objective type, never familiarity.
2. Write a brief per asset via `harness/brief-schema.md` — the brief inherits persona, angle, and proof from Phases 1-2; it does not invent them.
3. Run the content pipeline and quality gates as normal (Four U's, banned words, seo_lint, ad policy gates).
4. Route budget lines through `brand-activation-budget.md` ratios.

Where two frameworks give conflicting tactical guidance (e.g., broad-reach doctrine vs a narrow-ICP playbook), resolve via `knowledge/_arbitration.md` — do not average them silently.

Approval doctrine: every live-channel action tactics produce — publishing, posting, ad mutations, outreach sends — requires human approval per `AGENTS.md`. Nothing in this operating order authorizes skipping that.

---

## Failure Mode Taxonomy

The classic ways the operating order gets violated. Each has a detection signal Kai can check mechanically.

| # | Failure mode | What it is | Detection signal | Correction |
|---|--------------|-----------|------------------|------------|
| 1 | **Tactification** (Ritson) | The discipline reduced to tactics: plans that are lists of channels and executions with no diagnosis or strategy layer above them | Plan document contains channel names but no target, positioning, or objective section; "strategy" slide is a channel logo grid | Stop. Run Phases 1-2. A channel list is an output of strategy, never a substitute |
| 2 | **Communification** (Ritson) | Within tactics, everything collapses to communications — product, pricing, and distribution levers ignored | 100% of proposed actions are content/ads/social; zero offer, price, or availability actions despite diagnosis showing (e.g.) unanswered phones or a broken checkout | Re-open Phase 3 across all 4Ps; cheapest fix is often not a campaign |
| 3 | **Marketing-as-promotion-only** | The org scopes marketing as "the department that makes ads," so diagnosis/strategy work is never commissioned at all | Requests arrive pre-tactified ("write us 10 posts", "run some ads") with no MARKETING.md and no evidence folder | Kai Gate Rule below: route to `/kai-start` + diagnosis before producing |
| 4 | **Goals-as-strategy** (Rumelt) | Ambitious targets presented as strategy ("grow 40%") with no diagnosis or guiding policy | Objectives exist but none traces to a diagnosis finding; no named obstacle | Rewrite objectives per S3 rule 3; if no diagnosis exists, back to Phase 1 |
| 5 | **Research-skipping** | Strategy built on founder intuition; personas all `hypothesis`; numbers from memory | `persona_evidence_status: hypothesis` across the board; quantitative claims without collector sources | D1/D4 minimum evidence bars; provenance lint blocks handoff |
| 6 | **Perpetual diagnosis** | Research as procrastination; the plan never exits Phase 1 | Diagnosis running past its time-box with exit-gate items already green | Exit gate is sufficient, not perfect; ship the strategy, revisit quarterly |

Modes 1-3 are nested: promotion-only scoping (3) produces communification (2), which is the loudest strain of tactification (1). Fixing 3 upstream usually clears all three.

---

## The Kai Gate Rule: No PRODUCE Before Diagnosis

**Rule:** No skill in the PRODUCE lane of the `/kai` router (`/kai-write`, `/kai-landing-page`, `/kai-email-system`, `/kai-ad-campaign`, `/kai-social`, `/kai-content-calendar`, `/kai-launch`, `/kai-cold-outreach`, and the rest of the PRODUCE table in `harness/skills/kai/SKILL.md`) may run until diagnosis inputs exist:

1. **`MARKETING.md` exists** at the project root (created by `/kai-start`), containing at minimum a diagnosis summary and one strategy block (target, positioning, objective), and
2. **Evidence exists:** a diagnosis evidence folder (collector output per the Data Provenance Rule) or a brief whose persona and quantitative claims carry non-`hypothesis` evidence labels.

**When the check fails:** do not produce. Say what is missing, then route: no `MARKETING.md` → `/kai-start`; `MARKETING.md` but no evidence → the Phase-1 checklist above (D1-D4); evidence but no strategy block → Phase 2. Producing anyway and labeling it "draft" is the tactification failure mode with a disclaimer stapled on.

**Narrow exception:** the human explicitly directs production without diagnosis, in their own words, after being told what is missing. Log the override and the missing inputs in the output header. AUDIT and ANALYZE lane skills are exempt — they *are* diagnosis tooling. PLAN lane skills (`/kai-brief`, `/kai-growth-plan`, `/kai-brand`) may run with partial diagnosis but must list gaps in their output.

This rule is the operating-order equivalent of the quality gates: gates check the asset after writing; this checks the *right to write* before starting.

---

## Worked Example (compressed)

Request arrives: "Write us a month of social posts" for a 6-attorney personal-injury firm. Gate check: no `MARKETING.md`, no evidence → decline to produce, run the order.

- **Diagnosis (1 week):** collector run + GSC + call-log pull. Findings: firm ranks #2 locally, but tracked lines show a large share of after-hours calls go unanswered; reviews praise one attorney by name; competitors all claim "aggressive" and "no fee unless we win"; buyer conversations show cases are compared on callback speed, not content quality. Critical obstacle (one sentence): *demand capture leaks after hours; content is not the constraint.*
- **Strategy:** target = injured locals in the 72-hour post-accident window (DR doctrine — in-market, urgent) plus category-buyer reach for mental availability; positioning = the firm that answers first, proof = tracked callback times; objectives = (1) answer rate ≥95% within 60 days, (2) +30% consult bookings within 120 days — sequenced, registered.
- **Tactics:** fix availability first (after-hours answering — phone-led fit signals present, so a KaiCalls evaluation with disclosure and alternatives per the Fit Rule), then LSA/GBP optimization, and only then the social calendar — now briefed against the answer-first positioning instead of generic "legal tips."

The original request (social posts) ended up third in priority. That reordering — not better posts — is what the operating order buys.

---

## How This Maps Into Kai

| Kai surface | Decision this doc informs |
|---|---|
| `/kai` router + every PRODUCE skill | The Gate Rule: verify MARKETING.md + evidence before producing; route to `/kai-start` or Phase 1 when missing |
| `/kai-start` (`harness/skills/kai-start/SKILL.md`) | MARKETING.md is the Phase-1/2 artifact this doc requires; onboarding = entering the operating order |
| `/kai-growth-plan`, `/kai-brand`, `/kai-budget` | Phase-2 executors: targeting/positioning/objectives structure, S3 objective rules |
| `/kai-audit`, `/kai-funnel-audit`, `/kai-cro`, `/kai-competitors`, `/kai-brand-pulse` | Phase-1 executors (exempt from the Gate Rule); their outputs populate D1-D4 |
| `/kai-brief` + `harness/brief-schema.md` | Phase-3 entry ticket; briefs inherit from Phases 1-2, never substitute for them |
| `knowledge/_arbitration.md` | Loaded when frameworks conflict inside a phase; this doc decides which phase you're in first |
| Plan/audit reviews (any lane) | Failure-mode taxonomy as a review checklist: flag tactification, communification, promotion-only scoping, goals-as-strategy |
| Weekly `cmo_review` + goals registry | S3 objectives registered via `harness_cli.py goals` so pace-vs-deadline tracking has real targets |

---

## Sources

- Ritson, M. — "Tactics without strategy is dumbing down our discipline" (tactification, communification), Marketing Week: https://www.marketingweek.com/mark-ritson-beware-the-tactification-of-marketing/
- Ritson, M. — "Marketers who skip brand research are doomed to fail," Marketing Week: https://www.marketingweek.com/mark-ritson-marketers-skip-brand-research-doomed-fail/
- Ritson, M. — "Planning for marketing planning: 14 steps," Marketing Week: https://www.marketingweek.com/mark-ritson-marketing-planning-14-steps/
- Mini MBA — "The missing step in marketing plans: brand diagnosis": https://minimba.com/articles/the-missing-step-in-marketing-plans-brand-diagnosis
- Rumelt, R. — *Good Strategy Bad Strategy* (2011), kernel summary: https://www.alexmurrell.co.uk/summaries/richard-rumelt-good-strategy-bad-strategy
- Narver, J.C. & Slater, S.F. (1990) — "The Effect of a Market Orientation on Business Profitability," *Journal of Marketing* 54(4): https://journals.sagepub.com/doi/abs/10.1177/002224299005400403
- Kohli, A.K. & Jaworski, B.J. (1990) — "Market Orientation: The Construct, Research Propositions, and Managerial Implications," *Journal of Marketing* 54(2): https://journals.sagepub.com/doi/10.1177/002224299005400201
- Kirca, A.H., Jayachandran, S. & Bearden, W.O. (2005) — "Market Orientation: A Meta-Analytic Review," *Journal of Marketing* 69(2): https://journals.sagepub.com/doi/10.1509/jmkg.69.2.24.60761
- Doran, G.T. (1981) — "There's a S.M.A.R.T. way to write management's goals and objectives," *Management Review* 70(11): https://www.scirp.org/reference/ReferencesPapers?ReferenceID=1459599
- BetterBriefs/IPA (2021) — "One third of marketing budgets could be wasted" (1,700+ respondents, 70+ countries): https://ipa.co.uk/news/betterbriefs
- BetterBriefs coverage with perception-gap figures (80%/10%, 78%/5%), Mi3: https://www.mi-3.com.au/18-10-2021/200bn-black-hole-marketers-wasting-third-budgets-giving-agencies-crap-briefs-and-dont
