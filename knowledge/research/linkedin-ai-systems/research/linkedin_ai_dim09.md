# Dimension 9: Open Source & ML Infrastructure — Deep Dive Research

**Research Date:** 2025  
**Researcher:** AI Research Agent  
**Sources:** LinkedIn Engineering Blog, Apache Foundation, arXiv, ACM/IEEE venues, conference proceedings, GitHub, technical blogs  
**Searches Conducted:** 25+ independent queries across web, academic, and code repositories

---

## Table of Contents

1. [Apache Kafka: Origins at LinkedIn & ML Pipeline Backbone](#1-apache-kafka)
2. [Apache Pinot: Real-Time Analytics for ML Monitoring & Feature Serving](#2-apache-pinot)
3. [Feathr: Feature Store Architecture & Point-in-Time Correctness](#3-feathr)
4. [Liger Kernel: Triton Kernels for GPU LLM Training](#4-liger-kernel)
5. [Pro-ML: Full ML Lifecycle Platform & Health Assurance](#5-pro-ml)
6. [Galene: Search Architecture & Write-Read Decoupling](#6-galene)
7. [ThirdEye: Anomaly Detection for ML Model Monitoring](#7-thirdeye)
8. [Managed Beam: Real-Time Feature Engineering Pipelines](#8-managed-beam)
9. [Infrastructure for AI at Scale: Serving 1B+ Users](#9-ai-infrastructure-scale)
10. [Open Source Strategy: Why LinkedIn Open-Sources](#10-open-source-strategy)
11. [Additional Open Source Projects](#11-additional-projects)
12. [Summary & Key Metrics](#12-summary)

---

## 1. Apache Kafka: Origins at LinkedIn & ML Pipeline Backbone

### Origins and Creation

Apache Kafka was created at LinkedIn in **2010** by engineers **Jay Kreps, Neha Narkhede, and Jun Rao** to solve a fundamental data infrastructure problem: moving large volumes of event data reliably between internal systems [^118^][^120^]. At the time, LinkedIn was experiencing tremendous growth in digitized information, and existing infrastructure — databases designed for data at rest and traditional messaging systems not built for scale — could not handle the demands [^120^].

> "LinkedIn designed Kafka with the purpose of addressing persistent data challenges. Around that time, LinkedIn witnessed a tremendous growth in the volume of digitised information it accumulated... We needed a system capable of accommodating a 1,000x growth in digitised information." — **Jun Rao, Co-founder of Confluent** [^120^]

Kafka was **open-sourced in June 2011** and donated to the Apache Software Foundation, where it became one of the most successful Apache projects [^118^].

### Scale at LinkedIn

LinkedIn operates one of the largest Kafka deployments in the world [^118^]:

| Metric | Value |
|--------|-------|
| Messages per day | **7 trillion+** |
| Kafka clusters | **100+** |
| Brokers | **4,000+** |
| Partitions | **7 million+** |
| Topics | **100,000+** |
| Peak throughput | **4.5 million messages/second** |

**LinkedIn Kafka Timeline** [^118^]:
- **2010**: Kafka developed internally at LinkedIn
- **June 2011**: Open-sourced; processing 1 billion messages/day by July
- **2012**: 20 billion messages/day
- **2013**: 200 billion messages/day; Apache Samza open-sourced
- **2015**: 1 trillion messages/day; Burrow open-sourced
- **2016**: ~1.4 trillion messages/day; 1,400+ brokers; 2+ PB/week
- **2017**: Kafka Cruise Control open-sourced
- **2018**: Migrated to Brooklin for cross-cluster replication
- **2019**: 7 trillion messages/day; Brooklin and Cruise Control Frontend open-sourced
- **2023**: Apache Beam adopted to unify batch and streaming pipelines

### How Kafka Powers the ML Pipeline

Kafka serves as the **central data transport layer** across LinkedIn, connecting virtually every system [^118^]:

1. **Activity Tracking** (Kafka's original use case): Captures member activity events — pageviews, search queries, ad impressions — and delivers them to both offline batch analytics (Hadoop) and real-time online services [^118^].

2. **Real-Time Search Indexing**: Delivers network-update events to LinkedIn's search engine (Galene), making updates searchable within seconds [^118^].

3. **Stream Processing with Samza**: Apache Samza consumes from and produces to Kafka for all real-time processing jobs. Samza uses log-compacted Kafka topics as durable state backup stores [^118^].

4. **ML Feature Generation**: Streaming Apache Beam pipelines read from Kafka to generate real-time ML features, eliminating the 24-48 hour delay that existed with offline pipelines [^30^].

5. **Database Replication (CDC)**: Kafka powers change data capture for Espresso (LinkedIn's internal NoSQL store), replacing MySQL replication with a Kafka-backed pipeline requiring no-data-loss guarantees [^118^].

6. **Derived Data to Venice**: Kafka asynchronously uploads data into Venice, LinkedIn's derived-data serving store, decoupling the write path from downstream consumers [^118^].

7. **Anti-Abuse AI Modeling**: The Anti-Abuse platform (Chronos) reads user activity events from Kafka, aggregates them, and triggers AI scoring models — reducing abuse labeling from 1 day to 5 minutes [^30^].

> "With Kafka serving as the central hub for integrating digitised information from various sources in real time, it became the foundation for feeding downstream use cases... We essentially provided an opportunity for every developer at LinkedIn to actively respond to real-time business events." — **Jun Rao** [^120^]

---

## 2. Apache Pinot: Real-Time Analytics for ML Monitoring & Feature Serving

### Origins and Purpose

Apache Pinot was **originally developed at LinkedIn in 2014** to power user-facing real-time analytics applications. The first use case was the iconic **"Who Viewed My Profile"** feature, which required instantaneous access to fresh data rather than batch-processed data that was hours or days old [^157^].

> "The story of Pinot at LinkedIn is the story of the realization that we needed something more than faster horses. Yes, we were solving issues of speed of data ingestion and query response latencies but this was at an unprecedented scale." — **Kishore Gopalakrishna, Pinot founding engineer** [^157^]

The success of "Who Viewed My Profile" was transformative — engagement shot up to unprecedented levels, but the existing infrastructure (Kafka for ingestion, Hadoop for storage, Sensei/Bobo for querying) could not handle the query load. The team went from hundreds to over a thousand queries per second, requiring cluster expansions of hundreds of nodes just to maintain SLAs [^157^].

### Scale at LinkedIn

| Metric | Value |
|--------|-------|
| User-facing applications | **50-80+** |
| Queries per second | **250,000+** |
| Query latency SLA | **Milliseconds to sub-second** |
| Business metrics stored | **~10,000** |
| Dimensions tracked | **~50,000+** |

> "Apache Pinot powers over 50 user-facing applications at LinkedIn, serving 250,000+ queries per second with millisecond latency across hundreds of billions of records." — **LinkedIn Engineering** [^146^]

Key applications powered by Pinot at LinkedIn [^107^][^145^][^157^]:
- "Who Viewed My Profile"
- Talent Insights
- Ad Analytics
- Publisher Analytics
- Feed Analytics
- Employee Analytics
- Internal dashboards
- ThirdEye anomaly detection and root cause analysis
- Real-time ML feature serving for feed personalization

### Pinot for ML: Feature Serving & Monitoring

LinkedIn uses Pinot to **compute near-real-time features for feed personalization**, retrieving member actions with attributes in **under 50ms at 20,000+ queries/sec** [^99^]. Pinot serves as the real-time analytics layer for:

- **Personalization & Recommendations**: Millisecond-latency lookups for real-time personalization with support for complex joins between user and behavioral data [^99^]
- **ML Model Monitoring**: Stores feature drift statistics computed by the Health Assurance platform, forwarding them to ThirdEye for alerting [^128^]
- **Automated Observability**: Powers time-series query engines for automated anomaly detection with 100K+ concurrent alert evaluations [^99^]

### Technical Architecture

Pinot is a **distributed OLAP datastore** with these key characteristics [^146^]:
- **Columnar storage** with smart indexing and pre-aggregation techniques
- **Real-time streaming ingestion** from Kafka, Pulsar, Kinesis
- **Batch ingestion** from Hadoop, Spark, S3
- **Sub-second queries** on petabyte-scale datasets
- **Horizontal scalability** and fault tolerance
- **SQL query interface** via built-in editor and REST API
- **Built-in upserts** (production-tested since v0.6)

The transformation from pre-Pinot to Pinot infrastructure was dramatic: "Who Viewed My Profile" went from requiring **thousands of nodes** to just **75 nodes**, while serving close to **5,000 queries per second** with latencies of **84-136 milliseconds** — with no cache involved [^157^].

---

## 3. Feathr: Feature Store Architecture & Point-in-Time Correctness

### Overview

**Feathr** is LinkedIn's open-source enterprise-grade feature store, widely used in production for over 6 years before being open-sourced in **April 2022**. It joined the **LF AI & Data Foundation** in September 2022 [^127^][^130^][^133^].

> "Feathr is the feature store that has been used in production and battle-tested in LinkedIn for over 6 years, serving all the LinkedIn machine learning feature platform with thousands of features in production." — **LinkedIn & Azure announcement** [^130^]

### Core Problem Solved

Before Feathr, each LinkedIn team maintained **bespoke feature pipelines** that were difficult to scale, prone to training-serving skew, and prevented feature reuse across projects [^104^]. Key pain points included:

- Redundant costs from individual teams each maintaining their own feature pipelines
- No common abstraction for features — no uniform naming, type system, or deployment patterns
- Feature reuse across projects was nearly impossible
- Training-serving skew was a constant risk
- Adding new features took **weeks** of engineering time [^133^]

### Architecture & Design

Feathr operates as an **abstraction layer** between raw data sources and ML model workflows, providing a unified feature namespace [^104^]:

**Producer-Consumer Model**:
- **Producers** (feature engineers): Define and register features based on raw data sources, including time-series data, or compose features from other features
- **Consumers** (data scientists/ML engineers): Specify which features to import by name, without needing to understand implementation details

**Key Capabilities** [^127^][^130^]:
- **Point-in-time correctness**: Automatically computes feature transformations and joins them to training data using point-in-time-correct semantics to avoid data leakage
- **Unified transformation API**: Works in offline batch, streaming, and online environments
- **Feature registry**: Makes named transformations and features discoverable and reusable across teams
- **Rich type system**: Including embeddings for deep learning scenarios
- **Built-in optimizations**: Bloom filters, salted joins; processes billions of rows and PB-scale data

```python
# Example: Window Aggregation Feature with Point-in-Time Correctness
agg_features = [Feature(name="f_location_avg_fare",
                        key=location_id,
                        feature_type=FLOAT,
                        transform=WindowAggTransformation(
                            agg_expr="cast_float(fare_amount)",
                            agg_func="AVG",
                            window="90d"))]
```

### Impact at LinkedIn

| Metric | Value |
|--------|-------|
| Production years | **6+ years** |
| Features managed | **Thousands** |
| Time to add new features | Reduced from **weeks to days** |
| Performance improvement | **Up to 50%** faster than custom pipelines |
| Applications powered | **Dozens** (Search, Feed, Ads) |
| Data scale | **Billions of rows, petabytes** |

> "Teams reported reducing engineering time for adding new features from weeks to days, observed performance improvements of up to 50% compared to custom pipelines, and successfully enabled feature sharing between similar applications, leading to measurable business metric improvements." [^104^]

---

## 4. Liger Kernel: Triton Kernels for GPU LLM Training

### Overview

**Liger Kernel** is an open-source collection of efficient Triton kernels for LLM training, released by LinkedIn in **August 2024**. It achieves **~20% increase in training throughput** and **~60% reduction in GPU memory usage** compared to Hugging Face implementations [^98^][^105^].

> "Liger Kernel is a collection of Triton kernels designed specifically for LLM training. It can effectively increase multi-GPU training throughput by 20% and reduces memory usage by 60%." — **GitHub README** [^98^]

### Technical Approach

The core optimization technique is **operator fusion** — combining multiple standalone GPU kernels into a single kernel to eliminate per-operation time and memory overhead [^102^]:

1. **Kernel Fusion**: Eliminates HBM-to-SRAM memory traffic between operations
2. **In-Place Replacement**: Reduces memory allocation overhead
3. **Chunking/Blockwise Computation**: Avoids materializing full logits, reducing memory footprint — especially important for models with large vocabulary spaces

### Key Technical Details

- **Implementation**: Built using OpenAI's Triton programming language for Python-like GPU kernel development
- **Compatibility**: Works out of the box with Flash Attention, PyTorch FSDP, and Microsoft DeepSpeed
- **Exact computation**: No approximations; rigorous unit tests and convergence testing
- **Minimal dependencies**: Only requires PyTorch and Triton
- **Multi-GPU supported**: FSDP, DeepSpeed, DDP

### Supported Models

Liger Kernel supports patching for [^98^]: Qwen2/2.5/3, Paligemma, Phi3/3.5, OLMo2/3, GLM-4, GPT-OSS, InternVL3, Llama, Mistral, Gemma, and more.

### Benchmarks

| Model | Throughput Gain | Memory Reduction |
|-------|----------------|------------------|
| LLaMA 3-8B | **42.8%** | **54.8%** |
| Qwen2 | **25.5%** | **56.8%** |
| Gemma 7B | **11.9%** | **51.8%** |
| Mistral 7B | **27%** | **21%** |
| Phi3 | **17%** | **13%** |

> "Hugging Face models start to OOM at a 4K context length, whereas Hugging Face + Liger Kernel scales up to 16K." [^98^]

### Production Impact at LinkedIn

- **3X reduction** in end-to-end training time for an in-house ~70B parameter model [^102^]
- **10-20% throughput gains** for models at ~100B and ~10B scale
- **275,000 GPU hours saved** through optimizations including Liger Kernels [^121^]
- Integrated into LinkedIn's production LLM training infrastructure stack: Flyte → Kubernetes → GPU training [^102^]

### Community Adoption (as of early 2025)

- **3,000+ GitHub stars**
- **200,000+ downloads**
- **40+ contributors**
- **250+ pull requests**
- Integrated with: Axolotl, LLaMa-Factory, SFTTrainer, Hugging Face Trainer, SWIFT

### Academic Publication

- **Tech Report**: arXiv:2410.10989 [^105^]
- **Conference**: OpenReview [^100^]
- **Authors**: Pin-Lun Hsu, Yun Dai, Vignesh Kothapalli, Qingquan Song, Shao Tang, Siyu Zhu, Steven Shimizu, Shivam Sahni, Haowen Ning, Yanning Chen (LinkedIn Inc.)

---

## 5. Pro-ML: Full ML Lifecycle Platform & Health Assurance

### Overview

**Pro-ML** is LinkedIn's centralized machine learning platform that provides a comprehensive lifecycle management system for hundreds of AI models serving LinkedIn's members and customers [^128^][^131^].

### Health Assurance Layer

The **Health Assurance (HA)** platform is a critical component of Pro-ML that addresses the challenge of monitoring hundreds of production AI models [^128^]:

> "Before the Health Assurance platform was built, individual teams at LinkedIn had to develop their own monitoring systems and tools for ensuring model health, which significantly decreased AI engineer productivity and created fragmented approaches across the organization." [^128^]

**Key Capabilities**:
- **Feature drift monitoring**: Tracks feature values computed at inference time, runs daily batch jobs computing statistics, pushes to Pinot
- **Real-time feature distributions**: Captures numeric feature value distributions with minute-level granularity
- **Inference latency tracking**: Mean, P50, P75, P90, P99 latency metrics
- **Alerts via ThirdEye**: Automated alerting when significant distribution changes are detected

**Three-Phase Deployment Monitoring** [^128^]:
1. **Dark Canary**: Models run without serving real traffic — catch inconsistencies before going live
2. **Experimentation**: Small percentage of production traffic with business/technical metric monitoring
3. **MME (Majority Member Experience)**: Full production with real-time distribution monitoring

### Architecture Integration

The Health Assurance component is **embedded directly into inference applications** [^128^]:

```
Inference App → HA Component → Real-time feature distributions → Kafka → Samza → 
Metrics Aggregator → InGraphs (visualization)
                     ↓
                Daily batch job → Pinot → ThirdEye (alerting)
```

**The Metrics Aggregator Innovation**: With ~1,000 models on 500 hosts tracking 10 features with 5 metrics each, a naive implementation would create **25 million metric keys**. The Metrics Aggregator solves this by aggregating at the model level rather than host level [^128^].

### Key Technologies

- **Kafka**: Event transport
- **Samza**: Stream processing for metric aggregation
- **Pinot**: Real-time analytics datastore for drift statistics
- **ThirdEye**: Alerting on anomalies
- **InGraphs**: Internal real-time monitoring visualization

---

## 6. Galene: Search Architecture & Write-Read Decoupling

### Overview

**Galene** is LinkedIn's search architecture, built to deliver highly personalized search over semi-structured data at massive scale. It was developed to replace LinkedIn's previous Lucene-based system which had scaling limitations [^20^][^23^][^25^].

> "LinkedIn's corpus is a richly structured professional graph comprised of 300M+ people, 3M+ companies, 2M+ groups, and 1.5M+ publishers. Members perform billions of searches, and each of those searches is highly personalized." — **Diego Buthay & Sriram Sankar, LinkedIn** [^20^]

### Write-Read Decoupling Architecture

Galene implements **strict node-level read-write separation**, a key architectural pattern identified in academic literature on large-scale search engines [^109^][^112^]:

> "LinkedIn Galene maintains strict separation between Indexer nodes (consuming Kafka streams, building Lucene segments, and periodically force-merging snapshots) and Searcher nodes (loading and serving snapshots). Searcher nodes never perform indexing, completely eliminating merge overhead from the query path." [^109^]

**Three Index Types** [^119^]:
1. **Base Index**: Generated by Hadoop periodically; single-segment Lucene index; on-disk, immutable, MMAPed and MLOCKed; contains complex/rich features computed offline
2. **Live Index**: In-memory data structure with incremental updates to documents
3. **Snapshot Index**: On-disk snapshot of Live index; single-segment Lucene index that Live index is folded into regularly

### Key Features

- **Offline index building** via Hadoop
- **Live updates at fine granularity**
- **Static rank and early termination** for efficient querying
- **Faceting** support (discoverable, static values, supplied values)
- **Data distribution** across shards
- **Relevance framework** for rapid experimentation
- **Query rewriting** system for converting user queries into structured Galene queries [^124^]

### Impact

- Instant Member Search became **more than 2x faster** using **~1/3 of the hardware** [^25^]
- Enabled searching the entire LinkedIn database (previously limited to 1st/2nd degree connections)
- Supports offline static rank computation, personalization by connection degree, and approximate name matching [^25^]

### Academic Recognition

Galene is cited as a canonical example of **node-level read-write separation** in search engine architecture in the academic survey paper *"Write-Read Decoupling in Modern Large-Scale Search Engines"* (2026) [^109^][^112^].

---

## 7. ThirdEye: Anomaly Detection for ML Model Monitoring

### Overview

**ThirdEye** is LinkedIn's open-source integrated tool for **real-time monitoring of time series and interactive root-cause analysis**. It enables collaboration on identification and analysis of deviations in business and system metrics [^114^].

> "ThirdEye is an integrated tool for realtime monitoring of time series and interactive root-cause analysis. It enables anyone inside an organization to collaborate on effective identification and analysis of deviations in business and system metrics." — **GitHub** [^114^]

### Key Features

**Detection** [^114^]:
- Detection toolkit based on business rules and exponential smoothing
- Real-time monitoring of high-dimensional time series
- Native support for seasonality and permanent change points
- Email alerts with 1-click feedback for automated tuning

**Root-Cause Analysis**:
- Collaborative root-cause analysis dashboards
- Interactive slice-and-dice of data, correlation analysis, event identification
- Reporting and archiving tools for anomalies and analyses
- Knowledge graph construction from user feedback

**Integration** [^114^]:
- Connectors for Pinot, Presto, MySQL, CSV
- Connectors for discrete event data (holidays from Google Calendar)
- Plugin support for detection and analysis components

### ThirdEye at LinkedIn

ThirdEye powers LinkedIn's internal anomaly detection and root cause analysis platform, integrated with Pinot [^107^][^148^]. It serves as the alerting layer for:

- **Pro-ML Health Assurance**: Receives feature drift statistics from Pinot and alerts on distribution anomalies [^128^]
- **Business metrics monitoring**: ~10,000 business metrics across ~50,000 dimensions [^157^]
- **Automated observability**: Powers fully automated monitoring with no human in the loop

### ThirdEye in Production (External)

At AB Tasty, ThirdEye manages **12,000 detection rules per hour** across 4,000 clients, achieving **85% true positive rate** after tuning [^113^].

---

## 8. Managed Beam: Real-Time Feature Engineering Pipelines

### Overview

**Managed Beam** is LinkedIn's managed stream processing platform built on Apache Beam, processing **4 trillion events daily** through **3,000+ pipelines** [^30^].

> "At LinkedIn, Apache Beam plays a pivotal role in stream processing infrastructures that process over 4 trillion events daily through more than 3,000 pipelines across multiple production data centers." — **Apache Beam Case Study** [^30^]

### Real-Time ML Feature Generation

Managed Beam serves as the foundation for LinkedIn's **real-time ML feature engineering platform** [^30^][^110^]:

**The Problem**: Before Apache Beam, offline ML feature generation had a **24-48 hour delay** between member actions and their impact on recommendations, resulting in missed opportunities [^30^].

**The Solution**:
1. AI engineers create feature definitions and deploy them using Managed Beam
2. Streaming Apache Beam pipelines generate fresher ML features by filtering, processing, and aggregating events from Kafka in real-time
3. Features are written to the feature store (Feathr/Venice)
4. Downstream pipelines retrieve data and feed it into recommendation systems

**Results**:
- **End-to-end pipeline latency: seconds** (vs. 24-48 hours previously)
- **2x optimization in cost-to-serve**
- **2x improvement in processing performance**
- **Time-to-production for new pipelines: months → days** [^30^]

### Key Features of Managed Beam [^110^]

- **Cross-language compatibility**: Java and Python Beam APIs
- **Portable**: Write once, run on any supported platform
- **Managed**: Auto-sizing and auto-triaging with zero operational costs to ML users
- **Unified batch and streaming**: Single codebase for both real-time and backfill processing

### Anti-Abuse & AI Modeling

The Anti-Abuse platform (Chronos) uses two streaming Beam pipelines:
1. **Filter pipeline**: Reads from Kafka, extracts fields, aggregates and filters events
2. **Model pipeline**: Consumes filtered messages, triggers AI scoring models, writes abuse scores

Results: **6%+ improvement** in detecting logged-in scraping profiles; catch scrapers within minutes [^30^].

---

## 9. Infrastructure for AI at Scale: Serving 1B+ Users

### Scale Overview

LinkedIn serves AI to **1.2 billion members** through two distinct AI workloads [^111^][^121^]:

1. **Traditional recommendation and ranking models**: Power feeds, job suggestions, and search
2. **Generative AI features**: LinkedIn Hiring Assistant (LIHA), profile summarization, and other LLM-powered features

### GPU Infrastructure Strategy

**Animesh Singh, Executive Director of AI and ML Platform at LinkedIn**, describes the infrastructure strategies [^111^][^121^]:

> "LinkedIn trains models with 100+ billion parameters but compresses them to 7-8 billion parameters for inference using distillation, pruning, and quantization techniques. This approach makes running AI at scale ROI-positive."

**Key Optimizations**:
- **30x expansion** in petaflops capacity with rearchitected networking for GPU efficiency
- **Liger Kernels, fused ops, Avro accelerations**: Saved 275,000 GPU hours
- **Distillation, pruning, compression**: For efficient inference
- **Speculative decoding and low-precision training**: For faster inference
- **Incremental training**: Eliminates redundant data passes

### Reliability at Scale

With H100s and H200s experiencing **10% thermal stress failure rates**, LinkedIn's strategy includes [^111^]:
- Rapid checkpointing
- Automated recovery
- Intelligent job rescheduling
- Treating "GPUs as pets, not cattle" — individual GPU tracking and care

### Infrastructure Stack

| Layer | Technology |
|-------|-----------|
| Workflow Orchestration | Flyte |
| Container Orchestration | Kubernetes |
| Training Frameworks | HuggingFace Trainer, PyTorch Lightning, custom PyTorch |
| Distributed Training | FSDP, DeepSpeed, DDP |
| GPU Kernels | Liger Kernel, Flash Attention |
| Stream Processing | Apache Samza, Apache Beam |
| Message Broker | Apache Kafka |
| Real-Time Analytics | Apache Pinot |
| Feature Store | Feathr |
| Derived Data Store | Venice |
| Model Monitoring | ThirdEye, Pro-ML Health Assurance |

### LinkedIn's Production Data Stack [^118^][^137^]

```
Data Sources → Kafka → Stream Processing (Samza/Beam) → Feature Store (Feathr)
                                                    → Venice (online serving)
                                                    → Pinot (real-time analytics)
                                                    → Hadoop/HDFS (offline analytics)
                                                    → Galene (search indexing)
```

---

## 10. Open Source Strategy: Why LinkedIn Open-Sources

### Philosophy

LinkedIn has open-sourced **more than 75 projects** across multiple categories, with several gaining widespread adoption and becoming part of the Apache Software Foundation [^30^][^136^].

> "Numbers can often be vanity metrics. We consider community adoption to be our key indicator of success." — **Igor Perisic, VP Engineering & Chief Data Officer, LinkedIn** [^136^]

### Why LinkedIn Open-Sources

According to Igor Perisic, LinkedIn's open source strategy delivers value on multiple dimensions [^136^]:

**1. Better Software Quality**:
> "We've found that the first result of open-sourcing your projects is that your developers will write better software. When a developer open sources a piece of code, their reputation is on the line. It's essentially a type of peer review." [^136^]

**2. Developer Growth**:
> "Working on an open source project exposes our developers to the developer community outside of the company where they work. It will help them become more aware of new trends, and help them learn how to assess the value of other developers' input." [^136^]

**3. Engineering Brand**:
> "From a company's perspective it also helps develop your engineering brand, which proves useful in attracting new talent and retaining existing employees." [^136^]

**4. Community Engagement**:
> "One lesson we learned early is that you can't just put software out into the community and not continue to innovate. Many of the things that determine whether an open source project will be successful are related to how you engage with the community." [^136^]

### Apache Software Foundation Projects

Several LinkedIn projects have become **top-tier Apache projects** [^136^]:
- **Apache Kafka**: The de facto standard for event streaming; used by 80%+ of Fortune 100
- **Apache Samza**: Stream processing framework
- **Apache Helix**: Cluster management framework
- **Apache Pinot**: Real-time distributed OLAP datastore

### Key Open Source Projects Timeline

| Year | Project | Description |
|------|---------|-------------|
| 2010 | Kafka (internal) | Event streaming platform |
| 2011 | Kafka (open-sourced) | Donated to Apache Foundation |
| 2013 | Apache Samza | Stream processing framework |
| 2014 | Apache Pinot (internal) | Real-time analytics (open-sourced later) |
| 2015 | Burrow | Kafka consumer lag monitoring |
| 2016 | Galene (production) | Search architecture |
| 2017 | Kafka Cruise Control | Automated cluster management |
| 2019 | Brooklin | Data streaming service |
| 2022 | Feathr | Feature store (open-sourced) |
| 2024 | Liger Kernel | GPU Triton kernels for LLM training |

---

## 11. Additional Open Source Projects

### Venice: Derived Data Platform

**Venice** is LinkedIn's open-source derived data storage platform, serving as the default storage layer for online AI use cases [^141^][^143^][^144^].

- **Scale**: 2,600+ production stores, 175M+ key lookups/sec, 230M+ writes/sec
- **Write latency SLA**: Under 10 minutes
- **Use cases**: People You May Know, feed, videos, ads, notifications, A/B testing, LinkedIn Learning
- **Architecture**: Three ingestion paths — bulk loads (Spark), nearline writes (Samza), direct online writes
- **Suitable for**: Feature stores (like Feathr), real-time recommendation systems [^143^]

### Brooklin: Data Streaming Service

**Brooklin** is an extensible distributed system for reliable nearline data streaming [^161^][^162^]:
- **Scale**: 2,000+ datastreams, 1,000+ unique sources, 200+ applications
- **Throughput**: 38 billion messages/day (non-Kafka), 2 trillion messages/day (Kafka mirroring)
- **Supports**: Kafka, Espresso, Oracle, EventHubs, Kinesis as sources
- **Guarantees**: At-least-once delivery, partition-level ordering

### Kafka Cruise Control: Automated Cluster Management

**Cruise Control** is an autopilot for Kafka clusters, open-sourced in 2017 [^152^][^156^][^158^]:
- **Anomaly detection**: Broker failures, metric anomalies, disk failures, slow brokers
- **Self-healing**: Automatic replica movement from failed brokers
- **Multi-goal rebalancing**: Rack-awareness, resource capacity checks, traffic distribution
- **Scale at LinkedIn**: Manages 10,000+ Kafka brokers where broker deaths are an almost daily occurrence [^158^]

---

## 12. Summary & Key Metrics

### LinkedIn Open Source Ecosystem at a Glance

| Category | Project | Status | Scale/Impact |
|----------|---------|--------|-------------|
| **Streaming** | Apache Kafka | Apache TLP | 7T+ messages/day; 80%+ Fortune 100 |
| **Stream Processing** | Apache Samza | Apache TLP | 4T events/day at LinkedIn |
| **Real-Time Analytics** | Apache Pinot | Apache TLP | 250K+ QPS, 50-80+ apps |
| **Feature Store** | Feathr | LF AI & Data | 6+ years production, 1000s of features |
| **LLM Training** | Liger Kernel | Open Source | 20% throughput, 60% memory reduction |
| **Search** | Galene | Internal | Billions of personalized queries |
| **Anomaly Detection** | ThirdEye | Open Source | 10K+ business metrics monitored |
| **Derived Data Store** | Venice | Open Source | 230M+ writes/sec |
| **Data Streaming** | Brooklin | Open Source | 2T+ messages/day mirrored |
| **Kafka Management** | Cruise Control | Open Source | 10K+ brokers managed |
| **Feature Engineering** | Managed Beam | Internal | 3,000+ pipelines, 4T events/day |
| **ML Platform** | Pro-ML | Internal | 100s of models monitored |

### Key Business Impact

- **Kafka**: Used by 80%+ of Fortune 100 companies; created a $10B+ company (Confluent)
- **Pinot**: Powers 50-80+ user-facing applications at LinkedIn; adopted by Uber, Stripe, DoorDash, Walmart, Cisco Webex
- **Feathr**: Reduced feature engineering time from weeks to days; 50% performance improvement
- **Liger Kernel**: 60% GPU memory reduction, 20% throughput increase; adopted by major LLM training frameworks
- **Managed Beam**: 2x cost-to-serve optimization; pipeline production time from months to days

### LinkedIn's ML Infrastructure Philosophy

LinkedIn's approach to ML infrastructure embodies several key principles:

1. **Open source as a strategy**: Build internally, open source strategically, engage with community
2. **Unified platforms over fragmented tools**: Pro-ML, Managed Beam, and Feathr centralize capabilities
3. **Real-time by default**: Kafka + Samza/Beam + Pinot enable sub-second data freshness
4. **Point-in-time correctness**: Feathr's temporal join prevents data leakage
5. **Co-design between modeling and infrastructure**: GPU teams, platform engineers, and data scientists collaborate from day one [^111^]
6. **Health assurance embedded**: Monitoring is part of the platform, not bolted on

---

## Source Index

[^30^] Apache Beam Case Study: "4 Trillion Events Daily at LinkedIn" - https://beam.apache.org/case-studies/linkedin/

[^98^] Liger Kernel GitHub Repository - https://github.com/linkedin/Liger-Kernel

[^99^] Apache Pinot Use Cases - https://pinot.apache.org/use-cases/

[^100^] Liger Kernel OpenReview - https://openreview.net/forum?id=36SjAIT42G

[^101^] Liger Kernels on AMD GPU (EmbeddedLLM) - https://embeddedllm.com/blog/cuda-to-rocm-portability-case-study-liger-kernel

[^102^] ZenML: Optimizing LLM Training with Triton Kernels - https://www.zenml.io/llmops-database/optimizing-llm-training-with-triton-kernels-and-infrastructure-stack

[^103^] Feathr GitHub Mirror Documentation - https://gitee.com/mirrors/feathr

[^104^] ZenML: Feathr Feature Store Case Study - https://www.zenml.io/mlops-database/linkedin-pro-ml-feathr-feature-store

[^105^] Liger Kernel: Efficient Triton Kernels for LLM Training (arXiv:2410.10989) - https://arxiv.org/html/2410.10989v2

[^107^] AI Council: Building Real-Time Analytics with Apache Pinot - https://aicouncil.com/talks/building-real-time-analytics-applications-using-apache-pinot

[^108^] Write-Read Decoupling in Modern Large-Scale Search Engines (Paper Review) - https://www.themoonlight.io/zh/review/write-read-decoupling-in-modern-large-scale-search-engines

[^109^] Write-Read Decoupling in Modern Large-Scale Search Engines (arXiv:2605.01260) - https://arxiv.org/html/2605.01260v1

[^110^] Beam Summit: Managed Beam at LinkedIn - https://beamsummit.org/sessions/2023/power-realtime-machine-learning-feature-engineering-with-managed-beam-at-linkedin/

[^111^] LinkedIn AI Infrastructure Secrets for 1.2B Users (WEKA) - https://www.youtube.com/watch?v=Cp-3XPdFTn4

[^112^] Write-Read Decoupling in Modern Large-Scale Search Engines (PDF) - https://arxiv.org/pdf/2605.01260

[^113^] Timeseries Anomaly Detection at Scale with ThirdEye (Medium) - https://medium.com/the-ab-tasty-tech-blog/data-quality-timeseries-anomaly-detection-at-scale-with-thirdeye-468f771154e6

[^114^] ThirdEye GitHub Repository - https://github.com/project-thirdeye/thirdeye

[^116^] LinkedIn's Pro-ML Architecture (Medium) - https://medium.com/dataseries/linkedins-pro-ml-architecture-summarizes-best-practices-for-building-machine-learning-at-scale-77fcb6afc9ec

[^118^] How LinkedIn Uses Apache Kafka in Production (FactorHouse) - https://factorhouse.io/articles/linkedin-kafka-architecture

[^119^] Galene: LinkedIn's Search Architecture (SlideShare) - https://www.slideshare.net/slideshow/galene-linkedins-search-architecture/42056756

[^120^] How (and why) Kafka was created at LinkedIn (Frontier Enterprise) - https://www.frontier-enterprise.com/unleashing-kafka-insights-from-confluent-jun-rao/

[^121^] Inside LinkedIn's AI Stack (AI Infra Summit) - https://www.youtube.com/watch?v=iwHeugRNAq8

[^122^] ML Lifecycle Management Guide (Clarifai) - https://www.clarifai.com/blog/ml-lifecycle-management/

[^123^] Jay Kreps Interview (First Round) - https://review.firstround.com/what-nobody-tells-engineers-about-becoming-a-ceo-jay-kreps-co-founder-and-ceo-confluent/

[^124^] LinkedIn Basic Search is Galene (BooleanStrings) - https://booleanstrings.com/2014/11/06/linkedin-basic-search-is-galene-lir-search-is-lucene/

[^125^] LinkedIn AI Infrastructure (WEKA transcript) - https://www.weka.io/resources/video/linkedins-ai-infrastructure-secrets-for-1-2b-users/

[^127^] Feathr Official Documentation - https://feathr-ai.github.io/feathr/

[^128^] ZenML: Pro-ML Model Health Assurance - https://www.zenml.io/mlops-database/linkedin-pro-ml-pro-ml-model-health-assurance

[^129^] Feathr: FS Summit 2022 Talk - https://www.youtube.com/watch?v=u8nLY9Savxk

[^130^] Feathr on Azure Announcement - https://azure.microsoft.com/en-us/blog/feathr-linkedin-s-feature-store-is-now-available-on-azure/

[^131^] LinkedIn's Pro-ML Architecture (KDnuggets) - https://www.kdnuggets.com/2020/09/linkedin-pro-ml-architecture-best-practices-for-building-machine-learning-scale.html

[^133^] Feathr joins LF AI & Data Foundation (SiliconAngle) - https://siliconangle.com/2022/09/12/linkedins-open-source-feathr-feature-store-for-machine-learning-joins-lf-ai-data-foundation/

[^135^] How LinkedIn Uses Apache Samza (InfoQ) - https://www.infoq.com/articles/linkedin-samza/

[^136^] The Secrets to LinkedIn's Open Source Success (InfoWorld) - https://www.infoworld.com/article/2250626/the-secrets-to-linkedins-open-source-success.html

[^137^] LinkedIn Data Tech Stack (Reddit) - https://www.reddit.com/r/dataengineering/comments/1g5t5ck/linkedin-data-tech-stack/

[^139^] How LinkedIn Customizes Its 7 Trillion Message Kafka Ecosystem (ByteByteGo) - https://blog.bytebytego.com/p/how-linkedin-customizes-its-7-trillion

[^140^] LinkedIn Open-Sourced Its Feature Store (InfoQ) - https://www.infoq.com/news/2022/07/linkedin-feathr-fs/

[^141^] Venice: How LinkedIn Built a Pipeline at 230M Records/sec - https://www.datatinkerer.io/p/how-linkedin-built-a-pipeline-that-scales-to-230-million-records

[^142^] Why Open Source is Cool on LinkedIn (TheLinkedInEngineer) - https://www.thelinkedinengineer.com/p/why-open-source-is-cool-on-linkedin

[^143^] Venice Architecture Overview - https://venicedb.org/getting-started/learn-venice/architecture-overview/

[^144^] Venice GitHub Repository - https://github.com/linkedin/venice

[^145^] Apache Pinot Blog - https://pinot.apache.org/blog

[^146^] Apache Pinot Official Website - https://pinot.apache.org/

[^148^] Building Real-Time Analytics Applications Using Apache Pinot (YouTube/Data Council) - https://www.youtube.com/watch?v=mOzjVRf0yt4

[^151^] Exploring Kafka Cruise Control - https://cefboud.com/posts/kafka-cruise-control/

[^152^] Apache Kafka Cruise Control Step by Step (Axual) - https://axual.com/blog/apache-kafka-cruise-control

[^154^] Speed of Apache Pinot at the Cost of Cloud Object Storage (InfoQ) - https://www.infoq.com/presentations/apache-pinot-cloud/

[^155^] Igor Perisic Profile (OECD Events) - https://www.oecd-events.org/e/ai-wips-2021/attendee/c622c569-7356-eb11-b9ed-000d3a20e9aa

[^156^] LinkedIn Announces Cruise Control Open Source (TechCrunch) - https://techcrunch.com/2017/08/28/linkedin-announces-new-automated-load-balancing-tool-to-keep-kafka-clusters-running/

[^157^] Launching At LinkedIn: The Story Of Apache Pinot (StarTree) - https://startree.ai/resources/launching-at-linkedin-the-story-of-apache-pinot/

[^158^] Cruise Control for Apache Kafka (GitHub) - https://github.com/linkedin/cruise-control

[^160^] Igor Perisic, VP Engineering & CDO (CharityBuzz) - https://www.charitybuzz.com/catalog_items/auction-tour-linkedin-hq-enjoy-lunch-with-igor-perisic-1304301

[^161^] A Dive into Streams @LinkedIn with Brooklin (InfoQ) - https://www.infoq.com/presentations/linkedin-streams-brooklin/

[^162^] Brooklin GitHub Repository - https://github.com/linkedin/brooklin

[^163^] Igor Perisic, LinkedIn VP (YouTube) - https://www.youtube.com/watch?v=HZu-KCj0a3k

---

*Document compiled from 25+ independent searches across LinkedIn Engineering Blog, Apache Foundation venues, arXiv, conference proceedings, GitHub repositories, and technical analysis platforms.*
