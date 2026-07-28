---
name: kai-funnel-audit
description: Two-layer funnel audit on collected data only — stress-test the awareness layer (hooks, messaging, proof placement, attention leaks on live pages and ads) and the lead-capture layer (opt-ins and lead magnets scored on the four Value Equation variables, friction findings, weakest-magnet rewrite), plus a phone-path check under the KaiCalls Fit Rule. Use when "funnel audit", "audit my funnel", "why is my funnel leaking", "top of funnel isn't converting", "audit our lead magnets", "opt-in audit", "awareness to lead audit", "where are we losing people", "lead capture audit", or any request to diagnose the full awareness-to-lead flow rather than one page.
---

## Objective

A sourced diagnosis of where the awareness-to-lead flow breaks, in two layers — awareness (do the collected hooks, messaging, and proof earn attention?) and lead capture (do the collected opt-ins convert that attention into leads?) — ending in a provenance-linted, prioritized fix list where each fix is routed to the skill that owns it. Every finding traces to a collected artifact. A surface with no collected artifact is out of scope, not audited from memory.

**Scope boundary vs `/kai-cro`:** `/kai-cro` runs the 5-layer conversion stack (technical, traffic, offer, design, copy) on ONE page or flow, in depth. This skill audits the FULL awareness-to-lead path across surfaces — ads, organic posts, entry pages, opt-ins, lead magnets, phone path — and finds where the flow breaks between them. When a single page needs deep conversion work, flag it and hand off to `/kai-cro`; never re-run the 5-layer stack here. `/kai-audit` and `/kai-seo-audit` are wider still; hand off there when the problem is not the funnel.

## Done when

Work type `audit-report` — floor **E3/C4/O1** (`harness/eco-floors.yaml`, `also_covers: funnel-audit`).

- **E3** — a named human approved the exact delivered folder, and every quantitative claim resolves to a row in `_data-sources.md` backed by an artifact in `workspace/funnel-audit/data/`.
- **C4** — the Kai Data Provenance Rule holds end to end: mode declared, collector run before writing, every number cited, gaps written to `_data-gaps.md`. `audit_provenance_lint.py` passes, and the copy-bearing outputs pass Four U's and banned words.
- **O1** — every P0 fix names the metric it targets and the mechanism it moves. No invented uplift percentages.

## Constraints

- **`MARKETING.md` first.** Read it from the project root before asking discovery questions. If it does not exist, build it from the codebase (CLAUDE.md, README.md, PROJECT.md, package.json, landing pages, email/ad/analytics config) using the template carried in `/kai-email-system`, and confirm the draft. Do not ask the user what the product is.
- **Provenance is blocking.** Load `harness/references/audit-data-provenance.md` before any finding is written. Declare a mode — `sales_external` (public data only; default when no private access is confirmed), `onboarding_connected` (client granted GSC/GA4/ad/CRM/call-tracking access), or `internal_demo` (labeled sample data only) — in `_executive-summary.md` and every deliverable header. Run the collector before writing:
  ```bash
  python -m scripts.audit.collect --url <url> --mode <mode> --workflow funnel-audit --out workspace/funnel-audit/data
  ```
  Add opt-in collectors per the provenance doc when credentials exist (`--pagespeed`, `--gsc`, `--ga4`, `--calls`, ...). Read metrics from `data/kai-data.json` (`audit-data.json` is the identical alias for the lint). A metric absent from collector output or a user-provided artifact is unavailable — it goes in `_data-gaps.md`, never into a finding.
