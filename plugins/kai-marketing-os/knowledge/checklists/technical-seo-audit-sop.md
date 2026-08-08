# Technical SEO Audit SOP (Screaming Frog)

Standard operating procedure for conducting technical SEO audits using Screaming Frog. Includes issue classification, dev ticket templates, and required exports.

---

## 1. Pre-Crawl Setup (MANDATORY)

### 1.1 Choose the Correct Crawl Mode

| Site Type | Crawl Mode |
|-----------|------------|
| **Standard site** | Spider mode |
| **JavaScript-heavy (React/Vue/SPA)** | Configuration → Spider → Rendering → JavaScript |
| **Partial crawl / blocked site** | Crawl XML sitemap OR List Mode (specific URLs only) |

### 1.2 Prevent Server Overload / 429 Errors

If you see 429, Cloudflare blocks, timeouts, or slow response:

**Screaming Frog settings:**

| Setting | Location | Recommended Value |
|---------|----------|-------------------|
| Threads | Configuration → System → Threads | 1–3 |
| URL rate limit | Configuration → Speed | 0.2 – 1 URLs/second |
| Request delay | Configuration → Speed | Increase as needed |
| Disable resources | Configuration → Spider | Disable images, CSS, JS unless required |
| AJAX crawling | Configuration → Spider | Disable if not needed |

**If still blocked:**
1. Stop crawl
2. Notify PM / lead
3. Ask devs to allowlist your IP or relax rate-limits temporarily

**Dev instruction template (429):**
```
We are receiving HTTP 429 errors during crawling due to server rate limiting.
Please temporarily allowlist our IP or increase request thresholds.
Crawl speed is already limited to X threads and Y URLs/second.
```

---

## 2. Google AI Search / AEO Overlay

Google AI Overviews and AI Mode use Google Search systems. Treat this overlay as a technical SEO check for generative Search visibility, not as a separate crawler or markup project.

### 2.1 Eligibility Checks

- Confirm key pages are crawlable by Googlebot and not blocked by `robots.txt`, WAF rules, or server protections
- Confirm key pages are indexable and canonicalized to the intended URL
- Confirm key pages are eligible for snippets: no accidental `nosnippet`, `data-nosnippet`, or overly restrictive `max-snippet`
- Confirm rendered HTML exposes the main content, headings, links, media, and product/local details
- Confirm JavaScript-rendered sites follow JavaScript SEO best practices and do not hide primary content until after user interaction

### 2.2 Content + Data Checks

- Validate structured data only where it matches visible content and a real Google Search feature
- For ecommerce sites, verify Product schema, Merchant Center feed health, price, availability, return policy, shipping, and image eligibility
- For local businesses, verify Google Business Profile data, local business schema, NAP consistency, service areas, hours, reviews, and location/service pages
- For image/video-heavy pages, verify descriptive filenames, alt text, captions/transcripts, video metadata, and sitemap/feed coverage where applicable
- Use query fan-out/PAA research to identify missing user facets, then consolidate into useful pages or clusters; do not create doorway pages for every query variant

### 2.3 Measurement Checks

- Export Google Search Console page/query data for the audit period where access exists
- Track impressions, clicks, CTR shifts, indexed pages, and query/page pairs; Google does not provide a universal AI Overview-only report in Search Console
- Record any manual AI Overview / AI Mode observations with query, location/device, date, and screenshot
- Cite every client-facing visibility claim from Search Console, crawler exports, SERP screenshots, or a named third-party AI visibility tool
- Label AI visibility by engine; do not combine Google AI Overview observations, Bing AI Performance, ChatGPT samples, Claude samples, Perplexity citations, and Grok/X observations into one undifferentiated "AI ranking"
- For Bing Webmaster Tools AI Performance, report citation counts, cited pages, grounding queries, and date range as Microsoft AI surface data

### 2.4 Agent-Readiness Overlay

Run this overlay for AI search, browser agents, documentation sites, local businesses with booking forms, ecommerce, and any site that expects agents to compare, summarize, or transact.

