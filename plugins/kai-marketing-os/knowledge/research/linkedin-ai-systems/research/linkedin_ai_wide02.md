# Facet: Engineering Blog & Technical Papers — LinkedIn AI/ML Systems

> **Research Date:** 2025-07-17
> **Scope:** LinkedIn's published technical content about AI/ML systems, including engineering blogs, academic papers (arXiv, ACM, IEEE), conference proceedings, and open-source projects.
> **Searches Conducted:** 15+ independent search queries across Google, arXiv, ACM DL, and direct blog browsing
> **Total Publications Found:** 30+ papers, 10+ open-source projects, 15+ engineering blog series

---

## Key Findings

- **LinkedIn operates one of the most extensive industrial AI research programs**, with publications spanning KDD, RecSys, AAAI, CIKM, and arXiv. Two flagship papers — **LiGNN** (Graph Neural Networks) [^1^] and **LiRank** (Large-Scale Ranking) [^2^] — represent their most significant recent contributions.

- **The "AI solving AI" content detection system** (led by Laura Lorenzetti, VP of Product & Executive Editor) uses human-editor-annotated training data and ML classifiers to detect AI-generated posts, comments, and engagement bait at scale [^3^].

- **LinkedIn's open-source ecosystem is substantial**: Apache Kafka, Apache Pinot, Feathr (feature store), and Liger Kernel (GPU-optimized LLM training) are all open-sourced tools that originated at LinkedIn [^4^][^5^][^6^].

- **The Pro-ML platform** unifies the entire ML lifecycle across LinkedIn, featuring a custom DSL, Quasar execution engine, Frame feature marketplace (tens of thousands of features), and Health Assurance monitoring [^7^].

- **LinkedIn's Economic Graph** (1B+ nodes, 200B+ edges) powers GNN-based recommendations across Feed, Jobs, People, and Ads — with reported production lifts of 0.5% Feed DAU, 1% job application hearing-back rate, 2% Ads CTR [^1^].

- **Recent work on LLM-based retrieval** (AAAI 2026) fine-tunes Meta's LLaMA-3 as a dual encoder for feed content retrieval, showing significant gains especially for newer members [^8^].

---

## Publications by Category

### Category 1: Graph Neural Networks (GNN)

