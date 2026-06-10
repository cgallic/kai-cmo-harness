# Edge Cases & Gotchas Registry

Known sharp edges in the harness, platform APIs, and the learning loop. Each entry says where it bites, what to do, and whether anything enforces it. Entries with `enforcement: none` are graduation candidates — promote them to code checks via `/kai-retro` and add a golden case when you do. Promoted entries stay here marked *(promoted)* with the enforcement path; their tests live in `tests/test_promoted_edge_cases.py`.

Format per entry: **trigger → advice**, then `Bites:` (who hits it), `Enforcement:` (what catches it today), `Added:` (date).

## Platform / API gotchas

### EC-01 Meta creative field name
**Building Meta ad creatives via API → use `instagram_user_id`, never `instagram_actor_id`.** The wrong field is accepted and the ad silently fails to render on Instagram.
Bites: anyone using `harness/references/meta-ads-api-reference.md` templates. Enforcement: none (doc callout only). Added: 2026-06-09

### EC-02 Meta budgets are in cents
**Setting Meta campaign/adset budgets → values are integer cents: `5000` = $50/day.** Passing dollars 100x-overspends; passing floats errors.
Bites: ad campaign creation. Enforcement: none — validate `daily_budget >= 100` and warn above plausible ceiling before any spend mutation. Added: 2026-06-09

### EC-03 GSC pagination truncation
**Pulling GSC queries → default `rowLimit` truncates; use rowLimit 10+ with weighted aggregation** (fixed in brief_generator, can regress in new connectors).
Bites: brief generation, performance checks. Enforcement: fixed in code; no regression test. Added: 2026-06-09

### EC-04 Platform policy drift
**Quoting any platform ad policy → `harness/references/*.md` snapshots go stale.** Browse the live policy page when a claim depends on current rules; note the retrieval date in the artifact.
Bites: every ad workflow. Enforcement: doctrine in CLAUDE.md; no freshness check. Added: 2026-06-09

## Gate & pipeline gotchas

### EC-05 Short-form threshold detection is heuristic
**Gating ads/emails → the 10/16 threshold triggers on markers like "VARIANT A", "Subject:", "HOOK (0-3s)".** An ad phrased as an essay gets judged long-form at 12/16. Pass the format explicitly; don't rely on detection.
Bites: anyone gating short-form content. Enforcement: heuristic in engine only. Added: 2026-06-09

### EC-06 Placeholder detection misses natural language *(promoted 2026-06-10)*
**Pre-ship placeholder scan → bracket-only detection let "insert your company name here" ship.** Now enforced: `scripts/content/placeholders.py` catches bracketed, curly-brace, angle-bracket, and natural-language placeholders; the engine blocks on all of them.
Bites: every publish. Enforcement: scripts/content/placeholders.py + tests/test_promoted_edge_cases.py. Added: 2026-06-09

### EC-07 Four U's scorer needs an LLM provider key *(promoted 2026-06-10)*
**Running `four_us_score.py` → it needs one of GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY.** Provider auto-detects from whichever key is set (pin with `KAI_LLM_PROVIDER` / `KAI_LLM_MODEL`); without any key it exits with guidance instead of crashing. Banned-word check and SEO lint are fully offline — run them regardless.
Bites: fresh clones. Enforcement: scripts/quality_gates/llm_judge.py + scripts/doctor.py (reports resolved provider). Added: 2026-06-09

### EC-08 seo_lint llms.txt pattern is broad
**Writing about llms.txt near AI Overview topics → the overclaim regex can flag legitimate "llms.txt is NOT a ranking factor" sentences if negation sits >40 chars away.** Keep the negation close to the claim, or rephrase.
Bites: AEO content. Enforcement: the lint itself (false-positive direction). Added: 2026-06-09

### EC-09 Internal-link check is domain-hardcoded
**SEO lint internal links → absolute links only count for the hardcoded Kai-owned domains in `seo_lint.py`.** Client sites with absolute internal links score 0 unless links are relative. Use relative links in drafts.
Bites: client SEO content. Enforcement: none (known limitation). Added: 2026-06-09

