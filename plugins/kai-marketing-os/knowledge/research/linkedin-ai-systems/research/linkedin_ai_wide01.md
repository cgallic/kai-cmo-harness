# Facet: Patent & IP Landscape -- LinkedIn AI/ML Systems

## Research Metadata
- **Research Date**: June 2025
- **Researcher**: Patent & IP Research Agent
- **Searches Conducted**: 15+ independent queries across USPTO, Google Patents, Justia, arXiv, and web sources
- **Total Patents Identified**: 40+ relevant patents and applications
- **Confidence Levels**: High (verified patent documents), Medium (published applications), Lower (indirect attribution)

---

## Key Findings

1. **LinkedIn holds 4,500+ patents** assigned to LinkedIn Corporation, with Microsoft Technology Licensing LLC now listed as assignee post-acquisition [^8^][^96^]. The patent portfolio spans graph databases, machine learning, recommendation systems, anti-abuse infrastructure, and NLP.

2. **Feed ranking is a core IP area**: LinkedIn filed patents covering learning-to-rank models (US9626654B2), sequential recommenders (Feed-SR, arXiv 2026), and GLMix-based job recommendation systems [^12^][^194^].

3. **Graph-based recommendations are foundational**: US10387788B2 ("Graph based techniques for predicting results") and the LiGNN paper (arXiv 2024) represent LinkedIn's core graph neural network IP for recommendations [^193^][^107^].

4. **Anti-abuse and trust & safety patents exist but are limited in public filings**: LinkedIn has filed patents for "Escalation-compatible processing flows for anti-abuse infrastructures" and "Automatically detecting and managing anomalies in statistical models" [^8^][^132^].

5. **No directly identified patents specifically for "AI slop" detection**: LinkedIn's "AI solving AI" approach to detect AI-generated content appears to be a trade secret or very recent unpublished work, not yet visible in public patent filings [^1^][^18^].

6. **Microsoft patent families overlap**: Post-acquisition (2016), many LinkedIn patents were reassigned to Microsoft Technology Licensing LLC, creating joint patent families [^193^][^194^].

---

## Patents by Category

### 1. Content Ranking & Feed Algorithms

#### US9626654B2 - "Learning a ranking model using interactions of a user with a jobs list"
- **Inventors**: Lijun Tang, Eric Huang, Xu Miao, Yitong Zhou, David Hardtke, Joel Daniel Young
- **Assignee**: LinkedIn Corporation (now Microsoft Technology Licensing LLC)
- **Filed**: June 30, 2015 | **Granted**: April 18, 2017
- **Abstract**: "A learning to rank model can learn from pairwise preference (e.g., job posting A is more relevant than job posting B for a particular member profile) thus directly optimizing for the rank order of job postings for each member profile. With ranking position taken into consideration during training, top-ranked job postings may be treated by a recommendation system as being of more importance than lower-ranked job postings."
- **URL**: https://patents.google.com/patent/US9626654B2
- **Confidence**: High

#### Feed Sequential Recommender (Feed-SR) - arXiv:2602.12354
- **Authors**: Lars Hertel, Gaurav Srivastava, Syed Ali Naqvi, Satyam Kumar, Yue Zhang, Borja Ocejo, Benjamin Zelditch, Adrian Englhardt, Hailing Cheng, Andy Hu, Antonio Alonso, Daming Li, Siddharth Dangi, Chen Zhu, Mingzhou Zhou, Wanning Li, Tao Huang, Fedor Borisyuk, Ganesh Parameswaran, Birjodh Singh Tiwana, Sriram Sankar, Qing Lan, Julie Choi, Souvik Ghosh
- **Publication**: February 12, 2026
- **Abstract**: "Feed Sequential Recommender (Feed-SR), a transformer-based sequential ranking model for LinkedIn Feed that replaces a DCNv2-based ranker and meets strict production constraints... Feed-SR is currently the primary member experience on LinkedIn's Feed and shows significant improvements in member engagement (+2.10% time spent) in online A/B tests."
- **URL**: https://arxiv.org/abs/2602.12354
- **Confidence**: High (published research paper, not patent)

#### US9247015B2 - "Methods and systems for recommending a context based on content interaction"
- **Inventor**: Jennifer Granito Ruffner
- **Assignee**: LinkedIn Corporation
- **Filed**: March 28, 2013 | **Granted**: January 26, 2016
- **Abstract**: Storing content items and recommending contexts based on content interactions within an online social networking system.
- **URL**: https://patents.google.com/patent/US9247015B2
- **Confidence**: High

