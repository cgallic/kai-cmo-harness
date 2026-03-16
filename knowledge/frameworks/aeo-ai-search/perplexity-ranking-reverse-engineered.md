# Deep Research Report

**Query:** Reverse-engineer Perplexity AI's source selection, ranking algorithm, and citation behavior for content optimization.

OBSCURE SOURCES TO PRIORITIZE:
1. Aravind Srinivas (Perplexity CEO) - ALL interviews, podcasts, Twitter/X threads, conference talks (he's unusually transparent about their tech)
2. Denis Yarats (Perplexity CTO, ex-Meta AI Research) - his academic papers, talks, and any public statements about Perplexity architecture
3. Johnny Ho (Perplexity founding engineer) - technical discussions, blog posts
4. Perplexity company blog technical posts (not marketing fluff)
5. Y Combinator Demo Day presentations, HN launch threads, and Perplexity-related HN discussions
6. Perplexity API documentation - what parameters do they expose? What does this reveal about their ranking?
7. Perplexity Pro vs Free differences - what changes with 'Pro Search'?
8. Reddit r/perplexity_ai - user experiments, reverse-engineering attempts, complaints (complaints reveal algorithm biases)
9. Comparative tests by SEO practitioners: same query on Perplexity vs Google vs ChatGPT
10. Perplexity's open-source contributions on GitHub (if any)
11. VCs who invested (IVP, NEA, Jeff Bezos) - their investment memos or public statements about the tech
12. Competitor analysis from Kagi, You.com, Phind - they analyze Perplexity

TECHNICAL QUESTIONS TO ANSWER:
- Does Perplexity use their own web crawler or Bing's index? Or both?
- How does Perplexity weight .edu, .gov, Wikipedia vs commercial domains?
- What's the exact 'Pro Search' multi-step reasoning process?
- How do they handle freshness vs authority tradeoffs?
- Do they have anti-SEO-spam measures? What triggers them?
- What makes a source get CITED IN THE ANSWER vs just listed in 'Sources' sidebar?
- How does Perplexity handle conflicting information from multiple sources?
- What content structures get extracted most reliably?
- How does their 'Focus' feature (Academic, Writing, Reddit, etc.) change ranking?

COMPETITIVE INTELLIGENCE TO EXTRACT:
- What content types does Perplexity favor that Google DOESN'T?
- Which queries does Perplexity handle better than Google? (arbitrage opportunity)
- What's the best way to get indexed by Perplexity specifically?
- How to optimize for Perplexity's 'Related Questions' feature
- Perplexity Pages - how does content there rank vs external sources?

OUTPUT FORMAT:
- Direct quotes from Srinivas/Yarats with dates and sources
- Technical architecture details with evidence level
- Actionable optimization tactics specific to Perplexity
- Differences from Google/Bing that create optimization opportunities
**Generated:** 2026-01-10 12:35:04
**Source:** Gemini Deep Research API

---

# Reverse-Engineering Perplexity AI: Architecture, Ranking Algorithms, and Optimization Strategies

## Executive Summary and Key Findings

Perplexity AI represents a fundamental paradigm shift from traditional "search engines" (retrieval-based) to "answer engines" (synthesis-based). Unlike Google, which optimizes for routing traffic to websites via a ranked list, Perplexity optimizes for **information extraction and synthesis** to keep the user on the platform.

**Key Findings:**
*   **Hybrid Indexing Architecture:** Perplexity does not rely on a single index. It utilizes a hybrid model combining the **Bing Search API** for broad coverage and its own **PerplexityBot** for real-time depth, all orchestrated through **Vespa.ai’s** vector search infrastructure [cite: 1, 2, 3].
*   **The "Citation Trust" Algorithm:** Ranking is not determined by backlinks alone. It is driven by a **curated trust pool** (whitelists) and **extractability**. Domains like Reddit, LinkedIn, and Wikipedia are hard-coded as high-authority "seed" sources [cite: 4, 5, 6].
*   **The L3 Reranker:** Research indicates a three-layer ranking system. After initial retrieval, a machine-learning-based "L3 Reranker" filters results based on semantic relevance and data density. If a source passes the retrieval stage but fails the L3 quality check (e.g., too much fluff, low information density), it is discarded before the LLM synthesis phase [cite: 4, 7, 8].
*   **Pro Search Reasoning:** "Pro Search" utilizes a **Chain-of-Thought (CoT)** process that decomposes queries into sub-tasks, executes multiple parallel searches, and synthesizes findings. It is not just a "deeper" search; it is an agentic workflow that plans, executes, and refines [cite: 9, 10, 11].
*   **Optimization Strategy (AEO):** Optimization for Perplexity (Answer Engine Optimization) requires a shift from "keyword stuffing" to "entity density." The most effective tactic is **Parasite SEO** on trusted platforms (e.g., Reddit, Medium) and structuring content specifically for RAG (Retrieval-Augmented Generation) extraction using clear headers and direct answers [cite: 5, 12].

---

## 1. Technical Architecture and Infrastructure

To optimize for Perplexity, one must first understand that it is a **Retrieval-Augmented Generation (RAG)** system, not a traditional search engine. Its architecture is built to feed an LLM, not a human user.

### 1.1 The Retrieval Layer: Bing + PerplexityBot + Vespa.ai
Perplexity does not crawl the entire web in the same manner as Google. It employs a tiered retrieval strategy:

1.  **Broad Retrieval (The Bing Dependency):** For the vast majority of queries, Perplexity relies on the **Bing Search API** to identify candidate URLs. This provides the "breadth" of the internet without the cost of maintaining a Google-scale index [cite: 2].
2.  **Depth Retrieval (PerplexityBot):** Once candidate URLs are identified (or for specific news/real-time queries), **PerplexityBot** visits these pages to extract full text. This bot is aggressive regarding freshness. It respects `robots.txt` but is designed to parse content specifically for LLM ingestion, stripping away navigation, ads, and boilerplate code [cite: 13, 14].
3.  **The Orchestration Layer (Vespa.ai):** This is the critical "brain" of the retrieval process. Perplexity partners with **Vespa.ai** to manage its search function in-house. Vespa allows Perplexity to store document embeddings (vectors) and perform hybrid searches (keyword + semantic) at scale. This infrastructure enables the system to update its index in real-time, a necessity for their "freshness" value proposition [cite: 1, 3, 15].

**Evidence of Architecture:**
> "Perplexity's innovative approach... relies on a massive and scalable Retrieval-Augmented Generation (RAG) architecture... By building on Vespa's platform, Perplexity delivers accurate, near-real-time responses." — *Vespa.ai Case Study* [cite: 3].

### 1.2 The Synthesis Layer: Model Agnosticism
Perplexity is model-agnostic. While the "Pro" version allows users to select between GPT-4o, Claude 3, and Sonar (their proprietary model based on Llama), the default architecture uses a fine-tuned version of these models optimized for **conciseness and citation accuracy**.

*   **Sonar Models:** Perplexity trains its own "Sonar" models (based on open-source models like Llama 3). These are specifically fine-tuned to reduce hallucinations and enforce citation behavior. They are trained to say "I don't know" rather than fabricate information if the retrieved context is insufficient [cite: 16, 17].

---

## 2. Reverse-Engineering the Ranking Algorithm

Perplexity’s ranking algorithm differs significantly from Google’s PageRank. It prioritizes **Semantic Relevance** and **Information Density** over link equity.

### 2.1 The Three-Layer (L3) Reranking System
Independent research by Metehan Yesilyurt has uncovered a sophisticated filtering process known as the **L3 Reranker**. This system operates *after* the initial search results are retrieved from Bing/Vespa but *before* the LLM generates the answer [cite: 4, 7, 8].

1.  **Layer 1 (Initial Retrieval):** The system fetches a broad set of candidate URLs based on keyword matching and basic semantic similarity (often via Bing API).
2.  **Layer 2 (Coarse Ranking):** Candidates are scored based on domain authority and freshness.
3.  **Layer 3 (The "L3" Quality Filter):** This is the "kill zone." A machine learning model evaluates the content's **extractability**. If a page is loaded with fluff, pop-ups, or lacks clear entity relationships, it is discarded *even if it has high domain authority*. The L3 reranker has a `drop_threshold`; if the content doesn't meet a specific density score, the entire result set might be scrapped in favor of a new search [cite: 4, 8].

**Optimization Implication:** Your content must survive the L3 filter. This requires "Answer-First" formatting—placing the core answer immediately after the H1 or H2 headers to ensure the reranker detects high information density immediately [cite: 4, 18].

### 2.2 The "Curated Trust Pool" (Whitelists)
Perplexity maintains a manual or semi-automated "allowlist" of high-trust domains. Content from these domains bypasses many of the stricter filters and is prioritized for citation.

*   **Tier 1 (Seed Authority):** Wikipedia, Reddit, LinkedIn, GitHub, Stack Overflow, .gov, and .edu domains.
*   **Tier 2 (News & Media):** Major outlets (Bloomberg, NYT, Reuters) are prioritized for "News" focus queries.
*   **Tier 3 (Commercial/General):** E-commerce and general blogs. These require significantly higher semantic relevance to displace Tier 1 sources [cite: 4, 6, 19].

**Evidence of Bias:**
> "Perplexity maintains curated lists of high-trust sources across different categories... Content associated with these domains receives inherent authority boosts." — *Metehan Yesilyurt's Analysis* [cite: 4].

### 2.3 Freshness vs. Authority Trade-off
Perplexity applies a **Time Decay Factor** (`time_decay_rate`). Unlike Google, which may keep an old, authoritative post at #1 for years, Perplexity aggressively down-ranks content as it ages, particularly for queries with "news" or "tech" intent.
*   **The Window:** There is a `new_post_impression_threshold` where new content is given a "test" period. If it generates engagement (clicks/citations) within the first few hours/days, it is indexed permanently. If not, it is dropped from the active retrieval set [cite: 4].

---

## 3. Source Selection and Citation Behavior

Why does Perplexity cite one source over another? The decision is made during the **Context Assembly** phase of the RAG pipeline.

### 3.1 Citation Logic: The "Needle in Haystack" Approach
Perplexity does not cite the "whole page." It cites specific **sentences or paragraphs** (chunks).
1.  **Chunking:** PerplexityBot breaks web pages into chunks (passages).
2.  **Vector Matching:** These chunks are converted into vector embeddings.
3.  **Similarity Search:** The user's query is compared against these chunks.
4.  **Citation Decision:** The LLM is instructed to generate an answer *only* using the retrieved chunks. If a chunk is used to generate a sentence, that source gets a citation number [cite: 15, 20].

**Key Differentiator:** A source is cited in the answer (Inline Citation) if it provides a **unique fact** or **statistic** that contributes to the synthesis. It is merely listed in the "Sources" sidebar if it was retrieved but its specific content wasn't essential to the generated text [cite: 5, 20].

### 3.2 Handling Conflicting Information
When sources disagree, Perplexity's behavior depends on the model and mode:
*   **Standard Search:** Tends to favor the "consensus" view or the source with higher Domain Authority (Tier 1 sources).
*   **Pro Search:** Is designed to identify conflict. It may present multiple viewpoints ("Some sources say X, while others suggest Y").
*   **Denis Yarats (CTO) on Conflict:** Yarats has stated that the system aims to maximize **diversity** in retrieval. If multiple documents contain the same entropy (information), the system is tuned to retrieve a document with *different* entropy to provide a counter-viewpoint, rather than retrieving five documents that say the exact same thing [cite: 21].

### 3.3 The Role of "Focus" Modes
Perplexity's "Focus" modes act as **hard filters** on the retrieval index:
*   **Academic:** Restricts retrieval to Semantic Scholar and PubMed APIs. It ignores general web SEO [cite: 22].
*   **Writing:** Disables retrieval entirely; relies solely on the LLM's internal training data.
*   **Reddit/YouTube:** Restricts the search domain to specific URLs (`site:reddit.com`, etc.).
*   **Implication:** To rank in "Academic" focus, you must be published in journals or repositories. To rank in "Reddit" focus, you must optimize Reddit threads, not your own blog [cite: 22, 23].

---

## 4. Pro Search: The Multi-Step Reasoning Engine

"Pro Search" (formerly Copilot) is Perplexity's premium feature. It is not just a search; it is an **agentic workflow**.

### 4.1 The "Chain of Thought" Architecture
Pro Search uses a multi-step process described by the engineering team:
1.  **Query Decomposition:** The LLM breaks the user's complex query into sub-questions.
    *   *User:* "Compare the battery life of iPhone 15 vs. Pixel 8 and their charging speeds."
    *   *System:* Generates sub-queries: "iPhone 15 battery life test," "Pixel 8 battery life test," "iPhone 15 charging speed," "Pixel 8 charging speed."
2.  **Sequential Execution:** It executes these searches sequentially. The result of Step 1 can influence the search terms for Step 2 [cite: 9, 10, 24].
3.  **Clarification (Human-in-the-loop):** If the query is ambiguous, the system pauses to ask the user a clarifying question (e.g., "Do you mean the Pro or base models?").
4.  **Synthesis:** It aggregates all retrieved contexts into a single, comprehensive report.

**Technical Insight:**
> "The system works as follows: when a user submits a query, the AI first creates a plan... For each step in the plan, a list of search queries are generated and executed... The execution is sequential rather than parallel." — *ZenML Case Study on Perplexity* [cite: 24].

### 4.2 Deep Research Mode
Introduced later, "Deep Research" extends Pro Search by performing **dozens** of searches and reading hundreds of sources. It uses a "retrieval-reasoning-refinement" cycle. It actively looks for missing data points and re-queries until the confidence threshold is met [cite: 10, 11].

---

## 5. Actionable Optimization Tactics (AEO)

To rank in Perplexity, you must optimize for **Machine Readability** and **Trust**, not just human readability.

### 5.1 Content Structure: The "Inverted Pyramid" for AI
Perplexity's L3 reranker favors content that is easy to parse.
*   **Direct Answers:** Start your article with a `TL;DR` or a direct answer to the target question. This increases the likelihood of being picked up as a "featured snippet" or direct citation [cite: 4, 18].
*   **Structured Data:** Use `FAQ Schema`, `Article Schema`, and `HowTo Schema`. Perplexity relies heavily on structured data to understand the context of a page without parsing the entire HTML DOM [cite: 4, 25].
*   **Objective Tone:** Avoid marketing fluff. Perplexity's fine-tuning penalizes promotional language. Use "neutral, encyclopedic tone" to increase trust scores [cite: 26].

### 5.2 Parasite SEO: Leveraging the Trust Pool
Since Perplexity hard-codes trust for domains like Reddit and LinkedIn, the fastest way to rank is to publish content *on* those platforms.
*   **Tactic:** Identify a trending query on Perplexity. Write a detailed, sourced answer on Reddit or a LinkedIn Pulse article. Perplexity is statistically more likely to cite that Reddit thread than your new WordPress blog [cite: 5, 12].
*   **Evidence:** "Reddit was Perplexity's most cited domain... followed by YouTube and reputable sources like Forbes." [cite: 5].

### 5.3 Optimizing for "Related Questions"
Perplexity generates "Related Questions" at the bottom of every answer. These are generated based on **semantic adjacency** and **query logs**.
*   **Tactic:** Use Perplexity to search for your target keyword. Look at the "Related Questions." Create an FAQ section on your website that explicitly answers these questions using the exact phrasing. This signals to the retrieval engine that your page covers the entire "topic cluster" [cite: 25, 27].

### 5.4 Technical SEO for PerplexityBot
*   **Robots.txt:** Ensure `User-agent: PerplexityBot` is allowed.
*   **JavaScript:** While Perplexity can render JS, it is slower and more prone to failure. Server-side rendering (SSR) or static HTML is preferred for higher "extractability" scores [cite: 13, 14].

---

## 6. Competitive Intelligence: Google vs. Perplexity

### 6.1 Content Favored by Perplexity (Arbitrage Opportunity)
*   **Data Tables & Lists:** Perplexity excels at extracting structured data (e.g., "List of top 10 CRM tools with pricing"). Google often buries this in long-form content; Perplexity extracts and presents it.
*   **Academic/Technical Summaries:** Perplexity is preferred by knowledge workers for summarizing PDFs and technical papers. Optimizing PDF content (whitepapers) is a largely untapped arbitrage opportunity [cite: 16, 23].
*   **Subjective/Opinion Synthesis:** Google struggles with "What is the general consensus on X?" Perplexity synthesizes Reddit/Forum discussions to answer this well.

### 6.2 Differences Creating Optimization Opportunities

| Feature | Google | Perplexity AI | Optimization Opportunity |
| :--- | :--- | :--- | :--- |
| **Ranking Metric** | Backlinks & Clicks | Citation Trust & Extractability | Focus on **Information Density** (facts per paragraph) rather than word count. |
| **Content Age** | Older domains often win | Freshness is heavily weighted | Update content **weekly** with current dates/stats to trigger the "Freshness Boost." |
| **Long-tail Queries** | Matches keywords | Matches **Intent/Reasoning** | Target complex questions ("Why does X happen when Y...") rather than simple keywords. |
| **Format** | 10 Blue Links | Synthesized Answer | Write in **Q&A pairs**. Make your content "copy-paste" ready for an AI. |

---

## 7. Leadership Insights & Strategic Direction

### 7.1 Aravind Srinivas (CEO) Quotes
*   **On the Business Model:** "We do not have to beat [Google], neither do we have to take them on... We never even tried to play Google at their own game." (Lex Fridman Podcast, 2024) [cite: 28].
*   **On Citations:** "Citations are our currency." (Forbes Interview, 2024) [cite: 29].
*   **On Accuracy:** "If there isn't enough solid information retrieved, Perplexity should admit the lack of sufficient data... This retrieval process ensures the grounding of AI-generated text." [cite: 30].

### 7.2 Denis Yarats (CTO) Technical Insights
*   **On RAG:** "The quality of AI answers depends on the quality of information retrieved... First, solve search, then use it to solve everything else." [cite: 31].
*   **On Conflicting Data:** Yarats emphasizes that the model is tuned to understand when documents carry the *same* information versus *conflicting* information, aiming to present the user with the conflict rather than smoothing it over [cite: 21].

### 7.3 Johnny Ho (Founding Engineer) Product Philosophy
*   **On User Intent:** "The user is never wrong." The product is designed to anticipate what the user *meant* to ask, even if the query is poorly phrased, by using LLMs to rewrite the query before search execution [cite: 32, 33].

---

## Conclusion

Perplexity AI is not merely a "wrapper" around ChatGPT or Bing. It is a sophisticated **RAG engine** built on **Vespa.ai**, utilizing a **multi-stage ranking system** that aggressively filters for information density and domain trust.

For content creators and SEOs, the strategy must shift from "optimizing for clicks" to **"optimizing for citations."** This involves:
1.  **Structuring content** for easy extraction (Schema, Lists, Direct Answers).
2.  **Leveraging high-trust domains** (Reddit, LinkedIn) via Parasite SEO.
3.  **Maintaining extreme freshness** to satisfy the time-decay algorithms.
4.  **Focusing on "Answer-Worthy" content**—facts, data, and distinct viewpoints—rather than generic fluff.

By aligning with Perplexity's architectural preference for **verifiable, dense, and structured data**, publishers can secure their place as the "source of truth" in the age of Answer Engines.

**Sources:**
1. [bytebytego.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHtixt2LJyeo64ZjORhruaJfm7r8HFiKwl_rC6-pawNpeCkH_CuLfScNQGlA6aNioaP-vZ2-ZdF5bCRhuJ3p9PmedAwR0zIcWNQycKqt2cbbASugU5WT2U_Aei89I6CLivBMsiCWK6dvEdyGbze0CLeWowNeE0=)
2. [hyperlinker.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFg08qxp3imOcvj3f6LWaBdTpnj_UaB4y8W_LQKlbhkQhccj3KT6YLM9VYuB0gVQtPn-gO4FCH70K11zjYo4yzDsE6MOs3AMAQuoeBv3kbzJI0VdPCpW3O3wXMayWv-UHHEboRFbIMgJFSI)
3. [vespa.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFXlo9XXTIgPqS8f9NLcs_3n3f-y8TbAlXSyq7A7K4sKh6Lm-xoBeuiLKXkRAgQdiGCLy9-NZOYi8LuSWTLMmey0wKfNweME6nV-3UxZZHjmUvmBodQ9ybyVgFWai2Cb9c-R34EtwiKAh5hYZDVrurgIEL5qW0kRnqyIrOAYhxej2ybvTxRdPJquu3XrKRVWA==)
4. [wpseoai.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHigBbb-qom5UblFjNsg3PzHtnH7wlo-W7fcuKIr5QHxzu50mqjV23-Bko3up8HeDrxIbuSfURGvX9ZYAQShKVc30C-HZsot6k0y7izEp4ESRukjLhczd6QO4jTEZRvbDo38mS7aiscnrE=)
5. [surferseo.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFOACTx3fzn159xo2BvTwT7mPoWzOa5R63Wni016hMpS4utm9S33x22BBBeBZ9T7if1ZfJqX4fl0flBIKfHzaRpK7Z1l25jT0tqpH_iyRCEptw-dXuYRQBr1hImyf2OBOrWNJERhP0tHydFrQ==)
6. [tryanalyze.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFWugIhCQlDGPyJ9yVf1NJJYFmUXNKR34r6YuV2MgP2yTfGTNV2VSVQvqiTJMw_dnH2C5VNDiTQLFlxjAixNxX4RSbXegXNsDixRXZabaL9PdrRW4Iiov5KCMOufGze57NESnGckTTE29macWlsDg==)
7. [searchengineland.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFUS9SdKEgXWDSjvHepjwJbazasm51KV6z-tcdS2_0dodihoVHzP6NfOhKZ0cz-7aYFtSI1uL5psrqLBuPJAfJHQfxdQqYbm1jPV6euo0FWJhKeraBJWx2pZs8focOKDsY6mYulKCGbk6ieD5vewhGKE9mF3PKIMTzmdXYibZb6)
8. [hueston.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFby3MVPUKwrwRnFUqSshpne3KE0qscyJyGxlr_0iBxLTzyDFAQfA0G308ZsTKtWd06CnOR844sEuViBBV69ekWWXNuM2xkg10iJrDMM0uYe7e0WudUs1Ix2k5sRW5GgIGMu4DJ2Nzhun3yxVF9m3yeaOd6cqPJX-x361OoHKpUFTnE1YF9DY0xXlA=)
9. [mynextdeveloper.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGEZ6Q603DMLU2SZEjJ5ES3xQeF0ZMMX9O-a26XUkQPKOdbENYKyvof04WudBE89bGzQc3AX8PJR_82p_ikA6H4wFfQhE9Yri3JQwhVx8Ba20jI6ue0KLPU2UScNjP8n__d8NhvO-FS-Oo7K6YMZzVtvOeeDcI6ESt0prcyq8F-VJKrqUGX2VM=)
10. [datastudios.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQElTVPeBRpoToo_q-k9ui_ZYdiatvlgq7xskZs30ypXcEYOnBKYsm9NGHfRNjyRyq8uFsBXia3-zQma83YN8px2i0I9zuwJ7fctk8uoBwyyBxuWhQxnI76OR3TxCDvlIKHZ0-591Y7YY07Iv8Fr2ewT0pXgxq4fGsIU5eB9MuXiyBGsUvwr6ifmzh0QvmHrok5OrLbwzhXF_-DQ7XQI-XOCCUz8vV47NyJGvf8=)
11. [datastudios.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH3JHyAvTySmO-4mRu28ejhRKusy8Z0aOPMoFxu8loWZaMKbnlaiBna54PILfvYK0wKqRMXSFQplEAPT5x_6X7FiuZPxDm_DVzwHh-QKTVYhVXqswrwbJWpHwIEI8LQNMIox1EGjPAFy1N5YNg4u-By_0be4jvrzsu8mlwaKyDTzlwXu-M6VhhQicCsCleT7WjjSfM5v9oE-0BdGYXa4rwl)
12. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEgxzYfAxcqFj8ailqvlcsff_msvo3r1wjhaByuA3pBo0qrYNIc1YCRGqBea_nYYh_x4buRy8XrT5KrIAvHe9nFVNGApPWTGpq8WFQGb1jV3UiIGn4hby0qRadL5EQNlWkMOIvjtuSTnCHL7r3xGkQw3wc3j_F2A2aPtPlpNMEn4ya1wHGvcJP7qyKos98DQLoKqNkYp8N6)
13. [rathoreseo.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHPCyBz73sc1UvtDSR5xmcSkyAW6BC_ZxpixUtanQbHQ1bZxDu0DcOVNrwCd8KZYri0MTntnjUmhUk15becjhCxSYAMlTeczTu81UBUbH7rkzn34Qfx-c099M6kVAhJsse6ShPNnlQQxudk8TXqTH4Y83uqvW8mGTKfjtB_7VPrpqLPOFA=)
14. [darkvisitors.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEdZtp9GwXBh61vypHTRwu2gUmL8LJgWfYLS26HU0Qpz1Md9N0PSBRqbzuzbjAEjHNF0VYpgw_CorgNWhgYI6jWQb7YGay9dOzmyHzZhVG_NDHqfI8UyQqQSXNLU8znRhv-aW8=)
15. [vespa.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEWBjFk2zyO2K4HkDxKro9RMN7cYs6XMb4Zqk9TMJYpEK6-PiN3ltpWDgNCnlkrHdOwGIa1fDzNsWORJjbsLXdJH6pfwiWU3KdrFD_60m_TPf1HTT6BTioA9YlQBPzK12mu7_2E9OlqIQpH7I23GQL5RAjqdn426ZEE0rX0vg==)
16. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEGUTZ7MHP9ZgymrJh5Xg9gqdoXl--drMMJTknmzO15PdOVFAtcnq7PiF1cEJQwf_1QmWPK3Fy3apZrNtrqKMAAXltQGK_piunBGl0cOS6jGN8ZXCk7HrNqW5hYZqEv_OyNPsAhC-r21KuZj6vasv0a-MTTNKguYVlc6brWRFcbSNLGp6zpn7hxRamghYec4XGr6QEgMoEIZDireVFEjSW2N7Y80R66db7KToGmqODGMwTuPQ7F0zt8f3iLfBoq6Msvt3lTvIIs)
17. [perplexity.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8gqGnAQrAlhUL7NTLh7EmUg8xKj-qDrdZVOszH6RpPbd8sXDDcZkMHf__6U22j7DMLiFDomOTMF0K9V_0-rzmmhfhzks2ytc1MR3E0pMFAJSR_rCb2mKIbjE61KBr6dEn6Tazj44lOcc=)
18. [optimizeyour.blog](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF7vF7D3Do6g8kKMewzYRthSGxIaz9a4AekELh2zAL3oIbALQFBawkhJDuAtpxxgqw4faXZseYUNT7c3WFwaEA6sBYXXJsSmZOGpJktF-9l3fIzi_MChz3hrZZjgqMr8GvI-Mdz--QaNrGB304-ElwNayEuzPPNV0bKvB9QM7I=)
19. [onely.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGWm-9SwnczIX2ecWFSBQRadb3E_chCbmy90Sxu824x60wDJUbdZ8s0U35Bio1V5P0tBGYyETlq0qPIPgfGbOKwePd7t4SDfx1WknwBI9PvQo87fNsn3aaEZiVBwPy3Z5cp7uJwvx-BLRN5Sw==)
20. [seoagencyusa.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGvMCEhdJGYpbAyh5jw5tv8c7xauKdkYw0lZ2ld5L3OyTAcbQayhD_TjinQc6ixNW3sq4TDWrbzQWwWUBuaTMBFXY8eCEQuBumodMCOcUJ27fGlZ4IGCnmUUBoEp9Y1af3SU6eftGD9xH-tJwvhXjWpIeLpc2k=)
21. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGTCXXvOh9l37DujUIjIqKAh6ogQhIWIWxhArVAFdnv843iyO0uElaAljNc9sWsJUwxHYSKGM0M6Q6bLm7-k5wDtL2fFsVNDyHfRjt6RqwVyeKW9GoQY925vQOy7V2w)
22. [glbgpt.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEGcRmS4G2Wpklycczz9b_QHrKf-c-o5DWRF_kaD1UzEuqPHIp35qWQOY9G069dNu2bRictw6a_5xzEUQ_UNopgrEBXWoSYhDySLEREt5blASeNHy5scFHN_6FGem113rmFOhLh7hz2ApVKFp5jPfwganvXO_I1RhDfZuI1JDc_s-MVpudNiVJvL6s14c4xKaotNWnYZg==)
23. [skywork.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQECVEuxilpmiN7Xf3U2Quy8dGiqrMwh5n9ZFH3ei0RkgeIFlASRk00FaVmCZHMHpLenZFZzBi_lVfcZF9IxmEwbJriVhuaKLVtewIXJYt4qgIMQMR24bs8zsc2KyWxNe_UgUgsHW_iJt5OUiRg=)
24. [zenml.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE-ZJ3PC7_-syPg0hJ7rE2q5u2bNvvMuqCdfllYW3UlsU5HF_ZCaRsfAcRbGkJEBISWgWDNqsE28HHETY8JfHqoH6wlYurqQtbo0klIz19iMLidhQww7SODBy-Qu4Jq8nUZcwnb-WtlkCXvfPGwRMwhYkSup6BVb3hIpBX3JrqqLMtxKOHe5nCJ-SbvP305lf4W8dSRRdjH3g==)
25. [techmagnate.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEWeDqULsNL0qoAY6z8cfKlz3lW15t8UaLQVoV0puqiDsTU6V3cPCzM6K3mWza8t1L-LJ6611MuD9A1GQIiVhwkaNiiMf_kT1YpoxMs2du9F3nVrCJznU42L_ElMBDtUAe-gJSA6FbdWGJPA2NaQIK3PrdRPQ==)
26. [yogeshkandel.com.np](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGCr9KzENwzP3vUB3Sl_N15sVwccuQA4zvdJjtZcIWVAv1kfRnoa9XazIC35pFp76X003TIS8dUjYWVzycXEep5JNRVtVU1ABwZ3z8Hgt6PzpV-Q4RZ3MTncUhj_bjBCKKat9weFfNoGMaDcKBnJdwoDtIItg==)
27. [saffronedge.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEApKg9kHp7ClRgHK_7q5YqAkE2YbKvloaaHl3cCc7j3VwO5zPao8mFKmVP6FHrDjhaoQREpwMPo2aJsRu7_YEzIS4sP56O-9_cDPD45rLI6fK8xL4nR0VtZ5wNHiQ2Bvs=)
28. [lexfridman.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEzqB5zSfRL9rG8cQWWt3KDtpXTlX9s6EdvWuSSLgBcb6ZZuIazowDVNhMjSueblDDcymSouRHB-8qhzM4C_sZ56IebBtyh_tShlUwwVH-_h8hMVafvLYeu99D1b3-NyT1l3hzmmSP4iKU=)
29. [forbes.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHRHj6Vog2Mz8HlbVvVr8gbEzMIjLPFJsiJGtQJJY926fc4mb-8C70tOFaHDSynhrWRC8EJn_sD_WL8Bxh2pelpN3raTAYY7lNEikq9ywe8qB7et9NbYiGcaYcLc0ERZnVgXnUwIFlcPbCP0tJSXBR44spKs4wvH2Qolmqyw4KMjGU9ZhoVs71YhyKHP6gLpzaHtx6ZXvpwZPa9m81tsfbvaiBc3AL5jCPYt6OSy-3xxRU=)
30. [shortform.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGEYhIp1SN61WOIfRaR6pYJbWk8488v1lwNHHrOSYly2WCS5xzxeC5zbF8_G0-6ANsHingPJwQgPqir0OL7vwJRbiPSSFPvGyeyTDcHlhAzN1cXYcw534hjpk9FeFnQ8hinTJO5mILJ-qKt2KTDlAnYrr_Et33R0wnz4fZsv-NK1mxrHV-NaYQsxcIJxWkGYEnmpvR7kScu_VrhI6znnuwrJNTP0HLsKDfbB-aO8CekKlE_4O9i-q4QMafIUWIiLPqXs1N-5GHjtRwoeq3AEXAlVgSC6Vvhuw==)
31. [vespa.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGL-pLOAU8zgDEhUWg2_E1URFKQpcrCGUC9DmVpkv62xtbYQp5rnsiv80MtXXqRJcQYYvQRUiHzKNi3fn_XeFY46EQ-nSEyKpoymlOeoVfzZzsa)
32. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEgmNgXDBZbxBkD6qXlwuchRoFvxtrhkyJ2CGKFR7EpaQd355JH5qYofAlhGyRP8GkV4fJsqrX95EPD2TMRfO9WRw2WlF7LcphbWupAqERRpDmy8WVmDr5uWzO4C8NtuAkE)
33. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8TnModTcAdTk8syrTyOdinXFd2ELjYTJHk7R6zmaWyVT-BmMYjHgW8SLcOslKr0DSC_RCBYvWTfujPxt69CF2IxV1pFYlxxKDTQC5yS1GO4u1jVrLP6k1VWo-lYDFPByU)
