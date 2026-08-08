# Dimension 1: LinkedIn 360Brew Foundation Model - Deep Dive Research

## Research Summary

This document presents a comprehensive analysis of LinkedIn's 360Brew foundation model, a 150-billion-parameter decoder-only model for personalized ranking and recommendation. The research synthesizes findings from the withdrawn arXiv paper (2501.16450), the Feed-SR production paper (2602.12354), the LLM-based retrieval paper (2510.14223), the official LinkedIn Engineering blog post (March 12, 2026), and numerous secondary sources. A critical finding: **the 360Brew LLM-Ranker was evaluated and explicitly rejected for the production LinkedIn Feed**, which instead uses a hybrid architecture combining an LLaMA-3-based retrieval system with a separate sequential recommender (Feed-SR/GR).

---

## 1. Paper Details and Publication History

### Finding 1.1: Paper Identity and Authors

- **Claim**: The 360Brew paper was published on arXiv as "360Brew: A Decoder-only Foundation Model for Personalized Ranking and Recommendation" with arXiv ID 2501.16450.
- **Source**: arXiv.org
- **URL**: https://arxiv.org/abs/2501.16450
- **Date**: January 27, 2025 (v1)
- **Excerpt**: "We introduce our research pre-production model, 360Brew V1.0, a 150B parameter, decoder-only model that has been trained and fine-tuned on LinkedIn's data and tasks."
- **Context**: 23 authors from LinkedIn's Foundation AI Technologies (FAIT) team
- **Confidence**: High

**Full Author List (23 authors)**:
Hamed Firooz, Maziar Sanjabi, Adrian Englhardt, Aman Gupta, Ben Levine, Dre Olgiati, Gungor Polatkan, Iuliia Melnychuk, Karthik Ramgopal, Kirill Talanine, Kutta Srinivasan, Luke Simon, Natesh Sivasubramoniapillai, Necip Fazil Ayan, Qingquan Song, Samira Sriram, Souvik Ghosh, Tao Song, Vignesh Kothapalli, Xiaoling Zhai, Ya Xu, Yu Wang, Yun Dai

- **Corresponding Authors**: Maziar Sanjabi, Hamed Firooz
- **Team**: Foundation AI Technologies (FAIT), LinkedIn

### Finding 1.2: Paper Withdrawal

- **Claim**: The 360Brew paper was withdrawn by arXiv administrators on August 23, 2025 (v4), with the official note: "This version has been removed by arXiv administrators as the submitter did not have the right to agree to the license at submission."
- **Source**: arXiv.org admin note
- **URL**: https://arxiv.org/abs/2501.16450
- **Date**: August 23, 2025 (withdrawal date)
- **Excerpt**: "arXiv admin note: This version has been removed by arXiv administrators as the submitter did not have the right to agree to the license at submission."
- **Context**: The paper went through 4 versions (v1: Jan 27, v2: Feb 1, v3: Feb 7, v4: Aug 23) before all were withdrawn. Each version was approximately 1,900 KB. The withdrawal reason suggests corporate IP/approval issues rather than academic concerns.
- **Confidence**: High

### Finding 1.3: Paper Mirror Availability

- **Claim**: Despite withdrawal from arXiv, the full paper remains accessible through ar5iv.org mirror and has been widely archived.
- **Source**: ar5iv.org
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: Accessed during research (still available)
- **Excerpt**: Full HTML version of the paper including all figures, tables, and technical content is preserved.
- **Context**: The paper is also cited in at least 3 other arXiv papers (the Feed-SR paper 2602.12354, the retrieval paper 2510.14223, and TrustInsights analysis), ensuring its content is permanently part of the academic record.
- **Confidence**: High

### Finding 1.4: Paper Classification

- **Claim**: The paper explicitly states 360Brew is a "pre-production model" and "research" project, not a deployed production system.
- **Source**: arXiv 2501.16450 (ar5iv mirror)
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "We introduce our research on our pre-production model, 360Brew V1.0, developed by a small team of researchers and engineers over a 9-month period."
- **Context**: Multiple references to "More details to come soon" in the paper suggest it was published before full development was complete. The paper explicitly focuses on ranking tasks, not retrieval.
- **Confidence**: High

---

## 2. Training Methodology

### Finding 2.1: Base Architecture

- **Claim**: 360Brew V1.0 is built on top of the Mixtral 8x22B pre-trained Mixture of Experts (MoE) architecture, not LLaMA 3 as commonly reported in secondary sources.
- **Source**: arXiv 2501.16450 Section 2.2
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "The 360Brew model V1.0 is built on top of Mixtral 8x22 pre-trained MoE architecture."
- **Context**: The Mixtral 8x22B architecture uses 8 expert groups each with 22B parameters, totaling ~141B parameters with ~39B active parameters per token. Secondary sources often incorrectly state LLaMA 3 as the base; this appears to be conflation with the separate retrieval system (which does use LLaMA 3).
- **Confidence**: High

