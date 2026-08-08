## Facet: Feed Algorithm & Recommendation Systems — LinkedIn AI

### Key Findings

- LinkedIn's feed ranking has undergone a fundamental architectural transformation from a "feature factory" of separate task-specific models to unified foundation models (360Brew and LiGR/Feed-SR) that use transformer architectures and semantic understanding [^46^][^48^][^168^][^12^].

- **360Brew**, a 150-billion-parameter decoder-only foundation model (based on Mixtral 8x22B/LLaMA 3), replaced thousands of separate recommendation models and powers 30+ predictive tasks across feed, jobs, people recommendations, and ads [^48^][^46^][^49^].

- **Feed-SR** (Feed Sequential Recommender), deployed February 2026, is a transformer-based sequential ranking model that replaced the DCNv2-based ranker and achieved +2.10% time spent in A/B tests, now serving as the primary member experience on LinkedIn's Feed [^12^][^51^].

- LinkedIn's retrieval pipeline uses **LLM-based dual encoders** fine-tuned on Meta's LLaMA 3 to generate embeddings for users and content, narrowing hundreds of millions of candidates down to ~2,000 per request in milliseconds [^173^][^208^].

- The platform shifted from a **Social Graph** (distribution through connections) to an **Interest Graph** (distribution through semantic topic relevance), enabling content to reach beyond a creator's immediate network based on topic authority [^62^][^163^].

- **Dwell time** has become the most important engagement signal — posts with 61+ seconds of dwell time achieve 15.6% engagement vs. 1.2% at 0-3 seconds, significantly outweighing likes [^62^][^160^][^58^].

- LinkedIn's job matching uses **LinkSAGE**, a Graph Neural Network framework operating on a heterogeneous job marketplace graph with billions of nodes and edges (1B members, 50M jobs, 41K skills), improving relevance matching especially for members with limited data [^83^][^81^].

- **LiNR** (LinkedIn Neural Retrieval) is LinkedIn's GPU-based retrieval system supporting billion-sized indexes, using model-based embedding retrieval with custom CUDA kernels for pre-filtering, contributing to a 3% relative increase in professional DAU [^193^][^194^].

- LinkedIn's **People You May Know (PYMK)** uses a dynamic graph traversal engine with self-tuning models that update daily, processing millions of graph updates per second [^165^].

- **Feathr**, LinkedIn's feature store (now open-source on Azure), has been battle-tested in production for 6+ years with thousands of features, supporting point-in-time joins, aggregations, and embeddings [^172^].

- The **LiFT (LinkedIn Fairness Toolkit)** is an open-source Scala/Spark library for measuring fairness in large-scale ML workflows, deployed across training data measurement, model performance evaluation, and online serving fairness monitoring [^196^][^200^][^201^].

- LinkedIn uses fairness-aware re-ranking in **Talent Search**, achieving a 3X improvement (from 33% to 95%) in queries with gender-representative results without statistically significant impact on business metrics [^199^].

- Post embeddings are generated using a **pre-trained transformer-based LLM fine-tuned via multi-task learning**, outperforming OpenAI's ADA-001/ADA-002 embeddings on LinkedIn-specific tasks and deployed on nearline infrastructure making embeddings available within minutes of post creation [^195^].

- LinkedIn's **Collaborative Articles** use AI to generate topics, select expert contributors based on profile skills/endorsements/job titles, and rank contributions through engagement-based voting [^170^][^171^].

- The feed distribution follows a **4-stage process**: Quality Filtering → Initial Audience Test (first 30-60 min) → Engagement Scoring → Extended Distribution to 2nd/3rd-degree connections [^62^].

---

### Algorithms by Type

#### 1. Feed Ranking & Content Recommendation

