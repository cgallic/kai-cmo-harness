---
name: kai-proof-builder
description: Build and maintain a provenance-clean proof library — inventory every real proof asset (analytics, reviews, permitted testimonials, case studies, press, certifications), categorize it, rewrite each cleared item in 3 lengths, fuse top assets with narrative, and gate everything through FTC testimonial rules before it can ship. Use when "proof library", "gather our proof", "authority builder", "collect testimonials", "social proof assets", "proof points for the sales page", "what results can we claim", or any request to assemble evidence for marketing claims. NEVER invents proof — missing proof is reported as a gap.
---

## Objective

A proof library at `workspace/proof-library/` where every asset carries a source, a permission status, and a readiness verdict — and where gaps are documented as findings rather than filled with plausible copy. Cleared assets are rewritten at three lengths and can be pulled by downstream skills by provenance ID; nothing else may be used at all.

**Proof is collected, never composed. If it cannot be traced to a real source, it does not exist.** Missing proof is itself a finding: "no usable transformation proof exists — run `/kai-case-study` with the two clients named in the CRM export" is a correct output of this skill.

## Done when

Work type `audit-report` — floor **E3/C4/O1** (`harness/eco-floors.yaml`): client-facing analysis whose every quantitative claim must resolve to a collector source.

- **E3** — a named human approved the exact `_provenance.md` ledger and the rendered assets. This skill builds a library; it never publishes.
- **C4** — the Kai Data Provenance Rule in full (collector ran before any number was written, mode declared, every quantitative claim citing a collector source, every gap in `_data-gaps.md` rather than in a guess), plus the FTC gate below, `banned_word_check` clean, and Four U's at **12/16** for full stories and fusion pieces, **10/16** for stat lines and blurbs.
- **O1** — the summary names the single highest-value next action with an owner and a date (e.g. "get written permission from the P-002 customer — strongest transformation asset in the library").

Max 2 retry cycles, fixing only the named failure. After 2 failures, escalate with specifics and log the diagnosis per `memory/lessons.md` doctrine.

## Constraints

- **Read `MARKETING.md` from the project root first.** If absent, build it from the codebase — CLAUDE.md, README.md, PROJECT.md, package.json, landing pages, email/ad/analytics config — using the template from `/kai-email-system`, and confirm the draft. Do not ask the user what the product is.
- **Run the collector before writing anything public or quantitative** (review counts, rankings, traffic, visible press):

  ```bash
  python -m scripts.audit.collect --url https://<domain> --mode <sales_external|onboarding_connected> --workflow proof-builder --out workspace/proof-library/_data
  ```

  Declare the mode first — `sales_external` by default, `onboarding_connected` only with confirmed access, `internal_demo` labeled as sample data everywhere it appears. Read `kai-data.json` from the output folder.
- **Every item gets a provenance row** in `workspace/proof-library/_provenance.md`: ID, one-line asset, source class, source location (file / URL / system plus date), source tier, permission status, verification method, readiness.
- **A quote without a locatable source** — file, URL, transcript timestamp, email date — is not inventory; it is a gap. **A number the user remembers is Tier 4** until they produce the export; record it as a gap naming who can supply it.
- **Never fill a thin category with plausible-sounding entries.** Every hole goes in `workspace/proof-library/_data-gaps.md` with what is missing, why it matters, and who or what can supply it.
- **Numbers are frozen.** Not rounded up, not "nearly," not annualized, not extrapolated. The number in a rendering equals the number in its source.
- **Direct quotes stay verbatim and attributed.** Ellipses may shorten a quote only when meaning is unchanged; two quotes are never spliced. Attribution matches the permission status — named, first-name, or anonymized. Named testimonial use requires written permission on file.
- **No superlatives** ("best," "#1," "fastest") unless a Tier 1–2 source substantiates that exact comparative claim. Every rendering carries its provenance ID in an HTML comment: `<!-- proof: P-001 -->`.
- **Anything not `cleared` never ships.** `/kai-landing-page`, `/kai-social`, `/kai-write`, and `/kai-brief` may pull only `cleared` assets, by provenance ID.
- **Approval doctrine.** Any use of a cleared asset on a live channel goes through `/kai-gate` and human approval first. Permission requests to customers are drafted for a human to send — never sent autonomously.
- **Guarantees and risk reversal are offer mechanics, not proof assets** — hand off to `/kai-offer-builder`.

## Context

| Need | Load |
|---|---|
| Data modes, source tiers, hard rules | `harness/references/audit-data-provenance.md` |
| Value Equation and proof mechanics (categorization depends on it) | `knowledge/people/alex-hormozi-knowledge.md` |
| Unsourced-claim history | `memory/lessons.md` |
| FTC endorsement, substantiation, fake-review rules | `harness/references/advertising-compliance.md` §1, §2, §10 |
| Per-channel material-connection disclosure formats | `harness/references/creator-disclosure.md` |
| Product, ICP, voice, current channels | `MARKETING.md` (project root) |
| Building a transformation asset that does not exist yet | `/kai-case-study` |

**Where real proof comes from** — check connected tools and the repo before asking the user:

