# AEO & AI Search Playbook 2026

> Operating doctrine for visibility across Google AI Overviews and AI Mode, ChatGPT Search, Claude, Perplexity, Bing/Copilot, Grok, and browser agents. Treat recommendations as evidence-tiered hypotheses unless an official source says they are requirements.

---

## 1. Executive Summary

### Evidence Ladder

Every recommendation in this playbook must carry an evidence tier. Use the tier in briefs, audits, client reports, and test plans.

| Tier | Label | Use for |
|------|-------|---------|
| 1 | Official requirement | Platform rules needed for eligibility, crawling, indexing, serving, or policy compliance |
| 2 | Official best practice | Platform guidance that improves access, understanding, quality, or user experience |
| 3 | Academic study | Peer-reviewed or preprint research that tested methods or measurement behavior |
| 4 | Patent / system disclosure | Patent filings, public architecture talks, or engineering posts; useful for hypotheses, not proof of live ranking weight |
| 5 | Vendor / platform measurement | Tool-provider or platform reports with methodology and sample limits |
| 6 | Practitioner observation | Reputable field research, reverse engineering, or case work with clear caveats |
| 7 | Internal measurement | Kai/client data collected with declared method, sample size, and dates |
| 8 | Inference / hypothesis | Plausible idea to test; never present as a recommendation without measurement |
| 9 | Missing data | Required evidence is absent; list in `_data-gaps.md` instead of guessing |

### The 6 Operating Principles

**1. AI visibility is multi-engine, not Google-only.**
Google, OpenAI/ChatGPT, Anthropic/Claude, Perplexity, Microsoft/Bing/Copilot, and xAI/Grok use different discovery paths. Google says generative AI features in Search are rooted in normal Search systems: crawlability, indexability, snippet eligibility, quality systems, RAG, and query fan-out. OpenAI, Anthropic, and Perplexity publish separate controls for search/discovery, user-triggered retrieval, and model-training crawlers. Build a provider matrix before changing robots policy. Evidence: Tier 1-2.

**2. Google AI work is still SEO.**
For Google AI Overviews and AI Mode, do not sell `llms.txt`, special AI schema, AI-only Markdown files, forced chunking, or long-tail rewrites as ranking requirements. Google explicitly says those are not needed for generative AI Search. Use them only when they serve other agents or readers. Evidence: Tier 1-2.

**3. Content needs non-commodity value.**
Information Gain patents and GEO research support the same practical direction: do not publish a paraphrase of the top results. Add original data, expert review, firsthand experience, source-backed examples, product/local details, or clearer synthesis. Do not call Information Gain a deterministic ranking factor unless Google says so. Evidence: Tier 3-4.

**4. Passage retrievability beats page bloat.**
AI search systems often retrieve, parse, and cite specific passages. Build self-contained section-answer pairs, descriptive headings, tables, definitions, examples, and visible HTML. Do not break a page into tiny artificial chunks purely for AI. Evidence: Tier 2-4.

**5. Entity clarity reduces ambiguity.**
Use consistent names, entity homes, author pages, Organization/Product/Article schema where it matches visible content, and corroborating third-party profiles. Schema helps eligibility and disambiguation; it is not special AI markup. Evidence: Tier 2, Tier 6.

**6. Measurement is probabilistic.**
AI visibility changes by engine, prompt wording, location, time, personalization, and sampling. Report citations, mentions, absorption into the answer, clicks/referrals, and conversions with method notes and confidence. Never promise to "rank in ChatGPT" or guarantee AI citations. Evidence: Tier 3, Tier 7.

### Removed Claims

Do not use the following legacy claims in client-facing work:

- "Information Gain is the #1 AI ranking factor"
- "External citations create a 115%+ visibility boost"
- "Perplexity hardcodes Reddit, LinkedIn, and Wikipedia as Tier 1 trust sources"
- "Sites can expect 30-50% more AI Overview citations in 90 days"
- "`llms.txt` is a Google AI Overview ranking factor"
- "A page can be guaranteed to rank in ChatGPT, Claude, Perplexity, or Google AI Mode"

---

## 2. The AI Search Landscape

### How the Major AI Search Engines Differ

| Platform | Retrieval Method | Primary Ranking Factor | Citation Style |
|----------|------------------|------------------------|----------------|
| **Google AI Overviews** | Google Search index + Query Fan-Out | Helpful, reliable content + crawl/index eligibility | Inline cards linking to sources |
| **Google AI Mode** | Google Search index + Deep Query Fan-Out + recursive gap-filling | Topical authority, freshness, page experience | Comprehensive report with layered citations |
| **ChatGPT Search / Atlas** | OAI-SearchBot for search; ChatGPT-User for user-triggered fetches | Crawl access + clear citation-worthy pages | Summaries, snippets, links, UTM-tagged referrals |
| **Claude Search / User Fetch** | Claude-SearchBot for search quality; Claude-User for user-directed fetches | Crawl access + accessible, well-structured pages | Answers with cited or fetched source context |
| **Perplexity AI** | PerplexityBot plus partner/search index signals | Retrieval, ranking, and answer synthesis with visible source links | Numbered footnotes in answer |
| **Bing / Microsoft Copilot** | Bing index via Bingbot + generative search | Bing crawl/index eligibility + useful page structure | AI answer with source links |
| **Grok / X** | Public X posts + real-time web search when Grok chooses | X presence, public web availability, brand/entity consensus | Conversational answer with web/X context |

