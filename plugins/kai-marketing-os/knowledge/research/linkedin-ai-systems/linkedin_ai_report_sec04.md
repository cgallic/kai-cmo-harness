## 4. Graph Neural Networks: The Economic Graph Backbone

The feed ranking pipeline described in the preceding chapter does not operate in a vacuum. The embedding-based retrieval (EBR) stage that surfaces the initial candidate set of ~1,500 posts per member request draws its semantic signal, in large part, from a graph neural network (GNN) framework that encodes the LinkedIn Economic Graph — a heterogeneous structure of more than 100 billion nodes and several hundred billion edges spanning members, jobs, companies, skills, titles, and content [^96^] [^258^]. This chapter examines the architecture, training infrastructure, and production deployment of LiGNN, the GraphSAGE-based encoder-decoder system that serves as the backbone for retrieval and ranking across LinkedIn's major surfaces, and LinkSAGE, its specialized variant for job matching. Together, these systems illustrate how a single embedding space, learned from a unified graph, can be adapted to disparate downstream tasks while maintaining inference latencies in the low tens of milliseconds.

### 4.1 LiGNN Framework Architecture

#### 4.1.1 Scale: The Heterogeneous Economic Graph

The LinkedIn Economic Graph is a digital representation of the global professional economy, connecting entities across 200+ countries [^308^]. Unlike homogeneous social graphs where a single node type dominates, the Economic Graph integrates at least nine distinct node types into a single unified embedding space [^258^]. Member profiles constitute the largest node set at approximately one billion; job postings add roughly 50 million; companies contribute 25 million; canonical skills number 41,000; job titles 25,000; and (company, title) position tuples 195 million [^55^]. Posts, ad campaigns, and ad creative nodes add further millions. The total node count exceeds 100 billion when intermediate nodes are counted, with edges in the several hundred billion [^282^].

This heterogeneity is central to the graph's utility. Three broad edge categories connect these nodes: engagement edges (member liked post, member applied to job), weighted by interaction strength; affinity edges recording historical member-creator interactions; and attribute edges encoding "HAS-A" relationships such as "member has title software engineer" at uniform weight [^258^] [^260^]. The combination of social, activity, and knowledge graph signals into a single structure enables information to propagate across entity types — a member's skill connections can inform job recommendations even when direct member-job interactions are sparse.

| Node Type | Approximate Count | Representative Edge Types |
|-----------|------------------:|---------------------------|
| Members | 1 billion | Member-post like, member-job apply, member-member connect |
| Jobs | 50 million | Member-title (1B edges), member-skill (1.2B), job-skill (33M) |
| Companies | 25 million | Member-company (966M), job-company (42M) |
| Skills | 41,000 | Skill-relevance scored member-skill and job-skill links |
| Titles | 25,000 | Member-title (1B), job-title (46M) |
| Positions | 195 million | Member-position (139M), job-position (41M) |
| Posts / Campaigns / Creatives | Millions | Ad impression, click, seeker engagement (2.7B) |

*Table: LinkedIn Economic Graph node and edge type inventory. Attribute edge counts are drawn from the LinkSAGE job-marketplace subgraph; the full LiGNN graph contains additional surface-specific edges [^55^] [^258^].*

The scale imposes hard engineering constraints. Pre-computing sampled subgraphs for 500 million nodes required 20 hours of Spark processing and inflated storage to 10× the original graph size before LinkedIn switched to real-time sampling [^258^]. Operating on the full graph demands both algorithmic efficiency in neighbor sampling and systems-level optimizations to keep training and inference tractable. The choice to abandon Spark pre-computation in favor of real-time sampling via DeepGNN was a pivotal infrastructure decision: it eliminated the 20-hour preprocessing step, reduced storage overhead to 1× graph size, and accelerated model iteration by 10× by removing the need to regenerate static graphs for any sampling parameter change [^258^].

#### 4.1.2 GraphSAGE Encoder-Decoder and the 7× Training Speedup

LiGNN adopts an encoder-decoder architecture designed to generate reusable node embeddings that downstream models consume as features [^258^]. This decoupled design is deliberate: the encoder produces embeddings without a full GNN inference pass at serving time, avoiding the latency penalty that has historically limited GNN adoption in real-time recommenders.

The encoder follows the GraphSAGE framework with inductive learning capabilities. Sampling is performed by the Microsoft DeepGNN graph engine, supporting multi-hop random sampling, weighted sampling configurable per edge type, Personalized PageRank (PPR) sampling, and an optimized two-hop PPR variant selected as the production default after delivering +2.1% AUC with 3× the speed of multi-hop PPR [^258^]. Aggregation supports both mean pooling and attention-based aggregation, the latter delivering +0.9% AUC on Follow Feed [^96^]. The decoder offers three configurations: an MLP for classification/regression, cosine similarity for link prediction, and in-batch negative sampling using dot products [^258^].