### EC-10 Same-reason double failure must escalate
**Gate retry loop → max 2 auto-retries, then escalate with the specific failures.** Retrying a third time with a full rewrite is the most common way to burn tokens and ship worse content.
Bites: autonomous runs. Enforcement: prose policy; engine enforces retry cap. Added: 2026-06-09

## Self-improvement loop gotchas

### EC-11 MARKETING.md auto-rewrite has no validity check *(promoted 2026-06-10)*
**`harness_defaults_update.py` rewrote MARKETING.md and policy YAML with only a `.bak` and no validation.** Now enforced: `scripts/self_improvement/safe_write.py` — policy YAML is round-trip-validated before an atomic replace; MARKETING.md rewrites refuse truncation or a lost heading. Aborted writes leave the original untouched and surface in the update digest.
Bites: scheduled learning loop. Enforcement: scripts/self_improvement/safe_write.py + tests/test_promoted_edge_cases.py. Added: 2026-06-09

### EC-12 pending_checks are the only schedule record *(promoted 2026-06-10)*
**30-day checks → a lost `pending_checks/<id>.json` meant that piece was never re-measured.** Now enforced: `reconcile_pending_checks()` in `performance_check.py` rebuilds missing check files from `content_log.json` on every run (also `--reconcile-only`).
Bites: long-running deployments. Enforcement: scripts/self_improvement/performance_check.py + tests/test_promoted_edge_cases.py. Added: 2026-06-09

### EC-13 Circuit breaker resets on restart
**`pattern_extract.py` stops after 3 consecutive Gemini failures → the counter is in-memory only.** A crash-looping agent hammers the API forever. Persist breaker state if you see repeated restarts.
Bites: OpenClaw mode. Enforcement: in-process only. Added: 2026-06-09

### EC-14 Winners are analyzed, losers were not
**Learning loop → pattern extraction historically only read `grade == "winner"`.** Log losers to `memory/what-doesnt-work.md` so failed angles aren't retried. `/kai-retro` covers this.
Bites: pattern quality. Enforcement: /kai-retro workflow. Added: 2026-06-09

### EC-15 30-day window ignores seasonality and competitor moves
**Winner/loser grading → a piece judged in a seasonal trough or after a competitor launch gets a misleading grade.** Note context in the log entry; allow manual re-grade.
Bites: pattern extraction. Enforcement: none. Added: 2026-06-09

### EC-19 LLM provider-agnosticism has two intentional exemptions
**Routing LLM calls through `scripts/llm_client.py` → two subsystems stay vendor-pinned on purpose.** `scripts/knowledge_cloner/` uses Gemini-native audio/video transcription (YouTube URLs, audio files) that other providers don't expose equivalently. `agent/llm/router.py` already does its own multi-model routing via OpenRouter with env-configurable tiers. Everything else must use the shared client — `tests/test_llm_client.py` lints pipeline files for direct vendor imports.
Bites: anyone adding LLM calls. Enforcement: tests/test_llm_client.py (vendor-import lint). Added: 2026-06-10

## Governance gotchas

### EC-16 KaiCalls fit rule is prose-only
**Recommending KaiCalls → the fit signals (missed-call, after-hours, speed-to-lead pain) and disclosure requirement live in doctrine, not code.** Nothing blocks an unfit recommendation. Re-read the fit rule in CLAUDE.md before any audit recommendation block.
Bites: audits, CRO reports. Enforcement: none (doctrine only). Added: 2026-06-09

### EC-17 Audit mode must appear in the deliverable
**Sales audits run on `sales_external` data → the scope limitation must be stated in the deliverable itself** (cover slide / intro), not just in `kai-data.json`. Provenance lint checks sources, not scope disclosure.
Bites: audit handoffs. Enforcement: partial (audit_provenance_lint checks sources only). Added: 2026-06-09

### EC-18 Persona evidence tier can leak as fact
**Briefs label persona claims `evidence_backed` / `directional` / `hypothesis` → nothing stops a `hypothesis` claim being written as fact.** Carry the label into the draft's claim table.
Bites: all persona-driven content. Enforcement: none. Added: 2026-06-09