**Primary Architecture: Multi-Stage Pipeline**
| Stage | Component | Description |
|-------|-----------|-------------|
| L0 (Retrieval) | LLM-based dual encoder + LiNR | Narrows hundreds of millions to ~2,000 candidates using LLaMA 3 embeddings on GPU [^173^] |
| L1 (Light Ranking) | First Pass Rankers (FPRs) | Separate rankers per inventory type (posts, jobs, articles, connections) [^56^][^37^] |
| L2 (Rich Ranking) | Feed-SR / LiGR | Transformer-based sequential recommender scoring candidates [^12^][^168^] |
| Re-Ranking | Setwise + Fairness Re-Ranker | LiGR setwise attention for diversity; LiFT for fairness [^37^][^196^] |

**Feed-SR (Primary Production Model, Feb 2026)**
- **Architecture**: Transformer-based sequential recommender with interleaved post-action sequences, causal attention mask, RoPE positional encoding [^12^][^51^]
- **Key Innovations**:
  - Uses only ~20% of the features of the previous DCNv2 production model (feature engineering deprecation)
  - Two-tower architecture for passive tasks (click, skip, long-dwell) vs. active tasks (like, comment, share)
  - Late-fusion of sequence features (identity/semantic) and context features (popularity, recency, affinity)
  - Incremental daily training on new interaction data
  - Position debiasing via Inverse Propensity Weighting + learned position offsets
- **Serving**: CPU-optimized inference with member history sequence processing; GPU exploration ongoing
- **Online Impact**: +2.10% time spent vs. DCNv2 production model in A/B tests [^12^]

**LiGR (LinkedIn Generative Recommender)**
- **Architecture**: Modified transformer with learned gated normalization and simultaneous setwise attention to user history and ranked items [^168^]
- **Breakthroughs**:
  - Outperformed prior state-of-the-art using only 7 features (vs. hundreds in baseline)
  - Validated scaling laws for ranking: larger models + more data + longer sequences = better performance
  - Setwise joint scoring for automated diversity improvement
- **Feature Ablation**: Actor ID embeddings were most significant single feature; content embeddings + Actor IDs matched full feature set performance [^168^]

**360Brew (Foundation Model)**
- **Parameters**: 150B decoder-only (Mixtral 8x22B MoE base, LLaMA 3 family) [^48^][^46^]
- **Training**: 9-month development on LinkedIn first-party data (profiles, posts, interactions, jobs) [^48^]
- **Interface**: Textual prompt-based — converts user profiles, post content, and interaction history into natural language prompts for ranking predictions
- **Capabilities**: Zero-shot generalization to new recommendation surfaces; handles 30+ tasks across 8+ surfaces without task-specific fine-tuning [^48^]
- **Example Prompt**: Member profile + job interaction history + task instruction to predict apply/view/dismiss actions [^48^]
- **Deployment Status**: Gradual rollout from mid-2024; publicly announced March 12, 2026 [^46^][^76^]

**Legacy DCNv2 Ranker**
- Two neural network towers (passive vs. active actions)
- DCNv2 module + dense-gating layers + multi-task output
- Numeric features, content embeddings, ID embeddings, categorical features
- Scored on CPU in Java stack [^51^]

#### 2. Interest Graph vs. Social Graph

**The Fundamental Shift (2024-2026)**

| Dimension | Social Graph (Pre-2024) | Interest Graph (2025-2026) |
|-----------|----------------------|---------------------------|
| Distribution basis | Who you know (connections) | What you're interested in (topics) |
| Reach | Limited to network | Extended beyond network |
| Optimization target | Network size | Content quality & topic authority |
| Key metric | Impressions, followers | Engagement quality, dwell time |
| Algorithm | Separate retrieval pipelines | Unified semantic understanding via 360Brew |

- The shift enables a post on a niche topic to reach thousands of interested users even with 500 connections, while generic posts from accounts with 10,000+ connections may remain limited [^62^][^163^]
- Top Creator visibility climbed from 15% (2022) to 31% (2025), while "Other Creator" visibility collapsed from 57% to 28% — a direct symptom of interest-graph distribution rewarding semantic relevance [^62^]
- The most common reason a 2nd-degree post appears in feeds is because a 1st-degree connection commented on it — using interpersonal engagement as a relevance signal [^161^]

