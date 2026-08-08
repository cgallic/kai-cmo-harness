## 3. Feed Ranking Architecture: What Actually Powers LinkedIn

The popular narrative holds that LinkedIn's feed is ranked by "360Brew," a 150-billion-parameter foundation model that replaced thousands of separate recommendation systems in a single sweeping overhaul. That narrative is wrong. Primary source documents from LinkedIn Engineering — the Feed-SR paper published February 2026 [^12^], the LLM-based retrieval paper presented at AAAI 2026 [^84^], and the official LinkedIn Engineering blog announcement [^46^] — describe a fundamentally different architecture: a four-stage production pipeline in which a fine-tuned LLaMA-3 3B parameter model handles retrieval, a compact decoder-only transformer called Feed-SR performs rich ranking, and the 150B parameter 360Brew model was evaluated and explicitly rejected for the feed ranking task.

This chapter maps the production pipeline stage by stage, provides a technical deep dive into Feed-SR (the system that actually ranks the feed), and clarifies the critical distinction between what industry observers believe powers LinkedIn and what the engineering papers confirm is running in production.

![LinkedIn Feed Ranking Pipeline](linkedin_feed_architecture_diagram.png)

### 3.1 The Production Pipeline: L0 → L1 → L2 → Re-Ranking

LinkedIn's feed ranking operates as a cascaded multi-stage pipeline in which each stage narrows the candidate pool and increases computational depth per item. The pipeline architecture follows the standard industrial pattern of retrieval → light ranking → rich ranking → re-ranking, but with distinctive model choices at each layer that reflect LinkedIn's specific constraints: sub-50 millisecond latency budgets at retrieval, thousands of queries per second, and a candidate pool of hundreds of millions of posts drawn from a member base exceeding 1.3 billion [^84^].

The following table summarizes the four pipeline stages, their functions, the models deployed at each layer, and the approximate candidate counts.

| Stage | Name | Function | Model / Technique | Candidate Count |
|-------|------|----------|-------------------|-----------------|
| L0 | Candidate Generation | Fast retrieval from heterogeneous sources | Fine-tuned LLaMA-3 3B dual encoder + LiNR GPU index + GNN embeddings [^84^] [^293^] | ~2,000 per request |
| L1 | Light Ranking (FPR) | Calibration and initial filtering per inventory | LightGBM / XGBoost first-pass rankers [^56^] | ~500 per inventory |
| L2 | Rich Ranking (SPR) | Deep sequential personalization | Feed-SR: decoder-only transformer with Pre-LN, RoPE, causal attention [^12^] | ~20–100 candidates |
| Re-Rank | Setwise + Business Rules | Diversity, fairness, MOO, frequency capping | LiGR setwise attention, LiFT fairness, rule-based filters [^37^] [^168^] | Final feed |

The progression from hundreds of millions of candidates to a final rendered feed of roughly 20–50 items requires each stage to operate under strict latency constraints while passing only the most promising subset forward. A failure mode at any stage — retrieval that misses relevant candidates, or light ranking that filters too aggressively — cannot be recovered downstream.

#### 3.1.1 L0 Candidate Generation: LLaMA-3 3B Dual Encoder + LiNR GPU Retrieval

The L0 retrieval stage narrows hundreds of millions of candidate posts to approximately 2,000 per request with a latency budget of "a few milliseconds" and inbound query throughput of "several thousand per second" [^84^]. This stage replaced five separate retrieval systems that previously operated in parallel: chronological network activity indices, global trending sources, geographic trending, collaborative filtering, and multiple two-tower embedding-based retrieval (EBR) systems [^53^]. The consolidation into a single LLM-powered retrieval system was driven by operational complexity — optimizing one of the five legacy sources routinely degraded another, and no single engineering team could tune across all sources simultaneously [^299^].

The retrieval model is a fine-tuned Meta LLaMA-3 3B parameter causal language model used as a dual encoder. Both member profiles and candidate posts are converted into textual prompts and passed through the shared LLM. Member prompts include profile headline, summary, industry, skills, job history, and a time-ordered sequence of previously engaged-with posts. Item prompts include post type, author information, popularity features (quantized into percentile buckets), article metadata, and post text [^84^]. The model produces hidden states H ∈ R^{L×d} which are mean-pooled into fixed-dimensional embeddings. Mean pooling over all tokens outperformed last-token pooling by 12.36% in Recall@10 [^184^], a finding that runs counter to common practice in language model embedding extraction. Cosine similarity between member and item embeddings drives the final retrieval ranking.

