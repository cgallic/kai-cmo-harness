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

## Phase 1: Wire Harness Through Quality Scorer
**Replace the 3 separate gate scripts with the unified quality scorer.**

- [ ] Refactor `run_gate()` in `scripts/harness_cli.py` to call `scripts.quality.gate.propose()` instead of `four_us_score.py` + `banned_word_check.py` + `seo_lint.py`
- [ ] Map harness format types to gate policies (blog→blog-publish, linkedin→linkedin-article, email→cold-email)
- [ ] Wire `revise_draft()` to use quality scorer violations as fix instructions (line numbers, exact suggestions)
- [ ] Update `post_for_approval()` to read gate proposal status
- [ ] Add policies: `press-release.yaml`, `tiktok-script.yaml`, `meta-ad.yaml`, `google-ad.yaml`
- [ ] Test end-to-end: `kai-harness run --task blog --site kaicalls --keyword "test"`

## Phase 2: Gate → Remote Zehrava Handoff
**Approved content auto-proposes to Zehrava Gate for delivery.**

- [ ] On local gate approve (or human approves pending): call `gate_client.propose(policy="blog-publish", destination="blog.publish", payload=draft)`
- [ ] Two gates in series: quality gate (instant, local) → action gate (remote, with delivery)
- [ ] Add `--deliver` flag: `python -m scripts.quality gate article.md --policy blog --deliver`
- [ ] Wire Discord notification for pending proposals (post to channel with approve/reject reactions)

## Phase 3: Self-Improvement Loop
**Quality scores feed back into the system automatically.**

- [ ] Wire `performance_check.py` to run quality scorer on published content retroactively
- [ ] Correlate quality scores with GSC/GA4 performance (position, CTR, session duration)
- [ ] `pattern_extract.py` extracts which quality rules correlate with winners
- [ ] Auto-update policy thresholds when n>=5 winner patterns emerge
- [ ] Cron: nightly batch score of all published content → trend in `content_log.json`
- [ ] Weekly: surface "your avg score improved from 72→79 this week" to Discord

## Phase 4: Architecture Page Rewrite
**meetkai.xyz/architecture should reflect harness engineering approach.**

- [ ] Reframe as "harness engineering for marketing" (parallel to OpenAI Codex approach)
- [ ] Show 4-layer stack: Runtime → Tooling → Domain Agents → Content Harness
- [ ] Feature quality scorer as the core moat (research-as-automated-tooling)
- [ ] Show feedback loop diagram: write → score → gate → publish → 30d check → pattern extract → update defaults
- [ ] Add 14 marketing skills to /skills page (currently showing only infra/dev skills)
- [ ] Add live quality scorer demo: paste content → get scored

## Phase 5: Open Source Prep
**Quality scorer as standalone pip package.**

- [ ] Extract `scripts/quality/` into standalone package (no dependency on knowledge_cloner)
- [ ] `pyproject.toml` with optional `[llm]` extra for Four U's
- [ ] PyPI: `pip install kai-quality` or `pip install content-quality-scorer`
- [ ] GitHub Actions CI: run tests on PR
- [ ] Contributing guide: how to add new rules
- [ ] Pre-built rule packs: `--pack aeo`, `--pack conversion`, `--pack technical`