#### 3. Job Recommendation AI (LinkSAGE)

**Architecture**: Heterogeneous Graph Neural Network (GNN) framework
- **Graph Scale**: Billions of nodes, billions of edges [^83^]
  - Members: 1B | Jobs: 50M | Skills: 41K | Titles: 25K | Companies: 25M | Positions: 195M
- **Node Types**: member, job, skill, title, company, position (company,title tuple)
- **Edge Types**: 
  - Static attribute edges (member→skill, member→title, job→company, etc.)
  - Implicit interaction edges (member→job for apply/click/save; job→member for recruiter outreach)
  - Reciprocal edges for augmentation

**Key Innovation**: Nearline Inference Pipeline
- GNN encoder pre-computes embeddings stored in in-memory feature store
- Eliminates need for expensive real-time GNN infrastructure
- Latency in low tens of milliseconds
- Enables fresh job embeddings within minutes instead of 24-hour batch delay [^83^]

**Training Approach**:
- Encoder-decoder GNN with inductive graph learning
- Decoupled GNN training from DNN ranking model training
- Transfer learning integrates GNN embeddings into existing DNN models
- Skill-level information critical for graph connectivity (avg member linked to 1.2 top skills) [^55^][^83^]

**Online A/B Test Results**:
- +1.0% Positive Hearing Back rate, +1.8% Company Follows (Top Applicant Job model)
- +20.0% Apply Clicks Positive Interaction, +2.2% survival rate (enriched graph)
- +3.2% increase in Qualified Applications for opportunistic job seekers
- +2.6% rise in Qualified Applications for urgent job seekers [^207^]

**Job Match AI (Launched January 2025)**:
- Uses LLMs for semantic understanding of job descriptions beyond keyword matching
- Analyzes entire profile (headline, skills, experience, education, endorsements)
- Infers unlisted skills (e.g., web developer → likely knows HTML)
- Ranks candidates against all other applicants in real-time
- Free version shows match summary; Premium shows competitive insights + Top Applicant badge [^164^]

#### 4. People You May Know (PYMK)

**Core Architecture**:
- Dynamic graph traversal engine with daily self-tuning models [^165^]
- Mines the LinkedIn Economic Graph (not just connections but companies, schools, and other linked nodes) [^185^]
- Uses AI, ML, and graph mining techniques on the Economic Graph [^185^]

**Candidate Generation**:
- Primary: Friends-of-Friends (FoF) traversal
- Additional sources: Profile views, search co-occurrence, shared professional communities, behavioral signals [^178^]

**Scoring Model Features**:
- **Node features**: company, school, location, title, experience level, account age, activity
- **Edge features**: mutual connections, same company/school, profile view frequency, interaction frequency [^178^]

**Graph Neural Network Approaches**:
- GraphSAGE for scalable neighborhood sampling and aggregation
- GCN for local connectivity pattern capture
- GAT for attention-weighted neighbor aggregation
- PinSage (from Pinterest) cited as high-performance GCN for large-scale recommendation [^25^][^182^]

**Real-time Characteristics**:
- Self-tuning models that adapt to behavior patterns hourly
- Processes millions of graph updates per second
- Balances relevance with "non-creepiness" constraints [^165^]

#### 5. Skill Recommendations & The Skills Graph

**Skills as Graph Infrastructure**:
- LinkedIn's skills graph connects members and jobs through skill nodes
- Average member has 17-18 skills; average job lists 30+ skill requirements
- Top skill scoring model assesses relevance before adding graph edges
- Skill connections facilitate info exchange between members with similar skill sets [^55^][^83^]

**Skill-First Matching**:
- LinkSAGE GNN propagates skill information through graph edges
- Members with less training data receive signals from skill-connected neighbors
- Graph enrichment with skill nodes improved offline recall by +1.5% [^83^]

