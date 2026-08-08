# Product-Led & Programmatic SEO Playbook

> **Use when:** Deciding whether to build a programmatic page section (integration pages, location pages, template galleries, comparison pages, calculator/data pages), designing the template and data pipeline for one, or auditing an existing programmatic section for scaled-content risk.
>
> **What this doc owns:** the programmatic/product-page motion — demand math, data requirements, template quality bar, scale gating.
> **What adjacent docs own (cross-link, don't duplicate):**
> - Topical maps, quality vs trending nodes, site-wide semantic architecture → `knowledge/playbooks/semantic-seo-methodology.md`
> - AI-search retrievability, entity clarity, evidence tiers for AI engines → `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`
> - General internal-linking mechanics (hub-and-spoke, anchor rules) → `knowledge/playbooks/seo-internal-linking.md`
> - Crawl/index troubleshooting → `knowledge/checklists/technical-seo-audit-sop.md`

---

## 1. The Core Idea

Product-led SEO (term popularized by Eli Schwartz's book *Product-Led SEO*, 2021) builds pages that ARE the product experience, not content ABOUT the product. The page itself does a job: converts a currency, shows an integration, renders a template, answers "salary for X at Y." Programmatic SEO is the production method: one template × one dataset × N entities = N pages.

The method is neutral. The same machinery built Zapier's integration pages and a million doorway-page penalties. The difference is a three-factor test, and all three factors must pass:

```
SHIP = Real Search Demand × Unique Data × Genuine Utility
       (any factor = 0 → the product is 0 → do not build)
```

| Factor | Question | Pass looks like | Fail looks like |
|--------|----------|-----------------|-----------------|
| **Real search demand** | Do people actually search this pattern, entity by entity? | Head terms + a repeating modifier pattern with volume across the long tail ("[app A] + [app B] integration", "[currency] to [currency]") | Volume exists only at the head; long-tail permutations are zero-volume guesses |
| **Unique data** | Does each page contain facts only we (or our licensed source) can publish? | Proprietary product data, user-generated content, licensed feeds, first-party measurements | Scraped competitor content, respun Wikipedia, LLM-generated "descriptions" of things you have no data on |
| **Genuine utility** | Would a user landing here get the job done without clicking back? | Interactive tool, live data, complete answer, transactable inventory | A paragraph of filler wrapped around one templated sentence, funneling to a signup form |

Schwartz's stronger claim: the best programmatic plays create demand categories competitors ignored, rather than fighting over existing keyword lists. Validate that with real query data before believing it for your case (see Section 6, Stage 1).

---

## 2. When Programmatic Pages Work — Reference Patterns

Third-party page counts below are vendor estimates (Tier 5-6 evidence per the AEO playbook's evidence ladder) — use as pattern references, not benchmarks to promise.

| Pattern | Example | Why it passes the three-factor test |
|---------|---------|-------------------------------------|
| **Entity-pair pages** | Zapier: an indexed page per app and per app-pair (~25,000+ pages per practitioner analyses) | Demand: people search "connect X to Y." Data: Zapier's own integration catalog. Utility: page starts the actual workflow |
| **Live-data utility pages** | Wise currency pages (~3,000+ pages) | Demand: "usd to eur" class queries. Data: Wise's own live rates. Utility: the converter works on the page |
| **Inventory pages** | Zillow (tens of millions of listing pages), Tripadvisor (location × category pages) | Demand: address/city-level queries. Data: proprietary or licensed listing inventory. Utility: the listing is the answer |
| **Template/asset galleries** | Canva template pages (~30,000+ per third-party counts) | Demand: "[occasion] invitation template." Data: Canva's own asset library. Utility: one click into the editor |
| **UGC-review pages** | G2, Glassdoor | Demand: "[product] reviews," "[company] salary." Data: user submissions no competitor holds. Utility: the reviews themselves |

Common denominator: in every winner, the dataset is the moat and the page is a working surface of the product. None of them could be replicated by a competitor with a scraper and a template.

---

## 3. When It's Spam — Google's Published Line

Google's [spam policies](https://developers.google.com/search/docs/essentials/spam-policies) define three failure modes that map directly onto bad programmatic builds. Quote-level definitions (Tier 1 evidence — official policy):

**Scaled content abuse** — "when many pages are generated for the primary purpose of manipulating search rankings and not helping users." Listed examples include: "using generative AI tools or other similar tools to generate many pages without adding value for users" and "scraping feeds, search results, or other content to generate many pages... where little value is provided to users." The March 2024 policy update deliberately made this method-agnostic: human-written, AI-written, or hybrid — scale without value is the violation ([Google Search Central blog, March 2024](https://developers.google.com/search/blog/2024/03/core-update-spam-policies)). Google projected the accompanying core + spam updates would cut low-quality, unoriginal content in results by 40% ([Google blog, March 2024](https://blog.google/products-and-platforms/products/search/google-search-update-march-2024/)); after the rollout completed in April 2024, Google said the actual reduction was 45% ([Search Engine Land, April 2024](https://searchengineland.com/google-march-2024-core-update-rollout-is-now-complete-438713)).

**Doorway abuse** — pages "created to rank for specific, similar search queries" that "lead users to intermediate pages that are not as useful as the final destination." The listed example is the classic bad-programmatic build: "having multiple domain names or pages targeted at specific regions or cities that funnel users to one page." A location-page section where every city page is the same pitch with a swapped city name is a doorway section.

**Thin affiliation** — product pages "where the product descriptions and reviews are copied directly from the original merchant without any original content or added value." Programmatic affiliate builds fail here by default unless each page adds original data.

**Decision rule:** if the honest description of your build is "we generated N pages so we'd rank for N queries," you are inside the scaled-content-abuse definition. If the honest description is "we have N things (integrations, listings, datasets, templates) and each gets a page," you are outside it. Write that sentence down before building; it is the fastest audit.

---

## 4. Template-Page Quality Bar

A programmatic page must survive being read alone, as if it were the only page on the site. Minimum bar, checked on the prototype (Section 6, Stage 3) and re-checked on random samples at scale:

1. **Majority-unique content test.** More than 50% of the rendered visible content must be entity-specific data that differs page to page (numbers, inventory, reviews, screenshots, structured facts). Template boilerplate — intro paragraph, FAQ shell, CTA blocks — stays under 50%. If two random pages diff to near-identical text with nouns swapped, the section fails.
2. **The zero-data rule.** No page ships for an entity you have no real data on. An integration page for an integration that doesn't exist, a city page for a city with no inventory, a stats page with "data coming soon" — these are doorway/thin pages. Suppress (noindex or don't generate) any page below a data-completeness threshold you set per section (e.g., "≥3 reviews," "≥1 live listing," "rate feed present").
3. **On-page task completion.** The searcher's job finishes on the page: converter converts, template opens, listing is viewable, comparison table is complete. If the page's only affordance is "sign up to see the answer," it's a doorway.
4. **Unique metadata + one unique human-readable insight.** Title, H1, and meta description are generated from data, not from one string with a variable. Where feasible, add a per-page derived insight ("Rates for X dropped 12% this quarter" — computed, not hallucinated).
5. **Standard content gates still apply.** Copy blocks in the template pass `four_us_score.py` (12/16, SEO threshold), `banned_word_check.py`, and `seo_lint.py` — gate the template once, then gate rendered samples, because data merges create new sentences.
6. **AI-retrievability.** Each page's core fact block should be a self-contained, extractable passage (answer-first, visible HTML, eligible schema) — mechanics owned by `aeo-ai-search-playbook-2026.md` §3 (Content Optimization Checklist); apply them to the template, and they replicate everywhere.
7. **No hallucinated attributes.** LLM-assisted copy may rephrase and structure the data you have; it may not invent attributes, counts, reviews, or comparisons. This is the same line Google draws (AI is fine; valueless scale is not) and the same line Kai's provenance rules draw.

---

## 5. Data-Source Requirements (Kai provenance rules apply)

Programmatic SEO is a data product. The data pipeline is governed before the template is designed:

- **Allowed sources:** proprietary product data, first-party measurements, user submissions you have rights to display, licensed feeds/APIs used within license terms, and public government/open datasets with attribution.
- **Banned sources:** scraped competitor content, republished merchant feeds with no added value (thin affiliation), fabricated or LLM-imagined data points, and review/rating counts you didn't collect. Google's scaled-content examples name scraping-plus-transformation ("synonymizing, translating, or other obfuscation") explicitly.
- **Kai Data Provenance Rule applies in full** (see `AGENTS.md` and `harness/references/audit-data-provenance.md`): every quantitative claim rendered into a page traces to a collector source; missing data goes to `_data-gaps.md` — or the page doesn't generate — never to a guess. Run `audit_provenance_lint.py` on any client-facing audit of a programmatic section.
- **Freshness contract:** define per-section how stale data can get before pages are updated or suppressed (live rates: minutes; salary data: quarterly; static templates: on change). A programmatic section with dead data decays into thin content without anyone touching it.
- **License audit:** record the license/terms for every third-party feed in the section's data manifest. "We found an API" is not a license.

---

## 6. Build Order: Demand → Data → Prototype → Gate → Scale

Never invert this order. Building the generator first is how 50,000 thin pages happen.

### Stage 1 — Demand validation (kill ~half of ideas here)
- Enumerate the query pattern: `[modifier] + [entity]` or `[entity A] + [entity B]`. Pull volume for the head term AND a random sample of ≥50 long-tail permutations (GSC if you rank for adjacent terms, keyword tools otherwise; label the evidence tier).
- **Pass:** demand is distributed across the tail, intent matches the page's job, and SERP inspection shows the pattern rewards dedicated pages (competitors' entity pages rank, not one mega-page).
- **Fail:** volume concentrates in the head → build one strong page instead (the semantic-SEO doc's rule: one continuously updated evergreen page, not thousands of individual pages). Zero-volume tails can still be worth building only when there's a documented creation-of-demand thesis (Schwartz's argument) plus a non-search value for the pages — write the thesis down and set a review date.

### Stage 2 — Data audit
- Inventory: entity count, attributes per entity, % completeness per attribute, source + license per attribute, refresh cadence.
- Set the generation threshold (Section 4, rule 2). Count how many entities clear it — **that number, not the entity count, is your page count.**
- If <100 entities clear the bar, question whether this is a programmatic section at all; a hand-built hub may win.

### Stage 3 — Template prototype
- Hand-build 3-5 pages for representative entities (best-case, median, worst-case data completeness). The worst-case page decides the design.
- Design the empty-state behavior: what does the template do when an attribute is missing? (Omit the module — never render placeholder text.)
- Run the quality bar (Section 4) and standard gates on all prototypes.

### Stage 4 — Quality gate at small scale
- Generate 50-200 pages. Index them. Human-review a random 10% against Section 4. Diff random page pairs for boilerplate ratio.
- Instrument: GSC indexation coverage, impressions per page, engagement. Wait one full crawl-index-rank cycle (typically 4-8 weeks) before judging.
- **Go/no-go:** majority of the batch indexed, impressions distributed across pages (not just the index page), no manual action, no "Crawled — currently not indexed" pile-up. Indexation refusal at small scale is Google grading your quality bar — fix the template, don't scale past it.

### Stage 5 — Scale, in tranches
- Release in tranches (e.g., 500 → 2,500 → 10,000), each gated on the previous tranche's indexation and engagement. Never dump the full dataset in one deploy.
- Standing monitors: indexation ratio per tranche, sample re-reviews each quarter, data-freshness alarms, and the section's rollback plan (ability to noindex a tranche in one change).
- **Human approval is required before each tranche goes live** — publishing programmatic pages is a live-channel mutation and follows the same approval doctrine as everything else in this harness (publishing default OFF).

---

## 7. Internal-Linking Architecture for Programmatic Sections

General linking mechanics live in `seo-internal-linking.md`; semantic-node strategy in `semantic-seo-methodology.md`. Programmatic-specific rules:

1. **Every programmatic page must be reachable through a browsable hierarchy** — home → section hub → (category index) → detail page, ≤4 clicks. Google's doorway definition flags "substantially similar pages that are closer to search results than a clearly defined, browseable hierarchy"; orphaned pages fed to Google only via XML sitemap fit that description.
2. **Hub + paginated category indexes, not a flat dump.** The section hub is a quality node (it earns external links); category indexes (by letter, geography, type) carry PageRank down to detail pages. Detail pages cross-link laterally to genuinely related entities (same category, same pair-member, nearby location) — capped at a fixed, small number (5-10) chosen by relevance rules, not "all 40,000 siblings" footers.
3. **Link programmatic detail pages UP to commercial quality nodes.** The section exists to feed authority and users to the pages that convert (the semantic-SEO doc's trending-node → quality-node pattern).
4. **Control combinatorial crawl explosion.** Entity-pair and faceted sections multiply URLs; Google calls faceted navigation "by far the most common source of overcrawl issues" site owners report ([Google Search Central blog, Dec 2024](https://developers.google.com/search/blog/2024/12/crawling-december-faceted-nav)). Follow Google's faceted-navigation guidance: robots-disallow filter permutations you don't want indexed, keep filter parameter order consistent, and return 404 for empty combinations ([Google Search Central docs](https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation)). Decide index/noindex per URL class before launch, not after the crawl budget is gone.
5. **Segmented XML sitemaps per tranche/category** so indexation can be monitored per segment in GSC (pairs with `harness/references/google-indexation-monitoring.md`).

---

## 8. UGC-SEO Loops

The strongest programmatic moat is data that users create for you (G2 reviews, Glassdoor salaries, Tripadvisor reviews, Stack Overflow answers): every user contribution improves a page, better pages rank and attract more users, who contribute more. Loop design requirements:

- **Contribution → page mapping:** each contribution must land on a determinate page (entity page, question page) — that's what compounds. Feeds and profiles don't build search equity.
- **Cold-start honesty:** pages below the contribution threshold stay noindexed until they clear it (Section 4, rule 2). A UGC section at launch is mostly empty pages — suppressing them is the difference between a loop and a spam section.
- **Moderation as a quality gate:** unmoderated UGC imports spam, defamation risk, and policy violations into your index. Budget moderation (human or model-assisted with human escalation) as a permanent cost of the loop.
- **Prompted structure beats free text:** structured contribution forms (ratings by dimension, pros/cons fields) generate extractable, passage-retrievable content that both classic SERPs and AI engines can cite (AEO playbook, passage-retrievability principle).
- **Rights:** terms of service must grant display rights; UGC counts as first-party data only when they do.
- Loop mechanics and incentive design beyond SEO → `knowledge/playbooks/growth-loops-applied.md` and `knowledge/playbooks/community-as-channel.md`.

---

## 9. Kill Criteria & Anti-Patterns

Kill or noindex a programmatic section when any of these holds:

- Indexation ratio for a tranche stays under ~50% after two crawl cycles and template fixes (Google is refusing the quality bar).
- The data source dies or the license lapses (pages will rot into thin content).
- Manual action or visible post-core-update section-wide demotion — noindex first, remediate against Section 4, request review only after the fix is real.
- The section's pages cannibalize a stronger evergreen page for the same intents.

Anti-patterns (log recurrences to `memory/what-doesnt-work.md`): city-swap doorway pages; LLM-generated "reviews" of products never touched (fabricated proof — Stop condition under the Instruction Contract); publishing the full entity list on day one; template intros longer than the data they introduce; "we'll add the data later" launches.

---

## How This Maps Into Kai

- **`kai-seo-audit` / technical SEO audits** load this doc when the target site has (or plans) programmatic sections — Sections 3-4 supply the scaled-content risk rubric, Section 7 the crawl/linking checks. Pair with `knowledge/checklists/technical-seo-audit-sop.md` and `knowledge/checklists/seo-checklist.md`.
- **Growth/SEO strategy work** (`kai-growth-plan`, content strategy briefs) uses Section 1's three-factor test and Section 6's build order to decide whether to recommend a programmatic motion at all.
- **Provenance enforcement:** any audit or plan quoting a section's traffic, page counts, or indexation runs the Kai Data Provenance Rule (`harness/references/audit-data-provenance.md`, `audit_provenance_lint.py`). Never quote this doc's third-party example numbers as client benchmarks.
- **Quality gates:** template copy and rendered samples go through `four_us_score.py`, `banned_word_check.py`, `seo_lint.py` like any SEO content; algorithmic-authorship rules (`knowledge/frameworks/content-copywriting/algorithmic-authorship.md`) apply to template prose.
- **Approval doctrine:** generating pages is content work; publishing/indexing them is a live-channel mutation — human approval per tranche, publishing default OFF.
- **Adjacent strategy docs:** semantic architecture → `semantic-seo-methodology.md`; AI-engine visibility of programmatic pages → `frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`; linking mechanics → `seo-internal-linking.md`; indexation monitoring → `harness/references/google-indexation-monitoring.md`.

## Sources

- Google Search Central — Spam policies (scaled content abuse, doorway abuse, thin affiliation): https://developers.google.com/search/docs/essentials/spam-policies
- Google Search Central Blog — "What web creators should know about our March 2024 core update and new spam policies": https://developers.google.com/search/blog/2024/03/core-update-spam-policies
- Google — "New ways we're tackling spammy, low-quality content on Search" (40% projection): https://blog.google/products-and-platforms/products/search/google-search-update-march-2024/
- Search Engine Land — "Google March 2024 core update rollout is now complete" (45% actual reduction, per Google): https://searchengineland.com/google-march-2024-core-update-rollout-is-now-complete-438713
- Google Search Central Blog — "Crawling December: Faceted navigation" (overcrawl quote): https://developers.google.com/search/blog/2024/12/crawling-december-faceted-nav
- Google Search Central — Managing crawling of faceted navigation URLs: https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation
- Eli Schwartz — *Product-Led SEO: The Why Behind Building Your Organic Growth Strategy* (2021): https://www.elischwartz.co/book
- Zapier — "Programmatic SEO: How to do it & if you should": https://zapier.com/blog/programmatic-seo/
- Ahrefs — "Programmatic SEO, Explained for Beginners": https://ahrefs.com/blog/programmatic-seo/
- Practical Programmatic — case studies (Zapier, Tripadvisor; page-count estimates, Tier 5-6): https://practicalprogrammatic.com/examples
- SEOmatic — "Programmatic SEO Examples: 7 Real Sites Doing It at Scale" (Wise, Canva, G2 page-count estimates, Tier 5-6): https://seomatic.ai/blog/programmatic-seo-examples
