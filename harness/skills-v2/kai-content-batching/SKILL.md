---
name: kai-content-batching
description: Turn a brand's positioning into a 30-day, multi-platform content batch — 3-7 pillars, subtopic matrix mapped to funnel stage and persona, pillar pieces plus derivative fan-out, proof elements in at least half the slots, all registered in the editorial calendar store and quality-gated. Use when "content batch", "batch my content", "30 days of content", "month of content", "content batching machine", "content pillars", "fill the content calendar", "plan a month of posts", or any request to produce a full month of multi-platform content in one run.
---

## Objective

Thirty days of multi-platform content that exists, is gated, and is scheduled — derived from 3–7 pillars the brand can actually own, with at least half the slots carrying real proof. Every slot registered `planned` in the editorial calendar store, every asset through the gates, nothing published without a human. The month follows the Give-Away-Everything model: give away the method, sell the implementation. Roughly 1% of an audience implements free content themselves; the other 99% are the buyers. The content is the proof of competence — trust, not information, is the bottleneck. Pillars that tease the method instead of teaching it fail this skill's purpose.

**Scope boundaries.** `/kai-content-calendar` plans blog/SEO calendars, `/kai-social` batches social-only, `/kai-write` writes one piece, `/kai-repurpose` fans one pillar into 15–25 derivatives. This skill orchestrates them. Hand off; never restate derivative formats, counts, or platform adaptations that `/kai-repurpose` owns.

## Done when

Work type `campaign` — floor **E5/C3/O4**, `composite: true` (`harness/eco-floors.yaml`).

- **E5** — every slot is registered in the calendar store and reads back via `--list --status planned`. Assets that publish need their own provider receipt and public read-back at publish time.
- **C3** — every asset cleared `four_us_score` (12/16 publishing; 10/16 ads, email, hooks), `banned_word_check`, and `seo_lint` on SEO/blog pieces, and a named non-producer read the batch end to end.
- **O4** — a campaign-level threshold declared before the first slot ships, read at 45 days.

Composite rule: the batch is CLOSED only when every child asset is CLOSED. One unshipped asset keeps the batch open. Each child carries its own work-type floor — `blog-post` E5/C3/O3, `social-post` E5/C2/O3, `email-lifecycle` E5/C3/O3.

## Constraints

- **Pillars: 3–7**, derived from Hormozi's five working categories, keeping only what the brand can own: **own frameworks** (the brand's IP, step by step), **common mistakes** (what the ICP gets wrong — contrast positioning), **counterintuitive takes** (challenge consensus — attention), **behind-the-scenes** (real work, real results — requires proof inventory), **Q&A / implementation replays** (giving away implementation in real time).
- Every candidate pillar passes the **Value Equation** — Value = (Dream Outcome × Perceived Likelihood of Achievement) ÷ (Time Delay × Effort & Sacrifice). A pillar earns its slot only if its content raises the ICP's perceived likelihood of the dream outcome or cuts their time and effort. Pillars that only describe the product fail. Cut them.
- **Banned angles are excluded.** Any pillar or hook style logged in `memory/what-doesnt-work.md` is out — binary-contrast "It's not X, it's Y" hooks, study percentages reframed as promises. Record each exclusion with the line that banned it.
- Pillars extend measured winners where `knowledge/playbooks/what-works.md` has evidence; unproven pillars are labeled "unproven — new bet", not presented as proven.

**Subtopics (8–10 per pillar).** Each tagged with funnel stage (TOFU problem-aware / MOFU solution-aware / BOFU product-aware), persona (one of the 8, or null for pure SEO informational), primary format, channel(s), and a proof-slot flag. **Verify the channel guide exists in `knowledge/channels/` before assigning a channel.** Default stage mix roughly 60/25/15 TOFU/MOFU/BOFU — a planning default, not a measured benchmark; shift it when `what-works.md` says otherwise. TOFU and MOFU give the full method; BOFU sells implementation.

**Offer-adjacent BOFU pieces** load `knowledge/playbooks/funnel-hack-offer-architecture.md`: offer mechanics come from sourced funnel evidence, and any Grand Slam Offer framing must describe the brand's real, documented offer. **Keyword and SERP grounding** is handed to `/kai-topical-map` or `/kai-content-calendar` — never guess search volumes.

**Production.** Select 4–5 pillar pieces for the 30 days (about one per week, one per pillar), choosing the subtopic with the strongest winner evidence first. Brief each via `/kai-brief` (`harness/brief-schema.md`). Write pillars repurposing-ready: self-contained H2 sections, standalone data points, quotable frameworks. Complete one pillar's cluster before scattering across all of them (`knowledge/playbooks/content-publication-velocity.md`). 4–5 pillars × 15–25 derivatives covers 30+ daily slots.

**Proof — at least half of all calendar slots carry a proof element** (result, named example, screenshot, review, case study, before/after), and only from a real inventory:

