# Deep Research Report

**Query:** Google Query Fan-Out for AI Mode - how complex queries are decomposed into sub-queries.

FOCUS ONLY ON:
1. Google I/O 2025 announcements on Query Fan-Out (Liz Reid quotes)
2. How many sub-queries are generated and how they're merged
3. People Also Ask (PAA) as visible fan-out - how to use PAA data
4. Content structure to capture multiple sub-queries on one page
5. Hub-and-spoke vs pillar content models for fan-out

OUTPUT: Fan-out architecture diagram, PAA optimization tactics, content structure recommendations
**Generated:** 2026-01-10 13:26:17
**Source:** Gemini Deep Research API

---

# Google Query Fan-Out Architecture and Optimization Strategies: A Comprehensive Analysis of AI Mode Mechanics

**Key Points**
*   **Google I/O 2025 Announcement:** Liz Reid, Head of Search, introduced "Query Fan-Out" as a core component of the new **AI Mode**, powered by a custom version of Gemini 2.5. This technique allows the search engine to decompose complex queries into multiple sub-topics and execute them simultaneously [cite: 1, 2].
*   **Mechanism of Action:** The system breaks a single user prompt into a "multitude" of sub-queries (observed examples suggest 8 or more parallel searches). It retrieves information from the open web, Knowledge Graph, and Shopping Graph, then synthesizes these distinct data streams into a coherent, cited report [cite: 3, 4].
*   **People Also Ask (PAA) Utility:** PAA data serves as a "visible blueprint" of the fan-out process. SEOs can use PAA questions to reverse-engineer the sub-intents that AI Mode is likely to generate, allowing for proactive content optimization [cite: 5, 6].
*   **Content Strategy:** Success in AI Mode requires shifting from keyword targeting to **entity-rich content clusters**. The "Hub-and-Spoke" model is validated as the superior architecture for capturing fan-out queries, provided the central pillar and spokes are semantically linked and structured with schema to facilitate AI parsing [cite: 3, 7].

## 1. Introduction: The Paradigm Shift to Agentic Search

The announcements at Google I/O 2025 marked a definitive transition from traditional information retrieval to "agentic" search. Central to this evolution is the introduction of **AI Mode**, a conversational interface designed to handle open-ended, complex reasoning tasks that previously required users to perform multiple manual searches. The technological backbone of this capability is a process Google terms **Query Fan-Out**.

Unlike traditional search, which maps a query to an index of documents based on keyword frequency and PageRank, Query Fan-Out introduces an intermediate reasoning layer. This layer interprets the user's intent, deconstructs it into constituent logical parts, and executes a parallel retrieval process. For the academic and digital marketing communities, understanding this architecture is critical. It suggests that visibility in the AI-first era is no longer a function of matching a specific string of text, but of satisfying a distributed set of sub-intents that the AI generates dynamically.

This report provides an exhaustive analysis of the Query Fan-Out architecture, drawing directly from Google I/O 2025 disclosures and subsequent technical analyses. It explores the decomposition mechanics, the strategic utility of "People Also Ask" (PAA) data, and the necessary evolution of content modeling from simple pillars to complex, entity-mapped clusters.

## 2. Google I/O 2025: The Official Unveiling of Query Fan-Out

The concept of Query Fan-Out was formally introduced by Liz Reid, Vice President and Head of Search, during the Google I/O 2025 keynote. Her presentation outlined the capabilities of **AI Mode**, a feature distinct from the standard AI Overviews, designed for "advanced reasoning" and complex problem solving.

### 2.1 Liz Reid’s Key Pronouncements
Liz Reid’s commentary provides the primary source material for understanding the intent and function of this technology. She described AI Mode as a tool that "isn't just giving you information—it's bringing a whole new level of intelligence to search" [cite: 1, 8].

The core definition provided by Reid is as follows:
> "What makes this possible is something we call our **query fan-out technique**. Now, under the hood, Search recognizes when a question needs advanced reasoning. It calls on our custom version of Gemini to break the question into different subtopics, and it issues a multitude of queries simultaneously on your behalf." [cite: 1, 3, 9].