#### US9411858B2 - "Methods and apparatus for targeting communications using social network metrics"
- **Inventor**: Brian Lawler
- **Assignee**: LinkedIn Corporation
- **Priority**: 2004-04-07 | **Granted**: August 9, 2016
- **Abstract**: Delivering electronic communications based on social network metrics to target relevant communications.
- **URL**: https://patents.google.com/patent/US9411858B2
- **Confidence**: High

---

### 2. AI Content Detection (Anti-Slop)

**Note**: LinkedIn's "AI solving AI" approach to detect AI-generated "slop" content, as described by VP Laura Lorenzetti, appears to be primarily trade secret or very recent work not yet visible in public patent filings. However, related patents exist:

#### US9176957B2 - "Selective fact checking method and system"
- **Inventor**: Lucas J. Myslinski
- **Assignee**: LinkedIn Corporation
- **Filed**: February 11, 2013 | **Granted**: November 3, 2015
- **Abstract**: Automatically detecting keywords and causing real-time fact-checking results to be presented, comparing searchable information with multiple sources.
- **URL**: https://patents.google.com/patent/US9176957B2
- **Confidence**: High

#### US9015037B2 - "Interactive fact checking system"
- **Inventor**: Lucas J. Myslinski
- **Assignee**: LinkedIn Corporation
- **Filed**: February 11, 2013 | **Granted**: April 21, 2015
- **Abstract**: Device for fact-checking information with reliability ratings for sources.
- **URL**: https://patents.google.com/patent/US9015037B2
- **Confidence**: High

#### US9483159B2 - "Fact checking graphical user interface including fact checking icons"
- **Inventor**: Lucas J. Myslinski
- **Assignee**: LinkedIn Corporation
- **Filed**: February 11, 2013 | **Granted**: November 1, 2016
- **Abstract**: GUI for fact checking with reliability ratings and source selection.
- **URL**: https://patents.google.com/patent/US9483159B2
- **Confidence**: High

#### Microsoft Synthetic Media Detection Patent (Related)
- **Title**: "Synthetic Media Detection and Management of Trust Notifications"
- **Assignee**: Microsoft (LinkedIn parent)
- **Filed**: 2022
- **Note**: Microsoft filed early synthesis detection patents, introducing confidence-scored AI detection embedded into presentation software [^68^].
- **Confidence**: Medium

---

### 3. Job Recommendation Systems

#### US9811569B2 - "Suggesting candidate profiles similar to a reference profile"
- **Inventors**: Christian Posse, Abhishek Gupta, Anmol Bhasin, Monica Rogati
- **Assignee**: LinkedIn Corporation (now Microsoft Technology Licensing LLC)
- **Priority**: July 29, 2011 | **Granted**: November 7, 2017
- **Abstract**: "A general recommendation engine is used to extract features from member profiles, and then store the extracted features, including any computed, derived or retrieved profile features, in an enhanced member profile. In real-time, the general recommendation engine processes client requests to identify member profiles similar to a source member profile by comparing select profile features stored in the enhanced member profile with corresponding profile features of the source member profile, where the comparison results in several similarity sub-scores that are then combined."
- **URL**: https://patents.google.com/patent/US9811569B2
- **Cited by**: 78 subsequent patents
- **Confidence**: High

#### US9438689B2 - "Method and system to determine a member profile associated with a reference"
- **Inventor**: Anand R. Iyer
- **Assignee**: LinkedIn Corporation
- **Filed**: September 23, 2014 | **Granted**: September 6, 2016
- **Abstract**: Ranking module determines rank of name entities corresponding to members of an online social networking system.
- **URL**: https://patents.google.com/patent/US9438689B2
- **Confidence**: High

#### GLMix (Generalized Linear Mixed Models) - RecSys 2014/2017
- **Authors**: LinkedIn Engineering (Xianren Wu et al.)
- **Publication**: RecSys 2014, 2017
- **Abstract**: Large-scale generalized linear mixed models containing millions of parameters. "The global regression coefficients act as our prior prediction given a member profile and job posting. The posterior is estimated through fitting the per-member and per-job regression coefficients... Deploying the GLMix model increased job applications by 20% to 40% per day." [^11^]
- **Confidence**: High (published research)