The quantization of numerical features represents one of the most consequential engineering decisions in the retrieval system. Raw engagement counts (e.g., "views: 12345") produced a near-zero correlation (-0.0037) between popularity and embedding similarity because LLM tokenizers treat digits as ordinary text tokens [^53^]. Converting raw counts into percentile buckets (1–100) wrapped in special tokens increased this correlation 30× (to 0.1156) and improved Recall@10 by 15% [^184^]. This alignment between retrieval and ranking layers is critical because popularity features carry significant weight in the downstream Feed-SR ranker.

The production serving infrastructure for retrieval uses 48 NVIDIA H100 GPUs for nearline member and item embedding inference, plus 24 GPUs for online GPU-RAR (Retrieval as Ranking) kNN indexing [^84^]. Freshness guarantees are strict: newly created items are indexed within one minute, and embedding updates following member interactions propagate within 30 minutes [^84^]. Matryoshka Representation Learning enables dimension reduction from 3,072 to 512 dimensions with only a -0.8% recall drop, yielding approximately 83% storage savings in the GPU index [^355^].

Online A/B tests demonstrated a revenue lift of +0.8% (p = 0.03) and +0.2% in daily unique professional interactors (p = 0.005) platform-wide. For newer members with fewer connections — the cohort most dependent on suggested content — the gains were substantially larger: DAU +0.23%, interactions +1.17%, and revenue +3.29% (p = 0.03) [^84^].

#### 3.1.2 L1 Light Ranking: LightGBM/XGBoost First-Pass Rankers

Following retrieval, L1 First-Pass Rankers (FPRs) separately score items from each inventory source using lightweight gradient-boosted tree models — typically LightGBM or XGBoost [^56^]. These models operate as calibration layers, mapping heterogeneous candidate signals onto a common probabilistic metric (primarily P(CTR)) so that candidates from different sources become comparable. The L1 stage processes roughly 2,000 candidates per request in 10–20 milliseconds, filtering down to approximately 500 candidates per inventory type before passing the top-k from each inventory to L2 [^56^].

Key signals at the L1 stage include source-specific match scores, real-time contextual features (device, time of day), and frequency capping counters that prevent over-exposure of individual authors or content types. Because L1 models are lightweight, they can be updated frequently and serve as a defensive layer against distribution shift, catching anomalies before they reach the computationally expensive L2 stage.

#### 3.1.3 L2 Rich Ranking: Feed-SR Transformer

L2 is the computational core of the ranking pipeline. Feed-SR (Feed Sequential Recommender) is a transformer-based sequential ranking model that processes the member's recent interaction history — 1,000+ historical impressions — through a decoder-only transformer with causal attention [^12^]. Unlike the retrieval system, which treats member history as a text prompt, Feed-SR operates on embedded representations: each historical post is encoded as just two tokens (an item embedding and an action embedding), interleaved into a sequence that captures temporal ordering [^264^]. This representation is dramatically more compact than the LLM-Ranker approach, which required tens of thousands of tokens to represent the same history [^51^].

Feed-SR replaced LinkedIn's previous production ranker, a DCNv2-based model, in February 2026. It achieved a +2.10% increase in time spent in online A/B tests compared to the existing production system, making it one of the most impactful single model upgrades in LinkedIn's feed history [^12^]. A detailed technical analysis of Feed-SR follows in Section 3.2.

#### 3.1.4 Re-Ranking: LiGR Setwise Attention, LiFT Fairness, and Business Rules

The final re-ranking stage transforms pointwise L2 scores into a coherent feed experience through multiple complementary mechanisms. LiGR (LinkedIn Generative Recommender) extends the transformer with in-session attention blocks that enable setwise scoring — joint evaluation of items within a slate rather than independent scoring of each candidate [^168^]. This setwise attention provides an additional +0.2% Long Dwell AUC gain by automatically improving diversity and reducing redundancy, replacing rigid rule-based diversity filters (such as the previous minimum-two-item gap rules between out-of-network content or posts by the same actor) [^168^]. LiFT (LinkedIn Fairness Toolkit) provides privacy-preserving fairness adjustments that counteract demographic biases in the ranking scores [^37^].

The multi-objective optimization (MOO) layer combines predictions across engagement types — P(Click), P(Like), P(Comment), P(Share), P(Long Dwell) — into a single composite score using weighted combination. These weights are tuned through the XLNT A/B testing platform and adjusted based on product goals [^37^]. Final filtering applies impression discounting (reducing scores for recently seen content), block list enforcement, frequency capping per author, and anti-gaming rules that detect and suppress artificial engagement patterns.