This statement reveals three critical architectural components:
1.  **Intent Recognition:** The system first classifies the query as requiring "advanced reasoning," distinguishing it from simple navigational or factual queries [cite: 7].
2.  **Decomposition (Gemini-Powered):** A custom version of the Gemini model (specifically Gemini 2.5) is responsible for the semantic breakdown of the query [cite: 2, 7].
3.  **Simultaneous Execution:** The sub-queries are not run sequentially but in parallel ("simultaneously"), implying a massive increase in the computational load per user interaction, handled by Google's infrastructure [cite: 1, 10].

### 2.2 The Scope of Retrieval
Reid further elaborated on the depth of this retrieval process. She noted that the system "searches across the entire web going way deeper than a traditional search" [cite: 1]. Crucially, the fan-out is not limited to the textual web. Reid specified that the system:
> "...taps into all of our data sets of real-time information like the knowledge graph, the shopping graph, and in this case local data including insights from our maps community of over 500 million contributors." [cite: 1, 2].

This confirms that Query Fan-Out is a **multi-modal** and **multi-source** retrieval technique. A single user prompt can trigger sub-queries that fetch local map data, real-time inventory from the Shopping Graph, and semantic entities from the Knowledge Graph, all of which are merged into the final response.

### 2.3 Quality Assurance and Recursive Search
A significant, often overlooked detail from the I/O presentation is the recursive nature of the process. Reid explained that after the initial fan-out and retrieval:
> "Search pulls together a response and it checks its work to make sure it meets our high bar for information quality. And if it detects any gaps, it issues even more searches to fill them in." [cite: 2].

This "check and re-issue" loop implies a multi-stage fan-out architecture where the output of the first set of sub-queries is evaluated for completeness. If the synthesized answer is deemed insufficient (e.g., missing a specific data point or citation), the system triggers a secondary wave of sub-queries.

## 3. Architectural Mechanics: Decomposition, Execution, and Merging

To optimize for AI Mode, one must understand the "black box" mechanics of how a query is processed. Based on the I/O descriptions and third-party analyses, the architecture can be visualized as a dynamic tree structure where a single root node (the user query) branches into multiple leaf nodes (sub-queries) before converging back into a single output.

### 3.1 The Fan-Out Architecture Diagram

The following text-based diagram illustrates the logical flow of the Query Fan-Out process as described in the research literature:

```mermaid
graph TD
    A[User Complex Query] --> B{Intent Classifier};
    B -- Simple Query --> C[Traditional Search / Basic AI Overview];
    B -- Complex/Reasoning Needed --> D[AI Mode (Gemini 2.5)];
    
    subgraph "Query Fan-Out Process"
    D --> E[Decomposition Engine];
    E --> F1[Sub-Query 1: Factual Basis];
    E --> F2[Sub-Query 2: Semantic Context];
    E --> F3[Sub-Query 3: Entity Relationships];
    E --> F4[Sub-Query 4: Real-time/Local Data];
    E --> F5[Sub-Query 5...N: Specific Facets];
    end
    
    subgraph "Parallel Retrieval"
    F1 --> G1[Web Index Search];
    F2 --> G2[Knowledge Graph Lookup];
    F3 --> G3[Shopping/Maps Graph];
    F4 --> G4[News/Real-time Data];
    F5 --> G5[Web Index Search];
    end
    
    subgraph "Synthesis & Validation"
    G1 & G2 & G3 & G4 & G5 --> H[Information Synthesis];
    H --> I{Quality/Gap Check};
    I -- Gaps Detected --> J[Secondary Fan-Out (Recursive)];
    J --> G1;
    I -- Quality Met --> K[Final Response Generation];
    end
    
    K --> L[User Output: Synthesized Answer + Citations];
```

### 3.2 Sub-Query Generation: Quantity and Granularity
The exact number of sub-queries generated is dynamic and dependent on the complexity of the user's prompt.
*   **Observed Volume:** Analysis of AI Mode behavior suggests that the system frequently "kicks off 8 searches" for moderately complex queries [cite: 3]. However, other sources indicate the system can issue "dozens" of related meanings and sub-questions [cite: 4].
*   **Granularity:** The sub-queries are not merely synonyms. They represent distinct "sub-intents." For example, a query like "best sneakers for walking" might be decomposed into:
    1.  "Best sneakers for men" (Demographic segmentation)
    2.  "Best sneakers for walking in different seasons" (Contextual usage)
    3.  "Sneakers for walking on a trail" (Terrain specificity)
    4.  "Best slip-on sneakers" (Feature specificity) [cite: 11].