**Job Match Skill Analysis**:
- Algorithm considers both explicit skills and inferred skills
- Endorsements act as social proof of claimed skills
- Focus on 15-20 most relevant skills out of 50 allowed
- Consistency between claimed skills and experience descriptions checked [^164^]

#### 6. Collaborative Articles AI

**Process**:
1. AI generates topic + editorial team review
2. Algorithms identify "experts" based on: profile skills, skill endorsements, recent job titles, implicit skills from hiring data, likelihood to contribute based on posting/commenting activity
3. Selected experts invited to contribute perspectives
4. Reader engagement (likes, comments) determines "Top Voice" badges
5. Badges reviewed every 60 days [^170^][^171^]

**Expert Selection Signals**:
- Explicit skills from profile
- Endorsement counts for skills
- Recent job titles
- Implicit skills from recent hires and self-evaluation during job applications
- Posting and commenting activity (likelihood to contribute) [^170^]

**Impact**: Called "biggest traffic driver" on the platform within 6 months of March 2023 launch [^170^]

#### 7. LinkedIn Learning Recommendations

**Architecture**: Two-algorithm system [^56^]
1. **Neural Collaborative Filtering**: Course and learner features input into neural network computing ranking scores between learner and course embeddings
2. **Response Prediction**: Separate model predicting engagement likelihood

**Feature Engineering**:
- Course features: topic, instructor, duration, difficulty
- Learner features: job title, industry, skills, career trajectory, past course engagement
- Combines collaborative signals with content-based matching

#### 8. Post Embeddings (CIKM 2025)

**Architecture**:
- Pre-trained transformer-based LLM fine-tuned via multi-task learning
- Multiple semantic labeling tasks with positive transfer across tasks
- Nearline infrastructure: embeddings available within minutes of post creation

**Performance**:
- Outperforms OpenAI ADA-001/ADA-002 on LinkedIn-specific datasets
- Zero-shot learning capability for broader applicability
- Battle-tested in production for 2+ years [^195^]

**Usage**: Feed ranking, Feed retrieval, video ranking retrieval [^195^]

---

### Infrastructure & Architecture

#### Feature Store: Feathr
- Open-sourced on Azure in 2022; battle-tested at LinkedIn for 6+ years
- Serves all LinkedIn ML features with thousands of features in production
- Key capabilities:
  - Scalable: processes billions of rows and PB-scale data
  - Point-in-time joins and aggregations
  - Rich type system including embedding support
  - Feature sharing and reuse via feature registry
  - Pythonic APIs with PySpark/Spark SQL support [^172^]

#### GPU Retrieval: LiNR (LinkedIn Neural Retrieval)
- Large-scale GPU-based retrieval system supporting billion-sized indexes
- Integrates item embeddings and model weights in the same model binary
- Key capabilities:
  - Exhaustive KNN search on GPU with latencies as low as 4ms
  - Attribute-based pre-filtering (custom CUDA kernels)
  - 1-bit quantization reducing 120GB embedding memory to 7.5GB
  - Live model updates without performance degradation
  - Multi-embedding retrieval with Hadamard MLP and Mixture-of-Logits
- Online Impact: +3% relative increase in professional DAU for OON recommendations [^193^][^194^]

#### ProML (Machine Learning Lifecycle Platform)
- Controls entire ML model lifecycle from training to monitoring
- Scales LinkedIn's thousands of production models
- Integrated with Model Cloud for serving [^180^][^181^]

#### Model Cloud / Model Serving Infrastructure
- Framework-agnostic model serving (TensorFlow, PyTorch)
- Java-based native serving stack for low latency
- Supports both CPU inference (current production) and GPU inference (LiNR)
- Nearline inference pipeline for GNN embeddings [^193^][^187^]