### 3.2 Feed-SR Technical Deep Dive

Feed-SR is the most thoroughly documented component of LinkedIn's feed architecture, described in a 25-author paper published to arXiv in February 2026 [^12^]. The paper provides architectural specifications, training methodology, inference optimizations, and online A/B test results at a level of detail rare in industrial recommendation system publications.

#### 3.2.1 Architecture: Decoder-Only Transformer with Pre-LN, RoPE, Causal SDPA, Scaled Residuals

Feed-SR uses a decoder-only transformer with Pre-LayerNorm (Pre-LN) formulation, Rotary Positional Embeddings (RoPE), causal scaled dot-product attention (SDPA), and scaled residual connections [^51^]. The computational flow follows:

Q, K, V = W_q LN(X_in), W_k LN(X_in), W_v LN(X_in)

Q_r, K_r = RoPE(Q, K)

Attn = W_o Concat(SDPA(Q_r, K_r, V; causal))

Y = RescaleAndAdd(X_in, Attn)

Z = RescaleAndAdd(Y, FFN(LN(Y)))

The Pre-LN formulation is essential for training stability. The paper reports that without it, training AUC collapses to 0.5. Among attention variants, standard softmax attention matched or exceeded sigmoid, SiLU, and ReLU activations in LinkedIn's setting [^51^]. RoPE improved score stability and yielded +0.20% Long Dwell AUC over learned absolute position embeddings — learned absolute embeddings produced unstable average prediction scores because tokens at the same absolute position in different sequences can carry very different semantic meanings [^51^].

LinkedIn also evaluated replacing Feed-SR transformer blocks with HSTU (HiSTorical Transformer Unit, the open-source Meta implementation) but observed consistent performance degradation. At matched compute (10^{17} FLOPs), HSTU decreased Long Dwell AUC by 0.21%. For larger configurations, the open-source HSTU code ran out of memory entirely, while Feed-SR could leverage standard FlashAttention [^51^].

The interleaved post-action sequence representation is central to Feed-SR's efficiency. Each historical post is represented by just two tokens: a post embedding and an action embedding. These are interleaved and processed through transformer blocks with a causal attention mask. Historical context tokens attend causally to preceding tokens, while candidate tokens (appended at sequence end during inference) attend to all context tokens and themselves [^264^]. During inference, all candidates to be ranked are appended to the end of the sequence and scored in a single forward pass — the architectural basis for the 80× speedup described in Section 3.2.4.

The prediction head uses MMoE (Multi-gate Mixture of Experts), which achieved the best performance among Linear, MLP, DCNv2, and MMoE alternatives on both Long Dwell and Contributions responses. Tasks are grouped into passive (click, skip, long-dwell) and active (like, comment, share, repost) sets for gate routing, with dropout applied to post-softmax gates during training to mitigate expert collapse [^51^].

#### 3.2.2 Feature Reduction: From Hundreds to ~20%

Feed-SR uses approximately 20% of the production DCNv2 model's feature set, splitting features into sequence features (processed through the transformer) and context features (fused after the transformer via late fusion) [^51^]. Sequence features per history item include actor/root-actor hashed ID embeddings (from a shared embedding table), a 50-dimensional content embedding, categorical features (actor type, verb type, device OS, connection status), and numeric features (actor popularity, viewer-actor dwell-time affinity, viewer network size). Context features for the candidate post include viewer-actor affinity scores (time-segmented across 7–365 day windows), candidate popularity metrics, bucketed dwell-time popularity (0–5s to >>60s), post age, and viewer network strength [^51^].

The late fusion architecture restricts the sequential encoder to features that benefit from temporal modeling while incorporating additional candidate and context features after the transformer. Offline experiments showed only a 0.07% degradation in Long Dwell AUC when moving one-third of features out of the sequence pathway and into late fusion, yielding approximately 12% reduction in per-step training time [^51^]. The bucketed dwell-time popularity feature alone provides +2.5% absolute Long Dwell AUC lift [^51^]. Feature ablation studies identified actor/root-actor ID embeddings as the single most important feature — consistent with LiGR's independent finding that Actor ID alone achieves Long Dwell AUC 0.731, close to the full model's performance [^168^].

