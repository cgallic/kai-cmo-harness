# Legacy

Retired surfaces kept for reference. Nothing in this directory is installed by
`install.sh` or the Claude Code plugin, and nothing in the current pipeline
reads from it.

| Item | What it was | Replaced by |
|------|-------------|-------------|
| `ad-copy/`, `ad-render/`, `ad-research/`, `checklist/`, `content-brief/`, `content-gate/`, `content-ideas/`, `content-report/`, `content-retro/`, `content-write/`, `creative-brief/`, `email-sequence/`, `marketing-sprint/`, `seo-audit/` | The original content-sprint skill family (`/content-*` commands) | The `/kai` router and `harness/skills/kai-*` skills |
| `kai-marketing-SKILL.md` | Root-level router skill for the content-sprint family | `harness/skills/kai/SKILL.md` |
| `setup` | Installer that registered the `/content-*` family | `install.sh` and the Claude Code plugin (`/plugin install kai@kai-marketing-os`) |
| `kai-upgrade/` | Self-update skill pointing at the old repo URL | `/plugin` auto-updates; `install.sh` re-runs are idempotent |

Background on why these were retired: `docs/install-ux-research.md`.
