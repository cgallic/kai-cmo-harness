# Dimension 5: LLM-Based Retrieval (AAAI 2026 Paper) — Deep Dive

> **Paper Title:** "Large Scale Retrieval for the LinkedIn Feed Using Causal Language Models"  
> **Venue:** AAAI 2026, IAAI Technical Track on Deployed Highly Innovative Applications of AI  
> **Published:** March 14, 2026  
> **arXiv Preprint:** October 16, 2025 (arXiv:2510.14223)  
> **Pages:** 9 pages, 4 figures

---

## 1. Paper Overview and Metadata

### Full Citation

```
Ramanujam, S. S., Alonso, A., Kataria, S., Dangi, S., Gupta, A., Tiwana, B. S., 
Somaiya, M., Simon, L., Byrne, D., Ha, S., Zhou, S., Akterskii, A., Liu, Z., 
Sriram, S., Xiong, Z., Pei, Z., Shao, A., Li, A., Xiao, A., Kolb, C., Kistler, T., 
Moore, Z., & Firooz, H. (2026). Large Scale Retrieval for the LinkedIn Feed Using 
Causal Language Models. Proceedings of the AAAI Conference on Artificial Intelligence, 
40(47), 40101–40109. https://doi.org/10.1609/aaai.v40i47.41445
```

### Authors (23 authors, all from LinkedIn Corporation, Sunnyvale, CA)

| Author | Equal Contribution? | Role |
|--------|---------------------|------|
| Sudarshan Srinivasa Ramanujam | * | Lead author |
| Antonio Alonso | * | |
| Saurabh Kataria | * | |
| Siddharth Dangi | * | |
| Akhilesh Gupta | * | |
| Birjodh Singh Tiwana | * | |
| Manas Haribhai Somaiya | * | |
| Luke Simon | * | |
| David Byrne | * | |
| Sojeong Ha | | |
| Sen Zhou | | |
| Andrei Akterskii | | |
| Zhanglong Liu | | |
| Samira Sriram | | |
| Zihan (Crescent) Xiong | | |
| Zhoutao Pei | | |
| Angela Shao | | |
| Alex Li | | |
| Annie Xiao | | |
| Caitlin Kolb | | |
| Thomas Kistler | | |
| Zach Moore | | |
| Hamed Firooz | †Work done while at LinkedIn | Principal Scientist, team lead |

### Key URLs

