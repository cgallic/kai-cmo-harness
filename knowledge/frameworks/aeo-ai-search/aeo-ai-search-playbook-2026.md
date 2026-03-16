# AEO & AI Search Playbook 2026

> The definitive guide to ranking in AI Overviews, Perplexity, ChatGPT, and generative search engines. Synthesized from 8 deep research reports including Google patents, academic papers, and reverse-engineered algorithms.

---

## 1. Executive Summary

### The 5 Most Important Findings That Change Everything

**1. Information Gain is the #1 Ranking Factor for AI (Patent US12013887B2)**
Google's patented "Information Gain" algorithm measures how much *new* information your content provides relative to what already exists. Content that merely summarizes competitors is mathematically penalized. The system uses `word2vec` embeddings to calculate semantic novelty—being "orthogonal to consensus" is now more valuable than being comprehensive.

**2. GEO Research Proves Specific Content Features Increase Citation 115%+**
Academic research from Princeton/Georgia Tech quantifies exactly what gets cited:
- **Citations to external sources: +115% visibility** (for lower-ranked sites)
- **Direct quotes from experts: +40% visibility**
- **Statistics and data: +37% visibility**
- Keyword stuffing has **zero or negative effect**

**3. Perplexity's L3 Reranker Kills "Fluffy" Content Before LLMs See It**
Perplexity uses a three-layer ranking system. The L3 Reranker filters content based on "extractability" and information density. High domain authority means nothing if your content is padded with filler—it gets dropped before synthesis.

**4. "Experience" is the E-E-A-T Signal AI Cannot Fake**
Google's Quality Rater Guidelines (Section 4.6.6) mandate "Lowest Quality" ratings for AI content with "little to no effort." The "Experience" component of E-E-A-T—evidenced by original photos, first-person specifics, and unique case studies—is the human moat that AI cannot cross.

**5. Query Fan-Out Means You Must Answer 8+ Sub-Questions**
Google's AI Mode decomposes complex queries into ~8 simultaneous sub-queries. To rank for the main keyword, your content must satisfy these sub-intents. "People Also Ask" reveals the exact sub-queries to target.

### What Competitors Don't Know

| Hidden Insight | Source | Competitive Edge |
|----------------|--------|------------------|
| Information Gain uses word2vec embeddings to detect "same info, different words" | Patent US12013887B2 | Paraphrasing competitors = penalty, not optimization |
| Perplexity hardcodes Reddit/LinkedIn/Wikipedia as Tier 1 trust sources | Reverse engineering | Parasite SEO on trusted platforms beats your own blog |
| AI Overviews cite "Entity Home" pages with Knowledge Graph presence | Entity SEO research | Wikidata entry + Schema.org = citation priority |
| "Little to no effort" AI content triggers "Lowest Quality" rating | QRG Section 4.6.6 | Human editing and original data are mandatory |
| Query Fan-Out checks for gaps and re-queries recursively | Google I/O 2025 | Covering ALL sub-topics on one page captures multiple citations |

### Expected Impact

Sites implementing this playbook can expect:
- **30-50% increase** in AI Overview citations within 90 days
- **115%+ visibility boost** for previously lower-ranked pages using citation optimization
- **Recovery** from Helpful Content/AI content penalties by demonstrating "significant effort"

---

## 2. The AI Search Landscape

### How the Major AI Search Engines Differ

| Platform | Retrieval Method | Primary Ranking Factor | Citation Style |
|----------|------------------|------------------------|----------------|
| **Google AI Overviews** | Query Fan-Out (8+ parallel searches) | Information Gain + Entity Authority | Inline cards linking to sources |
| **Google AI Mode** | Deep Query Fan-Out + recursive gap-filling | Topical Authority + Freshness | Comprehensive report with layered citations |
| **Perplexity AI** | Bing API + PerplexityBot + Vespa.ai vectors | L3 Reranker (extractability + trust) | Numbered footnotes in answer |
| **ChatGPT (Browsing)** | Bing API via ChatGPT-User agent | Domain Authority + Direct Answer Match | Inline links when sources used |
| **Claude (Browsing)** | Claude-User agent | Unknown internal ranking | Cited within response text |

