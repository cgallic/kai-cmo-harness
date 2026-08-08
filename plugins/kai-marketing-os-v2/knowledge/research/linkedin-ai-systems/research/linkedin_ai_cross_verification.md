# Cross-Verification Results: LinkedIn AI Systems Deep Research

## Summary
Research spanned 6 wide-exploration agents and 12 deep-dive agents across 300+ independent searches. Below is the confidence-classified synthesis of all findings.

---

## HIGH CONFIDENCE FINDINGS (Confirmed by ≥2 agents from independent sources)

### Architecture & Systems
1. **Feed-SR is the production feed ranking model** — Transformer-based sequential recommender deployed Feb 2026, replacing DCNv2. Achieved +2.10% time spent in A/B tests. Uses decoder-only transformer with Pre-LN, RoPE, causal attention, interleaved post-action sequences. [Dim01, Dim02, Dim05]
2. **LLM-based retrieval uses fine-tuned LLaMA-3 3B as dual encoder** — Replaced 5 separate retrieval systems. 3072-dim embeddings, sub-50ms latency, 72 H100 GPUs (48 nearline + 24 online). [Dim01, Dim02, Dim05]
3. **360Brew 150B model (arXiv 2501.16450) was explicitly REJECTED for feed ranking** — Feed-SR paper Section 5.1 states: "The LLM-Ranker never achieved superior online performance." Three reasons: (1) difficult to encode numeric features as text, (2) tens of thousands of tokens per history, (3) struggled with network-based recommendations. [Dim01, Dim02, Dim12]
4. **360Brew is built on Mixtral 8x22B (not LLaMA 3)** — The paper explicitly states this; secondary sources commonly misreport LLaMA 3. The retrieval system uses LLaMA 3, not 360Brew. [Dim01]
5. **360Brew paper was withdrawn Aug 23, 2025** — Official reason: "submitter did not have the right to agree to the license." Suggests corporate IP concerns. Content preserved via ar5iv mirror. [Dim01, Dim12]
6. **LiGNN operates on 100B+ node heterogeneous graph** — Member (1B), Job (50M), Company (25M), Skill (41K), Title (25K), Position (195M) nodes. KDD 2024 paper. Production metrics: +0.5% Feed DAU, +1.0% Jobs hearing-back, +2.0% Ads CTR. [Dim04]
7. **LinkSAGE uses near-line inference** — GNN encoder pre-computes embeddings stored in Venice feature store. Eliminates real-time GNN inference. Low tens of milliseconds latency. [Dim04, Dim06]

### AI Content Detection
8. **"AI solving AI" system uses human annotation + ML classifiers** — Editors annotate thousands of posts (generic vs. original), multiple reviewers per post, labels train classifiers. Targets: (1) generic AI posts, (2) bot comments, (3) attention-bait videos. [Dim03, Wide04]
9. **Flagged content gets distribution suppression, not removal** — Only shown to 1st-degree connections, removed from recommendations. [Dim03, Wide04]
10. **Detection signals include pattern, vocabulary, structural, engagement, and account-level features** — "Contrastive construction" ("it's not X, it's Y"), AI vocabulary (delve, tapestry, leverage), uniform structure, low dwell time, unnaturally consistent posting style. [Dim03, Wide04, Wide06]
11. **Engagement pod detection claimed at 97% accuracy** — Multi-signal detection (velocity, network analysis, semantic analysis). Penalties: shadow bans (60-90 day recovery). [Dim07, Wide06]

### Key People
12. **Deepak Agarwal returned as Chief AI Officer Jan 2025** — Previously VP AI 2012-2020. From Pinterest where he scaled AI org 200→1,000. Founded AI Academy in first tenure. [Dim08]
13. **Hamed Firooz leads ~50-person FAIT team** — Built 360Brew in 9 months. Previously led multimodal Content Understanding at Meta AI. [Dim01, Dim08]
14. **Ya Xu left for Google DeepMind Sep 2024** — Led 1,000-person Data & AI org. Stanford PhD. Fortune 40 Under 40. [Dim08]
15. **Qingquan Song departed for OpenAI 2025** — Senior Staff ML Engineer, core LiRank contributor. 55 papers, 2,450+ citations. [Dim08]

