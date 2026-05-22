---
issue: 2
title: "Kai Harness — Marketing Intelligence System (CLAUDE.md for Marketing)"
state: OPEN
labels: [enhancement]
assignees: []
created: 2026-03-20T02:05:34Z
updated: 2026-03-20T02:05:34Z
author: cgallic
url: https://github.com/cgallic/kai-cmo-harness/issues/2
comments_count: 0
reactions_count: 0
---

# #2: Kai Harness — Marketing Intelligence System (CLAUDE.md for Marketing)

## Description

## Concept

Claude Code has CLAUDE.md. It tells the coding agent: here's the repo, rules, tools, what good looks like.

**Kai Harness is the same thing, for marketing.**

Without it: inconsistent output. Quality depends on who prompted it.
With it: every content task runs through the same pipeline. Research → brief → write → quality gate → publish → measure → learn.

## Core Philosophy

**Three laws:**
1. **No brief, no write.** Every piece starts with research brief. No exceptions.
2. **No publish without gate.** Four U's ≥12/16, banned words clean, SEO lint pass. Automated.
3. **No publish without tracking.** Every piece gets performance entry. 30-day check runs automatically.

## System Map

```
MARKETING.md ← Master map (entry point for all agents)
  ↓
Research Agent → Brief (300 words)
  ↓
Write Agent → Draft (format-specific)
  ↓
Gate Agent → Pass/Fail (hard block)
  ↓
Publish + Log
  ↓
30-Day Measure
  ↓
Knowledge Base Update (self-improvement loop)
```

## Components

1. **MARKETING.md** — The harness config (like CLAUDE.md)
2. **Brief Schema** — Input contract for every content task
3. **Quality Gate Scripts:**
   - `four_us_score.py` — LLM-graded 1-4 per U, min 12/16
   - `banned_word_check.py` — Tier 1 = hard block
   - `seo_lint.py` — Title/meta/H2 checks
4. **Pipeline Orchestrator** — `kai-harness run` CLI
5. **Self-Improvement Loop** — Pattern extraction on wins, knowledge base updates
6. **Skill Contracts** — yaml interface for every content skill

## What Changes Day-to-Day

**Before:**
"Write a blog post about law firm call answering"
*[Manual skill selection, quality eyeballing, publish, forget]*

**After:**
`kai-harness run --task blog --site kaicalls --keyword "law firm call answering"`
*[Auto: GSC data → brief → write → self-score → approval request → publish → log → 30-day check → pattern extraction]*

## Timeline

- **Week 1:** Scaffolding (MARKETING.md, 3 quality gate scripts)
- **Week 2:** Pipeline (orchestrator, research brief generator, content log)
- **Week 3:** Feedback loop (performance check, pattern extraction)
- **Week 4:** Refinement (pattern-based harness updates, dashboard)

## Related

- OpenAI Harness Engineering: https://openai.com/index/harness-engineering/
- Viv Trivedy (@Vtrivedy10): vtrivedy.com/posts/claude-code-sdk-haas-harness-as-a-service
- HumanLayer breakdown: humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents
- ETH Zurich study: arxiv.org/abs/2602.11988
- Full spec in #build Discord channel

## Status

Ready to build Week 1
