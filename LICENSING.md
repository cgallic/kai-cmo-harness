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
| **everything else** | **Elastic License 2.0** | `app-meetkai/`, `daemon/`, `agent/`, `gateway/`, `kai/`, `lib/`, `tools/`, `bin/`, `deploy/`, `evals/`, `site/`, `prod-static/`, and the rest of `scripts/` |

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