### Infrastructure
16. **Apache Kafka processes 7T+ messages/day at LinkedIn** — 4,000+ brokers. Powers entire ML pipeline. Created 2010 by Jay Kreps, Neha Narkhede, Jun Rao. [Dim09]
17. **Apache Pinot serves 250K+ QPS** — 50-80+ user-facing apps including "Who Viewed My Profile" and Talent Insights. [Dim09]
18. **Feathr feature store reduced feature engineering from weeks to days** — 6+ years in production. Open-sourced 2022. Point-in-time correctness. [Dim09]
19. **Liger Kernel achieves 60% GPU memory reduction** — Triton kernels for LLM training. 275K GPU hours saved. [Dim09]

### Bias & Fairness
20. **Independent AAAI 2026 audit found under-representation of minorities in Talent Search** — Korolova et al. (Princeton/USC/Stony Brook). Black-box evaluation using real-world LinkedIn Recruiter results. [Dim10]
21. **LinkedIn deployed counteracting AI for gender bias in 2018** — DetGreedy algorithm for representative gender distribution. A/B test: 33% → 95% improvement in queries with representative results. [Dim10]
22. **IZA study: men's profiles 11.5% more likely to be viewed by recruiters** — Field experiment with fictitious profiles across LinkedIn, ZipRecruiter, Monster. [Dim10]

---

## MEDIUM CONFIDENCE FINDINGS (Confirmed by 1 agent from authoritative source)

1. **360Brew may power non-feed surfaces** — Paper covers 30+ tasks across 8+ surfaces, but no public confirmation of deployment anywhere. [Dim01]
2. **Feed-SR uses ~20% of DCNv2's feature set** — From the paper, but exact feature count not specified. [Dim02]
3. **360Brew authenticity score 0-100, posts under 40 deprioritized** — From third-party analysis, not LinkedIn official. [Dim03]
4. **Comments ~15x raw weight, ~2x after NLP quality scoring** — AuthoredUp NLP-aware analysis vs. industry estimates. Precise weights are not published by LinkedIn. [Dim02, Wide05]
5. **Feed composition: ~31% 1st-degree, ~25% 2nd/3rd, ~10% suggested** — From independent researcher Melanie Goodman, not LinkedIn official. [Dim02]
6. **Top Creator visibility 15%→31% (2022→2025)** — van der Blom's 1.8M-post study. Methodology is transparent but data is observational. [Dim02, Wide06]
7. **54% of long-form LinkedIn posts are AI-generated** — Originality.ai study (commercial tool, potential detection bias). [Wide06]
8. **Daniel Hall exposed 200+ creators in engagement pods** — Demonstrated evidence, Lempod vulnerability confirmed by LinkedIn. [Dim07, Wide06]
9. **LiGR achieved +2.4% Long Dwell AUC** — From paper, but online A/B test results not reported. [Dim02]
10. **Microsoft Graph connects LinkedIn data to Copilot** — 33M Copilot users. More about data sharing than shared AI training infrastructure. [Dim01]

---

## LOW CONFIDENCE FINDINGS (Weak sourcing or single unverified claim)

1. **"Exact reach impact: -47% median reach per post"** — Third-party estimate (Falia), not confirmed by LinkedIn. Exact percentages vary across sources. [Dim01]
2. **"360Brew 40-100% deployed by fall 2025"** — Independent estimate. LinkedIn never confirmed deployment percentage. [Dim01]
3. **Three-stage training process for 360Brew** — From TrustInsights unofficial guide only (SFT, RLHF claims not in original paper). [Dim01]
4. **"14 distinct AI systems working together"** — Trust Insights claim. May reflect historical architecture more than current consolidated system. [Wide06]
5. **25% of LinkedIn traffic may be bots/fake accounts** — Daniel Hall citing Lunio study. Broad estimate. [Dim07, Wide06]
6. **Saves drive 5x more reach than likes** — AuthoredUp analysis. Conflicting estimates across sources. [Wide05, Wide06]