### Finding 2.2: Training Data

- **Claim**: The model was trained and fine-tuned on LinkedIn's primarily first-party data, including raw entity data (member profiles, job descriptions, LinkedIn posts) and interaction data (including member job applications) across 5+ surfaces, excluding EU users.
- **Source**: arXiv 2501.16450 Abstract and Section 2.2
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "360Brew is a 150B parameter, decoder-only model that has been trained and fine-tuned on LinkedIn's primarily first-party data and tasks (from users outside European Union)."
- **Context**: The EU exclusion is significant for privacy/regulatory reasons. The training data spans 9 months of LinkedIn data. The paper mentions training on both raw entity data and interaction data, using a combination of continuous pre-training approaches.
- **Confidence**: High

### Finding 2.3: Training Duration and Team Size

- **Claim**: 360Brew V1.0 was developed by a small team over a 9-month period.
- **Source**: arXiv 2501.16450 Abstract
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "360Brew V1.0, developed by a small team of researchers and engineers over a 9-month period."
- **Context**: The team was led by Hamed Firooz (Principal AI Scientist at LinkedIn Core AI) and Maziar Sanjabi (Principal Scientist at LinkedIn AI). Hamed Firooz leads a ~50-person FAIT team.
- **Confidence**: High

### Finding 2.4: Many-Shot In-Context Learning Formulation

- **Claim**: 360Brew formulates recommendation as many-shot in-context learning by conditioning on member profile and interaction history to predict future interactions through joint probability estimation.
- **Source**: arXiv 2501.16450 Section 2.1
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "In any recommendation task, each member, with their unique profile and history of interactions, can be viewed as a many-shot problem. Consequently, when the ranking model is conditioned on the member's profile and interaction history, it can identify and generalize patterns that are highly personalized for that member, extending these patterns to future interactions."
- **Context**: The mathematical formulation treats recommendation as estimating P(m, (e1,i1), ..., (eN,iN)) where m is the member profile and (ej,ij) are historical item-interaction pairs encoded as text. This is fundamentally different from traditional ID-based recommendation approaches.
- **Confidence**: High

### Finding 2.5: Three-Stage Training Process

- **Claim**: The TrustInsights unofficial guide describes a three-stage training process for 360Brew: Continuous Pre-Training, Supervised Fine-Tuning, and Reinforcement Learning.
- **Source**: TrustInsights - The Unofficial LinkedIn Algorithm Guide, Q1 2026 Edition
- **URL**: https://www.trustinsights.ai/wp-content/uploads/2025/05/the_unofficial_linkedin_algorithm_guide_for_marketers_mid_2025_edition.pdf
- **Date**: May 2025
- **Excerpt**: "360Brew went through a rigorous three-stage training process -- Continuous Pre-Training..."
- **Context**: This is from an unofficial third-party analysis and should be treated as secondary information. The original paper does not explicitly detail a three-stage training process with RLHF.
- **Confidence**: Medium

---

## 3. Model Architecture and Technical Specifications

### Finding 3.1: Model Size

- **Claim**: 360Brew has approximately 150 billion parameters.
- **Source**: arXiv 2501.16450 Abstract
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "150B parameter, decoder-only model"
- **Context**: The model uses MoE (Mixture of Experts) architecture, meaning not all parameters are active for each token. Based on Mixtral 8x22B specs, approximately 39B parameters are active per token.
- **Confidence**: High

### Finding 3.2: Scaling Laws

- **Claim**: The paper demonstrates three key scaling properties: data scaling (more data improves performance), model scaling (larger models improve performance), and history scaling (longer context/history improves performance).
- **Source**: arXiv 2501.16450 Sections 2.3-2.5
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt (Data Scaling)**: "The model's efficacy correlated positively with the amount of training data."
- **Excerpt (Model Scaling)**: "360Brew models get better as we increase the size of the model (by using larger and more powerful pre-trained architectures)."
- **Excerpt (History Scaling)**: "360Brew model's performance gets better as we increase the history by increasing the max context length."
- **Context**: History scaling is particularly important as it suggests the model benefits from seeing more of a member's interaction history, reducing the need for hand-crafted features.
- **Confidence**: High

### Finding 3.3: Textual Interface and Prompt Engineering

- **Claim**: 360Brew uses a textual interface where member profiles, item descriptions, and interaction histories are verbalized as natural language prompts, eliminating traditional feature engineering.
- **Source**: arXiv 2501.16450 Section 2.1 and Table 1
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "By employing natural language interfaces for task definitions and verbalizing member behaviors and their social connections, we eliminate the need for feature engineering and the maintenance of complex directed acyclic graphs (DAGs) of model dependencies."
- **Context**: The paper provides a toy example (Table 1) showing a job recommendation prompt that includes member profile, past job interactions (applied, viewed, dismissed), and asks the model to predict future behavior for a new job.
- **Confidence**: High

---

## 4. Task Coverage and Zero-Shot Generalization

