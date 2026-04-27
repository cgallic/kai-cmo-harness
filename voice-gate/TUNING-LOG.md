# Voice Gate — Tuning Log

One-line-per-iteration log of changes to `judge-prompt.md` and what each change was meant to fix. Append new entries at the top.

---

## Iteration 3 — 2026-04-17 — Match existing Blog #1 editorial-notes output shape exactly

**Change:** Restructured the Output Format block in `judge-prompt.md` to match `how-to-write-a-podcast-pitch.EDITORIAL-NOTES.md` one-for-one — header metadata (reviewer / calibration / target file / word count / verdict), Summary Table first, numbered Detailed Issues, What's Working, Systemic Patterns, Signature-Move Count table. Added a row format for "cap hit" in the summary table. Added the constraint that every issue must cite the specific voice-guide rule or an explicitly-marked editorial principle.

**Why:** The brief specified the Voice Gate output must be structurally identical to the human-ish editorial pass already done. Without locking the output format, the judge drifts into freeform critique.

**Test result:** Simulated run against Blog #1 produced a report that matches the editorial-notes.md shape. All four brief-required issues (sing-songy intro, "I repeat" 3×, triple-list systemic pattern, "Attach nothing" stack) caught at High severity.

---

## Iteration 2 — 2026-04-17 — Hard-rule FAIL triggers explicit

**Change:** Added a concrete list of hard-rule violations that trigger FAIL on a single occurrence — Tier 1 banned vocab, year-count inconsistency, AI-slop phrase from the guide's forbidden list, cold-open rule broken on an SEO post. Previously the verdict rules said "any voice-guide hard-rule violation" without enumerating which ones.

**Why:** Ambiguous FAIL triggers let the judge under-escalate. Enumeration forces deterministic verdicts.

**Test result:** Blog #1 earned a FAIL verdict (6 High issues). Without enumeration, the prior iteration returned HOLD despite a clear "I repeat" over-cap.

---

## Iteration 1 — 2026-04-17 — Few-shot calibration block added

**Change:** Added three few-shot calibration examples (one High, one Medium, one Low) pulled from the real Blog #1 editorial notes. Each example shows the required format: verbatim quote + voice-guide citation + 2-3 sentence diagnosis + direction-only fix.

**Why:** Per the research doc (arxiv 2506.13639), "clear evaluation criteria matter more than model choice, chain-of-thought, or temperature." Few-shot examples are the single biggest quality lever. Without them the judge was writing paraphrases instead of verbatim quotes and paraphrasing rule citations instead of referencing §-numbered sections.

**Test result:** Simulated run produced verbatim quotes for every issue and voice-guide §-references for every applicable flag. Issue 1 ("I repeat" 3×) correctly counted the signature-move occurrences (3) against the cap (1).

---

## Iteration 0 — 2026-04-17 — Initial prompt shape

**Change:** Initial version of `judge-prompt.md`. Role + Inputs + Method + 9 Issue Categories + Severity Key + Hard Requirements + Output Format scaffold.

**Baseline test against Blog #1 (before iterations 1–3):**
- Caught: "I repeat" over-cap, some triple-list issues, FAQ atomicity
- Missed: the specific voice-guide §-references, the verbatim-quote hard requirement, the signature-move count table, the cap-hit summary row, the structural parity with editorial-notes.md

These misses drove iterations 1–3.
