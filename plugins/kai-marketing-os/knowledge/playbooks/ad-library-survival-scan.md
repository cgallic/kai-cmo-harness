---
title: Ad Library Survival Scan + Jev Judgment
type: playbook
created: 2026-11-12
updated: 2026-11-12
---

# Ad Library Survival Scan + Jev Judgment

> **Use when:** you need to know which hooks, offers, angles, proof types and formats keep getting paid for in a category before writing paid creative, before filling a creative bench, or before a client audit's "what is working for your competitors" section. Skill: `/kai-ad-library-scan`. Code: `scripts/ads/ad_library/`.

## The method in one paragraph

Pull a category's ads from the Meta Ad Library. Compute how many days each ad ran, in code. Have Jev (TypeSafe's System One model) tag each ad on visible features: hook, offer, angle, proof and format. Drop ads that are not really in the category. Then measure, per tag, how often ads carrying it survived 60+ days, with every advertiser weighted equally. Tags that survive more often than the category average are the patterns to write in. An LLM writes briefs in those patterns, Jev checks each brief against them and against the brand file, code turns the answers into a 0–100 score, and only the top briefs get produced.

## Why survival works

**An advertiser does not keep paying for an ad that loses money.** Run length is therefore a proxy for profit that every competitor reveals for free. An ad still running after 60 days has been through many budget reviews and survived all of them. An ad stopped inside three weeks usually failed one.

Run length is the signal. Do not hedge it with "maybe they forgot to turn it off": spend is reviewed weekly, and a forgotten loser costs real money. The noise to manage is sample size and who is in the sample, which is what the thresholds below handle.

This tells you what the **category** rewards. It does not prove an ad will win on **your** account. Survivor patterns choose what enters the test; the test still decides (`knowledge/playbooks/meta-creative-testing-decision-framework.md`, `knowledge/playbooks/creative-test-resolution-protocol.md`).

## Buckets and thresholds

| Bucket | Rule | Used how |
|---|---|---|
| Survivor | ran **60+ days** (still active or stopped) | numerator |
| Short | **stopped** before day 21 | denominator only |
| Undecided | everything else, including **active ads younger than 60 days** | left out: their outcome is not known yet |

- **Survivor rate** = survivors / (survivors + short).
- **Advertiser-weighted.** Each advertiser carries equal total weight, split across its decided ads. One advertiser with 300 ads counts the same as one with 3, so a big spender's catalog cannot set the category's answer.
- **Lift** = a tag's weighted survivor rate / the overall weighted survivor rate. Above 1.0 survives more often than average.
- **Trust floor.** A cell (one tag value) counts only with **n ≥ 10 ads from ≥ 3 advertisers**. Below that it is a hypothesis and is not used to score briefs (`--include-untrusted` exists for tiny categories; say so in the report when you use it).
- Unsure Jev answers are left out of every cell, never guessed.

## Jev question rules

Jev answers typed questions: a choice with a probability per option, a yes/no probability, or a score on a fixed rubric. It never writes prose. The harness client is `scripts/autonomy/decision_log.py` (`ask_jev`, pinned models `jev-1.14` default, `jev-1.13`, Laya checkpoints; `OPENROUTER_API_KEY`). The ad scripts call it through `scripts/ads/ad_library/jev.py`; there is no second client.

1. **Ask about visible features, not judgments.** "Does the first sentence contain a number?" not "Is the hook strong?". That wording change moved one labeling test from 34–43% wrong to 97–99% right.
2. **Counts, dates, weights and scores are computed in code.** Jev never counts days, never scores a brief, never decides a threshold.
3. **Pair every choice question with a yes/no "does any listed option fit?".** A choice always returns one of its options, so without the companion an ad with no hook type gets one anyway. When the companion gates to "no", the label becomes `other`.
4. **Gate every answer.** The harness gate keeps a choice at confidence ≥ 0.60 with a lead ≥ 0.20 over the runner-up, and reads a yes/no as yes at p ≥ 0.70 and no at p ≤ 0.30. Everything else is `unsure`.
5. **Pin the model version** and re-check thresholds against a small hand-labeled sample whenever it changes.
6. **Brand safety fails closed.** If Jev is unsure whether a brief uses something the brand file says to avoid, the brief gets no brand points and the report says to check it by hand.

### What gets tagged