#### US10540683B2 - "Machine-learned recommender system for performance optimization"
- **Inventor**: Huiji Gao
- **Assignee**: Microsoft Technology Licensing LLC (LinkedIn origin)
- **Filed**: April 24, 2017 | **Granted**: January 21, 2020
- **Abstract**: Machine-learned recommender system for performance optimization of network-based applications, with recommendations identifying how much to modify particular feature values.
- **URL**: https://patents.google.com/patent/US10540683B2
- **Confidence**: High

#### US10380500B2 - "Version control for asynchronous distributed machine learning"
- **Inventor**: Xu Miao
- **Assignee**: Microsoft Technology Licensing LLC (LinkedIn origin)
- **Filed**: September 24, 2015 | **Granted**: August 13, 2019
- **Abstract**: Version control system for distributed machine learning, with client generating recommendations based on aggregated training data and user input during a job search session.
- **URL**: https://patents.google.com/patent/US10380500B2
- **Confidence**: High

---

### 4. Graph-Based Recommendations

#### US10387788B2 - "Graph based techniques for predicting results"
- **Inventors**: Qiang Zhu, John Chao, Qingbo Hu
- **Assignee**: LinkedIn Corporation (now Microsoft Technology Licensing LLC)
- **Filed**: February 18, 2016 | **Granted**: August 20, 2019
- **Abstract**: "Techniques are provided for determining predicted results for entities based on relatedness of the entities in a graph of nodes... A node in the graph of nodes represents an entity, and nodes representing entities with known results are assigned those results as their respective node values. The assigned node values are then propagated between the neighboring nodes throughout the graph of nodes in the amount determined by the relatedness of the nodes."
- **URL**: https://patents.google.com/patent/US10387788B2
- **Cited by**: 10 subsequent patents
- **Confidence**: High

#### LiGNN: Graph Neural Networks at LinkedIn - arXiv:2402.11139
- **Authors**: LinkedIn Engineering Team
- **Publication**: February 2024
- **Abstract**: "LiGNN" is LinkedIn's production Graph Neural Network framework deployed at scale for recommendations. Covers GNN modeling, training stability, near-line inference, and deployment lessons.
- **URL**: https://arxiv.org/abs/2402.11139
- **Confidence**: High (published research paper)

#### "Real-time graph traversals for network-based recommendations" (Application 20190384861)
- **Application Number**: US20190384861A1
- **Assignee**: LinkedIn Corporation
- **Filed**: December 19, 2019
- **Abstract**: Real-time traversal of graph databases for generating network-based recommendations.
- **Note**: Identified via Justia patent listing [^8^]
- **Confidence**: Medium (application only)

#### US10675534B2 - "Friend recommendation system"
- **Inventor**: Kevin A. Lee
- **Assignee**: LinkedIn Corporation
- **Filed**: April 29, 2019 | **Granted**: June 9, 2020
- **Abstract**: Optimized friend recommendation system for social networks.
- **URL**: https://patents.justia.com/patent/10675534
- **Confidence**: High

---

### 5. NLP & Content Understanding

#### US8805845B1 - "Framework for large-scale multi-label classification"
- **Inventor**: Liyun Li
- **Assignee**: LinkedIn Corporation
- **Filed**: July 31, 2013 | **Granted**: August 12, 2014
- **Abstract**: "A framework for large-scale multi-label classification of an electronic document. An example multi-label classification system is configured to first apply weak classifiers and identify seed labels, then determine additional labels based on the seed labels and label correlation data."
- **URL**: https://patents.google.com/patent/US8805845B1
- **Confidence**: High

#### DeText: Deep Text Ranking Framework with BERT - CIKM 2020
- **Authors**: LinkedIn Engineering (Weiwei Guo et al.)
- **Publication**: October 19, 2020
- **Abstract**: "DeText is a general ranking framework that can be applied to various ranking productions." Uses BERT-based ranking for industry search systems. Open-sourced by LinkedIn.
- **URL**: https://dl.acm.org/doi/10.1145/3340531.3412699
- **Confidence**: High (published research)

#### LiBERT: Deep NLP for LinkedIn Search - arXiv:2108.08252
- **Authors**: Weiwei Guo, Xiaowei Liu, Sida Wang, Michael Kazi, Zhiwei Wang, Zhoutong Fu, Jun Jia, Liang Zhang, Huiji Gao, Bo Long
- **Publication**: July 30, 2021
- **Abstract**: "We introduce a comprehensive study of applying deep NLP techniques to five representative tasks in search engines... this work builds on existing efforts of LinkedIn search, and is tested at scale on a commercial search engine."
- **URL**: https://arxiv.org/abs/2108.08252
- **Confidence**: High (published research)