Feed-SR also incorporates member profile embeddings generated by a fine-tuned Qwen3 0.6B parameter model as a late-fused dense feature. These embeddings are refreshed daily and provide greater than +2% AUC gains for members with fewer than 10 historical actions, directly addressing the cold-start problem that plagues ID-based recommendation systems [^51^].

#### 3.2.3 Training: Daily Incremental Updates, Recency-Weighted Loss, In-Session Leakage Mitigation

LinkedIn's ranking models are updated daily using newly arrived interaction data. During incremental updates, the loss is computed only on newly observed interactions while still providing the full historical sequence as input — a form of curriculum learning that avoids reprocessing stale data [^51^].

Recency weighting operates at two granularities. Position weighting applies exponential decay within each training sequence: with half-life set to sequence length, the first position receives 50% weight while the final position receives full weight. Timestamp weighting applies sample-level decay based on data recency with a default 60-day half-life [^51^]. This dual recency weighting ensures the model prioritizes recent behavioral patterns without discarding older data entirely.

In-session leakage mitigation addresses a critical training artifact: user feedback signals are strongly correlated within a session because a member's mental state, available time, and context persist across multiple impressions. To prevent the model from learning these session-level spurious correlations, LinkedIn applies randomization within sessions during training data construction [^51^].

Position debiasing uses a two-pronged approach: Inverse Propensity Weighting (IPW), where per-position propensity scores for click and other actions are computed from offline data and the loss for each post is weighted by the inverse of its position's propensity score; and explicit logit offsets learned for the top 60 feed positions for each label, added to final logits during training [^51^]. During online scoring, items are scored with position set to 5, which the paper found produces well-calibrated predictions since the actual render position is unknown at scoring time [^51^].

#### 3.2.4 Inference: Shared Context Batching and Custom CUDA Kernels

Feed-SR's inference system uses a disaggregated architecture separating CPU-bound feature processing from GPU-heavy model inference, enabling independent scaling and optimal resource utilization [^51^]. The CPU-based inference driver handles feature fetching, tracking, and transformations; a PyTorch inference server runs on GPU with a gRPC interface using Apache Arrow buffers for zero-copy conversion to PyTorch tensors [^51^].

The primary inference optimization is Shared Context Batching: all candidate tokens are appended to the history sequence and scored in a single forward pass via a custom attention mask. Historical context tokens attend to themselves in causal mode, while each candidate token attends to all context tokens and itself. By eliminating redundant reprocessing of the shared history for each candidate, this achieves an 80× speedup on the transformer forward pass for typical workloads with approximately 500 candidates and history length of 1,000 [^51^].

LinkedIn developed a specialized CUDA kernel called SRMIS (Sequential Recommender Multi-Item Scoring) that extends Flash Attention to support Feed-SR's multi-item scoring pattern. The kernel accepts two scalar parameters (context_length and candidate_length) and implements the attention masking directly within Flash Attention, eliminating O((L+N)^2) mask tensor allocation. SRMIS achieves an average 2× speedup over masked SDPA [^51^]. Combined, these optimizations enable Feed-SR to meet sub-second latency requirements despite processing 1,000+ historical interactions per ranking request. Notably, despite being a larger model than the prior DCNv2-based ranker, Feed-SR uses less energy during inference because GPU-based transformer inference is more efficient per FLOP than the CPU-bound DCNv2 computation [^51^].

#### 3.2.5 A/B Test Results: +2.10% Time Spent Overall

Feed-SR achieved a +2.10% increase in time spent in online A/B tests compared to the existing DCNv2-based production model [^12^]. Broken down by member segments, the largest metric gains occurred among the most active member segments, while results remained positive for less active members and neutral for new members [^51^]. This segment-level pattern is consistent with sequential recommenders generally benefiting from richer history signals: highly active members have longer, more informative interaction sequences, while new members lack the historical context that Feed-SR is designed to exploit. The profile embedding component (Section 3.2.2) partially mitigates this cold-start gap by providing +2% AUC lift for members with fewer than 10 actions [^51^].

LinkedIn also evaluated an LLM-Ranker approach (a fine-tuned LLaMA model scoring candidates via full-text prompting) and TransAct (a transformer-based action sequence model) before selecting Feed-SR. The LLM-Ranker showed promising offline results in early experiments but "never achieved superior online performance over the existing production model" [^51^]. TransAct improved offline and online metrics but increased training time and inference latency significantly, especially for longer sequences [^51^]. Feed-SR's selection reflects a deliberate engineering tradeoff: maximizing online metric gains while maintaining serving latency within production constraints.

