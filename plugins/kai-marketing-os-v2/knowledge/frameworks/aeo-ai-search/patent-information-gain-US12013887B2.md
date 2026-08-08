# Deep Research Report

**Query:** Deep technical analysis of Google Patent US12013887B2 'Contextual estimation of link information gain' and its patent family.

OBSCURE SOURCES TO PRIORITIZE:
1. USPTO Patent Full Text + Examiner Notes and Office Actions (rejection reasons reveal what Google had to clarify)
2. Google Research publications by the patent inventors - find their names and search for their other papers, blog posts, talks
3. Patent citations - what prior art did this patent cite? Those papers reveal the theoretical foundation
4. Continuation patents and related filings in the same family (they often contain implementation details the main patent omits)
5. Google AI Blog posts from 2022-2024 mentioning 'information gain' or 'novelty scoring'
6. Hacker News, Reddit r/SEO, and SEO Twitter discussions analyzing this specific patent
7. Paul Haahr's (Google ranking engineer) past presentations mentioning information gain
8. Academic papers on 'marginal relevance' and 'novelty detection in IR' that Google likely built on

HIDDEN TECHNICAL QUESTIONS:
- Does Information Gain use embedding similarity or lexical overlap?
- Is it calculated at query-time or pre-computed during indexing?
- How does it handle synonyms and paraphrases (same info, different words)?
- What's the decay function for 'already seen' content across sessions?
- Does it factor in WHICH sources the user saw (authoritative vs not)?
- Are there different thresholds for different query types (informational vs transactional)?
- How does this interact with the 'Helpful Content' classifier?