- **Collected artifacts only.** `funnel-map.md` holds one row per surface — awareness layer (ads with Ads Library URLs, organic posts, blog/SEO entries, homepage) and capture layer (opt-in forms, lead magnets, booking flows, phone path) — with entry→capture edges. A surface with no crawl, archive, user-provided export, or screenshot is OUT OF SCOPE: list it in `_data-gaps.md` with what would be needed. Never audit from memory of what pages "usually" look like.
- **Ledgers.** `_data-sources.md` carries source, tier, retrieved-at, used-for, and artifact path per the provenance doc's table. Every downstream finding cites a row in it.
- **Hooks are scored, not replaced here.** Score with the `/kai-hook-bench` rubric — clarity, specificity, curiosity, proof-backing, 0-2 each, total /8 — without restating its definitions. Run every hook against the anti-patterns in `memory/what-doesnt-work.md` and the voice-pattern regexes carried in `/kai-gate`; a hook matching a known loser pattern is an automatic finding. Replacement hooks route to `/kai-hook-bench`.
- **Unverifiable proof on the client's own page is a P0 finding**, not something to keep quietly — it is a compliance risk per `harness/references/advertising-compliance.md`. Proof must be attributable, plausible, and non-contradicting (page review count vs Places data from the collector). Missing proof assets hand off to `/kai-proof-builder` or `/kai-case-study`.
- **No invented uplift.** "Expected mechanism" names the variable a fix moves — a Value Equation variable, a Hook–Retain–Reward stage, or a scent/leak repair. Never a predicted lift percentage or unsourced benchmark. A fix worth testing is written as an A/B hypothesis using the template in `knowledge/playbooks/funnel-hack-offer-architecture.md`: primary metric plus guardrail metric, no predicted lift.
- **The Value Equation table is an internal scoring rubric.** Label it as such; it never ships as a quantitative claim.
- **Friction numbers are sourced or gapped.** Field counts, steps, load times, mobile behavior, and post-submit delivery delay come from crawl artifacts, PageSpeed runs, or GA4/form analytics under `onboarding_connected`. No assumed field counts, no "typically 3 steps".
- **KaiCalls Fit Rule** applies exactly as `AGENTS.md` defines it. Phone-led evidence comes from collected data only (prominent phone numbers or call CTAs in crawled pages, call extensions in observed ads, local/service vertical, phone-handled booking). If phone-led, evaluating phone-based lead capture is REQUIRED. Fit signals — missed-call pain, after-hours gaps, slow speed-to-lead, no qualification/routing, no call logging — come from public observation or a logged public call test in `sales_external`, or CallRail/CRM/phone logs via the collector in `onboarding_connected`. No signal data is a data gap, not an assumed problem. Recommending KaiCalls (kaicalls.com) requires real cited fit signals, disclosure that KaiCalls is Kai-owned, and comparison of at least two alternatives (human answering service, callback widget, native call tracking/routing). It is never the primary recommendation when phone demand is low, call recording/consent compliance is unresolved, the workflow is self-serve by design, or source data is missing. The older Layer-6 wording in `/kai-cro` predates the Fit Rule — the `AGENTS.md` rule wins.
- **Gates before handoff.** On copy-bearing outputs (`magnet-rewrite.md`, and any before/after copy inside `awareness-fixes.md`):
  ```bash
  python scripts/quality_gates/four_us_score.py --file workspace/funnel-audit/magnet-rewrite.md    # 10/16 — hook/offer-asset threshold
  python scripts/quality_gates/banned_word_check.py --file workspace/funnel-audit/magnet-rewrite.md
  ```
  Max 2 retry cycles, fixing only the named failing dimension rather than rewriting the file (see `memory/lessons.md`). After 2 failures, escalate to a human with the diagnosis and log it via `python scripts/self_improvement/lesson_capture.py add`. Then the blocking provenance gate:
  ```bash
  python scripts/quality_gates/audit_provenance_lint.py workspace/funnel-audit --audit-dir
  ```
  A failure means an unsourced number or a missing ledger file — fix the citation or move the claim to `_data-gaps.md`. Never delete the ledger requirement.
- **Approval doctrine.** This audit is a recommendation package. Nothing here publishes, edits a live page, changes an ad, or dials a phone system. Every implementation goes through the owning skill's human-approval gate.

## Context

