---
name: kai-seo-audit
description: One-click technical SEO audit of a website. Runs the full technical SEO audit SOP — crawlability, indexation, Core Web Vitals, schema markup, internal linking, mobile UX, and content quality. Outputs a prioritized fix list. Use when "SEO audit", "technical SEO", "site audit", "crawl issues", "indexation problems", "why aren't we ranking", "SEO health check", or any request to diagnose SEO issues on a website.
---

Run a technical SEO audit using the harness SOPs and checklists. Produces a prioritized fix list.

## Phase 1: Site Input

Ask the user:

1. **URL** — what site are we auditing?
2. **Scope** — full site or specific sections?
3. **Known issues** — anything already flagged?
4. **Access** — do we have Search Console / analytics access?
5. **Priority** — what matters most? (rankings, traffic, indexation, speed)

## Phase 2: Audit Execution

Load these before starting:
- `E:\Dev2\kai-cmo-harness-work\knowledge\checklists\technical-seo-audit-sop.md`
- `E:\Dev2\kai-cmo-harness-work\knowledge\checklists\technical-seo-checklist.md`
- `E:\Dev2\kai-cmo-harness-work\knowledge\checklists\seo-checklist.md`

### Audit Layers (run in order)

**Layer 1: Crawlability & Indexation**
- robots.txt — blocking important pages?
- XML sitemap — exists, submitted, up to date?
- Canonical tags — correct, consistent?
- Noindex/nofollow — any unintended blocks?
- HTTP status codes — 404s, redirect chains, 5xx errors?
- Pagination — rel=next/prev or infinite scroll handling?

**Layer 2: Technical Performance**
- Core Web Vitals (LCP, FID/INP, CLS)
- Mobile-friendliness
- Page speed (server response time, render-blocking resources)
- HTTPS — mixed content, certificate issues?
- Structured data / schema markup — present, valid?

**Layer 3: On-Page SEO**
- Title tags — unique, keyword-included, under 60 chars?
- Meta descriptions — unique, compelling, under 155 chars?
- H1 tags — one per page, keyword-relevant?
- Image alt text — descriptive, keyword-relevant?
- Internal linking — orphan pages, shallow link depth?
- URL structure — clean, descriptive, flat hierarchy?

**Layer 4: Content Quality**
- Thin content pages (under 300 words)
- Duplicate content (internal and external)
- Keyword cannibalization (multiple pages targeting same keyword)
- Content freshness — last updated dates
- E-E-A-T signals — author bios, citations, credentials

**Layer 5: Off-Page Signals**
- Backlink profile overview (if data available)
- Brand mentions without links
- Local SEO (if applicable) — GBP, NAP consistency

Use the browse/gstack skill to actually crawl pages if available. Otherwise, work from what the user provides or can check.

## Phase 3: Prioritized Fix List

Score each finding:

| Priority | Impact | Effort | Examples |
|----------|--------|--------|----------|
| **P0** | High impact, easy fix | < 1 hour | Missing title tags, broken canonical, noindex on important pages |
| **P1** | High impact, moderate effort | 1 day | CWV failures, redirect chains, thin content |
| **P2** | Medium impact | 1 week | Schema markup, internal linking optimization |
| **P3** | Low impact / nice-to-have | Ongoing | Alt text gaps, URL cleanup |

## Phase 4: Output

```markdown
# SEO Audit Report: [site.com]

## Health Score: [X]/100

## Critical Issues (P0)
| Issue | Pages Affected | Fix |
|-------|---------------|-----|
| ... | ... | ... |

## High Priority (P1)
| Issue | Pages Affected | Fix |
|-------|---------------|-----|

## Medium Priority (P2)
...

## Low Priority (P3)
...

## Technical Checklist Results
- [ ] robots.txt: [PASS/FAIL — detail]
- [ ] XML sitemap: [PASS/FAIL]
- [ ] Canonical tags: [PASS/FAIL]
- [ ] Core Web Vitals: [PASS/FAIL — LCP: Xs, INP: Xms, CLS: X]
- [ ] Mobile: [PASS/FAIL]
- [ ] HTTPS: [PASS/FAIL]
- [ ] Schema: [PASS/FAIL]
- [ ] Title tags: [PASS/FAIL]
- [ ] Internal linking: [PASS/FAIL]
...

## Recommendations
[Top 5 actions ordered by impact-to-effort ratio]
```

Save to `workspace/seo-audit/[domain].md`.