### Finding 4.1: 30+ Tasks Across 8+ Surfaces

- **Claim**: 360Brew is capable of solving over 30 predictive tasks across 8+ LinkedIn surfaces.
- **Source**: arXiv 2501.16450 Abstract and Section 2.2
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "This model is capable of solving over 30 predictive tasks across various segments of the LinkedIn platform, achieving performance levels comparable to or exceeding those of current production systems based on offline metrics, without task-specific fine-tuning."
- **Context**: The 8+ surfaces include: Feed, Job Recommendations, People You May Know (PYMK), Ads, Search, Notifications, and more. The paper categorizes tasks into T1 (in-domain) and T2 (out-of-domain).
- **Confidence**: High

### Finding 4.2: T1 (In-Domain) Tasks

- **Claim**: T1 tasks are those where recommendation data from past periods is used in training, with at least a one-month gap between training data and benchmark data to account for distribution shift.
- **Source**: arXiv 2501.16450 Section 2.2
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "T1 (in-domain): Tasks where recommendation data from past periods is used in training the model. There is at least a one-month gap between the T1 data used in training and the benchmark dataset."
- **Context**: These tasks represent standard recommendation scenarios where the model has seen similar member behavior during training but must generalize to new time periods.
- **Confidence**: High

### Finding 4.3: T2 (Out-of-Domain) Tasks

- **Claim**: T2 tasks and surfaces are not part of the training data. The model achieves performance similar to or better than production models on these out-of-domain tasks.
- **Source**: arXiv 2501.16450 Section 2.2 and Section 2.6.1
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "T2 (out-of-domain): Tasks and surfaces that are not part of the training data...the 360Brew model can generalize to out-of-domain tasks and surfaces, and achieves performance similar to or better than the production model."
- **Context**: This zero-shot generalization capability is one of the key claims of the paper - that a single foundation model can handle new recommendation surfaces and tasks without task-specific fine-tuning.
- **Confidence**: High

### Finding 4.4: Cold-Start Performance

- **Claim**: 360Brew shows significantly better performance on cold-start members (those with few interactions) compared to the production baseline model.
- **Source**: arXiv 2501.16450 Section 2.6.2
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "The performance gap between the two models is the largest when member has few available interactions, which shows that 360Brew model has a greater margin over the production model for members with fewer interactions."
- **Context**: The paper shows a figure (Figure 6) demonstrating that the relative performance gap between 360Brew and the production model increases as the number of historical interactions decreases from 100 to 5.
- **Confidence**: High

### Finding 4.5: Temporal Generalization

- **Claim**: 360Brew's performance is less affected by temporal distribution shift compared to baseline models, suggesting it requires less frequent retraining.
- **Source**: arXiv 2501.16450 Section 2.6.3
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "The performance of the 360Brew model is less affected by time. This means that using 360Brew could potentially lead to more developer efficiency and less maintenance and technical debt as we do not need to update the model so frequently."
- **Context**: The paper attributes this to the model's ability to use in-context learning to adjust its answers based on member behavior seen in the context window.
- **Confidence**: High

---

## 5. Deployment Architecture and Production Infrastructure

### Finding 5.1: Critical Distinction - 360Brew NOT Directly Used in Production Feed

- **Claim**: The 360Brew LLM-Ranker (the 150B parameter model described in the paper) was evaluated and explicitly rejected for the production LinkedIn Feed. Instead, LinkedIn deployed a different architecture: an LLM-based retrieval system + a separate sequential recommender (Feed-SR/GR).
- **Source**: "An Industrial-Scale Sequential Recommender for LinkedIn Feed Ranking" (arXiv 2602.12354) Section 5.1
- **URL**: https://arxiv.org/html/2602.12354v1
- **Date**: February 8, 2026
- **Excerpt**: "Before Feed SR, we explored an LLM-Ranker system in which all the features of a candidate post were represented as text and passed into an LLM as part of a prompt...The LLM-Ranker never achieved superior online performance over the existing production model."
- **Context**: The Feed-SR paper explicitly states three reasons for rejecting the LLM-Ranker: (1) difficulty encoding numeric features as text, (2) expensive training/serving due to tens of thousands of tokens per history, (3) struggled with network-based recommendations. Feed SR uses only 2 tokens per history item instead.
- **Confidence**: High

### Finding 5.2: Production Architecture - Two-Stage System

- **Claim**: The production LinkedIn Feed uses a two-stage architecture announced March 12, 2026: (1) LLM-powered retrieval using fine-tuned LLaMA-3 as a dual encoder, and (2) Generative Recommender (GR/Feed-SR) sequential ranking model.
- **Source**: LinkedIn Engineering Blog, "Engineering the next generation of LinkedIn's Feed"
- **URL**: https://www.linkedin.com/blog/engineering/feed/engineering-the-next-generation-of-linkedins-feed
- **Date**: March 12, 2026
- **Excerpt**: "We're rolling out a new advanced ranking system, powered by LLMs and GPUs, that better understands what a post is actually about and how it relates to a member's evolving interests and career goals."
- **Context**: This blog post by Hristo Danchev (Senior Staff TPM at LinkedIn) is the official announcement. It describes the retrieval system (arXiv 2510.14223) and the ranking system (arXiv 2602.12354), NOT the 360Brew paper (2501.16450).
- **Confidence**: High

