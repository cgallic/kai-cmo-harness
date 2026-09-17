---
name: kai-local-audit
version: 1.0.0
category: measurement
last_updated: 2026-09-17
---

# Kai Local Audit

### One-line claim
Audit a third-party local business the way its customers meet it — located rankings, map packs, AI-assistant answers, reviews, listings, backlinks, site crawl and real-browser checks — and deliver priced offers, an exact change list and a 12-week plan, optionally localized and bilingual.

### Triggers
- audit this business
- full marketing audit of a local business
- prospect audit
- local business audit
- use DataForSEO for the hard SEO data
- rerun it for local <market>
- also in Spanish
- give me the offers, changes and 3 month plan

### Inputs
- `request` (string, required) - natural-language task that triggered this skill.
- `audit_mode` (enum, required) - `sales_external`, `onboarding_connected`, or `internal_demo`.
- `target_url` (URL, required) - the business's website, Google Maps listing, or `share.google` link.
- `config` (file, required) - `workspace/local-audit/<slug>/config.json` built from `examples/local-audit-config.example.json`: vantage towns, market location codes, keywords by intent and language, Maps queries, review targets, competitor domains, AI prompts.
- `languages` (list, optional) - market languages for located pulls and a translated report.
- `source_evidence` (files or URLs, optional) - exports, screenshots, or client-provided data.

### Outputs
- Artifact -> `workspace/local-audit/<slug>/` with `audit-data.json`, `kai-data.json`, `_data-sources.md`, `_data-gaps.md`, `raw/` (API responses, direct-check artifacts, screenshots, shipping quotes), `local-audit/` (per-pull summaries), `report.html`, and `<lang>/report.html` when translated.
- Quality report -> provenance lint result, banned-word result, rendered-page checks at 390 px and 1280 px.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `gates`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md) and the located-data method in [local-audit-playbook.md](../../harness/references/local-audit-playbook.md).

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-005** - "Run `python -m scripts.audit.collect --url <url> --mode <mode> --workflow <workflow> --out <data-folder>` before using numbers in data-backed workflows." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-008** - "Missing credentials or unavailable sources must produce `_data-gaps.md` entries. Do not replace missing sources with estimates or placeholder metrics." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-010** - "Run `python scripts/quality_gates/audit_provenance_lint.py <audit-folder> --audit-dir` before audit or deck handoff." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- Located pulls: `python -m scripts.local_audit.pulls` (volumes, discover, serp, maps, listings, reviews, backlinks, ai, lighthouse, crawl) and `python -m scripts.local_audit.checks` (access, assets, dns, shopify). Share of estimated clicks is modeled and labeled as such.

### Dependencies
- [kai-audit](./kai-audit.md)
- [kai-html-presentation](./kai-html-presentation.md)

### Called by
- [kai-audit](./kai-audit.md)

### Quality gates
- Provenance lint passes; every ranking, volume, review, listing, backlink, AI-answer, Lighthouse and page-weight claim cites a source and retrieval date.
- Banned-word check passes on the report.
- Rendered page: no horizontal overflow at 390 px or 1280 px outside table wrappers, all images loaded, no duplicate ids.
- After two failed retry cycles, remaining failures are surfaced instead of hidden.

### Provenance written
- `data_mode` - written into `audit-data.json` and the report header.
- `source_tiers` - `connected` for DataForSEO API pulls, `public_observed` for direct checks.
- `retrieval_dates` - per source in `_data-sources.md`.
- `collector_paths` - raw artifact paths under `raw/`.
- `data_gaps` - `_data-gaps.md`.
- `blocked_claims` - any metric a failed pull could not support.

### Example artifacts
- Config template: [local-audit-config.example.json](../../examples/local-audit-config.example.json)

### Failure modes
- Missing DataForSEO credentials limit the audit to direct public checks; located metrics become data gaps.
- A loose `brand_pattern` matches unrelated businesses sharing the name and produces a false "listing found".
- Rankings move day to day; single-position claims without a date mislead.
- Business Listings requests with more than ~8 categories fail with `40501 Invalid Field: 'categories'`.
- Quantitative claims are blocked when collector data or source citations are missing.

### Competitive claim
This skill measures a local business from its customers' towns, devices and languages instead of the auditor's browser, and ties every finding to a priced offer, an exact change and a dated plan week. It does not claim guaranteed ranking, map-pack or AI-assistant lifts.