This granularity means that to rank for the broad term, a website must possess content that addresses these specific, narrower sub-queries. The AI is effectively performing a "content gap analysis" on the user's behalf, looking for pages that cover the specific facets it has identified as relevant.

### 3.3 The Merging Process (Synthesis)
Once the parallel searches are complete, the system enters the synthesis phase. This is where the "Fan-In" occurs.
*   **Clustering:** Retrieved results are grouped into clusters based on intent, source type, and entity type [cite: 4].
*   **Cross-Referencing:** The AI evaluates the retrieved documents for consensus and authority. It prioritizes "high-quality, granular content with strong signals of trust" [cite: 12].
*   **Citation Layering:** The final output is a generated text that integrates information from multiple sources. Crucially, the system layers citations, linking specific claims in the generated text to the source documents that provided that specific fragment of information [cite: 4, 13].

## 4. People Also Ask (PAA) as Visible Fan-Out

While the internal logic of Gemini 2.5 is proprietary, the "People Also Ask" (PAA) feature in Google Search provides a publicly visible approximation of the fan-out logic. PAA boxes represent Google's existing map of related intents and follow-up questions, making them an invaluable dataset for reverse-engineering the sub-queries AI Mode is likely to generate.

### 4.1 PAA as the "Blueprint" for AI Reasoning
Research suggests that PAA questions often align with the sub-queries generated during the fan-out process [cite: 5]. PAA reflects the "next steps" a user typically takes, which is exactly what the AI attempts to automate.
*   **Predictive Modeling:** PAA data is essentially a historical record of query refinement. If users searching for "vegan diet" frequently click on "is vegan diet healthy for heart," the AI Mode is highly likely to generate "benefits of vegan diet for heart health" as a sub-query during fan-out [cite: 14].
*   **Intent Mapping:** By analyzing PAA, SEOs can map the "intent graph" of a topic. This graph represents the nodes (questions) and edges (relationships) that the AI traverses to build a comprehensive answer [cite: 6].

### 4.2 Tactics for Using PAA Data
To optimize for Query Fan-Out using PAA data, a more sophisticated approach than simple list generation is required.

**Tactic 1: Recursive PAA Mining**
Do not stop at the first layer of PAA questions. Click on a PAA question to expand it, which generates new, deeper questions. This simulates the "recursive search" capability of AI Mode [cite: 2].
*   *Action:* Map PAA questions 3-4 levels deep to identify niche sub-topics that might be triggered by a complex query.

**Tactic 2: Categorization by Intent Facet**
Group PAA questions into logical categories (facets) such as "Cost," "Process," "Safety," "Alternatives," and "Technical Specs."
*   *Rationale:* AI Mode decomposes queries into subtopics [cite: 1]. These subtopics usually correspond to these logical facets. Ensuring your content covers all these categories increases the probability of being retrieved for multiple sub-queries.

**Tactic 3: The "Answer a Facet" Mentality**
Instead of writing a single FAQ section, adopt an "Answer a Facet" mentality. Treat each major PAA theme as a distinct sub-topic requiring a comprehensive answer, not just a one-sentence reply [cite: 7, 15].
*   *Implementation:* If PAA shows questions about "safety," create a dedicated section or even a separate page (linked to the hub) that exhaustively covers safety, citing studies and expert opinions.

## 5. Content Structure for Multi-Sub-Query Capture

The Query Fan-Out architecture demands a specific content structure. Since the AI retrieves specific fragments to answer sub-queries, content must be structured to allow for easy "parsing" and extraction of these fragments.

### 5.1 Structural Requirements for AI Parsing
Liz Reid emphasized that AI Mode looks for "high-quality, granular content" [cite: 12]. To be "granular" and accessible to the AI, content should follow these guidelines:

1.  **Descriptive Subheadings (H2/H3):** Use headings that explicitly state the sub-topic or question being addressed. This helps the decomposition engine map a sub-query (e.g., "best sneakers for trails") directly to a specific section of your page [cite: 3].
2.  **The "Inverted Pyramid" for Sections:** Within each subsection, place the direct answer immediately after the heading (2-3 sentences), followed by detailed elaboration. This "concise summary" format is preferred for AI Overviews and likely for AI Mode synthesis [cite: 16].
3.  **Structured Data (Schema):** Implement robust schema markup, particularly `FAQPage`, `Article`, and `HowTo`. While not a direct ranking factor, schema helps the AI disambiguate the content and understand the relationship between questions and answers [cite: 15, 17].
4.  **Lists and Tables:** Use bullet points and comparison tables. These formats are highly "parsable" and are frequently used by AI to construct comparisons and lists in the final output [cite: 3].

### 5.2 Optimizing for "Zero-Click" Citations
A significant portion of AI Mode interactions may result in "zero-click" satisfaction, where the user reads the AI summary and does not click through. However, citations are still valuable for brand authority and visibility.
*   **Brand Mentions as Signals:** Ensure your brand is associated with authoritative answers. Unlinked brand mentions and positive sentiment are signals used to assess trustworthiness [cite: 7].
*   **Unique Data Points:** To earn a citation (link), provide unique data, original research, or contrarian viewpoints that the AI cannot find elsewhere. Generic information is easily synthesized without attribution; unique data requires a citation [cite: 7].

## 6. Strategic Content Models: Hub-and-Spoke vs. Pillar

To capture the wide net of sub-queries generated by fan-out, the organization of content across a website is as important as the content itself. The two dominant models—Pillar and Hub-and-Spoke—must be adapted for the AI era.

### 6.1 The Evolution of the Pillar Model
Traditionally, a "Pillar Page" was a massive, long-form guide covering a broad keyword, with links to blog posts. In the context of Query Fan-Out, the Pillar Page must evolve into an **Entity Hub**.
*   **The "Reverse Fan-Out" Strategy:** Think of a content pillar as a "fan-out in reverse." Just as the AI breaks a topic down, your pillar should build it back up, aggregating all the sub-topics (spokes) into a cohesive whole [cite: 18].
*   **Comprehensive Topical Authority:** The goal is not just to rank for the head term but to establish "Topical Authority." The AI evaluates whether a site is an authority on the *entire* cluster of related entities. If your site covers the main topic but lacks depth on the sub-queries (spokes), the AI may prefer a competitor who covers the full spectrum [cite: 4, 7].

### 6.2 Hub-and-Spoke Architecture for AI
The Hub-and-Spoke model is superior for Query Fan-Out optimization because it aligns perfectly with the decomposition/synthesis mechanism.

*   **The Hub (Synthesis Target):** The central page serves as the synthesis point. It provides the high-level overview that matches the user's initial broad query.
*   **The Spokes (Sub-Query Targets):** Each spoke page is dedicated to a specific sub-query or facet (e.g., "Safety of X," "Cost of X," "History of X").
    *   *Why this works:* When the AI "fans out" the query "Guide to X" into "Safety of X" and "Cost of X," it finds your specific spoke pages. Because these pages are semantically linked to the Hub, the AI recognizes the cluster's authority.
    *   *Parallel Retrieval Alignment:* Since the AI executes searches in parallel, having distinct, high-quality pages for each sub-topic increases the surface area for retrieval. Your site can potentially provide the source material for *multiple* sub-queries simultaneously [cite: 4].

### 6.3 Recommendation: The "Cluster-First" Approach
For AI Mode, we recommend a **Cluster-First** approach:
1.  **Identify the Core Entity:** (e.g., "Cloud Computing").
2.  **Map the Fan-Out:** Use PAA and tools to identify the 10-20 likely sub-queries (e.g., Security, Cost, Providers, Implementation).
3.  **Build the Spokes First:** Create deep, granular content for each sub-query.
4.  **Construct the Hub:** Build the central page that summarizes and links to the spokes.
5.  **Interlink Semantically:** Use descriptive anchor text that matches the sub-query intent when linking from Hub to Spoke and vice versa.

## 7. Conclusion

Google's Query Fan-Out technique represents a fundamental change in search engine architecture. By moving from keyword matching to intent decomposition and parallel retrieval, Google has shifted the optimization goalpost. Success in AI Mode is not about optimizing for a single string of text, but about constructing a web of content that anticipates and satisfies the "multitude" of sub-queries the AI will generate.

