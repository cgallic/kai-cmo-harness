# Dimension 8: Key People, Org Structure & Talent Flow — LinkedIn AI Deep Dive

**Research Date:** 2025  
**Sources:** 60+ web searches, conference talks, academic papers, press releases, blog posts  
**Classification:** Internal-Use Research

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Deepak Agarwal — Chief AI Officer (Jan 2025)](#2-deepak-agarwal--chief-ai-officer-jan-2025)
3. [The FAIT Team & Foundation AI Technologies](#3-the-fait-team--foundation-ai-technologies)
4. [Ya Xu Departure to DeepMind (Sep 2024)](#4-ya-xu-departure-to-deepmind-sep-2024)
5. [Qingquan Song to OpenAI (2025)](#5-qingquan-song-to-openai-2025)
6. [Craig Martell's Legacy — AI Academy](#6-craig-martells-legacy--ai-academy)
7. [Karthik Ramgopal — GenAI & Agent Platform](#7-karthik-ramgopal--genai--agent-platform)
8. [Laura Lorenzetti — Editorial + Product Intersection](#8-laura-lorenzetti--editorial--product-intersection)
9. [Other Key AI Personnel](#9-other-key-ai-personnel)
10. [Org Chart Reconstruction](#10-org-chart-reconstruction)
11. [New Hires and Openings](#11-new-hires-and-openings)
12. [Conference Appearances & Publications](#12-conference-appearances--publications)
13. [Talent Flow Analysis](#13-talent-flow-analysis)
14. [Key Insights & Strategic Implications](#14-key-insights--strategic-implications)

---

## 1. Executive Summary

LinkedIn's AI organization underwent a significant leadership reshuffle in 2024-2025. The departure of Ya Xu (VP Data & AI, to DeepMind in Sep 2024) and the arrival of Deepak Agarwal as Chief AI Officer (Jan 2025) marked a major inflection point. The company is now organized around a central "Core AI" function led by Agarwal, with specialized teams for Foundation AI Technologies (FAIT), Generative AI applications, Trust/Responsible AI, and product-specific AI teams for Talent Solutions and Marketing Solutions.

Key talent losses include Ya Xu (to DeepMind), Qingquan Song (to OpenAI, 2025), and Vignesh Kothapalli (to Stanford PhD). Key talent gains include Deepak Agarwal (from Pinterest) and continued investment in internal leaders like Karthik Ramgopal (Distinguished Engineer, GenAI), Hamed Firooz (Principal AI Scientist, FAIT), and Daniel Olmedilla (Sr. Director, Trust AI).

The company's flagship AI initiatives include: **360Brew** (150B-parameter foundation model for personalization), **Hiring Assistant** (first production AI agent for recruiting), **LiRank/LiGNN** (industrial-scale ranking and graph neural network systems), and the **EON** fine-tuned LLM series.

---

## 2. Deepak Agarwal — Chief AI Officer (Jan 2025)

### 2.1 Background & Appointment

Deepak Agarwal returned to LinkedIn as **Chief AI Officer in January 2025**, marking his second tenure at the company. [^122^] He previously served as **VP of AI at LinkedIn for eight years (2012-2020)**, where he led a team of more than 500 engineers and laid the foundation for much of LinkedIn's current AI infrastructure. [^411^] [^412^]

**Immediate Pre-LinkedIn Role:** Chief AI Officer and VP of Consumer and Trust Engineering at **Pinterest** (2020-2025), where he scaled his organization from ~200 to roughly **1,000 engineers**, unifying AI Foundations, Consumer Engineering, Trust & Safety, and AI Product. [^2^] He also serves as a **Distinguished Fellow and Venture Partner at Fellows Fund**, advising and investing in AI startups. [^127^]

**Earlier Career:** VP of Engineering at Yahoo!, researcher at AT&T Labs. Published extensively on large-scale recommender systems (including a book) and elected **Fellow of the American Statistical Association**. [^127^]

### 2.2 Strategy & Vision

Agarwal's stated mission focuses on four pillars [^122^] [^411^]:

1. **Push boundaries of AI innovation** — ensuring LinkedIn remains "cutting-edge and industry-defining"
2. **Ethical, inclusive, human-centric AI** — emphasizing empathy in AI development
3. **Economic opportunity for every member** — aligning AI with LinkedIn's mission
4. **Responsible and compliant AI** — building trust through safety and governance

At a podcast appearance, Agarwal outlined his approach to org design for AI platforms, discussing how he scaled Pinterest's AI org from 200 to 1,000+ engineers by unifying AI Foundations, Consumer Engineering, Trust & Safety, and AI Product under one umbrella. [^127^] He emphasized treating AI as an "operating model" rather than a set of isolated tools.

Agarwal also established LinkedIn's **AI Academy and empathy programme** during his first tenure (2012-2020), which became a model for industry-wide AI literacy programs. [^411^]

### 2.3 Speaking Engagements

- **HumanX 2026** (San Francisco) — Featured speaker [^386^]
- **Podcast interviews** on AI platform scaling and org design [^127^]
- **PR Week Dashboard 25** — Named to Class of 2025 [^385^]

---

## 3. The FAIT Team & Foundation AI Technologies

### 3.1 What is FAIT?

**FAIT = Foundation AI Technologies**, the core AI research and infrastructure team at LinkedIn responsible for building the company's foundational models, training infrastructure, and core AI platforms. The team operates under Deepak Agarwal's leadership and is the successor to the organization Ya Xu previously led.

### 3.2 Key FAIT Personnel

| Name | Title | Focus Area | Background |
|------|-------|------------|------------|
| **Hamed Firooz** | Principal AI Scientist, FAIT Team Lead | 360Brew foundation model, personalization | 15 years in large-scale AI; ex-Meta AI (led multimodal Content Understanding models); 50-person team [^138^] [^407^] |
| **Maziar Sanjabi** | Principal Scientist, LinkedIn AI | LLMs for personalization tasks | Ex-Meta AI; 60+ papers at NeurIPS, ICML, ICLR, ACL, CVPR [^13^] [^138^] |
| **Necip Fazil Ayan** | Senior Director, FAIT | Foundational AI Technologies, Knowledge Graph | Ex-Director of Facebook AI (2013-2022); PhD UMD [^70^] |
| **Sathiya Keerthi Selvaraj** | Principal Staff Scientist | Distributed training, large-scale linear programming, information extraction | Ex-Criteo Research, Microsoft, Yahoo! Research; 100+ papers; Action Editor JMLR [^60^] [^78^] |
| **Souvik Ghosh** | Principal Staff Engineer & Scientist | Large-scale recommender systems, probabilistic ML | Ex-Yahoo! Research, Assistant Professor Columbia; PhD Cornell [^45^] |
| **Fedor Borisyuk** | Core Researcher | LiRank (industrial-scale ranking), LiGNN (graph neural networks) | Key author of KDD 2024 Best Applied Data Science Paper [^413^] |
| **Qingquan Song** | Senior Staff ML Engineer (until 2025) | LiRank, AutoML, recommender systems | PhD Texas A&M; moved to OpenAI in 2025 [^8^] [^3^] |

### 3.3 Key FAIT Projects

#### 360Brew — Foundation Model for Personalization
- **150-billion-parameter** decoder-only foundation model
- Trained on **1 trillion LinkedIn engagement tokens**
- Solves **30+ personalization tasks** out-of-the-box without task-specific fine-tuning
- Achieved **20x cost and latency reduction** through on-policy knowledge distillation, model compression, and serving optimizations
- Authors include: Hamed Firooz, Maziar Sanjabi, Karthik Ramgopal, Qingquan Song, Ya Xu, Yu Wang, Yun Dai, Necip Fazil Ayan, and 15+ others [^147^]
- Paper submitted to arXiv (later withdrawn) [^147^]
- Talk presented at **AI Engineer World's Fair 2025** [^138^]

#### LiRank — Industrial Large-Scale Ranking
- Deployed for Feed ranking, Jobs Recommendations, and Ads CTR prediction
- Combines Residual DCN, Dense Gating, Transformers
- Quantization and vocabulary compression for production serving
- **Results**: +0.5% member sessions (Feed), +1.76% qualified job applications, +4.3% Ads CTR
- Won **KDD 2024 Best Paper Award — Applied Data Science Track** [^15^] [^417^]
- Authors: Fedor Borisyuk, Mingzhou Zhou, Qingquan Song, Siyu Zhu, Birjodh Tiwana, and 30+ others [^413^]

#### LiGNN — Graph Neural Networks at LinkedIn
- Large-scale deployed GNN framework for LinkedIn's Economic Graph
- Won **KDD 2024 Best Paper Award — Applied Data Science Track** (shared with LiRank) [^15^]
- Authors: Fedor Borisyuk, Shihai He, Yunbo Ouyang, and 20+ others [^1^]

#### EON — Fine-tuned LLM for Jobs Domain
- Open-source LLMs fine-tuned on LinkedIn Economic Graph data
- Uses multitask instruction tuning to understand job postings, member profiles, and feed posts
- Powers candidate evaluation in Hiring Assistant [^44^] [^80^]

---

## 4. Ya Xu Departure to DeepMind (Sep 2024)

### 4.1 Role at LinkedIn

Ya Xu served as **VP of Engineering and Head of Data & AI at LinkedIn**, leading a global team of **~1,000 data scientists and AI engineers** responsible for all of LinkedIn's data and AI innovations. [^155^] [^57^] She joined LinkedIn as its **first female Principal Staff Engineer** and established the company's initial experimentation platform before rising to VP in 2021. [^154^]

Her organization owned:
- Feed ranking and relevance
- Job search and recommendations
- "People You May Know"
- A/B testing and experimentation platforms
- Data infrastructure for strategic decision-making

### 4.2 Departure Circumstances

Ya Xu **left LinkedIn for Google DeepMind in September 2024** as a VP of Engineering. [^159^] The circumstances of her departure are disputed:

- **Anonymous Blind posts** (unverified) claimed she was "debatably forced out" and that her "entire org got ripped away from her and handed to someone else." The posts alleged her strategies were a failure and that she focused on "empire building." [^159^]
- **Counter-narratives** on the same thread praised her, with one ex-employee stating "she set AI progress forward by 10 years." [^159^]
- Her departure coincided with Deepak Agarwal's return announcement, suggesting a planned leadership transition.

### 4.3 Impact on the Organization

The transition from Ya Xu to Deepak Agarwal represents a significant strategic pivot:
- Ya Xu's background was in **data, experimentation, and statistical ML** (PhD from Stanford in Statistical Machine Learning)
- Agarwal's background is in **large-scale AI platforms, consumer products, and recommender systems** — more aligned with the GenAI transformation
- Her departure triggered reorganization of the Data & AI org, with the FAIT team and GenAI teams being restructured under new leadership

### 4.4 Background

- **Education:** PhD in Statistical Machine Learning from Stanford University
- **Prior to LinkedIn:** Microsoft (noted she "jokes that I've worked for only one company: Microsoft... Microsoft acquired LinkedIn") [^155^]
- **Recognition:** Fortune 40 Under 40 in Tech; delivered Stanford commencement speech (2019)
- **Publications:** Co-authored "Trustworthy Online Controlled Experiments"

---

## 5. Qingquan Song to OpenAI (2025)

### 5.1 Role at LinkedIn

Qingquan Song was a **Senior Staff Machine Learning Engineer at LinkedIn Core AI** (2021-2025), specializing in automated machine learning, recommender systems, and tensor analysis. [^8^] He was a **core contributor to LiRank** (one of the most impactful ranking systems at LinkedIn) and a key author on the **Planner-R1 paper** (agentic RL for travel planning). [^391^]

### 5.2 Departure to OpenAI

Song **joined OpenAI as a Researcher in 2025** on the foundation team. [^8^] His OpenReview profile confirms the transition. [^3^] His LinkedIn-authored paper "Planner-R1" (submitted Sep 2025) includes a footnote noting "Work done while at LinkedIn; currently at OpenAI." [^391^]

### 5.3 Impact of Departure

Song's departure represents a meaningful loss for LinkedIn:
- He was a **core contributor** to LiRank, one of LinkedIn's most impactful production systems
- His expertise in **AutoML and recommender systems** was directly relevant to LinkedIn's core product
- His move to OpenAI's foundation team suggests his skills were highly valued in the broader AI market
- The departure coincides with LinkedIn's push into agentic AI (Planner-R1 work), suggesting his expertise was transitioning into the exact area OpenAI is pursuing

### 5.4 Background

- **Education:** PhD in Computer Science from Texas A&M (2021), supervised by Prof. Xia (Ben) Hu; BS in Statistics from USTC (2016) [^8^]
- **Research:** Automated machine learning, tensor analysis, recommender systems; co-author of "Automated Machine Learning in Action" (Manning)
- **Publications:** 55 research works, 2,450+ citations [^6^]

---

## 6. Craig Martell's Legacy — AI Academy

### 6.1 Role at LinkedIn

Craig H. Martell led multiple AI teams and initiatives at LinkedIn in the mid-2010s, most notably founding the **LinkedIn AI Academy** — a pioneering program to train employees on AI concepts. [^50^] [^51^]

### 6.2 AI Academy Impact

The LinkedIn AI Academy was one of the **industry's first corporate AI literacy programs**, designed to:
- Train non-technical employees on AI concepts and capabilities
- Build an "AI-first" culture across the organization
- Upskill engineers in machine learning techniques
- Establish empathy programs for responsible AI development [^411^]

The program became a model that other tech companies emulated and was cited as a key element of LinkedIn's AI culture transformation during Agarwal's first tenure.

### 6.3 Career Trajectory Post-LinkedIn

Martell's career demonstrates the increasing value of AI leadership expertise:
- **LinkedIn** (mid-2010s): Led AI initiatives, founded AI Academy [^51^]
- **Dropbox**: Head of Machine Intelligence [^51^]
- **Lyft**: Head of Machine Learning [^51^]
- **Cohesity** (2024): Chief Technology Officer, then Chief AI Officer [^51^]
- **U.S. Department of Defense** (2022-2024): First Chief Digital and Artificial Intelligence Officer (CDAO); led Task Force Lima on generative AI; testified before Congress [^41^]
- **Lockheed Martin** (2025-present): Vice President and Chief Technology Officer [^392^]

Martell's trajectory from LinkedIn AI Academy founder to DoD CDAO to Lockheed Martin CTO illustrates how AI leadership expertise developed at consumer tech companies translates to defense and enterprise sectors.

---

## 7. Karthik Ramgopal — GenAI & Agent Platform

### 7.1 Role

**Karthik Ramgopal** is a **Distinguished Engineer at LinkedIn** and the **Uber Technical Lead for the Product Engineering team**, leading approximately **5,000 engineers** responsible for all member and customer-facing products. [^395^] He is specifically responsible for **all Generative AI applications and the Generative AI platform** at LinkedIn. [^393^]

### 7.2 Key Contributions

#### Hiring Assistant — LinkedIn's First Production AI Agent
- AI tech lead for LinkedIn's **Hiring Assistant**, the company's first large-scale agentic AI product [^393^] [^44^]
- Built on top of LinkedIn's broader **agent platform** — a foundation of reusable components
- Uses supervisor agent architecture with specialized sub-agents (intake, sourcing, evaluation, outreach, screening, learning, cognitive memory) [^9^]
- Achieved: **48% less time** reviewing applications, **62% fewer profiles** reviewed per hire, **69% higher InMail acceptance rate** [^79^]
- Spoke extensively about the journey at **InfoQ** and **QCon AI 2025** [^393^] [^44^]

#### GenAI Platform Architecture
- Led the shift from Java to **Python as a first-class language** for GenAI development [^49^]
- Built unified GenAI application stack eliminating fragmented per-product scaffolding
- Created **prompt source of truth service** with namespacing, versioning, and backward compatibility [^393^]
- Abstracted LLM inference through **OpenAI-compatible API**, enabling on-the-fly model switching between Azure OpenAI and on-prem fine-tuned open-source models [^393^]
- Built on **PyTorch, DeepSpeed, and vLLM** for fine-tuning [^49^]

#### Agent Platform
- Architected LinkedIn's **internal agent platform** supporting both foreground (IDE/Copilot) and background agents [^66^]
- Presented at **QCon AI New York 2025** with Prince Valluri on "Platform Teams Enabling AI" [^56^]
- Emphasized spec-driven agent development, sandboxed execution, and human-in-the-loop governance [^66^]

### 7.3 Speaking Engagements

- **QCon AI New York 2025** — "Platform Teams Enabling AI - MCP/Multi-Agentic Tools Across LinkedIn" (with Prince Valluri) [^56^]
- **InfoQ Podcast** — "Platform Engineering for AI: Scaling Agents and MCP at LinkedIn" [^59^] [^66^]
- **InfoQ presentation** — "Lessons Learned from Building LinkedIn's First Agent: Hiring Assistant" (with Daniel Hewlett) [^44^]
- **ByteByteGo collaboration** — "The Evolution of LinkedIn's Generative AI Tech Stack" [^49^]

### 7.4 Background

- **Education:** BS Computer Science, UC Davis; PhD Political Science (machine learning, NLP, network analysis) [^408^]
- **Career at LinkedIn:** Rose from engineer (Pulse acquisition, 2013) through Sr. Engineering Manager (Head of Feed AI) to VP Engineering, AI & Data Science [^404^] [^411^]

---

## 8. Laura Lorenzetti — Editorial + Product Intersection

### 8.1 Role

**Laura Lorenzetti** serves as **VP of Product & Executive Editor at LinkedIn News**. [^397^] She leads the intersection of **editorial content strategy and product development** for LinkedIn's news and content ecosystem.

### 8.2 Editorial + Product Intersection

Lorenzetti's role is unique in that it bridges LinkedIn's **editorial/news function** with its **AI-driven product strategy**:
- Oversees LinkedIn's positioning as a "de facto competitor to PR Newswire" [^397^]
- Advises communicators on how to break through on LinkedIn — emphasizing authenticity and conversation
- Manages the intersection of algorithmic content distribution (AI) with editorial judgment
- Sat down with Jason Feifer (Editor-in-Chief, Entrepreneur Magazine) to discuss "What the Algorithm Really Wants" [^397^]

### 8.3 Strategic Importance

Her role is critical to LinkedIn's AI strategy because:
- LinkedIn's **collaborative articles** (AI-generated + human-edited) are a core AI product [^4^] [^7^]
- The **editorial team works with AI** to generate article topics and match them with expert contributors
- She manages the trust/authenticity balance as AI-generated content scales
- LinkedIn is "boosting authenticity & credibility" as a core platform objective [^397^]

### 8.4 Speaking & Media

- Interviewed by **PRWeek** on content strategy [^397^]
- Panel discussion with Entrepreneur Magazine Editor-in-Chief
- Regular media commentary on LinkedIn's content algorithm

---

## 9. Other Key AI Personnel

### 9.1 Trust, Safety & Responsible AI

| Name | Title | Focus | Background |
|------|-------|-------|------------|
| **Daniel Olmedilla** | Sr. Director, Trust/Responsible AI | Trust, privacy, responsible AI implementation | Two PhDs (Information Retrieval + AI/Agent-based Trust); ex-Meta (Ads, Reality Labs); 100+ publications, 3,000+ citations; advises European Commission [^414^] [^129^] |
| **Oscar Rodriguez** | VP Trust Product | Identity verification, fake account detection, trust signals | Leading verification efforts; 100M+ verified members; "Verified on LinkedIn" cross-platform trust [^88^] [^96^] |
| **James Verbus** | Staff ML Engineer, Anti-Abuse AI | Deep learning for abuse detection, AI developer productivity | PhD experimental particle astrophysics (Brown); ex-dark matter detector builder; pioneered DL for abusive sequence detection [^405^] [^406^] |
| **Grace Tang** | Senior Staff ML Engineer, Anti-Abuse | Unsupervised learning for abuse detection | Co-presented with Verbus at Fighting Abuse @Scale 2019 [^409^] |

### 9.2 Talent Solutions AI

| Name | Title | Focus | Background |
|------|-------|-------|------------|
| **Prashanthi Padmanabhan** | VP Engineering, Talent Solutions | Hiring Assistant, LinkedIn Recruiter, LinkedIn Learning | Ex-Yahoo, Verizon Media; 20+ years in tech; executive sponsor Women In Tech [^84^] [^85^] |
| **Daniel Hewlett** | Principal AI Engineer | AI tech lead for Hiring Assistant | Led Hiring Assistant development [^44^] |
| **Mark Lobosco** | Chief Business Officer (prev. VP Talent Solutions) | Go-to-market for talent AI products | 17+ years at LinkedIn; elevated to CBO Jan 2026 [^86^] [^87^] |

### 9.3 Product Management — AI

| Name | Title | Focus | Background |
|------|-------|-------|------------|
| **Keren Baruch** | Director of Product, GenAI Experiences | Generative AI experiences for flagship app, creator tools | Ex-Yahoo; 5+ years at LinkedIn; led creator strategy [^93^] [^94^] |
| **Lakshman Somasundaram** | Director of Product Management | Collaborative articles, AI content products | Led development of collaborative articles feature [^4^] |

### 9.4 Platform & Infrastructure

| Name | Title | Focus | Background |
|------|-------|-------|------------|
| **Prince Valluri** | Principal/Staff Engineer | AI-powered developer productivity, agent platform for 10,000+ engineers | 9+ years at LinkedIn specializing in developer productivity; tech lead for AI productivity initiatives [^68^] [^74^] |
| **Tim Jurka** | VP Engineering, AI & Data Science | Consumer platform AI, feed ranking, data engineering | Ex-Pulse (acquired 2013); BS CS, PhD Political Science UC Davis [^404^] [^408^] |

### 9.5 Research & Engineering — Core AI

| Name | Title | Focus | Background |
|------|-------|-------|------------|
| **Siyu Zhu** | Researcher (now at LinkedIn Core AI) | Agentic RL, travel planning (Planner-R1) | Co-author of Planner-R1 paper [^391^] |
| **Vignesh Kothapalli** | Senior ML Engineer (until 2025) | Foundation models for recommendation | Ex-IBM; MS NYU; now PhD Stanford; co-author Liger-Kernel [^67^] [^69^] |
| **Aman Gupta** | Staff/Principal Engineer | LLM alignment, reinforcement learning | Co-author AlphaPO, Planner-R1 [^391^] |
| **Shao Tang** | Researcher | LLM training, alignment | Co-author AlphaPO, Planner-R1 [^391^] |
| **Mingzhou Zhou** | Researcher/Engineer | Large-scale ranking systems | Co-author LiRank paper [^413^] |
| **Birjodh Tiwana** | Staff Engineer | Ranking, recommendations | Co-author LiRank, LiGNN [^413^] |

---

## 10. Org Chart Reconstruction

### 10.1 Simplified LinkedIn AI Org Structure (2025)

```
┌─────────────────────────────────────────────────────────────┐
│                    DEEPAK AGARWAL                           │
│                 Chief AI Officer (Jan 2025)                  │
│     Company-wide AI strategy, Core AI, Responsible AI       │
└───────────────────────┬─────────────────────────────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
┌───▼────┐      ┌──────▼──────┐     ┌─────▼─────┐
│ CORE AI │      │  PRODUCT AI  │     │ TRUST/RAI │
│  (FAIT) │      │             │     │           │
└───┬────┘      └──────┬──────┘     └─────┬─────┘
    │                  │                   │
    ▼                  ▼                   ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│Hamed     │    │Karthik       │    │Daniel        │
│Firooz    │    │Ramgopal (DE) │    │Olmedilla     │
│(Principal│    │GenAI Apps +  │    │(Sr. Dir)     │
│ Scientist)│   │Agent Platform│   │Responsible AI│
│360Brew   │    │Hiring Asst.  │    │James Verbus  │
│150B model│    │EON LLM       │    │(Staff MLE,   │
│          │    │              │    │Anti-Abuse)   │
├──────────┤    ├──────────────┤    ├──────────────┤
│Maziar    │    │Prashanthi    │    │Oscar         │
│Sanjabi   │    │Padmanabhan   │    │Rodriguez     │
│(Principal│    │(VP Eng,      │    │(VP Trust     │
│ Scientist)│   │Talent Sol.)  │    │Product)      │
│LLMs for  │    │Recruiter AI  │    │              │
│personal- │    │Learning AI   │    │              │
│ization   │    │              │    │              │
├──────────┤    ├──────────────┤    └──────────────┘
│Necip Fazil│   │Keren Baruch  │
│Ayan      │    │(Dir Product, │
│(Sr. Dir) │    │GenAI Exper.) │
│FAIT + KG │    │              │
├──────────┤    ├──────────────┤
│Sathiya   │    │Laura         │
│Keerthi   │    │Lorenzetti    │
│(Principal│    │(VP Product & │
│ Scientist)│   │Exec Editor)  │
│Distributed│   │Content + AI  │
│Training  │    │              │
├──────────┤    └──────────────┘
│Souvik    │
│Ghosh     │
│(Principal│
│Staff Eng)│
│RecSys,   │
│Probabilis-│
│tic ML    │
├──────────┤
│Fedor     │
│Borisyuk  │
│(Core     │
│Researcher)│
│LiRank,   │
│LiGNN     │
└──────────┘
```

### 10.2 Key Reporting Lines (Inferred)

- **Deepak Agarwal** reports to LinkedIn CEO (likely Ryan Roslansky) or CTO
- **Karthik Ramgopal** as Distinguished Engineer spans product engineering and AI — operates at VP-equivalent level with ~5,000 engineers in scope [^395^]
- **Tim Jurka** (VP Engineering, AI & Data Science) leads the data engineering and AI science teams that build the consumer platform [^404^]
- **Prashanthi Padmanabhan** leads Talent Solutions engineering (Hiring Assistant, Recruiter, Learning) [^84^]
- **Daniel Olmedilla** leads Trust/Responsible AI across the platform [^414^]
- **Laura Lorenzetti** bridges editorial and product for content AI [^397^]

---

## 11. New Hires and Openings

### 11.1 AI Roles in High Demand at LinkedIn

LinkedIn's own data shows **AI engineer** is the **fastest-growing job title** for young workers for the second consecutive year. [^392^] [^394^] Between 2023-2025, LinkedIn added **639,000 AI-related U.S. job postings**, including **75,000 for AI engineer roles**. [^392^]

### 11.2 Specific LinkedIn AI Openings

Based on job postings analysis, LinkedIn is actively hiring for:

**Staff AI Engineer** (Sunnyvale, San Francisco, Bellevue, NYC)
- Salary: $170,000 - $277,000
- Requirements: 4+ years ML/NLP, Java/Python, Spark, TensorFlow
- Responsibilities: Production ML models for newsfeed, "BIG data" at millions of samples scale
- Preferred: MS/PhD, GAI/LLM experience, publications at KDD/WWW/WSDM [^128^]

**AI Engineer/ML Engineer (Multiple Levels)**
- Building and deploying LLMs, AI agents, and automation systems
- Key skills sought: LangChain, RAG, PyTorch, MLOps [^394^]

### 11.3 Market Context

- LinkedIn itself is hiring entry-level AI talent across technology, financial services, defense, consulting, and academia
- Role variants: AI Specialist, Generative AI Engineer, Digital Content Creator [^392^]
- Geographic shift: hiring growth moving to smaller companies and non-metro areas; firms with 1-10 employees grew AI hiring **64%** between 2023-2025 [^392^]
- Companies are "just gorging on AI talent" — Kory Kantenga, Head of Economics, Americas at LinkedIn [^392^]

### 11.4 What This Means for LinkedIn's AI Team

LinkedIn must compete for AI talent against:
- **OpenAI** (poached Qingquan Song, Vignesh Kothapalli went to Stanford)
- **Meta** (has been aggressive in AI hiring)
- **Google DeepMind** (acquired Ya Xu)
- **xAI, Anthropic, and other AI labs**

LinkedIn's competitive advantages include:
- Massive proprietary data (Economic Graph, 1B+ members)
- Real-world AI impact at billion-user scale
- Agarwal's leadership and industry reputation
- AI-first platform strategy

---

## 12. Conference Appearances & Publications

### 12.1 Key Conference Presentations (2024-2025)

| Conference | Year | Speaker(s) | Topic | Source |
|------------|------|-----------|-------|--------|
| **AI Engineer World's Fair** | 2025 | Hamed Firooz, Maziar Sanjabi | 360Brew: LLM-based Personalized Ranking | [^138^] |
| **QCon AI New York** | 2025 | Karthik Ramgopal, Prince Valluri | Platform Teams Enabling AI - MCP/Multi-Agentic Tools | [^56^] |
| **InfoQ (podcast/talk)** | 2025 | Karthik Ramgopal, Prince Valluri | Platform Engineering for AI: Scaling Agents and MCP | [^59^] [^66^] |
| **InfoQ** | 2025 | Karthik Ramgopal, Daniel Hewlett | Lessons Learned from Building LinkedIn's First Agent | [^44^] |
| **HumanX** | 2026 | Deepak Agarwal | AI Platforms keynote | [^386^] |
| **KDD** | 2024 | Fedor Borisyuk et al. | LiRank: Best Paper Award (Applied Data Science) | [^15^] |
| **KDD** | 2024 | Fedor Borisyuk et al. | LiGNN: Best Paper Award (Applied Data Science) | [^15^] |
| **YouTube/Scale Events** | 2021 | James Verbus | Deep Learning to Detect Abusive Sequences | [^405^] [^382^] |
| **Fighting Abuse @Scale** | 2019 | Grace Tang, James Verbus | Preventing Abuse Using Unsupervised Learning | [^409^] |
| **QCon** (various) | 2024-2025 | Various LinkedIn engineers | ML systems scaling, agentic AI talks | [^58^] |

### 12.2 Key Academic Publications

| Paper | Venue | Authors | Year | Impact |
|-------|-------|---------|------|--------|
| **360Brew: A Decoder-only Foundation Model for Personalized Ranking and Recommendation** | arXiv (withdrawn) | Firooz, Sanjabi, Englhardt, Gupta, Ramgopal, Song, Xu, et al. | 2025 | 150B param model, 30+ tasks, 20x cost reduction |
| **LiRank: Industrial Large Scale Ranking Models at LinkedIn** | KDD 2024 | Borisyuk, Zhou, Song, Zhu, Tiwana, et al. (30+ authors) | 2024 | **Best Paper ADS**; +0.5% sessions, +1.76% jobs, +4.3% CTR |
| **LiGNN: Graph Neural Networks at LinkedIn** | KDD 2024 | Borisyuk, He, Ouyang, Ramezani, et al. | 2024 | **Best Paper ADS**; deployed GNN framework |
| **Planner-R1: Reward Shaping Enables Efficient Agentic RL** | arXiv | Zhu, Jiang, Song, He, Jain, Wang, Geramifard | 2025 | 56.9% TravelPlanner, 2.7x GPT-5; Song's last LinkedIn paper |
| **LinkedIn Post Embeddings** | CIKM 2023 | Various (Borisyuk et al. cited) | 2023 | Industrial scale embedding generation |
| **AlphaPO: Reward Shape Matters for LLM Alignment** | arXiv | Gupta, Tang, Song, Zhu, et al. | 2025 | Novel LLM alignment approach |

---

## 13. Talent Flow Analysis

### 13.1 Departures (2024-2025)

| Name | Role | Destination | Date | Impact |
|------|------|-------------|------|--------|
| **Ya Xu** | VP Engineering, Head of Data & AI | Google DeepMind (VP Eng) | Sep 2024 | **Critical** — Led 1,000-person org; strategic pivot point |
| **Qingquan Song** | Senior Staff ML Engineer | OpenAI (Researcher, Foundation Team) | 2025 | **High** — Core contributor LiRank, Planner-R1 author |
| **Vignesh Kothapalli** | Senior ML Engineer | Stanford PhD program | 2025 | **Medium** — Foundation model work; Liger-Kernel co-author |

### 13.2 Arrivals (2024-2025)

| Name | Role | Source | Date | Significance |
|------|------|--------|------|-------------|
| **Deepak Agarwal** | Chief AI Officer | Pinterest (CAIO) | Jan 2025 | **Transformative** — Veteran LinkedIn AI leader returns; 8 years prior as VP AI |

### 13.3 Internal Promotions/Mobility

| Name | Evolution | Significance |
|------|-----------|-------------|
| **Karthik Ramgopal** | Distinguished Engineer, expanded to GenAI platform + 5,000 engineers | Central architect of LinkedIn's AI agent strategy |
| **Daniel Hewlett** | Principal AI Engineer, AI tech lead for Hiring Assistant | Key technical leader for first production agent |
| **Prince Valluri** | Principal Engineer, AI productivity for 10,000+ engineers | Driving AI-powered developer productivity |
| **Oscar Rodriguez** | VP Trust Product, expanded verification to cross-platform trust signals | Critical for AI-era trust and authenticity |

### 13.4 Talent Pipeline Patterns

**LinkedIn AI as a talent feeder:**
- Multiple researchers have departed for **top AI labs** (OpenAI, DeepMind) and **PhD programs** (Stanford)
- Suggests LinkedIn AI is viewed as elite training ground for AI talent
- Risk of continued attrition to well-funded AI labs

**Competitive dynamics:**
- LinkedIn must compete with labs offering equity/research freedom
- Advantage: unique data assets (Economic Graph) and production scale
- Agarwal's return signals renewed investment in AI talent retention

---

## 14. Key Insights & Strategic Implications

### 14.1 The Agarwal Effect

Deepak Agarwal's return as CAIO represents LinkedIn's most significant AI leadership move in years. His prior 8-year tenure established much of the company's AI infrastructure, and his Pinterest experience scaling 200→1,000 engineers in an AI-first consumer platform directly applies to LinkedIn's current GenAI transformation. [^411^] [^2^]

### 14.2 The Agent Platform Strategy

LinkedIn is betting heavily on **AI agents** as its next paradigm:
- **Hiring Assistant** is the first production agent, with impressive metrics (69% higher InMail acceptance)
- **Agent platform** (foreground + background agents) being built for 10,000+ engineers
- **Spec-driven development** with sandboxed execution and human-in-the-loop governance
- Investment in **MCP (Model Context Protocol)** for tool interoperability

### 14.3 Foundation Models at Scale

**360Brew** represents a major technical bet:
- 150B parameters — among the largest industry-specific foundation models
- Trained on proprietary 1T-token LinkedIn engagement data
- Universal task solver eliminating need for task-specific fine-tuning
- If successfully deployed, could dramatically simplify LinkedIn's AI architecture

### 14.4 Trust as Differentiator

LinkedIn's emphasis on **Responsible AI** under Daniel Olmedilla and **Trust Product** under Oscar Rodriguez is strategically important:
- In hiring, trust failures have direct human impact
- Verification (100M+ members) creates competitive moat
- Anti-abuse AI (James Verbus, Grace Tang) protects platform integrity
- Agarwal's stated commitment to "ethical, inclusive, human-centric AI" signals cultural priority

### 14.5 Risks

1. **Talent attrition** — Continued departures to OpenAI, DeepMind, and academia threaten institutional knowledge
2. **Leadership transition** — Ya Xu's departure and Agarwal's arrival may cause organizational friction
3. **360Brew execution** — The model paper was withdrawn from arXiv; unclear production timeline
4. **Collaborative articles failure** — Product was sunset after mixed reception; signals GenAI product risk [^44^]
5. **Competition** — Google, Meta, and Microsoft all investing heavily in professional AI tools

### 14.6 What to Watch

- **Agarwal's org changes** — How will he restructure the AI organization he inherits from Ya Xu's era?
- **360Brew deployment** — Will the 150B model reach production or remain a research project?
- **Agent platform adoption** — How quickly will internal engineering teams adopt the agent platform?
- **New hires** — Is LinkedIn successfully attracting top AI talent post-Agarwal?
- **Conference presence** — Will LinkedIn increase its research publications and conference presence?

---

## Source Index

| Citation | Source | URL |
|----------|--------|-----|
| [^1^] | LinkedIn Post Embeddings (CIKM 2023) | arxiv.org |
| [^2^] | Deepak Agarwal YouTube Interview | youtube.com |
| [^3^] | Qingquan Song OpenReview | openreview.net |
| [^4^] | LinkedIn Collaborative Articles (Business Insider) | businessinsider.com |
| [^6^] | Qingquan Song ResearchGate | researchgate.net |
| [^7^] | LinkedIn Collaborative Articles Critique (Fortune) | fortune.com |
| [^8^] | Qingquan Song Personal Website | qingquansong.github.io |
| [^9^] | LinkedIn Hiring Assistant (ByteByteGo) | blog.bytebytego.com |
| [^13^] | 360Brew Talk (YouTube) | youtube.com |
| [^15^] | KDD 2024 Awards | kdd2024.kdd.org |
| [^41^] | Craig Martell Wikipedia | wikipedia.org |
| [^44^] | LinkedIn Hiring Assistant (InfoQ) | infoq.com |
| [^45^] | Souvik Ghosh (AI Council) | aicouncil.com |
| [^49^] | LinkedIn GenAI Tech Stack (ByteByteGo) | blog.bytebytego.com |
| [^50^] | Craig Martell SF ELC Speaker | sfelc.com |
| [^51^] | Craig Martell Wikipedia (updated) | wikipedia.org |
| [^56^] | QCon AI LinkedIn Platform (InfoQ) | infoq.com |
| [^57^] | Ya Xu (Women Who Code) | womenwhocode.com |
| [^58^] | QCon Takeaways 2024 (InfoQ) | infoq.com |
| [^59^] | InfoQ Podcasts | infoq.com |
| [^60^] | Sathiya Keerthi Website | keerthis.com |
| [^63^] | Ya Xu Blind Discussion | teamblind.com |
| [^66^] | Platform Engineering Podcast (InfoQ) | infoq.com |
| [^67^] | Vignesh Kothapalli OpenReview | openreview.net |
| [^68^] | Prince Valluri QCon Speaker | ai.qconferences.com |
| [^70^] | Necip Fazil Ayan (The Org) | theorg.com |
| [^78^] | Sathiya Keerthi OpenReview | openreview.net |
| [^79^] | LinkedIn Hiring Assistant Case Study | zenml.io |
| [^80^] | LinkedIn Hiring Assistant (InfoQ talk) | infoq.com |
| [^84^] | Prashanthi Padmanabhan Interview | hrtechnologyinsights.com |
| [^85^] | LinkedIn AI Hiring Agent (LeadDev) | leaddev.com |
| [^86^] | Mark Lobosco CBO Announcement | exchange4media.com |
| [^88^] | Oscar Rodriguez Trust Interview | helpnetsecurity.com |
| [^93^] | Keren Baruch Interview | hiretechladies.com |
| [^96^] | Oscar Rodriguez Fake Accounts (Adweek) | adweek.com |
| [^122^] | LinkedIn Appoints Agarwal (CDO Magazine) | cdomagazine.tech |
| [^127^] | Agarwal YouTube Interview | youtube.com |
| [^128^] | LinkedIn Staff AI Engineer Job | smartrecruiters.com |
| [^129^] | Daniel Olmedilla About Me | olmedilla.info |
| [^138^] | 360Brew Talk (YouTube) | youtube.com |
| [^147^] | 360Brew Paper (arXiv) | arxiv.org |
| [^154^] | Ya Xu CNA Interview | cnalifestyle.channelnewsasia.com |
| [^155^] | Ya Xu McKinsey Interview | mckinsey.com |
| [^159^] | Ya Xu Blind Post | teamblind.com |
| [^385^] | PR Week Dashboard 25 | prweek.com |
| [^386^] | HumanX Speaker Page | humanx.co |
| [^391^] | Planner-R1 Paper | arxiv.org |
| [^392^] | LinkedIn AI Fastest-Growing Role | letsdatascience.com |
| [^393^] | LinkedIn Hiring Assistant InfoQ | infoq.com |
| [^394^] | LinkedIn AI Jobs (ZDNet) | zdnet.com |
| [^395^] | Karthik Ramgopal QCon Speaker | qconlondon.com |
| [^397^] | Laura Lorenzetti (FoLD Substack) | liamdarmody.substack.com |
| [^404^] | Tim Jurka Crunchbase | crunchbase.com |
| [^405^] | James Verbus YouTube Talk | youtube.com |
| [^406^] | James Verbus Podcast | youtube.com |
| [^407^] | Hamed Firooz Personal Website | firooz.us |
| [^409^] | Fighting Abuse @Scale 2019 | engineering.fb.com |
| [^411^] | Deepak Agarwal (AI Magazine) | aimagazine.com |
| [^412^] | Agarwal Appointment (National CIO Review) | nationalcioreview.com |
| [^413^] | LiRank Paper (arXiv) | arxiv.org |
| [^414^] | Daniel Olmedilla Website | olmedilla.info |
| [^417^] | LiRank (ACM DL) | dl.acm.org |

---

*Document compiled from 20+ independent searches across web, academic databases, conference proceedings, and industry publications. All claims cited inline.*
