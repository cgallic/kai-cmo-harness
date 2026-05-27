# Transcript-To-Content Ops

> **Use when:** Turning calls, podcasts, webinars, sales recordings, interviews, or videos into clips, quotes, posts, briefs, newsletters, or long-form content.

---

## Core Thesis

Transcripts are source material, not permission to fabricate authority.

Kai extracts useful claims, stories, objections, and phrasing while preserving provenance, consent, privacy, and approval state.

---

## Source Requirements

Each transcript job must declare:

- Recording source and owner.
- Consent or lawful basis for internal use.
- Mode: `sales_external`, `onboarding_connected`, or `internal_demo`.
- Speaker names or anonymized speaker labels.
- Transcript source, tool, date, and confidence if known.
- Privacy scan result.
- Approved destination channels.

If consent, ownership, or speaker identity is unclear, use the transcript only for internal analysis until reviewed.

---

## Extraction Layers

| Layer | Output | Notes |
|-------|--------|-------|
| Quote candidates | Short excerpts for review | Must preserve speaker and timestamp |
| Claim candidates | Factual statements | Require source check before publication |
| Story beats | Problem, tension, action, result | Do not invent missing outcomes |
| Objections | Buyer concerns or blockers | Useful for sales, CRO, FAQ, and ads |
| Proof assets | Demos, numbers, customer language | Quantitative claims need source refs |
| Clip moments | Timestamped segments | Score for clarity, novelty, and platform fit |
| Content angles | Draft topics and hooks | Advisory until approved |

---

## Workflow

1. Ingest transcript and metadata.
2. Run privacy sanitizer before summarizing or repurposing.
3. Split the transcript into timestamped segments.
4. Extract claims, quotes, stories, objections, and clip moments.
5. Score candidates by usefulness, uniqueness, clarity, risk, and channel fit.
6. Dedupe against existing content and prior clip history.
7. Produce a dry-run content pack.
8. Request approval before publishing, scheduling, clipping, emailing, or uploading.
9. Log approved outputs and rejected candidates.

---

## Candidate Schema

| Field | Notes |
|-------|-------|
| `candidate_id` | Stable ID |
| `source_id` | Recording or transcript ID |
| `timestamp_start` | Required for audio/video |
| `timestamp_end` | Required for clips |
| `speaker` | Named or anonymized |
| `candidate_type` | Quote / clip / post / article / email / ad / FAQ |
| `source_excerpt` | Short source-backed note, not long copied transcript |
| `summary` | Kai-written abstraction |
| `risk_flags` | PII, confidential, legal, medical, financial, customer identity, unsupported claim |
| `score` | 1-5 |
| `approval_state` | Draft / requested / approved / rejected |
| `destination` | Channel or internal use |

---

## Dry-Run Content Pack

```markdown
# Transcript Content Pack

Source:
Mode:
Privacy scan:
Approval owner:

## Best Candidates
| ID | Type | Timestamp | Speaker | Score | Risk | Destination |
|----|------|-----------|---------|-------|------|-------------|

## Claims Requiring Proof

## Data Gaps

## Rejected Candidates

## Approved-Only Actions
Approval required before any action in this list.
- Publish post
- Schedule email
- Export clip
- Upload video
- Add to CMS
```

---

## Guardrails

- Do not present simulated panels or AI summaries as real expert review.
- Do not turn private customer remarks into public proof without approval.
- Do not add results, numbers, credentials, or endorsements that are not in the source ledger.
- Do not publish clips that reveal private data, account details, health data, financial data, or confidential strategy.
- Do not assume transcript accuracy for names, numbers, or legal claims.
