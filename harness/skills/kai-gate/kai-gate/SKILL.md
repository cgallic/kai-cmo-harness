---
name: kai-gate
description: Run Kai CMO Harness quality gates on content. Scores Four U's (Unique/Useful/Ultra-specific/Urgent), checks for banned words and AI slop, runs SEO lint for search content. Use when "score this", "quality check", "run quality gates", "check this content", "four u's score", "banned word check", "SEO lint", or any request to validate content quality before publishing.
---

Run the Kai CMO Harness quality gate pipeline on a piece of content.

## Gate Pipeline

Run all three checks in order:

### 1. Four U's Score

Score each dimension 1-4:

| U | Question | Score |
|---|----------|-------|
| **Unique** | Can only WE write this? Original data, perspective, or experience? | 1-4 |
| **Useful** | Can the reader take action immediately? | 1-4 |
| **Ultra-specific** | Numbers, named tools, concrete examples? | 1-4 |
| **Urgent** | Is there a reason to engage today? | 1-4 |

**Thresholds:** 12/16 for blog/SEO/articles. 10/16 for email/ads.

### 2. Banned Word Check

**Instant reject (Tier 1):** leverage, utilize, synergy, innovative, deep dive, circle back, touch base, moving forward, at the end of the day

**AI slop (also reject):** "In conclusion", "It's important to note", "In today's rapidly evolving", "This comprehensive guide", "Without further ado", "It's worth noting that"

Flag exact locations of violations.

### 3. SEO Lint (search content only)

Apply only if the content targets search engines. Check against Algorithmic Authorship rules:
- Conditions after main clause
- Instructions start with verbs
- Sentences under 20 words
- Bold the answer, not query terms
- No links in first sentence of paragraphs

For full rule set, read `E:\Dev2\kai-cmo-harness-work\knowledge\frameworks\content-copywriting\algorithmic-authorship.md`.

## Output Format

```
## Quality Gate Results

**Four U's:** [X]/16 [PASS/FAIL]
- Unique: [X]/4 — [reason]
- Useful: [X]/4 — [reason]
- Ultra-specific: [X]/4 — [reason]
- Urgent: [X]/4 — [reason]

**Banned Words:** [PASS/FAIL]
- [list violations with line numbers, or "None found"]

**AI Slop:** [PASS/FAIL]
- [list violations with line numbers, or "None found"]

**SEO Lint:** [PASS/FAIL/SKIPPED]
- [list violations, or "All rules pass"]

**Overall:** [PASS/FAIL]
```

If FAIL: list specific fixes needed. Offer to auto-fix and re-score.