### Tactics That Work Across ALL Platforms

| Universal Tactic | Why It Works Everywhere |
|------------------|-------------------------|
| **Source-backed facts** | Academic GEO work and platform guidance both favor clear evidence, but effect sizes vary by engine and domain |
| **Expert quotations** | Useful when the expert, quote, and source are real, relevant, and cited inline |
| **External citations** | Help readers and systems verify claims; do not promise a fixed citation lift |
| **Answer-first formatting** | Makes passages easier to retrieve, quote, and understand when the query calls for a direct answer |
| **Eligible schema markup** | Helps rich result eligibility and entity clarity where it matches visible content |
| **Short, self-contained sentences** | Easier for people, snippets, and retrieval systems to parse |
| **Provider-specific crawl policy** | Search, user-action, and training bots are different products |
| **Accessible, server-rendered content** | Browser agents and user-triggered fetchers need visible DOM text, labels, and forms |

### Platform-Specific Differences

| Factor | Google | Perplexity | ChatGPT |
|--------|--------|------------|---------|
| **Freshness Weight** | Moderate (QRG-based) | HIGH (time decay algorithm) | Moderate |
| **Domain Authority** | Important via Knowledge Graph | Curated Trust Pool (whitelist) | Bing-inherited |
| **UGC Content** | Hidden Gems filter | Reddit/LinkedIn prioritized | Less emphasis |
| **YMYL Sensitivity** | Very High (Ray Update) | Moderate | Moderate |
| **Schema Value** | High for KG | High for FAQ extraction | Moderate |

### Provider Access Matrix

Use this matrix before any AEO, surround-sound, SEO audit, or agent-readiness work. The point is not to "allow every bot"; the point is to make a deliberate business decision per engine.

| Engine | Discovery / Search Access | User-Triggered Access | Training / Model Access | Kai Default |
|--------|---------------------------|------------------------|-------------------------|-------------|
| Google Search AI features | `Googlebot`, indexed pages, snippet eligibility | Browser agents may inspect DOM/accessibility tree | `Google-Extended` controls Gemini/Vertex AI training use, not Search ranking | Allow `Googlebot`; decide on `Google-Extended`; do not treat `llms.txt` as a Google requirement |
| ChatGPT | `OAI-SearchBot` controls ChatGPT Search discovery | `ChatGPT-User` may fetch pages for user actions; robots rules may not always apply | `GPTBot` controls potential OpenAI foundation-model training | Allow `OAI-SearchBot`; usually allow `ChatGPT-User`; decide on `GPTBot` |
| Claude | `Claude-SearchBot` supports search result quality | `Claude-User` supports user-directed retrieval | `ClaudeBot` supports Anthropic model training | Allow `Claude-SearchBot` and `Claude-User`; decide on `ClaudeBot` |
| Perplexity | `PerplexityBot` indexes pages for Perplexity answers and respects robots.txt | Perplexity says URL summarization of robots-blocked pages has been disabled to prevent misuse | Perplexity docs say PerplexityBot indexing is not foundation-model pre-training | Allow official Perplexity access where visibility is desired and verify IP ranges at WAF |
| Bing / Copilot | `bingbot` feeds Bing Search and generative Bing experiences | Browser/user agents vary by product | No separate public Copilot training token for normal web visibility | Allow `bingbot`; verify Bing Webmaster Tools |
| Grok / X | X Help says Grok may search public X posts and the real-time web | Grok product behavior is user-facing and not exposed as a stable crawler contract in X Help | X users can opt out of public/interactions data use for Grok training in X settings | Optimize public X/entity presence; monitor referrals/logs; do not hard-code a supposed Grok UA as a P0 requirement |

---

## 3. Content Optimization Checklist

### A. Information Gain and Non-Commodity Value (Evidence Tier 4)

The Information Gain patent describes a way to estimate how much additional information a document provides relative to documents already seen. Treat it as a useful lens for content gap analysis, not as a known live "AI ranking factor." The durable action is simple: publish information a serious reader could not get from the top results alone.

**PRIORITY Tactics:**

- [ ] **Audit top 10 results for your keyword** — List the facts/angles covered by ALL of them
- [ ] **Identify the "Information Gap"** — What perspectives, data, or counter-arguments are missing?
- [ ] **Add unique data points** — Original research, proprietary data, case studies nobody else has
- [ ] **Include contrarian viewpoints** — "Most experts say X, but our experience shows Y because [specific evidence]"
- [ ] **Avoid "Skyscraper" content** — Do not make a longer rewrite of the same facts
- [ ] **Name the evidence source** — Label each new claim as client data, field observation, public dataset, expert review, or hypothesis
- [ ] **Keep invented terminology useful** — Coin terms only when they clarify a real pattern; novelty theater does not help readers

**Audit output example:**

```markdown
Information gap: The top five pages explain "AI receptionist" features, but none show after-hours call handling failure modes.
Evidence we can add: 60-day call log export from CallRail, three anonymized missed-call transcripts, and a pricing comparison table.
Confidence: medium. The data proves usefulness for this client, not a universal search ranking effect.
Data gap: We do not have Google AI Overview inclusion history for this topic.
```

### B. Evidence-Rich Passage Design (Evidence Tier 3)