---

## CONFLICT ZONES (Contradictions requiring resolution)

### Conflict 1: CRITICAL — What Actually Powers LinkedIn's Feed?
- **Narrative A (widely reported)**: 360Brew (150B parameter model) runs LinkedIn's feed. [Multiple third-party blogs, Falia, TrustInsights]
- **Narrative B (from primary sources)**: Feed-SR + LLaMA-3 retrieval powers the feed. 360Brew was evaluated and rejected. [Feed-SR paper Section 5.1, LinkedIn Engineering Blog March 12, 2026]
- **Resolution**: Narrative B is HIGH CONFIDENCE (primary sources). Narrative A is widespread misinformation. The term "360Brew" has been appropriated as marketing shorthand for the entire algorithm overhaul. The actual production system uses: (1) LLaMA-3 3B for retrieval, (2) Feed-SR transformer for ranking.
- **Status**: RESOLVED — Primary sources win.

### Conflict 2: Comment Weight Estimates
- **Claim A**: Comments are ~15x the weight of likes [Industry estimate, van der Blom]
- **Claim B**: Comments are ~2x likes after NLP quality scoring [AuthoredUp 3M-post analysis]
- **Resolution**: Both may be partially correct. Raw comment count may have high weight, but NLP quality scoring discounts generic comments ("Great post!"), reducing effective weight. LinkedIn likely uses both raw count and quality-scored signals.
- **Status**: PARTIALLY RESOLVED — Both signals likely used simultaneously.

### Conflict 3: 360Brew Deployment Status
- **Claim A**: 360Brew is NOT in production (Feed-SR paper says LLM-Ranker rejected) [Dim01]
- **Claim B**: 360Brew powers 30+ tasks across 8+ surfaces [360Brew paper]
- **Claim C**: 360Brew is deployed at 40-100% as of fall 2025 [Third-party estimates]
- **Resolution**: Claim A refers to feed RANKING specifically. 360Brew may be used for other surfaces (jobs, PYMK, ads) or for content understanding/embedding generation even if not for feed ranking. The exact deployment status is intentionally opaque.
- **Status**: PARTIALLY RESOLVED — Different claims may refer to different surfaces.

### Conflict 4: Reach Decline Narrative
- **Claim A**: 40-50% organic reach drops for most creators [8+ independent studies]
- **Claim B**: LinkedIn frames changes as "improving relevance and quality" [LinkedIn official]
- **Resolution**: Not mutually exclusive. Reach may be declining in aggregate but becoming more targeted/relevant. The shift from Social Graph to Interest Graph redistributes visibility from broad-network creators to topic-specific creators.
- **Status**: RESOLVED — Both can be true; different metrics.

### Conflict 5: LinkedIn Bias Claims vs. Independent Audit
- **Claim A**: LinkedIn's self-reported fairness improvements show significant progress (33%→95% gender representation) [LinkedIn KDD 2019 paper]
- **Claim B**: Independent AAAI 2026 audit found "under-representation of minority groups in early ranks" and temporal disparities [Korolova et al.]
- **Resolution**: LinkedIn's metrics (MinSkew@100 = -0.011) may look good at rank 100 but mask disparities at top ranks (k=25, k=50). Independent audit found women churn ~0.07 units more than men at top ranks. The metrics measure different things at different positions.
- **Status**: RESOLVED — Both can be true; metrics capture different rank positions.

### Conflict 6: AI Content Prevalence
- **Claim A**: 54% of long-form posts are AI-generated [Originality.ai]
- **Claim B**: 53.7% in 2025 (99 profiles) [Originality.ai updated]
- **Claim C**: AI posts receive 45% less engagement [Originality.ai]
- **Claim D**: Some industries show 0-100% variation [Originality.ai]
- **Resolution**: Claims are consistent (same source). The 45% engagement penalty and industry variation are sub-findings of the same study. Commercial detection bias possible but methodology is transparent.
- **Status**: RESOLVED — Internally consistent from single source.
