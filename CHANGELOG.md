# Changelog

## v0.1.0 — 2026-03-24

Initial release as a skill-based marketing platform.

### Skills (11 slash commands)
- `/content-brief` — Generate strategic briefs from (format, site, keyword)
- `/content-write` — Write content using brief + framework + persona + learned patterns
- `/content-gate` — Score content against 28 quality rules with auto-retry
- `/content-report` — Pull GSC + GA4 performance data for published content
- `/content-retro` — Extract winner patterns and auto-update learned defaults
- `/ad-copy` — Platform-compliant ad copy with TOS rules for 9 platforms
- `/email-sequence` — Email nurture flows with lifecycle + perception engineering
- `/seo-audit` — Technical SEO audit with 17-point checklist
- `/content-ideas` — Keyword gap analysis + persona matching for topic suggestions
- `/marketing-sprint` — Full pipeline in one command: brief → write → gate → log
- `/kai-upgrade` — Self-updater

### Infrastructure
- `bin/` CLI tools: kai-gate, kai-brief, kai-config, kai-report
- `setup` script with multi-platform detection (Claude Code, Codex, Gemini)
- `~/.kai-marketing/` persistent state directory
- One-message install prompt
- Voice consistency quality gate rule (VC-01)

### Knowledge Base
- 100+ marketing frameworks
- 17 validation checklists
- 8 audience personas
- 9 ad platform TOS policies + cross-platform compliance
- 12 AEO/AI search files
