# Deep Research Report

**Query:** Meta Andromeda ad retrieval system: Complete technical architecture including hierarchical indexing, model elasticity, sublinear inference, creative signals for targeting, and how it filters millions of candidates. Include official Meta Engineering findings.
**Generated:** 2026-01-13 12:10:51
**Source:** Gemini Deep Research API

---

# Meta Andromeda Ad Retrieval System: Technical Architecture and Algorithmic Paradigm

### Executive Summary
Meta’s Andromeda is a next-generation, AI-driven ad retrieval engine designed to address the computational bottlenecks of scaling personalized advertising to billions of users and millions of creative assets. Officially detailed by Meta Engineering in late 2024, Andromeda replaces legacy heuristic-based retrieval methods with a deep learning architecture co-designed with specialized hardware (NVIDIA Grace Hopper Superchips and Meta’s MTIA). The system introduces **hierarchical indexing** to achieve **sublinear inference costs**, allowing it to process a candidate pool 10,000 times larger than previous iterations without increasing latency. By shifting from static audience targeting to **creative-signal processing** and **sequence learning**, Andromeda fundamentally alters the ad delivery mechanism, prioritizing semantic relevance and temporal user behavior over manual segmentation.

**Key Technical Findings:**
*   **Sublinear Inference:** Andromeda utilizes a hierarchical tree structure for indexing, enabling the system to navigate millions of ad candidates logarithmically rather than linearly, drastically reducing compute time [cite: 1].
*   **Hardware Co-Design:** The system stores precomputed embeddings in the local memory of NVIDIA Grace Hopper Superchips, overcoming traditional CPU-to-GPU bandwidth bottlenecks [cite: 1, 2].
*   **Model Elasticity:** A segment-aware design dynamically adjusts model complexity in real-time, allocating higher compute resources to high-value impression opportunities [cite: 1].
*   **Performance Gains:** Official engineering logs report a **6% improvement in retrieval recall** and an **8% increase in ad quality** on selected segments following deployment [cite: 1, 3].
*   **Creative as Targeting:** The architecture integrates "Sequence Learning," treating user actions as a temporal narrative (similar to a language model) rather than isolated events, effectively making ad creative the primary signal for audience discovery [cite: 4, 5].

---

## 1. Introduction: The Retrieval Bottleneck and the Shift to Andromeda

In the architecture of large-scale recommendation systems, "retrieval" serves as the initial funnel, tasked with selecting a manageable subset of candidates (thousands) from a massive global inventory (millions or billions) to be passed to the computationally expensive "ranking" stage. Historically, Meta’s retrieval systems relied on isolated model stages and rule-based heuristics to manage volume. This approach faced severe scalability limits as the volume of ad creatives exploded due to Generative AI and automated tools like Advantage+ [cite: 1, 6].

The introduction of **Andromeda** marks a transition from heuristic-heavy retrieval to a fully learned, deep neural network (DNN) retrieval paradigm. The primary engineering challenge addressed by Andromeda is the "300-millisecond problem"—the strict latency budget within which the system must identify the most relevant ads for a user impression [cite: 5, 7]. By implementing a hierarchical structure and leveraging massive hardware parallelism, Andromeda enables **end-to-end optimization**, where the retrieval model and the index are jointly trained, aligning the vector space of user intent with the vector space of ad creatives [cite: 1].

## 2. Hardware-Software Co-Design: The Infrastructure of Andromeda

The capabilities of Andromeda are inextricably linked to its underlying hardware infrastructure. Meta’s engineering team co-designed the software architecture with the **NVIDIA Grace Hopper Superchip** and Meta’s proprietary **Training and Inference Accelerator (MTIA)** [cite: 1, 8].

### 2.1 Overcoming the Memory Wall
Prior to Andromeda, retrieval models were constrained by the bandwidth between CPUs (which handled feature extraction and index management) and GPUs (which handled inference). This "memory wall" limited the complexity of the models and the number of features that could be processed in real-time.