### Finding 5.3: Stage 1 - LLM-Based Retrieval (LLaMA-3 Dual Encoder)

- **Claim**: The retrieval stage uses a fine-tuned Meta LLaMA-3 model (3B parameters) as a dual encoder to generate embeddings for members and items, achieving sub-50ms retrieval latency.
- **Source**: "Large Scale Retrieval for the LinkedIn Feed using Causal Language Models" (arXiv 2510.14223)
- **URL**: https://arxiv.org/abs/2510.14223
- **Date**: October 16, 2025
- **Excerpt**: "This paper presents a novel retrieval approach that fine-tunes a large causal language model (Meta's LLaMA 3) as a dual encoder to generate high quality embeddings for both users (members) and content (items)...sub-50ms retrieval latency for serving tens of thousands of queries per second on a corpus of hundreds of millions of items."
- **Context**: The retrieval system uses cosine similarity between member and item embeddings. Key innovation: quantizing numerical features into percentile buckets improved correlation between popularity and embedding similarity by 30x.
- **Confidence**: High

### Finding 5.4: Stage 2 - Generative Recommender / Feed-SR

- **Claim**: The ranking stage uses Feed Sequential Recommender (Feed-SR), a transformer-based sequential model that processes 1,000+ historical interactions with causal attention and late fusion architecture.
- **Source**: "An Industrial-Scale Sequential Recommender for LinkedIn Feed Ranking" (arXiv 2602.12354)
- **URL**: https://arxiv.org/html/2602.12354v1
- **Date**: February 8, 2026
- **Excerpt**: "Feed SR is a new ranking system for the LinkedIn Feed based on sequential recommendation...interleaves posts with actions...processed by a number of transformer blocks with a causal attention mask."
- **Context**: Feed-SR achieved +2.10% increase in time spent in online A/B tests. Uses late fusion to separate sequence features from context features, achieving ~12% reduction in training time. Uses MMoE (Multi-gate Mixture-of-Experts) prediction head.
- **Confidence**: High

### Finding 5.5: Training Infrastructure

- **Claim**: The retrieval system (LLaMA-3 dual encoder) was trained using 8 H100 GPUs with per-GPU batch size of 4, on 5M member-item pairs.
- **Source**: arXiv 2510.14223 Section 7
- **URL**: https://arxiv.org/html/2510.14223
- **Date**: October 2025
- **Excerpt**: "We used 5M member-item pairs from public engagement in the LinkedIn Feed as our training samples. We used 8 H100 GPUs for each training run with a per-GPU batch size of 4."
- **Context**: Both Meta-LLaMA 3B and 1B parameter models were experimented with. The 3B model was used for final production. Matryoshka Embeddings were used for variable-dimension embeddings.
- **Confidence**: High

### Finding 5.6: Serving Infrastructure

- **Claim**: The production system uses 48 H100 GPUs for nearline item/member embedding inference and 24 GPUs for online GPU-RAR kNN retrieval.
- **Source**: arXiv 2510.14223 Section 6
- **URL**: https://arxiv.org/html/2510.14223
- **Date**: October 2025
- **Excerpt**: "In the online stack, we used a cluster of 48 H100 GPUs for nearline item and member embedding inference...We used a cluster of 24 GPUs for indexing item embeddings and for performing online GPU-RAR kNN retrieval."
- **Context**: Freshness: newly created items indexed within 1 minute; interaction updates within 30 minutes. Uses GPU Retrieval as Ranking (GPU-RAR) index with cosine similarity.
- **Confidence**: High

### Finding 5.7: Disaggregated Inference Architecture

- **Claim**: The Feed-SR production system uses a disaggregated architecture separating CPU-bound feature processing from GPU-heavy model inference.
- **Source**: arXiv 2602.12354 Section 6.1
- **URL**: https://arxiv.org/html/2602.12354v1
- **Date**: February 2026
- **Excerpt**: "Our inference system employs a disaggregated architecture that separates CPU and GPU workloads to enable independent scaling and optimal resource utilization."
- **Context**: CPU-based inference driver handles feature fetching, tracking, and transformations. PyTorch inference server runs on GPU with gRPC interface using Apache Arrow buffers for zero-copy conversion to PyTorch tensors.
- **Confidence**: High

### Finding 5.8: GRMIS - Custom Flash Attention Variant