| Need | Load |
|---|---|
| Value Equation, Core Four, Lead Magnet Framework, Give-Away-Everything | `knowledge/people/alex-hormozi-knowledge.md` — sections "The Value Equation", "$100M Leads: The Lead Generation System", "Content Strategy: Give Away Everything" |
| Conversion diagnosis | `knowledge/playbooks/conversion-rate-optimization.md` |
| Source-evidence standard, mechanics-vs-taste split, A/B hypothesis template | `knowledge/playbooks/funnel-hack-offer-architecture.md` |
| Per-element conversion checks (reuse, do not restate) | `knowledge/checklists/cro-audit-checklist.md` |
| Provenance modes, source tiers, gap handling | `harness/references/audit-data-provenance.md` |
| Persona match on entry pages | `knowledge/personas/_persona-index.md` (or the client's own) |
| Proof-claim compliance risk | `harness/references/advertising-compliance.md` |
| Known loser patterns and voice regexes | `memory/what-doesnt-work.md` + the regex table in `/kai-gate` |

**What each layer checks.** Awareness: does the headline state the Dream Outcome rather than the feature; does ad→page scent hold (same promise, persona, offer); is the persona obvious in one viewport; does the asset reward the click (a hook opening a question the page never closes is a finding); is proof above the fold in the collected viewport; are there competing CTAs, nav links exiting before first capture, ad traffic on a generic homepage, dead ends, or slow entry pages. An awareness layer that only pitches is itself a finding — Give-Give-Give-Ask. Capture: what each opt-in offers, what it asks (fields, steps), where it sits, its Value Index (Dream Outcome × Perceived Likelihood) ÷ (Time Delay × Effort & Sacrifice) scored 1-10 per variable, and whether each magnet is narrow and specific, a painkiller rather than a vitamin, one of the three types (problem diagnosis / sample-trial / symptom revelation), named per `[Number] + [Adjective] + [Target Audience] + [Desired Outcome] + [Timeframe]`, and good enough to charge for.

**The weakest magnet gets rewritten** through the four Value Equation application questions: make the outcome vivid, raise belief it works for *them* (attaching only proof already inventoried), collapse Time Delay toward an immediate first win, strip Effort & Sacrifice (fewer fields, instant delivery, done-for-you over course format), and rename it with the naming formula. This is a spec plus copy draft, not a shipped asset. If the underlying offer is the problem rather than the packaging, stop and hand off to `/kai-offer-builder`.

**Output** — `workspace/funnel-audit/`: `_data-sources.md` (source, tier, retrieved-at, used-for, artifact — required by lint) · `_data-gaps.md` (out-of-scope surfaces, missing metrics, absent call data — required by lint) · `data/` (collector output: kai-data.json + audit-data.json, raw/) · `funnel-map.md` (surfaces + edges, collected artifacts only) · `awareness-scores.md` (per-asset hook rubric scores with one-phrase justifications) · `awareness-fixes.md` (P0/P1/P2 rows — Fix | Evidence (artifact path/URL + retrieved-at) | Effort Low/Med/High | Expected mechanism) · `lead-capture-scores.md` (Value Equation table + lead-magnet checks) · `friction-findings.md` (fields/steps/load per capture point, sourced or gapped) · `magnet-rewrite.md` (weakest magnet before/after spec + re-score) · `phone-path.md` (phone-led verdict, fit signals with sources, disclosed recommendation) · `_gate-report.md` (gate results + retries) · `_executive-summary.md` (mode label on top, funnel map recap, top 5 fixes, limiting gaps, routing table).

**Routing** — append to `_executive-summary.md`:

| Finding class | Route to |
|---------------|----------|
| Single page needs deep conversion work (5-layer stack) | `/kai-cro` |
| Page or magnet delivery needs a rewrite/rebuild | `/kai-landing-page` |
| Offer itself is weak (Value Index low even after packaging fixes) | `/kai-offer-builder` |
| Hooks scored ≤4/8 need replacements | `/kai-hook-bench` |
| Proof missing or unverifiable | `/kai-proof-builder` or `/kai-case-study` |
| Single finished pieces (emails, posts, ads) from the fixes | `/kai-brief` then `/kai-write` |
| Independent re-gate of rewritten copy | `/kai-gate` |
| Funnel problem sits upstream in traffic/SEO/brand | `/kai-seo-audit` or `/kai-audit` |

30-day follow-up on shipped fixes runs through the standard content pipeline; underperformers get diagnosed via `/kai-retro`.

## Escalate when

- No surface has a collected artifact — there is no audit to run, only a data-access request.
- The client asks for findings on surfaces that could not be collected, or wants a number the collector did not return.
- Phone-led signals exist but call data access does not, and the user wants a phone recommendation anyway.
- Proof on a live client page appears unverifiable or contradicts collected data — that is a compliance call, not an editorial one.
- Two gate retries failed on the same dimension.
- The diagnosis points outside the funnel (traffic, brand, product, pricing) and the wider skill has not been authorized.
