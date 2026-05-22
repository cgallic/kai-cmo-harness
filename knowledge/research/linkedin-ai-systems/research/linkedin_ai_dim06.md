# Dimension 6: LinkedIn Job Matching & The Economic Graph — Deep Dive

> **Research Date:** 2025  
> **Searches Conducted:** 20+ independent queries across arXiv, ACM, LinkedIn Engineering, third-party analyses  
> **Key Sources:** LinkSAGE (arXiv:2402.13430), LiJAR (KDD 2017), GLMix (KDD 2016), JUDE (LinkedIn 2024), LiFT (CIKM 2020), Fairness-Aware Ranking (KDD 2019), Learning to Retrieve (KDD 2024), Skills Graph (LinkedIn Engineering)

---

## Table of Contents

1. [LinkSAGE: GNN-Based Job Matching Architecture](#1-linksage-gnn-based-job-matching-architecture)
2. [JUDE (Job Match AI): LLM-Powered Semantic Understanding](#2-jude-job-match-ai-llm-powered-semantic-understanding)
3. [Skills Graph: 41,000+ Skills Architecture](#3-skills-graph-41000-skills-architecture)
4. [GLMix: The Legacy Generalized Linear Mixed Model](#4-glmix-the-legacy-generalized-linear-mixed-model)
5. [LiJAR: Job Application Redistribution](#5-lijar-job-application-redistribution)
6. [Full Job Recommendation Pipeline](#6-full-job-recommendation-pipeline)
7. [Fairness in Job Matching](#7-fairness-in-job-matching)
8. [The Economic Graph Structure](#8-the-economic-graph-structure)

---

## 1. LinkSAGE: GNN-Based Job Matching Architecture

### 1.1 Overview

LinkSAGE is LinkedIn's framework for integrating Graph Neural Networks (GNNs) into large-scale personalized job matching systems. It operates on what LinkedIn describes as "the largest and most intricate job marketplace graph in the industry," featuring **billions of nodes and edges** [^55^]. The paper (arXiv:2402.13430, 2024) was authored by Ping Liu, Haichao Wei, Xiaochen Hou, Jianqiang Shen, Shihai He, Kay Qianqi Shen, Zhujun Chen, Fedor Borisyuk, Daniel Hewlett, Liang Wu, Srikant Veeraraghavan, Alex Tsun, Chengming Jiang, and Wenjing Zhang — all LinkedIn employees [^368^].

### 1.2 Graph Structure

The heterogeneous job marketplace graph contains multiple node types [^55^]:

| Node Type | Description |
|-----------|-------------|
| **Members** (Job Seekers) | 1 billion+ professional profiles |
| **Jobs** | 50 million+ active job postings |
| **Skills** | 41,000+ canonical skill entities |
| **Titles** | Job title entities |
| **Companies** | Employer organizations |
| **Positions** | Specific role instances |

**Edge types** connect members to their attributes (Skill, Title, Company, Position), jobs to their attributes, and members to jobs through engagement signals (save, apply, click) [^55^]. This creates a richly interconnected network where information can propagate across entity types.

### 1.3 Encoder-Decoder GNN Architecture

LinkSAGE uses an **encoder-decoder GNN model** with the following design [^54^]:

- **Encoder**: Processes the heterogeneous graph through graph neural network layers, propagating information across edges to produce rich node embeddings. The encoder captures neighborhood information — a member node receives signal from connected skill nodes, title nodes, company nodes, and job nodes.
- **Decoder**: Reconstructs predictions from the encoded embeddings for downstream tasks.

The GNN is trained with **inductive graph learning**, meaning it can generalize to unseen nodes (new members, new jobs) without retraining [^55^].

### 1.4 Nearline Inference System

A key innovation is the **nearline inference pipeline** for serving GNN embeddings [^55^]:

1. The computationally intensive GNN encoder is **pre-computed** offline/nearline
2. Outputs are stored in an **in-memory feature store** (Venice, LinkedIn's key-value store)
3. Existing Deep Neural Network (DNN) ranking models consume these pre-computed embeddings as features via **transfer learning**
4. This eliminates the need for expensive real-time GNN inference while maintaining up-to-date graph signals

**Latency**: The system achieves latency in the **low tens of milliseconds** — critical for real-time job recommendations at LinkedIn's scale [^55^]. Without nearline inference, the full potential of the GNN would not be realized until the next day's inference task completes — unacceptable given the vast number of jobs posted daily [^55^].

### 1.5 Training Methodology

The training decouples GNN model training from existing DNN model training [^55^]:

- The GNN encoder is trained on the heterogeneous graph structure
- The DNN ranking models continue their normal training cycle
- GNN embeddings are periodically refreshed and fed into the DNN models
- This eliminates the need for frequent GNN retraining while maintaining near real-time graph signals

### 1.6 Key Results from A/B Tests

LinkSAGE was validated across multiple downstream products [^54^]:

| Product | Metrics Improved |
|---------|-----------------|
| **Top Applicant Jobs (TAJ)** | Increased Premium member engagement, improved recruiter interaction metrics, increased subscription renewals |
| **Jobs You May Be Interested In (JYMBII)** | +Qualified Applications (QA), +QA rate, +job session metrics, -Dismiss-to-Apply ratio |
| **Job Search** | +successful search sessions, +Apply-to-Job-View ratio, +application volume, +positive recruiter interactions |

### 1.7 Equity and Cold-Start Benefits

A significant finding: the heterogeneous graph enables **information propagation through edges**, allowing member nodes with less training data to receive significant information from neighboring nodes with more robust data [^55^]. This improved relevance matching across all member segments — from power users to infrequent visitors historically lacking predictive data [^55^]. The system demonstrates potential in **promoting equality and inclusivity** in job recommendations [^55^].

---

## 2. JUDE (Job Match AI): LLM-Powered Semantic Understanding

### 2.1 Overview

JUDE (Job Understanding Data Expert) is LinkedIn's production platform that leverages **fine-tuned Large Language Models (7B parameters)** to generate high-quality embeddings for job recommendations at scale [^419^]. It represents the evolution beyond traditional feature engineering and taxonomy-based approaches. JUDE launched in production in 2024 and powers the **Job Match** feature released in January 2025 [^164^][^399^].

### 2.2 Two-Tower Architecture with Shared LLM

JUDE employs a **bi-encoder (two-tower) architecture** [^398^][^419^]:

- **Job Tower**: Processes job postings through prompt templates like: *"Given this job posting, generate an embedding that catches the role requirements, seniority, and skills needed."*
- **Member/Resume Tower**: Processes member profiles through prompts like: *"Given this member profile, generate an embedding that captures their experience, skills, and career trajectory."*
- Both towers share the **same underlying 7B-parameter LLM** with specialized prompt templates as soft task descriptors
- Similarity is computed via simple vector operations (dot product/cosine similarity) between the embeddings

**Why two-tower instead of cross-encoder?** Cross-encoders are more accurate (full transformer attention between both inputs) but computationally infeasible at LinkedIn's scale with 15M+ active job postings and millions of member profiles [^398^]. The two-tower design reduces inference from billions of LLM calls to one embedding computation per entity.

### 2.3 Cross-Encoder Distillation

To recover accuracy lost from the two-tower approach, LinkedIn uses a **distillation technique** [^398^][^419^]:
1. Train a cross-encoder model offline (where cost doesn't matter)
2. Use its outputs as a teaching signal for the two-tower model
3. This bridges **50% of the performance gap** between the two approaches

### 2.4 Training Details

- **Fine-tuning**: Uses LoRA (Low-Rank Adaptation) with rank=8 applied to Query-Key-Value matrices in Transformer attention blocks [^419^]
- **Model**: 7B parameter decoder-only LLM fine-tuned on LinkedIn's proprietary data
- **Optimization**: Flash Attention 2, bfloat16 mixed precision, gradient checkpointing, gradient accumulation [^419^]
- **Infrastructure**: Multi-node multi-GPU distributed training on NVIDIA H100 cards using DeepSpeed ZeRO Stage 1 [^419^]
- **Max context length**: 1,800 tokens for job descriptions/resumes, 1,024 tokens for member profiles [^418^]

### 2.5 Dual Supervision Signals

The training combines two types of labels [^398^][^419^]:

| Label Type | Description | Purpose |
|------------|-------------|---------|
| **Relevance Labels** | Human-annotated judgments of job-member match quality | Teach semantic precision — what a "correct" match looks like |
| **Engagement Labels** | Real application data from millions of job seekers | Align with actual user behavior and marketplace dynamics |

### 2.6 Loss Function Engineering

Three complementary loss functions are combined [^419^]:
1. **Binary Cross-Entropy (BCE)**: Core classification task
2. **Triplet/InfoNCE Loss**: Contrastive learning for retrieval and semantic search
3. **VP-Matrix Loss**: Robust outlier handling and effective weak convergence

Semi-hard negative mining is used — selecting negatives that are challenging but not the hardest, reducing false negatives [^418^].

### 2.7 Production Impact

Deployment results (A/B tests) [^398^][^419^]:

| Metric | Improvement |
|--------|-------------|
| Qualified Applications | +2.07% |
| Dismiss-to-Apply Ratio | -5.13% |
| Total Job Applications | +1.91% |

LinkedIn described this as **"the greatest metric improvement from a single model change"** observed by the team supporting talent initiatives during that period [^398^]. At LinkedIn's scale (260M+ monthly job searchers), a 2% improvement means millions of additional strong matches annually [^398^].

### 2.8 Kappa Architecture for Real-Time Serving

JUDE uses a **Kappa architecture** (streaming-first) with four subcomponents [^419^]:

1. **Sources**: Kafka/Brooklin streams for job postings, member profiles, resumes
2. **Real-Time Processing**: Samza pipelines for feature extraction, prompt application, change detection, embedding inference
3. **GPU Model Serving**: Kubernetes-deployed LLM serving clusters with GRPC endpoints, latency <300ms at p95
4. **Output Sinks**: Venice (online key-value store) + Kafka→HDFS (offline for training)

**Optimization**: Hashing-based change detection reduces inference volume by **~6x** compared to naive database change tracking [^419^].

### 2.9 JUDE + LinkSAGE Integration

JUDE LLM embeddings are integrated with LinkSAGE GNN as node features. Experiments show that incorporating LLM embeddings into GNN models improves validation AUC from 0.8447 (baseline) to 0.8489 — a meaningful improvement in matching quality [^418^].

### 2.10 Job Match Feature (January 2025)

The consumer-facing **Job Match** tool launched in January 2025 [^164^][^399^]:

- **Free tier**: Qualification breakdown showing required/preferred qualifications met or missing, skill gap highlighting, AI profile improvement suggestions
- **Premium tier**: Categorical match ratings (High/Medium/Low), **"Top Applicant" badge** when ranking in top 50% of applicants for positions with 10+ applicants, curated "Jobs where you're a top applicant" section, competitive insights

---

## 3. Skills Graph: 41,000+ Skills Architecture

### 3.1 Overview

LinkedIn's Skills Graph is the foundational knowledge structure that connects **41,000+ canonical skills** across 26 languages, with 374,000+ aliases and 200,000+ links between skills [^19^][^364^]. It serves as the backbone for member-job matching, learning recommendations, skills-first hiring, and feed personalization.

### 3.2 From Taxonomy to Ontology

The Skills Graph evolved from a simple hierarchical taxonomy to a richer ontology [^19^][^32^]:

- **Taxonomy phase**: Skills organized in a tree hierarchy with parent-child relationships ("knowledge lineages")
- **Ontology phase**: Richer relational structure connecting skills not just hierarchically but also to other concepts (jobs, companies, industries, learning content) [^32^]

As noted by former LinkedIn AI Technical Lead Mike Dillinger, taxonomies are "the duct tape of connected data" — limited to hierarchical relationships which are only a small part of real-world connections [^32^]. The ontology approach has provided "great improvements when it comes to ranking and recommendation" [^32^].

### 3.3 Skill Extraction Pipeline Architecture

The multi-stage extraction pipeline [^364^][^21^]:

#### Stage 1: Skill Segmentation
- Raw text (job descriptions, resumes, profiles) is parsed into meaningful sections
- For job postings: identifies "responsibilities," "qualifications," "benefits" sections
- Location of skill mentions provides signal about relevance

#### Stage 2: Skill Tagging (Hybrid Approach)
LinkedIn uses a **dual approach** combining speed and semantic understanding [^364^]:

| Method | Technology | Strength | Limitation |
|--------|-----------|----------|------------|
| **Trie-Based Token Matching** | Skill names encoded in trie structure, token lookups | Exceptional speed and scalability | Depends on taxonomy completeness |
| **Semantic Two-Tower Model** | Multilingual BERT as text encoder, contextual embeddings for text and skill names | Infers skills from context (e.g., "experience with design of iOS application" → "Mobile Development") | Higher compute cost |

#### Stage 3: Skill Expansion
- Uses the Skills Graph structure to expand tagged skills
- Queries for: related skills in same skill group, parent skills, children skills, sibling skills
- Increases coverage and relevance of skill matches [^364^]

#### Stage 4: Multitask Cross-Domain Skill Scoring
- **Shared Module**: Contextual Text Encoder (Transformer) + Contextual Entity Encoder (pre-calculated embeddings for skills, titles, industries, geographies)
- **Domain-Specific Modules**: Separate towers for each vertical (job postings, member profiles, learning courses, feed posts) [^364^]

### 3.4 KGBert for Relationship Prediction

LinkedIn developed **KGBert** (inspired by KG-BERT) — a supervised model that applies deep semantic understanding to predict skill relationship lineages at scale, helping automate taxonomy construction that would be impossible with human taxonomists alone [^19^].

### 3.5 Human-in-the-Loop Growth

The Skills Graph is curated through a **feedback loop** between machine learning and human taxonomists [^19^]:

1. ML models detect new skills and new ways of mentioning existing skills
2. Potential additions are batched for human review
3. Approved skills are dynamically added to the graph
4. New skills subsequently become available for tagging across content

Example: "Prompt Engineering" emerged as a new skill and was rapidly added to the Skills Graph as it gained prominence [^19^].

### 3.6 Skill Assessments and Validation

LinkedIn Skill Assessments (SAs) provide **validated skill signals** — adaptive assessments that evaluate member proficiency [^19^]. Members scoring 70th percentile or higher receive a "verified skill" badge. These assessments help assess skill depth beyond self-reported profile claims.

---

## 4. GLMix: The Legacy Generalized Linear Mixed Model

### 4.1 Overview

GLMix (Generalized Linear Mixed Models for Large-Scale Response Prediction) was presented at **KDD 2016** by Xianping Zhang, Yitong Zhou, Yiming Ma, Bei-Chen Chen, Liang Zhang, and Deepak Agarwal — all LinkedIn researchers [^366^]. It was deployed in LinkedIn's job recommender system and generated **20% to 40% more job applications** for job seekers [^366^].

### 4.2 Model Architecture

GLMix extends logistic regression with ID-level coefficients [^367^]:

```
g(E[y_mj]) = x_mj · β + s_j · α_m + q_m · β_j
```

Where:
- `x_mj · β`: Global features (interactions between member features and job features)
- `s_j · α_m`: Per-member model component (member-specific preferences to job features)
- `q_m · β_j`: Per-job model component (what types of members like to apply for a given job)

**Features used**:
- Member side: title, industry, work history, skills, education, location
- Job side: title, company, qualifications, desired skills, experience requirements [^363^]

### 4.3 Scalability Solution

The key challenge was fitting a model with a massive number of ID-level coefficients. LinkedIn solved this through **parallelized block coordinate descent** under the Bulk Synchronous Parallel (BSP) paradigm [^366^], making it feasible to train at LinkedIn's scale.

### 4.4 Why It Was Replaced

GLMix was a foundational system but had limitations that led to its replacement by more modern architectures:

| Limitation | Modern Replacement |
|------------|-------------------|
| Relied on handcrafted feature engineering | JUDE LLM embeddings capture semantic meaning automatically |
| Required manual query model construction | Embedding-Based Retrieval (EBR) with learned representations |
| Static model without deep semantic understanding | LinkSAGE GNN captures graph structure and propagation |
| Limited ability to understand emerging roles/skill | LLMs understand new roles from text without taxonomy updates |
| No direct fairness considerations | LiFT + fairness-aware re-ranking integrated into pipeline |

GLMix was replaced in stages — first by more sophisticated neural ranking models (LiRank), then augmented with GNN embeddings (LinkSAGE), and now with LLM embeddings (JUDE) [^11^][^363^].

---

## 5. LiJAR: Job Application Redistribution

### 5.1 Overview

LiJAR (LinkedIn Job Applications Forecasting and Redistribution) was presented at **KDD 2017** by Fedor Borisyuk, Liang Zhang, and Krishnaram Kenthapadi [^363^][^365^]. It addresses a critical two-sided marketplace problem: some job postings receive too many applications while others receive too few.

### 5.2 The Problem

In LinkedIn's job marketplace [^363^]:
- Popular jobs (famous companies, generic roles) can receive 100+ applications
- Niche or less visible jobs may receive fewer than 8 applications
- **Both cases cause dissatisfaction**: too many applications → overwhelmed recruiters; too few → unfilled positions and lost contracts
- If too many seekers compete for the same job, each seeker's chance of getting hired is reduced

### 5.3 Dynamic Forecasting Model

LiJAR uses a **statistical forecasting model** to estimate the expected number of applications a job will receive by its expiration date [^363^]:

1. Tracks real-time job statistics (#impressions, #applications so far)
2. Uses job features (title, company, industry, location) to predict final application count
3. Provides **confidence intervals** (not just point estimates) for the prediction
4. Accounts for the exponential decay of impressions/applications over time after posting

The model achieves **~90% recall for boosting strategy** with only **~3% false positive rate** at 95% confidence intervals [^363^].

### 5.4 Boosting and Penalization Algorithm

Based on the confidence interval `[l_t, u_t]` at time t:

| Condition | Action | Formula |
|-----------|--------|---------|
| `u_t < minApps` (8) | **Boost** the job's score | Multiply score by boost factor (e.g., 1.05) |
| `l_t > maxApps` (100) | **Penalize** the job's score | `newScore = originalScore × e^(-applications/softness)` |
| Otherwise | No intervention | Pass through unchanged |

The penalization uses exponential decay — the incremental value of each additional application decreases exponentially, reflecting diminishing returns [^363^].

### 5.5 Architecture and Production Deployment

LiJAR is integrated into the job recommendation pipeline [^363^]:

1. Job recommendation request arrives
2. CaSMoS candidate selection generates the query
3. GLMix ranking model scores candidates
4. **LiJAR module** queries the forecasting model for application predictions
5. Boost/penalize scores based on forecast
6. Final ranked list returned to user

**Offline workflow**: Daily retraining on Hadoop, model parameters pushed to Voldemort key-value store for online access [^363^].

### 5.6 Results

Online A/B testing (Sep-Dec 2016) [^363^]:

| Metric | Result |
|--------|--------|
| Engagement on underserved jobs | **+6.5%** |
| Total job applications | Flat (no decline) |
| Entropy of application distribution | **+12%** (more even distribution) |

The system successfully redistributes applications from over-served jobs (Bucket 3) to under-served jobs (Bucket 1) while maintaining the same total number of applications [^363^].

---

## 6. Full Job Recommendation Pipeline

### 6.1 Multi-Stage Architecture (L0 → L1 → L2 → L3)

LinkedIn's job recommendation follows a **4-stage funnel** [^18^]:

```
50M jobs → L0 Retrieval (~5,000) → L1 Calibration (~500) → L2 Deep Ranking (~20) → L3 Re-Ranking (final)
```

### 6.2 Stage 0: Retrieval (Candidate Generation)

**Goal**: From 50M job postings, find ~5,000 candidates worth considering in under 100ms [^18^].

**Technologies**:
- **Two-Tower Model + ANN**: User tower generates member embedding in real-time; ANN search (HNSW/FAISS) against pre-computed job embedding index
- **Embedding-Based Retrieval (EBR)**: Wide & deep two-tower DNN with text encoder (BERT/T5) + entity features [^52^]
- **Term-Based Retrieval (TBR)**: Traditional inverted index with CaSMoS learned WAND queries [^434^]
- **Graph-Based Retrieval**: LinkSAGE GNN embeddings for graph-based candidate generation
- **Hybrid TBR + EBR**: On-GPU solution supporting both kNN and term matching efficiently [^52^]

**Curriculum Learning for EBR** [^52^]:
- Stage 1: Train with easy negatives (in-batch + random) for coarse ranking
- Stage 2: Fine-tune with top-1024 hardest negatives for refined decision boundary
- Adding 40-60% easy negatives gives decent recall improvement; curriculum learning further improves EBR performance

### 6.3 Stage 1: L1 Calibration Ranking

**Goal**: Calibrate 5,000 candidates from diverse sources into a single comparable list, cut to ~500 [^18^].

- **Lightweight model**: Logistic Regression or LightGBM/XGBoost
- **Why lightweight**: Must score 5,000 items in ~10-20ms
- **Input signals**: Source signal (which scout found this?), raw match scores, real-time context (device, time), frequency capping
- **Output**: Calibrated probability score (0-1) across all candidates

### 6.4 Stage 2: L2 Deep Ranking (LiRank)

**Goal**: From 500 candidates, predict which 20 the member is most likely to engage with [^18^].

LinkedIn's **LiRank** is a large-scale Multi-Task Learning (MTL) framework:

| Component | Description |
|-----------|-------------|
| **Click Tower** | Predicts probability of click and long dwell |
| **Apply Tower** | Predicts probability of job application |
| **Contribution Tower** | Predicts social actions (comments, likes, shares) |
| **Utility Function** | Combines: Score = w₁·Click + w₂·Like + w₃·Comment + w₄·Apply |

**Key technical features** [^18^]:
- **Residual DCN with Attention**: For complex feature interactions
- **TransAct (Transformer-Encoder)**: Models recent user actions (last 5-10) for real-time personalization
- **Isotonic Calibration Layer**: Co-trained to ensure predicted probabilities are accurate
- **JUDE LLM embeddings**: Semantic text embeddings for jobs and profiles
- **LinkSAGE GNN embeddings**: Graph-based node embeddings as features

### 6.5 Stage 3: L3 Re-Ranking (Business Rules & Fairness)

**Goal**: Apply business rules, diversity, freshness, and fairness that the model can't encode [^18^].

| Rule Type | Example | Purpose |
|-----------|---------|---------|
| **Diversity** | Don't show 20 jobs from the same company | Variety improves experience |
| **Freshness** | Boost jobs posted in last 48 hours | Trust and relevance |
| **Fairness** | Ensure representative gender distribution | Legal compliance + values |
| **Business** | Promote LinkedIn hiring partners | Revenue |
| **Deduplication** | Remove already-applied jobs | User experience |
| **LiJAR** | Boost under-served jobs, penalize over-served ones | Marketplace balance |

**Formula**: `FinalScore = L2Score × DiversityPenalty × BusinessBoost × FairnessAdjustment`

### 6.6 Two Pipelines: Organic vs. Promoted

LinkedIn maintains **separate flows** [^52^]:

| Aspect | Organic Pipeline | Promoted Pipeline |
|--------|-----------------|-------------------|
| **Objective** | Maximize seeker engagement | Deliver value to recruiter customers |
| **Retrieval** | Embedding-based + personalization | Qualification-based targeting |
| **Ranking** | Engagement prediction (pCTR, pApply) | Auction-based with quality constraints |
| **Key Metric** | Qualified applications, session quality | Quality of applicants, recruiter satisfaction |
| **Revenue Model** | Free | Pay-per-click from job posters |

Both flows are merged through a **blending model** that balances business objectives before presenting results to the job seeker [^52^].

---

## 7. Fairness in Job Matching

### 7.1 The Bias Discovery

LinkedIn discovered that its recommendation algorithms were producing **biased results** [^233^]:

- The algorithm was ranking candidates partly based on how likely they were to apply or respond to recruiters
- Men tend to be more aggressive at seeking out new opportunities (apply to stretch roles, list more skills, engage more with recruiters)
- The system wound up referring **more men than women** for open roles
- Even though gender was explicitly excluded from features, **behavioral patterns served as proxies** for gender [^233^]

**Example**: Men are more likely to apply for jobs requiring experience beyond their qualifications; women tend to only apply when qualifications match. The algorithm interpreted this behavioral difference and adjusted recommendations, inadvertently disadvantaging women [^233^].

### 7.2 Fairness-Aware Re-Ranking (KDD 2019)

LinkedIn's groundbreaking paper at **KDD 2019** by Sahin Geyik, Stuart Ambler, and Krishnaram Kenthapadi presented the first large-scale deployed framework for ensuring fairness in hiring [^421^][^423^]:

**Framework**:
1. Proposes **complementary measures** to quantify bias with respect to protected attributes (gender, age)
2. Presents **algorithms for fairness-aware re-ranking** of results
3. Seeks to achieve a **desired distribution** of top-ranked results with respect to protected attributes
4. Can be tailored to achieve fairness criteria: **equality of opportunity** and **demographic parity**

**Results**: Nearly **3-fold increase** in the number of search queries with representative results, **without affecting business metrics** — deployed to **100% of LinkedIn Recruiter users worldwide** [^421^].

### 7.3 LiFT: LinkedIn Fairness Toolkit (CIKM 2020)

LiFT is a **Scala/Spark open-source library** for measuring fairness in large-scale ML workflows [^196^][^435^]:

**Capabilities** [^201^]:
1. Measuring biases in training data
2. Evaluating fairness metrics for trained models (AUC, precision, recall, FPR across subgroups)
3. Detecting statistically significant differences in model performance across subgroups
4. Post-processing mitigation to achieve **equality of opportunity** for rankings

**Integration points** [^196^]:
- Before training: Bias measurement on training datasets
- During training: Model selection based on fairness metrics
- After training: Fairness evaluation on test datasets
- Online serving: Ongoing fairness monitoring during A/B tests

**Key insight**: "Focusing on a few fairness metrics and protected attributes greatly simplifies the effort needed to measure and mitigate bias" [^196^].

### 7.4 Fairness in Practice: How It Works

LinkedIn's fairness approach is a **secondary AI system** [^233^][^399^]:
1. Primary model generates ranked list of candidates with relevance scores
2. Fairness module monitors **demographic distribution** across recommendations
3. Reorders candidates to ensure **representative distribution** across gender
4. This is **post-processing** — improving exposure fairness without modifying the primary model

**Limitations**: The approach doesn't address upstream issues like structural inequalities in profile data or differences in platform behavior across groups [^399^].

### 7.5 Fairness Research Extensions

Recent research has extended LinkedIn's work [^420^][^424^]:
- **Fair resource allocation**: Re-ranking under quantity constraints to ensure female users receive similar salary-range job recommendations as male users
- **Personalized counterfactual fairness**: Ensuring recommendations would be the same if a user's protected attributes were different
- **Adversarial debiasing**: Fine-tuning LLMs to learn job-candidate similarity while removing gender information from embeddings
- **Regularization-based approaches**: Adding fairness terms to the loss function (e.g., Sinkhorn Divergence)

---

## 8. The Economic Graph Structure

### 8.1 Overview

LinkedIn's **Economic Graph** is a digital mapping of the global economy, described as "the digital home of the global workforce" [^425^]. It represents the interconnected network of professional entities that powers LinkedIn's matching capabilities.

### 8.2 Core Entities

The Economic Graph connects six primary entity types [^425^]:

| Entity | Scale | Description |
|--------|-------|-------------|
| **Workers/Members** | 1 billion+ | Professional profiles worldwide |
| **Companies** | 60-70 million | Employers and organizations |
| **Jobs** | 50 million+ | Active job postings |
| **Skills** | 41,000+ | Required competencies |
| **Schools/Education** | Thousands | Higher education institutions and courses |
| **Knowledge Content** | Millions | Published professional content |

### 8.3 How the Economic Graph Powers Job Matching

The Economic Graph enables LinkedIn's AI systems to understand **relationships between entities** that simple keyword matching would miss [^399^]:

- **Skill-to-Job mapping**: Which skills are required for which jobs
- **Skill-to-Skill relationships**: Parent/child/related skills (e.g., "Python" → "Machine Learning" → "Data Science")
- **Company-to-School pipelines**: Where companies tend to hire from
- **Career trajectory patterns**: Typical progression paths between titles and companies
- **Geographic skill distribution**: Where specific skills are concentrated

### 8.4 Skills-First Economy Vision

LinkedIn is transitioning toward a **skills-first hiring** model [^19^][^32^]:

- Traditional hiring filters by degree, years of experience, previous employers
- Skills-first evaluates candidates based on demonstrated competencies
- The Skills Graph enables this by providing a common language for skills across:
  - Job postings (required skills)
  - Member profiles (claimed skills + endorsements)
  - Learning courses (skills taught)
  - Feed content (skills mentioned)

### 8.5 Applications Beyond Job Matching

The Economic Graph data enables LinkedIn to [^425^]:

- **Advise governments** on talent migration patterns to inform work visa policies
- **Advise educational institutions** on what courses to offer based on employer demand
- **Advise companies** on optimal locations for new offices based on talent availability
- **Enable salary insights** through aggregate compensation data
- **Power Training Finder**: Matching workers to upskilling programs based on skill gaps

### 8.6 LinkedIn Search Infrastructure (Galene)

The Economic Graph is indexed and served through **Galene**, LinkedIn's search architecture built on Apache Lucene [^20^][^25^]:

- **Inverted Index**: Maps search terms to entities
- **Forward Index**: Maps entities to metadata
- **Distributed Architecture**: Partitioned and replicated across searcher nodes
- **Real-Time Updates**: Zoie library for real-time index updates
- **Personalization**: Search results personalized based on connection degree and profile matching

The search broker applies candidate selection models to construct queries, executes against distributed partitions, and merges results [^434^].

---

## Summary: Evolution of LinkedIn Job Matching

| Era | System | Technology | Key Innovation |
|-----|--------|-----------|----------------|
| **2014-2016** | GLMix | Generalized Linear Mixed Models | Per-member + per-job coefficients; 20-40% application lift |
| **2016** | CaSMoS | Decision Tree + WAND Queries | Learned candidate selection; 25% latency reduction |
| **2017** | LiJAR | Statistical Forecasting + Boosting | Application redistribution; +6.5% underserved job engagement |
| **2017** | Personalized Job RecSys | Search + GLMix + LiJAR integration | End-to-end multi-objective pipeline |
| **2019** | Fairness-Aware Ranking | Post-processing re-ranking | Representative results across gender; 3x fairness improvement |
| **2020** | LiFT | Spark-based Fairness Toolkit | Open-source fairness measurement and mitigation |
| **2023-2024** | LinkSAGE | Graph Neural Networks | GNN on heterogeneous graph with nearline inference; improved equity |
| **2024** | JUDE | LLM-based Embeddings (7B params) | Semantic understanding replacing handcrafted features; +2.07% qualified apps |
| **2024-2025** | JUDE + LinkSAGE | LLM + GNN Integration | Combined LLM node features with GNN propagation; AUC 0.8447→0.8489 |

---

## Key Architectural Principles

1. **Decoupling for Scale**: GNN training decoupled from DNN training; LLM inference decoupled from ranking; nearline inference for expensive computations
2. **Multi-Objective Optimization**: Not just clicks — applications, quality, fairness, marketplace balance simultaneously
3. **Two-Sided Marketplace Design**: Optimizing for both job seekers (relevance) and job posters (qualified applications)
4. **Semantic over Syntactic**: Evolution from keyword matching (GLMix) → embeddings (EBR) → semantic understanding (JUDE LLMs)
5. **Graph-Aware**: Using the Economic Graph's structure for information propagation and cold-start mitigation
6. **Fairness by Design**: Integrated fairness measurement (LiFT) and fairness-aware re-ranking throughout the pipeline

---

## References

[^18^] AI PM Insider, "LinkedIn's Job Recommendation System — AI System Design Teardown," 2026.  
[^19^] Linked Data Orchestration, "How LinkedIn is moving towards a skills-based economy with the Skills Graph," 2023.  
[^20^] Lucidworks, "LinkedIn's Galene Search Architecture Built on Apache Lucene."  
[^21^] ZenML, "LinkedIn: Building and Deploying Large Language Models for Skills Extraction at Scale."  
[^52^] J. Shen et al., "Learning to Retrieve for Job Matching," KDD 2024, arXiv:2402.13435.  
[^53^] P. Liu et al., "Optimizing Job Matching Using Graph Neural Networks," arXiv:2402.13430, 2024.  
[^54^] Moonlight, "Optimizing Job Matching Using Graph Neural Networks — Review."  
[^55^] arXiv, "Optimizing Job Matching Using Graph Neural Networks (LinkSAGE)."  
[^108^] F. Borisyuk et al., "CaSMoS: A Framework for Learning Candidate Selection Models," KDD 2016.  
[^164^] The Interview Guys, "LinkedIn's New AI Job Match Tool," 2025.  
[^196^] S. Vasudevan et al., "LiFT: A Scalable Framework for Measuring Fairness in ML Applications," CIKM 2020.  
[^201^] GitHub, "linkedin/LiFT: The LinkedIn Fairness Toolkit."  
[^233^] MIT Technology Review, "LinkedIn's job-matching AI was biased. The company's solution? More AI," 2021.  
[^363^] F. Borisyuk et al., "LiJAR: A System for Job Application Redistribution," KDD 2017.  
[^364^] ZenML, "LinkedIn: Building and Deploying Large Language Models for Skills Extraction at Scale."  
[^366^] X. Zhang et al., "GLMix: Generalized Linear Mixed Models For Large-Scale Response Prediction," KDD 2016.  
[^367^] X. Zhang et al., "GLMix: Generalized Linear Mixed Models For Large-Scale Response Prediction," KDD 2016 paper PDF.  
[^368^] arXiv, "Optimizing Job Matching Using Graph Neural Networks (LinkSAGE abstract)."  
[^391^] VentureBeat, "LinkedIn open-sources toolkit to measure AI model fairness," 2020.  
[^398^] JustAnotherPM, "Here's How an LLM Fixed Broken LinkedIn's Job Recommendation System," 2026.  
[^399^] BrainForge AI, "How LinkedIn Uses AI to Match You With Jobs," 2025.  
[^402^] HeroHunt AI, "LinkedIn Recruiter 2025: New AI Features," 2025.  
[^418^] arXiv, "A Scalable and Efficient Signal Integration System for Job Matching," 2025.  
[^419^] ZenML, "JUDE: Large-Scale LLM-Based Embedding Generation for Job Recommendations."  
[^420^] Pike et al., "Fairness in AI-Driven Recruitment," 2025.  
[^421^] KDD 2019, "Fairness-Aware Ranking in Search & Recommendation Systems with Application to LinkedIn Talent Search."  
[^423^] arXiv, "Fairness-Aware Ranking in Search & Recommendation Systems with Application to LinkedIn Talent Search," 2019.  
[^424^] PMC, "Fairness of recommender systems in the recruitment domain."  
[^425^] Harvard D3, "LinkedIn's Economic Graph – The Digital Home of the Global Workforce," 2016.  
[^434^] F. Borisyuk et al., "CaSMoS: A Framework for Learning Candidate Selection Models," KDD 2016.  
[^435^] arXiv, "LiFT: A Scalable Framework for Measuring Fairness in ML Applications," 2020.