#### Nearline Inference for GNN
- Sequential joining with in-memory NoSQL feature store
- "Stateful" job marketplace graph without real-time graph engine
- Average job lifespan ~3 weeks; 50% of job seekers resume sessions within 10 minutes
- Updates embeddings within minutes vs. 24-hour offline delay [^83^]

#### Training Infrastructure
- TensorFlow and PyTorch models
- Apache Spark for distributed data processing
- Daily incremental training for feed ranking models
- Inverse Propensity Weighting for position debiasing
- Recency-weighted loss for capturing evolving interests [^12^]

#### Key Latency Benchmarks
| Component | Latency | Scale |
|-----------|---------|-------|
| LiNR GPU retrieval (single query) | 4ms | 240M embeddings (128-dim, fp16) |
| LiNR top-2K selection | ~97ms p95 | 1B members (64-dim, quantized) |
| Feed candidate retrieval | milliseconds | ~2,000 from hundreds of millions |
| GNN nearline inference | tens of milliseconds | 3-5TB graph |
| Post embedding availability | minutes | nearline |

---

### Ranking Signals Hierarchy (2026)

**Most Important Signals** (in approximate order):

| Signal | Weight/Impact | Notes |
|--------|--------------|-------|
| Dwell Time (61+ sec) | 15.6% engagement vs 1.2% | Primary quality signal [^62^] |
| Saves | ~5x like weight | Strong reference value signal [^49^] |
| Substantive Comments | ~15x like (industry est.) | Thread depth matters [^62^] |
| Private Shares (DMs) | High-intent signal | Most valuable share type [^58^] |
| Profile Actions (post-click) | Quality indicator | Click to profile after reading [^162^] |
| Comment Threads | Aggressive reach expansion | Multi-reply threads weighted heavily [^62^] |
| "See more" expansion | Engagement depth | Opening long posts signals quality |
| Likes | Baseline signal | Lowest algorithmic weight |
| External Links | ~60% reach penalty | Strongly penalized as of 2026 [^160^] |

**Signal Categories Used by Feed-SR**:
- **Sequence features**: Actor/root-actor ID embeddings, content embeddings, post type, lightweight categorical attributes
- **Context features**: Popularity, dwell-time buckets, post age, explicit viewer-actor affinity [^12^]

---

### Trends & Signals

- **Shift to Foundation Models**: LinkedIn is consolidating thousands of separate models into unified foundation models (360Brew, LiGR), reducing technical debt and enabling cross-surface learning [^48^][^168^].

- **Semantic Understanding Over Keywords**: LLM-based retrieval understands semantic relationships between topics (e.g., "electrical engineering" → "small modular reactors") without keyword overlap [^173^][^209^].

- **Dwell Time as Primary Metric**: All major social platforms are moving beyond binary engagement signals; LinkedIn explicitly optimizes for time spent and depth of engagement [^12^][^58^][^62^].

- **Sequential Recommendation**: Feed-SR treats user interaction history as a sequence rather than a static profile, enabling faster adaptation to evolving interests [^12^].

- **Graph Neural Networks for Heterogeneous Data**: LinkSAGE demonstrates GNNs can effectively model multi-type relationships (member-job-skill-title-company) at billion-node scale [^83^].

- **Nearline Inference**: The industry trend of pre-computing expensive model outputs (like GNN embeddings) and storing them in feature stores for low-latency serving is validated by LinkSAGE's architecture [^83^].

- **Fairness as First-Class Concern**: LiFT is deployed across LinkedIn's ML pipelines, and fairness-aware re-ranking in Talent Search achieved 3X improvement in gender representation without business metric degradation [^199^][^200^].

- **Company Page Reach Collapse**: Organic reach for company pages dropped to ~2-4% of feed allocation, making employee advocacy the primary organic growth channel [^161^][^163^].

- **Content Volume Growth**: Content creation up 14% YoY, driving need for more aggressive quality filtering and anti-spam measures [^Context^].

