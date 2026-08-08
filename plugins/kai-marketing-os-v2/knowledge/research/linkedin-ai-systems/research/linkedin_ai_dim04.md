# Dimension 4: Graph Neural Networks (LiGNN) - Deep Dive

## Executive Summary

LiGNN is LinkedIn's production-scale Graph Neural Network (GNN) framework deployed across the LinkedIn Economic Graph, a heterogeneous graph with 100B+ nodes and hundreds of billions of edges [^96^]. The system was published at KDD 2024 (arXiv:2402.11139) and represents one of the most comprehensive industrial GNN deployments documented in academic literature. LiGNN achieves a 7x training speedup through adaptive sampling, grouping/slicing, and shared-memory queue optimizations. Production metrics include +1% job hearing-back rate, +2% Ads CTR, +0.5% Feed DAU, +0.2% session lift, and +0.1% weekly active user lift [^282^].

---

## 1. LiGNN Full Paper Analysis

### 1.1 Publication Details

| Attribute | Details |
|-----------|---------|
| **Title** | LiGNN: Graph Neural Networks at LinkedIn |
| **Venue** | KDD 2024 (30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining), Barcelona, Spain |
| **arXiv ID** | arXiv:2402.11139 [cs.LG] |
| **Submission Date** | February 17, 2024 |
| **Authors** | Fedor Borisyuk, Shihai He, Yunbo Ouyang, Morteza Ramezani, Peng Du, Xiaochen Hou, Chengming Jiang, Nitin Pasumarthy, Priya Bannur, Birjodh Tiwana, Ping Liu, Siddharth Dangi, Daqi Sun, Zhoutao Pei, Xiao Shi, Sirou Zhu, Qianqi Shen, Kuang-Hsuan Lee, David Stein, Baolei Li, Haichao Wei, Amol Ghoting, Souvik Ghosh |
| **Institution** | LinkedIn Inc. |
| **Pages** | 10 pages |
| **URLs** | [arXiv Abstract](https://arxiv.org/abs/2402.11139), [arXiv PDF](https://arxiv.org/pdf/2402.11139), [ACM DL](https://dl.acm.org/doi/10.1145/3637528.3671566) |

[^282^] [^96^] [^268^]

### 1.2 Complete Architecture Overview

LiGNN adopts an **encoder-decoder architecture** designed to generate reusable node embeddings that can be integrated into downstream application models as new features [^258^]. This decoupled design allows the trained encoder to produce embeddings without requiring a full GNN inference at serving time.

#### 1.2.1 Encoder: GraphSAGE-Style Framework

The encoder follows the **GraphSAGE** (Hamilton et al., 2017) framework with inductive learning capabilities:

- **Graph sampling**: Performed by the DeepGNN Graph Engine, supporting:
  - Multi-hop random sampling
  - Weighted sampling (user-configurable per edge type)
  - Personalized PageRank (PPR) sampling
  - Two-hop PPR sampling (optimized for near-line serving) [^258^]

- **Neighborhood aggregation**: Two primary modes:
  - **Mean aggregation**: Averages neighbor embeddings
  - **Attention-based aggregation**: Learns attention weights over neighbors (outperforms mean by +0.9% AUC) [^96^]

#### 1.2.2 Decoder Options

The decoder consumes encoder-generated embeddings and supports three configurations [^258^]:

1. **MLP Decoder**: Multi-layer perceptron for classification/regression tasks
2. **Cosine Decoder**: Computes cosine similarity between source and destination embeddings for link prediction
3. **In-batch Negative Sampling Decoder**: Treats all other samples in the batch as negative samples, using dot products for prediction

#### 1.2.3 Key Architectural Innovations

- **Dual Encoders**: Separate encoders for source and destination nodes (+2.5% AUC improvement for link prediction) [^96^]
- **ID Embeddings**: Learnable embeddings for node IDs (+15.3% AUC improvement - the single largest gain) [^96^]
- **Multi-head dimensions**: The SAGE encoder output is expanded to multi-head dimensions with head number H (e.g., 4), reshaping into a sequence of length H and dimension d [^96^]

### 1.3 Core Technical Equations

#### 1.3.1 Edge Weight Formula (People Recommendations)

For people recommendation, the edge weight between members u and v is computed as:

```
weight(u,v) = (# of common connections between u and v) / (sqrt(# of u's connections) * sqrt(# of v's connections))
```

[^258^]

#### 1.3.2 Transformer-Based Temporal Model

The temporal model architecture works as follows [^96^]:

1. **Neighbor Sampling**: Last N (e.g., 100) activities of a member before a certain time are sampled
2. **SAGE Encoder**: Produces multi-head output with dimension H*d, reshaped to sequence (length H, dim d)
3. **Node Encoding**: N activities are encoded via a node encoding module
4. **Concatenation**: SAGE outputs + activity embeddings form a sequence of length H+N, dimension d
5. **Transformer Encoder**: Processes the full sequence with:
   - Positional encoding added
   - **Prefix causal masking**: First H tokens have full attention; each of last N tokens attends to all H tokens and only tokens before itself in the N activity sub-sequence

#### 1.3.3 Long-Term Loss Function

The training combines [^96^]:
- **Binary Cross Entropy (BCE) loss**: Standard link prediction loss
- **Long-term losses**: Extended prediction to N2 future events
  - The N-length activity sequence is split: N1 (past) + N2 (future) = N
  - Output embeddings at positions N1 are used to predict embeddings from N1 to N
  - This captures long-range temporal dependencies

#### 1.3.4 Graph Densification Algorithm

```
Algorithm 1: Graph Densification
Function DENSIFY(node):
  embedding = Query(node)           # Get external content embedding
  similar_nodes = approximate_knn(embedding, k)  # HNSW-based k-NN
  for target in similar_nodes:
    if out_degree(node) < degree_lower_bound:
      if out_degree(target) > degree_lower_bound:
        create_edge(node, target)   # Add artificial edge
```

Production parameters [^96^]:
- `degree_upper_bound`: 90th percentile
- `degree_lower_bound`: 36th percentile
- `k` (number of artificial edges): approximately 50

---

## 2. Graph Construction: The LinkedIn Economic Graph

### 2.1 Scale and Scope

The LinkedIn Economic Graph is a digital representation of the global economy [^33^] [^308^]:

| Metric | Scale |
|--------|-------|
| Total nodes | Up to 100 billion+ |
| Total edges | Several hundred billion |
| Member nodes | 1 billion+ |
| Countries | 200+ |

[^258^] [^282^]

### 2.2 Node Types

LiGNN integrates multiple entity types into a **single unified embedding space** [^258^]:

| Node Type | Description | Approximate Count |
|-----------|-------------|-------------------|
| **Members** | LinkedIn users/professionals | 1 billion |
| **Posts** | Content posts on the platform | Millions |
| **Jobs** | Job postings | 50 million |
| **Companies** | Organization pages | 25 million |
| **Skills** | Professional skills | 41,000 |
| **Titles** | Job titles | 25,000 |
| **Positions** | (Company, Title) tuples | 195 million |
| **Campaigns** | Ads campaign nodes | Millions |
| **Creatives** | Ad creative nodes | Millions |

[^55^] [^258^]

### 2.3 Edge Types

The heterogeneous graph contains three primary categories of edges [^258^] [^260^]:

#### 2.3.1 Engagement Edges
- Represent direct interactions between members and content
- Examples: "member liked post", "member applied to job", "member clicked ad"
- Weighted by interaction strength/frequency
- Examples from LinkSAGE graph: member-to-job seeker engagement = 2.7B edges; recruiter interaction = 26M edges [^55^]

#### 2.3.2 Affinity Edges
- Record historical interactions between members and content creators
- Examples: "member engaged with creator M1's content"
- Capture implicit interest signals
- Examples: Ads + Feed affinity + member connection edges used in Ads CTR models [^96^]

#### 2.3.3 Attribute Edges
- Describe "HAS-A" relationships between nodes and their attributes
- Examples: "member has title software engineer", "job requires skill machine learning"
- Uniform weight of 1.0
- Examples from LinkSAGE: member-title (1B edges), member-company (966M), member-position (139M), member-skill (1.2B) [^55^]

### 2.4 Graph Construction Philosophy

The graph construction follows a multi-domain integration approach [^258^]:
- Combines social graph (member connections), activity graph (member-content interactions), and knowledge graph (member/company/job attributes)
- Edges are weighted by interaction strength (except attribute edges)
- Designed for **multi-task learning** across different LinkedIn surfaces

---

## 3. Training Infrastructure

### 3.1 Kubernetes-Based Deployment

All GNN training and inference jobs execute in LinkedIn's in-house **Kubernetes (K8S)** cluster with access to **HDFS** [^258^]:

| Component | Hardware | Role |
|-----------|----------|------|
| Graph Engine (GE) | CPU nodes | Real-time graph sampling and data serving |
| GNN Trainer | GPU nodes | Model training/inference |

[^258^]

### 3.2 DeepGNN Graph Engine

**Microsoft DeepGNN** (Samylkin, 2022) is the core graph engine providing [^258^]:

- **Real-time graph sampling**: Eliminates need for pre-computed graphs
- **Distributed memory serving**: Graph data loaded into distributed memory
- **gRPC communication**: Trainers query GE via gRPC calls
- **Multiple sampling strategies**: Random, weighted, PPR (multi-hop and 2-hop)
- **Partitioning support**: One or more pod instances serve portions of the partitioned graph

#### Key advantages over pre-computation [^258^]:
| Aspect | Spark Pre-computation | DeepGNN Real-time |
|--------|----------------------|-------------------|
| Preprocessing time | 20 hours for 500M nodes | None |
| Storage overhead | 10x original graph size | Original graph size |
| Model iteration speed | Slow (regenerate for any change) | 10x faster |
| Generalization | Limited (static graphs) | Better (randomness per request) |

### 3.3 Training Speed Optimizations (7x Speedup)

LiGNN achieved a **7x training speedup** through multiple techniques [^258^] [^96^]:

#### 3.3.1 Adaptive Neighbor Sampling (24.2% time reduction)
- Start with small neighbor count (e.g., 2 neighbors)
- Adaptively increase by monitoring model performance (AUC)
- Only increase when metrics stop improving beyond tolerance threshold
- Stride of 20 neighbors per increase

Algorithm [^258^]:
```
Adaptive_Neighbor_Sampling:
  current_count = starting_neighbor_count
  for each epoch:
    train with current_count
    evaluate(model)
    if metric <= last_metric + tolerance:
      current_count = min(current_count + stride, final_neighbor_count)
    tolerance *= tolerance_decay
```

#### 3.3.2 Grouping and Slicing (69.9% time reduction)
- Group training records by member_id
- Active members interact with multiple items (e.g., 10 interactions)
- Group size of 5: reduces 10 queries to 2 queries per member
- Configurable gradient steps between grouped backprop and per-sample backprop

Parameters used: group_size = 4, gradient_step = 1 [^258^]

#### 3.3.3 Shared-Memory Queue (68% time reduction)
- Python Multi-Processing for parallel prefetching and preprocessing
- Custom shared-memory queue using Python multiprocessing package
- Eliminates data copying overhead between parent/child processes
- Simultaneously queries DeepGNN Graph Engine across multiple processes

#### 3.3.4 Local Gradient Aggregation (35.2% time reduction)
- Gradients aggregated locally on each worker for N mini-batches
- Reduces AllReduce communication frequency
- Effectively increases batch size by N times
- Combined with learning rate scaling for large-batch training

#### 3.3.5 Additional Optimizations

| Technique | Time Reduction | Notes |
|-----------|---------------|-------|
| MLPinit | 16.25% | Pre-trains node encoders without GE queries |
| Mixed Precision Training | 8% | FP16 forward/backward, FP32 for reductions |
| GPU Co-location | 0% | GE on CPU of GPU machines (no benefit observed) |

[^258^]

**Total**: Training time reduced from 24 hours to **3.3 hours** [^258^].

### 3.4 Training Stability Improvements

Training success rate improved from **30% to over 90%** [^258^]:

| Technique | Success Rate Improvement |
|-----------|------------------------|
| gRPC Retry (max attempts/backoff) | +15% |
| Horovod Training (vs. TF MultiWorkerMirroredStrategy) | +35% |
| GeneratorEnqueuer (memory leak fix) | +10% |

[^258^]

### 3.5 Multi-Hop Graph Sampling Strategies

Three sampling techniques were evaluated [^258^]:

| Method | Description | Speed | Quality |
|--------|-------------|-------|---------|
| Multi-hop random/weighted | Random or user-configurable weighted | Fastest | Baseline |
| Multi-hop PPR | Top-k neighbors by PPR score | Slower | +2.3% AUC |
| **2-hop PPR** (chosen default) | Top-k within 2-hop via random walks | 3x faster | +2.1% AUC, 90% of gains |

[^258^]

---

## 4. Inference Pipeline: Near Real-Time Embedding Generation

### 4.1 Architecture Overview

LiGNN uses a **near-line inference pipeline** for near real-time embedding generation and serving [^258^] [^96^]:

```
Kafka Event -> Apache Beam Pipeline -> Feature Collection -> GNN Inference -> Venice Feature Store
```

### 4.2 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Event streaming | Apache Kafka | Item creation and member interaction events |
| Stream processing | Apache Beam (Managed Beam) | Pipeline orchestration |
| Feature storage | Venice (LinkedIn's feature store) | Embedding storage and serving |
| ML Framework | TensorFlow | Model inference |
| Sampling | DeepGNN | Real-time graph sampling for inference |

[^258^] [^269^]

### 4.3 Pipeline Flow

1. **Event ingestion**: Item creation event via Kafka (member clicks, connects, applies to an item)
2. **Feature collection**: Beam pipeline performs joins to collect features for GNN model
3. **GNN inference**: Model conducts forward pass to generate embeddings
4. **Storage**: Outputs stored in Venice feature storage or published to Kafka topics for downstream Beam pipelines
5. **Member updates**: Process also applies to member updates with tracking of item-interacting members

[^258^]

### 4.4 Latency Characteristics

- Near-line (not real-time) inference: embeddings computed within minutes of interaction
- LinkSAGE achieves **low tens of milliseconds** latency at serving time by pre-computing GNN encoders and storing outputs in in-memory feature store [^55^]
- Eliminates need for costly real-time GNN infrastructure

### 4.5 Beam Components for GNN

LinkedIn developed specific Apache Beam components for GNN use cases [^258^]:
- **SourceComponent** / **SinkComponent** / **InferenceComponent**: Standard ML infrastructure components
- Custom components for batch feature fetchers, 2D tensor data converters, and sampling functions
- Integration with LinkedIn's Frame framework and ML infra data types

[^269^]

---

## 5. Cold-Start Handling: HNSW Graph Densification

### 5.1 Problem Statement

Social network graphs follow a **power-law degree distribution**, meaning most nodes have very few interactions [^96^]. This creates challenges for neighborhood aggregation in GNNs, particularly for low-out-degree (cold-start) nodes.

### 5.2 Graph Densification Algorithm

LiGNN addresses this by adding **artificial edges** based on auxiliary content embeddings [^96^]:

```
Algorithm 1: Graph Densification
  Function DENSIFY(node):
    embedding = Query(node)              # Get external content embedding
    similar_nodes = approximate_knn(     # HNSW-based k-NN search
      embedding, k=50, 
      candidates=high_out_degree_nodes
    )
    for target in similar_nodes:
      create_artificial_edge(node, target)
```

#### Key Steps:

1. **Query Function**: Retrieves external content embedding for a node
   - Member nodes: Profile LLM embeddings (derived from profile data)
   - Item nodes: Content embeddings (based on text and image content)

2. **approximate_knn Function**: Uses in-house **HNSW-based approximate nearest neighbor search** [^96^]
   - HNSW (Hierarchical Navigable Small World) provides efficient approximate k-NN
   - Scales to billions of nodes

3. **Create Edge**: Forms artificial edges between low-out-degree nodes and similar high-out-degree nodes

### 5.3 Production Parameters

| Parameter | Value |
|-----------|-------|
| degree_upper_bound | 90th percentile of out-degree |
| degree_lower_bound | 36th percentile of out-degree |
| k (number of artificial edges) | ~50 |
| External embedding types | Profile LLM (members), Content (items) |

[^96^]

### 5.4 Impact

| Application | Metric | Improvement |
|-------------|--------|-------------|
| Follow Feed | AUC | +0.5% validation |
| Ads CTR | AUC | +0.28% (with densification) |
| General | Cold-start node representation | Significantly improved |

[^96^]

### 5.5 Key Insight

Graph densification enables **information flow from active nodes to less active nodes**, mitigating cold-start issues by allowing cold-start nodes to receive signals from similar but more active nodes [^259^].

---

## 6. Temporal Modeling: Transformer-Based Sequence Model

### 6.1 Motivation

Standard GNNs are static and cannot capture the temporal dynamics critical for professional social networks. LiGNN integrates transformer-based temporal modeling directly into the GNN encoder [^258^].

### 6.2 Architecture Details

#### 6.2.1 Modified SAGE Encoder with Temporal Neighbor Sampling
- Neighbor sampling modified to capture the last N (e.g., 100) activities of a member **before a certain time**
- Time-based node sampling ensures temporal ordering is preserved

#### 6.2.2 Multi-Head SAGE Output Expansion
- SAGE encoder output expanded to multi-head dimensions with head number H (e.g., 4)
- Output dimension: H x d, reshaped into sequence of length H, dimension d

#### 6.2.3 Activity Encoding and Concatenation
- N activities encoded via a node encoding module
- Concatenated with SAGE encoder outputs
- Final sequence: length H+N, dimension d

#### 6.2.4 Transformer Encoder
- Processes the combined (H+N) sequence
- Adds positional encoding [^96^]
- Uses **prefix causal masking** [^96^]:
  - First H tokens: **full attention** (all-to-all)
  - Last N tokens: **causal attention** - each token attends to all H SAGE tokens + only preceding tokens in the N activity sub-sequence

### 6.3 Long-Term Loss

- The N-length activity sequence is split: N1 (history) + N2 (future) = N
- Output embeddings at position N1 predict embeddings from N1 to N
- Captures long-range temporal dependencies beyond immediate next-step prediction
- Parameters: future history length N2 tested at 40, 20, and 10 (best at 10) [^96^]

### 6.4 Ablation Results (Feed Data)

| Configuration | AUC | Relative Lift |
|---------------|-----|---------------|
| Baseline SAGE + BCE | 0.71978 | - |
| + Temporal Encoder (TempEnc) | 0.75204 | +4.48% |
| + TempEnc + Positional encoding | 0.75277 | +4.58% |
| + TempEnc + Stationary encoding | 0.75433 | +4.80% |
| + TempEnc + Engold Causal mask | 0.74991 | +4.19% |
| + TempEnc + Prefix Causal Mask | 0.75316 | +4.64% |
| + TempEnc + DST neighbors in src | 0.75978 | +5.56% |
| + TempEnc + Long term loss (future=10) | 0.75193 | +4.47% |
| **All combined (future=10)** | **0.76176** | **+5.83%** |

[^96^]

### 6.5 Production Impact

| Application | Temporal Model Impact |
|-------------|----------------------|
| Follow Feed | +5.8% AUC lift |
| Job Recommendations | +6.8% AUC lift, +0.4% job viewers, +0.4% qualified applicants |

[^258^] [^96^]

---

## 7. Production Deployment

### 7.1 Infrastructure Stack

| Layer | Technology |
|-------|-----------|
| Container orchestration | Kubernetes (K8S) |
| Storage | Hadoop File System (HDFS) |
| Graph engine | Microsoft DeepGNN |
| ML framework | TensorFlow |
| Distributed training | Horovod (with NCCL 2) |
| Stream processing | Apache Beam + Kafka |
| Feature store | Venice |
| Serving | Model Cloud L0 |

[^258^] [^269^] [^295^]

### 7.2 GPU/CPU Allocation

- **Graph Engine**: Deployed on CPU nodes (can be 1 to many pods for graph partitioning)
- **GNN Trainer**: Deployed on GPU nodes
- **Distributed training**: 6 to 24 workers
- Training jobs: **data-bound** (I/O from GE is bottleneck, not TF-to-TF communication) [^258^]

### 7.3 Training Stability Achievements

| Metric | Before | After |
|--------|--------|-------|
| Training success rate | ~30% | >90% |

### 7.4 Key Deployment Lessons

#### Lesson 1: Impression Discount Before Retrieval
In Follow Feed, models showed high offline metrics but online gains faded after a few days. Root cause: impression discount (filtering already-viewed content) was positioned **after** retrieval. Since GNN relevance scores are stable, the system kept discarding the same relevant items. Moving impression discount **before** retrieval stabilized and improved online metrics [^258^].

#### Lesson 2: Graph Engine Enables Model Iteration
Switching from Spark pre-computation to DeepGNN real-time sampling [^258^]:
- Eliminated 20-hour preprocessing for 500M nodes
- Reduced storage from 10x to 1x original graph size
- Accelerated model iteration by **10x** (no regeneration needed for sampling changes)
- Improved model generalization through per-request sampling randomness

---

## 8. Multi-Task Learning: Single Embedding Space for Multiple Surfaces

### 8.1 Unified Graph Design

LiGNN's key design principle is creating a **unified graph embedding space** for multiple entity types and downstream tasks [^258^]. The heterogeneous graph integrates:

- **Feed**: Member-post engagement and affinity edges
- **Jobs**: Member-job-skill-title-position-company connections
- **People**: Member-member social connections
- **Ads**: Member-creative-campaign-company interactions

### 8.2 Shared Infrastructure

The same GNN training infrastructure serves all surfaces:
- Single Graph Engine deployment with partitioned graph
- Same encoder-decoder architecture pattern
- Shared sampling strategies (2-hop PPR as default)
- Shared training optimizations (adaptive sampling, grouping/slicing)

### 8.3 Surface-Specific Adaptations

| Surface | Graph Focus | Encoder Output | Downstream Model |
|---------|-------------|----------------|------------------|
| Follow Feed | Member-post | Member + Post embeddings | EBR (cosine similarity + recency) |
| OON Feed | Member-post-creator | Member + Post embeddings | EBR candidate generator |
| Jobs | Member-job-skill-position | Member embeddings | Two-tower + ranking model |
| People | Member-member | Member embeddings | EBR for connection suggestions |
| Ads | Member-creative-campaign | Member + Creative + Campaign | CTR prediction model |

[^258^] [^96^]

### 8.4 Multi-Surface Production Impact

| Surface | Offline Metric | Online Metric | Impact |
|---------|---------------|--------------|--------|
| **Follow Feed** | +9.6% recall | Feed Engaged DAU | +0.5% |
| **OON Feed** | - | DAU engaging with professional content | +0.2% |
| **Jobs (TAJ)** | +1.1% AUC | Hearing back rate | +1.0% |
| **People Recs** | +29.6% recall | Weekly Active User | +0.1% |
| **Ads CTR** | +0.39% AUC | CTR | +2.0% |

[^258^] [^96^]

---

## 9. LinkSAGE: Job-Specific GNN Variant

### 9.1 Publication Details

| Attribute | Details |
|-----------|---------|
| **Title** | Optimizing Job Matching Using Graph Neural Networks |
| **Authors** | Ping Liu, Haichao Wei, Xiaochen Hou, Jianqiang Shen, Shihai He, Kay Qianqi Shen, Zhujun Chen, Fedor Borisyuk, Daniel Hewlett, Liang Wu, Srikant Veeraraghavan, Alex Tsun, Chengming Jiang, Wenjing Zhang |
| **Venue** | KDD 2024 (Applied Data Science Track) |
| **arXiv ID** | arXiv:2402.13430 |
| **URLs** | [arXiv](https://arxiv.org/abs/2402.13430), [ACM DL](https://dl.acm.org/doi/10.1145/3690624.3709396) |

[^55^] [^81^]

### 9.2 How LinkSAGE Differs from LiGNN

LinkSAGE is a specialized GNN framework optimized for LinkedIn's job marketplace [^55^]:

#### 9.2.1 Job-Specific Graph Construction

| Node Type | Count |
|-----------|-------|
| Members | 1 billion |
| Jobs | 50 million |
| Titles | 25,000 |
| Positions | 195 million |
| Companies | 25 million |
| Skills | 41,000 |

[^55^]

| Edge Type | Count |
|-----------|-------|
| Member-title | 1 billion |
| Member-company | 966 million |
| Member-position | 139 million |
| Member-skill | 1.2 billion |
| Job-title | 46 million |
| Job-company | 42 million |
| Job-position | 41 million |
| Job-skill | 33 million |
| Seeker engagement | 2.7 billion |
| Recruiter interaction | 26 million |

[^55^]

#### 9.2.2 Key Differences from General LiGNN

1. **Skill-First Graph Design**: Graph connectivity is primarily driven by skill connections
   - Members linked to ~1.2 top skills on average
   - Jobs linked to ~0.67 top skills on average
   - Skill relevance scoring model identifies top skills for each member/job
   - +1.5% recall improvement compared to baseline without skill nodes [^55^]

2. **Bidirectional Edge Strategy**: Specific edge directionality for optimal performance:
   - Bidirectional edges between members and titles
   - Bidirectional edges between members and skills
   - Bidirectional edges for position transitions
   - Bidirectional edges between members/jobs and positions [^55^]

3. **Transfer Learning Integration**: 
   - GNN encoder training is **decoupled** from existing DNN model training
   - GNN embeddings are pre-computed and integrated as features in existing ranking models
   - Eliminates need for frequent GNN retraining
   - Maintains up-to-date graph signals through near-line inference [^55^]

4. **Near-line Inference**: 
   - Pre-computes GNN encoder outputs
   - Stores embeddings in in-memory feature store
   - DNN models consume stored embeddings at serving time
   - Latency remains in **low tens of milliseconds** [^55^]

### 9.3 LinkSAGE Production Applications

#### 9.3.1 Top Applicant Jobs (TAJ) - Premium Feature

| Metric | Impact |
|--------|--------|
| Positive Hearing Back Rate | +1.0% |
| Onsite Application Positive Rating Rate | +1.3% |
| Company Follows | +1.8% |
| Renewal Rate | +0.3% |

Second A/B test (enhanced recruiter-member edges): Survival Rate +2.2%, Apply Clicks Positive Interaction +20.0% [^55^]

#### 9.3.2 Jobs You May Be Interested In (JYMBII)

| Metric | Impact |
|--------|--------|
| Qualified Applications | +2.2% |
| Qualified Applications Rate | +0.3% |
| Job Sessions | +0.6% |
| Dismiss To Apply Ratio | -6.0% |

Segment results for members lacking predictive data [^55^]:
- Opportunistic job seekers: QA +3.2%, Dismiss/Apply ratio -13.8%
- Open to job: QA +2.8%, Dismiss/Apply ratio -24.2%
- Urgent job seekers: QA +2.6%, Dismiss/Apply ratio -25.3%

#### 9.3.3 Job Search

| Metric | Impact |
|--------|--------|
| Total Applies | +0.5% |
| Apply to view ratio | +0.5% |
| Successful job search sessions | +0.6% |
| Onsite apply positive interactions | +0.8% |

[^55^]

#### 9.3.4 Embedding-Based Retrieval (EBR) for Job Search

| Metric | Organic | Promoted |
|--------|---------|----------|
| Successful Job Search Sessions | +2.4% | +1.1% |
| Apply Clicks | +1.5% | +0.4% |
| Apply To Viewport Ratio | +0.9% | +0.9% |
| CTR | +1.5% | +1.8% |

[^55^]

### 9.4 Key LinkSAGE Contribution

LinkSAGE demonstrates that GNN can improve relevance matching **across all member segments**, including infrequent visitors historically lacking in predictive data. The heterogeneous graph enables information propagation so that nodes with less training data receive signals from neighboring nodes with more robust data [^55^].

---

## 10. Comprehensive Ablation Studies

### 10.1 Follow Feed Ablation (Table 4 from LiGNN paper)

| Experiment Setup | AUC Lift |
|-----------------|----------|
| Baseline SAGE, 20 neighbors, Mean Aggregator | - |
| SAGE, 200 neighbors | +3.2% |
| + Attention Aggregator | +0.9% |
| + Dual Encoder | +2.5% |
| + ID embeddings | **+15.3%** |
| + Graph Densification | +0.5% |
| + 2-hop PPR Sampling | +0.6% |
| + Temporal Graph | +5.8% |

[^96^]

### 10.2 Temporal Model Ablation (Table 1 from LiGNN paper)

See Section 6.4 for full details. Key finding: prefix causal masking outperforms full causal masking, and combining all techniques achieves +5.83% AUC lift [^96^].

### 10.3 Sampling Strategy Comparison (People Recommendations)

| Sampling Method | GNN Validation AUC Lift |
|-----------------|------------------------|
| 2-hop Weighted Sampling | - |
| Multi-Hop PPR Sampling | +2.3% |
| 2-hop PPR Sampling | +2.1% |

[^258^]

### 10.4 Ads CTR Model Ablation

| Edges | Output GNN Embeddings | AUC Lift |
|-------|----------------------|----------|
| Ads | member | +0.17% |
| Ads + graph densification | member | +0.28% |
| Ads + Feed affinity + member connection | member | +0.29% |
| Ads + Feed affinity + member connection | member + creative + campaign | **+0.39%** |

[^96^]

### 10.5 Training Speed Contributions

| Technique | Training Time Reduction |
|-----------|------------------------|
| MLPinit | 16.25% |
| Adaptive neighbor sampling | 24.2% |
| Grouping and Slicing | 69.9% |
| Mixed Precision | 8.0% |
| Local Gradient Aggregation | 35.2% |
| Shared-Memory Queue | 68.0% |
| **Total (combined)** | **7x speedup (24h -> 3.3h)** |

[^258^]

---

## 11. Related Systems at LinkedIn

### 11.1 LiNR (LinkedIn Neural Retrieval)

LiNR is LinkedIn's GPU-based model retrieval system that complements LiGNN embeddings [^295^]:
- Supports billion-sized index on GPU
- Integrates with Venice feature store for near-line embedding updates
- Apache Beam pipeline for joining and transforming feature data
- Full scan model-based retrieval with latencies as low as 4ms
- Applied to Out-of-Network post recommendations with +3% professional DAU improvement
- Uses GNN embeddings as one of multiple embedding sources for retrieval [^296^]

### 11.2 Apache Beam at LinkedIn

LinkedIn processes **4 trillion events daily** through 3,000+ Apache Beam pipelines [^269^]:
- Near real-time processing from 24-48 hour offline delay to millisecond/second latency
- Used for both anti-abuse detection and GNN embedding serving
- Beam's unified framework enables 2x cost-to-serve optimization

---

## 12. Summary of All Production Metrics

| Application | Surface | Metric | Relative Improvement |
|-------------|---------|--------|---------------------|
| LiGNN | Follow Feed | Feed Engaged DAU | +0.5% |
| LiGNN | OON Feed | DAU engaging with professional content | +0.2% |
| LiGNN | Jobs (TAJ) | Hearing back rate | +1.0% |
| LiGNN | Jobs (TAJ) | Premium renewal rate | +0.3% |
| LiGNN | Jobs (TAJ) | Company follows | +1.8% |
| LiGNN | People Recs | Weekly Active User | +0.1% |
| LiGNN | People Recs | New member connections | +2.4% |
| LiGNN | People Recs | Sessions | +0.2% |
| LiGNN | Ads | CTR | +2.0% |
| LinkSAGE | JYMBII | Qualified Applications | +2.2% |
| LinkSAGE | JYMBII | QA Rate | +0.3% |
| LinkSAGE | JYMBII | Job Sessions | +0.6% |
| LinkSAGE | JYMBII | Dismiss to Apply Ratio | -6.0% |
| LinkSAGE | Job Search | Successful sessions | +0.6% |
| LinkSAGE | Job Search | Total applies | +0.5% |
| LinkSAGE | Job Search EBR (Organic) | Successful sessions | +2.4% |
| LiNR | OON Feed | Professional DAU | +3.0% |

[^258^] [^55^] [^295^]

---

## References

[^55^] Liu, P., Wei, H., Hou, X., et al. "Optimizing Job Matching Using Graph Neural Networks." KDD 2024. arXiv:2402.13430. https://arxiv.org/abs/2402.13430

[^81^] ACM Digital Library. "Optimizing Job Matching Using Graph Neural Networks." https://dl.acm.org/doi/10.1145/3690624.3709396

[^96^] Borisyuk, F., et al. "LiGNN: Graph Neural Networks at LinkedIn." KDD 2024. arXiv:2402.11139 PDF. https://arxiv.org/pdf/2402.11139

[^258^] Borisyuk, F., et al. "LiGNN: Graph Neural Networks at LinkedIn." arXiv HTML version. https://arxiv.org/html/2402.11139v1

[^259^] Moonlight Blog (Korean). "LiGNN Paper Review." https://www.themoonlight.io/ko/review/lignn-graph-neural-networks-at-linkedin

[^260^] Moonlight Blog (Chinese). "LiGNN Paper Review." https://www.themoonlight.io/zh/review/lignn-graph-neural-networks-at-linkedin

[^261^] Hugging Face Papers. "LiGNN: Graph Neural Networks at LinkedIn." https://huggingface.co/papers/2402.11139

[^262^] ResearchGate. "LiGNN: Graph Neural Networks at LinkedIn." https://www.researchgate.net/publication/383411382

[^267^] ChatPaper. "LiGNN: Graph Neural Networks at LinkedIn Analysis." https://chatpaper.com/paper/57082

[^268^] ACM DL PDF. "LiGNN: Graph Neural Networks at LinkedIn." https://dl.acm.org/doi/pdf/10.1145/3637528.3671566

[^269^] Apache Beam Case Study. "4 Trillion Events Daily at LinkedIn." https://beam.apache.org/case-studies/linkedin/

[^282^] arXiv. "LiGNN: Graph Neural Networks at LinkedIn Abstract." https://arxiv.org/abs/2402.11139

[^283^] KDD 2024 Presentation Instructions. https://kdd2024.kdd.org/presentation-instructions/

[^294^] Moonlight Blog (English). "LinkSAGE: Optimizing Job Matching Using Graph Neural Networks Review." https://www.themoonlight.io/en/review/linksage-optimizing-job-matching-using-graph-neural-networks

[^295^] LiNR Paper. "LiNR: Model Based Neural Retrieval on GPUs at LinkedIn." CIKM 2024. https://arxiv.org/abs/2407.13218

[^296^] LiNR Paper HTML. "LiNR: Model Based Neural Retrieval on GPUs at LinkedIn." https://arxiv.org/html/2407.13218v2

[^298^] Medium. "Embedding-Based Retrieval: A Novel Approach." https://medium.com/@jvashistha01/embedding-based-retrieval

[^299^] "A Scalable and Efficient Signal Integration System for Job Matching." https://arxiv.org/abs/2507.09797

[^301^] LiGNN PDF Viewer. https://arxiv.org/pdf/2402.11139

[^304^] LinkSAGE PDF. https://dl.acm.org/doi/pdf/10.1145/3690624.3709396

[^306^] MUG: Meta-path-aware Universal Heterogeneous Graph Pre-training. AAAI 2026.

[^308^] WIC Internet. "LinkedIn Economic Graph." https://www.wicinternet.org/2021-11/24/c_941620.htm

[^309^] Harvard Business School. "LinkedIn's Economic Graph." https://d3.harvard.edu/platform-rctom/submission/linkedins-economic-graph/

[^33^] Zenodo. "Graph Neural Networks for the LinkedIn Economic Graph." https://zenodo.org/records/6501633

[^60^] ACM DL. "LiGNN: Graph Neural Networks at LinkedIn." https://dl.acm.org/doi/10.1145/3637528.3671566

[^104^] Emergent Mind. "LiGNN: Graph Neural Networks at LinkedIn." https://www.emergentmind.com/papers/2402.11139

---

*Research compiled from 20+ independent searches across arXiv, ACM, IEEE, Apache Beam documentation, LinkedIn Engineering resources, and academic paper analysis platforms.*

*Last updated: July 2025*
