# Changelog

## Unreleased — 2026-07-22 (second pass)

### Adoption-focused README + status-table completions

**README**
- Leads with a 60-second no-API-key first run (`/kai:kai-gate` right after plugin install) and a real gate scorecard excerpt from `demo/examples/`
- New "Why Not A Blank Chat?" honest comparison (blank chat / prompt pack / script toolbox / Kai)
- Requirements reduced to the truth: Claude Code (or Cursor/Codex) running — nothing else

**Status-table completions (audited against the code, then wired)**
- Learning + memory → Built: the writing prompt now auto-retrieves measured losers (`memory/what-doesnt-work.md`) alongside winners and runtime memory (`scripts/content/engine.py` + `_writer.py`); proposals can attach prior brand learnings via `action_from_finding(base_dir=...)`
- Watchers/monitoring → Built with credential-gated feeds: `WebsiteHealthWatcher` checks are live (stdlib HTTP status with GET-fallback, TLS expiry via real handshake, form-endpoint reachability, phone presence/mismatch, tracking-script detection); new `watchers_tick` agent task runs archetype watcher packs on the daily cron loop; `NotificationSystem.dispatch_finding` delivers immediate findings through the agent notification channel; `create_default_registry()` registers all 13 watchers
- Creative module relabeled Built (by design): recipe generator + LLM-backed writers is the intended architecture
- Autonomous campaign loops relabeled Guarded, working; remote automation scheduling stays honestly Planned
- 14 new regression tests (`tests/test_watchers_live.py`); full suite 888 passing

## 2026-07-22

### Launch polish — clean root, accurate README

- **Root cleanup**: retired the legacy `/content-*` skill family, the old `setup` installer, `kai-upgrade`, and the root router `SKILL.md` into `legacy/` (with a README mapping each item to its replacement, per `docs/install-ux-research.md`); moved `voice-gate/` to `harness/voice-gate/` (runner path updated), `taste/` research notes to `docs/research/taste/`, status reports (`TODO.md`, `TEST-RESULTS.md`, `INTEGRATION-SUMMARY.md`, `CONTEXT_HEALTH.md`) to `docs/status/`, `VIDEO-PRODUCTION.md` to `docs/`, and demo audio to `demo/audio/`
- **Deleted**: stray test audio artifacts, `restart.prompt` (personal session notes), and both `.bak-20260618` context backups
- **README rewrite**: removed the duplicated second half (repeated positioning, tables, and repo maps), corrected stale counts (47 public `/kai` commands, 52 `kai-*` skills, 67 playbooks, 33 frameworks), added the 8 missing commands to the reference tables (`/kai-start`, `/kai-brand-pulse`, `/kai-content-batching`, `/kai-funnel-audit`, `/kai-hook-bench`, `/kai-offer-builder`, `/kai-proof-builder`, `/kai-retro`), replaced the nonexistent `kai-harness` wrapper and `serve.sh` references with real invocations, and consolidated to a single repository map reflecting the new layout

## 2026-07-05

### Install UX overhaul — plugin marketplace + installer v2

**Claude Code plugin (new hero install path)**
- Repo is now a plugin marketplace: `/plugin marketplace add cgallic/kai-cmo-harness` then `/plugin install kai@kai-marketing-os` — two lines inside Claude Code, no terminal
- `plugins/kai-marketing-os/` packages skills + knowledge + references + contracts + quality gates (~7 MB) via symlinks, dereferenced at install; workspace/site/media junk never ships
- `version` intentionally omitted from plugin.json → SHA-based auto-updates on every push

**install.sh v2.0.0**
- Now installs the knowledge base to `~/.claude/kai/` (v1 shipped skills whose referenced frameworks/contracts/gates were never installed)
- `kaicalls-design` is optional (warn, not fail); uses local checkout when run from one
- Executable bits fixed on `install.sh`, `setup.sh`, `deploy.sh`, `setup`, `bin/*` (previously `./install.sh` failed on every fresh clone)

**Skills**
- 34 skills gained a "Kai root note" so `knowledge/`/`harness/`/`scripts/` paths resolve in all three install modes (repo, plugin cache, `~/.claude/kai`) and missing `scripts/` commands are skipped-and-declared, never fabricated
- `/kai-start`: goal-loop step auto-skips without `scripts/harness_cli.py`; first recommendation is now `/kai-growth-plan` (works anywhere) instead of `/kai-audit` (repo-only collectors)
- `/kai-audit`: explicit qualitative mode when collectors are unavailable — unmeasured numbers go to `_data-gaps.md`, never estimated
- Fixed `kai-growth-hacker` YAML frontmatter (unquoted `:` silently dropped all skill metadata)

