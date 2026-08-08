# Kai CMO Harness — What's Next

## Done (Mar 16, 2026)
- [x] Built Content Quality Scorer (28 rules, 4 categories, 3 output formats)
- [x] Built Local Gate (YAML policies, SQLite audit trail, approve/reject/hold)
- [x] Deployed quality scorer to Kai-CMO server (`/opt/cmo-analytics/quality/`)
- [x] Deployed 14 marketing skills to OpenClaw (129 → 143 total)
- [x] Synced 7 missing framework files to server knowledge base
- [x] Gateway integration (`POST /webhooks/quality/score`)
- [x] 4 gate policies: blog-publish, linkedin-article, cold-email, default

---

## Phase 1: Wire Harness Through Quality Scorer ✅
**Replace the 3 separate gate scripts with the unified quality scorer.**

- [x] Refactor `run_gate()` in `scripts/harness_cli.py` to call `scripts.quality.gate.propose()` instead of `four_us_score.py` + `banned_word_check.py` + `seo_lint.py`
- [x] Map harness format types to gate policies (blog→blog-publish, linkedin→linkedin-article, email→cold-email, press→press-release, tiktok→tiktok-script, meta-ads→meta-ad, google-ads→google-ad)
- [x] Wire `revise_draft()` to use quality scorer violations as fix instructions (rule IDs, line numbers, exact suggestions)
- [x] Update `post_for_approval()` to include proposal_id + score + grade + approve command
- [x] Add policies: `press-release.yaml`, `tiktok-script.yaml`, `meta-ad.yaml`, `google-ad.yaml`
- [ ] Test end-to-end: `kai-harness run --task blog --site kaicalls --keyword "test"`

## Phase 2: Gate → Remote Zehrava Handoff
**Approved content auto-proposes to Zehrava Gate for delivery.**

- [ ] On local gate approve (or human approves pending): call `gate_client.propose(policy="blog-publish", destination="blog.publish", payload=draft)`
- [ ] Two gates in series: quality gate (instant, local) → action gate (remote, with delivery)
- [ ] Add `--deliver` flag: `python -m scripts.quality gate article.md --policy blog --deliver`
- [ ] Wire Discord notification for pending proposals (post to channel with approve/reject reactions)

## Phase 3: Self-Improvement Loop ✅
**Quality scores feed back into the system automatically.**

- [x] Wire `performance_check.py` to run quality scorer on published content retroactively (`retro_score_content()`)
- [x] Correlate quality scores with GSC/GA4 performance (position, CTR, session duration)
- [x] `pattern_extract.py` extracts which quality rules correlate with winners (`--correlate` flag)
- [x] Auto-update policy YAML thresholds when n>=5 winner patterns emerge (`harness_defaults_update.py`)
- [x] Cron: nightly batch score of all published content → `--batch-score` flag
- [x] Weekly: surface quality summary to Discord → `--weekly-summary` flag

## Phase 4: Architecture Page Rewrite ✅
**meetkai.xyz/architecture should reflect harness engineering approach.**

- [x] Reframe as "harness engineering for marketing" (parallel to OpenAI Codex approach)
- [x] Show 4-layer stack: Runtime → Tooling → Domain Agents → Content Harness
- [x] Feature quality scorer as the core moat (research-as-automated-tooling)
- [x] Show feedback loop diagram: write → score → gate → publish → 30d check → pattern extract → update defaults
- [x] 14 marketing skills grid
- [x] Live quality scorer demo wired to POST /webhooks/quality/score

## Phase 4.5: Code Hardening ✅
**Address competitive review findings — production-grade code quality.**

- [x] Centralized config: `scripts/harness_config.py` + `config.yaml` — all hardcoded paths, IDs, thresholds extracted
- [x] API timeouts: 30s timeout on all Gemini API calls (configurable via `api_timeout`)
- [x] Circuit breaker: fail after 3 consecutive API errors (configurable via `api_max_retries`)
- [x] Input sanitization: `sanitize_input()` strips control chars, truncates, escapes prompt-injection patterns
- [x] Replace `os.system()` with `subprocess.run()` — proper error handling, timeouts, return code checks
- [x] MARKETING.md backup: `.bak` created before every auto-update (policy YAML files too)
- [x] Fix GSC pagination: `rowLimit: 1` → `10` with weighted aggregation across rows
- [x] Fix duplicate `SHORT_FORM` definition in harness_cli.py
- [x] Remove hardcoded Discord channel fallback — now from `config.yaml`
- [x] LRU cache for quality scoring — identical content not scored twice
- [x] Structured JSON logging across all scripts (`logging` module, not bare `print()`)
- [x] Test suite: gate module tests (test_gate.py) added to existing AA/GEO/CS/engine/parser tests

## Phase 5: Open Source Prep
**Quality scorer as standalone pip package.**

- [ ] Extract `scripts/quality/` into standalone package (no dependency on knowledge_cloner)
- [ ] `pyproject.toml` with optional `[llm]` extra for Four U's
- [ ] PyPI: `pip install kai-quality` or `pip install content-quality-scorer`
- [ ] GitHub Actions CI: run tests on PR
- [ ] Contributing guide: how to add new rules
- [ ] Pre-built rule packs: `--pack aeo`, `--pack conversion`, `--pack technical`
