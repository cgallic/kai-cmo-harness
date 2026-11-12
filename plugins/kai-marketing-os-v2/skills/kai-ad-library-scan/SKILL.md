---
name: kai-ad-library-scan
description: Find which ad patterns keep getting paid for in a category. Scans the Meta Ad Library (Apify or ScrapeCreators, under a spend cap), computes days running in code, has Jev tag each ad's hook, offer, angle, proof and format, drops off-category ads, measures advertiser-weighted 60+ day survival per tag, then scores LLM-written briefs against the surviving patterns and the brand file. Read-only. Use when "ad library", "competitor ads", "what ads are working in my category", "long-running ads", "winning ad patterns", "swipe file", "which hooks work", "score these ad briefs", or before writing a paid creative bench.
---

# /kai-ad-library-scan — What a Category Pays to Keep Running

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

The owner knows which hooks, offers, angles, proof types and formats survive 60+ days in their category (advertiser-weighted, trusted cells only), which ones die early, and which of their candidate briefs use the survivors while fitting the brand. They end with a survival report, a hand-checked tag set, a ranked brief list with a computed score and reasons per brief, and the exact spend.

Doctrine: `knowledge/playbooks/ad-library-survival-scan.md`. Output: `workspace/ad-library-scan/<category-slug>/<YYYY-MM-DD>/`.

## Done when

Work type `internal-research` (E2/C2/O0) for an internal scan; `audit-report` (E3/C4/O1) when delivered to a client as a competitor section, with every number citing the scan files. Briefs that ship are judged under `paid-ad-campaign` (`harness/eco-floors.yaml`).

- `RUN.md` states the category sentence, searches, countries, relevance regex, spend ceiling, and what each step dropped and charged.
- `report.md` and `patterns.json` come from `survival_report` at the default thresholds, with off-category ads removed.
- `handcheck.md` shows 20 random in-category ads checked label by label: at least 85% of confident labels right and no more than 2/20 off-category. Below that, the regex or category sentence is fixed and the ads re-tagged before the report is used.
- `ranked.md` comes from `score_briefs` with the brand file, includes at least one negative control, and every "check by hand" brief has been checked by a human. The top briefs pass `/kai-gate` (10/16 Four U's for ads).

## Constraints

- **Read-only.** Public ad archives only. No ad account is created, edited, paused or uploaded to. Production goes through `/kai-ad-campaign` and its approval gate, with the playbook's pre-flight yes/no checks run before upload.
- **Spend cap.** Every Apify run passes `--max-usd` (sent to Apify as `maxTotalChargeUsd`) and fits under `APIFY_MONTHLY_CAP_USD` in the fail-closed ledger (`python -m scripts.ads.ad_library.budget status`). The owner hears the ceiling before the first paid run. Imports via `--from-apify` / `--from-scrapecreators` cost nothing extra.
- **Counts in code, features from Jev.** Days running, advertiser weights, lifts and the 0–100 brief score come from `scripts/ads/ad_library/`. Jev answers only visible-feature questions through the harness client (`scripts/autonomy/decision_log.py`); unsure answers are excluded, never guessed. Never hand-estimate a lift.
- **Thresholds hold.** Survivor 60+ days, short = stopped under 21 days, active-and-younger-than-60 left out, trusted cell = 10+ ads from 3+ advertisers. Untrusted cells are reported as hypotheses and are not used to score unless the report says `--include-untrusted` was used and why.
- **Relevance before measurement.** Political ads dropped, `--require` regex applied, and `--category` passed to `tag_ads` so Jev's `in_category` removes keyword bleed before survival is measured.
- **Brand safety fails closed.** An unsure "uses something to avoid" answer earns no brand points and needs a human check.
- **No fabricated proof.** A surviving proof pattern (reviews, testimonials, experts, user counts) is used only with proof on record; otherwise it is a data gap.
- **Policy before copy.** `harness/references/meta-ads-rules.md` and `harness/references/advertising-compliance.md` are loaded before any brief is written.

## Context

- Collect: `python -m scripts.ads.ad_library.collect_ads --apify-run --search-terms "<term>" --countries US --max 500 --max-usd 0.50 --require "<regex>" --out <dir>/raw/<term>.jsonl`, or `--from-apify <export>` / `--from-scrapecreators <file>`, or `--meta-api` (EU-delivered commercial ads only, `META_ACCESS_TOKEN`).
- Tag: `python -m scripts.ads.ad_library.tag_ads --in <ads.jsonl> --out <tagged.jsonl> --category "<category sentence>"` (`OPENROUTER_API_KEY`; `--model` pinned, default `jev-1.14`; `--mock` offline).
- Survival: `python -m scripts.ads.ad_library.survival_report --in <tagged.jsonl> --report <report.md> --patterns <patterns.json>`.
- Score: `python -m scripts.ads.ad_library.score_briefs --briefs <briefs.jsonl> --patterns <patterns.json> --brand <brand.txt> --out <ranked.jsonl> --report <ranked.md>`. Briefs are JSONL `id, hook, body, format, offer`.
- Brand file: voice, audience, and words or claims to avoid, from `MARKETING.md` or the owner.
- Where the results go next: `knowledge/playbooks/combinatorial-creative-bench.md` (angle and format axes), `knowledge/playbooks/meta-creative-testing-decision-framework.md` (the test still decides), `knowledge/playbooks/ad-creative-best-practices.md` (copy).
- Worked example and failure modes (template ads, keyword bleed, political ads): the playbook.

## Escalate when

- The first paid run would exceed the remaining monthly cap, or the owner has not agreed a ceiling.
- No cell is trusted after a full collection: the category may be too thin for this method.
- The hand check stays below 85% agreement or above 2/20 off-category after one fix.
- The strongest surviving patterns need proof the brand does not have.
- A top brief carries a claim the platform policy reference flags (income, health, before/after, personal attributes).
