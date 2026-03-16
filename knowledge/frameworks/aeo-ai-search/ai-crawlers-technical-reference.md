# Deep Research Report

**Query:** llms.txt specification and AI crawler user agents - technical implementation guide.

FOCUS ONLY ON:
1. llms.txt exact file format, location, directives (from Jeremy Howard's proposal)
2. Complete list of AI crawler user agents: GPTBot, ClaudeBot, PerplexityBot, Google-Extended, Bytespider, CCBot, etc.
3. robots.txt configurations for AI bots - allow RAG but block training
4. How major sites (NYT, Reddit, Wikipedia) handle AI crawlers
5. Difference between training crawlers vs retrieval/RAG crawlers

OUTPUT: Exact user agent strings, robots.txt examples, llms.txt format specification
**Generated:** 2026-01-10 13:22:20
**Source:** Gemini Deep Research API

---

# Technical Guide to AI Web Standards: llms.txt, Crawler User Agents, and Access Control

### Key Points
*   **llms.txt** is a proposed standard file located at the root of a domain (e.g., `example.com/llms.txt`) designed to provide Large Language Models (LLMs) with a curated, Markdown-formatted map of a website's most important content for inference-time retrieval.
*   **AI Crawlers** are distinct from traditional search engine bots; they are categorized primarily into **Training Crawlers** (bulk data collection for model weights) and **Retrieval/RAG Crawlers** (real-time fetching for user queries).
*   **Access Control** via `robots.txt` now requires granular configuration to distinguish between these categories. It is possible to block training bots (e.g., `GPTBot`, `ClaudeBot`) while allowing retrieval agents (e.g., `ChatGPT-User`, `Claude-User`) to ensure visibility in AI-generated answers without surrendering intellectual property for model training.
*   **Google-Extended** is a unique `robots.txt` token, not a User-Agent string, allowing webmasters to block Google's AI training data collection while maintaining visibility in Google Search.

---

## 1. Introduction

The architecture of the open web is undergoing a fundamental shift. For decades, the primary machine consumer of web content was the search engine crawler (e.g., Googlebot), designed to index content for keyword-based retrieval. Today, a new class of automated agents—AI crawlers—dominates network traffic. These agents serve two distinct purposes: **Training**, where content is ingested to build the underlying weights of foundation models, and **Retrieval-Augmented Generation (RAG)**, where content is fetched in real-time to ground AI responses in current facts.

This technical guide provides a comprehensive specification for the emerging `llms.txt` standard, a detailed registry of AI crawler User Agents (UAs), and implementation strategies for `robots.txt` to manage the delicate balance between AI visibility and data sovereignty.

---

## 2. The llms.txt Specification

Proposed by Jeremy Howard of Answer.AI in late 2024, `llms.txt` is a standard designed to help LLMs navigate websites during inference (runtime). Unlike `sitemap.xml`, which is designed for search engine indexing, `llms.txt` is designed to be semantic and concise, providing a "clean" path to text-heavy content stripped of HTML boilerplate.

### 2.1 File Location and Discovery
*   **Path**: The file must be located at the root of the domain.
    *   **Correct**: `https://example.com/llms.txt`
    *   **Incorrect**: `https://example.com/assets/llms.txt`
*   **Discovery**: AI agents are expected to check this path deterministically, similar to how `robots.txt` is accessed [cite: 1].

### 2.2 Exact File Format
The file must be written in **Markdown**. It follows a strict structural hierarchy to ensure it is machine-parsable while remaining human-readable.

#### Structure Requirements
1.  **H1 Header (Required)**: The file must begin with an H1 tag containing the project or site name.
2.  **Blockquote Summary (Required)**: Immediately following the H1, a blockquote (`>`) must provide a concise summary of the site's purpose. This helps the LLM decide if the site is relevant to the current user query.
3.  **Detailed Information (Optional)**: Markdown paragraphs or lists (no headers) providing context, usage instructions, or API key details.
4.  **File Lists (Optional)**: Sections delimited by H2 headers (`##`) containing lists of links to the actual content.

#### Link Syntax
Links within the H2 sections must follow standard Markdown syntax, with an optional description separated by a colon:
`- [Link Title](URL): Optional description of the content.`

#### The "Optional" Section
If an H2 section is titled `## Optional`, the LLM interprets the links within it as secondary information that can be skipped if the context window is limited or the query is simple [cite: 1].

### 2.3 Example llms.txt File
Below is a compliant example based on the official proposal:

```markdown
# FastHTML
> FastHTML is a python library which is the fastest way to create an HTML app.

FastHTML allows you to create complex web applications using nothing but Python.
It is built on Starlette and Uvicorn.

## Documentation
- [Quick Start](https://docs.fastht.ml/): A guide to getting started with FastHTML
- [Reference](https://docs.fastht.ml/api/): Full API reference documentation

## Optional
- [Examples](https://docs.fastht.ml/examples/): Example applications built with FastHTML
```

### 2.4 Auxiliary Files
The specification recommends two additional file types to support the main `llms.txt`:

1.  **llms-full.txt**: A single text file containing the concatenated full text of all linked documents. This allows an LLM to ingest the entire documentation in one HTTP request without traversing links.
2.  **Markdown Mirrors (.md)**: For every HTML page (e.g., `docs.html`), the server should serve a Markdown equivalent at the same URL with an `.md` extension (e.g., `docs.html.md` or `docs.md`). This provides a clean, tag-free version of the content for the agent to read [cite: 1, 2].

---

## 3. Comprehensive List of AI Crawler User Agents

AI crawlers identify themselves via the HTTP `User-Agent` request header. Webmasters must distinguish between agents used for **Model Training** (which provide no direct traffic benefit) and **Retrieval/Search** (which provide citations and traffic).

### 3.1 OpenAI
OpenAI employs a split-agent architecture, separating training from runtime retrieval.

| User Agent String | Token (robots.txt) | Purpose | Category |
| :--- | :--- | :--- | :--- |
| `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)` | **GPTBot** | Crawls the web to collect data for training future models (e.g., GPT-5). | **Training** |
| `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot` | **ChatGPT-User** | Browses the web in real-time on behalf of a ChatGPT user (e.g., "Search the web for..."). | **Retrieval** |
| `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot` | **OAI-SearchBot** | Indexes content specifically for SearchGPT/Prototyping search features. | **Retrieval** |

**Note**: Blocking `GPTBot` prevents training but allows ChatGPT to still access your site for answers if `ChatGPT-User` is allowed [cite: 3, 4, 5].

### 3.2 Anthropic (Claude)
Anthropic also distinguishes between training and user-driven actions, though they have legacy agents as well.

| User Agent String | Token (robots.txt) | Purpose | Category |
| :--- | :--- | :--- | :--- |
| `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)` | **ClaudeBot** | General crawler for training data collection. | **Training** |
| `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude/1.0; https://claude.ai/)` | **Claude-User** | Used when Claude browses the web to answer a specific user prompt. | **Retrieval** |
| `Mozilla/5.0 ... compatible; Claude-SearchBot/1.0; ...` | **Claude-SearchBot** | Indexes content for Anthropic's search features. | **Retrieval** |
| `Mozilla/5.0 ... compatible; anthropic-ai/1.0; ...` | **anthropic-ai** | Legacy/General crawler token. | **Training** |

**Note**: `Claude-Web` is an older or undocumented agent often seen in logs, likely associated with earlier training runs [cite: 6, 7, 8].

### 3.3 Google
Google's approach is unique. They do not use a distinct User-Agent string for training in HTTP headers. Instead, they use a **User-Agent Token** in `robots.txt` that controls the behavior of their standard crawlers (Googlebot).

| User Agent String (HTTP Header) | Token (robots.txt) | Purpose | Category |
| :--- | :--- | :--- | :--- |
| `Googlebot` (Standard) | **Google-Extended** | This is a **control token**. Adding `User-agent: Google-Extended` `Disallow: /` prevents Google from using data crawled by Googlebot for training Gemini/Vertex AI. | **Training Control** |
| `GoogleOther` | **GoogleOther** | Generic crawler for non-search tasks, often used for R&D and internal training datasets. | **Training/Misc** |
| `Google-Vertex-AI-Search-Bot` | **Google-Vertex-AI-Search-Bot** | Enterprise search crawler for Google Cloud customers. | **Retrieval** |

**Crucial Implementation Detail**: You cannot block `Google-Extended` by User-Agent string in a firewall (WAF) because the string doesn't exist. You must block it in `robots.txt` [cite: 9, 10, 11].

### 3.4 Perplexity AI
Perplexity is an "Answer Engine" heavily reliant on RAG.

| User Agent String | Token (robots.txt) | Purpose | Category |
| :--- | :--- | :--- | :--- |
| `Mozilla/5.0 ... compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot` | **PerplexityBot** | Builds Perplexity's internal search index. | **Retrieval/Indexing** |
| `Mozilla/5.0 ... Perplexity-User/1.0 ...` | **Perplexity-User** | Real-time fetching when a user asks a question. | **Retrieval** |

### 3.5 Other Major AI Crawlers

| Company | Token (robots.txt) | User Agent String Fragment | Purpose |
| :--- | :--- | :--- | :--- |
| **ByteDance (TikTok)** | **Bytespider** | `Mozilla/5.0 ... Bytespider ...` | Aggressive crawler for TikTok search and LLM training (Doubao). |
| **Common Crawl** | **CCBot** | `CCBot/2.0` | Non-profit web archive. **Critical**: Used as the base training set for almost *all* major LLMs (Llama, GPT, etc.). Blocking this blocks the foundation of most open models. |
| **Meta (Facebook)** | **FacebookBot** | `FacebookBot` | Used for speech recognition and AI training, alongside link previews. |
| **Meta** | **Meta-ExternalAgent** | `Meta-ExternalAgent` | Specific crawler for LLM training data. |
| **Amazon** | **Amazonbot** | `Amazonbot` | Used for Alexa and potentially Olympus (Amazon's LLM) training. |
| **Apple** | **Applebot-Extended** | `Applebot-Extended` | Similar to Google-Extended; a control token to opt-out of Apple Intelligence training while allowing Applebot for Siri/Spotlight. |

---

## 4. Robots.txt Configurations: The "Allow RAG, Block Training" Strategy

To maximize visibility in AI answers (which drives traffic) while preventing your content from being used to train models (which devalues your IP), you should implement a "Split-Brain" `robots.txt` configuration.

### 4.1 The Strategy
1.  **Disallow Training Bots**: Explicitly block `GPTBot`, `ClaudeBot`, `Google-Extended`, `CCBot`, and `Bytespider`.
2.  **Allow Retrieval Bots**: Explicitly allow `ChatGPT-User`, `Claude-User`, `PerplexityBot` (if you want to appear in Perplexity search), and `Googlebot` (for SEO).

### 4.2 Implementation Example

```robots.txt
User-agent: *
Allow: /

# --- BLOCK TRAINING CRAWLERS ---
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

# --- ALLOW RAG / RETRIEVAL AGENTS ---
# OpenAI Retrieval (ChatGPT Browsing)
User-agent: ChatGPT-User
Allow: /

# Anthropic Retrieval (Claude Browsing)
User-agent: Claude-User
Allow: /

# Google Search (Required for SEO and AI Overviews)
User-agent: Googlebot
Allow: /

# Perplexity (AI Search Engine)
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /
```

### 4.3 Technical Nuance: Google-Extended
Note that `User-agent: Google-Extended` is placed in `robots.txt` even though the crawler identifies as `Googlebot`. Google's infrastructure parses the `robots.txt` file, sees the `Google-Extended` directive, and tags the data collected by `Googlebot` as "Search Only - Do Not Train" [cite: 11, 12].

---

## 5. Major Site Implementations

How are the giants handling this?

### 5.1 The New York Times (NYT)
*   **Stance**: Aggressive Protection.
*   **Implementation**: NYT blocks `GPTBot`, `Google-Extended`, `ClaudeBot`, and `CCBot`. They have sued OpenAI for copyright infringement. Their goal is to force AI companies to license data rather than scrape it for free.
*   **Effect**: NYT content is excluded from new training runs but may still appear in RAG responses if the retrieval agent is not blocked (though they often block those too to force direct traffic) [cite: 13, 14].

### 5.2 Reddit
*   **Stance**: Paywall / API Only.
*   **Implementation**: Reddit updated their `robots.txt` to block **all** commercial crawlers, including search engines like Bing, unless they have a paid licensing deal (like Google).
*   **Effect**: Reddit data is now largely invisible to unauthorized AI models. They aggressively rate-limit and block unknown User Agents at the WAF level, not just via `robots.txt` [cite: 15].

### 5.3 Wikipedia
*   **Stance**: Open Knowledge.
*   **Implementation**: Wikipedia generally allows all crawlers, including `GPTBot` and `CCBot`. Their mission aligns with the dissemination of knowledge, and they view AI as a way to distribute that knowledge.
*   **Nuance**: They monitor for excessive crawl rates that degrade service performance but do not block based on the *purpose* (training vs. search) of the bot [cite: 13].

---

## 6. Technical Distinction: Training vs. Retrieval Crawlers

Understanding the difference is vital for security and SEO teams.

### 6.1 Training Crawlers (The Harvesters)
*   **Goal**: Download the entire internet to create a static dataset (e.g., Common Crawl, C4).
*   **Behavior**:
    *   **Breadth-First**: They crawl every link they find.
    *   **High Volume**: They may request thousands of pages per second (if not rate-limited).
    *   **Storage**: Content is stored, tokenized, and compressed into model weights.
    *   **Temporal State**: The data becomes "frozen" in time (e.g., "Knowledge cutoff Jan 2024").
    *   **Examples**: `GPTBot`, `CCBot`, `Bytespider`.

### 6.2 Retrieval / RAG Crawlers (The Librarians)
*   **Goal**: Answer a specific user question using live data.
*   **Behavior**:
    *   **Depth-First / Targeted**: They only visit pages relevant to a specific search query.
    *   **Low Volume**: Traffic mimics human browsing patterns (bursty, query-driven).
    *   **Storage**: Content is processed ephemerally to generate an answer and then usually discarded (or cached briefly). It is *not* used to update the model's weights.
    *   **Temporal State**: Real-time.
    *   **Examples**: `ChatGPT-User`, `Claude-User`, `Google-Vertex-AI-Search-Bot`.

### 6.3 The "Agentic" Future
A third category is emerging: **Agentic Browsers**.
*   **Examples**: Anthropic's "Computer Use" or OpenAI's "Operator".
*   **Behavior**: These do not identify as crawlers. They use standard browser User Agents (e.g., Chrome on Windows) and interact with the DOM (clicking buttons, filling forms).
*   **Detection**: Extremely difficult. Requires behavioral analysis (mouse movement jitter, request timing) rather than User-Agent filtering [cite: 16, 17].

---

## 7. Conclusion

For technical implementation in 2025, the "allow-all" approach of the past is obsolete. Webmasters must adopt a tiered strategy:
1.  **Deploy `llms.txt`**: To guide cooperative AI agents to your high-value content.
2.  **Configure `robots.txt`**: To strictly separate training (block) from retrieval (allow).
3.  **Monitor Logs**: For aggressive undocumented bots (like `Bytespider` or `Claude-Web`) and block them at the firewall level if they ignore `robots.txt`.

This architecture ensures your digital estate remains visible and useful in the AI era without becoming unpaid fuel for the next generation of models.

**Sources:**
1. [llmstxt.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEhRRKNSKNzBZq7F5EhjHkymJfXhrbi8UMtTF-tfZ_ZPlk8UC-DEwDkbhhLCVwrXFMMHUNvYfnCiIbCZpR7AfZPD5KvkfUwsPPYew==)
2. [answer.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFtPJD3xFfWSYmdPEfrpODsb-OJEKYs1fh4F2k2GAIvW2_My7XHRCKx3pILeciayKR9jv4PUIPo8D-_PegydxckmZAIncnfA9TFSlWK7zObppwbhrFYmjhRjn5UfbJAlrN4LUWZOFWXXqE=)
3. [webmaster-zone.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHImdFp3OAQY9SaaIZSbIvn5YTGWlIBqZvUR9Wnv9uuIxh5PT0NZ4kBbMzA2c88TPezOsj1Uc3_MqZwPCbUGUW918QKba26tKPLq93elpG3cxMyROH6b8w_UN_yZnfVihUIq9OHl77tV3n9)
4. [searchenginejournal.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGfZyoNmhKJMmgNlJnwWz_2rYhKN8IszSRCrI9zHLG8EGcGBn3U_-64hUnm_ePP0DyjKJuK9Mb16s142qnEm1j46CVMxgZ41pvMr0se4f6tpGTFcmoOcqIfE-LMgYVPn-YbWRBUT_2FwFZ9GKqrrj_yPdN_HcHGvCi8DQ0IuQ==)
5. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFzqqbz17LczkGgZapKI30dzeTG8kg7HHfguEPgbrXu6uc3Zw8aK2k8hu-Krb8qubNbI6RzEGTBgfCH1ifqZrmx9Na0zTa5BA4xUD6ZVHXe7pT4mws2)
6. [tenten.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFI96H49zk8QqSoo_3S1MwjOtCm4LFCFYIkAu_G97ca6kOfZV89VqgmSYThVwm6zp54JJr0O_TUemcIHALSBx5I4NUO1PrrsL8H0mKMMUfQGtElKBgtw6YmChIjOqg9VOLxMSFqsS6pn8r_JJMWd5MGhHYk5v-S7wPjKME4dA==)
7. [xseek.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEbG1bmKW1yxJ8TaYpuELbjp2l59aHIWcxuZhpLCo1VfWOcGxnJoYNfvMtP6gfRmGpWX7OMFc1TJC0-cQTBdP-0CbO9DGa2P-mcZri-vBAuotc9uHkdMoSZDxRe7kSZmdearw==)
8. [darkvisitors.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF-zewjnjQ-tXkT_XAJBSVa0s6mHaH4BLBk67B1pr8R2iVa_-alaolHmYmcNdFnE8IO-3IOG12nwFA-JPllCD0D5Xf5qIDGwQJdSXMatN3glKP0NM0JwGawSjPaDvWFsUk=)
9. [thatware.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE2QFXNygk8U7MKDw5jHBaPQ93COIJH5ecut4s2u6Mm2P8x8D5wT3dc3Tmhp0FT5xnE4NnyxEjndmGGDJumG138Jftys8IHko_A6LJTJzmhWytExeU_oSBGMKF-el4m678wUQUBFmsoEIg=)
10. [datadome.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFt92uVG9XMuivEWFUP6MFsQlcz5CZz-bKDcg9wpuITbXU1iiomw_F9RuhtcnRVSnoqP9UARddx0W5hwf_KVxchzBQvCb0zus20wlCnvMOc8uVFR6IGMHoUPOT4h8xL6w==)
11. [google.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH3trVs-gpJGSHLR39wwagV6Z_MoU0EphO5HfdccN9GBvCViwoArhpYhf_tw835QGlNEtqp10KDjfO9Aul_e-v3pQqHrDp4lcXtC5mLW2fZitshJZdUEOxAad3ekViB0FaMAN3np1EoqTyTlpmxmWiASvWBLJfF9f5ij6_48RM3LuBQXpJowlqQ19Q=)
12. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE_1u_u9lVRW-SV3gneAoFJLkOfzkIfJp91gLhLWezXzby4nVSeCRmn5suytMiSUjYLQKdWDqyRhrQnwpzzfJMj6k1WU1NZTwLfepl7fo9aCJahOTLqrU9F5GSIYNtnzto9_kaJYeAoUJjF5X0B7N3WZc5T4MEg5ZxjaJd-2Z4LKwHhg0iqXSGC)
13. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHG81C7wLyfb5CQLGdp6lDbOVpH8Ra1X_QbGR-GOPpyslMuhEWMwB5vPMh-oeJ-_DTk3F6v5b_qziDkaHTkm4r79BCNXycQ6B_-Iv8WIHmdRShWOkK9CKB60UVKf-MfKpYLvn8B2dpS9i3L1DOBV_dXSBoImSF8c1LYwO5p4ay8A7wKoqSM0vA3wDMC4KvNXi-r5uqO89IXhKujzYbfMlPwJlc6TnFhZQuBZCY=)
14. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH3-yuVxBBKdM0RsE9Vv4trFIwEDr6rx8b_EGd3ESOzD5j_PQUiZ0j4E6c39cuMM-ocrscNCHnKDJWXf1l9ZpyLTmWAyhgdApASFaGKWihVYUndRGUnkCuS9guDydnlaPZUJRC5L7r0TIK32E6Rn3PZVnjKodC-MNyJ6mkmYKYEGkSKp0hNIpPtR3nE23G7rUkH-WoanKoi7pk=)
15. [pcmag.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFVRMQRUAJnQ7qVgbyFXTxU19PIz548fwmPfLblwaWwPbPzBDDtmEGsY2jXaPAkhx09BiWNCRu8J0mTxxhROyaHhK-Tiwnmf1s2D7t7G0v04ynhj_-6n8QLgyKJrbbPdHyJkkXfVZPjq8rxLRG5zYy7PVCza-yIdJam9WpqgFgo4K-lI2Fm7WmR7RAJYIXURuD-ZbUAshB1yVUAUJ5SHfFd)
16. [workos.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE_CtaBw-Aw5zf2CNPCbgmBvVyYlsOkj59f8rKx8k8i2EME7bTY3GkvW5SJfd-RIQHgH8E2v3Xuh9ZY_P0yReuWYzWw29HCU935eM7rvduiKyrxqNm07ODPrfyZtrMjZ0-upCXgJ-vh--1Ozo-3UL8kfVB1hM4N639R6Thibd2vWdLw4SddU5ZXPeH-2JY=)
17. [pageradar.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHLpNVOx5Q3DnKLH0aqOh9iRhZ7j7KKiJK2kTKV-2LW_7DD2tY13TL-eTJ1DeLbwRVgAUCMVJ2ye8jqHdzvdxBSiWAYBJHAvn_29bnrfs03mra7R_LGmd6NYrUqQ5TOPmjLRrex4s0PgbM=)