### 3.3 The Critical 360Brew Clarification

No discussion of LinkedIn's feed architecture is complete without addressing the most pervasive misinformation in the ecosystem: the belief that 360Brew, a 150-billion-parameter foundation model, powers the LinkedIn feed. This section clarifies what 360Brew actually is, why it was rejected for feed ranking, and how the term has been appropriated as marketing shorthand.

#### 3.3.1 360Brew 150B Parameter Model: Three Documented Failure Modes

360Brew V1.0 is a 150-billion-parameter, decoder-only foundation model built on Mixtral 8x22B (Mixture of Experts), developed by LinkedIn's Foundation AI Technologies (FAIT) team over a nine-month period [^82^]. The model formulates recommendation as many-shot in-context learning, verbalizing member profiles, interaction histories, and candidate item features as natural language prompts. It is capable of solving over 30 predictive tasks across at least eight LinkedIn surfaces without task-specific fine-tuning [^82^].

The Feed-SR paper explicitly documents the evaluation and rejection of the LLM-Ranker (the 360Brew approach) for feed ranking. The paper states: "The LLM-Ranker never achieved superior online performance over the existing production model" [^51^]. Three specific failure modes are identified:

First, numeric features proved difficult to encode as text. The LLM-Ranker verbalized all features into natural language prompts, but numerical signals — which are among the most predictive features in recommendation systems, such as dwell-time affinity scores and popularity percentiles — lose precision and discriminative power when rendered as text tokens [^51^].

Second, sequence length made training and serving prohibitively expensive. Because each historical post required hundreds of tokens to represent as text (post content, author description, action type, timestamp), a member's full interaction history consumed tens of thousands of tokens per training example. By contrast, Feed-SR compresses each history item to just two embedded tokens, enabling processing of 1,000+ interactions within standard transformer context windows [^51^].

Third, the LLM-Ranker struggled with network-based recommendations. Relationship strength between members — a critical signal for LinkedIn's professional network graph — is inherently structured and loses semantic richness when converted to textual descriptions [^51^]. ID-based embeddings, which Feed-SR uses for actor and root-actor features, capture network patterns more effectively than verbalized relationship descriptions.

The following table contrasts the 360Brew research model with the Feed-SR production system across key dimensions.

| Dimension | 360Brew (Research / Rejected) | Feed-SR (Production / Deployed) |
|-----------|------------------------------|--------------------------------|
| Architecture | 150B parameter Mixtral 8x22B MoE [^82^] | Compact decoder-only transformer, Pre-LN, RoPE [^51^] |
| Input representation | Full text prompts (10,000+ tokens per history) [^51^] | Embedded tokens (2 per history item: post + action) [^264^] |
| Feature handling | All features verbalized as natural language [^82^] | Sequence features + late-fusion context features [^51^] |
| History length | Limited by LLM context window (~2–3 months) [^82^] | 1,000+ interactions per sequence [^51^] |
| Numeric encoding | Textual rendering (precision loss) [^51^] | Direct embedding + bucketed quantization [^51^] |
| Network relationships | Verbalized descriptions [^51^] | ID embeddings in shared lookup tables [^51^] |
| Training cost | Very high (150B parameters, full attention) [^82^] | Optimized: custom C++ loader, CUDA kernels, shared batching [^51^] |
| Online A/B performance | Never beat production model [^51^] | +2.10% time spent [^12^] |
| Inference latency | Prohibitively expensive [^51^] | 80× speedup via shared context batching + SRMIS kernel [^51^] |

#### 3.3.2 "360Brew" as Marketing Shorthand

The term "360Brew" has been widely adopted in marketing materials, industry analyses, and social media discourse as shorthand for LinkedIn's entire 2025–2026 algorithm overhaul, even though the actual production system does not use the 360Brew model for feed ranking [^37^]. Industry publications have attributed specific reach declines (e.g., "-47% median reach"), engagement signal reweightings, and interest-graph shifts to "360Brew," when these effects are in fact produced by the Feed-SR + LLaMA-3 retrieval architecture described in this chapter.

This conflation is not entirely accidental. LinkedIn's March 12, 2026 engineering blog announcement described the new feed as "powered by LLMs and GPUs" without clarifying which LLMs or distinguishing between the 3B-parameter retrieval model and the 150B-parameter research project [^46^]. The ambiguity allows LinkedIn to claim leadership in foundation-model-powered recommendation while running a more efficient, less computationally extravagant architecture in production. Third-party analyses that purport to measure "360Brew's impact" on creator reach are almost certainly measuring the effects of Feed-SR and the LLM-based retrieval system instead.