**Docs**
- README + Quick Start lead with the plugin path; manual install now includes the knowledge payload; research + design decisions in `docs/install-ux-research.md`

## v0.3.0 — 2026-07-05

### Long-Horizon Loops (#37, #39)

**Publish truthfulness**
- Engine no longer logs fabricated URLs. Auto-publish is double-opt-in (`publishing.enabled` + `publishing.sites.<site>`, default OFF); otherwise entries log `approved_unpublished` (`url: null`) until `content_log.mark_published()` backfills the real URL — which also arms the 30-day check
- Content-hash dedup on log + publish; WordPress slug-lookup updates instead of duplicating and never demotes a live post
- Publisher success without a returned URL logs `approved_unpublished` (recoverable), never an unmeasurable `published/url=None`

**Scheduler self-containment**
- Agent loop now seeds the self-improvement crons itself: 30-day performance check (daily 02:00), pattern extract + defaults update (Mondays) — no external crontab needed
- New editorial calendar (`scripts/campaigns/calendar.py`, `data/calendar/editorial.jsonl`) + hourly tick task: dated items become drafts through the normal gate/approval pipeline; stale `generating` items auto-recover

**Goal loop (plan → act → measure → replan)**
- `kai-harness goals add|list|update` writes the GoalRegistry
- Weekly `cmo_review` task (Mon 07:00): goal pace from graded 30-day results → GoalDecomposer task graphs for behind-pace goals → executed by the existing loop; failed graphs flag `needs_replan`
- All actions still gate through ActionStore approval + mandates

**Learning-loop repair**
- Grade vocabulary unified on `underperformer` (the `loser` grade was never produced — the negative flywheel could never fire); shared `grades.py` tolerates dict/legacy-string `performance_30d`
- EC-15 partial: site-level GSC baseline captured when an entry gains a real URL; 30-day grading adds `baseline_relative` context (baseline-less entries grade identically to before)
- EC-13 promoted: pattern-extract circuit breaker persists to disk, survives restarts, 1h cooldown

**Campaign identity & state**
- `campaign_id` minted at plan time, threaded planner → tracker → RuntimeStore `campaign_plan` artifact → content log → pending checks
- `migrate_legacy_log.py` merges `~/.kai-marketing/content-log.jsonl` into canonical `data/content_log.json`; gateway job retention 7 → 45 days
- Business-profile overlay store (`data/runtime/profile/`) — onboarding answers persist across sessions

**Instruction chain & CI**
- Recreated `.claude/rules/architecture-and-memory.md` + `scripts-and-tools.md` (were referenced but missing/gitignored); `doctor.py` fails on dangling doc references
- CI runs the full test suite (was 2 files); fixed impossible `searchconsole` pin; removed duplicate `config.example.yaml`
- Tests: 575 → 806 passing

## v0.2.0 — 2026-03-25

### Taste, Creative Production & Component Architecture

**Taste Scoring (6 new quality rules)**
- `TS-01` Specificity density — catches vague claims without numbers/names/examples
- `TS-02` Emotional resonance — catches flat, clinical language that doesn't trigger action
- `TS-03` Originality score — catches AI clichés, buzzwords, and template language
- `TS-04` Hook strength — catches weak openings ("In today's rapidly evolving...")
- `TS-05` CTA clarity — catches missing or generic calls-to-action ("learn more")
- `TS-06` Proof density — catches claims without named evidence
- New "Taste" category at 20% weight. Total rules: 28 → 35 across 5 categories.

**Brand System**
- `kai-config get/set brand.*` — design tokens stored in config
- Brand section in `~/.kai-marketing/config.yaml` (colors, fonts, voice, assets)
- `lib/components/creative/brand_tokens.py` — extract from tailwind/CSS/package.json
- Auto-generates Remotion `brand.ts` from config