- **Claim**: LinkedIn developed GRMIS (Generative Recommender Multi-Item Scoring), a custom Flash Attention variant delivering 2x speedup over standard PyTorch scaled dot-product attention.
- **Source**: ByteByteGo analysis and arXiv 2602.12354
- **URL**: https://blog.bytebytego.com/p/how-linkedin-feed-uses-llms-to-serve
- **Date**: April 13, 2026
- **Excerpt**: "GRMIS (Generative Recommender Multi-Item Scoring), a custom Flash Attention variant natively supporting their attention pattern, delivering an additional 2x speedup over PyTorch's standard scaled dot-product attention."
- **Context**: Shared context batching computes the user's history representation once, then scores all candidates in parallel using custom attention masks. This is critical for meeting sub-second latency requirements.
- **Confidence**: High

---

## 6. Relationship Between 360Brew and Feed-SR

### Finding 6.1: 360Brew Was the LLM-Ranker That Was Rejected

- **Claim**: The 360Brew model (as described in the 2501.16450 paper) corresponds to the "LLM-Ranker" approach that was evaluated and rejected in favor of Feed-SR for the production feed.
- **Source**: arXiv 2602.12354 Section 5.1 and third-party analysis
- **URL**: https://arxiv.org/html/2602.12354v1
- **Date**: February 2026
- **Excerpt**: "This LLM-Ranker showed promising offline results in early experiments...However, the LLM-Ranker also had several key disadvantages...The LLM-Ranker never achieved superior online performance over the existing production model."
- **Context**: Three specific reasons: (1) difficult to encode numeric features as text, (2) tens of thousands of tokens per history made training/serving expensive, (3) struggled with network-based recommendations where relationship strength is hard to encode textually.
- **Confidence**: High

### Finding 6.2: Key Differences Between 360Brew and Feed-SR

| Aspect | 360Brew (LLM-Ranker) | Feed-SR (Production) |
|--------|----------------------|----------------------|
| Architecture | 150B parameter full LLM | Compact transformer (decoder-only, Pre-LN, RoPE) |
| Input representation | Full text prompts (tens of thousands of tokens) | Embedded tokens (2 per history item: post + action) |
| Feature handling | All features verbalized as text | Sequence features + late-fusion context features |
| History length | Limited by LLM context window | 1,000+ interactions (T=1000 impressions) |
| Training cost | Very high | Optimized with custom C++ data loader, CUDA kernels |
| Online performance | Never beat production | +2.10% time spent |
| Network relationships | Difficult to encode | ID embeddings capture patterns well |

- **Source**: Synthesis from arXiv 2501.16450, arXiv 2602.12354, and LinkedIn Engineering Blog
- **Confidence**: High

### Finding 6.3: 360Brew May Power Non-Feed Surfaces

- **Claim**: While 360Brew was rejected for the Feed ranking task, the paper's scope covers 30+ tasks across 8+ surfaces, suggesting it may be used or evaluated for other LinkedIn surfaces (jobs, PYMK, ads, search, notifications).
- **Source**: arXiv 2501.16450 Section 2.2
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "Finally, we apply the model to 30+ tasks across 8+ surfaces."
- **Context**: There is no public confirmation that 360Brew is deployed in production for any surface. The paper describes it as a "pre-production model" and "research." Some third-party sources conflate the Feed-SR/GR production system with 360Brew.
- **Confidence**: Medium

### Finding 6.4: The "360Brew" Name Has Been Appropriated

- **Claim**: The term "360Brew" has been widely adopted in marketing and social media as shorthand for LinkedIn's entire 2025-2026 algorithm overhaul, even though the actual production system does not use the 360Brew model directly for feed ranking.
- **Source**: Multiple third-party analyses
- **URL**: Various (Falia, TrustInsights, TheLime, etc.)
- **Date**: 2025-2026
- **Excerpt (from TheLime)**: "360Brew has become shorthand for the whole LinkedIn algorithm overhaul. Whether or not the exact research model is running the show, the signals, strategies, and content principles are the same."
- **Context**: This conflation has led to widespread misinformation, with many sources incorrectly claiming that a "150B parameter model" directly ranks every feed post, when in fact the production system uses a much smaller LLaMA-3 3B model for retrieval and a compact transformer for ranking.
- **Confidence**: High

---

## 7. Microsoft Synergies and Broader Strategy

### Finding 7.1: Limited Direct Microsoft Infrastructure Synergy

- **Claim**: There is limited public evidence that LinkedIn's 360Brew/Feed-AI systems directly leverage Microsoft's AI infrastructure (Azure, Copilot, etc.) in a technically deep way. LinkedIn appears to operate its own AI training and serving infrastructure independently.
- **Source**: Analysis across all sources
- **URL**: Various
- **Date**: Research synthesis
- **Excerpt**: No direct mention of Azure, Microsoft infrastructure, or Copilot integration in any of the three LinkedIn papers (2501.16450, 2510.14223, 2602.12354) or the engineering blog post.
- **Context**: LinkedIn was acquired by Microsoft in 2016 for $26.2B but maintains significant engineering independence. The papers reference NVIDIA H100 GPUs without mentioning Azure's cloud infrastructure.
- **Confidence**: High