The GEO paper introduced a black-box framework for improving visibility in generative engine responses and reported up to 40% visibility gains in the tested setting. Use the study as directional research, not as a universal promise. Effects vary by domain, engine, query type, and baseline content quality.

**PRIORITY tactics to test:**

| Feature | Evidence Tier | Implementation |
|---------|---------------|----------------|
| **Cite external sources** | Tier 3 | Link to primary sources, official docs, academic papers, and public datasets where they support the sentence |
| **Add quotations** | Tier 3 | Use short, real expert quotes with attribution and retrieval/source notes |
| **Add statistics** | Tier 3 | Add sourced numbers only when they are current enough and relevant to the claim |
| **Use technical terms accurately** | Tier 3 / Tier 6 | Define domain terms once, then use them consistently |
| **Improve clarity** | Tier 2 / Tier 3 | Use short sentences, specific nouns, tables, and self-contained answer blocks |

**Tactics That FAILED or Had NEGATIVE Effect:**

| Failed Tactic | Why It Fails |
|---------------|--------------|
| Keyword stuffing | Semantic systems and readers both punish unnatural repetition |
| Authoritative tone alone | Confidence without evidence is not trust |
| Adding more words | More text can dilute the passage if it adds no new facts |

**Optimal Content Structure (GEO Research):**

- **Paragraph length:** 60-100 words where natural (often easier to retrieve and quote)
- **Sentence length:** 15-20 words maximum
- **Answer position:** Direct answer in first 30-50 words after H2
- **Format:** Clean HTML or Markdown-style structure preferred over complex, JS-hidden content
- **Atomic fact density:** Include verifiable facts where they serve the answer; do not stuff numbers into unsupported claims

### C. Structure for AI Parsing (Query Fan-Out)

Google's Query Fan-Out decomposes some complex queries into multiple sub-queries. Your content should satisfy the important sub-intents users genuinely need.

**PRIORITY Tactics:**

- [ ] **Use PAA to reverse-engineer sub-queries**
  ```
  1. Search your main keyword on Google
  2. Extract ALL "People Also Ask" questions (3-4 levels deep)
  3. Categorize by intent facet (Cost, Safety, Process, Alternatives, etc.)
  4. Create dedicated H2 sections for each facet
  ```

- [ ] **Header structure must match sub-queries**
  ```html
  <h1>Complete Guide to [Topic]</h1>
  <h2>What is [Topic]?</h2>          <!-- Definitional sub-query -->
  <h2>How much does [Topic] cost?</h2> <!-- Cost sub-query -->
  <h2>Is [Topic] safe?</h2>          <!-- Safety sub-query -->
  <h2>[Topic] vs [Alternative]</h2>   <!-- Comparison sub-query -->
  ```

- [ ] **Inverted Pyramid within each section**
  ```
  [H2: Question]
  [Direct answer: 2-3 sentences, 40-60 words] <-- easiest to extract and cite
  [Supporting detail paragraph 1]
  [Supporting detail paragraph 2]
  [Data/examples/quotes]
  ```

- [ ] **Hub-and-Spoke architecture decision**

  | Use Hub-and-Spoke When | Use Single Pillar When |
  |------------------------|------------------------|
  | Topic has 10+ distinct facets | Topic is narrow/focused |
  | Facets warrant 1000+ word coverage each | Sub-topics need <500 words each |
  | Competing for high-volume head terms | Targeting long-tail only |
  | Building topical authority domain-wide | Creating single landing page |

**Eligible Schema Markup:**

