# Experimentation Ledger

> **Use when:** Planning, reading, or promoting marketing experiments across ads, landing pages, email, SEO, sales motions, pricing, or content systems.

---

## Core Thesis

Kai treats experiments as memory candidates, not one-off campaign notes.

An experiment can change the operating system only after it has:

- A clear hypothesis.
- A declared data source.
- A dry-run or preflight artifact.
- A confidence label.
- A business-value note.
- Human approval before any live mutation.

Never promote a result because it "looks right" in one dashboard. Promote it when the evidence, limits, and next action are legible.

---

## Required Inputs

| Input | Requirement |
|-------|-------------|
| `mode` | `sales_external`, `onboarding_connected`, or `internal_demo` |
| `workflow` | Skill or workflow that created the experiment |
| `owner` | Human accountable for approval |
| `hypothesis` | One falsifiable sentence |
| `primary_metric` | The metric that decides the read |
| `guardrail_metrics` | Metrics that can block promotion |
| `sources` | URLs, exports, dashboards, logs, or collector outputs |
| `sample_floor` | Minimum read volume before any decision |
| `start_date` | YYYY-MM-DD |
| `planned_read_date` | YYYY-MM-DD |

Missing inputs go into `_data-gaps.md`. Do not fill gaps with assumptions.

---

## Ledger Schema

Use one row per experiment read.

| Field | Notes |
|-------|-------|
| `experiment_id` | Stable ID across planning, readout, and memory promotion |
| `mode` | Data provenance mode |
| `status` | Planned / running / paused / read / promoted / archived |
| `risk_tier` | Low / medium / high based on spend, audience, compliance, and mutation risk |
| `hypothesis` | Falsifiable claim |
| `variant_a` | Control or current state |
| `variant_b` | Proposed change |
| `primary_metric` | Decision metric |
| `guardrail_metrics` | Metrics that can veto |
| `source_refs` | Links to source ledger entries |
| `result` | Win / loss / inconclusive / invalid |
| `confidence` | Low / medium / high |
| `practical_impact` | Expected business value if repeated |
| `limitations` | Seasonality, sample, attribution, data quality, channel drift |
| `next_action` | Iterate / graduate / pause / retest / archive |
| `approval_state` | Draft / requested / approved / rejected |
| `memory_candidate` | Yes / no |

---

## Workflow

1. Write the hypothesis and decision rule before looking for a winner.
2. Run a privacy scan on source files, exports, transcripts, and screenshots.
3. Create the dry-run artifact for any action that could publish, send, upload, enroll, activate, delete, or change spend.
4. Log source refs, retrieval dates, and mode.
5. Read the result only after the sample floor is met.
6. Mark invalid experiments before interpreting performance.
7. Record confidence and limitations.
8. Request approval before live mutation or memory promotion.
9. Add the result to Kai memory only when the decision survives source, privacy, and mutation checks.

---

## Decision Labels

| Label | Meaning |
|-------|---------|
| Win | Result beat the decision rule and guardrails held |
| Loss | Result missed the decision rule |
| Inconclusive | Sample, variance, or attribution cannot support a decision |
| Invalid | Setup error, tracking error, policy issue, audience mismatch, or source failure |
| Retest | Signal exists but the read is not strong enough to promote |

Use "inconclusive" generously. False certainty is more expensive than a slower read.

---

## Promotion Rules

Promote an experiment into Kai memory only when all are true:

- Source refs are present.
- Quantitative claims cite collector output, export, dashboard, or URL.
- Privacy scan passes.
- Mutation risk is cleared.
- The owner approved the next action.
- The lesson is reusable outside the exact run.
- The memory has an expiration or review date.

Do not promote simulated expert scoring, internal demo data, or one-off anecdotes as proof.

---

## Readout Template

```markdown
# Experiment Readout

Experiment ID:
Mode:
Owner:
Read date:

## Hypothesis

## Sources
- Source:
- Retrieved/exported:
- Evidence tier:

## Result
- Decision:
- Primary metric:
- Guardrails:
- Confidence:

## Limits
- Data gaps:
- Attribution limits:
- Seasonality/channel drift:

## Next Action
- Dry-run artifact:
- Approval state:
- Memory candidate:
```