### Finding 7.2: Microsoft Graph and Copilot Integration

- **Claim**: Microsoft Graph connects LinkedIn professional data with Microsoft Copilot's enterprise AI capabilities, creating professional entity verification pathways.
- **Source**: Stackmatix analysis
- **URL**: https://www.stackmatix.com/blog/linkedin-and-microsoft-copilot-integration
- **Date**: March 9, 2026
- **Excerpt**: "Microsoft Graph connects LinkedIn professional data with Copilot's enterprise AI capabilities, creating a visibility pathway that many brands overlook."
- **Context**: This is more about data sharing and enterprise visibility rather than shared AI model training infrastructure. 33M active Copilot users, 54% employee adoption via Microsoft 365 productivity apps.
- **Confidence**: Medium

### Finding 7.3: LinkedIn AI Leadership

- **Claim**: Ya Xu (VP of Engineering and Head of Data and AI at LinkedIn) provides strategic leadership for LinkedIn's AI initiatives. Hamed Firooz leads the ~50-person FAIT team building 360Brew.
- **Source**: MIT Sloan Management Review, McKinsey, AI Engineer World's Fair bio
- **URL**: https://sloanreview.mit.edu/audio/the-collaboration-muscle-linkedins-ya-xu/
- **Date**: 2022-2025
- **Excerpt (Ya Xu bio)**: "Ya Xu, vice president of engineering and head of data and AI at LinkedIn"
- **Excerpt (Hamed Firooz bio)**: "Hamed leads the 50-person team behind LinkedIn's 150-billion-parameter foundation model that personalizes the experience for hundreds of millions of members."
- **Context**: Firooz previously led multimodal Content Understanding models at Meta AI handling tens of billions of daily requests. Maziar Sanjabi has published 60+ papers at venues including NeurIPS, ICML, ICLR, ACL, EMNLP, and CVPR.
- **Confidence**: High

---

## 8. Criticisms, Limitations, and Open Questions

### Finding 8.1: Paper Withdrawal Raises IP/Approval Questions

- **Claim**: The official reason for withdrawal ("submitter did not have the right to agree to the license") suggests that Hamed Firooz may not have had proper corporate authorization to publish the paper, or that LinkedIn/Microsoft legal intervened.
- **Source**: arXiv admin note
- **URL**: https://arxiv.org/abs/2501.16450
- **Date**: August 23, 2025
- **Excerpt**: "This version has been removed by arXiv administrators as the submitter did not have the right to agree to the license at submission."
- **Context**: arXiv's policy states they will not remove papers for "failure to obtain consent from co-authors" but WILL remove if the submitter lacked legal authority. This suggests corporate IP concerns.
- **Confidence**: High

### Finding 8.2: EU Data Exclusion

- **Claim**: The model was explicitly trained on data "from users outside European Union," raising questions about geographic bias and regulatory compliance.
- **Source**: arXiv 2501.16450 Abstract
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "trained and fine-tuned on LinkedIn's primarily first-party data and tasks (from users outside European Union)"
- **Context**: This exclusion was likely due to GDPR compliance concerns. However, it means the model may not generalize well to EU user behavior patterns and may introduce geographic bias.
- **Confidence**: High

### Finding 8.3: 360Brew Never Beat Production Model Online

- **Claim**: Despite promising offline metrics, the 360Brew LLM-Ranker approach "never achieved superior online performance over the existing production model" in A/B tests.
- **Source**: arXiv 2602.12354 Section 5.1
- **URL**: https://arxiv.org/html/2602.12354v1
- **Date**: February 2026
- **Excerpt**: "The LLM-Ranker never achieved superior online performance over the existing production model."
- **Context**: This is a critical finding for the "foundation model for recommendation" thesis. The reasons (numeric feature encoding, sequence length, network relationships) suggest fundamental limitations of text-only approaches for certain recommendation tasks.
- **Confidence**: High

### Finding 8.4: Widespread Misinformation

- **Claim**: A significant gap exists between what LinkedIn has officially confirmed and what third-party sources claim about 360Brew, leading to widespread misinformation.
- **Source**: empower.agency analysis
- **URL**: https://empower.agency/insights/social-media/what-linkedins-new-feed-algorithm-means-for-your-content-strategy/
- **Date**: March 24, 2026
- **Excerpt**: "LinkedIn has published no engineering blog posts confirming 360Brew is running in the feed, announced no rollout timeline, and made no suggestion that the platform has switched to a unified foundation model."
- **Context**: Many sources claim exact reach drops (e.g., "-47% median reach"), specific engagement weightings, and that a "150B parameter model" directly ranks feed posts. None of these are confirmed by LinkedIn's official publications.
- **Confidence**: High

### Finding 8.5: Incomplete Paper with "More Details to Come"

