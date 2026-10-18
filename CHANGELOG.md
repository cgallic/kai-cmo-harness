# Changelog

## Unreleased — 2026-10-03

**New skill: `/kai-page-refresh`, and the harness now grades its own SEO fixes.** Across 62 properties, four established sites carried 93% of search clicks and new satellite sites earned almost none, so the default SEO route is now "fix what already ranks, then measure it." New `scripts/seo/` package (stdlib only, shipped in both plugins): `gsc_data.py` loads a Search Console query x page export (CSV or JSON, loose headers) or pulls one from the API with its window recorded; `portfolio.py` labels each property invest / maintain / freeze by its share of non-brand clicks; `striking_distance.py` builds a refresh queue of CTR gaps (ranks 1-7, under half the expected CTR) and striking-distance queries (8-20), with brand excluded, a CTR curve calibrated on the site's own data, title-alignment checks, internal-link sources and split-query detection; `refresh_tracker.py` records each fix with a baseline that must end before the ship date, grades it at 28 days against the rest of the site's non-brand clicks, emits ECO evidence, and reports win rate by fix type. New ECO work type `page-refresh` (E3/C3/O3), playbook `knowledge/playbooks/page-refresh-loop.md`, manifest page, router row, Framework Map row, and two lessons plus one anti-pattern in `memory/`. Also re-syncs the plugin copies of `scripts/reddit_monitor/` and the social platform monitor files, which had drifted and failed the plugin-sync check on `main`.

## Unreleased — 2026-09-30