Use schema only when it matches visible page content and a real Search feature. Google does not require special AI schema for generative Search.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "How much does [Topic] cost?",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "The average cost of [Topic] is $X-Y based on [source]..."
    }
  }]
}
```

### D. E-E-A-T Signals (QRG Research)

The January 2025 QRG update explicitly targets AI-generated content. "Experience" is the anti-AI signal.

**PRIORITY: Demonstrating "Experience" (The Human Moat)**

- [ ] **Original photos** — Not stock, not AI-generated. Show the product in use, the location visited
- [ ] **First-person specifics** — "The button was stiff when my hands were wet" (AI can't know this)
- [ ] **Proprietary data** — Internal research, customer surveys, A/B test results
- [ ] **Contrarian opinions with evidence** — "Unlike popular advice, we found X because [specific case]"
- [ ] **Author byline with verifiable history** — LinkedIn, other publications, speaking engagements

**What Triggers "Lowest Quality" Rating (Section 4.6.6):**

> "The Lowest rating applies if all or almost all of the MC is copied, paraphrased, embedded, auto or AI generated with **little to no effort, little to no originality, and little to no added value**."

Triggers:
- [ ] ❌ Phrases like "As an AI language model"
- [ ] ❌ Obvious hallucinations or factual errors
- [ ] ❌ Scaled content patterns (thousands of similar pages)
- [ ] ❌ No human editing evidence
- [ ] ❌ Zero unique data or perspective
- [ ] ❌ Fake author profiles

**How to Demonstrate E-E-A-T for AI-Assisted Content:**

| Component | Evidence Required |
|-----------|-------------------|
| **Experience** | Original photos, personal anecdotes with specific details, case studies |
| **Expertise** | Author credentials, "Reviewed by [Expert]" for YMYL, accurate technical terminology |
| **Authoritativeness** | Citations FROM other authorities, Knowledge Graph presence, brand mentions |
| **Trustworthiness** | Zero factual errors, transparent AI disclosure, primary sources cited |

---

## 4. Platform-Specific Tactics

### A. Google AI Overviews

**Official Google Search baseline (verified 2026-05-16):**
Google's generative AI features use the same public, crawlable Search systems that already process pages for Google Search. To appear, pages must be crawlable, indexable, and eligible for snippets. Google explicitly says site owners do not need `llms.txt`, special AI markup, AI-only Markdown files, forced content chunking, long-tail rewrites, inauthentic mentions, or special schema for generative AI Search. Keep normal technical SEO, helpful people-first content, media quality, local/ecommerce feeds, and page experience strong.

**The "Ray Update" Reality:**
Following the May 2024 AIO launch failures (glue on pizza, etc.), Google implemented significant tightening:
- AIOs reduced dramatically for YMYL queries
- Citations now heavily weighted toward Knowledge Graph entities
- Brand authority required for YMYL citation

**Optimization Tactics:**

1. **Target Featured Snippet position first**
   - John Mueller (Jan 2025): "Think about AI Overviews the same way SEOs optimize for featured snippets"
   - Win the snippet → likely to be cited in AIO

2. **Cover important Query Fan-Out sub-topics**
   - Use fan-out as a research model, not a doorway-page factory
   - Google warns against creating separate content for every query variation primarily to manipulate generative AI responses
   ```
   User query: "Compare iPhone 15 vs Pixel 8"

   Fan-out generates:
   - "iPhone 15 battery life test"
   - "Pixel 8 battery life test"
   - "iPhone 15 charging speed"
   - "Pixel 8 charging speed"
   - "iPhone 15 camera comparison"
   - "Pixel 8 camera comparison"
   - "iPhone 15 price"
   - "Pixel 8 price"

   -> Your page should satisfy the important facets users actually need
   ```

3. **YMYL Strategy:**
   - For medical/financial/legal: MUST have expert review visible
   - "Medically reviewed by Dr. [Name], [Credentials]"
   - Link author to Knowledge Graph entity (Wikidata, LinkedIn)

4. **Build Knowledge Graph presence** (see Section 5)

### B. Perplexity AI

**Architecture Understanding:**
- PerplexityBot indexes pages for Perplexity answers and, per Perplexity's help docs, respects robots.txt
- Perplexity says allowing PerplexityBot does not put content into foundation-model pre-training
- Treat claims about specific rerankers, hardcoded trust pools, or source whitelists as practitioner hypotheses unless Perplexity publishes them

**Optimization Tactics:**

1. **Make passages extractable**
   - Place direct answer immediately after H1/H2
   - High atomic fact density (2-3 facts per paragraph)
   - Zero fluff, zero marketing language
   - Avoid: "In today's fast-paced world..." (instant penalty)

2. **Earn third-party corroboration**

   | Source type | Acceptable use | Disallowed use |
   |-------------|----------------|----------------|
   | Wikipedia / Wikidata | Create or update only when notability and sourcing rules are met | Promotional entries, self-serving edits, paid undisclosed editing |
   | Reddit / forums | Participate with disclosure and useful answers where community rules allow it | Seeding fake consensus, bought accounts, coordinated voting |
   | LinkedIn / GitHub / Stack Overflow | Publish real expertise, docs, code, or analysis under the right identity | Thin reposts made only to bait citations |
   | .gov / .edu / standards bodies | Cite primary evidence | Misrepresenting endorsement |

   **Tactic:** Build durable, disclosed authority in the places your market already trusts. Do not create off-site content only to manipulate citations.

3. **Freshness matters by topic**
   - Update volatile content when facts change, not on an arbitrary weekly schedule
   - Show `dateModified` and explain material changes
   - Archive stale claims and list missing source data instead of backfilling guesses

4. **Optimize for "Related Questions"**
   - Search your keyword on Perplexity
   - Note the "Related Questions" generated
   - Create FAQ sections answering these exact questions

5. **Technical requirements**
   ```
   robots.txt:
   User-agent: PerplexityBot
   Allow: /

   User-agent: Perplexity-User
   Allow: /
   ```

### C. ChatGPT/Bing (GPT Search/Browsing)

**Key Distinction:**
- `OAI-SearchBot` = ChatGPT Search discovery and automatic crawl control
- `GPTBot` = OpenAI foundation-model training crawler; allow or block based on the client's training-data policy
- `ChatGPT-User` = user-triggered retrieval for ChatGPT and Custom GPTs; OpenAI says robots.txt may not apply because a user initiated the action and that this bot does not determine Search inclusion

**Optimization Tactics:**

1. **Allow the right crawler:** Use `OAI-SearchBot` policy for ChatGPT Search inclusion decisions
2. **Make answers self-contained:** Define terms, include dates, and connect claims to sources so a fetched passage can stand alone
3. **Measure separately:** Track ChatGPT referrals, cited URLs, brand mentions, and answer absorption separately from Google and Bing

**robots.txt Configuration:**
```
User-agent: GPTBot
Disallow: /     # Example: block training if the client chooses that policy

User-agent: ChatGPT-User
Allow: /        # Allow user-triggered retrieval where visibility matters

