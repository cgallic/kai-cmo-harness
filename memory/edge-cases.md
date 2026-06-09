# Edge Cases & Gotchas Registry

Known sharp edges in the harness, platform APIs, and the learning loop. Each entry says where it bites, what to do, and whether anything enforces it. Entries with `enforcement: none` are graduation candidates — promote them to code checks via `/kai-retro` and add a golden case when you do.

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

### EC-06 Placeholder detection misses natural language
**Pre-ship placeholder scan → `_find_bracket_placeholders()` in `scripts/content/engine.py` only catches `[company]`-style tokens.** "Insert your company name here" ships. Scan for natural-language placeholders too.
Bites: every publish. Enforcement: partial (bracket regex only). Added: 2026-06-09

### EC-07 Four U's scorer needs GEMINI_API_KEY
**Running `four_us_score.py` → it calls Gemini and loads `/opt/cmo-analytics/.env` (a server path).** Without `GEMINI_API_KEY` in the environment it crashes rather than degrading. Banned-word check and SEO lint are fully offline — run them regardless.
Bites: fresh clones. Enforcement: scripts/doctor.py reports it. Added: 2026-06-09

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

### EC-11 MARKETING.md auto-rewrite has no validity check
**`harness_defaults_update.py` rewrites MARKETING.md and policy YAML → it backs up `.bak` but never validates the result parses.** A bad rewrite breaks every later run. Validate YAML before replacing; roll back on parse failure.
Bites: scheduled learning loop. Enforcement: none. Added: 2026-06-09

### EC-12 pending_checks are the only schedule record
**30-day checks → if `pending_checks/<id>.json` is lost, that piece is never re-measured.** `content_log.json` has enough to regenerate them; do so on startup if counts mismatch.
Bites: long-running deployments. Enforcement: none. Added: 2026-06-09

### EC-13 Circuit breaker resets on restart
**`pattern_extract.py` stops after 3 consecutive Gemini failures → the counter is in-memory only.** A crash-looping agent hammers the API forever. Persist breaker state if you see repeated restarts.
Bites: OpenClaw mode. Enforcement: in-process only. Added: 2026-06-09

### EC-14 Winners are analyzed, losers were not
**Learning loop → pattern extraction historically only read `grade == "winner"`.** Log losers to `memory/what-doesnt-work.md` so failed angles aren't retried. `/kai-retro` covers this.
Bites: pattern quality. Enforcement: /kai-retro workflow. Added: 2026-06-09

### EC-15 30-day window ignores seasonality and competitor moves
**Winner/loser grading → a piece judged in a seasonal trough or after a competitor launch gets a misleading grade.** Note context in the log entry; allow manual re-grade.
Bites: pattern extraction. Enforcement: none. Added: 2026-06-09

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