Ablation studies reveal that architectural choices compound non-linearly. Increasing neighbors from 20 to 200 improved AUC by +3.2%; attention aggregation added +0.9%; dual encoders (separate parameters for source and destination nodes) added +2.5% on link prediction; and the single largest gain — +15.3% AUC — came from learnable ID embeddings [^96^]. This finding is notable: node identity carries substantial predictive signal that structural neighborhood information alone cannot capture.

Training at scale required a 7× speedup to make iteration feasible. LinkedIn achieved this through stacked complementary optimizations whose combined effect reduced training from 24 hours to 3.3 hours [^258^].

| Optimization Technique | Time Reduction | Mechanism |
|------------------------|---------------:|-----------|
| Grouping and slicing | 69.9% | Group records by member_id; batch graph engine queries (group_size=4) |
| Shared-memory queue | 68.0% | Python multiprocessing with zero-copy inter-process transfer |
| Local gradient aggregation | 35.2% | Local gradient accumulation for N steps before AllReduce |
| Adaptive neighbor sampling | 24.2% | Start with 2 neighbors, increase by 20 when AUC plateaus |
| MLPinit | 16.25% | Pre-train encoders without graph engine queries |
| Mixed precision (FP16) | 8.0% | FP16 forward/backward, FP32 reductions |
| **Combined (measured)** | **7×** | **24h → 3.3h** |

*Table: LiGNN training speed optimizations. Percentages are not additive due to overlap; the 7× figure is empirically measured [^258^].*

The largest contributor — grouping and slicing at 69.9% — exploits the observation that active members interact with multiple items. By grouping training records, ten graph engine queries for a member with ten interactions become two queries. The shared-memory queue eliminates copying overhead between Python processes during parallel prefetching. Local gradient aggregation effectively increases batch size, reducing distributed AllReduce frequency. Training stability improved in parallel from a ~30% success rate to over 90% through gRPC retry logic (+15%), switching from TensorFlow MultiWorkerMirroredStrategy to Horovod with NCCL 2 (+35%), and fixing a data generator memory leak (+10%) [^258^].

#### 4.1.3 Near-Line Inference via Apache Beam + Kafka

LiGNN's inference pipeline operates near-line: Kafka events trigger Apache Beam stream processing, which collects features, runs GNN forward passes, and writes embeddings to Venice (LinkedIn's feature store) within minutes of an interaction [^258^] [^269^]. This design trades the freshness of real-time inference for the latency budget required by downstream ranking models. Events such as clicks, connections, or job applications trigger the pipeline; downstream EBR and ranking systems consume the resulting embeddings via Venice lookups.

The near-line approach is viable because GNN embeddings are relatively stable — a member's graph neighborhood changes gradually, and small perturbations do not dramatically shift the encoded representation. This stability enables pre-computation but means the system cannot capture very recent graph dynamics within the same request cycle. LinkedIn addresses this by combining near-line GNN embeddings with real-time behavioral features in the ranking model, allowing the transformer-based ranker to compensate for embedding staleness with up-to-the-moment activity sequences.

### 4.2 LinkSAGE for Job Matching

#### 4.2.1 The Heterogeneous Job Marketplace Graph

While LiGNN provides a general embedding framework, LinkSAGE specializes it for the job marketplace. Published at KDD 2024 alongside LiGNN, LinkSAGE operates on what LinkedIn describes as "the largest and most intricate job marketplace graph in the industry" [^55^]. The subgraph retains the same heterogeneous node set but constructs edges with a skill-first philosophy: skills are the primary bridge between members and jobs. Members link to an average of 1.2 top skills; jobs to 0.67 top skills, identified by a relevance scoring model [^55^]. Bidirectional edges connect members to titles, members to skills, and members/jobs to positions, allowing information to flow in both directions. Adding skill nodes improved recall by +1.5% versus a baseline without them [^55^].

#### 4.2.2 Decoupled GNN Training from DNN Serving

LinkSAGE's central architectural decision is strict separation of GNN encoder training from DNN ranking model serving. The encoder is trained on the full heterogeneous graph, but encoder outputs are pre-computed through the same near-line Apache Beam + Kafka pipeline and stored in an in-memory feature store [^55^]. Downstream DNN ranking models consume stored embeddings as additional features via transfer learning, integrating graph-derived signals without executing a GNN forward pass during live requests.

This decoupling provides key operational advantages. GNN retraining occurs on its own cadence while DNN models continue their normal training cycle. Graph signals remain sufficiently fresh through near-line inference. And serving latency stays in the low tens of milliseconds [^55^] — critical for job search and recommendation pages where user abandonment rises steeply with load time. Without this decoupling, the full value of GNN embeddings would not be available until the next day's batch inference completed, an unacceptable delay given the volume of jobs posted daily.

#### 4.2.3 Equity for Cold-Start Job Seekers

A significant finding from LinkSAGE's deployment is its disproportionate benefit for cold-start members. In the heterogeneous graph, information propagates through edges: a member with sparse direct interactions receives signal from neighboring nodes — connected skills, similar titles, peer companies — that have richer data [^55^]. Segment-level A/B tests on Jobs You May Be Interested In (JYMBII) illustrate the pattern: opportunistic job seekers saw qualified applications rise +3.2% and dismiss-to-apply fall -13.8%; members explicitly open to work saw +2.8% qualified applications and -24.2% dismiss-to-apply; urgent job seekers saw +2.6% and -25.3% respectively [^55^]. The progressively larger dismiss-to-apply improvements for more active segments suggest the graph surfaces more relevant jobs precisely when recommendation quality matters most.