Andromeda utilizes **GPU preprocessing**, where feature extraction occurs directly on the accelerator. Crucially, all precomputed ad embeddings and features are stored in the local high-bandwidth memory (HBM) of the Grace Hopper Superchip [cite: 1, 2]. This architecture eliminates the heavy memory I/O overhead associated with transferring data between host CPUs and accelerator GPUs.
*   **Throughput Improvement:** This design achieves over **100x improvement** in feature extraction latency and throughput compared to previous CPU-based components [cite: 1].
*   **Parallelism:** The architecture leverages instruction and thread-level parallelism, utilizing deep kernel fusion to minimize kernel dispatching overhead [cite: 1].

### 2.2 Tail Utilization and Reliability
To maintain stability at this scale, Meta implemented "Tail Utilization" optimizations. In distributed systems, the "tail" refers to the high-percentile latency (e.g., p99) caused by the slowest responding nodes. By optimizing the utilization of the top 5% of servers and implementing better load balancing across heterogeneous hardware, Meta reduced timeout error rates by two-thirds and cut p99 latency by half [cite: 4, 9]. This reliability is essential for Andromeda, which processes significantly higher model complexity than its predecessors.

## 3. Hierarchical Indexing and Sublinear Inference

The core algorithmic innovation of Andromeda is its **Hierarchical Indexing** mechanism, which allows the system to scale its candidate pool by **10,000x** while maintaining **sublinear inference costs** [cite: 1].

### 3.1 The Hierarchical Structure
In a standard "Two-Tower" retrieval model (commonly used in the industry), a query embedding is matched against a database of item embeddings using Approximate Nearest Neighbor (ANN) search. While effective, this often scales linearly or requires significant trade-offs in accuracy for speed.

Andromeda organizes ads into a **hierarchical tree structure** with multiple layers. Instead of scoring every potential ad against the user, the model traverses the tree, evaluating only the most relevant nodes at each layer [cite: 1, 7].
*   **Node Traversal:** The inference process starts at the root and moves down branches that have high probability scores, effectively pruning vast sections of the ad catalog that are irrelevant.
*   **Sublinear Cost:** Because the system does not need to scan the entire catalog, the computational cost grows logarithmically ($O(\log N)$) rather than linearly ($O(N)$) relative to the number of ads [cite: 1].

### 3.2 Joint Training of Index and Model
A critical differentiator in Andromeda’s architecture is that the hierarchical index and the retrieval models are **jointly trained** [cite: 1]. In traditional systems, the index (e.g., a graph or tree) is often built *after* the embeddings are trained, which can lead to a misalignment between the model's understanding of relevance and the index's structure.
*   **Alignment:** By training them together, Andromeda ensures that the index representations are perfectly aligned with the neural network's decision boundaries.
*   **Recall Improvement:** This joint training is credited with the **6% recall improvement**, as it reduces the "quantization error" typically found in decoupled indexing systems [cite: 1].

### 3.3 Semantic Clustering and Entity IDs
While Meta’s official engineering posts focus on the "hierarchical index," industry analysis suggests this manifests as **semantic clustering**. Ads that share similar visual patterns, copy, and conversion objectives are grouped into "Entity IDs" or clusters within the tree [cite: 7].
*   **Implication:** If an advertiser launches 50 variations of an ad that are semantically identical, Andromeda may cluster them into a single node. If that node fails to gain traction during the initial traversal, all 50 variations may be pruned early, never reaching the auction stage. This explains the shift in strategy away from massive split-testing of minor variations toward "distinctly different" creative concepts [cite: 7, 8].

## 4. Model Elasticity and Dynamic Resource Allocation

Andromeda introduces **Model Elasticity**, a mechanism designed to maximize Return on Investment (ROI) for compute resources. Not all ad impressions are of equal value; showing an ad to a user with high purchase intent justifies more computational expense than showing an ad to a passive scroller.

### 4.1 Segment-Aware Design
The system employs a segment-aware design that automatically adjusts model complexity and inference steps in real-time based on available resources and the predicted value of the impression [cite: 1].
*   **High-Value Segments:** For users exhibiting high-intent signals, Andromeda utilizes higher-complexity models (deeper trees, more features) to ensure the highest precision in retrieval.
*   **Efficiency:** For lower-value segments, the system may use a "lighter" version of the model or fewer inference steps.
*   **Result:** This elasticity, combined with the hierarchical structure, boosts overall model inference efficiency by **10x** [cite: 1].

