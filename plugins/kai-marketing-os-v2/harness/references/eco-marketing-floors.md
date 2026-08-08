# ECO Applied to Marketing

> Doctrine: `docs/system/eco-completion-standard.md` · Machine-readable floors: `harness/eco-floors.yaml` · Verifier: `python -m scripts.quality_gates.eco_gate`
>
> Last updated: 2026-07-28

Marketing is the discipline where "done" lies most easily. A draft exists, so the post is "done." The campaign launched, so the launch is "done." The deck was delivered, so the audit is "done." None of those statements says whether anything happened, whether the work was any good, or whether it caused the result it promised.

ECO splits that single word into three claims a verifier can falsify.

| | Marketing translation |
|---|---|
| **E — Execution** | The thing is actually live at the real target, and the live version matches what was approved. |
| **C — Craft** | The work clears the quality gates, the platform policy, and the provenance rule — and a human other than the writer read it. |
| **O — Outcome** | The number it was supposed to move actually moved, measured at a window declared before ship. |

---

## The three failures ECO is designed to catch

**1. The draft that never shipped.** A blog post sits in `workspace/output/` with a passing Four U's score and gets logged as complete. E1 is not E5. Until the public URL returns 200 with the approved body, nothing happened. This is why `content_log.mark_published()` requires a publisher-returned URL and why **never log a URL that wasn't returned by a publisher** is a standing rule.

**2. The number nobody sourced.** An audit says "your competitor gets 40K monthly visits." Where did 40K come from? If it came from the model rather than a collector run, the deck is a fabrication with good typography. That is why `audit-report` carries a **C4** floor, not C2: the Kai Data Provenance Rule is a field standard, not a lint.

**3. The campaign graded by its own platform.** Meta says ROAS 4.2. Meta is not an independent verifier of Meta. Platform-reported conversions are E-grade evidence that the ad ran; they are not O5 attribution. That is why `paid-ad-campaign` sets `attribution_required: true` and points at the incrementality framework.

---

## Floors by work type

Full definitions in `harness/eco-floors.yaml`. Summary:

| Work type | Floor | What E actually requires | Outcome window |
|---|:---:|---|:---:|
| Blog post / SEO content | E5 / C3 / O3 | Live URL 200 + approved body | 30d (GSC) |
| Landing page | E5 / C3 / O4 | Page live, CTA submits, copy matches | 30d + min sample |
| Organic social post | E5 / C2 / O3 | Provider post id **and** permalink read-back | 7d |
| Lifecycle email | E5 / C3 / O3 | ESP send receipt reconciled to approved segment | 14d |
| Cold email | E5 / **C4** / O3 | Send receipt + suppression-list reconciliation | 14d |
| Paid ad campaign | E5 / **C4** / **O4** | Ad object ids + live-entity read-back field-for-field | 14d + attribution |
| Audit / report / deck | E3 / **C4** / O1 | Approved hash-pinned file, every number sourced | 60d |
| Strategy plan | E3 / C3 / O1 | Human approved the exact document | 30d |
| Campaign (composite) | E5 / C3 / O4 | Every child item CLOSED | 45d |
| Product UI / design system | E5 / **C4** / O3 | Live screen loaded by a non-actor at real breakpoints | 30d |
| Internal research | E2 / C2 / O0 | File exists and matches structure | none |
| Harness change | E3 / C3 / O1 | Tests + doctor + golden corpus pass | 30d |

Three floors deserve their reasoning stated:

- **Cold email is C4, not C3.** The residue is legal, not editorial. Sender identity, opt-out mechanics, and consent basis are field-standard obligations under CAN-SPAM/GDPR/CASL. A good reviewer who is not checking those is not clearing C4.
- **Product UI is C4, not C3.** The residue is accessibility and design-system integrity — WCAG AA contrast, focus order, token compliance, and every loading/empty/error state. A reviewer who likes how it looks but has not checked those has not cleared C4.
- **Audits are E3, not E5.** An audit has no external publishing target — the deliverable is the file. E tops out at approval of the exact bytes. All the weight moves to C4 provenance.

---

## What counts as evidence in marketing

The gate discards evidence whose verifier is the actor. In practice that means:

| Claim | Not evidence | Evidence |
|---|---|---|
| The post is live | "I published it" | `curl` of the permalink returning 200 with the approved marker |
| The email sent | The send script exited 0 | ESP message ids reconciled against the approved segment |
| The ad is running | The upload call succeeded | Read-back of the live ad entity matching the approved bundle |
| The copy is good | The writer likes it | Gate report + a named non-producer's end-to-end read |
| The number is real | It appears in the deck | A collector source id in the audit data folder |
| It worked | Platform dashboard screenshot | Metric read from the authoritative source at the predeclared window |
| It caused the lift | Correlation with launch date | Holdout, geo-split, or switchback design |

---

## The outcome debt

Almost no marketing work is CLOSED on ship day. SEO needs indexing time. Lifecycle emails need a cohort. Ads need to exit learning. Landing pages need sample size.

So the normal terminal state on ship day is **SHIPPED with an open outcome debt**:

```text
SHIPPED E5/C3/O1
Outcome due: 2026-08-27
Required next evidence: O3 — organic_clicks read from GSC
Owner: Connor
```

The harness already produces most of this: publishing registers a 30-day pending check, and `/kai-retro` grades it. ECO makes the debt explicit and refuses to call the item finished until it is paid.

**If a SHIPPED item has no owner and no due date, SHIPPED is just the old "done" wearing a new label.**

---

## Reading a metric too early is not O3

An O3 observation made before the declared window, or before the declared minimum sample, is not an observation — it is noise given a grade. The landing-page and paid-ad floors both carry a `minimum_sample` clause for this reason. When the window arrives and the sample is still short, the correct record is a failure record with `condition: blocked`, `next_check_at` set — not an early read.

---

## Where marketing outcomes come from

| Axis | Source of truth |
|---|---|
| Organic search | Google Search Console (site-level baseline snapshot captured at publish) |
| Site behavior | Analytics connector (GA4 or equivalent) |
| Email | ESP connector |
| Paid | Ads connector, plus an incrementality design for O5 |
| Social | Platform insights |
| Phone-led demand | Call-tracking connector (see the KaiCalls Fit Rule in `AGENTS.md`) |
| Adoption of advice | Manual, owner-attested — the weakest source, so it caps at O3 |

---

## How this changes day-to-day work

Before ECO, a skill's job was to produce an artifact and pass a gate. After ECO, a skill's job is to reach a declared floor, and the artifact is a means to it.

That changes three habits:

1. **Declare the outcome before writing.** The O1 baseline — metric, source, pre-state, threshold, window, owner — is captured at brief time, not after the piece performs. See `harness/brief-schema.md`.
2. **Stop at the floor, not at the artifact.** A skill that produces a draft and stops has reached E1. If the floor is E5, the work is still open.
3. **Record the failure.** An attempt that ends short of the floor writes a failure record naming the axis that failed. "The publish step errored" in prose does not count.

Related: `knowledge/frameworks/marketing-science/attribution-and-incrementality.md` · `knowledge/frameworks/marketing-science/experiment-rigor.md` · `harness/references/audit-data-provenance.md`