#### 3.3.3 What 360Brew Actually Is: Research Pre-Production Model for 30+ Tasks

The 360Brew paper explicitly describes the model as a "research pre-production model," not a deployed production system [^82^]. Its scope extends across 30+ predictive tasks and eight or more LinkedIn surfaces including feed, job recommendations, People You May Know, ads, search, and notifications [^82^]. The paper demonstrates strong performance on both in-domain (T1) tasks and zero-shot generalization to out-of-domain (T2) tasks and surfaces, with the largest performance gap over baseline models occurring for cold-start members who have few historical interactions [^82^].

While 360Brew was rejected for feed ranking specifically, no public confirmation exists regarding its deployment status for other surfaces. The model's zero-shot generalization capability and strong cold-start performance suggest it may be evaluated for or deployed on surfaces where history is sparse and textual understanding of member profiles and item descriptions is particularly valuable — such as job recommendation, where a member's profile and job description are naturally textual, or People You May Know, where mutual connections and profile similarity drive predictions. The paper's withdrawal from arXiv on August 23, 2025 (official reason: "submitter did not have the right to agree to the license") further obscures the model's production status, though the full text remains accessible via ar5iv mirrors [^82^].

### 3.4 Ranking Signals Hierarchy

The production pipeline processes signals across multiple categories with markedly different weightings. Understanding this hierarchy is essential for interpreting how content moves through the system. The following table synthesizes signal priorities from LinkedIn engineering publications, independent research analyses, and industry studies. Precise weightings are not published by LinkedIn; the hierarchy below reflects cross-validated estimates from multiple sources.

| Signal Category | Specific Signal | Estimated Relative Weight | Mechanism / Notes |
|----------------|----------------|--------------------------|-------------------|
| **Dwell time** | Long Dwell (>context-dependent percentile) | Highest-quality binary signal [^315^] | Binary classifier predicting whether dwell exceeds position/content/platform-adjusted threshold; more important than likes |
| **Comments** | Thoughtful comments (NLP-quality-scored) | ~2× a like (effective) [^211^] | NLP quality scoring discounts generic comments ("Great post!"); comment threads trigger aggressive reach expansion |
| **Comments** | Raw comment count | ~15× a like (industry estimate) [^323^] | Raw count used as early-stage signal before quality filtering |
| **Shares** | Reposts / shares | ~5× a like [^323^] | Signals content deserves wider distribution beyond immediate network |
| **Saves** | Bookmark saves | ~3× a like [^323^] | Signals lasting reference value; strong indicator of depth score |
| **Reactions** | Likes and other reactions | 1× (baseline) [^211^] | Passive signal; lowest individual weight but highest volume |
| **Click** | Click-through | Intermediate [^315^] | Predicted by dedicated head in MMoE; correlated with but distinct from dwell |

The distinction between raw signal counts and quality-adjusted signals is operationally significant. LinkedIn's 2026 ranking update introduced "Depth Score" as a composite metric measuring dwell time, comment depth (substantive discussions), saves for later, and private shares via direct messages [^58^]. Depth Score represents a deliberate shift away from surface-level engagement (likes, shallow comments) toward signals that indicate meaningful content consumption. This shift aligns with the broader platform strategy of reducing distribution for engagement-bait content while rewarding material that generates genuine professional value.

Four parallel evaluation systems process every post: News Feed logic (relevance and interest matching), Engagement logic ( predicted click-through and dwell), Trust & Safety classification (spam detection, policy compliance, AI-content flagging), and Design/User Experience logic (format compatibility, external link penalties) [^263^]. Each system operates independently, and a post must pass all four gates to reach its full distribution potential. A post that scores highly on relevance and engagement but triggers Trust & Safety flags — for exhibiting AI-generated patterns or engagement-bait characteristics — receives distribution suppression rather than removal, limited primarily to first-degree connections [^263^].

The signal hierarchy and parallel evaluation architecture explain why posts with high engagement volume sometimes see limited distribution: if the engagement is concentrated in low-weight signals (likes, brief comments) while high-weight signals (long dwell, saves, substantive comments, shares) are weak, the composite ranking score may not justify extended distribution beyond the initial audience test. Conversely, a post with modest engagement but strong depth signals — extended dwell time, multiple saves, thoughtful comment threads — can achieve broader distribution because the quality-adjusted signal profile aligns with what the ranking system is optimized to reward.
