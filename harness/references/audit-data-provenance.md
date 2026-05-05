# Kai Data Provenance Standard

Use this reference for every Kai workflow that publishes measured marketing, search, crawl, revenue, call, or conversion data. That includes marketing audits, SEO audits, CRO audits, local audits, competitive teardowns, audit decks, analytics plans, growth plans, campaign retrospectives, and client reports.

The failure this prevents: producing a polished client artifact with numbers that came from model inference, quick search snippets, or partial public observation.

## Data Modes

Every data-backed workflow must declare one mode before findings, recommendations, plans, reports, or decks are written.

| Mode | Use When | Allowed Data | Client-Facing Label |
|------|----------|--------------|---------------------|
| `sales_external` | Prospect or sales process before access is granted | Public website crawl, public SERP observation, robots/sitemap/schema, PageSpeed Insights, third-party APIs with agency keys | Sales intelligence audit, external-only |
| `onboarding_connected` | Client has signed and granted access | Everything in `sales_external`, plus GSC, GA4, GBP owner data, ad accounts, CRM, call tracking, analytics exports | Client onboarding audit |
| `internal_demo` | Showing a workflow shape before data is connected | Fabricated or placeholder values only if clearly marked as sample data | Internal demo, not client-ready |

Default to `sales_external` if no private access is confirmed.

## Collection Rule

Run the source-backed collector before any workflow uses numbers:

```bash
python -m scripts.audit.collect --url https://<domain> --mode sales_external --workflow <workflow> --out workspace/<workflow-data>
```

The collector writes both `kai-data.json` and the backward-compatible `audit-data.json`. New workflows should read `kai-data.json`; audit and deck instructions may continue to require `audit-data.json`. The contents are identical.

Collectors are opt-in beyond the public crawl:

```bash
python -m scripts.audit.collect --url https://<domain> --mode onboarding_connected --workflow analytics --out workspace/analytics-data --pagespeed --places --dataforseo --seo-provider auto --gsc --ga4 --calls --keywords "kw1,kw2" --location "Denver, CO" --date-from 2026-04-01 --date-to 2026-05-01
```

Missing credentials must create `_data-gaps.md` entries. They must not create placeholder metrics.

## Source Tiers

Every finding and every quantitative claim must use one source tier.

| Tier | Label | Examples | Client-Facing? |
|------|-------|----------|----------------|
| 1 | Connected source | GSC, GA4, GBP API, CallRail, Meta Ads, Google Ads, CRM, Ahrefs/Semrush/DataForSEO with API response | Yes |
| 2 | Public observed source | URL crawl, page source, sitemap, robots.txt, schema markup, live SERP capture, PageSpeed Insights URL | Yes, with timestamp |
| 3 | User-provided source | Client export, screenshot, spreadsheet, brief, call transcript | Yes, with filename/date |
| 4 | Inference or hypothesis | Agent judgment, pattern match, competitive assumption, missing-data proxy | No, unless explicitly labeled "hypothesis" and excluded from scoring |

Do not blend tiers. If a recommendation depends on a Tier 4 assumption, write it as a data gap or hypothesis, not as a finding.

## Hard Rules

1. Do not publish numbers without a source.
   Review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, and local pack placement must cite the source and retrieval date.

2. Do not turn inference into fact.
   Phrases like "likely ranks", "appears to be", or "educated guess" are not acceptable in client-facing findings. Convert them into `Data needed` items.

3. Do not score what was not measured.
   Missing GSC, GA4, GBP, call tracking, backlink, or ad-platform data must reduce scope confidence or create a data-gap flag. It must not be replaced by invented estimates.

4. Do not hide the audit mode.
   The executive summary and deck cover must say whether the audit is external-only, connected onboarding, or internal demo.

5. Do not cite a tool you did not actually run.
   If Ahrefs, DataForSEO, PageSpeed Insights, BuiltWith, Google Places, GSC, GA4, or GBP is named as a source, include the retrieved date and the exported/raw artifact path or API response summary.

## Required Output Files

Audit folders must include:

```text
workspace/marketing-audit/
├── _data-sources.md
├── _data-gaps.md
├── kai-data.json
├── audit-data.json
├── _executive-summary.md
├── _detailed-findings.md
└── _prioritized-fixes.md
```

`_data-sources.md` must list every source used:

```markdown
| Source | Tier | Access | Retrieved At | Used For | Artifact |
|--------|------|--------|--------------|----------|----------|
| https://example.com/sitemap.xml | Public observed | External | 2026-05-05 10:52 | Indexed URL count | raw/sitemap.xml |
```

`_data-gaps.md` must list every missing source:

```markdown
| Missing Source | Blocks | Sales Version Handling | Onboarding Version Handling |
|----------------|--------|------------------------|-----------------------------|
| Google Search Console | Query, page, CTR, and ranking truth | Mark ranking findings as unavailable | Pull 16-month query/page export |
```

## Required Finding Shape

Every finding should carry this evidence block, whether rendered as YAML, JSON, markdown, or slide notes:

```yaml
finding_id: local-seo-001
claim: "The site has no LocalBusiness schema on the homepage."
source_tier: public_observed
source_name: "Homepage source crawl"
source_url: "https://example.com/"
retrieved_at: "2026-05-05T10:52:00-04:00"
confidence: high
evidence_artifact: "raw/homepage.html"
score_eligible: true
```

Use `score_eligible: false` for hypotheses, missing-data notes, or internal demo claims.

## Sales vs Onboarding Data

Use this split when a user asks whether an audit belongs in sales or after signup.

| Dataset | Sales External | Onboarding Connected |
|---------|----------------|----------------------|
| Website crawl | Required | Required |
| PageSpeed Insights | Required if performance is scored | Required |
| Schema validation | Required if schema is scored | Required |
| SERP ranks | DataForSEO/Serp API only | DataForSEO plus GSC |
| Reviews/GBP | Google Places API or public GBP capture | GBP owner data |
| Backlinks/DR | Ahrefs/Semrush/Moz API only | Same plus client context |
| Organic clicks/CTR | Not available | GSC required |
| Sessions/conversions | Not available | GA4 required |
| Calls/missed calls | Not available unless public call test is performed | CallRail/CRM/phone logs required |
| Ad performance | Not available | Platform export required |

## Deck Rules

Every audit deck must include:

- Cover label: `Sales intelligence audit - external-only`, `Client onboarding audit`, or `Internal demo - sample data`.
- Source footer on every slide that contains a number.
- Appendix slide named `Data Sources and Gaps`.
- No competitive, ranking, traffic, review, AI Overview, or conversion claim without a source footer.

## Gate

Before writing a data-backed workflow output, collect source-backed data:

```bash
python -m scripts.audit.collect --url https://<domain> --mode sales_external --workflow audit --out workspace/marketing-audit
```

Generated audit reports and decks must read from `audit-data.json`. Non-audit Kai workflows should read from `kai-data.json`. If a metric is not present there, it is unavailable.

Run the provenance gate on generated markdown or HTML before sending:

```bash
python scripts/quality_gates/audit_provenance_lint.py workspace/marketing-audit --audit-dir
```

The gate fails risky numeric claims without nearby source markers and fails audit directories that do not include `_data-sources.md` and `_data-gaps.md`.
