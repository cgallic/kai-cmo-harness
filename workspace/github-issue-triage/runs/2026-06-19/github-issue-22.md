# GitHub Issue Triage Run: 2026-06-19

## Inventory

- needs_triage: 2 at intake (#21, #22)
- actionable_now: 1 (#22)
- needs_info: 0
- duplicate_candidate: 0
- blocked: 0
- stale_or_low_value: 1 (#21)
- security_or_private_disclosure_needed: 0
- already_fixed_or_has_pr: 0
- open_prs_at_intake: 0

## Metadata And Comments Applied

- Created/confirmed compact labels: `type/bug`, `type/chore`, `area/runtime`, `area/deps`.
- Labeled #22 with `type/bug`, `priority/p2`, `area/runtime`, `area/deps`, and moved status from `status/ready` to `status/in-progress`.
- Commented on #21 explaining it appeared to be a tracker test issue with no actionable Kai CMO Harness work.
- Closed #21 as not planned after the cleanup comment.

## Selected Issue

- Issue: #22, "deps: openai (OpenRouter client) is required but undeclared - agent loop crashes on clean install"
- Why actionable: the issue named concrete imports and a single dependency manifest target. Fresh `origin/main` already declared `openai`, but scoped import inspection confirmed `aiohttp` and `feedparser` were still imported by repo scripts and missing from `scripts/requirements.txt`.

## Files Inspected

- `AGENTS.md`
- `memory/MEMORY.md`
- `scripts/requirements.txt`
- `agent/llm/router.py`
- `scripts/leads/lead_pipeline.py`
- `scripts/reddit_monitor/reddit_digest.py`
- `scripts/knowledge_cloner/discovery.py`

## Files Changed

- `scripts/requirements.txt`
  - Added `aiohttp>=3.9.0` for the async lead pipeline.
  - Added `feedparser>=6.0.0` for Reddit monitor and knowledge cloner RSS parsing.

## Verification

- `python -c "<requirements declaration check>"` verified `openai`, `aiohttp`, and `feedparser` are declared.
- Focused clean temp virtualenv verification passed:
  - Installed `openai>=1.0.0`, `aiohttp>=3.9.0`, and `feedparser>=6.0.0`.
  - Ran `import openai, aiohttp, feedparser`.
  - Result: `focused imports ok`.
- `git diff --check` passed. It only warned that Git may normalize line endings from LF to CRLF on Windows.

## Blockers / Notes

- Full `pip install -r scripts/requirements.txt` was attempted in a disposable temp virtualenv but failed before reaching this slice because `searchconsole>=0.2.0` has no matching distribution available to pip in this environment. That appears unrelated to #22 and should be handled as the next dependency cleanup slice.
- The primary workspace at `E:\Dev2\kai-cmo-harness` had pre-existing local changes on `main`, so implementation used a separate clean worktree at `E:\Dev2\kai-cmo-harness-issue-22`.

## PR / Merge Status

- Branch: `codex/issue-22-declare-agent-deps`
- PR: pending at run-note creation time.
- Merge: pending at run-note creation time.

## Next Recommended Slice

Fix or re-scope the `searchconsole>=0.2.0` requirement so a full clean `pip install -r scripts/requirements.txt` can complete.
