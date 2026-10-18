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

## Revenue Lens: Measure Revenue, Not Activity

Sourcing a number correctly does not make it the right number. The failure this section prevents: a well-sourced report that reads sessions, pageviews and lead counts, where an expert operator would read revenue, buyer intent and the whole funnel.

**Lead with the funnel.** Every audit, report, review, growth plan and dashboard opens with the funnel, one row per stage, before any channel or technical finding:

| Stage | Expert question | Typical source |
|-------|-----------------|----------------|
| Traffic source | Which sources send buyers, not just visitors? | GA4 source/medium, GSC queries, ad platforms |
| Intent | Are the visitors and queries ones that buy (pricing, comparison, "near me", "hire", "cost", competitor names), or research and noise? | GSC query mix, landing page mix, ad search terms |
| Lead | How many qualified leads, at what rate, from which intent? | Forms, calls, chats, CRM |
| Follow-up | How fast and how completely is each lead worked (speed to lead, touches, unanswered calls)? | CRM, call tracking, inbox, SDR logs |
| Booked / paid | How many leads became meetings, signups, deposits or revenue, and what is each worth? | CRM stages, Stripe/payments, booking system |

**Rank by dollars.** The biggest gap is the stage that loses the most revenue, usually the leak between adjacent stages (high-intent traffic with no lead path, leads with no follow-up, follow-up with no booking). Sessions and lead counts are inputs; never present them as the result. When the funnel is broken past "lead", that is the headline, whatever else is true about traffic.

**Technical setup is a line, not the finding.** Schema, `llms.txt`, AI crawler access, sitemap and robots are usually already in place. Confirm them in one line (Pass / Fail with the source) and move on. They become findings only when a measured check fails (a P0 in the agent-readiness gate, a blocked crawler, a broken sitemap). Never pad a report with technical items to fill space while the funnel goes unread.

**Mark unverified items `check`.** Any claim, stage value or recommendation not verified against a source in this run is labeled `check` in the client-facing text, with what would verify it (e.g. `check: lead-to-booked rate; needs CRM stage export for Sept`). `check` items are not scored and are mirrored in `_data-gaps.md`. A funnel stage with no data is shown as `check`, never skipped and never estimated: an empty stage is often the most important finding.

In `sales_external` mode, the lead, follow-up and booked/paid stages are usually `check`. Say so, and use a public test (a form fill, a test call, a booking attempt) only when the workflow allows it.

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
