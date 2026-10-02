# Upstream: design-taste-frontend

Third-party skill, vendored unmodified.

| Field | Value |
|---|---|
| Upstream repository | https://github.com/Leonxlnx/taste-skill |
| Upstream path | `skills/taste-skill/SKILL.md` |
| Upstream commit | `3c7017d636c3a4aad378433ea6d0cfa6c921da4a` (last change to that file, 2026-05-26) |
| License | MIT, Copyright (c) 2026 Leonxlnx. The full text is in `LICENSE` in this folder. |
| Vendored | 2026-09-30 |
| Changes | None. v1 `SKILL.md` and v2 `references/taste-rules.md` are byte-identical to upstream. The v2 `SKILL.md` is our goal-shaped wrapper around those unchanged rules. |

To update: fetch the upstream file, replace both copies, bump the commit above, run `python scripts/sync_plugin_assets.py` and add a CHANGELOG line.

It is not a `kai-*` skill, so it has no page in `docs/skill-manifest/` and no row in the `/kai` router table. The router's "When In Doubt" list points to it.