**New third-party skill: `ux-writing`.** Interface copy (microcopy) for buttons, labels, error messages, notifications, forms, onboarding, empty states, success messages and help text: four quality standards (purposeful, concise, conversational, clear), per-element patterns, tone by emotional state and stakes, a four-phase editing pass, accessibility rules and length/reading-level benchmarks. Vendored unmodified from [content-designer/ux-writing-skill](https://github.com/content-designer/ux-writing-skill) (MIT, commit `98cacde`), in the layout of upstream `dist/ux-writing-skill.zip` (`SKILL.md`, `docs/`, `examples/`, `references/`, `templates/`). v1 ships the upstream `SKILL.md` byte-for-byte; v2 is a goal-shaped wrapper with the same frontmatter, and the unchanged rules sit in `references/ux-writing-rules.md`. Both folders carry the upstream `LICENSE` and an `UPSTREAM.md`. Not a `kai-*` skill, so it has no manifest page and no router table row. The `/kai` "When In Doubt" list routes to it, and `LICENSING.md` gains a row. Synced into both plugins; the capability fixture is re-baselined (62 skill directories, 62 v2).

**New third-party skill: `design-taste-frontend`.** The anti-slop frontend skill for landing pages, portfolios and redesigns (brief inference, three dials, audit-first redesign protocol, AI-tell bans, a 60-box pre-flight check), vendored unmodified from [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) (MIT, commit `3c7017d`). v1 ships the upstream `SKILL.md` byte-for-byte; v2 is a goal-shaped wrapper with the same frontmatter, and the unchanged rules sit in `references/taste-rules.md`. Both folders carry the upstream `LICENSE` and an `UPSTREAM.md`. Not a `kai-*` skill, so it has no manifest page and no router table row. The `/kai` "When In Doubt" list routes to it, and `LICENSING.md` gains a third-party table. Synced into both plugins; the capability fixture is re-baselined (61 skill directories, 61 v2).

**New skill: `/kai-motion-spot`.** Code-rendered product video in three formats: a 20-30 s hype launch spot, a polished walkthrough built from real screenshots (with a downsample-first privacy blur), and a 19 s pain-point video whose muted site cut carries the story in burned-in text. The engine ships in both plugins as `scripts/motion_spot/`. It includes a seek(t) reference page with a real 9:16 re-layout, a walkthrough page generator, and a parallel Playwright renderer with adaptive motion blur, cut-side subframe clamping, a warm-up pass and a two-rAF paint wait. It also covers ElevenLabs Music generation (`ELEVENLABS_API_KEY` from the environment only, with `--dry-run`); drop analysis that snaps past a pre-drop hit to the real drop and reads tempo with a comb filter, plus `--verify` on the built master; a bar-accurate score builder; synthesized SFX with grid-offset reporting; QA sheets (phone-size tiles, cut tiles, privacy sheets, frame-spike scan); poster baking; and web encodes (1280 px H.264 faststart plus VP9, CRF-searched into 1.5-3 MB) with muted-autoplay or click-to-play embed snippets. An Upload-Post publisher is dry-run by default, with ids in the spec rather than in code. `harness/references/motion-spot-method.md` holds the method, taste rules and watch-back QA table. `harness/references/motion-spot-service-playbook.md` covers selling it: the deliverables menu, client inputs, turnaround, QA checklist, the approval step, sourced market price points, and an INTERNAL cost basis measured from real render logs. The price is left to the founder. The skill is registered in the `/kai` router (PRODUCE) and cross-referenced from `/kai-video-production`, and the capability manifest has been regenerated.

**Plugin ships the DataForSEO local-audit collector.** `/kai-local-audit` in the `kai` and `kai-v2` plugins now carries its own stdlib-only collector — `scripts/local_audit/` (located SERPs, map packs, volumes, listings, reviews, backlinks, AI answers, crawl, Lighthouse, direct checks), `scripts/audit/` (provenance collector) and `examples/local-audit-config.example.json` — so plugin installs run located pulls instead of falling back to qualitative mode. Credentials come only from `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD`. The skill now states how to run the modules from the plugin root, the every-search-in-every-market-language rule, the ~$8-per-run cost with caching, private hosting (noindex, unguessable URL, your own host), and that internal economics never appear on a customer-facing page. Also re-syncs the plugin copies of `scripts/reddit_monitor/`, which had drifted and failed the plugin-sync check on `main`.

## Unreleased — 2026-07-29

**New skill: `/kai-gtm-pack`** — package a client GTM engagement as a cross-linked set of private HTML pages topped by a client hub (the arrangement/ask, tool install for the client's setup, access grants as click-paths, and the ordered signup checklist with verified URLs). Encodes the verify-numbers-before-reuse rule (re-pull keyword figures fresh before planning), the hub-last build order, and the guest-facing vs internal linking boundary. Registered in the `/kai` router (PLAN) and the README strategy table.

## Unreleased — 2026-07-27

### New skill: `/kai-client-dashboard`

- Added `harness/skills/kai-client-dashboard/SKILL.md`: builds a white-labeled, client-facing intelligence dashboard for an agency's own clients — brand auto-extraction from the client's URL, a three-tier build (Basic/Standard/Advanced), an onboarding feature wizard, a 10-page inventory, a Deliverables page, and an Agent Registry page populated from real scheduled work
- Distinguished from existing dashboard surfaces rather than duplicating them: `/kai-data-dashboard` remains the data/spec layer this skill calls once sources are connected, and `scripts/build_dashboard.py` remains the operator's own internal ops dashboard, not a client deliverable
- Public-access guidance is provenance-gated: default public/no-login posture is scoped to aggregate metrics only, with an explicit split-access or obscured-and-gated pattern required before any PII-bearing page (Leads, Communications, deal data) ships, per `knowledge/checklists/privacy-sanitizer-checklist.md`
- SMS/prerecorded-voice engagement automation requires a logged consent and opt-out path per `harness/skills/kai-sdr-operator/references/compliance-matrix.md` before enrollment
- Added the manifest page (`docs/skill-manifest/kai-client-dashboard.md`), registered the skill in the `/kai` router and README command tables, cross-linked it from `kai-data-dashboard`, and refreshed skill-count references across `AGENTS.md`, `README.md`, `docs/skill-manifest/README.md`, and the router (55 skill directories, 53 canonical `kai-*` skills, 48 public `/kai` commands, 46 manifest pages)

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