- **AI Content Detection**: LinkedIn actively downranks "overly AI-sounding" content and detects coordinated engagement pods, with flagged accounts facing 60-90 day shadow bans [^162^][^46^].

---

### Controversies & Conflicting Claims

1. **360Brew Deployment Status**: The research paper was published January 2025, but LinkedIn only officially announced feed deployment on March 12, 2026. Independent analysts estimate 40-100% deployment as of early 2026, with LinkedIn never confirming exact percentages [^76^][^46^].

2. **Comment Weight Discrepancy**: Industry estimates claim comments are ~15x the weight of likes, but AuthoredUp's NLP-aware analysis suggests ~2x with quality scoring — indicating raw comment count matters less than comment substance [^62^].

3. **Top Creator Visibility vs. Average Creator**: Richard van der Blom's analysis of 1.8M posts shows Top Creator visibility doubled (15% → 31%) while average creator visibility collapsed (57% → 28%), suggesting the algorithm concentrates reach among established voices [^62^].

4. **Collaborative Article Quality Concerns**: Expert selection based primarily on profile skills/endorsements (which can be gamed) raises questions about actual expertise verification. The "top voice" badge system based on engagement quantity is susceptible to pod-like coordination [^170^].

5. **PYMK "Rich Get Richer"**: The algorithm tends to recommend users with similar backgrounds who are more likely to accept connections, creating a feedback loop where well-connected users get more recommendations, amplifying network inequality [^202^].

6. **Feed-SR vs. LLM Ranking**: Feed-SR was chosen over fine-tuned LLM-based ranking architectures due to better combination of online metrics and production efficiency, suggesting LLMs are not yet cost-effective for ranking at LinkedIn's scale [^12^].

7. **Interest Graph vs. Social Graph Tension**: Despite the proclaimed shift to interest graph, feed composition studies show 42.44% 1st-degree connections and 19.51% 2nd-degree — suggesting social connections still dominate, with interest-based OON content being a smaller fraction [^161^].

---

### Recommended Deep-Dive Areas

- **360Brew In-Context Learning**: How feeding 2-3 months of member activity directly into model prompts affects personalization quality and the "cold start" problem for new users. The paper notes this approach eliminates feature engineering but raises questions about prompt length limits and computational cost [^48^].

- **Feed-SR Sequence Length Scaling**: The paper shows clear scaling laws for sequence length but plateauing returns for ID embedding dimensions and layer count — understanding optimal sequence length for different user activity levels could inform product design [^12^].

- **LinkSAGE Nearline Inference Architecture**: The approach of decoupling GNN training from DNN ranking via pre-computed embeddings in a feature store represents a pragmatic pattern for industrial GNN deployment that could generalize to other heterogeneous graph applications [^83^].

- **LiGR Setwise Attention for Diversity**: The automated diversity improvements from setwise joint scoring represent a significant advance over rule-based diversity re-rankers — understanding the trade-offs between diversity and relevance in professional contexts warrants exploration [^168^].

- **Fairness-Aware Ranking in Hiring**: The 3X improvement in gender representation in Talent Search without business metric degradation is a landmark result; understanding how the re-ranking algorithm balances representation with relevance could inform hiring platform design globally [^199^].

- **LLM-Based Retrieval at Scale**: The use of LLaMA 3 as a dual encoder for feed retrieval, with quantization techniques enabling production-scale serving, represents a frontier in applying foundation models to high-throughput recommendation [^173^].

- **Economic Graph Embeddings (Company2Vec)**: The approach of computing company embeddings from member transition data and using them in Bayesian models for salary prediction shows how graph structure enables inference at sparse data points [^176^].

- **Co-Design of Model and Infrastructure**: LinkedIn's emphasis on modelers and infrastructure teams working together from the start, customizing storage and compute layers for AI workloads, represents an organizational pattern critical for scaling [^187^].

---

### Source Index