#### Deep Natural Language Processing for LinkedIn Search Systems (Extended) - arXiv:2108.13300
- **Authors**: Same team as LiBERT
- **Abstract**: "Our goal is to pre-train a BERT model on LinkedIn data (hence the name LiBERT)." Covers query intent prediction, query tagging, document ranking, auto-completion, and query suggestion.
- **URL**: https://arxiv.org/pdf/2108.13300
- **Confidence**: High

#### 360Brew Foundation Model
- **Description**: LinkedIn's proprietary 150-billion-parameter foundation model (referenced in marketing/technical materials, not a patent filing). Used for semantic understanding, content ranking, and member profiling. Cross-references posts with profile headlines and work history.
- **Sources**: LinkedIn engineering blog, TrustInsights analysis [^37^][^90^]
- **Confidence**: Medium (public references exist, but specific patent filings not identified)

---

### 6. Trust & Safety / Anti-Abuse

#### "Escalation-compatible processing flows for anti-abuse infrastructures"
- **Publication Number**: US20180349606A1
- **Assignee**: LinkedIn Corporation
- **Abstract**: "The disclosed embodiments provide a system for escalation-compatible processing flows for anti-abuse infrastructures."
- **Note**: Identified via Justia patent listing [^8^][^132^]
- **Confidence**: Medium

#### "Automatically detecting and managing anomalies in statistical models"
- **Publication Number**: US20190102361A1 (Application 15/721,359)
- **Inventors**: Ajith Muralidharan, Y Ma, F Raudies, Y Zhen
- **Assignee**: LinkedIn Corporation
- **Filed**: September 29, 2017 | **Published**: April 4, 2019
- **Abstract**: System for automatically detecting and managing anomalies in statistical models deployed in production systems.
- **URL**: https://patents.justia.com/assignee/linkedin-corporation
- **Confidence**: Medium (application)

#### "Automatic feature profiling and anomaly detection"
- **Assignee**: LinkedIn Corporation
- **Abstract**: Automatic profiling of features and detection of anomalies in data pipelines.
- **Note**: Identified via Justia patent listing [^8^]
- **Confidence**: Medium

#### LinkedIn's Isolation Forest Approach (Research Publication)
- **Source**: "Benchmarking Anomaly Detection Algorithms" (arXiv:2402.07281)
- **Quote**: "LinkedIn, for instance, still finds Isolation Forest based method to be quite effective in detecting various forms of abuse (modeled as anomalies) in their portal."
- **URL**: https://arxiv.org/html/2402.07281v3
- **Confidence**: High (referenced in published research)

---

### 7. Search & Information Retrieval

#### US8751940B2 - "Displaying a preference by a user of a content contribution"
- **Inventor**: R. Kevin Rose
- **Assignee**: LinkedIn Corporation
- **Priority**: 2006-06-22 | **Granted**: June 10, 2014
- **Abstract**: Detecting preference events, storing detected events, and responding to client queries for content recommendations.
- **URL**: https://patents.google.com/patent/US8751940B2
- **Confidence**: High

#### US9137275B2 - "Recording and indicating preferences"
- **Inventor**: R. Kevin Rose
- **Assignee**: LinkedIn Corporation
- **Priority**: 2006-06-22 | **Granted**: September 15, 2015
- **Abstract**: Recording user preferences for content contributions with single-action preference event detection.
- **URL**: https://patents.google.com/patent/US9137275B2
- **Confidence**: High

#### US8943138B2 - "Altering logical groups based on loneliness"
- **Inventor**: Vincent Mallet
- **Assignee**: LinkedIn Corporation
- **Priority**: 2011-03-23 | **Granted**: January 27, 2015
- **Abstract**: Systems and methods for adding users to logical groups based on relationship information and "loneliness" metrics.
- **URL**: https://patents.google.com/patent/US8943138B2
- **Confidence**: High

#### LinkedIn's Unified Retrieval System (2024-2025)
- **Description**: LLM-powered unified retrieval system replacing patchwork of separate systems (trending content lists, collaborative filtering, keyword matching, geography-based signals). Uses fine-tuned LLMs to convert posts and member profiles into semantic embeddings.
- **Sources**: LinkedIn engineering blog, TrustInsights analysis [^10^][^37^]
- **Confidence**: High (confirmed by LinkedIn engineering blog)

---

### 8. Collaborative Filtering & Embeddings

