# Creative Intelligence Ledger

> **Use when:** Turning creative test results into reusable memory, planning the next creative bench, or diagnosing why winning concepts stop working.

---

## Core Thesis

The ad account is not the memory. The ledger is the memory.

A creative program improves when every test leaves behind a structured lesson:

- What concept was tested.
- What changed.
- What the market did.
- What the team learned.
- What should happen next.

Without a ledger, the team keeps rediscovering the same loser ideas with new captions.

---

## Source Baseline

Load this with:

- `knowledge/playbooks/combinatorial-creative-bench.md`
- `knowledge/playbooks/creative-test-resolution-protocol.md`
- `knowledge/playbooks/ad-creative-best-practices.md`
- `knowledge/channels/meta-advertising.md`

External reference points:

- Motion ad reverse-engineering: separates messaging angle, pain/desire anchor, persona, awareness stage, hook, format, and creative mechanic.
  Source: https://motionapp.com/library/frameworks/creative-analysis
- Motion creative strategy engine: connects pain/desire, persona, messaging angle, awareness stage, and creator-perspective choices.
  Source: https://motionapp.com/library/frameworks/creative-strategy-engine
- TikTok Creative Insights: identifies creative patterns, selling points, visual elements, and components before production.
  Source: https://ads.us.tiktok.com/help/article/creative-insights?lang=en
- Google Performance Max asset groups: asset coverage and variation affect what the system can assemble and test.
  Source: https://support.google.com/google-ads/answer/14528220

---

## Ledger Row Schema

Use one row per resolved concept test.

| Field | Required? | Notes |
|-------|-----------|-------|
| `test_id` | Yes | From the test resolution memo |
| `concept_id` | Yes | From the P.D.A. bench |
| `date_launched` | Yes | YYYY-MM-DD |
| `date_read` | Yes | YYYY-MM-DD |
| `platform` | Yes | Meta, TikTok, Google, LinkedIn, etc. |
| `campaign` | Yes | Campaign or ad set name |
| `persona` | Yes | Persona or situational segment |
| `desire` | Yes | Customer-language progress desired |
| `angle` | Yes | Message frame or proof route |
| `awareness_stage` | Yes | Unaware / problem-aware / solution-aware / product-aware / most-aware |
| `format` | Yes | UGC, founder, demo, static, carousel, screen recording, etc. |
| `hook` | Yes | First line, first frame, or primary visual hook |
| `creative_mechanic` | Yes | Cognitive / emotional mechanism |
| `proof_type` | Yes | Review, demo, stat, story, authority, comparison, guarantee |
| `offer` | Yes | Commercial promise |
| `landing_match` | Yes | Strong / acceptable / weak |
| `primary_metric` | Yes | CPA, ROAS, CVR, qualified lead rate, etc. |
| `result` | Yes | Kill / iterate / graduate / inconclusive / invalid |
| `lesson` | Yes | One reusable sentence |
| `next_action` | Yes | Produce, iterate, pause, archive, relaunch, or route to landing page |

---

## Awareness Stage Taxonomy

Tag every concept with one awareness stage.

| Stage | Viewer State | Creative Job |
|-------|--------------|--------------|
| Unaware | Does not feel the problem yet | Create recognition or interruption |
| Problem-aware | Feels pain but has not chosen a solution type | Name the problem and cost |
| Solution-aware | Knows solution category | Show mechanism and differentiation |
| Product-aware | Knows the brand or product | Prove fit, remove objections, compare |
| Most-aware | Ready to buy or inquire | Clarify offer, urgency, and CTA |

Stage mismatch is a root-cause tag, not a minor note. A strong product-aware offer can fail in cold traffic because the viewer has not accepted the problem yet.

---

## Creative Mechanic Taxonomy

Use these tags to make lessons reusable:

| Mechanic | Use When |
|----------|----------|
| Identity callout | The viewer should recognize themselves immediately |
| Loss math | The ad quantifies what inaction costs |
| Mechanism reveal | The ad shows how the product works |
| Proof stack | The ad layers reviews, demos, data, or authority |
| Contrast | The ad reframes old way vs new way |
| Objection preempt | The ad handles a known reason not to act |
| Status shift | The ad changes what the buyer feels allowed to choose |
| Time pressure | The ad makes delay feel costly |
| Social mirror | The ad shows peers choosing or discussing the solution |
| Demonstration | The ad proves the claim on-screen |

Add new mechanics only when an existing tag cannot explain the creative.

---

## Fatigue Early-Warning Layer

Track fatigue by concept family, not only by ad ID.

| Signal | Warning |
|--------|---------|
| CTR | Down 20-30% from peak |
| CPM | Up 20-30% week-over-week |
| Frequency | Above 2.5-3 in prospecting |
| Hook retention | Down from the winning baseline |
| Comment quality | More confusion, objections, or negative feedback |
| Lead quality | Sales reports lower intent |
| Delivery concentration | One ad absorbs spend while sibling concepts get no read |

When two or more warnings appear, move one adjacent concept into production before the winner fully decays.

---

## Weekly Ledger Workflow

1. Pull active tests and spend.
2. Mark invalid rows before reading performance.
3. Resolve each valid row with the test protocol.
4. Add or update ledger rows.
5. Promote winners to the 60% bucket.
6. Create adjacent tests from partial winners.
7. Archive true losers with a loser lesson.
8. Update the P.D.A. bench with the highest-signal learning.

---

## Monthly Synthesis

Create a one-page synthesis each month:

```markdown
# Creative Intelligence Synthesis

## Winners
- Concept family:
- Repeated winning pattern:
- Awareness stage:
- Proof type:
- Format:

## Losers
- Repeated losing pattern:
- Likely reason:
- Do-not-repeat note:

## Fatigue
- Concept family at risk:
- Replacement concept queued:

## Next Bench
- Personas to expand:
- Desires to sharpen:
- Angles to test:
- Proof needed:
- Landing page changes needed:
```

---

## Storage

Default location:

```
workspace/ads/creative-intelligence-ledger.csv
```

For client work, store alongside the campaign artifacts:

```
workspace/clients/{client}/ads/creative-intelligence-ledger.csv
```

CSV header:

```csv
test_id,concept_id,date_launched,date_read,platform,campaign,persona,desire,angle,awareness_stage,format,hook,creative_mechanic,proof_type,offer,landing_match,primary_metric,result,lesson,next_action
```

---

## Example Rows

| Concept | Result | Lesson | Next Action |
|---------|--------|--------|-------------|
| Admin Martyr x missed calls x loss math | Graduate | Loss math pulled qualified local-service leads when the hook named after-hours calls in the first line. | Produce adjacent proof-stack version |
| Founder x book appointments x mechanism demo | Iterate | Demo generated clicks but weak lead quality because the offer was unclear. | Keep demo, rewrite CTA and landing hero |
| Office manager x staff relief x founder story | Kill | Founder story underperformed because persona was unclear in the first 3 seconds. | Rebuild with identity callout |

---

## Anti-Patterns

- Logging platform metrics without a lesson.
- Logging lessons without the P.D.A. concept ID.
- Treating invalid tests as strategic losers.
- Keeping winner notes but deleting loser notes.
- Writing vague lessons like "UGC worked."
- Ignoring sales quality, call quality, or retention after cheap lead wins.
- Planning next month's bench from memory instead of the ledger.
