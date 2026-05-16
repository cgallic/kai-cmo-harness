# Agent-Readiness Audit

## Recommendation

Kai should keep its custom `scripts/quality_gates/agent_readiness_lint.py` as the default CI gate and use `agentic-seo` as an optional broader audit.

Reason: Kai already needs repo-specific checks that map to its own AEO workflow: explicit AI crawler rules, `llms.txt`, no JavaScript gating, capability signaling, and Organization or SoftwareApplication schema. The external `agentic-seo` project is useful as a reference and spot check because it audits discovery, structure, token cost, capability signals, and copy-for-AI affordances.

Reference: https://github.com/addyosmani/agentic-seo

## Current State

| Area | Status | Evidence |
|------|--------|----------|
| Repo machine entrypoint | Fixed | Added root `llms.txt`. |
| Public site machine entrypoint | Fixed | Added `site/llms.txt`. |
| App dashboard machine entrypoint | Fixed | Added `app-meetkai/public/llms.txt`. |
| AI crawler policy | Fixed for static site | Added `site/robots.txt` with explicit AI bot rules. |
| App crawler policy | Partial | `app-meetkai/public/robots.txt` blocks private routes, but now needs explicit AI bot rules. |
| Markdown docs | Pass | README, AGENTS, MARKETING, knowledge index, and harness docs are markdown. |
| Capability signaling | Pass | README and MARKETING.md now name skills, runtime surfaces, gates, approvals, connectors, and scheduled tasks. |
| Token cost | Partial | The repo has long framework files. `llms.txt` points agents to index files first. |
| JS gating | Partial | Static docs are markdown and HTML. The dashboard public page is a login surface, not primary docs. |

## Follow-Up Fixes

1. Add explicit AI bot sections to `app-meetkai/public/robots.txt`.
2. Add copy-for-AI buttons or raw markdown links on public docs if the static site grows beyond one page.
3. Keep `llms.txt` under 8 KB so agents can fetch it cheaply.
4. Add `python scripts/quality_gates/agent_readiness_lint.py <production-url> --strict` to release checks once a public docs URL is stable.
5. Run `npx agentic-seo --url <docs-url>` during quarterly docs reviews for a wider heuristic score.

## Minimal Release Gate

```bash
python scripts/quality_gates/agent_readiness_lint.py https://meetkai.xyz --strict
python scripts/quality_gates/agent_readiness_lint.py https://app.meetkai.xyz --strict
```

P0 failures block AEO or surround-sound work. P1 failures create follow-up tasks unless the page is intentionally private.