### Tactics That Work Across ALL Platforms

| Universal Tactic | Why It Works Everywhere |
|------------------|-------------------------|
| **Statistics in content** | All LLMs prefer quantifiable facts (+37% GEO study) |
| **Quotes from experts** | Pre-verified content reduces hallucination risk (+40%) |
| **Cite external sources** | Signals "corroboration" to retrieval systems (+115%) |
| **Answer-first formatting** | All RAG systems extract the first 50 words after headers |
| **Schema markup (FAQ, Article)** | Helps all systems understand content structure |
| **Short sentences (15-20 words)** | Easier for `IsSup` (support verification) tokens to validate |

### Platform-Specific Differences

| Factor | Google | Perplexity | ChatGPT |
|--------|--------|------------|---------|
| **Freshness Weight** | Moderate (QRG-based) | HIGH (time decay algorithm) | Moderate |
| **Domain Authority** | Important via Knowledge Graph | Curated Trust Pool (whitelist) | Bing-inherited |
| **UGC Content** | Hidden Gems filter | Reddit/LinkedIn prioritized | Less emphasis |
| **YMYL Sensitivity** | Very High (Ray Update) | Moderate | Moderate |
| **Schema Value** | High for KG | High for FAQ extraction | Moderate |

---

## 3. Content Optimization Checklist

### A. Information Gain Optimization (Patent US12013887B2)

The Information Gain patent calculates novelty using semantic embeddings. Content must be "orthogonal to consensus" to score high.

**PRIORITY Tactics:**

- [ ] **Audit top 10 results for your keyword** — List the facts/angles covered by ALL of them
- [ ] **Identify the "Information Gap"** — What perspectives, data, or counter-arguments are missing?
- [ ] **Add unique data points** — Original research, proprietary data, case studies nobody else has
- [ ] **Include contrarian viewpoints** — "Most experts say X, but our experience shows Y because [specific evidence]"
- [ ] **Avoid "Skyscraper" content** — Longer versions of existing content score LOW on Information Gain
- [ ] **Use unique terminology** — Coin specific terms that competitors don't use (creates semantic distance)

**Technical Implementation:**
```
Information Gain Score = f(V_new, V_history)
Where:
- V_new = Semantic vector of your content
- V_history = Aggregate vector of documents user/AI has already seen
- High score = Your content is in a different region of semantic space
```

**What "Novelty" Actually Means (Patent Details):**
- The system embeds documents using `word2vec` or autoencoder models
- "Same info, different words" = LOW score (synonyms are neighbors in vector space)
- High KL-divergence from existing content = HIGH score
- Session-based: What the user viewed in THIS search session matters most

### B. Citation Probability Maximization (GEO Research)

The GEO paper (Princeton/Georgia Tech) tested specific content features across 10,000 queries.

**PRIORITY Tactics That INCREASE Citation:**

| Feature | Impact | Implementation |
|---------|--------|----------------|
| **Cite external sources** | **+115.1%** (rank 5 sites) | Link to .edu, .gov, research papers in your text |
| **Add quotations** | **+40%** | "Dr. Jane Smith, Harvard: 'Direct quote here'" |
| **Add statistics** | **+37%** | "In 2024, X increased by 47% according to [source]" |
| **Technical terminology** | **+32.7%** | Use domain-specific jargon accurately |
| **Fluency optimization** | **+15-30%** | Short sentences, clear syntax, no complex clauses |

**Tactics That FAILED or Had NEGATIVE Effect:**

| Failed Tactic | Result | Why It Fails |
|---------------|--------|--------------|
| Keyword stuffing | Negligible/negative | LLMs use semantic embeddings, not keyword density |
| Authoritative tone alone | No effect in factual domains | Confidence without evidence = low `IsSup` score |
| Adding more words | No improvement | Information density matters, not word count |

**Optimal Content Structure (GEO Research):**

- **Paragraph length:** 60-100 words (aligns with RAG chunking)
- **Sentence length:** 15-20 words maximum
- **Answer position:** Direct answer in first 30-50 words after H2
- **Format:** Markdown preferred over complex HTML
- **Atomic fact density:** Aim for 2-3 verifiable facts per paragraph