- **AAAI Official Publication:** [https://ojs.aaai.org/index.php/AAAI/article/view/41445](https://ojs.aaai.org/index.php/AAAI/article/view/41445) [^343^]
- **AAAI PDF Download:** [https://ojs.aaai.org/index.php/AAAI/article/view/41445/45406](https://ojs.aaai.org/index.php/AAAI/article/view/41445/45406) [^184^]
- **arXiv Preprint (v1):** [https://arxiv.org/abs/2510.14223](https://arxiv.org/abs/2510.14223) [^173^]
- **arXiv PDF:** [https://arxiv.org/pdf/2510.14223](https://arxiv.org/pdf/2510.14223) [^314^]
- **OpenReview Profile:** [https://openreview.net/profile?id=~Zach_Moore1](https://openreview.net/profile?id=~Zach_Moore1) [^346^]
- **ResearchGate:** [https://www.researchgate.net/publication/402663322](https://www.researchgate.net/publication/402663322) [^186^]

---

## 2. Abstract and Problem Statement

### Abstract (Full Text)

> "In large-scale recommendation systems like the LinkedIn Feed, the retrieval stage is critical for narrowing hundreds of millions of potential candidates to a manageable subset for ranking. LinkedIn's Feed serves suggested content from outside of the member's network (based on the member's topical interests), where **2000 candidates are retrieved from a pool of hundreds of millions of candidates with a latency budget of a few milliseconds and inbound QPS of several thousand per second**. This paper presents a novel retrieval approach that fine-tunes a large causal language model (Meta's LLaMA 3) as a dual encoder to generate high quality embeddings for both users (members) and content (items), using only textual input. We describe the end-to-end pipeline, including prompt design for embedding generation, techniques for fine-tuning at LinkedIn's scale, and infrastructure for low latency, cost effective online serving. We share our findings on how quantizing numerical features in the prompt enables the information to get properly encoded in the embedding, facilitating greater alignment between the retrieval and ranking layer. The system was evaluated using offline metrics and an online A/B test, which showed substantial improvements in member engagement. We observed significant gains among newer members, who often lack strong network connections, indicating that high-quality suggested content aids retention. This work demonstrates how generative language models can be effectively adapted for real time, high throughput retrieval in industrial applications."

### The Core Problem

LinkedIn's feed retrieval had evolved into a **highly complex ecosystem** comprising multiple index types [^184^]:

1. **Inverted indices** of chronologically ordered member activities [^84^]
2. **Trending sources** (global, geographic)
3. **Collaborative filtering** systems
4. **Two-tower embedding-based retrieval (EBR)** systems [^184^]

While this multi-index architecture enabled targeted and personalized Feed experiences, it introduced **significant engineering complexity and operational overhead**, particularly when integrating heterogeneous retrieval signals at scale. Optimizing one retrieval source could degrade another, and no single team could tune across all sources simultaneously [^299^].

### Key Scale Requirements

| Metric | Value |
|--------|-------|
| Candidate pool size | Hundreds of millions of posts |
| Retrieved candidates | 2,000 per request |
| Latency budget | A few milliseconds |
| Inbound QPS | Several thousand per second |
| Member base | 1.3 billion members |
| Context length | 20,480 tokens |

---

## 3. Dual Encoder Architecture

### 3.1 Overall Architecture

The system uses a **dual-encoder architecture with a single shared LLM** that encodes both members and items into a shared embedding space [^314^].

```
┌─────────────────────────────────────────────────────────────────┐
│                    DUAL ENCODER ARCHITECTURE                    │
├──────────────────────────────┬──────────────────────────────────┤
│     MEMBER SIDE              │        ITEM (POST) SIDE          │
│                              │                                   │
│  ┌──────────────────┐       │  ┌──────────────────┐             │
│  │ Member Prompt    │       │  │ Target Post      │             │
│  │ (Profile +       │       │  │ Prompt (Post     │             │
│  │  History)        │       │  │  features)       │             │
│  └────────┬─────────┘       │  └────────┬─────────┘             │
│           │ Tokenize         │           │ Tokenize              │
│           ▼                  │           ▼                       │
│  ┌──────────────────┐       │  ┌──────────────────┐             │
│  │ Token Sequence   │───────┼──│ Token Sequence   │             │
│  │ t_m1, t_m2, ... │       │  │ t_i1, t_i2, ... │             │
│  └────────┬─────────┘       │  └────────┬─────────┘             │
│           │                  │           │                       │
│           ▼                  │           ▼                       │
│  ┌──────────────────┐       │  ┌──────────────────┐             │
│  │ LLaMA-3 (Shared) │       │  │ LLaMA-3 (Shared) │             │
│  │                  │       │  │  (Same weights)  │             │
│  └────────┬─────────┘       │  └────────┬─────────┘             │
│           │ H_m ∈ R^(L×d)   │           │ H_i ∈ R^(L×d)        │
│           ▼                  │           ▼                       │
│  ┌──────────────────┐       │  ┌──────────────────┐             │
│  │ Mean Pooling     │       │  │ Mean Pooling     │             │
│  │ pool(H_m) = e_m  │       │  │ pool(H_i) = e_i  │             │
│  └────────┬─────────┘       │  └────────┬─────────┘             │
│           │                  │           │                       │
│           └──────────┬───────┴───────────┘                       │
│                      │                                            │
│                      ▼                                            │
│           ┌──────────────────┐                                    │
│           │ Cosine Similarity│                                    │
│           │ s(e_m, e_i) =    │                                    │
│           │ e_m·e_i / (‖e_m‖·‖e_i‖)                              │
│           └────────┬─────────┘                                    │
│                    │ Top-K Retrieval                               │
│                    ▼                                               │
│           ┌──────────────────┐                                    │
│           │ Top 1000-2000    │                                    │
│           │ Candidates       │                                    │
│           └──────────────────┘                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Embedding Generation

Both member and item texts undergo tokenization before being processed by the LLM. Given a tokenized sequence t of length L, the LLM produces a sequence of hidden states, H ∈ R^(L×d) where d denotes the dimensionality of the hidden states [^314^].

A pooling function is subsequently applied to generate a fixed-dimensional, dense representation:

**Embedding for member:** `e_m = pool(H_m)`  
**Embedding for item:** `e_i = pool(H_i)`

### 3.3 Similarity Function

The similarity between member and item embeddings is quantified using **cosine similarity** [^314^]:

```
s(e_m, e_i) = (e_m · e_i) / (‖e_m‖ · ‖e_i‖)
```

This similarity score serves as the primary retrieval ranking metric, enabling efficient identification of the most relevant items for a given member.

### 3.4 Pooling Strategies (Ablation Study Results)

The paper conducted extensive ablation studies on pooling strategies [^184^]:

| Pooling Method | Recall@10 vs. Baseline |
|----------------|----------------------|
| **Mean Pooling (all tokens)** | **Baseline** (Best) |
| Last 500 tokens | -7.06% |
| Last 250 tokens | -5.00% |
| Last 50 tokens | -11.26% |
| Last 1 token | -12.36% |

**Key finding:** Mean pooling over ALL tokens significantly outperforms last-n-token pooling strategies. Pooling any subset of tokens resulted in recall@10 drops. This is important because it validates the holistic representation approach — the entire sequence of tokens contributes to the semantic meaning [^355^].

---

## 4. LLaMA-3 Fine-Tuning

### 4.1 Base Model

| Parameter | Value |
|-----------|-------|
| **Base Model** | Meta LLaMA-3 (3B parameter variant) [^314^] |
| **Output dimension (default)** | 3,072 |
| **Architecture** | Decoder-only transformer-based causal language model |
| **Context length** | 20,480 tokens |
| **Models tested** | LLaMA-3 1B and 3B variants |

The LLaMA-3 3B model was ultimately selected for production deployment based on performance trade-offs [^84^].

### 4.2 Training Data

| Parameter | Value |
|-----------|-------|
| **Training samples** | 5 million member-item pairs [^84^] |
| **Data source** | Historical LinkedIn Feed interaction logs |
| **Label** | Binary "Professional Interaction" (PI): long dwell, react, comment, repost, share, etc. [^184^] |
| **Format** | Tuple of (target post features, member features, binary label) |

### 4.3 Training Hardware

| Parameter | Value |
|-----------|-------|
| **Training GPUs** | 8 × NVIDIA H100 GPUs per run [^84^] |
| **Per-GPU batch size** | 4 |
| **Total training cluster** | 8 H100s |

### 4.4 Training Objectives

Two loss functions were explored [^314^]:

#### Binary Cross-Entropy (BCE)
```
P(y=1 | e_m, e_i) = σ(s(e_m, e_i) / τ)
L_BCE = -[y log σ(s/τ) + (1-y) log(1 - σ(s/τ))]
```

#### InfoNCE (Information Noise-Contrastive Estimation)
```
L_InfoNCE = -log[ exp(s(e_m, e_i⁺)/τ) / (exp(s(e_m, e_i⁺)/τ) + Σ_j exp(s(e_m, e_ij⁻)/τ)) ]
```

**Results comparison:**

| Loss Function | Recall@10 |
|--------------|-----------|
| Random baseline | 0.0700 |
| LLaMA-3 without fine-tuning | 0.2434 |
| **BCE** | 0.3944 |
| **InfoNCE** | **0.4238** |
| InfoNCE + Matryoshka (full 3072d) | 0.4242 |

**Key finding:** InfoNCE outperforms BCE by ~7.4% in Recall@10. Matryoshka training does not hurt overall performance [^84^].

### 4.5 Negative Sampling Strategy

The training uses a **mixed negative sampling (MNS)** strategy combining [^355^]:

1. **Easy negatives (in-batch):** Negatives sampled from the global mini-batch across all GPUs. These provide weak negative pairs (impressions with no action), improving training stability and increasing the effective number of training examples by a factor of batch size² [^184^].

2. **Hard negatives (per-member):** Items that were impressed to a member but not engaged with. These are mined offline and stored in memory for sampling at training time [^314^].

**Impact of hard negatives:**

| Hard Negative Configuration | Recall@10 Improvement |
|----------------------------|----------------------|
| Easy negatives only | Baseline |
| +1 hard negative/member | +2.0% |
| **+2 hard negatives/member** | **+3.6%** |

### 4.6 Matryoshka Representation Learning (MRL)

MRL is employed to learn **nested, size-adaptive representations** by optimizing multiple sub-representations simultaneously [^314^]:

```
L_MRL = Σ(k=1 to K) λ_k · L_k
```

Where L_k is the InfoNCE loss computed on the first k dimensions of the embedding.

**Why MRL matters for production:** It enables flexible deployment with varying embedding dimensionalities without retraining or architecture modifications, reducing GPU index storage costs [^355^].

**Results: Matryoshka dimension reduction:**

| Embedding Dimension | Recall@10 vs. Full 3072d | Storage Savings |
|---------------------|------------------------|-----------------|
| 2048 | +0.1% (MRL) | ~33% |
| 1024 | -0.2% (MRL) | ~67% |
| **512** | **-0.8% (MRL)** | **~83%** |
| 2048 (pre-pool MLP) | -3.2% | ~33% |
| 1024 (pre-pool MLP) | -2.7% | ~67% |
| 512 (pre-pool MLP) | -1.1% | ~83% |

**Key finding:** MRL significantly outperforms MLP-based dimension reduction (both pre-pooling and post-pooling projections). Lowering dimension to **512 causes only -0.8% recall drop** while offering ~83% storage reduction [^184^].

---

## 5. Prompt Design

### 5.1 Prompt Library Architecture

LinkedIn built a **"prompt library"** to convert structured features into text templates for both member and item sides [^314^].

### 5.2 Target Post (Item) Prompt Format

```
<ST_P1>Post feature 1<ST_P2>Post feature 2<ST_PN>Post feature N
```

**Post features included:**
- Type of the post (original post, group post, like/comment on a previous post)
- What is being shared (text, image, video, job change, etc.)
- Author information (author name, profile headline, company, industry, title)
- **Post popularity features** (# of times the post has been liked, viewed for more than T secs, etc.)
- Article title/source (if the post contains an article link)
- Text of the post [^84^]

### 5.3 Member Prompt Format

```
<ST_M0>System prompt
<ST_M1>Member feature 1
<ST_M2>Member feature 2
...
<ST_MN>Member feature N
<ST_history>
  <ST_history_post><post 1 text>
  <ST_history_post><post 2 text>
  ...
  <ST_history_post><post H text>
```

**Member features included:**
- Name, profile headline & summary
- Industry, skill(s), location
- Job and education history
- Certifications, languages spoken
- **Activity history sequence:** Time-ordered list of Feed posts the member previously engaged with [^84^]

**System prompt:**
> "You are provided with a member's profile information, along with a set of historical feed posts that the member engaged with. Your task is to analyze the historical engagement data along with the member profile." [^314^]

### 5.4 Special Token Design

The `<ST_...>` strings are **special token strings added to the tokenizer's vocabulary** so they get tokenized as a single token [^314^]. This serves two purposes:
1. **Reduces prompt size** (single token vs. multiple character tokens)
2. **Mitigates prompt injection attacks** (actual strings not disclosed for security)

### 5.5 Context Length and History

- **Maximum context length:** 20,480 tokens [^84^]
- **Number of history posts:** Dynamic, based on total maximum context length and the tokenized length of each post
- **History ablation study results:**

| History Strategy | BCE Recall@10 | InfoNCE Recall@10 |
|-----------------|---------------|-------------------|
| Full history (all engagements) | 0.307 | 0.398 |
| **Positive-only history** | **0.3944** | **0.4238** |
| No history (profile only) | Not reported | Not reported |

**Key finding:** Filtering member interaction history to include **only positive engagements** (long dwell, reactions, comments, etc.) significantly boosts recall. Negative interactions were removed from all subsequent iterations [^355^].

---

## 6. Quantization and Numerical Feature Encoding

### 6.1 The Numerical Feature Problem

One of the most consequential findings involved how LLMs handle numbers [^53^]:

> "When a post had, say, 12,345 views, that figure appeared in the prompt as 'views:12345,' and the model treated it like any other text token, stripping it of its significance as a popularity signal."

**The problem:** Raw engagement counts (e.g., "views:12345") were treated like any other text token. The model failed to recognize them as numerical signals. This resulted in a **near-zero correlation (-0.0037)** between item popularity counts and cosine similarity scores [^184^].

### 6.2 The Solution: Percentile Quantization

LinkedIn engineers addressed this by:

1. **Converting raw counts into percentile buckets** (range 1-100 percent)
2. **Wrapping them in special tokens** so the model distinguishes them from unstructured text [^53^]

### 6.3 Quantization Results

| Model | Correlation (popularity ↔ cosine similarity) | Recall@10 |
|-------|---------------------------------------------|-----------|
| Baseline (raw counts, full post text) | -0.0037 | 0.158 |
| **Candidate Model (percentile buckets, truncated text)** | **0.1156** | **0.1839** |

**Key findings:**
- **30× increase** in correlation between popularity signals and embedding similarity (from -0.0037 to 0.1156) [^242^]
- **15% improvement in Recall@10** [^184^]
- The LLaMA-3 tokenizer's tendency to group digits into single tokens helps the model encode discretized numerical signals more effectively
- This enables **greater alignment between the retrieval and ranking layers**, since popularity features are important for the ranking model [^314^]

### 6.4 Matryoshka for Storage Cost Reduction

As detailed in Section 4.6, Matryoshka Representation Learning enables:

- Reducing from 3,072 dimensions to **512 dimensions with only -0.8% recall drop**
- **~83% storage reduction** in the GPU index
- Avoids retraining or architecture modifications for different deployment scenarios [^355^]

---

## 7. Production Serving Infrastructure

### 7.1 Hardware Configuration

| Component | Hardware |
|-----------|----------|
| **Nearline embedding inference** | 48 × NVIDIA H100 GPUs [^84^] |
| **Indexing + Online kNN retrieval** | 24 × GPUs |
| **Total GPU cluster** | 72 H100 GPUs |

The 48 H100 cluster also handles back-filling embeddings for new experimental models across the entire item and member corpus [^84^].

### 7.2 Three-Stage Nearline Pipeline

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Stage 1:       │    │  Stage 2:        │    │  Stage 3:        │
│  Activity Log   │───▶│  Prompt          │───▶│  Embedding       │
│  Generation     │    │  Generation      │    │  Generation      │
└─────────────────┘    └──────────────────┘    └────────┬─────────┘
                                                        │
                           ┌────────────────────────────┼────┐
                           ▼                            ▼    ▼
                    ┌──────────────┐           ┌──────────────┐
                    │  GPU-RAR     │           │  Key-Value   │
                    │  Item Index  │           │  Member Store│
                    │  (kNN)       │           │              │
                    └──────────────┘           └──────────────┘
```

**Stage 1 — Activity Log Generation:** Captures item/member creation/updates and interactions (likes, comments, shares) via direct RPC calls for low latency [^314^].

**Stage 2 — Prompt Generation:** Processes activity logs into item and member prompts using pre-defined templates. Fetches post text, member profile info, and popularity counts. Pushes decorated prompts to a key-value store for online access and to a nearline stream processor [^314^].

**Stage 3 — Embedding Generation:** Feeds updated prompts into an LLM inference server hosting the fine-tuned LLM. Item embeddings are ingested into a **GPU-RAR (Retrieval as Ranking) index** [^314^]. Member embeddings are stored in an online key-value store.

### 7.3 GPU-RAR kNN Retrieval with Attribute-Based Matching

For online feed queries [^314^]:
1. Fetch member query embedding from key-value store
2. Run online kNN against GPU-RAR item embeddings index
3. Retrieve top-K items using cosine similarity
4. Apply business logic filtering and privacy rules:
   - Trust classifier approval
   - Language matching
   - Blocked author exclusion
   - Already-seen content exclusion
5. Send filtered candidates to the ranker layer

### 7.4 Latency and Freshness Guarantees

| Metric | Value |
|--------|-------|
| **Retrieval latency** | **Sub-50 milliseconds** [^345^] |
| **Throughput** | Tens of thousands of QPS [^314^] |
| **New item indexing** | Within 1 minute of creation [^84^] |
| **Existing item embedding update** | Within 30 minutes of interaction [^84^] |
| **New member profile embedding** | Within 1 minute of creation [^84^] |
| **Existing member embedding update** | Within 30 minutes of activity [^84^] |

The embedding generation uses nearline stream processing with configurable window sizes to control LLM inference rate, balancing GPU compute against embedding freshness [^314^].

### 7.5 Disaggregated Compute Architecture

LinkedIn invested in **disaggregating CPU-bound feature processing from GPU-heavy model inference** [^53^]:
- Custom C++ data loaders to eliminate Python multiprocessing overhead
- Custom Flash Attention variant (**GRMIS — Generative Recommender Multi-Item Scoring**) delivering 2× speedup over PyTorch standard implementation
- Parallelized checkpointing (vs. serialized) to improve GPU memory utilization
- Shared context batching and MMoE (Multi-gate Mixture-of-Experts) prediction head for efficient ranking

---

## 8. Cold-Start Benefits

### 8.1 Why New Members Benefit More

The LLM-based retrieval system shows **significantly greater gains for newer members** who lack strong network connections [^314^]. The reasons are:

1. **World knowledge inference:** The LLM can infer professional interests from profile data alone (e.g., headline, skills, industry) without requiring engagement history [^46^]
2. **Semantic matching over keyword overlap:** A new member with "electrical engineer" in their profile can receive relevant content about power grid optimization or small modular nuclear reactors from day one — connections keyword systems would miss [^53^]
3. **Positive-only history:** Even minimal positive interactions contribute meaningfully to the embedding

### 8.2 Online A/B Test Results

**Overall platform metrics:**

| Metric | Improvement | p-value |
|--------|------------|---------|
| **Revenue** | **+0.8%** | 0.03 |
| **Daily Unique Professional Interactors** | **+0.2%** | 0.005 |

**New/infrequent member cohort (members with fewer connections and lower candidate liquidity):**

| Metric | Improvement | p-value |
|--------|------------|---------|
| **Daily Active Unique Users** | **+0.23%** | 0.05 |
| **Daily Unique Professional Interactions** | **+1.17%** | <0.0001 |
| **Revenue** | **+3.29%** | 0.03 |

**Key insight:** "The majority of platform-wide impact came from infrequent members and members with fewer connections, for whom suggested content plays a much more vital role" [^84^].

---

## 9. Comparison to Previous Retrieval Systems

### 9.1 The Five Systems That Were Replaced

The new unified LLM-based retrieval replaced **five separate retrieval pipelines**, each with its own infrastructure, index structure, and optimization strategy [^53^][^299^]:

| # | Previous System | Description |
|---|----------------|-------------|
| 1 | **Chronological index of network activity** | Posts from connections in reverse-chronological order |
| 2 | **Global trending topics** | Viral/trending content across the platform |
| 3 | **Trending in geography** | Location-specific trending content |
| 4 | **Collaborative filtering** | Interest-based filtering using similar members' preferences |
| 5 | **Multiple embedding-based retrieval (EBR) systems** | Previous two-tower EBR for unconnected content [^184^] |

### 9.2 Why the Old Architecture Failed

> "Each maintained its own infrastructure, index structure, and optimization strategy. The setup worked, but when the Feed team wanted to improve one part, they'd break another. Therefore, they made a radical bet and ripped out all five systems, replacing them with a single LLM-powered retrieval model." [^299^]

**Key problems with the heterogeneous architecture:**
- Optimizing one retrieval source could degrade another
- No single team could tune across all sources simultaneously
- Holistic improvement was nearly impossible
- Each system had dedicated engineering teams and maintenance overhead [^53^]

### 9.3 Quantified Improvements

| Dimension | Before | After |
|-----------|--------|-------|
| Number of retrieval systems | 5 separate pipelines | 1 unified system |
| Retrieval latency | Not disclosed | **<50 milliseconds** [^345^] |
| Maintenance complexity | 5 separate teams/infra stacks | Unified stack |
| Cold-start handling | Poor (required history) | **Strong (profile-only inference)** |
| Semantic understanding | Keyword-based | Deep semantic via LLM |
| Ranking alignment | Low (different indices) | High (unified embedding space) |

### 9.4 Revenue Impact

The platform saw a **+3.29% revenue increase** for the new/infrequent member cohort alone, demonstrating that the retrieval improvements directly translated into business value [^84^].

---

## 10. Integration with Ranking

### 10.1 Two-Stage Architecture

The new system operates in two distinct stages [^46^][^345^]:

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: LLM-BASED RETRIEVAL (This Paper)                     │
│  ┌──────────────────┐                                           │
│  │ 1.3B Members     │                                           │
│  │    query feed    │                                           │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │ Member Embedding │────▶│ GPU-RAR kNN      │                  │
│  │ (LLaMA-3 3B)     │     │ Retrieval        │                  │
│  └──────────────────┘     └────────┬─────────┘                  │
│                                    │                             │
│                           Top 2,000 candidates                   │
│                                    │                             │
│                                    ▼                             │
│  ┌──────────────────────────────────────────────────┐           │
│  │ STAGE 2: GENERATIVE RECOMMENDER (360Brew/GR)    │           │
│  │                                                   │           │
│  │ • 150B parameter decoder-only transformer        │           │
│  │ • Processes 1,000+ historical interactions       │           │
│  │   as ordered sequence                            │           │
│  │ • Temporal pattern understanding                  │           │
│  │ • Multi-task prediction (click, like, share,     │           │
│  │   comment, dwell time)                           │           │
│  │ • Late fusion with device type, profile          │           │
│  │   embeddings, aggregated engagement               │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 The Generative Recommender (360Brew)

For ranking, LinkedIn deployed **360Brew**, a **150-billion-parameter, decoder-only foundation model** [^345^][^48^]. Key characteristics:

- **Architecture:** Mixtral 8x22 MoE (Mixture of Experts) [^48^]
- **Training data:** LinkedIn raw entity data (profiles, job descriptions, posts) + interaction data across 5+ surfaces
- **Capability:** Solves 30+ predictive tasks across 8+ surfaces without task-specific fine-tuning
- **Context length:** Processes 1,000+ historical member interactions as an ordered sequence [^46^]

### 10.3 Why the Unified Architecture Helps Ranking

> "Instead of receiving candidates from disparate sources with different biases, the ranking layer now receives a coherent candidate set selected through the same semantic similarity. Ranking became easier, and each optimization to the ranking model became more effective." [^299^]

The unified retrieval provides:
1. **Consistent semantic signals** (vs. heterogeneous signals from different indices)
2. **Better alignment** between retrieval scores and ranking features (due to quantized popularity encoding)
3. **Cleaner candidate sets** that share the same embedding-based selection logic
4. **Easier optimization** — tuning retrieval no longer breaks other retrieval sources

### 10.4 Custom Infrastructure for GR Serving

LinkedIn built several custom components for the ranking stage [^299^]:

| Component | Description | Benefit |
|-----------|-------------|---------|
| **GRMIS** | Custom Flash Attention variant | 2× speedup over PyTorch standard |
| Custom C++ data loader | Eliminates Python multiprocessing overhead | Reduced training bottleneck |
| Parallelized checkpointing | Non-serialized GPU checkpoint save | Better GPU memory utilization |
| Custom CUDA kernels | Metric computation on GPU | Eliminated metric computation bottleneck |
| Disaggregated architecture | CPU feature processing + GPU inference | Optimal resource utilization |
| MMoE prediction head | Multi-gate Mixture-of-Experts | Shared computation across engagement types |

### 10.5 Temporal Understanding

A critical distinction from the old system: the GR model treats user history as an **ordered sequence**, not independent events [^345^]:

> "If someone shifted from content about hiring practices toward workforce automation, that trajectory informs what content is delivered next."

The model understands that a user's professional interests evolve over time and uses this temporal trajectory to predict future engagement — something the old system (which scored each post in isolation) could not do [^53^].

---

## 11. Key Results Summary

### 11.1 Offline Results

| Experiment | Result |
|-----------|--------|
| Base LLaMA-3 3B (no fine-tuning) Recall@10 | 0.2434 |
| Fine-tuned with BCE Recall@10 | 0.3944 |
| **Fine-tuned with InfoNCE Recall@10** | **0.4238** |
| InfoNCE + Matryoshka (3072d) Recall@10 | 0.4242 |
| Hard negatives (2/member) improvement | +3.6% |
| Positive-only history improvement | Significant over full history |
| Mean pooling vs. last-token pooling | +12.4% over last-1-token |
| Matryoshka 512d vs. full 3072d | -0.8% (production-viable) |
| Quantized popularity encoding | +15% Recall@10, 30× correlation increase |

### 11.2 Online A/B Test Results

**Platform-wide:**
- Revenue: +0.8% (p=0.03)
- Daily Unique Professional Interactors: +0.2% (p=0.005)

**New/Infrequent Members (where impact was largest):**
- Daily Active Unique Users: +0.23% (p=0.05)
- Daily Unique Professional Interactions: +1.17% (p<0.0001)
- Revenue: +3.29% (p=0.03)

### 11.3 Production Performance

| Metric | Value |
|--------|-------|
| Retrieval latency | <50ms |
| New item indexing | <1 minute |
| Member embedding freshness | <30 minutes |
| GPU cluster (nearline inference) | 48 H100s |
| GPU cluster (index + retrieval) | 24 GPUs |
| Candidate pool | Hundreds of millions |
| Retrieved candidates | 2,000 per request |

---

## 12. Future Work (from the Paper)

The authors outline several directions for future research [^84^]:

1. **Unimpressed content handling:** Improve handling of unimpressed content at the retrieval stage to encourage exploration
2. **Distillation strategies:** Investigate more effective distillation strategies for deriving dual encoders from cross encoders
3. **Embedding dimension reduction:** Building on Matryoshka learning efficacy, reduce embedding dimensionality further to lower storage costs
4. **Network content embeddings:** Explore LLM-powered embeddings for content generated by members' connections (the bulk of impressed items)
5. **Input sequence shortening:** Investigate methods to shorten input sequences to improve GPU throughput in the nearline system
6. **User-prompt-driven re-ranking:** Prototype user-prompt-driven feed recommendation as a re-ranking layer (already showing promising early results)

---

## 13. Related Work and Context

### 13.1 Previous LinkedIn Retrieval Systems

| System | Description | Relationship to This Work |
|--------|-------------|--------------------------|
| **LiNR** (CIKM 2024) [^293^] | Model-based neural retrieval on GPUs with Hadamard MLP and Mixture-of-Logits | Predecessor GPU retrieval infrastructure |
| **LinkedIn Post Embeddings** (2023) [^358^] | BERT-based fine-tuned model generating 50-dimensional post embeddings | Earlier embedding approach, much smaller scale |
| **Borisyuk et al. EBR** (2024) [^184^] | Two-tower embedding-based retrieval system | Explicitly cited as the previous EBR system being replaced |

### 13.2 Related Papers from the Same Team

| Paper | Description | Citation |
|-------|-------------|----------|
| **360Brew** (arXiv 2025, withdrawn) [^48^] | 150B parameter decoder-only foundation model for personalized ranking and recommendation | Firooz et al., arXiv:2501.16450 |
| **LinkedIn Post Embeddings** (CIKM 2024) [^358^] | Industrial scale embedding generation and usage across LinkedIn | Borisyuk et al., 2024 |
| **LiNR** (CIKM 2024) [^293^] | Model-based neural retrieval on GPUs at LinkedIn | CIKM 2024 |

### 13.3 Industry Context

The paper was published in the **IAAI Technical Track on Deployed Highly Innovative Applications of AI** at AAAI 2026, specifically recognizing the paper's contribution as a **deployed, high-impact industrial AI system** [^343^].

The public announcement came via LinkedIn Engineering Blog on **March 12, 2026**, authored by Hristo Danchev (Senior Staff TPM) [^345^][^46^].

---

## 14. Key Technical Insights and Learnings

### 14.1 Quantizing Numerical Features is Critical

> "Quantizing numerical features in the prompt enables the information to get properly encoded in the embedding, facilitating greater alignment between the retrieval and ranking layer." — Paper Abstract

This was described as "one of the most consequential findings" [^53^]. Raw numerical values in prompts are not effectively captured by LLM embeddings. Converting to percentile buckets with special tokens increases correlation with similarity scores by **30×**.

### 14.2 Mean Pooling Beats Last-Token Pooling

Contrary to common practice in language model embeddings, **mean pooling over all tokens significantly outperforms last-n-token pooling** (+12.4% over last-1-token). This validates the holistic representation hypothesis — every token in the prompt contributes to the semantic meaning.

### 14.3 Positive-Only History Matters

Including negative engagements (impressions without action) in the member's interaction history degrades retrieval performance. Filtering to **positive-only interactions** (reactions, comments, shares, long dwells) produces significantly better embeddings.

### 14.4 Matryoshka Learning Enables Cost Reduction

MRL allows production systems to reduce from 3,072 to 512 dimensions with only -0.8% recall drop, yielding **~83% storage savings** in the GPU index. This is critical for serving hundreds of millions of items at LinkedIn's scale.

### 14.5 Cold-Start is Where LLMs Shine

The biggest online impact (+3.29% revenue for new/infrequent members) came from members with the least behavioral data. This validates the core hypothesis that LLMs' **world knowledge enables inference from minimal signals** — a capability traditional collaborative filtering and keyword-based systems lack.

---

## 15. Sources and References

### Primary Sources

1. **Main Paper:** Ramanujam et al., "Large Scale Retrieval for the LinkedIn Feed Using Causal Language Models," AAAI 2026, IAAI Track. [arXiv:2510.14223](https://arxiv.org/abs/2510.14223) [^173^][^343^]
2. **AAAI Official Publication:** [https://doi.org/10.1609/aaai.v40i47.41445](https://doi.org/10.1609/aaai.v40i47.41445) [^343^]

### Secondary Sources and Analysis

3. **LinkedIn Engineering Blog:** "Engineering the next generation of LinkedIn's Feed," Hristo Danchev, March 12, 2026 [^345^][^46^]
4. **VentureBeat Coverage:** "How LinkedIn replaced five feed retrieval systems with one LLM model, at 1.3 billion-user scale," March 16, 2026 [^53^]
5. **ByteByteGo Analysis:** "How LinkedIn Feed Uses LLMs to Serve 1.3 Billion Users," April 13, 2026 [^299^]
6. **AI to ROI Newsletter:** "Case Study: LinkedIn's Global Feed Transformation," March 31, 2026 [^345^]
7. **360Brew Paper:** Firooz et al., "360Brew: A Decoder-only Foundation Model for Personalized Ranking and Recommendation," arXiv:2501.16450 (withdrawn) [^48^]
8. **LiNR Paper:** "LiNR: Model Based Neural Retrieval on GPUs at LinkedIn," CIKM 2024 [^293^]
9. **LinkedIn Post Embeddings:** "LinkedIn Post Embeddings: Industrial Scale Embedding Generation and Usage across LinkedIn," CIKM 2024 [^358^]
10. **Falia Analysis:** "360Brew: LinkedIn's New Algorithm Explained," April 2026 [^46^]

---

## Appendix: Key Metrics at a Glance

| Category | Metric | Value |
|----------|--------|-------|
| **Model** | Base architecture | Meta LLaMA-3 3B |
| | Output dimension | 3,072 (default) |
| | Production dimension | 512 (via Matryoshka) |
| | Context length | 20,480 tokens |
| **Training** | Training samples | 5M member-item pairs |
| | Training GPUs | 8 × H100 |
| | Per-GPU batch size | 4 |
| | Loss function | InfoNCE + Matryoshka |
| | Hard negatives | 2 per member |
| **Serving** | Nearline inference GPUs | 48 × H100 |
| | Index/retrieval GPUs | 24 |
| | Retrieval latency | <50ms |
| | Freshness (new items) | <1 min |
| | Freshness (updates) | <30 min |
| **Results** | Recall@10 (InfoNCE) | 0.4238 |
| | Revenue lift (overall) | +0.8% |
| | Revenue lift (new members) | +3.29% |
| | Professional interactors | +0.2% (overall), +1.17% (new) |
| | DAU lift (new members) | +0.23% |
