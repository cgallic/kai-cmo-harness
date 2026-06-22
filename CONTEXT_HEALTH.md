# Context-Health Issues — `kai-cmo-harness`
_Audited 2026-06-17 · score **11/100** · regenerate with `context_audit.py --root . --emit-issues`._

Each item is tagged by the tool whose file owns it (`claude` = CLAUDE.md, `codex` = AGENTS.md, etc.) so you can trace it back. Fix guidance: `CONTEXT_HEALTH_STANDARD.md`.

## `agent` files

- [ ] **[HIGH] CONTEXT-BUDGET** — `(repo-level)` — Root always-on context (CLAUDE.md + AGENTS.md) totals 1065 lines (> 400). Context rot: adherence drops as loaded tokens grow. Consolidate to one bridged file and move detail into path-scoped rules or skills loaded on demand.
- [ ] **[HIGH] NO-DUP-DIR** — `(repo-level)` — ./ has CLAUDE.md AND AGENTS.md that are ~91% identical and neither @-imports the other. Pick one source of truth; have the other `@import` it (Claude ignores AGENTS.md).

## `claude` files

- [ ] **[HIGH] CMD-BYTES** — `CLAUDE.md` — 36KB — over 25KB; this file is heavy on every load.
- [ ] **[HIGH] CMD-LEN** — `CLAUDE.md` — 642 lines — far over the ~200-line cap; long files reduce instruction adherence (Anthropic memory docs).

## `codex` files

- [ ] **[HIGH] CMD-BYTES** — `AGENTS.md` — 27KB — over 25KB; this file is heavy on every load.
- [ ] **[HIGH] CMD-LEN** — `AGENTS.md` — 423 lines — far over the ~200-line cap; long files reduce instruction adherence (Anthropic memory docs).
- [ ] **[HIGH] CMD-LEN** — `workspace/AGENTS.md` — 375 lines — far over the ~200-line cap; long files reduce instruction adherence (Anthropic memory docs).
- [ ] **[HIGH] REGROUND-PTR** — `AGENTS.md:1` — Root context file has no re-grounding / 'read this first' pointer in the first 15 lines. A fast model will act before loading context. Add a top-of-file read-before-act gate (see CONTEXT_HEALTH_STANDARD.md).
- [ ] **[MEDIUM] CRIT-FIRST-N** — `workspace/AGENTS.md:219` — 5 IMPORTANT/MUST/NEVER rule(s) appear after line 40 (first at L219); critical rules get lost mid-file.
- [ ] **[LOW] CMD-BYTES** — `workspace/AGENTS.md` — 19KB — over the 12KB warn threshold.
- [ ] **[LOW] REGROUND-PTR** — `workspace/AGENTS.md:1` — Nested context file (80+ lines) has no 'read this first' pointer; add one so an agent working in this subtree grounds before acting.