User-agent: OAI-SearchBot
Allow: /        # Allow SearchGPT indexing
```

---

## 5. Entity Building Protocol

### Step 1: Create the Entity Home

The "Entity Home" is the single page Google uses for entity reconciliation.

**Requirements:**
- [ ] Dedicated URL: `yoursite.com/about/[entity-name]` or `yoursite.com/about`
- [ ] Contains ALL facts you want Google to know
- [ ] Comprehensive Schema markup (see code below)
- [ ] Links OUT to corroborating sources (Wikidata, LinkedIn, Crunchbase)
- [ ] Receives links FROM those same sources (bidirectional confirmation)

**Schema.org Code Template:**

```json
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://yoursite.com/#organization",
      "name": "Your Company Name",
      "url": "https://yoursite.com",
      "logo": "https://yoursite.com/logo.png",
      "description": "One sentence description matching Wikidata",
      "sameAs": [
        "https://www.wikidata.org/wiki/Q[YOUR_QID]",
        "https://www.linkedin.com/company/your-company",
        "https://twitter.com/yourcompany",
        "https://www.crunchbase.com/organization/your-company"
      ],
      "founder": {
        "@type": "Person",
        "@id": "https://yoursite.com/#founder",
        "name": "Founder Name",
        "sameAs": [
          "https://www.linkedin.com/in/founder",
          "https://www.wikidata.org/wiki/Q[FOUNDER_QID]"
        ],
        "knowsAbout": [
          "Topic 1",
          "Topic 2",
          "Your Industry"
        ]
      }
    },
    {
      "@type": "WebPage",
      "@id": "https://yoursite.com/about/#webpage",
      "url": "https://yoursite.com/about/",
      "name": "About Your Company",
      "about": { "@id": "https://yoursite.com/#organization" },
      "mentions": [
        {
          "@type": "Thing",
          "name": "Your Industry Topic",
          "sameAs": "https://en.wikipedia.org/wiki/Your_Industry"
        }
      ]
    }
  ]
}
</script>
```

### Step 2: Wikidata Submission

Wikidata feeds Google's Knowledge Graph directly. Lower barrier than Wikipedia.

**Checklist:**
- [ ] Verify notability: Does entity meet [Wikidata notability criteria](https://www.wikidata.org/wiki/Wikidata:Notability)?
- [ ] Create account (4 days + 50 edits needed for bulk tools)
- [ ] Search to ensure no duplicate exists
- [ ] Create item with:
  - **Label:** Entity name
  - **Description:** Concise disambiguation (e.g., "American software company founded in 2020")
  - **Aliases:** Alternative names, abbreviations
- [ ] Add statements:
  - `instance of` (P31): e.g., "business" or "human"
  - `official website` (P856): Link to Entity Home
  - `occupation` (P106): For people
  - `industry` (P452): For companies
- [ ] Add REFERENCES for each statement (third-party sources, not your own site)

**SPARQL Query to Check Entity Status:**
```sparql
SELECT ?item ?itemLabel WHERE {
  ?item rdfs:label "Your Company Name"@en .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
```

### Step 3: Build Corroborative Nodes

Create consistent profiles on high-trust databases:

| Platform | Priority | Purpose |
|----------|----------|---------|
| LinkedIn (Company/Person) | HIGH | Trust Pool source, feeds KG |
| Crunchbase | HIGH | Business entity validation |
| Wikipedia (if notable) | HIGHEST | Strong corroborating entity source when notability and sourcing rules are met |
| EverybodyWiki | MEDIUM | Alternative for non-notable entities |
| Google Business Profile | HIGH (Local) | Local entity recognition |
| Industry directories | MEDIUM | Domain-specific authority |

**Critical: N.A.P. + D Consistency**
Name, Address, Phone, and Description must be IDENTICAL across all profiles.

### Step 4: Timeline Expectations

| Milestone | Expected Timeline |
|-----------|-------------------|
| Entity Home indexed | 1-2 weeks |
| Schema recognized | 2-4 weeks |
| Wikidata item live | 1-3 weeks |
| Knowledge Panel trigger | 3 weeks - 3 months |
| LLM training data inclusion | 6-12 months (training cutoff) |

---

## 6. Technical Implementation

### A. robots.txt Configuration

**Strategy: Allow search/retrieval, decide separately on training**

```
# robots.txt - Allow discovery/retrieval, decide separately on training

User-agent: *
Allow: /

# ============ BLOCK TRAINING CRAWLERS ============

# OpenAI Training
User-agent: GPTBot
Disallow: /

# Anthropic Training
User-agent: ClaudeBot
Disallow: /

# Google Training (Control Token)
User-agent: Google-Extended
Disallow: /

# Common Crawl (Base dataset for Llama, etc.)
User-agent: CCBot
Disallow: /

# ByteDance (TikTok/Doubao)
User-agent: Bytespider
Disallow: /

# Meta Training
User-agent: Meta-ExternalAgent
Disallow: /

# Apple Training
User-agent: Applebot-Extended
Disallow: /

# ============ ALLOW SEARCH / RETRIEVAL AGENTS ============

# Google Search (required for Google Search + AI Overviews / AI Mode)
User-agent: Googlebot
Allow: /

# Bing Search (feeds Bing and Microsoft Copilot search experiences)
User-agent: bingbot
Allow: /

# OpenAI Search (ChatGPT Search)
User-agent: OAI-SearchBot
Allow: /

# OpenAI user-triggered fetches
User-agent: ChatGPT-User
Allow: /

# Anthropic Search / Retrieval
User-agent: Claude-SearchBot
Allow: /
User-agent: Claude-User
Allow: /

# Perplexity Search / Retrieval
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /

# Sitemap
Sitemap: https://yoursite.com/sitemap.xml
```

**Notes:**
- `Google-Extended` is not a replacement for `Googlebot`; blocking `Googlebot` removes Google Search visibility, including Google generative Search features.
- `ChatGPT-User`, `Claude-User`, and `Perplexity-User` represent user-triggered fetches. Robots behavior can differ from automatic crawlers, so pair robots rules with WAF/IP allowlists and log monitoring.
- Do not add a required Grok/X user-agent rule unless xAI publishes an official crawler contract. Treat Grok as an observability and public-entity problem until then.

### B. llms.txt and Markdown Entry Points

Create `/llms.txt` to guide cooperative AI agents to your best content. Do not sell or score it as a Google AI Overview ranking requirement: Google says `llms.txt` and other special AI text files are not needed for Google generative AI Search. It remains useful for agents and tools that choose to read it, including docs-oriented crawlers, internal assistants, MCP clients, and AI browsers.

**File Format:**

```markdown
# Your Site Name

> One sentence description of what your site does and its authority.

Additional context about the site, target audience, or usage notes.

## Documentation
- [Main Topic Guide](https://yoursite.com/guide/): Comprehensive guide to [topic]
- [API Reference](https://yoursite.com/api/): Technical documentation

## Key Articles
- [Most Important Article](https://yoursite.com/article1/): Description of content
- [Second Article](https://yoursite.com/article2/): Description

## Optional
- [Less Critical Content](https://yoursite.com/other/): Can be skipped if context limited
```

**Also consider:**
- `/llms-full.txt` - concatenated full text of all key pages for cooperative agents
- `.md` versions of HTML pages (e.g., `/article.html.md`) when your audience includes developers, API users, or agentic workflows
- an internal ownership note that says which systems consume the file and how often it is regenerated

### C. Server-Side Optimization

| Requirement | Target | Why |
|-------------|--------|-----|
| TTFB (Time to First Byte) | < 200ms | RAG systems have retrieval timeouts |
| Full page load | < 1 second | Perplexity may abandon slow pages |
| JavaScript rendering | SSR preferred | AI crawlers have JS limitations |
| Mobile-first | Required | Google's primary index |

### D. Multi-Engine Agent-Readiness Audit (run this before shipping any AEO content)

Config alone is not enough. The site has to pass an audit for search engines, AI search products, and browser agents to actually use it. The **agent-readiness checklist** turns the technical configuration above into a scored audit covering provider-specific crawler access, robots decisions, optional `llms.txt`, markdown mirrors, JS-gating, capability signaling, schema, accessibility, WAF/IP allowlists, and token cost.

**Rubric:** `knowledge/checklists/agent-readiness-checklist.md`

**Scoring:**
- Pass: all P0 items + 80% of P1
- Partial: all P0 items + 50% of P1
- Fail: any P0 missing

**Automation:**
```bash
python scripts/quality_gates/agent_readiness_lint.py https://<your-domain>
```

Any P0 regression should block a deploy. Wire the linter into CI alongside `seo_lint.py` and `four_us_score.py`.

**When to run the audit:**
- Before starting any AEO content production (baseline)
- Before starting a `kai-surround-sound` engagement (Month 0 gate)
- On every production deploy (regression check)
- Monthly audit against the rubric (drift check)

---

## 7. Content Quality Gate

### Pre-Publish Checklist

Score each piece 1-5 (target: 35+/50 total)

| Dimension | Question | Score |
|-----------|----------|-------|
| **Information Gain** | Does this contain data/perspectives NOT in top 10 results? | /5 |
| **Unique** (Four U's) | Can only WE write this? | /5 |
| **Useful** (Four U's) | Can reader take immediate action? | /5 |
| **Ultra-specific** (Four U's) | Are there numbers, names, specific examples? | /5 |
| **Urgent** (Four U's) | Is there reason to read TODAY? | /5 |
| **Citations** (GEO) | Are external sources cited with links? | /5 |
| **Statistics** (GEO) | Does it include quantitative data? | /5 |
| **Quotes** (GEO) | Are expert quotes included? | /5 |
| **Experience** (E-E-A-T) | Is there original photos/first-person specifics? | /5 |
| **Structure** (AI) | H2s match sub-queries? Answer-first format? | /5 |

### Disqualifying Red Flags (Automatic Fail)

- [ ] Opens with "In today's fast-paced world..." or similar AI cliche
- [ ] Contains "As an AI language model" or obvious hallucinations
- [ ] No unique data or perspective vs. competitors
- [ ] No author byline or fake author
- [ ] Generic stock photos only
- [ ] Word count padding without information density
- [ ] Zero external citations

---

## 8. Measurement & Iteration

### Measurement Rules

AI visibility is sampled and volatile. Single-run tests are useful for discovery, not for executive reporting. The March 2026 uncertainty paper argues that citation metrics should be treated as sample estimates from an underlying response distribution. Report method, date range, engine, prompt set, location/device where relevant, sample count, and confidence.

**Measure four outcomes separately:**

| Outcome | What it answers | Sources |
|---------|-----------------|---------|
| Citation selection | "Was our URL shown as a source?" | Bing AI Performance, third-party AI visibility tools, manual screenshots |
| Citation absorption | "Did our page shape the actual answer?" | Answer comparison, quoted phrases, facts reused from page |
| Referral behavior | "Did users click or arrive from AI products?" | Analytics referrers, UTM data, server logs |
| Business impact | "Did AI discovery create pipeline, leads, sales, or subscribers?" | CRM, call tracking, ecommerce, form attribution with caveats |

**Minimum reporting protocol:**

1. Build a prompt/query set with branded, category, comparison, problem, local, and long-tail tasks.
2. Run each prompt at least 5-10 times per engine across multiple days for directional reporting.
3. Record engine, account state, location, date, device/browser, prompt, answer, citations, and screenshots.
4. Use confidence labels: high when repeated samples agree, medium when trends agree but citations vary, low when based on one-off observations.
5. Separate Google AI Overview / AI Mode observations from Bing/Copilot, ChatGPT, Claude, Perplexity, and Grok.
6. Put absent metrics in `_data-gaps.md`; do not infer AI visibility from rank tracking alone.

### Tracking AI Citation Appearance

**Tools and data sources:**
- [ ] **Google Search Console:** Query/page impressions, clicks, CTR, indexing, and snippet eligibility. Google does not provide a universal AI Overview-only Search Console report.
- [ ] **Bing Webmaster Tools AI Performance:** Citation counts, cited pages, grounding queries, and trend data for supported AI surfaces.
- [ ] **InLinks / entity tools:** Entity graph diagnostics and schema/entity gap checks.
- [ ] **Google Knowledge Graph API:** Entity presence checks; do not treat `resultScore` as an AI ranking score.
- [ ] **Manual Perplexity/ChatGPT/Claude/Grok testing:** Record repeated samples, not one-off wins.

**Data-gap language for reports:**

```markdown
Data gap: We did not have Bing Webmaster Tools AI Performance access for this audit. We cannot claim citation frequency in Copilot or Bing AI answers.
Data gap: Google Search Console does not expose a universal AI Overview-only report. We used Search Console page/query data plus dated screenshots as supporting evidence.
Data gap: ChatGPT and Claude outputs were sampled manually across 12 prompts on 2026-05-17. Treat the result as directional because answer generation is non-deterministic.
```

**Google KG API Query (Python):**
```python
import requests

API_KEY = "YOUR_API_KEY"
query = "Your Entity Name"
url = f"https://kgsearch.googleapis.com/v1/entities:search?query={query}&key={API_KEY}&limit=1"

response = requests.get(url).json()
if response.get('itemListElement'):
    result = response['itemListElement'][0]
    print(f"Entity ID: {result['result'].get('@id')}")
    print(f"Result Score: {result.get('resultScore')}")
else:
    print("Entity not found in Knowledge Graph")
```

### Experiment Framework

| Test Variable | Measurement |
|---------------|-------------|
| Add sourced statistics to existing page | Monitor citation selection, answer absorption, organic query/page metrics, and conversions |
| Add expert review or quote | Monitor trust-sensitive queries and answer language reuse |
| Rewrite H2s to match real facets | Monitor snippet capture, AI citations, engagement, and internal search behavior |
| Add valid schema matching visible content | Monitor rich result eligibility, Search Console enhancements, and entity clarity |
| Improve entity home and sameAs graph | Monitor Knowledge Graph presence, branded answer accuracy, and third-party profile consistency |

---

## 9. Failure Modes & Competitive Edges

### 10 Patterns To Watch

1. **"Little to no effort" is the death sentence** (QRG 4.6.6)
   - Even AI-assisted content survives if human effort is evident
   - The standard is "significant effort" — show your work

2. **Information Gain is a hypothesis lens, not a client promise**
   - Use it to find missing evidence and original perspective
   - Do not claim a measurable ranking boost without internal measurement

3. **Third-party sources matter only when they are legitimate**
   - Earned reviews, standards pages, docs, public datasets, and expert discussion can help corroboration
   - Astroturfing, bought accounts, and fake consensus are disallowed tactics

4. **Query Fan-Out triggers "gap-filling" re-queries** (Google I/O 2025)
   - Cover important facets where they help the reader
   - Do not create doorway pages for every possible fan-out query

5. **"Experience" is the only anti-AI moat in E-E-A-T**
   - Original photos with EXIF data
   - First-person specifics AI couldn't generate
   - Case studies with real client names (with permission)

6. **Low information density weakens extractability**
   - Long intros, generic claims, and vague comparisons make passages harder to reuse
   - Put the answer before context where the query calls for it

7. **Wikidata is not a shortcut around notability**
   - Use Wikidata only when the entity meets Wikidata rules and has reliable references
   - Schema `sameAs` should point to real, maintained profiles

8. **PAA questions 3-4 levels deep reveal long-tail fan-out**
   - Click PAA → new PAA appears
   - These deeper questions = AI Mode recursive sub-queries

9. **`Google-Extended` is NOT a user agent string**
   - It's a robots.txt token only
   - Cannot be blocked via WAF — must use robots.txt

10. **Training vs. Retrieval split is industry-wide**
    - Block `GPTBot` but allow `ChatGPT-User`
    - Your content in AI answers, NOT in training data

---

## 10. 30-Day Implementation Roadmap

### Week 1: Audit & Technical Setup

| Day | Task | Output |
|-----|------|--------|
| 1-2 | Audit top 5 pages for Information Gain gaps | Gap analysis document |
| 3 | Implement provider-specific robots.txt configuration | Updated robots.txt + decision log |
| 4 | Publish optional llms.txt and verify WAF/IP allowlists | /llms.txt live + crawler access notes |
| 5-6 | Audit Schema markup, add missing `sameAs` links | Schema updated |
| 7 | Set up monitoring (KG API, AI Overview tracking) | Dashboard/alerts |

### Week 2: Entity Building

| Day | Task | Output |
|-----|------|--------|
| 8-9 | Create/update Entity Home page | Dedicated About page |
| 10-11 | Submit to Wikidata (if notable) | Wikidata item |
| 12 | Create/update LinkedIn, Crunchbase profiles | Consistent NAP+D |
| 13-14 | Author page optimization with Person schema | Author pages live |

### Week 3: Content Restructuring

| Day | Task | Output |
|-----|------|--------|
| 15-16 | Mine PAA 3 levels deep for top 5 keywords | Sub-query map |
| 17-18 | Restructure 2 pillar pages (H2s match sub-queries) | Updated pages |
| 19-20 | Add citations, statistics, quotes to 3 pages | GEO-optimized content |
| 21 | Add "Experience" evidence (photos, first-person) | Human signals added |

### Week 4: Measurement & Iteration

| Day | Task | Output |
|-----|------|--------|
| 22-23 | Baseline measurement (AI Overview presence, KG score) | Benchmark report |
| 24-25 | A/B test: Add statistics to 2 underperforming pages | Test running |
| 26-27 | Create 1 Hub-and-Spoke cluster for new topic | Content cluster live |
| 28 | Query Perplexity/ChatGPT for target topics, document citations | Citation audit |
| 29-30 | Review results, prioritize next 30 days | Iteration plan |

---

## Appendix: Quick Reference Cards

### GEO Citation Triggers

| Add This | Expected Effect |
|----------|-----------------|
| External citations | Better verifiability and reader trust; test citation impact by engine |
| Expert quotes | Stronger experience/expertise signal when real and relevant |
| Statistics | More extractable evidence when current, sourced, and material |
| Technical terms | Better entity clarity when natural and useful |

### Information Gain Checklist

- [ ] Unique data not in top 10?
- [ ] Contrarian perspective with evidence?
- [ ] Original research/case study?
- [ ] New terminology or framework?

### Experience Evidence (Anti-AI)

- [ ] Original photos (not stock)
- [ ] First-person specifics
- [ ] Real client names/case studies
- [ ] Author with verifiable history

### Platform Priority by Content Type

| Content Type | Primary Target | Secondary |
|--------------|----------------|-----------|
| News/current events | Google AI Mode | Perplexity |
| Technical docs | Perplexity | ChatGPT |
| Local business | Google AI Overview | N/A |
| Research/data | Perplexity | Google |
| How-to/tutorial | Google AI Overview | ChatGPT |
| Product comparison | Google AI Overview | Perplexity |

---

## Sources & Research Files

This playbook synthesizes findings from:

1. `aeo-ai-search-strategies-2026.md` — Google I/O announcements, Mueller quotes
2. `patent-information-gain-US12013887B2.md` — Patent mechanics, word2vec, novelty scoring
3. `geo-academic-research-synthesis.md` — GEO paper and directional visibility experiments
4. `perplexity-ranking-reverse-engineered.md` — L3 Reranker, Trust Pool, Vespa.ai
5. `entity-seo-knowledge-graph-deep-dive.md` — Entity Home, Wikidata, Schema examples
6. `quality-rater-guidelines-deep-analysis.md` — QRG 4.6.x, Ray Update, Experience signal
7. `ai-crawlers-technical-reference.md` — crawler user agents, provider policy, optional llms.txt
8. `query-fan-out-guide.md` — Query decomposition, PAA optimization
9. [Google Search Central: AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) — official guidance on Google generative AI Search, `llms.txt`, chunking, and agentic experiences
10. [OpenAI Crawlers documentation](https://developers.openai.com/api/docs/bots) — `OAI-SearchBot`, `GPTBot`, `ChatGPT-User`
11. [Anthropic crawler documentation](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) — `ClaudeBot`, `Claude-User`, `Claude-SearchBot`
12. [Perplexity robots.txt guidance](https://www.perplexity.ai/help-center/en/articles/10354969-how-does-perplexity-follow-robots-txt) and [Perplexity Crawlers documentation](https://docs.perplexity.ai/docs/resources/perplexity-crawlers) — `PerplexityBot`, robots behavior, official IP endpoints
13. [X Help: About Grok](https://help.x.com/en/using-x/about-grok) — Grok real-time web search and X public-post usage
14. [Bing Webmaster Tools AI Performance](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview) — Microsoft AI citation reporting and grounding query data
15. [Microsoft Advertising: optimizing content for AI search answers](https://about.ads.microsoft.com/en/blog/post/october-2025/optimizing-your-content-for-inclusion-in-ai-search-answers) — Bing/Copilot passage structure guidance
16. [web.dev: Build agent-friendly websites](https://web.dev/articles/ai-agent-site-ux) — browser-agent UX, DOM, and accessibility-tree considerations
17. [arXiv: Quantifying Uncertainty in AI Visibility](https://arxiv.org/abs/2603.08924) — repeated-sampling and confidence interval guidance
18. [arXiv: From Citation Selection to Citation Absorption](https://arxiv.org/abs/2604.25707) — measurement framework for citation selection vs answer absorption

External sources retrieved: 2026-05-17.

---

*Last updated: 2026-05-17*