The "People Also Ask" feature serves as the Rosetta Stone for this new language, offering a glimpse into the AI's reasoning logic. By leveraging PAA data to build robust Hub-and-Spoke content clusters, digital marketers can align their architecture with Google's own, ensuring that when the AI fans out a query, it finds their content waiting at every node.

## References
[cite: 1, 2] Google I/O 2025 Keynote & Liz Reid Announcements
[cite: 3, 12] Technical Analysis of Query Fan-Out Mechanics
[cite: 18] Content Strategy & Pillar Models
[cite: 7] AI Mode & SEO Implications
[cite: 3, 4] Topic Clusters & Sub-Query Optimization
[cite: 5, 14] PAA & Intent Mapping
[cite: 6, 8] Fan-Out Visualization & PAA Strategy

**Sources:**
1. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGbdMqySbwnx9v78Ta_UusY1y7AfjyH3-Loft95xmeppHXZqae3R9ZDP3sJ-uPE1-gpEhGN6yLt4uzq6ufHLZBOTFRbZ0nDX6wdFUFnSM2sNN1VhqVV-QVE8pGTvp0aHQwR)
2. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGu8Yox4H-1r2a8D1L2i-OlgW-g4vzQpq9e6OcE25E6rIO686g8hRGZEFDhKAfqUnami12Y47CQ91iXqj4But7t9U6pnTnFVKVEYnwH0PToV-66P4L88z6dxTmnguVwJJHB)
3. [semrush.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEuK6igueGpCFVnwKlX0y_tCID-10RUYirPpnrbXJmG3JI0sIwO0uGOxRmZibHsggSSXCWstuPStGmPJ1NhsttDTa6i5wvw-zJCAkp2ZnRNEm61h96Bvr59dRTHJ5HGw9tj)
4. [susodigital.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGlWfBQNcNoqS-5EKcZ7Nn5zEKvOVdPKNcBg67rZUVtwMnpGEOjWd9ULWu60xM8dNdOvfKpntKmrL_2F-HnB0T03A1BIucxla-GD09jJS_kFC3FntKXIJkurp-ZiL4KYNAqvBziAK2mbBzjD5UqIXfdPbS7rqz5HQqyjii-)
5. [writesonic.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHDId-n-iE_6F6aIslkFOfORkBrCYXiBHoJMwK84u3MnKn0QmkSfbxwMMkqoquUd_CnVo47P3t71s4Fk4n2Tl5E4ZMJIGk5p4mMj0giCMIOCdrxCLo2FW7k7ReDSKDjrz_y6GL5iUb5)
6. [advancedwebranking.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG1mRXka53VVghe1fOfOpsJYkyhf_NkyW2mno1jXVRMQRPM2s0bVom9qvmwNg8GEX2QBVFeN1yOJWH0qW1t7omAuDrHkhcri36ijlLmHC4uCXSFPH9P2B3GvTqEWAopSitjmzoFkY4ukgEYpoBuKOxAxrluCQhk1C_0WD2vPgTh)
7. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFVbMqk-a38cWHrbybxTO1VLsuxs0CA0ulLeSvp_ngDTFmXcJ0ytzN59TLLQT-3ciCDkdP-8g9FkCQV2jHzpmYvC--L29sXbTuAynEnsuUEL8xXUCVZsLB9hyepeaMk6k_siLTFfLo1K7WKk2eJS83T_4FQAw==)
8. [mention.network](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEugbL6T6B7pQ-YZIQOF_ebCUB1Yn386bck1Gia5Px7RNuaMLgJ9mth2DTNkA2KB7YK7U-Nu_FiTZUtVlTS3NIzJBtvQr98fj_AWBoZjCkUqo87HeYr50Pwo7Bp1yem4wJJz_eP8u1lGcXKhwQ=)
9. [casc.at](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEzNr4BeivQ7PODD44ZGKMzyfZGuciAG2udvRry9fEZzRmNLEpIoUHc6bmRJtUrs6PFKxVN24w3_3dNQnJhomfSy71JW2mXYfinhXVNlVF6Ba-4XAm9ZJ-Ygu9b1a2KHDXEAbhS1GionqGcVcdD1gN29FHpch_zTf-VvwFGXMHl)
10. [superlines.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGHUlIYcEU_LIIazv0oLcWkO321d59-hs-Fd-0KhH7dunGAwXjTqnSzh0vSzN2scoLGRZZtkUC8U-TrRSpdfXg6j2viHKEV9XqjYq2L_yl0jssx6WM9up5IhTifRAtHUBhP50omeunfZcApuqiLAQ==)
11. [digiday.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEkxBdinbX7rA6Z-FyJAltMASzNzjTyy1Bm0jdkRsY9LrJa7L8dPWy0j7yrfTDcVSu0EMyncSd53SJDcxaC_II5yE6LAyRzHi5g7xkmcdMvB7cF8nTNMC5_D-TY1Ng-ta2F0lqO2Rk9fKyW8X1G2axD-aVZvyg4WSM=)
12. [milestoneinternet.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGkpbyk2ZSjEHRguEjsKhA51F9vTz5YuR4NpOaGPOYdjjxdQEwK59MleKAhcr6a_O3pQBvRBMsZXiufTLsTDRlhib2ehtkrK-IWrK3XadBJ5aZ1guKNo8xYCvFxypTx0b0LQSjOU0YkLu8yXtrh4xhedAx4J31mBNUengMtFaZzbv3aP1ZneGe9beUSw_roFw4qfW8LJ0Yhcb2B0F5kAwaMwhqrQDMBbtbvfLDZLUy03kp6)
13. [stanventures.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHUbGm3IYN6s0oR82GuYLERBRn0JbE_P_pEw92TY2t_2BTQWIauOa2E372V2n9iFWnj-VmGkie2zsPL9-Zm2h5VTdcjnHRjQW5luE-qDuCC6BwI7bbjKRdX8jkxJgna97qg7CddY7icr08hr65K50LM9KFpNNDcEZEegHxTkQe5e_Q0e5xCcNeiTY5BGxhug4kJ4BdjGkUzazYDp_UhHStbZLuoTepkBZvMu6A=)
14. [niara.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEVIiX6ud6XFQ-95tR9fyAPnyiFgg4CK3EpojRRD_eq54vElK2wkHXveTsmLETiKZPC0bXSzecAP-8OQ1O_vxOUYwuiFKPMGQ3knzpimSeLhawoMRxUA0ExwffJl-Q2Tt4FuNwk)
15. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHBDJ2im75RaWwbdDx7tLdsBYqGNoFrXneYHDJCiXIxTQh5etOxvRQLdq-OR0QkKTPOTN1r7QMrW_EmF59ChFNXn0HURw4sc8l1vF8WayyntvjwmDq9P0TCYVKBJH1sdUbSNVqiwnZDInpkpB9wyHqEFqeJGKv8MYYGu2WTpoo7GhIyt9_WVnJggrjgLqW5K-B_KeHnwuehJrThoPwIPRSzoqm0CqI=)
16. [theadfirm.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGqzrZGxnh6XsENoO7czQKpeaV8CLKFErT4sAt-ceVSxNmWL1e62z3npWA7kxBKhm0cjZVlOX8_K713EH98yYhxX9PezDbWTFU9oLdDkeaQems7eMKUajaqbYce5XrM2CypTPSEmgMuZ1a8ZM1jr_DmK7R08AR3jdqyXfsz0wSIuGUGRhtO2JLfEFOz)
17. [reusser.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEDCC5Ha0Eu_DeAMDgCC0EcPNFt2ZoQXvkIz_lV4yKXZ8YqCLDSEcj9yQSUaB-eiQXzstDcuBEm0gV-iVfAZIilpk-N79ob6e1G11-S3dq0UNQGH0Fym8TbKdv8Zj9T3hDx3pItaWtaAMsevTjw7efLa5kpOqAxILxmCfype4G9sA==)
18. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHsmVpZ-Xo4uYeZ15AQxMUB0Dw1EIGn_e6iE8AuDpRmaJWehUhbNkVPd6mgniMn_1vb-DCEf7FIq12M0Hum27L70Uo5qSvDeFJCIWv7ERR2D0rYNbtIPfel7T-bWaDWwGkY1qoZyYbHnKqgbcEbwJrC5oJp27ZuclO7JeH8hg==)
