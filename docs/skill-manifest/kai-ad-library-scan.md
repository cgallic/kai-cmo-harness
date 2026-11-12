---
name: kai-ad-library-scan
version: 1.0.0
category: strategy
last_updated: 2026-11-12
---

# Kai Ad Library Scan

### One-line claim
Which ad patterns a category keeps paying for. Kai scans the Meta Ad Library under a spend cap, has Jev tag each ad's visible features, measures advertiser-weighted 60+ day survival per tag, and ranks new briefs against the survivors and the brand file.

### Triggers
- ad library / competitor ads
- what ads are working in my category
- long-running ads / winning ad patterns
- which hooks work
- score these ad briefs
- before writing a paid creative bench

### Inputs
- `category` (string, required): the sentence Jev judges relevance against.
- `search_terms` (list, required): 4-8 keyword searches, plus countries and a relevance regex.
- `max_usd` (number, required for paid runs): per-run Apify ceiling, under `APIFY_MONTHLY_CAP_USD`.
- `export` (file, optional): an Apify or ScrapeCreators export instead of a paid run.
- `brand` (text file, required to score briefs): voice, audience, words and claims to avoid.
- `briefs` (JSONL, optional): `id, hook, body, format, offer`.

### Outputs
- `workspace/ad-library-scan/<slug>/<date>/RUN.md`: searches, drops, spend.
- `tagged.jsonl`: one row per in-category ad with days running and gated Jev labels.
- `report.md` + `patterns.json`: survivor rate, lift, n and advertisers per tag; trusted cells marked.
- `handcheck.md`: 20-ad label agreement.
- `ranked.jsonl` + `ranked.md`: 0-100 brief scores computed in code, with reasons.

### Methodology
- [ad-library-survival-scan.md](../../knowledge/playbooks/ad-library-survival-scan.md)
- Survivor = ran 60+ days; short = stopped under 21 days; active ads younger than 60 days are left out.
- Each advertiser carries equal weight; a cell counts only with 10+ ads from 3+ advertisers.
- Jev answers visible-feature questions through the harness client (`scripts/autonomy/decision_log.py`); counts, lifts and scores are computed in code.

### Dependencies
- [kai-gate](./kai-gate.md) for the top briefs
- [kai-ad-campaign](./kai-ad-campaign.md) produces and uploads the approved briefs

### Called by
- The `/kai` router (ANALYZE table)

### Quality gates
- Fail-closed Apify spend ledger plus a per-run `maxTotalChargeUsd` ceiling.
- Hand check: 85%+ confident-label agreement and no more than 2/20 off-category before the report is used.
- Brand safety fails closed: an unsure "uses something to avoid" earns no brand points.
- ECO `internal-research`, or `audit-report` when delivered to a client.

### Failure modes
- Keyword bleed (novels, drama apps, campaign ads) skews lifts until `--category` removes it.
- Catalog ads carry `{{product.name}}` templates; the collector reads the card copy instead.
- Thin categories produce no trusted cells; collect more advertisers rather than lowering the floor.
- Surviving proof patterns need proof the brand may not have.

### Competitive claim
Run length is a profit signal every competitor publishes for free. Weighting advertisers equally and trusting only broad cells turns it into patterns, and the first run cost $1.32 for 1,428 ads with 95% tag agreement on a hand check.