- Confirm primary content appears in initial HTML, not only after JS, login, modal, infinite scroll, or click-to-expand controls
- Confirm semantic structure: one H1, ordered H2/H3s, meaningful link text, visible main content, and no critical facts only in images/PDFs
- Confirm accessibility tree basics: labeled form controls, buttons with accessible names, descriptive image alt text, and visible focus/interaction states
- Confirm stable commercial facts: product name, price/price range, availability, address, hours, phone, service area, return policy, booking path, and approval/human-review path where relevant
- Confirm forms and booking flows expose labels, validation messages, confirmation states, and phone alternatives in text
- Confirm WAF/anti-bot rules do not block Googlebot, bingbot, declared AI search crawlers, or browser-like user agents needed for agentic experiences

**Agent-readiness data-gap language:**

```markdown
Data gap: The audit did not include authenticated checkout or booking flow access, so agent-readiness findings are limited to public pages.
Data gap: Server logs were unavailable, so we could not confirm whether OpenAI, Anthropic, Perplexity, Googlebot, or bingbot accessed the site during the audit window.
Data gap: The crawler export does not include rendered screenshots. We cannot confirm whether modal-only pricing or hidden tabs are visible to browser agents.
```

---

## 3. Indexation Monitoring SOP

Load `harness/references/google-indexation-monitoring.md` for launch QA, page-indexing issues, sitemap cleanup, and any audit where priority URLs are not appearing in Google Search.

### 3.1 Priority URL Decision

Assign one action to every questionable URL:

| Action | Use When |
|--------|----------|
| `index` | The page is canonical, useful, crawlable, and should appear in Search |
| `noindex` | The page should remain accessible but not appear in Search |
| `canonicalize` | The page duplicates another URL and should consolidate signals |
| `redirect` | The page has moved or should be merged into a replacement |
| `remove` | The page is obsolete, test-only, unsafe, or intentionally gone |
| `improve` | The page is useful in theory but too thin, duplicative, or unclear |

### 3.2 Monitoring Cadence

- First 7 days after launch: check priority URLs daily in Search Console Page Indexing and URL Inspection.
- Weeks 2-4: check two or three times per week unless the page is business-critical or status is changing.
- After 30 days: escalate unindexed URLs only after crawl access, canonicals, sitemaps, content quality, and internal links are checked.

### 3.3 Evidence Required

- Search Console Page Indexing status where access exists
- URL Inspection status, including Google-selected canonical
- Sitemap inclusion status
- Crawl status code, indexability, canonical tag, and internal inlinks
- Manual `site:example.com/exact-url` check, labeled as a rough check rather than source of truth
- Server log Googlebot evidence where access exists

### 3.4 Safe Fix Patterns

- Add crawlable internal links from relevant, already-indexed pages.
- Keep sitemap entries limited to clean canonical URLs.
- Fix blocked resources, WAF rules, login walls, `robots.txt`, accidental `noindex`, bad canonicals, and soft 404s.
- Improve thin pages with original information, examples, media, product/local data, or expert review.
- Consolidate duplicates instead of creating URL variants.

### 3.5 Rejected Tactics

Do not recommend repeated indexing requests for unchanged URLs, duplicate URL generation, cloaking, hidden text, fake social signals, link spam, keyword stuffing, fake freshness, doorway pages, or `robots.txt` blocking when a `noindex` directive must be seen by Googlebot.

### 3.6 Patent-History Caveat

Patents can explain possible crawl/index/ranking system designs, including sitemap hints, historical change, link discovery, freshness, and spam detection. Treat patent material as diagnostic context, not proof of current Google ranking behavior.

---

## 4. Post-Crawl Analysis Workflow

Review these tabs **in order**:

1. **Response Codes** - Identify 4xx, 5xx errors
2. **Redirect Chains** - Find multi-hop redirects
3. **Indexability** - Find noindex, blocked pages
4. **Canonicals** - Find canonical mismatches
5. **Inlinks** - Trace broken URL link sources
6. **robots.txt / Directives** - Check blocking rules
7. **Sitemaps vs Crawl** - Compare if sitemap provided
8. **Rendered HTML / JavaScript comparison** - Confirm main content is available to crawlers
9. **Structured data validation** - Confirm valid, content-matching schema for eligible rich results

---

## 5. Issue-by-Issue SOP + Dev Instructions

### A. 404 NOT FOUND

Every 404 must be classified into ONE of these types:

#### 404 TYPE 1 – Page was removed by mistake (should be live)

**Signs:**
- Important service/product page
- Has internal links or backlinks
- No replacement page exists

**Action:** Restore page and return 200

**Dev instruction:**
```
Restore /old-service-page (returns 404 currently).
Page was removed by mistake and should return a 200 status.
```

---

#### 404 TYPE 2 – Page moved → needs 301 redirect

**Signs:**
- New version exists
- Content clearly replaced

**Action:** Add 301 redirect to closest equivalent page

**Dev instruction:**
```
Implement 301 redirect:
/old-url → /new-url
Reason: page was moved/renamed. Final URL must return 200.
```

---

#### 404 TYPE 3 – Page is intentionally gone (valid 404)

**Signs:**
- No replacement
- No SEO value

**Action:**
- Remove all internal links
- Remove from sitemap

**Dev instruction:**
```
/dead-url is intentionally removed.
Please remove all internal links pointing to it and delete it from XML sitemap.
```

---

#### 404 TYPE 4 – Internal link typo / malformed URL

**Signs:**
- Misspellings
- Double slashes
- Wrong casing
- Broken parameters

**Action:** Fix internal link source

**Dev instruction:**
```
Fix internal link on /source-page.
Current link points to /servcie-page (404).
Update link to /service-page (200).
```

---

#### 404 TYPE 5 – Soft 404 (returns 200 but content = "not found")

**Signs:**
- Page returns 200
- Says "page not found"
- Very low content

**Action:** Return real 404/410 OR redirect to relevant page

**Dev instruction:**
```
/example-url is a soft 404 (returns 200 with "not found" content).
Please return proper 404/410 OR redirect to a relevant page.
```

---

### B. Redirect Issues (3xx)

#### Redirect Chains (CRITICAL)

**Rule:** Only ONE redirect allowed. Internal links must point to final URL.

**Example:** `/A → /B → /C`

**Dev instruction:**
```
Flatten redirect chain:
/A → /B → /C
Update redirect rules so /A redirects directly to /C with a single 301.
Update all internal links to point directly to /C.
```

---

#### Redirect Loops

**Example:** `/A → /B → /A`

**Dev instruction:**
```
Fix redirect loop between /A and /B.
Configure redirects so both resolve to a single final 200 URL.
```

---

#### Temporary Redirects Used Incorrectly

**Signs:** 302 / 307 used for permanent move

**Dev instruction:**
```
Change redirect from 302 to 301 for /old-url → /new-url to consolidate ranking signals.
```

---

#### HTTP / HTTPS / WWW Inconsistencies

**Dev instruction:**
```
Enforce a single canonical version:
- Redirect all HTTP → HTTPS
- Redirect all non-www → www (or vice versa)
Ensure this happens in one hop.
```

---

### C. 5xx Server Errors (URGENT)

**Examples:** 500, 502, 503, 504

**Action:** Provide URLs + timestamps

**Dev instruction:**
```
We are seeing 5xx errors on the following URLs:
/a, /b, /c
Please investigate server logs around crawl time and resolve application/server issues.
```

---

### D. No Response / Timeouts

**Causes:**
- WAF blocking
- Server overload
- Hosting issues

**Dev instruction:**
```
Requests to /example-url are timing out.
Please review firewall/WAF rules or server capacity and allow crawler access.
```

---

### E. Indexability Issues (200 but not indexable)

#### Noindex Applied Incorrectly