## 5. Creative Signals and Sequence Learning

Perhaps the most significant shift for advertisers is Andromeda’s move away from static user profiling toward **Sequence Learning** and **Creative Signals**. This represents a move from "targeting audiences" to "targeting through creative."

### 5.1 From Snapshots to Sequences
Traditional Deep Learning Recommendation Models (DLRMs) relied on "snapshots" of user data—aggregated features like "User X likes Shoes." Andromeda, however, integrates **Sequence Learning** architectures (transformers) that model user behavior as a temporal stream [cite: 4, 5].
*   **Event-Based Features (EBFs):** The model ingests raw streams of events (clicks, views, purchases) to understand the *narrative* of a user's behavior. It functions similarly to a Large Language Model (LLM), where user actions are "words" in a behavioral "sentence" [cite: 4, 5].
*   **Trajectory Prediction:** By analyzing the sequence (e.g., *User viewed Ad A -> User visited Site B -> User waited 2 days -> User searched for C*), the system predicts the *next* most relevant ad in the sequence, rather than just matching static interests [cite: 5, 10].

### 5.2 Creative as the Data Layer
In this architecture, the ad creative itself becomes a primary data signal. The system analyzes the semantic content of the ad (using computer vision and NLP) and matches it to the user's behavioral sequence [cite: 4, 11].
*   **The "Prospecting Bias":** Because the system relies on rich data sequences, it mathematically favors advertisers and creatives that generate high volumes of signal (events). Small advertisers with low data density may struggle to "teach" the model, leading to a bias toward larger, data-rich accounts [cite: 4].
*   **Semantic Matching:** Andromeda matches the *content* of the ad (e.g., "red flip-flops at the beach") to the specific context of the user (e.g., "planning a vacation"), rather than relying on the advertiser to select a "Beach" interest tag [cite: 6, 12].

## 6. Official Meta Engineering Findings and Performance

Meta’s engineering team released specific performance metrics regarding Andromeda’s deployment in late 2024. These findings validate the architectural shift toward deep learning retrieval.

### 6.1 Quantitative Improvements
*   **Model Capacity:** The sublinear inference design enabled a **10,000x increase** in model capacity (parameter count and complexity) compared to the previous system [cite: 1].
*   **Recall:** The system achieved a **+6% improvement in recall**. In retrieval, recall measures the percentage of *relevant* items that were successfully retrieved from the total pool. A 6% gain at Meta's scale represents a massive increase in the discovery of viable ad candidates [cite: 1].
*   **Ad Quality:** There was a **+8% improvement in ad quality** on selected segments. Ad quality is a composite metric involving user engagement, negative feedback (hiding ads), and conversion rates [cite: 1].
*   **Advertiser Value:** Advertisers using Advantage+ creative (which leverages this system) saw a **22% increase in ROAS** (Return on Ad Spend) [cite: 1, 3].

### 6.2 Infrastructure Efficiency
*   **Throughput:** The system delivered **35% more work** for the same amount of resources due to tail utilization optimizations [cite: 9].
*   **Latency:** p99 latency was reduced by **50%**, ensuring that the increased model complexity did not degrade the user experience [cite: 9].

## 7. Integration with the Broader AI Ecosystem (Lattice and GEM)

Andromeda does not operate in a vacuum; it is the retrieval engine that feeds into a larger ecosystem of AI models.

### 7.1 Meta Lattice
While Andromeda handles retrieval, **Meta Lattice** (introduced in 2024/2025) handles the **ranking** and prediction phase. Lattice is a "model space redesign" that unifies predictions across multiple domains (Feed, Reels, Stories) and objectives (Clicks, Conversions, Installs) [cite: 13].
*   **Data Consolidation:** Lattice allows cross-domain knowledge sharing. Signals learned from a user's behavior in Reels are instantly applicable to predictions in Feed.
*   **Synergy:** Andromeda retrieves the candidates; Lattice scores them using a massive, multi-objective transformer model.