**Remotion Video Ad Pipeline**
- New skill: `/ad-render` — scaffold Remotion projects from brand config + creative brief
- New CLI: `kai-render scaffold/render/archetypes`
- `lib/components/creative/scene_builder.py` — converts brief → scene compositions
- 4 archetypes: Problem-Agitation, Social Proof, Product Demo, Lifestyle
- Renders to MP4 in vertical (9:16), square (1:1), landscape (16:9)

**Component Library (`lib/components/`)**
- `creative/brand_tokens.py` — extract + convert design tokens
- `creative/format_specs.py` — char limits, dimensions, durations for 12 platform placements
- `creative/scene_builder.py` — Remotion scene composition generator
- `creative/copy_variants.py` — generate N copy variants for A/B testing
- `scoring/specificity.py` — reusable specificity scorer
- `research/keyword_scorer.py` — keyword opportunity scoring (0-100)

### Operational Edge (Real Code)

**A/B Test Tracker**
- `kai-ab create/record/analyze/list` — SQLite-backed variant tracking
- Two-proportion z-test for statistical significance
- Sample size estimation for planning
- Winner detection at 95% confidence threshold

**Scheduled Analytics Pull**
- `scripts/analytics/scheduled_pull.py` — cron-compatible weekly GSC/GA4/Meta data pull
- Timestamped JSONL snapshots in `~/.kai-marketing/analytics/snapshots/`

**Ad Policy Freshness Checker**
- `scripts/ads/policy_freshness.py` — tracks 10 platform policy files for staleness
- Reports age, source URLs for updates, changelog links

**Competitive Monitor**
- `scripts/analytics/competitive_monitor.py` — track competitor website changes
- Pricing signal extraction, content hash diffing, archived snapshots

**Performance Dashboard**
- `scripts/analytics/performance_dashboard.py` — weekly summary, 12-week trends, degradation alerts
- Ranking drop detection, CTR decline flagging

### Knowledge Base Expansion (153 total files)

**New Playbooks (+22)**
- Ad creative best practices, Ad campaign management, Social media strategy
- Video content creation, Product launch, Influencer marketing
- PR & communications, CRO / conversion optimization, Analytics & attribution
- Retargeting & remarketing, Marketing automation, Growth loops (applied)
- Brand positioning, Pricing strategy, Customer journey mapping
- Marketing by company stage, SEO link building, Technical marketing / tracking
- Content repurposing, Competitive intelligence, SaaS metrics deep dive
- Demand generation, Account-based marketing, Partnership / co-marketing
- Customer retention, Event & webinar marketing, E-commerce marketing
- Marketing budget & forecasting, SEO internal linking, Podcast marketing

**New Channel Guides (+5)**
- YouTube, Instagram, X/Twitter, Affiliate & referral, Community building, Newsletter strategy

**New Checklists (+6)**
- Ad launch, Creative production, Website launch, Social media audit
- CRO audit, Google Ads launch, LinkedIn Ads launch

**New Frameworks (+2)**
- 50 copywriting formulas (PAS, AIDA, BAB, + 47 more)
- Loop mechanics (12 loop types, 7 thinking personas, viral diagnostics)

---

## v0.1.0 — 2026-03-24

Initial release as a skill-based marketing platform.

### Skills (11 slash commands)
- `/content-brief` — Generate strategic briefs from (format, site, keyword)
- `/content-write` — Write content using brief + framework + persona + learned patterns
- `/content-gate` — Score content against quality rules with auto-retry
- `/content-report` — Pull GSC + GA4 performance data for published content
- `/content-retro` — Extract winner patterns and auto-update learned defaults
- `/ad-copy` — Platform-compliant ad copy with TOS rules for 9 platforms
- `/email-sequence` — Email nurture flows with lifecycle + perception engineering
- `/seo-audit` — Technical SEO audit with 17-point checklist
- `/content-ideas` — Keyword gap analysis + persona matching
- `/marketing-sprint` — Full pipeline in one command
- `/kai-upgrade` — Self-updater

### Infrastructure
- `bin/` CLI tools: kai-gate, kai-brief, kai-config, kai-report
- `setup` script with multi-platform detection (Claude Code, Codex, Gemini)
- `~/.kai-marketing/` persistent state directory
- Voice consistency quality gate rule (VC-01)

### Knowledge Base
- 100+ marketing frameworks
- 17 validation checklists
- 8 audience personas
- 9 ad platform TOS policies + cross-platform compliance
- 12 AEO/AI search files