- **Claim**: The 360Brew paper contains multiple placeholders stating "More details to come soon," suggesting it was published prematurely.
- **Source**: arXiv 2501.16450 Section 2.2
- **URL**: https://ar5iv.labs.arxiv.org/html/2501.16450
- **Date**: January 2025
- **Excerpt**: "More details to come soon." (appears multiple times in the architecture and training sections)
- **Context**: The paper lacks specific hyperparameters, exact training data sizes, detailed architecture modifications, and comprehensive ablation studies. This is unusual for a technical paper and suggests it was rushed to publication.
- **Confidence**: High

### Finding 8.6: Privacy and Data Usage Concerns

- **Claim**: LinkedIn's use of member data for AI training has raised privacy concerns, particularly after the platform expanded AI training opt-out settings to EU users in late 2025.
- **Source**: Proton AG analysis
- **URL**: https://proton.me/blog/linkedin-ai-training
- **Date**: September 22, 2025
- **Excerpt**: "LinkedIn isn't the first platform to expand its AI training datasets by opting in users by default...as a recruitment platform that stores resumes, job applications, and professional interactions, LinkedIn's move raises concerns about how your digital career identity fuels AI pipelines."
- **Context**: Users can opt out via Settings & Privacy > Data privacy > Data for Generative AI improvement. Non-members can also file objections.
- **Confidence**: High

---

## 9. Related Papers and Technical References

### Finding 9.1: Feed-SR Paper (2602.12354)

- **Claim**: The Feed-SR paper "An Industrial-Scale Sequential Recommender for LinkedIn Feed Ranking" was published on arXiv on February 8, 2026, and describes the actual production ranking system.
- **Source**: arXiv 2602.12354
- **URL**: https://arxiv.org/abs/2602.12354
- **Date**: February 8, 2026
- **Authors**: Lars Hertel, Gaurav Srivastava, Syed Ali Naqvi, Satyam Kumar, Yue Zhang, Borja Ocejo, Benjamin Zelditch, Adrian Englhardt, Hailing Cheng, Andy Hu, Antonio Alonso, Daming Li, Siddharth Dangi, Chen Zhu, Mingzhou Zhou, Wanning Li, Tao Huang, Fedor Borisyuk, Ganesh Parameswaran, Birjodh Tiwana, Sriram Sankar, Qing Lan, Julie Choi, Souvik Ghosh
- **Key Result**: +2.10% time spent in online A/B tests
- **Confidence**: High

### Finding 9.2: Retrieval Paper (2510.14223)

- **Claim**: The retrieval paper "Large Scale Retrieval for the LinkedIn Feed using Causal Language Models" was published on arXiv on October 16, 2025.
- **Source**: arXiv 2510.14223
- **URL**: https://arxiv.org/abs/2510.14223
- **Date**: October 16, 2025
- **Authors**: Sudarshan Srinivasa Ramanujam, Antonio Alonso, Saurabh Kataria, Siddharth Dangi, Akhilesh Gupta, Birjodh Singh Tiwana, Manas Somaiya, Luke Simon, David Byrne, Sojeong Ha, Sen Zhou, Andrei Akterskii, Zhanglong Liu, Samira Sriram, Crescent Xiong, Zhoutao Pei, Angela Shao, Alex Li, Annie Xiao, Caitlin Kolb, Thomas Kistler, Zach Moore, Hamed Firooz
- **Key Result**: Sub-50ms retrieval latency, significant improvements in member engagement, especially for newer members
- **Confidence**: High

---

## 10. Timeline of Key Events

| Date | Event | Source |
|------|-------|--------|
| Jan 27, 2025 | 360Brew paper (2501.16450) v1 published on arXiv | arXiv |
| Feb 1, 2025 | 360Brew paper v2 published | arXiv |
| Feb 7, 2025 | 360Brew paper v3 published (final content version) | arXiv |
| Feb 8, 2026 | Feed-SR paper (2602.12354) published on arXiv | arXiv |
| Mar 12, 2026 | LinkedIn Engineering Blog: "Engineering the next generation of LinkedIn's Feed" | LinkedIn Engineering |
| Aug 23, 2025 | 360Brew paper v4 published then withdrawn by arXiv admins | arXiv |
| 2025-2026 | Gradual rollout of new Feed system (retrieval + GR) | LinkedIn Engineering |

---

## 11. Search Queries Executed