#### 1.1 LiGNN: Graph Neural Networks at LinkedIn
| Field | Details |
|-------|---------|
| **Title** | LiGNN: Graph Neural Networks at LinkedIn |
| **Authors** | Fedor Borisyuk, Shihai He, Yunbo Ouyang, Morteza Ramezani, Peng Du, Xiaochen Hou, Chengming Jiang, Nitin Pasumarthy, Priya Bannur, Birjodh Tiwana, Ping Liu, Siddharth Dangi, Daqi Sun, Zhoutao Pei, Xiao Shi, Sirou Zhu, Qianqi Shen, Kuang-Hsuan Lee, David Stein, Baolei Li, Haichao Wei, Amol Ghoting, Souvik Ghosh |
| **Venue** | KDD 2024 (Barcelona, Spain) |
| **Date** | August 2024 |
| **arXiv** | [2402.11139](https://arxiv.org/abs/2402.11139) |
| **ACM DL** | [10.1145/3637528.3671566](https://dl.acm.org/doi/10.1145/3637528.3671566) |

**Key Technical Contributions:**
- Deployed large-scale GNN framework on LinkedIn's heterogeneous graph (100B nodes, hundreds of billions of edges)
- **Encoder-decoder architecture** using GraphSAGE with inductive learning for multi-entity (members, posts, jobs, companies, ads)
- **Temporal graph modeling** with transformer-based sequence models and long-term losses (+5.83% AUC on Feed data)
- **Graph densification** for cold-start via approximate k-NN (HNSW-based) artificial edge injection
- **7x training speedup** via adaptive neighbor sampling, grouping/slicing, shared-memory queue, local gradient optimization
- **Production metrics**: +1% job hearing-back rate, +2% Ads CTR, +0.5% Feed engaged DAU, +0.2% sessions, +0.1% WAU [^1^]
- Near-line inference pipeline using Apache Beam with Kafka-triggered embedding generation

**System Architecture:**
- Graph Engine (GE): Microsoft's DeepGNN on CPU nodes via Kubernetes
- GNN Trainer: GPU nodes with TensorFlow, using gRPC to fetch sampled compute graphs
- Two-hop Personalized PageRank (PPR) sampling preferred over random/weighted sampling
- Post-training quantization (8-bit row-wise middle-max) for model compression

#### 1.2 Graph Neural Networks for the LinkedIn Economic Graph (Presentation)
| Field | Details |
|-------|---------|
| **Title** | Graph Neural Networks for the LinkedIn Economic Graph |
| **Venue** | Zenodo presentation |
| **Date** | April 2022 |
| **URL** | [zenodo.org/records/6501633](https://zenodo.org/records/6501633) |

**Key Contributions:**
- Overview of applying GNNs to LinkedIn's Economic Graph (1B nodes, 200B edges)
- Combines social graph, activity graph, and knowledge graphs into one heterogeneous graph
- Case study: identifying job postings with vague titles and replacing them with more specific titles using GNNs [^9^]

---

### Category 2: Feed Ranking & Recommendation Systems

#### 2.1 LiRank: Industrial Large Scale Ranking Models at LinkedIn
| Field | Details |
|-------|---------|
| **Title** | LiRank: Industrial Large Scale Ranking Models at LinkedIn |
| **Authors** | (Large team, lead: Fedor Borisyuk, David Stein, et al.) |
| **Date** | February 2024 |
| **arXiv** | [2402.06859](https://arxiv.org/abs/2402.06859) |
| **ACM DL** | [10.1145/3637528.3671561](https://dl.acm.org/doi/10.1145/3637528.3671561) |

**Key Technical Contributions:**
- **Residual DCN**: Enhances DCNv2 with attention mechanism in low-rank cross net, plus skip connections (+2.15% contributions in Feed)
- **Isotonic Calibration Layer**: First trainable isotonic regression layer co-trained within DNN; bucketizes logits with trainable per-bucket weights using ReLU for monotonicity (+1.08% contributions)
- **Dense Gating + Large MLP**: Captures higher-order dense feature interactions (+1.00% and +1.23% respectively)
- **TransAct (Transformer-based history modeling)**: Two-layer Transformer-Encoder processing member interaction sequences, max-pooling token as feature (+1.66%)
- **Bayesian explore/exploit**: Neural Linear approach with Bayesian linear regression on last layer weights for Thompson Sampling
- **Multi-task learning**: Grouping strategy (+0.75%), MMoE (+1.19%), PLE (+1.34%) — but Grouping preferred for parameter efficiency
- **Dwell time modeling**: Binary classifier for context-dependent percentile dwell prediction (+0.8% time spent)
- **Incremental training**: 96% reduction in training time with metric boosts (+1.02% contributions)
- **Production metrics**: +0.5% Feed sessions, +1.76% qualified job applicants, +4.3% Ads CTR [^2^]

**Architecture Details:**
- Point-wise ranking with multi-task architecture: click tower (click + long dwell) and contribution tower (like, comment, share, vote)
- Sparse ID embedding features via Member/Actor and Hashtag Embedding Tables
- QR hashing for vocabulary compression (5x param reduction for Jobs)
- 8-bit middle-max embedding table quantization (+0.9% CTR in Ads)
- Custom Avro Tensor Dataset Loader (50% e2e training time reduction)
- Model parallelism: training time reduced from 70 to 20 hours

#### 2.2 Large Scale Retrieval for LinkedIn Feed Using Causal Language Models
| Field | Details |
|-------|---------|
| **Title** | Large Scale Retrieval for the LinkedIn Feed Using Causal Language Models |
| **Authors** | Sudarshan Srinivasa Ramanujam, Antonio Alonso, Saurabh Kataria, Siddharth Dangi, Akhilesh Gupta, Birjodh Singh Tiwana, Manas Haribhai Somaiya, Luke Simon, David Byrne, Sojeong Ha, Sen Zhou, Andrei Akterskii, Zhanglong Liu, Samira Sriram, Zihan Xiong, Zhoutao Pei, Angela Shao, Alex Li, Annie Xiao, Caitlin Kolb, Thomas Kistler, Zach Moore, Hamed Firooz |
| **Venue** | AAAI 2026 |
| **arXiv** | [2507.21117](https://arxiv.org/abs/2507.21117) / [2510.14223](https://arxiv.org/abs/2510.14223) |

**Key Technical Contributions:**
- Fine-tunes Meta's LLaMA-3 as a dual encoder for embedding-based retrieval (EBR) in LinkedIn Feed
- Consolidates multiple retrieval sources (inverted indices, collaborative filtering, trending) into a single unified EBR system
- Prompt design encodes member profile + interaction history as text; quantizes numerical features for better retrieval-ranking alignment
- Serves 2000 candidates from millions with millisecond latency at thousands of QPS
- Significant gains for newer members lacking strong network connections [^8^]

#### 2.3 LinkedIn Post Embeddings: Industrial Scale Embedding Generation
| Field | Details |
|-------|---------|
| **Title** | LinkedIn Post Embeddings: Industrial Scale Embedding Generation and Usage across LinkedIn |
| **Venue** | CIKM 2025 (Accepted) |
| **arXiv** | [2405.11344](https://arxiv.org/abs/2405.11344) |
| **Date** | November 2023 |

**Key Technical Contributions:**
- Pre-trained transformer-based LLM fine-tuned with multi-task learning across diverse semantic labeling tasks
- 50-dimensional embeddings outperform OpenAI ADA-001/ADA-002 on LinkedIn-specific tasks
- Positive transfer observed across all tasks via multi-task training
- Near-line infrastructure makes embeddings available within minutes of post creation
- Powers Feed ranking, Feed retrieval, out-of-network recommendations, and video ranking [^10^]

#### 2.4 LiNR: Model Based Neural Retrieval on GPUs at LinkedIn
| Field | Details |
|-------|---------|
| **Title** | LiNR: Model Based Neural Retrieval on GPUs at LinkedIn |
| **arXiv** | [2407.13218](https://arxiv.org/abs/2407.13218) |
| **Date** | July 2024 |

**Key Technical Contributions:**
- Differentiable GPU model-based retrieval combining exhaustive search with pre-filtering
- Item vectors + model weights coexist in same model binary (unlike traditional ANN indexing)
- Full-scan model-based index serving on GPUs with latencies as low as 4ms
- Handles indexes from 15M to 1B entries
- Multi-embedding retrieval algorithms for quality improvement
- Live-updatable model-based index serving infrastructure [^11^]

---

### Category 3: Job Recommendation Systems

#### 3.1 GLMix: Generalized Linear Mixed Models For Large-Scale Response Prediction
| Field | Details |
|-------|---------|
| **Title** | GLMix: Generalized Linear Mixed Models For Large-Scale Response Prediction |
| **Authors** | Xianxing Zhang, Yitong Zhou, Yiming Ma, Bee-Chung Chen, Liang Zhang, Deepak Agarwal |
| **Venue** | KDD 2016 |
| **ACM DL** | [10.1145/2939672.2939684](https://dl.acm.org/doi/10.1145/2939672.2939684) |

**Key Technical Contributions:**
- Introduces per-user and per-item random effects to logistic regression for personalized response prediction
- Parallelized Block Coordinate Descent under BSP paradigm on Apache Spark
- Two-stage ranking: Lucene-based first-pass + GLMix full model second-pass
- **Production impact**: 20-40% more job applications for job seekers at LinkedIn [^12^]
- Open-sourced as part of Photon-ML library

#### 3.2 CaSMoS: Candidate Selection Models over Structured Queries
| Field | Details |
|-------|---------|
| **Title** | CaSMoS: A Framework for Learning Candidate Selection Models over Structured Queries and Documents |
| **Authors** | Fedor Borisyuk, Krishnaram Kenthapadi, David Stein, Bo Zhao |
| **Venue** | KDD 2016 |
| **URL** | [PDF](http://www-cs-students.stanford.edu/~kngk/papers/CaSMoS-AFrameworkForLearningCandidateSelectionModels-KDD2016.pdf) |

**Key Technical Contributions:**
- Machine-learned candidate selection using Weighted AND (WAND) queries
- Constrained feature selection algorithm to learn positive weights for feature combinations
- Deployed on LinkedIn's Galene search platform
- **25% latency reduction** without sacrificing retrieval quality [^13^]

#### 3.3 Dionysius: Hierarchical User Interactions in Recommender Systems
| Field | Details |
|-------|---------|
| **Title** | Dionysius: A Framework for Modeling Hierarchical User Interactions in Recommender Systems |
| **Authors** | Jian Wang, Krishnaram Kenthapadi, Kaushik Rangadurai, David Hardtke |
| **arXiv** | [1706.03849](https://arxiv.org/abs/1706.03849) |
| **Date** | June 2017 |

**Key Technical Contributions:**
- Hierarchical graphical model incorporating implicit user interactions (views > applications)
- Learns hidden fields vector per user, replacing profile-based vector without expanding feature space
- EM-based iterative training; gracefully falls back to profile features for cold users
- Deployed for 18 months in LinkedIn job recommendations; improved VPI and API metrics [^14^]

#### 3.4 LiJAR: Job Application Redistribution
| Field | Details |
|-------|---------|
| **Title** | LiJAR: A System for Job Application Redistribution towards Efficient Career Marketplace |
| **Authors** | Fedor Borisyuk, Liang Zhang, Krishnaram Kenthapadi |
| **Venue** | KDD 2017 (Applied Data Science Track Oral) |
| **URL** | [PDF](http://theory.stanford.edu/~kngk/papers/LiJAR-SystemForJobApplicationRedistribution-KDD2017.pdf) |

**Key Technical Contributions:**
- Dynamic forecasting model to estimate expected job applications at expiration
- Boosting/penalization algorithms to redistribute applications across job postings
- Three-bucket strategy (underserved/moderate/overserved) with 12% entropy improvement
- **+6.5% engagement for underserved jobs** without affecting total applications [^15^]

#### 3.5 Personalized Job Recommendation System at LinkedIn
| Field | Details |
|-------|---------|
| **Title** | Personalized Job Recommendation System at LinkedIn: Practical Challenges and Lessons Learned |
| **Venue** | RecSys 2017 |
| **ACM DL** | [10.1145/3109859.3109921](https://dl.acm.org/doi/10.1145/3109859.3109921) |

**Key Technical Contributions:**
- Two-pass ranking architecture: candidate selection (first-pass) + GLMix ranking (second-pass)
- Decision tree-based query construction for WAND candidate selection
- Application redistribution across job buckets based on application volume
- Multi-tier service-oriented architecture with Galene search backend [^16^]

---

### Category 4: AI-Generated Content Detection

#### 4.1 "AI Solving AI" — LinkedIn's Content Quality System
| Field | Details |
|-------|---------|
| **Source** | Entrepreneur.com interview with Laura Lorenzetti |
| **Date** | May 2026 |
| **URL** | [entrepreneur.com](https://www.entrepreneur.com/business-news/linkedin-is-fighting-back-against-ai-slop-and-ai-comments) |

**Key Technical Contributions:**
- Three-target detection: (1) generic AI-written posts/comments, (2) automation tools for AI content, (3) attention-bait videos
- **Human-in-the-loop**: Editorial teams annotate thousands of posts, labeling generic vs. original content; multiple reviewers per post for consistency
- ML classifiers learn patterns from human-labeled examples to identify content lacking uniqueness/substance
- For AI comments: classifiers examine language patterns and volume/frequency patterns (AI tools comment faster/more often)
- Posts flagged as low-quality are not removed but distribution is suppressed beyond immediate network [^3^]
- Content creation on platform up 14% year over year, correlated with rise of AI tools

---

### Category 5: Infrastructure, Platform & Open Source

#### 5.1 Apache Kafka
| Field | Details |
|-------|---------|
| **Origin** | LinkedIn (2008-2011) |
| **Open Source** | June 2011 (Apache 2.0), ASF Top-Level Project October 2012 |
| **URL** | [kafka.apache.org](https://kafka.apache.org) |

- Created at LinkedIn to aggregate logs and distribute data across internal systems
- Now used by 80%+ of Fortune 100 companies
- Foundation of LinkedIn's real-time data streaming infrastructure [^4^]

#### 5.2 Apache Pinot
| Field | Details |
|-------|---------|
| **Origin** | LinkedIn (2012-2014) |
| **Open Source** | 2014 public, ASF incubation 2018, Top-Level 2021 |
| **URL** | [pinot.apache.org](https://pinot.apache.org) |

- Real-time analytics database for user-facing analytics at scale
- Star-tree index for efficient query processing
- Powers 30+ internal products at LinkedIn including A/B testing (XLNT), Who Viewed My Profile, Talent Insights
- Used for Health Assurance drift statistics, Feed analytics, and anomaly detection [^4^]

#### 5.3 Feathr: LinkedIn's Feature Store
| Field | Details |
|-------|---------|
| **Authors** | David Stein, Jinghui Mo, Hangfei Lin |
| **Open Sourced** | April 2022 |
| **URL** | [feathr.ai](https://feathr.ai) / [GitHub](https://github.com/feathr-ai/feathr) |

- Battle-tested at LinkedIn for 6+ years, serving Search, Feed, and Ads
- Reduced feature engineering time from weeks to days
- 50% faster than custom feature pipelines it replaced
- Key capabilities: point-in-time joins/aggregations, UDF support (PySpark/Spark SQL), embedding support, bloom filters, salted joins for PB-scale data
- Available on Azure with native cloud integration [^5^][^17^]

#### 5.4 Liger Kernel: Efficient Triton Kernels for LLM Training
| Field | Details |
|-------|---------|
| **Authors** | Pin-Lun Hsu, Yun Dai, Vignesh Kothapalli, Qingquan Song, Shao Tang, Siyu Zhu, Steven Shimizu, Shivam Sahni, Haowen Ning, Yanning Chen |
| **Venue** | OpenReview / PyTorch Blog |
| **arXiv** | [2410.10989](https://arxiv.org/pdf/2410.10989) |
| **GitHub** | [linkedin/Liger-Kernel](https://github.com/linkedin/Liger-Kernel) |
| **Date** | 2024-2025 |

- Open-source Triton kernel suite for LLM training optimization
- **60% reduction in GPU memory usage**, **20% throughput improvement**, **3x training time reduction**
- Key techniques: FlashAttention-based memory optimization, operator fusion, input chunking, in-place gradient computation
- HuggingFace-compatible layers: RMSNorm, RoPE, SwiGLU, CrossEntropy, FusedLinearCrossEntropy
- Post-training kernels for alignment/distillation (DPO, ORPO, CPO, SimPO) with 80% memory savings
- Supports PyTorch FSDP, DeepSpeed ZeRO/ZeRO++ [^6^][^18^]

#### 5.5 Pro-ML: LinkedIn's Machine Learning Platform
| Field | Details |
|-------|---------|
| **Initiative** | Productive Machine Learning (Pro-ML) |
| **Launched** | August 2017 |

**Architecture (Six Layers):**
1. **Authoring**: Custom DSL with IntelliJ bindings + Jupyter notebooks
2. **Training**: Hadoop, Spark, Azkaban for distributed offline training
3. **Deployment**: Central model repository with automatic validation
4. **Running**: Quasar execution engine (unified offline/nearline/online execution) + ReMix declarative Java API
5. **Health Assurance**: Automated validation, anomaly detection, dark canary monitoring
6. **Feature Marketplace**: Frame system managing tens of thousands of features [^7^][^19^]

**Health Assurance Details:**
- Monitors hundreds of production AI models for feature drift, data distribution anomalies
- Uses Kafka + Samza for real-time metric aggregation
- Pinot for drift statistics storage; ThirdEye for anomaly alerting
- Metrics Aggregator library solves metric bloat (would otherwise create 25M+ metric keys)
- Three deployment phases: dark canary → experimentation → full production [^20^]

#### 5.6 Galene: LinkedIn's Search Architecture
| Field | Details |
|-------|---------|
| **Origin** | LinkedIn (~2013-2014) |
| **URL** | [Blog post](https://engineering.linkedin.com/search/did-you-mean-galene) |

- Lucene-based search platform with strict Indexer/Searcher node separation
- Indexer nodes consume Kafka streams, build Lucene segments; Searcher nodes serve queries
- Supports precise offline index rebuilding in Hadoop
- Live index tier consuming document update events for real-time freshness
- Rich query language with WAND queries, ML scoring integration [^21^]

#### 5.7 ThirdEye: Anomaly Detection
| Field | Details |
|-------|---------|
| **Origin** | LinkedIn |

- Anomaly detection and root cause analysis platform at LinkedIn
- Monitors experiment metrics, site performance, user adoption
- Supports user-defined rules to complex ML models (regression, spline regression)
- Collects relationships between metrics for intelligent dependency graph walking
- Integrated with Pinot for real-time analytics [^22^]

#### 5.8 Managed Beam: Real-Time ML Feature Engineering
| Field | Details |
|-------|---------|
| **Presentation** | Beam Summit 2023 |
| **URL** | [beamsummit.org](https://beamsummit.org/sessions/2023/power-realtime-machine-learning-feature-engineering-with-managed-beam-at-linkedin/) |

- Cross-language (Java/Python) real-time feature generation pipelines
- Portable across platforms via Apache Beam's portable API
- Auto-sizing and auto-triaging for zero operational cost to ML users
- Powers real-time features for Job Recommendation, Search, Feed, and Ads [^23^]

---

### Category 6: NLP, Content Understanding & Generative AI

#### 6.1 LinkedIn Post Embeddings (Multi-Task Content Understanding)
| Field | Details |
|-------|---------|
| **Title** | LinkedIn Post Embeddings: Industrial Scale Embedding Generation and Usage across LinkedIn |
| **Venue** | CIKM 2025 |
| **arXiv** | [2405.11344](https://arxiv.org/abs/2405.11344) |

**Key Details:**
- Transformer-based LLM fine-tuned with multi-task learning across semantic labeling tasks
- Outperforms OpenAI ADA-001 and ADA-002 on LinkedIn-specific datasets
- Zero-shot learning capability for broader applicability
- Near-line deployment making embeddings available within minutes [^10^]

#### 6.2 LinkedIn Generative AI Application Tech Stack
| Field | Details |
|-------|---------|
| **Title** | The LinkedIn Generative AI Application Tech Stack: Personalization with Cognitive Memory Agent |
| **Source** | LinkedIn Engineering Blog |
| **URL** | [linkedin.com/blog](https://www.linkedin.com/blog/engineering/ai/the-linkedin-generative-ai-application-tech-stack-personalization-with-cognitive-memory-agent) |

**Key Technical Contributions:**
- **Cognitive Memory Agent (CMA)**: Four-layer memory architecture (conversational, episodic, semantic, procedural)
- Ingests activity traces through streaming and batch pipelines
- LLM-based orchestrator retrieves and reasons across all four memory layers
- Powers Hiring Assistant for auto-populating role requirements and generating recruiter-specific insights [^24^]

#### 6.3 Skills Graph & Knowledge Graph
| Field | Details |
|-------|---------|
| **Scale** | 41,000+ skills, 26 languages, 374,000+ aliases, 200,000+ links between skills (2023) |

- Human-in-the-loop curation combining taxonomists + ML
- **KGBert**: LinkedIn-developed tool inspired by KG-BERT for deep semantic skill understanding
- Dynamic skill harvesting with batch review pipeline
- Example: "prompt engineering" dynamically added as new skill [^25^]

---

### Category 7: Trust, Safety & Anti-Abuse

#### 7.1 Detecting Clusters of Fake Accounts
| Field | Details |
|-------|---------|
| **Title** | Detecting Clusters of Fake Accounts in Online Social Networks |
| **Authors** | Cao Xiao (UW + LinkedIn), David Mandell Freeman (LinkedIn), Theodore Hwa (LinkedIn) |
| **URL** | [Stanford PDF](https://theory.stanford.edu/~dfreeman/papers/clustering.pdf) |

- Supervised ML pipeline classifying clusters of accounts (not individual accounts)
- Features: statistics on user-generated text (name, email, company, university)
- Random forest classifier with AUC 0.98 (held-out), AUC 0.95 (out-of-sample)
- **Production impact**: Identified and restricted 250,000+ fake accounts [^26^]

#### 7.2 AI Fairness in Job Matching
| Field | Details |
|-------|---------|
| **Source** | MIT Technology Review, 2021 |
| **URL** | [technologyreview.com](https://www.technologyreview.com/2021/06/23/1026825/linkedin-ai-bias-ziprecruiter-monster-artificial-intelligence/) |

- Discovered recommendation algorithms were ranking candidates partly on likelihood to apply/respond
- System referred more men than women due to behavioral differences (men more aggressive job seekers)
- Built separate AI system to counteract bias, ensuring representative gender distribution in recommendations
- Deployed in 2018 [^27^]

---

### Category 8: Search & Information Retrieval

#### 8.1 Reimagining LinkedIn's Search Tech Stack
| Field | Details |
|-------|---------|
| **Author** | Fedor Borisyuk |
| **Source** | LinkedIn Engineering Blog |
| **URL** | [linkedin.com/blog/engineering/search/reimagining-linkedins-search-stack](https://www.linkedin.com/blog/engineering/search/reimagining-linkedins-search-stack) |

- Scalable LLM-based search stack
- Powers smarter, faster, more personalized search across people, jobs, content [^28^]

#### 8.2 Write-Read Decoupling in Search Engines (Survey including Galene)
| Field | Details |
|-------|---------|
| **Title** | Write-Read Decoupling in Modern Large-Scale Search Engines |
| **arXiv** | [2605.01260](https://arxiv.org/abs/2605.01260) |
| **Date** | 2026 |

- Galene uses strict Indexer/Searcher separation: Indexer nodes consume Kafka, build segments; Searcher nodes serve snapshots
- Eliminates merge overhead from query path completely
- Trade-off: minutes-level propagation latency for stable, low query latency [^21^]

---

## Major Authors & Researchers

| Name | Role/Relevance | Papers/Projects Found |
|------|--------------|----------------------|
| **Fedor Borisyuk** | Staff/Principal Engineer at LinkedIn; core AI researcher | LiGNN (KDD 2024), LiRank (KDD 2024), LiNR (2024), CaSMoS (KDD 2016), LiJAR (KDD 2017), Reimagining Search, GLMix deployment |
| **Krishnaram Kenthapadi** | Former LinkedIn Researcher/Engineer (now Google); established LinkedIn's AI research program | CaSMoS (KDD 2016), Dionysius (2017), LiJAR (KDD 2017), Job RecSys (RecSys 2017) |
| **David Stein** | Senior Staff Software Engineer; led Feathr and multiple ranking systems | CaSMoS, LiGNN, Feathr feature store, LiRank, GLMix, Job RecSys |
| **Laura Lorenzetti** | VP of Product & Executive Editor at LinkedIn | Led "AI solving AI" content detection initiative |
| **Ya Xu** | VP of Engineering, Data & AI at LinkedIn | Led Pro-ML platform initiative |
| **Deepak Agarwal** | Former VP of Engineering/AI at LinkedIn | GLMix (KDD 2016) |
| **Amol Ghoting** | Staff Engineer at LinkedIn | LiGNN, ML infrastructure |
| **Souvik Ghosh** | VP of Engineering at LinkedIn | LiGNN |
| **Shihai He** | Research Engineer at LinkedIn | LiGNN |
| **Siddharth Dangi** | Engineer at LinkedIn | LiGNN, LLM-based retrieval |
| **Birjodh Tiwana** | Staff Engineer at LinkedIn | LiGNN, LLM-based retrieval |

---

## Trends & Signals

- **Shift from feature-engineered models to deep learning + LLMs**: LinkedIn's ranking systems evolved from linear models (GLMix, 2016) through deep neural networks (LiRank, 2024) to LLM-based retrieval (AAAI 2026), representing a clear technological progression [^2^][^8^].

- **Graph Neural Networks as a foundational platform**: LiGNN serves as a unified GNN framework across all major LinkedIn surfaces (Feed, Jobs, People, Ads), demonstrating that GNNs have moved from research to production infrastructure at massive scale [^1^].

- **Real-time infrastructure as competitive advantage**: Kafka (streaming) + Pinot (analytics) + Beam (feature engineering) + Feathr (feature store) form a cohesive real-time ML stack that enables sub-minute feature freshness [^4^][^5^][^23^].

- **Open-source strategy amplifies impact**: LinkedIn's approach of building internally and then open-sourcing (Kafka, Pinot, Feathr, Liger Kernel) has created massive external adoption while also attracting engineering talent [^4^][^5^][^6^].

- **AI content detection is becoming a core platform capability**: The "AI solving AI" initiative reflects the industry's broader challenge of maintaining content quality in an era of generative AI proliferation [^3^].

- **Generative AI integration accelerating**: 2024-2025 saw rapid adoption of LLMs at LinkedIn, from post embeddings (CIKM 2025) to retrieval (AAAI 2026) to agent-based systems (Cognitive Memory Agent) [^8^][^10^][^24^].

- **Responsible AI and fairness are production concerns**: LinkedIn discovered and actively mitigated gender bias in job recommendations as early as 2018, deploying counterfactual AI systems to ensure representative outcomes [^27^].

---

## Controversies & Conflicting Claims

- **A/B testing practices scrutinized**: A New York Times investigation critiqued LinkedIn's experimentation practices, noting the company published academic papers analyzing potentially controversial A/B test results. LinkedIn's experimentation platform runs 400+ parallel experiments daily [^29^].

- **AI bias in hiring recommendations**: MIT Technology Review documented that LinkedIn's job recommendation algorithms inadvertently favored male candidates due to behavioral pattern differences (men apply more aggressively). While LinkedIn built countermeasures, the episode highlights that "blind" algorithms can still encode societal biases [^27^].

- **AI-generated content moderation tension**: LinkedIn must balance supporting AI-assisted content creation (which increased 14% YoY) with suppressing low-quality AI slop. The platform's approach of distribution suppression rather than removal avoids censorship concerns but may still penalize legitimate AI-assisted posts [^3^].

- **Pro-ML's ambitious goals vs. fragmentation reality**: While Pro-ML aimed to double ML engineer effectiveness, the reality of migrating hundreds of bespoke systems to a unified platform involved significant organizational and technical debt. The Health Assurance platform itself was acknowledged as "still in development" despite identifying major production issues [^7^][^20^].

---

## Recommended Deep-Dive Areas

1. **LiGNN architecture and production deployment**: The most comprehensive recent paper on LinkedIn's AI systems; offers detailed insights into scaling GNNs to hundreds of billions of edges across multiple product surfaces. Relevant for anyone building graph-based recommendation systems at scale.

2. **LLM-based retrieval architecture (AAAI 2026 paper)**: Represents a paradigm shift from traditional multi-index retrieval to unified LLM-based dense retrieval. Critical for understanding how LLMs are replacing traditional recommendation infrastructure.

3. **Pro-ML platform and Health Assurance**: Best documented industrial ML platform architecture; Health Assurance's approach to monitoring 1000+ models across 500+ hosts offers practical patterns for production ML observability.

4. **"AI solving AI" content detection system**: While not a published paper, this system represents a novel approach to content quality at scale. A direct engineering inquiry to LinkedIn could yield more technical detail about model architectures and annotation pipelines.

5. **Feathr feature store design**: As one of the earliest production feature stores, Feathr's approach to point-in-time correctness, vocabulary management, and cross-platform portability offers lessons for modern feature platform design.

6. **LinkedIn's open-source GPU optimization (Liger Kernel)**: The 60% memory reduction and 20% throughput improvement claims are significant; the Triton-based approach to operator fusion is directly applicable to any organization training LLMs.

7. **Historical evolution of job recommendation**: The sequence GLMix (2016) → CaSMoS (2016) → Dionysius (2017) → LiJAR (2017) → Personalized Job RecSys (2017) provides a complete picture of how industrial recommendation systems evolve over time, with each paper building on the previous.

---

## Sources

[^1^]: Borisyuk et al., "LiGNN: Graph Neural Networks at LinkedIn," KDD 2024. [arXiv:2402.11139](https://arxiv.org/abs/2402.11139)

[^2^]: Borisyuk et al., "LiRank: Industrial Large Scale Ranking Models at LinkedIn," 2024. [arXiv:2402.06859](https://arxiv.org/abs/2402.06859)

[^3^]: "LinkedIn Is Fighting Back Against AI Slop — and AI Comments," Entrepreneur, May 2026. [URL](https://www.entrepreneur.com/business-news/linkedin-is-fighting-back-against-ai-slop-and-ai-comments)

[^4^]: "Apache Kafka and Apache Pinot – Built together to work together," StarTree. [URL](https://startree.ai/resources/apache-kafka-and-apache-pinot/)

[^5^]: "Feathr: LinkedIn's feature store is now available on Azure," Microsoft/Azure Blog, April 2022. [URL](https://azure.microsoft.com/en-us/blog/feathr-linkedin-s-feature-store-is-now-available-on-azure/)

[^6^]: Hsu et al., "Liger Kernel: Efficient Triton Kernels for LLM Training," 2024. [arXiv:2410.10989](https://arxiv.org/pdf/2410.10989) / [GitHub](https://github.com/linkedin/Liger-Kernel)

[^7^]: "LinkedIn: Pro-ML platform unifying the ML lifecycle," ZenML MLOps Database. [URL](https://www.zenml.io/mlops-database/linkedin-pro-ml-pro-ml-platform-unifying-the-ml-lifecycle-to-scale-ml-engineering-across-fragmented-infrastructure)

[^8^]: Ramanujam et al., "Large Scale Retrieval for the LinkedIn Feed Using Causal Language Models," AAAI 2026. [arXiv:2507.21117](https://arxiv.org/abs/2507.21117)

[^9^]: "Graph Neural Networks for the LinkedIn Economic Graph," Zenodo presentation, April 2022. [URL](https://zenodo.org/records/6501633)

[^10^]: "LinkedIn Post Embeddings: Industrial Scale Embedding Generation and Usage across LinkedIn," CIKM 2025. [arXiv:2405.11344](https://arxiv.org/abs/2405.11344)

[^11^]: "LiNR: Model Based Neural Retrieval on GPUs at LinkedIn," 2024. [arXiv:2407.13218](https://arxiv.org/abs/2407.13218)

[^12^]: Zhang et al., "GLMix: Generalized Linear Mixed Models For Large-Scale Response Prediction," KDD 2016. [ACM DL](https://dl.acm.org/doi/10.1145/2939672.2939684)

[^13^]: Borisyuk et al., "CaSMoS: A Framework for Learning Candidate Selection Models over Structured Queries and Documents," KDD 2016. [PDF](http://www-cs-students.stanford.edu/~kngk/papers/CaSMoS-AFrameworkForLearningCandidateSelectionModels-KDD2016.pdf)

[^14^]: Wang et al., "Dionysius: A Framework for Modeling Hierarchical User Interactions in Recommender Systems," 2017. [arXiv:1706.03849](https://arxiv.org/abs/1706.03849)

[^15^]: Borisyuk et al., "LiJAR: A System for Job Application Redistribution towards Efficient Career Marketplace," KDD 2017. [PDF](http://theory.stanford.edu/~kngk/papers/LiJAR-SystemForJobApplicationRedistribution-KDD2017.pdf)

[^16^]: "Personalized Job Recommendation System at LinkedIn: Practical Challenges and Lessons Learned," RecSys 2017. [ACM DL](https://dl.acm.org/doi/10.1145/3109859.3109921)

[^17^]: "Self-serve feature platforms: architectures and APIs," Huyen Chip blog, January 2023. [URL](https://huyenchip.com/2023/01/08/self-serve-feature-platforms.html)

[^18^]: "Liger-Kernel: Efficient Triton Kernels for LLM Training," OpenReview 2025. [URL](https://openreview.net/forum?id=36SjAIT42G)

[^19^]: "Building, Adopting, and Maturing LinkedIn's Machine Learning Platform," TWIML Podcast, February 2021. [URL](https://twimlai.com/podcast/twimlai/building-adopting-and-maturing-linkedins-machine-learning-platform)

[^20^]: "LinkedIn: Pro-ML Model Health Assurance for monitoring drift and performance," ZenML MLOps Database. [URL](https://www.zenml.io/mlops-database/linkedin-pro-ml-pro-ml-model-health-assurance-for-monitoring-drift-and-performance-across-hundreds-of-production-ai-mode)

[^21^]: Liang et al., "Write-Read Decoupling in Modern Large-Scale Search Engines," 2026. [arXiv:2605.01260](https://arxiv.org/abs/2605.01260)

[^22^]: "ThirdEye" references from Software Engineering Daily podcast and Flexera blog.

[^23^]: "Power Realtime Machine Learning Feature Engineering with Managed Beam at LinkedIn," Beam Summit 2023. [URL](https://beamsummit.org/sessions/2023/power-realtime-machine-learning-feature-engineering-with-managed-beam-at-linkedin/)

[^24^]: "The LinkedIn Generative AI Application Tech Stack: Personalization with Cognitive Memory Agent," LinkedIn Engineering Blog. [URL](https://www.linkedin.com/blog/engineering/ai/the-linkedin-generative-ai-application-tech-stack-personalization-with-cognitive-memory-agent)

[^25^]: "How LinkedIn is moving towards a skills-based economy with the Skills Graph," LinkedIn Data Orchestration blog, December 2023. [URL](https://linkeddataorchestration.com/2023/12/13/how-linkedin-is-moving-towards-a-skills-based-economy-with-the-skills-graph/)

[^26^]: Xiao, Freeman, Hwa, "Detecting Clusters of Fake Accounts in Online Social Networks." [PDF](https://theory.stanford.edu/~dfreeman/papers/clustering.pdf)

[^27^]: "LinkedIn's job-matching AI was biased. The solution? More AI," MIT Technology Review, June 2021. [URL](https://www.technologyreview.com/2021/06/23/1026825/linkedin-ai-bias-ziprecruiter-monster-artificial-intelligence/)

[^28^]: "Reimagining LinkedIn's search tech stack," LinkedIn Engineering Blog. [URL](https://www.linkedin.com/blog/engineering/search/reimagining-linkedins-search-stack)

[^29^]: "[Technically dispatch] what is A/B testing and what did LinkedIn do wrong," Technically.dev, September 2022. [URL](https://read.technically.dev/p/technically-dispatch-what-is-ab-testing)