**Dev instruction:**
```
Remove noindex from /page-url.
Page should be indexable and currently returns 200.
```

---

#### Canonical Errors

**Common issues:**
- Canonical to wrong page
- Canonical to 404
- Canonical mismatch

**Dev instruction:**
```
Update rel=canonical on /page-url to self-referencing canonical (or correct destination).
Current canonical points to incorrect URL.
```

---

### F. robots.txt / X-Robots-Tag

#### Important Pages Blocked by robots.txt

**Dev instruction:**
```
robots.txt currently blocks /folder/ which contains indexable pages.
Remove or narrow this disallow rule.
```

---

#### PDFs or Resources Blocked via X-Robots-Tag

**Dev instruction:**
```
Remove X-Robots-Tag: noindex from /file.pdf if it should be indexed.
```

---

## 6. REQUIRED Dev Ticket Format (NO EXCEPTIONS)

Every issue sent to devs **MUST** include:

| Field | Description |
|-------|-------------|
| **Issue type** | Category (404, redirect chain, etc.) |
| **Example URLs** | Minimum 3 if pattern exists |
| **Source(s)** | Where link was found |
| **Required action** | Exact change needed |
| **Expected result** | Status code + final URL |
| **Priority** | Critical / High / Medium / Low |

### Example Ticket

```
Issue type: Redirect chain

URLs: /A, /A2, /A3

Sources: /services, /blog/post-1

Required action: Redirect /A → /C in one hop, update internal links

Expected result: /A → 301 → /C (200)

Priority: High
```

---

## 7. Mandatory Screaming Frog Exports

Always attach these reports:

| Report | Purpose |
|--------|---------|
| **Response Codes (3xx / 4xx / 5xx)** | All status code issues |
| **Redirect Chains report** | Multi-hop redirects |
| **Inlinks report for broken URLs** | Source of broken links |
| **Indexability report** | Noindex, blocked pages |
| **Canonical errors** | Canonical mismatches |
| **Sitemap vs Crawl comparison** | Missing/extra URLs (if sitemap used) |
| **Rendered HTML / JavaScript crawl comparison** | Main content visibility for Googlebot and AI Search eligibility |
| **Structured data validation export** | Rich result eligibility and schema/content mismatch evidence |
| **Google Search Console export** | Page/query visibility, indexing, CTR, and crawl/index evidence where access exists |
| **Indexation monitoring log** | Priority URL action, URL Inspection result, sitemap status, manual check, blocker, owner, and next check date |

---

## Priority Matrix

| Issue Type | Priority | SLA |
|------------|----------|-----|
| 5xx errors | **Critical** | Same day |
| Redirect loops | **Critical** | Same day |
| Soft 404s on key pages | **High** | 24-48 hours |
| Redirect chains | **High** | 24-48 hours |
| Standard 404s with backlinks | **High** | 24-48 hours |
| Canonical errors | **Medium** | 1 week |
| Internal link typos | **Medium** | 1 week |
| Valid 404s (cleanup) | **Low** | 2 weeks |

---

## Quick Reference: Status Code Actions

| Code | Meaning | Standard Action |
|------|---------|-----------------|
| **200** | OK | Verify content matches intent |
| **301** | Permanent redirect | Ensure single hop to 200 |
| **302** | Temporary redirect | Change to 301 if permanent |
| **304** | Not modified | Normal (caching) |
| **400** | Bad request | Fix malformed URL |
| **401** | Unauthorized | Check auth requirements |
| **403** | Forbidden | Check server permissions |
| **404** | Not found | Classify (Types 1-5) |
| **410** | Gone | Valid for intentionally removed |
| **429** | Too many requests | Reduce crawl speed |
| **500** | Internal server error | Escalate to devs (urgent) |
| **502** | Bad gateway | Escalate to devs (urgent) |
| **503** | Service unavailable | Escalate to devs (urgent) |
| **504** | Gateway timeout | Escalate to devs (urgent) |
