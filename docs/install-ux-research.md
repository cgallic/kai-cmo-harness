# Install UX — Research & Design Decisions (2026-07-05)

Findings from a 5-agent research pass (current-install audit, ICP profile, best-in-class installer research, technical-constraints audit, completeness critic) and the design decisions that came out of it. This doc is the provenance for the plugin packaging, `install.sh` v2, and the skill "Kai root note".

## Who installs Kai

Per `docs/icp-evaluation-prompt.md`, the primary installer is the **terminal-native solo technical founder** (1-5 people, can run Python, manages API keys); secondary: agency operators embedding Kai in client repos, and product engineers who want CI/CD-for-content. Non-technical marketers are explicitly out of scope for the repo funnel (meetkai.xyz routes them to the hosted app instead).

Doctrine that follows: first value in ≤3 minutes, zero API keys or config before value, "cheat code" register not wizard register, curl|bash acceptable, SaaS signup unacceptable.

## What was broken (pre-2.0 install)

1. **Hollow installs.** `install.sh` v1 copied only `harness/skills/` (848K). 34 of 49 skills reference `knowledge/`, `harness/references/`, `harness/skill-contracts/` paths, and 14 invoke `scripts/` Python — none of it installed. The installer verified green while most skills were functionally broken.
2. **Dead-end first command.** `/kai-start` and the installer both recommended `/kai-audit`, which hard-requires `python -m scripts.audit.collect` — guaranteed failure outside the repo.
3. **Hard-fail on optional assets.** The installer aborted entirely if `kaicalls-design` reference files were missing.
4. **No executable bits.** Every installer script was committed mode 644, so the documented `./install.sh`, `./deploy.sh`, `./setup` all failed on fresh clones.
5. **7+ overlapping install paths** (curl, manual cp, setup.sh A/B, legacy `setup`, repo copy ×2 variants, OpenClaw) that disagree on what to copy and never reference each other.
6. **Broken frontmatter.** `kai-growth-hacker/SKILL.md` had an unquoted `:` in its description — YAML parse failure, all metadata silently dropped at runtime.

## The design (what shipped)

### Hero path: Claude Code plugin (the "cheat")

The repo is now a **plugin marketplace** (`.claude-plugin/marketplace.json`). Install is two lines typed inside Claude Code, zero terminal:

```text
/plugin marketplace add cgallic/kai-cmo-harness
/plugin install kai@kai-marketing-os
```

Packaging mechanics (verified against code.claude.com/docs/en/plugins-reference and empirically with `claude` CLI v2.1.201):

- Installed plugins are **copied to `~/.claude/plugins/cache`**; paths outside the plugin root break. But **symlinks inside the marketplace are dereferenced at install** — so `plugins/kai-marketing-os/` is a curated directory of symlinks (`skills/` → `harness/skills`, plus `knowledge/`, `harness/references`, `harness/skill-contracts`, `harness/brief-schema.md`, `scripts/quality_gates`). The cache copy materializes ~7 MB of real files and excludes the repo's other ~106 MB (workspace/, .git, site/, mp3s…). Verified locally: 0 symlinks in cache, full payload present, no junk leaked, 49 skills registered, ~7.7k always-on tokens.
- `version` is intentionally **omitted** from `plugin.json`: version falls back to the git commit SHA, so every push is an update (docs-recommended for actively developed plugins). If we later adopt semver, remember: pushing commits without bumping the string ships nothing.
- A `CLAUDE.md`/`AGENTS.md` at plugin root is **not** loaded as context from plugins — doctrine must flow through the skills themselves.
- Plugin skills are namespaced `/kai:kai-start`. The shell-installer path keeps un-namespaced `/kai-start`.
- Validate with `claude plugin validate ./plugins/kai-marketing-os` (passes; the only warning is the intentional missing version).

### Path resolution: the "Kai root note"

Skills now carry a short note telling the agent to resolve `knowledge/`, `harness/`, `scripts/` paths against the first ancestor directory of the SKILL.md that contains `knowledge/` — which is the plugin cache root, `~/.claude/kai`, or the repo checkout, in all three install modes — and to skip-and-say-so (never fabricate) when a `scripts/` command isn't shipped. `MARKETING.md` and `memory/` always resolve to the user's project.

### install.sh v2

Ships the knowledge base (to `~/.claude/kai/`) alongside the skills, uses a local checkout when run from one, verifies knowledge + gates + skills, treats `kaicalls-design` as optional (warn, not fail), and exits onto `/kai-start` + three commands with time promises. `/kai-audit` is no longer promoted on skills-only installs.

### First-run flow fixes

- `/kai-start` Step 4 (goal loop CLI) is skipped silently when `scripts/harness_cli.py` isn't present; the goal goes into `MARKETING.md` instead.
- `/kai-start` Step 5 recommends `/kai-growth-plan` (works anywhere) and only recommends `/kai-audit` when the audit collectors exist.
- `/kai-audit` gained an explicit **qualitative mode** for installs without collectors: cite-what-you-browse, all unmeasured numbers go to `_data-gaps.md`, never estimate what the collector would have measured.

## Verified alternatives considered and rejected

- **`source: "./"` (repo root = plugin):** copies the entire 113 MB working tree into every user's plugin cache; no exclude/ignore mechanism exists in the plugin spec. Rejected for the symlinked curated subdir.
- **Checked-in copy of the payload under `plugins/`:** ~7 MB duplicated in git, guaranteed drift. Symlinks keep a single source of truth.
- **`${CLAUDE_PLUGIN_ROOT}` in SKILL.md prose:** documented for hooks/MCP/monitors, not confirmed for skill body text. The root-note convention avoids depending on it.

## Open items (owner decisions / future work)

1. **Windows checkouts without symlink support** materialize git symlinks as text files; a plugin install from such a clone would be broken. Claude Code fetches marketplaces itself (its git), so this mainly affects contributors on Windows. Watch for reports; fallback is `install.sh` under Git Bash/WSL.
2. **Four U's gate** still requires `google-genai` + `GEMINI_API_KEY` (hardcoded `gemini-2.0-flash`, dotenv path `/opt/cmo-analytics/.env`). Decide: model-self-scored fallback (needs new golden cases per the gate-change rule) vs. keeping it opt-in. The offline gates (banned words, SEO lint, provenance, agent-readiness) work with zero setup.
3. **Marketplace listing**: consider submitting to `anthropics/claude-plugins-community` (platform.claude.com/plugins/submit) for discovery + Anthropic safety-screening trust signal. Decide first whether `kaicalls-design` and the KaiCalls fit rule belong in a public listing.
4. **`npx skills add cgallic/kai-cmo-harness`** (Vercel skills CLI, agentskills.io standard) would reach Cursor/Codex/Copilot users; skills already conform. Low effort, separate PR.
5. **Team onboarding**: committing `extraKnownMarketplaces` + `enabledPlugins` in a client repo's `.claude/settings.json` prompts every collaborator to install Kai on folder-trust — the zero-command agency path.
6. **Legacy paths to retire**: the root `setup` script (registers the old `/content-*` family), the three conflicting config templates, `kai-upgrade`'s pointer at the wrong repo URL (`kai-marketing.git`), and README's `kai-harness` CLI references (no such wrapper exists — real invocation is `python scripts/harness_cli.py`). Deliberately left out of this change to keep it reviewable.