### 7.2 GEM (Generative Ads Recommendation Model)
**GEM** is a foundation model trained on billions of parameters to understand the *content* of ads. It acts as a "central brain," transferring knowledge to downstream models like Andromeda [cite: 14].
*   **Knowledge Distillation:** GEM learns high-level representations of what makes an ad effective and "distills" this knowledge into the retrieval and ranking models, improving their accuracy without requiring them to be as large as the foundation model [cite: 14].

## 8. Conclusion: The "Andromeda Era" of Advertising

The technical architecture of Meta Andromeda represents a definitive move away from manual, heuristic-based advertising toward a fully automated, AI-mediated environment. By solving the scalability challenges of retrieval through **hierarchical indexing** and **hardware co-design**, Meta has created a system that can process **10,000x** more complexity than its predecessor.

For the technical observer, Andromeda is a case study in **sublinear deep learning**—demonstrating how to apply massive neural networks to search problems that were previously thought to require lightweight approximations. For the advertising ecosystem, it enforces a new reality where **creative strategy** and **data signal quality** replace manual targeting as the primary levers of performance, as the system's ability to sequence user intent far outstrips human segmentation capabilities.

### References
[cite: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

**Sources:**
1. [fb.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF93GRyOlOn6YRdQmL3sG5reOOHoRGKvNDmlvZwoc01iH8_cfHNcag20VunqGU0fPmcnb_LiyzGx2Dm1Ip5-VMCWrqPMmpG9rErpXKcbxOeiKp207oyS5bcnSU_dlFOal6OH9tbmI45aYYEulYa4G-1OzYfH1gPNxzIPiYu8VevhGQSed3v8dor0vuIc-UdEKsKDfgbE7kxejiGPFepj8fB5JUTFeDkXMqmnJx9cLI3LWgmNwfLzPqLZibm6bmeLD3gGI4=)
2. [ppc.land](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFgZ-IMlztHWPFeKJNOFqLKBeFTSIhvSEv5II-Nn3SUUGK_JWg8taqZ2CV0sITQHwk99lWRYRDcZfyl9vbpUnr80zb0FrYHUue5_eFSJomiFM3mONaiGi1eD9yWeUQggfuWfTte0Q_Idxj3fMNZsdy3lt7-R842UaqECPgKQMmRmtzCyLF-2j0UQsaEIXNP0dKPhTXRhcQdLw==)
3. [socialnucleus.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFCuyCieUiXJU2PWkDQ2qrssGvg7IjkDjPH-OpWav7yDFKbTjz-qa4cScv-sjQ-ANT3KW6Wraw3qcoVEQ0W5YCD8Z_YLDT2hgt9ThuKa9x-Lo9oqRjfZ8vDfd9vHmuSOuI1zM5R3z7Ms_uNyWAaIE7_NQywMyFlCez4N_C6SnTyCAlJ12B5M_V9Cwb0MlULmVW9gF_y18VxsrnwWjR2MNtoO1x_NsY=)
4. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHSiGnk75EfJZzpTtmuL9yLZfaxAnPW4Ci_BZ1RVthrNJ0BjYIW3vhee03G_rkD1AYJWcdVMhwep_mp4wh9VPAlUcqagfB0HMeFkFFM_kgU558zdW0ZWbt_JhX4XYa9ZV2j6gQY0GzDlZ6V7T7qlzTfzfRtPBojZrj8tNXB7dQ9zgADDlR8BZd6IfyhWecP000bYFpTC48WlZFaI10dJhmQ974i3sdxtZXcFS-euc1dZ0-tigLzmpkGWRathesA4C1n6A==)
5. [fb.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGwafaUoWI_PfcykWAzSf3NA3Rg-N4rQTOYxX-BDo0CIX4ppWDpywYJnH17Ri342D3InF-y1yR-_qE-2ATvWFczR2Z7au3ncgSo-gOsH4QDPz2jHpu-l5Hw1taRM-74Jiy-w3l6NVOQ07IjLNWaFS-Wzb3Z2zJOLTSQXUJXyXP-ilOXRELFeBoZYiuGTGPWyRnYaX944oNFmlKXzG1euCSxq_d7)
6. [storehero.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFuIRmeauBIGwYGVIoQg40WSBXuxN2Zv3xK2dCa2kYdKmWAMsjw3Rod44IiMUglzbokN8RYgCHzISCZCQohAX0vobEkySl9xhTc3KlqGO3ZoaB_RaFfBxze2wnF1QNU5CM7wx-biLPVBciNB0xDLu2LAEVBduA3lvvPvfTUkepjiky-AOCo04Tu4A==)
7. [adsuploader.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHa7KlHUENGNUL6PJd7iz6viOXSQMYuisOtD1T6C8MBePGAkhuhP0YqtUvFxHiZlthQ08cY0sQtiC2ROdUKNFUm5jt6a0u0jwbS8aitfozqArsgjFRUso9kuv_x6kUrsTIV)
8. [segwise.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHiaz4Aqai8Ea1GVAtBzZ9T0xiWFPkrvUTqBx02tjiDmd6s5Oo_KPE64VzzPyS2qdc_RyzqnYCDUvRmCJWKgfZ7RCJiUVmQjNlWixi6z_v9BZZCYl0kp2cNpbvwgti0yURY9y6-qWBxlW0uRc5nRXXXibhg)
9. [fb.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHxHj4Fqd5wCQvEXE9WCB7-WuoYWEYnO8qYsUIuN0yKwx7WNoTldwAEkCs4BMfXpnm11zdihrvlkTcn5wXP8MrblaL6r3T2ERp8H6dw1oF4GDx848C1dcT78KLLvo8urykyj4oNuEqZONqVESS--33-6g2Y-wckQSKJTZy6EHi9xl7LwsAwH46wUVZfE-Dj_x4ujY_BwbqU)
10. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGnxQcJi1MtrF3VGzj9Az_Rsb14zZnG-jXQ85scb433PGh9BbikOcP4V4aIM0_uPewsAHxtkg-B_X4BMSidJKaajJVAjrhhwq-tv1a9IG-aWbxZyR3DXjw4OwbxL10477gq)
11. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFnWJnmuONxqLPeqU8dXhqeibuz7GDzV3D4B_hKf0huAJ6Lj8nDl22qvGeAPDqTvRDouFICV4BRKg_pjI9jG8VCk11gatU0VsngtlQgT0cMwe_aFfdrPTUK-vXWlKIchKhn)
12. [giovanniperilli.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFrXmZuN1tHCZ7lBdrh5Ex4x_HV5CCqQ8Q2rCI6JFVnlovNfE9cuREOMMb4Y7VpKH3wNn8mX64_jED8IOWZpJ5Qs2-uEDeYZp3fQ4E8B78gQOA6D_Xi_Hw5Hhxe0lkuoSvq-Zw8_lp7Y2toYaxpJzu8HxwnsMBx5WGGBbGylqMzP0cBh5h9dM1cFLJWPrLH8iV_J7qAxnntftmD0qDQzq18vtjzDXqetghYDQEgd-BOT9Wl4kiYbxA=)
13. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEZO9XNA97jTw6aQE8cUVSLSTSgCxfJ0WqWrD_LGgEkZZn0-i3dFYm-PqkWqjfT7M6Z3KSQpl5_Iu8pKCI7M0CO626aFxLCWXGgsPGkMyCdumvCWwZJcA==)
14. [fb.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEV4ZBGzRNyElRwyl55We9O7w65dThakRmvuYmB_7fyyVez8Au5DjsLPQz3ZfXMpPPlxtJ0OFQycuAXF-3TCI1gO3aoPlyWTb1JG1FqBgDKPBPC3CdypoGqIUA59cIaXIBMGRn0Ap9tlU4Q60Ps2LKs4gN_Zntf4dw6YDGtQTI9lm2IbT-fPZs7MrVpuNShjrmA5k7c-Z4OzuTlIH-Ld5oRc4PGW_hHC3fcoZgcewIxO-XpzZKvXSGobOOx9zuZh6rApWwkmDyJByxhiTA=)