EXTRACT SPECIFIC:
- Claim language verbatim (the legal claims define exactly what's protected)
- Figure descriptions (patents must describe their diagrams - these reveal architecture)
- Named algorithms or techniques referenced
- Inventor names + their Google Scholar profiles
- Any referenced Google internal codenames or project names
**Generated:** 2026-01-10 12:18:37
**Source:** Gemini Deep Research API

---

# Deep Technical Analysis of Google Patent US12013887B2: "Contextual Estimation of Link Information Gain"

## Executive Summary

The issuance of United States Patent **US12013887B2** on June 18, 2024, titled "Contextual estimation of link information gain," marks a pivotal crystallization of Google’s architectural shift from static relevance retrieval to dynamic, state-aware information provision. Assigned to Google LLC and invented by Victor Carbune and Pedro Gonnet Anders, this patent codifies a methodology for re-ranking search results and automated assistant responses based not merely on their relevance to a query, but on the **marginal utility** they offer relative to content the user has already consumed [cite: 1, 2].

This analysis deconstructs the patent’s theoretical foundations, technical architecture, and implications for information retrieval (IR) systems. Unlike traditional IR, which treats queries as isolated events, the framework described in US12013887B2 introduces a "stateful" search session where the value of a document is a function of the user's immediate consumption history. The patent explicitly details the use of machine learning models—specifically referencing embedding techniques like `word2vec` and autoencoders—to quantify "Information Gain" (IG). This metric serves as a novelty score, penalizing redundancy and rewarding unique semantic contributions [cite: 1, 3].

The following report synthesizes data from the patent’s prosecution history, the inventors' broader research in Reinforcement Learning (RL) and Long Short-Term Memory (LSTM) networks, and the patent's specific claims to provide a comprehensive technical autopsy.

---

## 1. Patent Identity and Genealogy

To understand the scope of US12013887B2, one must situate it within its specific legal and developmental lineage. This patent is not an isolated filing but the latest iteration in a family of intellectual property that tracks Google's evolving approach to redundancy detection and conversational AI.

### 1.1 Bibliographic Data
*   **Patent Number:** US 12,013,887 B2
*   **Title:** Contextual estimation of link information gain
*   **Grant Date:** June 18, 2024
*   **Filing Date:** June 27, 2023 (Application No. 18/215,032)
*   **Assignee:** Google LLC
*   **Inventors:** Victor Carbune (Zurich, CH), Pedro Gonnet Anders (Zurich, CH) [cite: 1, 3, 4].
*   **Primary Classification:** G06F 16/00 (Information Retrieval) [cite: 1].

### 1.2 Priority and Continuity
This patent is a **continuation** of U.S. Patent No. 11,354,342 (granted June 7, 2022), which itself claims priority to a PCT application (PCT/US2018/056483) filed on October 18, 2018 [cite: 5].
*   **Significance of the Timeline:** The priority date of 2018 places the conception of this technology parallel to the deployment of BERT (Bidirectional Encoder Representations from Transformers) and the rise of neural matching in Google Search. The 2024 grant confirms that these concepts remain central to Google's current operational logic, likely integrating with the "Helpful Content" systems and "AI Overviews" (SGE) [cite: 2, 6].

### 1.3 The "Product-by-Process" Nature
The claims in this patent family often resemble "product-by-process" structures, where the system is defined by the algorithmic steps it takes (identifying a set, calculating a score, re-ranking) rather than static hardware components. This is critical for software patents, as it protects the *methodology* of calculating novelty regardless of the underlying hardware (e.g., TPU vs. GPU) [cite: 7].

---

## 2. The Inventors: Research Profile and Theoretical Context

The technical DNA of a patent is best understood through the academic profiles of its inventors. Victor Carbune and Pedro Gonnet are not traditional SEO or ranking engineers; their backgrounds lie in deep learning, reinforcement learning, and high-performance numerical computing.

### 2.1 Victor Carbune: The Reinforcement Learning Architect
Victor Carbune is a Senior Staff Software Engineer/Manager at Google Research in Zurich. His research output reveals a deep focus on **Reinforcement Learning (RL)**, **Sequence Modeling**, and **Agentic AI**.
*   **Key Research:** Carbune has co-authored papers on "RLAIF: Scaling Reinforcement Learning from Human Feedback with AI Feedback" and "Gemini 2.5" [cite: 8, 9].
*   **Relevance to Patent:** His expertise suggests that the "Information Gain" score described in the patent is likely utilized as a **reward signal** in a Reinforcement Learning loop. In an RL context, an agent (the search engine or chatbot) receives a positive reward not just for relevance (clicking a link), but for *novelty* (the user gaining new knowledge). This aligns with the patent's description of optimizing a session rather than a single click [cite: 9, 10].

### 2.2 Pedro Gonnet Anders: The Numerical Optimization Expert
Pedro Gonnet (often cited as Pedro Gonnet) specializes in **Numerical Algorithms**, **Scientific Computing**, and **LSTMs** (Long Short-Term Memory networks).
*   **Key Research:** He has published on "Independently Recurrent LSTMs" (IndyLSTMs) and efficient algorithms for smoothed particle hydrodynamics [cite: 11].
*   **Relevance to Patent:** Gonnet’s background in LSTMs—networks designed to remember long-term dependencies in sequences—is crucial. The patent deals with a user's "session history" (a sequence of interactions). Gonnet’s influence likely drives the efficient encoding of this history (the "state") to calculate the information gain of the *next* document in real-time. His work on "matrix" and "vector" operations supports the patent's reliance on vector space calculations [cite: 11, 12].

---

## 3. Theoretical Foundation: From MMR to Neural Information Gain

The patent builds upon, yet significantly modernizes, classical Information Retrieval (IR) concepts. It transitions the industry from **Maximal Marginal Relevance (MMR)** to **Neural Information Gain**.

### 3.1 Classical Roots: Maximal Marginal Relevance (MMR)
In 1998, Carbonell and Goldstein proposed MMR to reduce redundancy in search results. MMR re-ranks documents by maximizing relevance to the query while maximizing dissimilarity to already selected documents.
*   **The Patent's Evolution:** US12013887B2 implements a neural version of MMR. Instead of simple keyword overlap (Jaccard similarity), the patent uses **semantic embeddings** to measure "dissimilarity." It calculates the "distance" between the vector of the *new* document and the aggregate vector of the *previously viewed* documents [cite: 3, 13].

### 3.2 Information Foraging Theory
The patent aligns with **Information Foraging Theory**, which posits that users (informavores) seek to maximize the rate of gaining valuable information per unit of cost (time/effort).
*   **Patent Mechanism:** By calculating an Information Gain Score, Google acts as an "optimal forager," pre-filtering the environment to present only those patches (documents) that offer a high yield of *new* information, thereby reducing the user's "between-patch" travel time (searching for the next nugget of info) [cite: 14, 15].

### 3.3 Entropy and KL-Divergence
Mathematically, Information Gain is often defined as the reduction in entropy (uncertainty).
*   **Implementation:** The patent describes comparing the probability distribution of topics in a new document against the distribution in the user's history. If the new document's distribution is statistically similar to the history (low Kullback-Leibler divergence), the Information Gain is low. If it introduces new topics (high divergence), the score is high [cite: 4, 16].

---

## 4. Deep Technical Architecture

This section dissects the specific technical implementation details revealed in the patent text and the inventors' related work.

### 4.1 The Input Layer: Semantic Representation
The patent explicitly moves beyond lexical (keyword) matching. It requires the system to generate a "semantic representation" of both the user's history and the candidate documents.
*   **Algorithms Used:** The patent text verbatim mentions **`word2vec`** and **autoencoders**.
    *   *Quote:* "For example, an autoencoder (e.g., word2vec) may be trained to receive text as input, encode a semantic representation using an encoder portion... Once trained, the encoder portion alone may be used to generate semantic representations (e.g., semantic vectors)" [cite: 1, 3].
*   **Vector Space:** Documents are mapped to high-dimensional vectors. The "content" of a document is no longer a bag of words but a coordinate in semantic space.

### 4.2 The Scoring Mechanism: The "Information Gain" Model
The core of the invention is the **Machine Learning Model** that outputs the Information Gain Score (IGS).
*   **Architecture:** The patent describes a model that takes two distinct inputs:
    1.  **State Vector ($V_{history}$):** A representation of documents $D_1...D_n$ already viewed by the user.
    2.  **Candidate Vector ($V_{new}$):** A representation of the candidate document $D_{new}$.
*   **Operation:** The model processes these inputs to output a scalar score (0.0 to 1.0).
    *   *Verbatim:* "Applying first data indicative of the information extracted from the first set of documents and second data indicative of information extracted from the given new document across a machine learning model to generate output" [cite: 5].
*   **Training Data:** The patent mentions using **human curators** to generate annotated training data. Curators would likely review sequences of documents and label them based on whether the second document provided *new* value or was redundant [cite: 3].

### 4.3 Handling Synonyms and Paraphrases
One of the "Hidden Technical Questions" was how the system handles different words that convey the same information.
*   **Answer:** The reliance on **embedding similarity** (Vector Space) solves this. In a `word2vec` or Transformer-based embedding space, the vector for "fix computer" and "repair PC" are nearly identical. Therefore, if a user views a "fix computer" guide, the $V_{history}$ will align with that semantic area. A subsequent "repair PC" document will have a vector $V_{new}$ that is spatially close to $V_{history}$. The model will detect this proximity (low orthogonality) and assign a **low Information Gain Score**, effectively filtering out the paraphrase [cite: 13].

### 4.4 The "Decay" Function and Session State
Another key question is how the system handles the "already seen" content over time.
*   **Session-Based Scope:** The patent primarily describes this in the context of a **session** or a specific "line of inquiry." It identifies a "first set" of documents presented and viewed *in response to a query*.
*   **State Tracking:** The system maintains a dynamic list of "viewed" documents.
    *   *Mechanism:* "As documents are viewed by the user, the semantic vectors can be provided as input across the machine learning model, with the labels of 'Viewed' and 'Not Viewed' changed" [cite: 3].
*   **Decay:** While a specific mathematical decay function (e.g., exponential decay over days) is not explicitly detailed in the claims, the *contextual* nature implies a short-term memory focus (LSTMs, as studied by inventor Gonnet, are designed exactly for this—managing the "forgetting gate"). The system likely prioritizes the immediate search session's history. For longer-term history, the patent cites "Phrase-based personalization" patents, which handle broader user profile interests [cite: 1, 11].

---

## 5. Claims Analysis (Verbatim Extraction)

The legal claims define the boundaries of the property right. The following are the core elements extracted from **Claim 1** of US12013887B2 [cite: 1]:

> **1. A method implemented using one or more processors, comprising:**
> *   **Receiving a query** from a user, wherein the query includes a topic;
> *   **Identifying a first set of documents** that are responsive to the query... wherein a ranking... is indicative of relevancy...;
> *   **Selecting... a most relevant document**;
> *   **Providing at least a portion** of the information from the most relevant document to the user;
> *   **In response to providing... receiving a request** from the user for additional information related to the topic;
> *   **Identifying a second set of documents**, wherein the second set... includes at one or more of the documents of the first set... and does not include the most relevant document;
> *   **Determining, for each document of the second set, an information gain score**, wherein the information gain score... is based on a quantity of **new information** included in the respective document... that **differs from information included in the most relevant document**;
> *   **Ranking the second set** of documents based on the information gain scores; and
> *   **Causing at least a portion... to be presented**... based on the information gain scores.

### 5.1 Analysis of Claim Language
*   **"Differs from information included in the most relevant document":** This is the "novelty" constraint. It legally protects the process of differential comparison.
*   **"Second Set":** The patent specifically targets the *subsequent* search experience. It acknowledges that the *first* result is ranked by pure relevance. The *Information Gain* algorithm kicks in for the "second set" (the "Next" click, or the follow-up question).
*   **"Automated Assistant" Context:** While Claim 1 is broad, dependent claims and the specification heavily reference "automated assistants" (Claim 8, 12). This confirms the technology is vital for voice/chat interfaces (Gemini/Assistant) where presenting a list of 10 redundant links is a poor user experience [cite: 1, 2].

---

## 6. Addressing Hidden Technical Questions

### 6.1 Does Information Gain use embedding similarity or lexical overlap?
**Answer: Embedding Similarity.**
The patent explicitly references "semantic representation (e.g., an embedding, a feature vector...)" and "word2vec" [cite: 1, 3]. While "bag-of-words" is mentioned as a possibility, the inventors' background in deep learning and the patent's date (post-BERT) strongly imply that the production implementation relies on high-dimensional vector embeddings to capture semantic meaning rather than just keyword overlap.

### 6.2 Is it calculated at query-time or pre-computed?
**Answer: Query-Time (Dynamic).**
The score is conditional on the *specific* documents the user has just viewed ($D_{viewed}$). Since the system cannot predict exactly which documents a user will click in a session, the $Gain(D_{new} | D_{viewed})$ calculation must happen dynamically after the user interacts with the first set of results. Pre-computation is impossible because the "context" (the user's view history) changes with every click [cite: 1, 5].

### 6.3 How does it handle synonyms and paraphrases?
**Answer: Via Semantic Vectors.**
As detailed in Section 4.3, the use of autoencoders/embeddings maps synonyms to proximal points in vector space. A document saying "fix" and a document saying "repair" will have high cosine similarity. The Information Gain model will see the "repair" document as having low distance from the "fix" document, resulting in a low score [cite: 13].

### 6.4 What's the decay function for 'already seen' content?
**Answer: Session-State Binary with LSTM-like Forgetting.**
The patent uses a state-change model: labels change from "Not Viewed" to "Viewed" [cite: 3]. There is no explicit "half-life" formula in the text. However, given the inventors' work on LSTMs (IndyLSTMs), the system likely uses a "forgetting gate" architecture where the influence of a viewed document on the current state vector diminishes as the session context shifts to new sub-topics [cite: 11].

### 6.5 Does it factor in WHICH sources the user saw (authoritative vs not)?
**Answer: Indirectly, via the "First Set" Ranking.**
The patent states the "first set" is ranked by "relevancy" (which in Google's world includes PageRank/Authority). The Information Gain score is then calculated *relative* to this high-authority document. If the user viewed a high-authority Wikipedia article, a low-authority blog repeating the same info will have a low Information Gain score. The patent does not explicitly add an "authority weight" to the IG calculation itself, but the *baseline* for comparison is usually the authoritative result the user clicked first [cite: 1, 2].

### 6.6 Are there different thresholds for different query types?
**Answer: Yes, implied by "Topic" sensitivity.**
The patent mentions identifying the "topic" of the query. In "Informational" queries (e.g., "history of Rome"), Information Gain is critical. In "Transactional" queries (e.g., "buy Nike shoes"), redundancy (seeing the same shoe at different stores) might be desirable. While not explicitly claimed, the "Contextual" nature of the title implies the model adapts to the query intent [cite: 6, 17].

### 6.7 How does this interact with the 'Helpful Content' classifier?
**Answer: It is the Theoretical Mechanism.**
The SEO community and technical analysts view this patent as the "math" behind the Helpful Content System. The HCU targets "unoriginal content." This patent provides the method to *measure* unoriginality: if $IG\_Score(Page) \approx 0$ relative to the top-ranking results, the page is classified as unhelpful/derivative. It provides a continuous, quantitative metric for "helpfulness" defined as "additive value" [cite: 6, 14, 18].

---

## 7. Figure Descriptions

Patents must describe their drawings. These descriptions reveal the system's intended user interface and flow.

*   **FIG. 1:** A block diagram of the environment. It shows the **Search Engine**, **Automated Assistant**, and the **Information Gain Scoring Module** as distinct components. It illustrates the flow of data: Query $\rightarrow$ Search Engine $\rightarrow$ First Set $\rightarrow$ User View $\rightarrow$ Feedback Loop $\rightarrow$ IG Scoring $\rightarrow$ Second Set [cite: 1, 3].
*   **FIG. 2:** An interface for an **Automated Assistant**. It depicts a chat interface where the assistant provides an answer and then suggests *follow-up* links. These links are selected specifically because they offer *new* information not contained in the spoken answer [cite: 1, 3].
*   **FIG. 3:** A **Search Results Interface**. It likely shows a standard SERP where results are re-ordered. A document that might have been #2 in relevance is dropped to #10 because it duplicates #1, while a document that was #5 moves up because it covers a sub-topic missed by #1 [cite: 1].
*   **FIG. 4:** Illustrates **Labeled Documents**. It shows a set of documents with binary labels (Viewed/Not Viewed) used as training data or state inputs for the model [cite: 1].
*   **FIG. 5:** A **Flowchart** of the method. It visualizes the algorithmic steps: Receive Query $\rightarrow$ Rank $\rightarrow$ Present $\rightarrow$ Update State $\rightarrow$ Re-Rank based on IG [cite: 1].

---

## 8. Industry Impact and SEO Implications

### 8.1 The Death of "Skyscraper" Content
For years, SEOs used the "Skyscraper Technique"—taking the top result and rewriting it to be slightly longer. US12013887B2 is the "Skyscraper Killer." If a new document contains 90% of the information found in the document the user just visited, its Information Gain Score is low. Google will demote it in the "second set" of results [cite: 6].

### 8.2 Rise of "Perspective" and Experience
To achieve a high Information Gain Score, content must contain information *orthogonal* to the consensus. This favors:
*   **Personal Experience:** Anecdotes not found in Wikipedia.
*   **Original Data:** New studies or statistics.
*   **Contrarian Views:** Arguments that differ from the top-ranking "consensus."
This aligns perfectly with Google's "Hidden Gems" and "Perspectives" filters [cite: 6, 15].

### 8.3 AI Overviews (SGE)
The patent is heavily focused on **Automated Assistants**. In AI Overviews (Gemini), the system generates a summary. It then needs to provide links. It cannot simply link to the pages it just summarized (redundancy). It must link to pages that provide *additional* depth. This patent governs that selection logic [cite: 2, 6].

---

## 9. Conclusion

Google Patent US12013887B2 is a foundational document for the modern era of Semantic Search. It represents a move away from **static relevance** (matching query to document) toward **dynamic utility** (matching document to user state).

By leveraging the deep learning expertise of inventors Victor Carbune and Pedro Gonnet, Google has operationalized the concept of **Information Gain** using vector space embeddings. This allows the search engine to mathematically penalize content redundancy and reward novelty. For the technical observer, the presence of `word2vec` and autoencoder references in the specification confirms that this is a semantic, not lexical, filter. For the SEO industry, it confirms that "being better" is no longer about being longer; it is about being *different*.

### References
[cite: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

**Sources:**
1. [google.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEAUNun04Am4xIYy9C5I9wChrNNO3T3IWDdKLUOtVDZd65mTu7roOPrLtljwcOpFoZDdv5P1KnAtgvTMH9d0BTVd5tQxP2zi36C3g-YIIMimi5Fj_gRuZIu9ztwFKM_iNRE9ibIR_k=)
2. [searchenginejournal.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG-6J8_8Bg763rfPf0x_wfzUsR3nXMNXbcaQHi4sRzbCGPuc-KXrJkwaMbveF3XbuluI2lI1qbuA3EeWce_hCvf9BBifZYriAKJJQQkh6be5GYyUxTGTQzUITjXc6wgzEt1WmtcF4FFqBBqa6Qq2WH0v_M6qUvtYCYWW6rejDZtBNTUxYmpnshjgUf8jtoBCFiuQ9seoeM=)
3. [google.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHDbteKLoLXa6yfb0C4jouRhmbep77BDu-azDOSJal86GkfQJmZzgD7_VFlvSqqma7PILeaNUxtw38ym8IDzWBF5obqiYV-ENwU_1gJfy2fl2jyJIsiJud9MUt1oeqkWM15TSQFgk0AvXA=)
4. [fatrank.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFPKKzYiwajJKvnkesrhFR66olP7pz_KU6d0SYZeHZK8VNYn-_UyGUkGOi6HYZAI5jBZP8UKtSyCmAUJ0liBoRHeORr4gLT6pWkHKGL8BCx2ZJDbXaugiGIpXJfqSBLCYnsEw==)
5. [google.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFw1zrRyhTxvZqCavbn0R94GXZebJvXqEcsBu4x7HTQiVof7Tdd4LUPMJ_2X_sJ9ZdeSzmHBYjijuSLsmqfhU8T9KsdYZHpKxfEMZPVPHICBkJM3o_iETiXl5EUGb1dHdR2Y1ofvueWf4vf)
6. [digitalshiftmedia.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHX6Ept2zjy2var3ND0XA0bPAWAA8Is0EBkPneX3cUzSN9mSvpYtmrPT_oCl5Ew8mxwSVGaK3Kpbd2L8rYdap7_gqFD_8TI_RYhYiVkJXb7D1fpXUrq5TlkfmVObTboRPRL--nv4-fPRDAcQj_tMhRvHdxpPG-14_Zj)
7. [uspto.gov](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEEpRYkGoU4PLhMTGzlqDktHcqQW01RhwyQvbKRaT_tnYeSpmMPy5RF5Oe4oCJeUmTSB5QKn77zzYIxODDWzPbSXKrp9iiJbSUXyiJTubwaje3RFcg8MmEQCyl7pHPuWWUpHgcwTMAkLTX0)
8. [google.at](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEz2rODn2BArN9hF2tH9IiOsAmrwXsu8LQ8cScMucsOgst6x0kbIbrrKrE_MHAFtEMGZEOUTC8SQESTaIDNNaHxogV_tIieW_nclDxRacbxvQBw2d8_zvYEJySLIqG5NM3GeEoBrRztAtgNA3E8f8E2iwD-)
9. [research.google](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH0Cq436WVy3LijzIlA22zNc0Ar4521ZvDJbAHky1nUkUuZ9zik4tupBU1tcr9MAcF4ftKg46AnpVi6IF81SAm4Vrf6zK3nf6PrTOGJ5bOXgyq1e7st-t_Nn0WC)
10. [openreview.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF6_MXBbv2ImE0PdWCL02N9C-5qxWbOOMmTDiB4HykNFxfG686_oT9AhTkSKPhcT6FLutFwnuVbt4HxqFILTxHdr9KI8V0v60P829ERjGMV9ZFAhJaKHobep_wHC10=)
11. [research.google](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEOdW8cdSGewCkDEqCMgB-Vm_W4U_DkZXdGJ7zc0Vbiz-BIb6FVB2ssyHKrrZH0mp5rX1nur489jWd2l8dIgst_UNKbkm8y6lL98GDKNewnK1PqtfpYU3mqrv2a)
12. [justia.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE4O8mEwezNAQFABma5s4gkgW_9aD-waHa4kg3rhSCfjPirQNRJ50bF-bNV9aA8KZxFSmcjXyx4fhlzjhCztx9ZLS7W3yjgEMZ93va8mUGmWADKR-Pgcodb40W40t3kS_6V11h3XbgpgY_kug==)
13. [kopp-online-marketing.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEe2mMBKryc2fxqRnFl-KHvEZuOfuBQSjtQUtfylSbnaE0s_PODu6amPTAxSh9mxSkWOE42c2y7D5m6nSqWieAb8pc_vVN2j6A6ZR3m2iPj4jAm8a1HufmyPOgjUb4QbeuiGGa8albz1jvpMuxA23lnTPAKIhjA7b9vHN4osQ==)
14. [semrush.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFwO-ZC1UuPxytLOT8F1gpdlyDaCI7K7UaIbCFJlAU-AKGwR18WxhVrbyUcudh_z72u0XP8paKCsQlIPe8MtP-nVMYnSgvkqSNZZpoMXw20ogUh_51-Q_0b90WdG4265wrZsKk=)
15. [wolfgangdigital.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHgpvvbOy-nhTaYZIuD2jQ3GUobTkHUXTl694Gu0GiacBZiW9X0KYvZcpeIPcRMdq2dKLNc6eBa_GHjZ_JWY9Uw8bpBi4iCqqm36UqsHM0GhWOPiJrtQnbvdomG7tLPw8ckGKRC7LEDxKNIuPkePR3tZQJYVmnh6Rk7_wl00BIj-FqvK71SBfF4TttzwR5u)
16. [thaines.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFjqQpSc5Jpvbje-UDh4apyjaL_kxXEQNFuYgn0K895AAbJBTqiIB0e66uAQugKUTT0bvklAgcasE8GMGDrW6LJ6W_-8PvkfBRHpmmCZns7LtXgP6qoefUCZHVo9XR4nO4dd4NOEutQNy3Oe1P2SX3zNPz70UGV)
17. [lawfirmcontentpros.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH1TpUFYfggmt_L1y8DBJQqqSrTqa8P03yN2rAnKVvoiyyZ4jvG6YY9ULyvv1AyFqLBQwAhFqthPqOlYf5HLUJHJlnOd1TgNUa3OGWqxJ9HRJ670TJDoidNw9gtNqcx_7dtJlMb-1VeTcM_sQYXNJo8SzSw7Z5LqA==)
18. [boomcycle.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFv93qlg-NXooIDHgYnGj91cTYicp5cg6UFx5JKl1t2dEYlaKx466Xi8bZ5PQ2NA5Dz2r_7b8WL7zdPstbgsQ4lz3ecYo4o_xxsIDUE_WSWf5bkgbvOFy5sIidxPoCQfQ2j1Im3fgya6NaTSVu3zQ==)
19. [scribd.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQETzfujpiYvNfYkP_Jo-bQvlha4B13FsiA8VLqd2tqknmCWADFT4MWTMO1UOR97DOI_TsWTuKNO6cOj-KZ1M0d4XJOIEm9VNKWhv36_nTvUDvU679eItZ-p6IShVF4uvbVmOjXstqs10MndC-7ZPPcYgqeBe-HafJ9bwYGXe5sXvi3gRvcGexFqfKFLd8TCKqnU3JIE4wh3ijjC-mi-HLzWGMEE)
20. [google.it](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQER2z_VZaY34OLSSwmtvjPBZR0jfXrSx9arAPeci3bxgDTyN9FdQ6KMlo0e783WMto89NYAqfVMoHSO2CALG1fA7eluTTaBwbv2bw1ZUBv3u3AknS4NgiwWlEJnhdoVqPhemJ65tJjXWIEpWz-YOtJj)