Across other surfaces, results were consistent: Top Applicant Jobs (premium) saw +1.0% hearing-back rate and +1.8% company follows; Job Search saw +0.6% successful sessions and +0.5% total applies; and embedding-based retrieval for organic job search increased successful sessions by +2.4% [^55^]. The breadth of improvements across retrieval, ranking, and multiple product surfaces indicates that graph-derived signals generalize across the job recommendation funnel rather than helping at a single stage.

### 4.3 Cold-Start Handling and Temporal Modeling

#### 4.3.1 HNSW-Based Graph Densification

The power-law degree distribution inherent in social graphs — most nodes have few connections, a small fraction have many — poses a fundamental challenge for neighborhood aggregation. GNNs perform poorly on low-degree nodes because aggregation has insufficient neighbor signal to draw upon [^96^]. LiGNN addresses this through graph densification: adding approximately 50 artificial edges per low-degree node based on content similarity.

The algorithm queries an external content embedding for each cold-start node — profile LLM embeddings for members, content embeddings for items — and uses an in-house HNSW (Hierarchical Navigable Small World) approximate nearest neighbor search to find the k≈50 most similar high-out-degree nodes [^96^]. Edges are created subject to degree bounds: nodes above the 90th percentile out-degree are not augmented, and only nodes below the 36th percentile receive artificial edges. This ensures information flows from well-connected active nodes to sparsely connected nodes through semantic similarity bridges rather than creating dense clusters of already well-connected nodes.

Production impact is measurable but modest: +0.5% validation AUC on Follow Feed, +0.28% on Ads CTR [^96^]. Its primary contribution is equity — new members, newly posted jobs, and infrequent creators receive structurally informed representations that would otherwise be unattainable. This equity effect compounds with LinkSAGE's cold-start benefits, creating a multi-layered defense against the cold-start problem that affects all large-scale recommendation systems.

#### 4.3.2 Transformer-Based Sequence Model with Prefix Causal Masking

Standard GNNs are inherently static: they encode topology but not the temporal dynamics of when edges formed or how a member's activity sequence unfolds. LiGNN integrates a transformer-based temporal model directly into the GNN encoder to capture these dynamics [^258^].

For a target member, the system samples the last N=100 activities before a cutoff time, preserving temporal ordering. The GraphSAGE encoder processes the static graph neighborhood and produces a multi-head output with H=4 heads, reshaped into a sequence of length H and dimension d. These H "SAGE tokens" are concatenated with N "activity tokens," producing a combined sequence of length H+N [^96^]. A transformer encoder processes this sequence with prefix causal masking: the first H SAGE tokens attend bidirectionally to each other, while each activity token attends to all H SAGE tokens and only to preceding tokens within the activity sub-sequence. This design allows the temporal sequence to draw on full graph context while maintaining causal structure within activities.

Training combines standard binary cross-entropy for link prediction with a long-term loss that splits the N-length sequence into N1 past and N2=10 future events; embeddings at position N1 predict embeddings from N1 through N, capturing dependencies beyond immediate next-step prediction [^96^].

The combined temporal modeling components achieved a +5.83% AUC lift on Follow Feed data (AUC 0.71978 → 0.76176) [^96^]. In production, the temporal model delivered +5.8% AUC lift on Follow Feed and +6.8% on job recommendations, with +0.4% job viewers and +0.4% qualified applicants [^258^] [^96^]. The integration of transformer temporal modeling into the GNN encoder means that produced embeddings encode both who a member is connected to and how their activity has evolved — a richer, temporally grounded signal than any static graph representation could provide.

### 4.4 LiGNN in the Broader Retrieval-Ranking Pipeline

The GNN embeddings produced by LiGNN and LinkSAGE serve as one of several embedding sources for LinkedIn's GPU-based neural retrieval system (LiNR), which supports billion-scale indices with latencies as low as 4 milliseconds [^295^]. LiNR integrates GNN embeddings with text embeddings from BERT/T5 and LLM-generated embeddings from fine-tuned LLaMA-3 models, performing full model-based scans. This multi-source embedding fusion — graph structure, text semantics, and large language model representations — forms the retrieval foundation upon which the Feed-SR ranking model described in Chapter 3 operates. The separation of concerns is precise: GNNs encode relational graph structure, LLMs encode semantic text understanding, and the transformer ranker sequences user behavior to produce the final ordered list. Each layer compensates for the others' limitations — the GNN's temporal staleness is offset by the ranker's real-time activity sequences; the LLM's lack of explicit relational reasoning is complemented by the graph's propagated neighborhood signals. This compositional architecture — rather than any single model — enables LinkedIn to operate a unified AI system across a billion-member graph at production scale.