- `workspace/proof-library/` if a prior `/kai-proof-builder` run exists (use only entries with sources), `data/content_log.json` 30-day winners (runtime log — absent on a fresh clone), `knowledge/playbooks/what-works.md`, existing case studies in `workspace/`, or live public data collected via `python -m scripts.audit.collect --url <url> --mode <mode> --workflow content-batching --out workspace/content-batch/data/` after loading `harness/references/audit-data-provenance.md`.
- Each inventory row: proof claim, source (file path, collector artifact, or approved customer quote with permission status), and which slots use it.
- **No fabricated testimonials, review counts, revenue numbers, or "top pains from Reddit"** without a real listening run (`/kai-reddit-listen`). Missing proof goes in `workspace/content-batch/_data-gaps.md`. If the inventory cannot cover half the slots, fill the shortfall with framework and mistake content and log the gap — a thin proof month is a finding, not something to hide.

**Gating.** No asset enters the calendar ungated. Max 2 retry cycles per asset; fix only the named failing dimension, never rewrite the whole draft (`memory/lessons.md`). After 2 failures, mark the slot `skipped` in the calendar store with the diagnosis in `--notes`, escalate to a human, and log the repeated diagnosis to `memory/lessons.md`.

`python scripts/quality_gates/four_us_score.py --file <file>` (12/16 publishing; 10/16 ads, email, hooks) · `python scripts/quality_gates/banned_word_check.py --file <file>` (Tier 1 = instant reject) · `python scripts/quality_gates/seo_lint.py --file <file> --keyword "<target keyword>"` (SEO/blog only).

**Approval doctrine.** Registering `planned` items schedules draft generation only. Nothing publishes or posts to a live channel without explicit human approval; the store never sets `published` without a human-in-the-loop publish.

## Context

| Need | Load |
|---|---|
| Positioning, ICP, value prop, channels | `MARKETING.md` (project root) |
| Measured winners to extend · banned angles | `knowledge/playbooks/what-works.md` · `memory/what-doesnt-work.md` |
| Give-Away-Everything, Value Equation | `knowledge/people/alex-hormozi-knowledge.md` ("Content Strategy: Give Away Everything") |
| Persona selection tables | `knowledge/personas/_persona-index.md` |
| Fan-out math · finish-the-segment discipline | `knowledge/playbooks/content-repurposing.md` · `knowledge/playbooks/content-publication-velocity.md` |
| Offer mechanics for BOFU | `knowledge/playbooks/funnel-hack-offer-architecture.md` |
| Provenance for any live number | `harness/references/audit-data-provenance.md` |
| Brief schema · calendar store | `harness/brief-schema.md` · `scripts/campaigns/calendar.py` |

**Registering slots** (verified against `scripts/campaigns/calendar.py` — `--add` requires `--site`, `--title`, and `--publish-at` in ISO 8601, UTC assumed if naive):

```bash
python scripts/campaigns/calendar.py --add --site <brand> --title "<slot title>" \
  --publish-at 2026-08-04T14:00Z --format <blog|linkedin-article|email|social|...> \
  --keyword "<target keyword or empty>" --persona <persona-or-omit> \
  --notes "pillar=<pillar-slug>; proof=<inventory-row-or-none>"
python scripts/campaigns/calendar.py --list --status planned --site <brand>
```

Items land as `planned`; the agent loop's hourly `editorial_calendar_tick` turns due items into drafts that flow through the normal gate and approval pipeline. Add `--campaign-id` when the batch belongs to a tracked campaign (`scripts/campaigns/campaign_tracker.py`). **Sequencing:** lead each week with the pillar piece on its highest-reach channel, then roll that pillar's derivatives across the rest of the week — playbook cadence is pillar Monday, clips/email/visuals/community posts Tuesday through Friday.

**Output** goes to `workspace/content-batch/`. `_calendar-30day.md` carries title, pillar, format, channel, persona, funnel stage, proof element (or "—"), and asset path per slot; `_gate-report.md` states the proof-coverage ratio (proof slots ÷ total slots), which must be ≥ 0.5 or explained in `_data-gaps.md`.

```
workspace/content-batch/
├── _pillars.md               # 3-7 pillars, Value Equation test, banned-angle exclusions
├── _subtopic-matrix.md       # 8-10 subtopics per pillar × stage × persona × channel
├── _proof-inventory.md       # sourced proof elements (or pointer to workspace/proof-library/)
├── _data-gaps.md             # missing proof/data — logged, never guessed
├── _calendar-30day.md        # date × slot table + calendar store item ids
├── _gate-report.md           # per-asset scores, retries, escalations, proof-coverage ratio
├── data/                     # scripts.audit.collect artifacts (if live data pulled)
├── pillars/                  # /kai-write output, one file per pillar piece
└── derivatives/              # /kai-repurpose output trees, one folder per pillar
```

## Escalate when

- The brand cannot own 3 pillars, let alone 7 — the positioning problem is upstream of the content batch.
- The proof inventory cannot cover half the slots and the shortfall would require inventing results.
- An asset fails its gate twice for the same reason, or a requested pillar is on the `what-doesnt-work.md` banned list and the user wants it anyway.
- The batch would need keyword volumes nobody has researched, or a customer quote lacks permission status.