| Citation | Source | Type | Date |
|----------|--------|------|------|
| [^12^] | arXiv 2602.12354 | Research Paper | Feb 2026 |
| [^17^] | The Linked Blog | Industry Analysis | Mar 2026 |
| [^25^] | aman.ai (Distilled) | Technical Summary | 2017 |
| [^33^] | Zenodo / LinkedIn GNN | Conference Presentation | Apr 2022 |
| [^37^] | TrustInsights.ai | Industry Report | 2025 |
| [^46^] | Falia.co | Technical Analysis | Apr 2026 |
| [^48^] | arXiv 2501.16450 (360Brew) | Research Paper | Jan 2025 |
| [^49^] | pettauer.net | Research Report | Jan 2026 |
| [^51^] | arXiv 2602.12354v1 | Research Paper | Feb 2026 |
| [^55^] | arXiv 2402.13430 | Research Paper | Feb 2024 |
| [^56^] | PyImageSearch | Technical Tutorial | Aug 2023 |
| [^58^] | digitalapplied.com | Industry Guide | Feb 2026 |
| [^62^] | meet-lea.com | Technical Analysis | Apr 2026 |
| [^76^] | thelinkedblog.com | Industry Analysis | Oct 2025 |
| [^81^] | ACM KDD 2024 | Conference Paper | 2024 |
| [^83^] | arXiv 2402.13430 (LinkSAGE) | Research Paper | Feb 2024 |
| [^160^] | dataslayer.ai | Industry Report | Feb 2026 |
| [^161^] | dsmn8.com | Industry Research | Mar 2026 |
| [^162^] | sourcegeek.com | Technical Guide | Jan 2026 |
| [^163^] | saleshigher.com | Technical Analysis | Mar 2026 |
| [^164^] | theinterviewguys.com | Industry Guide | Nov 2025 |
| [^165^] | techpreneurr.medium.com | Technical Analysis | Aug 2025 |
| [^168^] | arXiv 2502.03417 (LiGR) | Research Paper | Feb 2025 |
| [^170^] | practicalsmm.com | Industry Guide | Jul 2024 |
| [^171^] | hawkemedia.com | Industry Analysis | Apr 2023 |
| [^172^] | Microsoft Azure Blog | Engineering Blog | Apr 2022 |
| [^173^] | arXiv 2510.14223 | Research Paper | Oct 2025 |
| [^175^] | DigitalOcean | Industry Guide | Sep 2025 |
| [^176^] | ACM SIGKDD 2018 | Conference Paper | 2018 |
| [^178^] | dzone.com | Technical Tutorial | Apr 2026 |
| [^180^] | thesequence.substack.com | Newsletter | Dec 2020 |
| [^181^] | Towards AI | Technical Article | Apr 2022 |
| [^182^] | diva-portal.org (Thesis) | Academic Thesis | 2021 |
| [^185^] | InfoQ Presentation | Conference Presentation | Dec 2018 |
| [^187^] | weka.io (AI Summit) | Conference Talk | Mar 2026 |
| [^193^] | arXiv 2407.13218 (LiNR) | Research Paper | Jul 2024 |
| [^194^] | arXiv 2407.13218 (LiNR) | Research Paper | Jul 2024 |
| [^195^] | arXiv 2405.11344 (CIKM 2025) | Research Paper | Nov 2023 |
| [^196^] | ACM CIKM 2020 (LiFT) | Conference Paper | 2020 |
| [^199^] | ACM CIKM 2018 | Conference Paper | 2018 |
| [^200^] | VentureBeat | News Article | Aug 2020 |
| [^201^] | GitHub (linkedin/LiFT) | Open Source | 2020 |
| [^202^] | Cornell University Blog | Academic Blog | Sep 2021 |
| [^205^] | arXiv 1809.06473 | Research Paper | 2018 |
| [^207^] | liner.com | Paper Review | Feb 2024 |
| [^208^] | almcorp.com | Industry Analysis | Mar 2026 |
| [^209^] | Yahoo Tech / Social Media Today | News Article | Mar 2026 |
