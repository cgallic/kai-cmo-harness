# Licensing

Kai Marketing OS is dual-licensed. The rule is simple:

**If it ships to your machine when you install the plugin, it's MIT. If it runs
our hosted service, it's Elastic License 2.0.**

## The map

| Path | License | Why |
|---|---|---|
| `harness/` | MIT | Skills, skill contracts, references, ECO floors, brief schema — the plugin |
| `knowledge/` | MIT | Playbooks, checklists, frameworks, channel guides, personas |
| `docs/` | MIT | Documentation shipped alongside the plugin |
| `plugins/` | MIT | Plugin manifests, subagents, and the materialized plugin payloads |
| `scripts/quality_gates/` | MIT | Four U's scoring, banned-word checks, SEO lint, provenance lint, ECO gate |
| `scripts/reddit_monitor/` | MIT | Reddit Intelligence module — installed by `install.sh` and shipped in the plugin |
| **everything else** | **Elastic License 2.0** | `app-meetkai/`, `daemon/`, `agent/`, `gateway/`, `kai/`, `lib/`, `tools/`, `bin/`, `deploy/`, `evals/`, `site/`, `prod-static/`, and the rest of `scripts/` |

The rule that generates this table: **anything the plugin or `install.sh` copies
onto a user's machine must be MIT.** If a new payload is added to
`scripts/sync_plugin_assets.py` or to `install.sh`, its canonical directory
needs an MIT `LICENSE` and a row here — otherwise the same file ends up ELv2 at
its canonical path and MIT inside the plugin.

Each MIT subtree carries its own `LICENSE` file. The root `LICENSE` carries the
Elastic License 2.0 in full and governs everything not listed above.

## What that means in practice

**You can, freely and forever:**

- Install the plugin, use every skill, and use the knowledge base commercially.
- Fork the plugin, modify the skills, and redistribute them — including inside a
  paid product of your own.
- Read all of the source in this repository.
- Self-host `app-meetkai/`, `daemon/`, and `gateway/` for your own use, or for
  your own company's internal use.

**You cannot:**

- Offer the Elastic-licensed portion to third parties as a hosted or managed
  service that gives them access to a substantial set of its features. That is
  the one thing the Elastic License forbids, and it is the thing we sell.
- Remove or obscure the licensing notices.

If you want to offer a hosted service built on the Elastic-licensed portion,
that's a conversation, not a prohibition — reach out.

## Third-party material

Some skills are vendored from other open-source projects. Each keeps its own
license and copyright notice in its folder, and that notice governs it, not the
table above.

| Path | Upstream | License |
|---|---|---|
| `harness/skills/design-taste-frontend/`, `harness/skills-v2/design-taste-frontend/` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) `skills/taste-skill/SKILL.md` @ `3c7017d` | MIT, Copyright (c) 2026 Leonxlnx |
| `harness/skills/ux-writing/`, `harness/skills-v2/ux-writing/` | [content-designer/ux-writing-skill](https://github.com/content-designer/ux-writing-skill) `SKILL.md`, `docs/`, `examples/`, `references/`, `templates/` @ `98cacde` | MIT, Copyright (c) 2026 Christopher Greer |

## The prior MIT grant

Every commit published to this repository before **2026-08-08** was released
under the MIT License. Relicensing is not retroactive: those versions remain MIT
for anyone who obtained them, permanently, including the parts now covered by
the Elastic License. This change governs versions from 2026-08-08 onward.

We're stating this plainly rather than quietly hoping nobody notices, because
pretending otherwise would be both wrong and unenforceable.

## Contributions

By contributing to this repository you agree that your contribution is licensed
under the license that already applies to the path you're changing, per the map
above.

## Questions

Open an issue, or contact Connor Gallic (me@connorgallic.com).
