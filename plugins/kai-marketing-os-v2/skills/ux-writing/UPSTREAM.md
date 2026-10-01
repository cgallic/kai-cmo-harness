# Upstream: ux-writing

Third-party skill, vendored unmodified.

| Field | Value |
|---|---|
| Upstream repository | https://github.com/content-designer/ux-writing-skill |
| Upstream paths | `SKILL.md`, `docs/`, `examples/`, `references/`, `templates/` (the layout of upstream `dist/ux-writing-skill.zip`), plus `LICENSE` |
| Upstream commit | `98cacde4ba2dd10ed28df43a8d53eef1e321c539` (2026-05-26) |
| License | MIT, Copyright (c) 2026 Christopher Greer. The full text is in `LICENSE` in this folder. |
| Vendored | 2026-09-30 |
| Changes | None. v1 `SKILL.md` and v2 `references/ux-writing-rules.md` are byte-identical to upstream `SKILL.md`; `docs/`, `examples/`, `references/` and `templates/` are byte-identical in both folders. The v2 `SKILL.md` is our goal-shaped wrapper around those unchanged rules. Markdown only, no scripts. |

To update: fetch the upstream repo, replace the files in both folders (upstream `SKILL.md` goes to v1 `SKILL.md` and v2 `references/ux-writing-rules.md`), bump the commit above, run `python scripts/sync_plugin_assets.py` and add a CHANGELOG line.

It is not a `kai-*` skill, so it has no page in `docs/skill-manifest/` and no row in the `/kai` router table. The router's "When In Doubt" list points to it.