| Source class | Where to look | Tier |
|---|---|---|
| Analytics exports | GA4/GSC exports, dashboards, `data/` files the client provides | 1 (connected) or 3 (user-provided) |
| Review platforms | Google, G2, Trustpilot, app stores — via collector or screenshot | 1–2 |
| Testimonials | Emails, DMs, survey responses, call transcripts — written permission required for named use | 3 |
| Case studies | `/kai-case-study` output in `workspace/` | 3 |
| Press mentions | Live URLs, archived captures | 2 |
| Certifications / credentials | Certificates, license numbers, partner-program listings | 2–3 |
| Usage stats | Client's own billing, CRM, product database queries | 1 or 3 |

**Categories.** Proof's job in the Value Equation is raising Perceived Likelihood of Achievement — the prospect's belief that *they specifically* get the result, not just that it works. Third-party validation beats first-person claims.

| Category | What it is | Value Equation lever |
|---|---|---|
| Quantitative | Measured numbers: metrics, review counts, usage stats | Perceived Likelihood — specific numbers beat adjectives |
| Qualitative | Testimonials and reviews in the customer's own words | Perceived Likelihood via similarity |
| Transformation | Before → after arcs: case studies, documented journeys | Dream Outcome made concrete, framed as status elevation — how others perceive the achievement |
| Authority | Credentials, certifications, press, expert standing | Perceived Likelihood via source credibility |

Two Hormozi mechanics apply while sorting. **Proof over claims:** demonstrated work is itself proof of competence, so published frameworks, teardowns, and free tools belong in Authority when they exist — do not claim expertise the library can demonstrate. **The testimonial flywheel:** premium clients produce better results, which produce testimonials that justify the premium. Transformation is the highest-value category; when it is empty, say so in `_data-gaps.md` and route to `/kai-case-study`.

**Three renderings** per cleared asset, all in one file at `workspace/proof-library/<category>/<id>-<slug>.md`: a stat line (≤ 20 words, for ads, headers, proof bars), a short blurb (40–80 words, for landing sections, email, decks), and a full story (200–400 words, for case-study callouts and long-form). Single-piece polish is `/kai-write`'s job; channel distribution is `/kai-repurpose`'s.

**Fusion** pairs the 3–5 strongest cleared assets (prefer Transformation and Quantitative with named permission) with narrative: before state in the customer's words → turning point → measured after state. Every sentence is marked `[S]` sourced (traceable to the provenance row, transcript, or export) or `[C]` connective tissue (transitions and framing the writer added). `[C]` may set scene and connect facts; it may never add events, feelings the customer never expressed, dialogue, or implied metrics. If the story only works because of an invented detail, it is not ready — log the missing input, usually a follow-up question for the customer. Write to `workspace/proof-library/fusion/<id>-story.md` with a marked-up review copy above a clean copy.

**FTC compliance gate**, applied to every asset:

1. **Genuine and current** — a testimonial must reflect the endorser's genuine, current experience. Stale results (product changed, customer churned) get flagged for re-verification.
2. **Typical results** — an atypical featured result must disclose what typical consumers achieve. "Results not typical" alone is not sufficient; state the typical outcome from Tier 1–3 data. With no typical-results data, the atypical claim is blocked, not disclaimed around.
3. **Material connection** — payment, free product, affiliate, employment, or family relationship must be disclosed clearly and before or alongside the endorsement, never buried (16 CFR Part 255).
4. **No unsubstantiated superlatives** — anecdotal or testimonial evidence is never sufficient substantiation for an objective product claim.
5. **Fake Reviews Rule** — no purchased, undisclosed-incentivized, insider, or AI-fabricated reviews anywhere in the library. If provenance cannot rule this out for a review source, the asset is blocked.
6. **Expert framing** — anyone presented as an expert must hold the relevant qualifications, verified in the provenance row.

Then, per rendered file:

```bash
python scripts/quality_gates/four_us_score.py --file <file>    # 12/16 full stories & fusion pieces; 10/16 stat lines & blurbs
python scripts/quality_gates/banned_word_check.py --file <file> # zero violations
```

**Readiness verdicts** in `_provenance.md`: `cleared` (source verified, permission on file, compliance passed — usable by other skills); `needs-permission` (real asset, but written permission, typical-results data, or disclosure language is outstanding — list exactly what is needed and from whom); `blocked` (unverifiable source, failed compliance, permission refused, or fabrication risk — do not use; state why).

**Output** — `workspace/proof-library/` holds `_provenance.md` (the ledger), `_data-gaps.md`, `_data/` (collector output), the four category folders, `fusion/`, and `_quality-report.md` (gate scores, compliance results, retry log). Close with counts per verdict, top gaps, and the highest-value next action. Re-sweep quarterly or after any product or pricing change, and recheck `cleared` testimonials for currency. New wins land here first, then feed `/kai-case-study` and `knowledge/playbooks/what-works.md`.

## Escalate when

- A number matters to the pitch and no export, dashboard, or system query can produce it.
- Permission for a named testimonial is ambiguous, verbal, or secondhand.
- A featured result looks atypical and no typical-results data exists, or a review source cannot be ruled clean of incentives or fabrication.
- Someone is presented as an expert and their qualifications cannot be verified, or the library has no Transformation assets at all — that is a business finding, not a writing problem.
- A downstream skill asks for an asset that is not `cleared`.