1. `360Brew LinkedIn foundation model arxiv 2501.16450`
2. `360Brew LinkedIn decoder-only personalized ranking 150B`
3. `Hamed Firooz 360Brew foundation model FAIT`
4. `LinkedIn 360Brew many-shot in-context learning`
5. `360Brew withdrawn arxiv paper mirrored pdf`
6. `LinkedIn engineering blog next generation feed March 2026 360Brew`
7. `LinkedIn FAIT team Foundation AI technologies Ya Xu`
8. `360Brew Mixtral 8x22B architecture training hyperparameters`
9. `LinkedIn 360Brew zero-shot generalization out-of-domain tasks`
10. `LinkedIn "Engineering the next generation of LinkedIn's Feed" 2026`
11. `LinkedIn Feed-SR late fusion transformer architecture`
12. `LinkedIn 360Brew GPU infrastructure H100 training hardware`
13. `360Brew T1 T2 tasks surfaces evaluation AUC metrics`
14. `LinkedIn "LLM-Ranker" evaluated rejected Feed-SR 360Brew`
15. `360Brew arxiv withdrawn submitter did not have right license`
16. `LinkedIn 360Brew continuous pre-training SFT domain adaptation`
17. `LinkedIn generative recommender GR transformer 1000 interactions`
18. `LinkedIn 360Brew vs Feed-SR sequential recommender difference`
19. `LinkedIn AI Microsoft partnership Azure infrastructure`
20. `360Brew criticism limitations challenges`
21. `LinkedIn 360Brew Mixtral 8x22 150B training data 9 months development`
22. `LinkedIn 360Brew cold start temporal generalization performance AUC`
23. `LinkedIn AI Microsoft Copilot Teams integration synergy`
24. `360Brew 30 tasks surfaces feed jobs search ads notifications`
25. `LinkedIn large scale retrieval causal language model feed arxiv`

---

## 12. Confidence Summary

| Claim Category | Confidence Level | Reasoning |
|----------------|-----------------|-----------|
| Paper details, authors, dates | High | Direct from arXiv and ar5iv mirror |
| Architecture (Mixtral 8x22B base) | High | Explicitly stated in paper Section 2.2 |
| 150B parameters | High | Explicitly stated in paper abstract |
| 30+ tasks, 8+ surfaces | High | Explicitly stated in paper |
| Training data scope, EU exclusion | High | Explicitly stated in paper |
| 9-month development, small team | High | Explicitly stated in paper |
| 360Brew NOT in production feed | High | Explicitly stated in Feed-SR paper Section 5.1 |
| Production uses LLaMA-3 retrieval + Feed-SR | High | Confirmed by 2 arXiv papers + Engineering blog |
| H100 GPU infrastructure counts | High | Explicitly stated in retrieval paper |
| Three-stage training process | Medium | From third-party analysis only |
| Microsoft infrastructure synergy | Low/Medium | No direct evidence in primary sources |
| Exact reach impact metrics (-47%) | Low | From third-party estimates, not confirmed by LinkedIn |

---

## Sources Index

- [^1] arXiv 2501.16450 (360Brew paper): https://arxiv.org/abs/2501.16450
- [^2] ar5iv mirror of 2501.16450: https://ar5iv.labs.arxiv.org/html/2501.16450
- [^3] arXiv 2602.12354 (Feed-SR paper): https://arxiv.org/abs/2602.12354
- [^4] arXiv 2510.14223 (Retrieval paper): https://arxiv.org/abs/2510.14223
- [^5] LinkedIn Engineering Blog (March 12, 2026): https://www.linkedin.com/blog/engineering/feed/engineering-the-next-generation-of-linkedins-feed
- [^6] TrustInsights Unofficial Guide: https://www.trustinsights.ai/wp-content/uploads/2025/05/the_unofficial_linkedin_algorithm_guide_for_marketers_mid_2025_edition.pdf
- [^7] ByteByteGo analysis: https://blog.bytebytego.com/p/how-linkedin-feed-uses-llms-to-serve
- [^8] Falia 360Brew analysis: https://falia.co/en/360brew-linkedins-new-algorithm-explained-2026/
- [^9] Empower.agency analysis: https://empower.agency/insights/social-media/what-linkedins-new-feed-algorithm-means-for-your-content-strategy/
- [^10] TheLime analysis: https://thelime.one/lime/articles/360brew-linkedin-algorithm-explained-fix-your-linkedin-content-strategy
- [^11] Pettauer analysis: https://pettauer.net/en/linkedin-360brew-semantic-visibility-2026/
- [^12] MIT Sloan Ya Xu interview: https://sloanreview.mit.edu/audio/the-collaboration-muscle-linkedins-ya-xu/
- [^13] AI Engineer World's Fair talk (Hamed Firooz & Maziar Sanjabi): https://www.youtube.com/watch?v=U0S6CfzAY5c
- [^14] Proton LinkedIn AI training analysis: https://proton.me/blog/linkedin-ai-training
- [^15] Stackmatix LinkedIn-Copilot analysis: https://www.stackmatix.com/blog/linkedin-and-microsoft-copilot-integration
- [^16] Moonlight literature review: https://www.themoonlight.io/en/review/360brew-a-decoder-only-foundation-model-for-personalized-ranking-and-recommendation
- [^17] AlphaXiv overview: https://alphaxiv.org/overview/2501.16450v4
- [^18] Reddit r/linkedin discussion: https://www.reddit.com/r/linkedin/comments/1s4mbga/360brew/

---

*Research compiled from 25+ independent searches across arXiv, LinkedIn Engineering Blog, Google Patents, USPTO, and industry analysis sources. Document last updated: July 2025.*
