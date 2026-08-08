# SEO Ops Monitoring

> **Use when:** Running recurring SEO monitoring for traffic decay, striking-distance queries, content fingerprints, competitor gaps, technical drift, or AI-search visibility.

---

## Core Thesis

SEO ops is a monitoring loop, not a keyword dump.

Kai should first understand the client's existing corpus, crawlability, query data, and evidence gaps. Recommendations come after the source ledger is built.

---

## Required Sources

Use the best available sources for the mode:

- Google Search Console exports or API data.
- Analytics landing-page data.
- Crawl output.
- Rendered-page checks.
- `robots.txt`, optional `llms.txt`, sitemap, and schema checks.
- SERP or AI-search observations with retrieval date.
- Client CMS or content inventory exports.

For audits or client-facing reports, run the Kai data collector when available and cite collector output for quantitative claims.

---

## Monitoring Tracks

| Track | Question | Typical Action |
|-------|----------|----------------|
| Content fingerprint | What does the site already cover well? | Map URLs to entities, intents, formats, and proof assets |
| Striking distance | Which queries are near a useful ranking threshold? | Refresh page, add internal links, improve answer block, strengthen proof |
| Decay | Which pages lost impressions, clicks, or conversions? | Diagnose freshness, SERP changes, cannibalization, technical drift |
| Gap | Which topics are relevant but unsupported by owned content? | Create brief only after authority and fit are clear |
| Internal links | Which pages need crawl and equity support? | Add approved links through CMS workflow |
| AI-search readiness | Can engines and agents parse the site? | Fix crawl policy, schema, entity clarity, and JS-gating |
| Competitor movement | What changed in visible competitors? | Record source-backed observations, then seed experiments |

---

## Kai Workflow

1. Declare `mode`: `sales_external`, `onboarding_connected`, or `internal_demo`.
2. Build or refresh the source ledger.
3. Create the content fingerprint before recommending new pages.
4. Identify opportunities and mark data gaps.
5. Score each opportunity by evidence, business fit, effort, and mutation risk.
6. Produce a dry-run action plan.
7. Request approval before editing pages, publishing content, changing redirects, changing robots rules, or adding schema.
8. Log outcomes in the experiment ledger after implementation.

---

## Opportunity Schema

| Field | Notes |
|-------|-------|
| `opportunity_id` | Stable ID |
| `url` | Existing URL or proposed URL |
| `track` | Content fingerprint / striking distance / decay / gap / internal links / AI-search readiness |
| `query_or_entity` | Search query, entity, or topic cluster |
| `source_refs` | GSC, crawl, analytics, SERP, AI-search observation, or CMS export |
| `evidence_tier` | First-party / observed public / third-party / internal demo |
| `business_fit` | High / medium / low |
| `recommended_action` | Refresh / consolidate / link / brief / technical fix / monitor |
| `mutation_risk` | Low / medium / high |
| `approval_state` | Draft / requested / approved / rejected |
| `data_gaps` | Missing source facts |

---

## Dry-Run Artifact

Every SEO ops cycle should ship a dry-run artifact before mutation:

```markdown
# SEO Ops Dry Run

Mode:
Date:
Source ledger:

## Priority Actions
| ID | URL | Action | Evidence | Risk | Approval |
|----|-----|--------|----------|------|----------|

## Data Gaps

## Blocked Actions

## Approved-Only Mutations
- CMS edits
- Internal links
- Redirects
- Schema changes
- Robots or sitemap changes
- Publishing new URLs
```

---

## Guardrails

- Do not claim rankings, traffic, clicks, Core Web Vitals, backlinks, or AI Overview visibility without source refs.
- Do not invent competitor movement from memory.
- Treat AI-search observations as retrieval-time evidence, not permanent facts.
- Treat `llms.txt` as optional agent guidance, not a Google ranking requirement.
- Do not publish or edit live URLs without approval.