#### US8805845B1 - "Framework for large-scale multi-label classification" (also listed in NLP)
- **Inventor**: Liyun Li
- **Assignee**: LinkedIn Corporation
- **Filed**: July 31, 2013 | **Granted**: August 12, 2014
- **Abstract**: Multi-label classification using weak classifiers and label correlation data for content understanding and tagging.
- **URL**: https://patents.google.com/patent/US8805845B1
- **Confidence**: High

#### US9306998B2 - "Content sharing via social networking"
- **Inventor**: Bill Nguyen
- **Assignee**: LinkedIn Corporation
- **Priority**: 2011-09-21 | **Granted**: April 5, 2016
- **Abstract**: Systems and methods for content sharing via social networking, detecting device availability and identifying user devices via associations.
- **URL**: https://patents.google.com/patent/US9306998B2
- **Confidence**: High

#### "Online hyperparameter tuning in distributed machine learning"
- **Patent Number**: US10,380,500 (2019); US10,592,535
- **Inventors**: Ian Wood B., Xu Miao, Chang-Ming Tsai, Joel Young D.
- **Assignee**: LinkedIn Corporation
- **Abstract**: Online hyperparameter tuning system for distributed machine learning pipelines at scale.
- **Sources**: [^133^][^134^]
- **Confidence**: High

#### "Characterizing model performance using hierarchical feature groups"
- **Assignee**: LinkedIn Corporation
- **Abstract**: Techniques for hierarchical feature grouping to characterize and monitor ML model performance.
- **Note**: Identified via Justia patent listing [^8^]
- **Confidence**: Medium

---

### 9. Additional Notable Patents

#### "Aggregating member features into company-level insights for data analytics"
- **Assignee**: LinkedIn Corporation
- **Abstract**: Techniques for aggregating individual member features into company-level analytical insights.
- **Note**: Identified via Justia patent listing [^8^]
- **Confidence**: Medium

#### "Model-based assessment and improvement of relationships"
- **Assignee**: LinkedIn Corporation
- **Abstract**: Using statistical models to assess and improve professional relationship recommendations.
- **Note**: Identified via Justia patent listing [^8^]
- **Confidence**: Medium

#### "Learner engagement in online discussions"
- **Assignee**: LinkedIn Corporation
- **Abstract**: Measuring and predicting learner engagement in online educational discussions (LinkedIn Learning context).
- **Note**: Identified via Justia patent listing [^8^]
- **Confidence**: Medium

#### "Model-based routing and prioritization of customer support tickets"
- **Assignee**: LinkedIn Corporation
- **Abstract**: Using ML models to route and prioritize customer support tickets.
- **Note**: Identified via Justia patent listing [^8^]
- **Confidence**: Medium

#### "Centralized feature management, monitoring and onboarding"
- **Assignee**: LinkedIn Corporation
- **Abstract**: Centralized system for managing, monitoring, and onboarding ML features across products.
- **Note**: Identified via Justia patent listing [^8^]
- **Confidence**: Medium

---

## Major Players & Inventors

| Name | Role/Relevance |
|------|---------------|
| **Christian Posse** | Former LinkedIn Chief Data Officer; inventor on US9811569B2 (similar profile recommendations); foundational recommendation architecture |
| **Monica Rogati** | Former LinkedIn Data Science VP; inventor on US9811569B2; now AI advisor/investor |
| **Anmol Bhasin** | Former LinkedIn Engineering Director; inventor on US9811569B2; recommendation systems leader |
| **Qiang Zhu** | LinkedIn Staff Engineer; inventor on US10387788B2 (graph-based predictions) and anti-abuse anomaly detection patents |
| **John Chao** | LinkedIn Engineer; co-inventor on US10387788B2 graph patent |
| **Xu Miao** | LinkedIn/MS Engineer; inventor on distributed ML version control (US10380500B2) and hyperparameter tuning patents |
| **Huiji Gao** | LinkedIn Senior Staff Engineer; author on LiGNN paper and ML recommender patent (US10540683B2) |
| **Weiwei Guo** | LinkedIn Research Scientist; lead author on DeText and LiBERT NLP papers |
| **Bo Long** | LinkedIn Distinguished Engineer; co-author on deep NLP for LinkedIn search |
| **Souvik Ghosh** | LinkedIn Staff Research Scientist; author on LiGNN and graph recommendation research |
| **Lars Hertel** | LinkedIn Staff Machine Learning Engineer; lead author on Feed-SR paper |
| **Laura Lorenzetti** | VP of Product & Executive Editor at LinkedIn; public spokesperson for AI slop detection (not inventor) |