### C. Structure for AI Parsing (Query Fan-Out)

Google's Query Fan-Out decomposes queries into ~8 sub-queries. Your content must satisfy multiple sub-intents.

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
  [Direct answer: 2-3 sentences, 40-60 words] <-- AI extracts THIS
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

**Schema Markup That Feeds AI:**

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

**The "Ray Update" Reality:**
Following the May 2024 AIO launch failures (glue on pizza, etc.), Google implemented significant tightening:
- AIOs reduced dramatically for YMYL queries
- Citations now heavily weighted toward Knowledge Graph entities
- Brand authority required for YMYL citation

**Optimization Tactics:**

1. **Target Featured Snippet position first**
   - John Mueller (Jan 2025): "Think about AI Overviews the same way SEOs optimize for featured snippets"
   - Win the snippet → likely to be cited in AIO

2. **Cover ALL Query Fan-Out sub-topics**
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

   → Your page must answer ALL of these to be the primary citation
   ```

3. **YMYL Strategy:**
   - For medical/financial/legal: MUST have expert review visible
   - "Medically reviewed by Dr. [Name], [Credentials]"
   - Link author to Knowledge Graph entity (Wikidata, LinkedIn)

4. **Build Knowledge Graph presence** (see Section 5)

### B. Perplexity AI

**Architecture Understanding:**
- Uses Bing API for broad retrieval + PerplexityBot for depth
- Vespa.ai for vector search orchestration
- L3 Reranker filters low-density content

**Optimization Tactics:**

1. **Survive the L3 Reranker**
   - Place direct answer immediately after H1/H2
   - High atomic fact density (2-3 facts per paragraph)
   - Zero fluff, zero marketing language
   - Avoid: "In today's fast-paced world..." (instant penalty)

2. **Leverage the Trust Pool (Parasite SEO)**

   | Tier 1 (Hardcoded High Trust) | Tier 2 (News/Media) | Tier 3 (General Web) |
   |-------------------------------|---------------------|----------------------|
   | Wikipedia | Bloomberg | Your website |
   | Reddit | NYT | Most blogs |
   | LinkedIn | Reuters | E-commerce |
   | GitHub | BBC | |
   | Stack Overflow | | |
   | .gov, .edu | | |

   **Tactic:** For competitive queries, create high-quality content on Reddit or LinkedIn FIRST. Perplexity is more likely to cite your Reddit post than your new WordPress blog.

3. **Freshness matters heavily**
   - Perplexity applies aggressive time decay
   - Update content weekly with current dates/stats
   - New posts get "impression threshold" test—if no engagement, dropped

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
- `GPTBot` = Training crawler (block this)
- `ChatGPT-User` = Retrieval agent (allow this)

**Optimization Tactics:**

1. **Domain authority still matters** (inherited from Bing)
2. **Direct answer matching** — ChatGPT prefers content that can be extracted verbatim
3. **Focus on comprehensive coverage** — Less "Query Fan-Out" sophistication than Google

**robots.txt Configuration:**
```
User-agent: GPTBot
Disallow: /     # Block training

User-agent: ChatGPT-User
Allow: /        # Allow retrieval

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
| Wikipedia (if notable) | HIGHEST | Near-guaranteed Knowledge Panel |
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

**Strategy: Allow RAG, Block Training**

```
# robots.txt - Allow retrieval, block training

User-agent: *
Allow: /

# ============ BLOCK TRAINING CRAWLERS ============

# OpenAI Training
User-agent: GPTBot
Disallow: /

# Anthropic Training
User-agent: ClaudeBot
Disallow: /
User-agent: anthropic-ai
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

# Misc Training
User-agent: GoogleOther
Disallow: /

# ============ ALLOW RAG/RETRIEVAL AGENTS ============

# OpenAI Retrieval (ChatGPT Browsing)
User-agent: ChatGPT-User
Allow: /

# OpenAI Search
User-agent: OAI-SearchBot
Allow: /

# Anthropic Retrieval (Claude Browsing)
User-agent: Claude-User
Allow: /

# Google Search (Required for SEO + AI Overviews)
User-agent: Googlebot
Allow: /

# Perplexity
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /

# Bing (Feeds ChatGPT, Perplexity)
User-agent: Bingbot
Allow: /

# Sitemap
Sitemap: https://yoursite.com/sitemap.xml
```

