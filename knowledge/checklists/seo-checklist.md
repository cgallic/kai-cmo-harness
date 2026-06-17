# SEO Content Checklist

> **Use when:** Optimizing content for search rankings, Featured Snippets, or AI Overviews.

## Google Search Baseline
- [ ] Page is crawlable by Googlebot
- [ ] Page is indexable and canonicalized correctly
- [ ] Page has an explicit action: `index`, `noindex`, `canonicalize`, `redirect`, `remove`, or `improve`
- [ ] Priority page appears in a clean canonical XML sitemap and has crawlable internal links from relevant indexed pages
- [ ] Page is eligible to appear with a snippet (`nosnippet`, `data-nosnippet`, and `max-snippet` are not blocking key content)
- [ ] Main content is visible in rendered HTML, including on JavaScript-heavy pages
- [ ] Page satisfies Search Essentials and avoids scaled/doorway content patterns
- [ ] No indexation tactic depends on repeated unchanged URL submission, duplicate URL variants, cloaking, hidden text, fake social signals, link spam, keyword stuffing, fake freshness, or doorway pages

## Indexation Monitoring
- [ ] `harness/references/google-indexation-monitoring.md` was loaded for launch QA, indexing issues, sitemap cleanup, or priority URL troubleshooting
- [ ] First-week launch checks use Search Console Page Indexing, URL Inspection, sitemap status, crawl status, canonical status, and internal links
- [ ] Manual `site:example.com/exact-url` checks are labeled as rough visibility checks, not authoritative indexation proof
- [ ] URL Inspection records the Google-selected canonical and any crawl, indexing, or page-quality blockers
- [ ] Pages that should not be indexed are intentionally noindexed, canonicalized, redirected, removed, or blocked from discovery based on the use case
- [ ] Timeline language is cautious; no fixed indexing promise is made
- [ ] Patent-history claims are labeled as diagnostic hypotheses, not proof of current Google ranking behavior

## Google AI Search Calibration
- [ ] AEO/GEO work strengthens normal SEO; it is not treated as a separate Google ranking system
- [ ] No reliance on `llms.txt`, AI-only markdown, special AI schema, or forced content chunking for Google visibility
- [ ] Query fan-out and PAA research improve useful coverage instead of creating pages for every query variation
- [ ] Content adds non-commodity value: first-hand experience, original examples, named data, screenshots, images, video, product data, or local data
- [ ] Structured data is used only where it matches visible page content and a real Google Search feature

## Sentence Structure (Algorithmic Authorship)
- [ ] Conditions after main clause ("Do X if Y" not "If Y, do X")
- [ ] Instructions start with verbs ("Whip lightly" not "Lightly whip")
- [ ] Sentences short and declarative
- [ ] Complex sentences broken apart

## Entity & Anchor Rules
- [ ] Entities named twice before switching to attributes
- [ ] Anchor words connect sequential sentences
- [ ] Synonyms used for attributes in sequential sentences
- [ ] Abbreviations in parentheses on first mention

## Lists
- [ ] Numeric lists for steps/methods
- [ ] Bulleted lists for types/categories
- [ ] Same part of speech for first words in list items
- [ ] Same phrase patterns in list elements
- [ ] No trailing punctuation on incomplete sentences

## Numbers & Evidence
- [ ] Specific numbers used (not "many" or "several")
- [ ] Main types/factors stated before "other" types
- [ ] Examples follow every declaration
- [ ] Direction of factors stated (positive/negative effect)

## Formatting
- [ ] Answers bolded (NOT query-matching terms)
- [ ] No unnecessary words (if removal doesn't break grammar)
- [ ] No references to earlier sections ("As shown above...")

## Internal Linking
- [ ] No links in first word of sentences
- [ ] No links in first sentence of paragraphs
- [ ] Context provided before link
- [ ] Anchor text matches target page topic
- [ ] One internal link max per heading section

## External Sources
- [ ] Sources integrated in-text (not footnotes)
- [ ] Author/institution names included
- [ ] Research titles referenced
- [ ] Retrieval date captured for source-backed claims
- [ ] Evidence tier assigned: official requirement, official best practice, academic study, vendor/platform measurement, practitioner observation, internal measurement, hypothesis, or missing data
- [ ] Quantitative/client-facing claims cite a source; missing traffic, rankings, AI visibility, backlinks, Core Web Vitals, conversions, or schema findings are not guessed

## Featured Snippet Optimization
- [ ] Direct answer in first 100 words
- [ ] Definition format for "What is" queries
- [ ] Numbered list for "How to" queries
- [ ] Table for comparison queries

## AI Search Measurement
- [ ] AI visibility claims are engine-specific: Google AI Overviews/AI Mode, Bing/Copilot, ChatGPT, Claude, Perplexity, or Grok/X
- [ ] Manual AI answer checks include query/prompt, engine, date, location/device/account state where relevant, screenshot, citations, and sample count
- [ ] Bing AI Performance data is labeled as Microsoft AI citation data, not universal AI ranking
- [ ] Google Search Console data is labeled as Search performance data, not a universal AI Overview report
- [ ] No deterministic "rank in ChatGPT" or guaranteed AI citation promise appears in the draft

## Final Check
- [ ] Topic, entity, or primary query is clear in title/H1
- [ ] Direct answer appears in the first 100 words when the query calls for one
- [ ] Relevant facets appear in H2s or scannable sections
- [ ] Topic terms and synonyms are natural; no keyword-density target is being chased
- [ ] Reading level 6th-8th grade
- [ ] Page adds non-commodity value: firsthand experience, original examples, named sources, data, product/local details, or expert review
- [ ] `llms.txt`, special AI markup, forced Markdown, and chunking are not described as Google AI ranking requirements