---

## Trends & Signals

1. **Shift from Traditional ML to Transformers**: LinkedIn's feed ranking evolved from DCNv2-based rankers to transformer-based sequential models (Feed-SR) between 2024-2026 [^12^].

2. **Semantic/LLM-Powered Retrieval**: LinkedIn replaced patchwork retrieval systems with unified LLM-powered semantic retrieval using fine-tuned language models and embeddings [^10^].

3. **Graph Neural Networks at Scale**: LiGNN represents LinkedIn's deployment of GNNs for recommendation at billion-member scale, with artificial nearest-neighbor edges for cold-start nodes [^107^].

4. **Microsoft Patent Consolidation**: Post-acquisition (2016), LinkedIn patents are increasingly assigned to Microsoft Technology Licensing LLC, making them harder to identify as "LinkedIn" patents in isolation [^193^][^194^].

5. **AI Slop Detection Gap**: Despite significant public discussion of LinkedIn's "AI solving AI" approach, no specific patents have been publicly filed for AI-generated content detection as of the research date. This suggests either trade secret protection or very recent filings not yet published [^1^][^18^].

6. **Open Research, Closed Patents**: LinkedIn publishes extensive research papers (Feed-SR, LiGNN, DeText, LiBERT) but the corresponding production systems may have additional unpublished patent filings [^12^][^114^].

7. **Isolation Forest for Abuse Detection**: Despite industry trend toward deep learning for anomaly detection, LinkedIn continues to find Isolation Forest methods effective for abuse detection [^213^].

---

## Controversies & Conflicting Claims

1. **360Brew Misinformation**: Significant online misinformation claims LinkedIn deployed a 150B-parameter unified "super-model" called 360Brew in the feed. LinkedIn has NOT confirmed this in engineering blog posts; 360Brew exists as a research foundation model but its deployment scope is unverified [^10^].

2. **Bascom Research Patent Litigation**: LinkedIn was sued by Bascom Research LLC for allegedly infringing patents related to social graph APIs and link directories. The case was ultimately dismissed but highlights ongoing patent risk in social networking technology [^65^].

3. **Patent vs. Trade Secret for AI Detection**: LinkedIn's most-publicized recent AI work (AI slop detection) does not appear in patent filings, suggesting either intentional trade secret protection or that the technology is too new for publication (patent applications typically publish 18 months after filing) [^1^][^18^].

4. **hiQ Labs v. LinkedIn**: Landmark case establishing LinkedIn's right to control data scraping of its platform, with implications for AI model training data sources [^71^].

---

## Recommended Deep-Dive Areas

| Area | Why It Warrants Depth |
|------|----------------------|
| **Feed-SR Patent Filings** | Transformer-based sequential recommender is now primary feed ranking system; any patent filings would be highly valuable and recent |
| **360Brew Foundation Model** | 150B-parameter model; if patented, would represent LinkedIn's most significant AI IP; needs direct USPTO filing search |
| **AI Slop Detection Systems** | Active "AI solving AI" classifiers trained on human-annotated data; likely either trade secret or unpublished applications |
| **LiGNN Patent Family** | Production GNN framework at scale; any patent filings around graph neural network architecture would be foundational |
| **DeText/LiBERT Patent Family** | Deep NLP ranking frameworks; potential patent overlap with BERT/Google IP needs investigation |
| **Anti-Abuse Infrastructure** | "Escalation-compatible processing flows" patent application suggests sophisticated abuse detection pipeline |
| **GLMix Patent Family** | Generalized Linear Mixed Models for job recommendations cited as increasing applications 20-40% |
| **Microsoft Cross-Licensing** | Post-acquisition patent reassignment means many "LinkedIn" innovations now appear under Microsoft Technology Licensing LLC |

---

## Search Sources & Methodology

- **Google Patents**: https://patents.google.com/?assignee=LinkedIn+Corporation
- **Justia Patents**: https://patents.justia.com/company/linkedin
- **USPTO Patent Center**: https://patentcenter.uspto.gov
- **arXiv**: LinkedIn-authored papers on feed ranking, GNNs, NLP
- **ACM Digital Library**: DeText (CIKM 2020), RecSys papers
- **LinkedIn Engineering Blog**: Confirmed system architecture details
- **TrustInsights Analysis**: Unofficial LinkedIn algorithm guide based on engineering papers

---

*Research compiled through systematic searches across patent databases, academic literature, and technical publications. Patent information is current as of research date; new applications may have been filed since.*