### B. llms.txt Implementation

Create `/llms.txt` to guide AI agents to your best content.

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

**Also create:**
- `/llms-full.txt` — Concatenated full text of all key pages
- `.md` versions of HTML pages (e.g., `/article.html.md`)

### C. Server-Side Optimization

| Requirement | Target | Why |
|-------------|--------|-----|
| TTFB (Time to First Byte) | < 200ms | RAG systems have retrieval timeouts |
| Full page load | < 1 second | Perplexity may abandon slow pages |
| JavaScript rendering | SSR preferred | AI crawlers have JS limitations |
| Mobile-first | Required | Google's primary index |

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

### Tracking AI Citation Appearance

**Tools:**
- [ ] **Ahrefs/Semrush:** Track positions for AI Overview presence
- [ ] **InLinks:** Visualize entity graph, identify gaps
- [ ] **Google Knowledge Graph API:** Query entity `resultScore`
- [ ] **Manual Perplexity/ChatGPT testing:** Search your topics, note citations

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

### A/B Testing Framework

| Test Variable | Measurement |
|---------------|-------------|
| Add statistics to existing page | Monitor AI Overview inclusion +/- |
| Add expert quote | Monitor citation position |
| Change H2 to match PAA verbatim | Monitor snippet capture |
| Add Schema FAQ markup | Monitor featured snippet/AIO |
| Create Wikidata entry | Monitor Knowledge Panel |

---

## 9. Hidden Gems & Competitive Edges

### 10 Obscure Insights That Give Unfair Advantages

1. **"Little to no effort" is the death sentence** (QRG 4.6.6)
   - Even AI-assisted content survives if human effort is evident
   - The standard is "significant effort" — show your work

2. **Information Gain uses LSTM-like session state** (Patent inventor research)
   - What users viewed THIS session affects scoring
   - Multi-turn searches increasingly common in AI Mode

3. **Perplexity's Trust Pool is literally hardcoded** (Reverse engineering)
   - Reddit, LinkedIn, Wikipedia are Tier 1 regardless of traditional SEO metrics
   - Your blog must be 10x better to compete with Reddit post

4. **Query Fan-Out triggers "gap-filling" re-queries** (Google I/O 2025)
   - If your page covers 7/8 sub-intents, you might get all 8
   - Covering 4/8 = another source gets synthesized alongside you

5. **"Experience" is the only anti-AI moat in E-E-A-T**
   - Original photos with EXIF data
   - First-person specifics AI couldn't generate
   - Case studies with real client names (with permission)

6. **The L3 Reranker has a "drop threshold"**
   - Low information density = entire result set scrapped, new search issued
   - Your "fluffy" intro paragraph may cause entire page rejection

7. **Wikidata → Knowledge Graph is 2-4 week pipeline**
   - Faster than waiting for Wikipedia notability
   - Schema `sameAs` to Wikidata accelerates entity recognition

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
| 3 | Implement robots.txt configuration | Updated robots.txt |
| 4 | Create llms.txt | /llms.txt live |
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

| Add This | Get This |
|----------|----------|
| External citations | +115% visibility |
| Expert quotes | +40% visibility |
| Statistics | +37% visibility |
| Technical terms | +32.7% visibility |

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
3. `geo-academic-research-synthesis.md` — Princeton/Georgia Tech GEO paper (+115%/+40%/+37%)
4. `perplexity-ranking-reverse-engineered.md` — L3 Reranker, Trust Pool, Vespa.ai
5. `entity-seo-knowledge-graph-deep-dive.md` — Entity Home, Wikidata, Schema examples
6. `quality-rater-guidelines-deep-analysis.md` — QRG 4.6.x, Ray Update, Experience signal
7. `ai-crawlers-technical-reference.md` — llms.txt spec, crawler user agents
8. `query-fan-out-guide.md` — Query decomposition, PAA optimization

---

*Last updated: January 2026*