| Question | Type | Options |
|---|---|---|
| `hook_type` (+ companion) | choice | question, bold_claim_number, pain_callout, us_vs_them, testimonial_quote, offer_first, curiosity, news |
| `offer_type` (+ companion) | choice | discount_pct, free_trial, free_shipping, bundle, guarantee, lead_magnet, no_offer |
| `angle` (+ companion) | choice | problem_solution, transformation, social_proof, authority, comparison, founder_story, ugc_style |
| `proof_type` | choice | review, number_stat, before_after, expert, press, none |
| `price_shown`, `number_in_first_line`, `names_competitor_or_old_way`, `urgency_deadline`, `addresses_reader_as_you_in_first_line` | yes/no | — |
| `in_category` (with `--category`) | yes/no | "Is this ad selling a product, service or program for {category}? Answer no if the keyword only appears in passing, in a story, or in a list of unrelated categories." |
| `display_format` | code | video, image, carousel, dco (from the archive record) |

## Brief scoring

Briefs are JSONL rows (`id, hook, body, format, offer`), written by an LLM in the trusted surviving patterns and loaded with the brand file. Jev answers one yes/no per trusted pattern ("Is this true of the ad: it quotes a customer or reviewer?") plus three brand questions (fit 0–3, speaks to the brand's audience, uses something to avoid). Format is matched in code.

- **Pattern points (70, or 100 without a brand file):** per question, the brief earns the lift above 1.0 of the best value it matches, scaled between the worst and best possible brief under these patterns.
- **Brand points (30):** fit 0–3 → up to 20, audience → 10. Any "uses something to avoid" or unsure answer → 0 brand points.

Only the top briefs get produced. Before any of them is uploaded, run the pre-flight checks below; the upload itself goes through `/kai-ad-campaign` and its approval gate.

### Pre-flight checks before upload

Jev yes/no on the finished ad, answered on visible features:

- Does the first line match the hook the brief named?
- Is the product named in the first line?
- Does the ad make an income, earnings or health claim? (Meta's most common rejection on finance and earning apps; see `harness/references/meta-ads-rules.md`.)
- Does the button match the offer?

A "yes" on the claim question or a "no" on the others sends the ad back to the writer. These checks support the policy pass; they do not replace loading the platform policy reference before writing.

## Cost math

| Item | Price | Notes |
|---|---|---|
| Apify `curious_coder/facebook-ads-library-scraper` | **$0.75 per 1,000 ads** + $0.00005 per run start | list price checked 2026-11-12; settled runs came in about 10% under list |
| ScrapeCreators Facebook Ad Library | per-request pricing | file import only (`--from-scrapecreators`) |
| Meta Graph API `ads_archive` | free, rate limited | commercial ads only when delivered to the EU; needs Ad Library API access |
| Jev via OpenRouter | vendor figure $0.042 per million input tokens | measured: 957 ads cost $0.066 (`usage.cost`), about **$0.00007 per ad** |

A 5,000-ad scan costs about $3.75 in Apify at list and about $0.35 in Jev. Every Apify run takes a reservation under a fail-closed monthly cap (`APIFY_MONTHLY_CAP_USD`, ledger in `scripts/ads/ad_library/budget.py`), and the per-run ceiling (`--max-usd`) is passed to Apify as `maxTotalChargeUsd`, so Apify itself stops charging there. The ledger settles each run with Apify's reported `usageTotalUsd`; the tag and score scripts print the summed OpenRouter `usage.cost`, not an estimate, when it is present.

## Worked example: youth baseball training, 2026-11-12

First real run, for a physical deck of baseball learning cards. Category: youth baseball and softball training products, US, active and inactive ads.

| Step | Result |
|---|---|
| Collect | 8 keyword searches (baseball training, youth baseball, baseball IQ, baseball coaching, training aid, hitting drills, softball training, swing trainer). 1,571 items, **1,428 unique ads**. |
| Filter | 209 political/issue ads dropped, 262 dropped by the category regex, **307 judged off-category by Jev**. Kept **650 ads from 240 advertisers**. |
| Survival | 289 survivors, 139 short, 222 undecided. Survivor rate **75% advertiser-weighted** (68% unweighted) over 428 decided ads from 157 advertisers. 36 trusted cells. |
| Spend | Apify **$1.11** + Jev **$0.21** (four tagging passes, four scoring passes, one probe) = **$1.32** against a $3 cap. |
| Hand check | 20 random in-category ads × 9 labels: **156/164 confident labels right (95%)**, 9% unsure, in-category call right on 19/20. |

Trusted survivor patterns: social-proof angle 1.33x (29 ads, 14 advertisers), UGC-style angle 1.33x (12, 6), testimonial-quote hook 1.33x (10, 4), carousel 1.24x (51, 24), news hook 1.17x (59, 28). Losers: bundle offers 0.52x (35 ads), urgency/deadline 0.61x (53), curiosity hooks 0.62x (13), naming a competitor or the old way 0.65x (70), DCO 0.77x (42), problem/solution angle 0.81x (168).

How to read it: the three 1.33x cells hit a 100% survivor rate on narrow advertiser counts, so carousel and news hooks are the patterns with real breadth. Social proof and testimonials are patterns the brand **could not use honestly yet**, because it had no verified reviews; collecting real ones was the unlock. Never fabricate the proof a pattern needs.

Ten briefs were scored, two of them deliberate negative controls (a fake UGC testimonial and a curiosity tease with scarcity). The top three were a news-hook carousel (84), a game-situation question carousel with expert proof (82) and a news-hook image (80). The fake-UGC control scored 53 and the curiosity control 30. A brief leading with a pro player's credential scored 49 because Jev was unsure whether it broke the brand file's no-endorsement rule, and the gate failed closed.

## Failure modes found on the first run

| Failure | What happened | Fix in the code |
|---|---|---|
| **Keyword bleed** | A "youth baseball" search returned web novels, short-drama apps and campaign ads. In an early pass 8 of 20 sampled ads were not baseball at all. Without the fix `ugc_style` read 0.38x (worst pattern) because novels were tagged UGC; on the real category it is 1.33x. | `--require REGEX` cuts obvious misses before paying to tag; `--category` asks Jev `in_category`; the report drops "no". Relevance mattered more than label accuracy. |
| **Political/issue ads** | Their run length tracks an election, not a sale. 209 of 1,428. | Dropped by default from Meta's `categories` (`--keep-political` to keep). |
| **Template ads** | Catalog ads carry `{{product.name}}` or `[categoryOne1]` in the top-level snapshot; 137 of 855 in one pass. | Placeholder text is skipped in favour of the first real card copy. |
| **Uncapped scraper run** | The sync endpoint gave up at 300 s with no Apify-side charge cap and an unsettled reservation. | Async run + poll, `maxTotalChargeUsd`, settled with `usageTotalUsd`. |
| **Brand gate failing open** | An unsure "uses something to avoid" counted as clean. | Unsure → 0 brand points + "check by hand". |
| **Label errors** | Concentrated in `offer_type`/`proof_type` (a discount or stat read into copy that has none) and `urgency_deadline` (event dates read as deadlines). | Hand-check 20 ads per run; treat those cells with care. |
| **Graph API quirks** | `ads_archive` returns commercial ads only when delivered to the EU, has no CTA or format field, and its snapshot URL embeds the access token. | EU default countries; snapshot URL never stored; token scrubbed from errors. |

## Where it plugs in

- **Creative bench.** Trusted survivor patterns are evidence for the Angle and Format axes in `knowledge/playbooks/combinatorial-creative-bench.md`; record them in the creative intelligence ledger. Losers become kill-before-launch rules.
- **Testing.** Survivor briefs still enter a real test with a control and a data floor (`knowledge/playbooks/meta-creative-testing-decision-framework.md`).
- **Copy rules.** Write the briefs with `knowledge/playbooks/ad-creative-best-practices.md` and the platform policy reference loaded first (`harness/references/meta-ads-rules.md`).
- **Audits.** A competitor section built from a scan cites the scan's files as its source (`harness/references/audit-data-provenance.md`); counts are the scan's, not estimates.

## Jev beyond ads: SEO, rating and judgment

The same pattern (an LLM writes, Jev judges and filters on a closed checklist, code decides) applies wherever the rubric is yes/no or a fixed choice. Jev loses to an LLM on open rubrics and long text (SummEval 0.72 vs 0.47, vendor figure), so keep reasons and coaching with the LLM. The broader Jev playbook (project files, growth/jev-ryze-eval/PLAYBOOK.md, v2 2026-11-12) lists these uses; costs are vendor figures until our own runs confirm them:

- **Internal links.** Yes/no "is there an honest reason to link A to B?", asked only over candidates an embedding shortlist proposed (one run: 586 pages, 584 links, $0.21).
- **Cannibalization.** Yes/no "do these two URLs answer the same search intent?", then merge or redirect through `/kai-page-refresh`.
- **Prune / keep.** A score for "says something other pages do not", then a choice of keep, update, merge or prune.
- **Keyword intent labels.** A choice of buyer, researcher, job seeker, competitor or junk over keyword lists and search-terms reports; only buyer-intent terms enter content plans, and terms that converted in the last 90 days are never negated.
- **GEO answer checks.** Over collected AI answers: is the brand recommended, which competitor is, what source type is cited, is there a coverage gap.
- **Closed-rubric judging.** Call grading checklist items, 20 yes/no content QA checks per draft, review-theme choice for review mining, and swapping LLM-as-judge for Jev wherever the rubric is closed.

These are not part of `/kai-ad-library-scan`; that skill stays scoped to the ad scan.
