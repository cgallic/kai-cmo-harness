---
name: kai-ad-library-scan
description: Find which ad patterns keep getting paid for in a category. Scans the Meta Ad Library (Apify or ScrapeCreators, under a spend cap), computes days running in code, has Jev tag each ad's hook, offer, angle, proof and format, drops off-category ads, measures advertiser-weighted 60+ day survival per tag, then scores LLM-written briefs against the surviving patterns and the brand file. Read-only. Use when "ad library", "competitor ads", "what ads are working in my category", "long-running ads", "winning ad patterns", "swipe file", "which hooks work", "score these ad briefs", or before writing a paid creative bench.
---

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

Learn what a category pays to keep running, then write and rank briefs in those patterns. Doctrine: `knowledge/playbooks/ad-library-survival-scan.md`. Output: `workspace/ad-library-scan/<category-slug>/<YYYY-MM-DD>/`.

## Non-Negotiable Rules

- **Read-only.** This skill reads public ad archives. It never creates, edits, pauses or uploads anything in an ad account. Briefs that get produced ship through `/kai-ad-campaign` and its approval gate.
- **Spend cap first.** Every Apify run needs `--max-usd` (the per-run ceiling, passed to Apify as `maxTotalChargeUsd`) and must fit under `APIFY_MONTHLY_CAP_USD` (fail-closed ledger: `python -m scripts.ads.ad_library.budget status`). State the ceiling to the owner before the first paid run. List price is about $0.75 per 1,000 ads.
- **Counts in code, features from Jev.** Days running, weights, lifts and brief scores come from the scripts. Jev only answers questions about visible features. Never hand-estimate a lift or a survivor rate.
- **No fabricated proof.** A surviving pattern that needs proof (reviews, testimonials, expert quotes, user counts) is usable only with proof that exists on record. If the brand has none, say so and log it as a data gap.
- **Policy before copy.** Load `harness/references/meta-ads-rules.md` (and `harness/references/advertising-compliance.md`) before any brief is written.

## Phase 1 — Define the category

Write `workspace/ad-library-scan/<slug>/<date>/RUN.md` with: the category sentence Jev will judge relevance against (e.g. "youth baseball or softball players, parents or coaches"), 4-8 keyword searches, countries, a relevance regex, and the spend ceiling. Get the brand file (`brand.txt`: voice, audience, words and claims to avoid) from `MARKETING.md` or the owner.

## Phase 2 — Collect

```bash
python -m scripts.ads.ad_library.collect_ads --apify-run --search-terms "<term>" --countries US --max 500 \
    --max-usd 0.50 --require "<regex>" --out workspace/ad-library-scan/<slug>/<date>/raw/<term>.jsonl
# or import an export instead of paying for a run:
python -m scripts.ads.ad_library.collect_ads --from-apify export.json --out .../raw/ads.jsonl
python -m scripts.ads.ad_library.collect_ads --from-scrapecreators sc.json --out .../raw/ads.jsonl
```

Political/issue ads are dropped by default. Merge the per-term files into one `ads.jsonl`; `tag_ads` drops duplicate ad ids. Record items returned, unique ads, political and regex drops, and the charged amount in RUN.md.

## Phase 3 — Tag

```bash
OPENROUTER_API_KEY=... python -m scripts.ads.ad_library.tag_ads --in .../ads.jsonl --out .../tagged.jsonl \
    --category "<category sentence>"
```

Model `jev-1.14` unless `--model` says otherwise (pinned versions only). Check the printed error count and charged cost.

## Phase 4 — Survival report

```bash
python -m scripts.ads.ad_library.survival_report --in .../tagged.jsonl --report .../report.md --patterns .../patterns.json
```

Defaults: survivor 60+ days, short = stopped under 21 days, trusted cell = 10+ ads from 3+ advertisers, advertiser-weighted. Do not lower the trust floor to manufacture patterns; if no cell is trusted, collect more ads or advertisers.

## Phase 5 — Hand check

Read 20 random in-category tagged ads against their text, all 9 labels each, and write `handcheck.md`: agreement on confident labels, share unsure, in-category calls right. Below 85% agreement or more than 2/20 off-category, fix the regex or category sentence and re-tag before using the report.

## Phase 6 — Briefs and scores

Write 6-12 briefs as JSONL (`id, hook, body, format, offer`) in the trusted surviving patterns, plus at least one deliberate negative control. Then:

```bash
OPENROUTER_API_KEY=... python -m scripts.ads.ad_library.score_briefs --briefs .../briefs.jsonl --patterns .../patterns.json \
    --brand .../brand.txt --out .../ranked.jsonl --report .../ranked.md
```

Any brief marked "check by hand" is checked by a human before it can rank. Run `/kai-gate` on the top briefs (10/16 Four U's for ads). Only the top 3 go forward, to `/kai-ad-campaign`, with the pre-flight yes/no checks from the playbook run before upload.

## Report

```
## Ad Library scan: [category], [date]
Collected: [N] unique ads, [political] political, [regex] off-regex, [jev] off-category → [kept] ads, [advertisers] advertisers
Survival: [survivors] / [short] / [undecided]; survivor rate [weighted]% advertiser-weighted ([unweighted]% unweighted); [trusted] trusted cells
Top patterns: [tag = value: lift, n ads, advertisers] ...
Losers: [tag = value: lift, n] ...
Hand check: [x]/[y] confident labels right, [u]% unsure, in-category [k]/20
Briefs: [rank. id score] ... (controls: ...)
Spend: Apify $[charged] + Jev $[charged] = $[total] against a $[cap] ceiling
Data gaps: [proof the patterns need but the brand lacks, ...]
```

ECO: an internal scan is work type `internal-research`; delivered to a client as a competitor section it is `audit-report` and every number cites the scan files. Briefs that ship are judged under `paid-ad-campaign` in `harness/eco-floors.yaml`.
