# Facet: AI Content Detection & Moderation Systems — LinkedIn

## Key Findings

- **LinkedIn uses a dual-layered approach**: A unified foundation model (360Brew) for semantic understanding and ranking, combined with specialized human-in-the-loop classifiers for detecting AI slop, bot comments, and engagement bait [^46^][^61^].
- **The "AI solving AI" framework** is the company's umbrella term for technology systems built in partnership with editorial teams that distinguish between original thinking and posts that lack uniqueness or substance [^1^][^3^].
- **Flagged content is not deleted** but receives distribution suppression — posts will only appear to 1st-degree connections and followers, not in recommendations to broader audiences [^1^][^18^].
- **Content creation is up 14% year-over-year**, driven by AI tools, creating an urgent need for quality differentiation according to Laura Lorenzetti, VP of Product & Executive Editor [^1^].
- **Human editors annotate thousands of posts** (labeled generic vs. original), with multiple reviewers per post for consistency; these labels train ML classifiers that operate at scale [^1^].
- **LinkedIn's detection targets three core areas**: (1) Generic AI-written posts and comments, (2) Automation tools used to create AI content (bot comments), and (3) Attention-bait videos [^1^][^3^].
- **360Brew is a 150-billion-parameter decoder-only transformer** built on LLaMA 3 architecture, fine-tuned exclusively on LinkedIn's Economic Graph data, handling 30+ predictive tasks [^46^][^49^][^64^].
- **Detection systems achieved 97% accuracy** for engagement pod detection as of 2026, with similar pattern-based approaches applied to bot comment identification [^37^].
- **The "contrastive construction" tell** — phrases like "it's not X, it's Y" — was explicitly called out by LinkedIn as an AI writing pattern being targeted for detection [^2^][^3^].
- **"Em dash discourse"** in early 2026 illustrated the detection arms race: users noticed AI content overused em dashes, leading to widespread debate before LinkedIn's formal crackdown [^3^].
- **OpenAI discontinued its own AI text classifier** due to "low rate of accuracy," highlighting the industry-wide challenge that LinkedIn is attempting to solve through its hybrid human-ML approach [^102^].

---

## Detection Systems [by type]

### 1. Generic AI-Written Post Detection ("AI Slop")

**Architecture**: The system combines LinkedIn's 360Brew foundation model with specialized content quality classifiers trained on human-labeled data [^61^][^49^].

**How it works**:
- Human editors and content managers annotate thousands of posts, labeling them as either generic or original based on detailed definitions of what constitutes low- or high-quality content [^1^].
- Multiple people review each post to ensure consistency (inter-annotator agreement) [^1^].
- These human-labeled examples train machine learning models that identify patterns in content at scale [^1^].
- The classifiers learn from engagement patterns: what language adds perspective, context, or expertise versus what simply repeats existing ideas without contributing anything new [^3^].

**Detection signals** (as reconstructed from sources):
- **Pattern-level**: "Contrastive construction" ("it's not X, it's Y" phrasing), generic openers ("In today's fast-paced world"), templated closers ("What do you think?") [^3^][^50^]
- **Vocabulary-level**: Overused AI-associated words — delve, tapestry, leverage, robust, seamless, revolutionise, holistic, transformative, paradigm, multifaceted, navigate, impactful [^50^]
- **Structural-level**: Uniform sentence length, predictable transitions, balanced paragraphs, consistent paragraph length [^15^][^50^]
- **Engagement-level**: Low dwell time (2-4 seconds vs. 30+ for quality content), low comment-to-like ratios, absence of shares, generic one-line comments [^15^]
- **Account-level**: Unnaturally consistent posting style across weeks/months (same vocabulary, same structure, same posting rhythm) signals automation [^15^]

**360Brew authenticity scoring**: Posts are scored on a 0-100 authenticity scale; posts under 40 get deprioritized in the feed, limited to direct followers [^61^].

**Performance impact**: Pure AI posts perform at roughly half the engagement rate (0.31% vs. 0.67% average) and go viral at one-third the normal rate (0.8% vs. 2.16%) [^15^]. AI-assisted content with human editing performs identically to fully human-written posts [^61^].

**Confidence**: HIGH — Based on multiple corroborating sources including official LinkedIn statements, engineering papers, and third-party data analysis.

### 2. Bot Comment Detection

**Architecture**: Classifiers that analyze both comment language and posting behavior patterns [^1^].

**How it works**:
- LinkedIn builds classifiers to identify low-quality AI comments, examining both the actual language in comments and the patterns/volume in which comments are posted [^1^].
- Bot detection looks at comment velocity: if someone is using an AI tool, they might comment much faster and more often than a regular user [^1^].
- Detection systems identify patterns in: (1) comment timing, (2) language similarity, (3) engagement reciprocity indicating automation [^37^][^58^].
- AI-generated comments with unnatural timing (comments within seconds of a post going live) trigger flags [^41^].

**Specific patterns detected**:
- Same text posted repeatedly across multiple posts
- Comments within seconds of posting (impossible for human readers)
- Excessive volume: hundreds of comments daily [^77^]
- Generic phrases: "Great post!", "Thanks for sharing", "Love this!" repeated [^77^]
- Pod-like patterns: same group always engaging together [^77^]
- Summarizing/repeating what the original post was about (a tell of AI comment bots) [^1^]

**Enforcement**: LinkedIn had already banned AI commenting tools in its Terms of Service. Detection is now catching violators with claimed 97% accuracy for obvious patterns [^37^][^77^]. Penalties include shadowban-style reach reduction rather than account suspension.

**Confidence**: MEDIUM-HIGH — Official confirmation of detection approach but limited technical details on classifier architecture.

### 3. Attention-Bait Video Detection

**Architecture**: Pattern recognition system targeting videos designed purely to keep people watching without adding real value [^1^].

**How it works**:
- LinkedIn targets "attention-bait videos" — content designed purely to keep people watching without adding real value [^1^].
- Examples include: lengthy videos of construction accidents paired with generic workplace safety advice, extended footage of manufacturing processes accompanied by vague business platitudes [^1^].
- These videos were often proven on other platforms (Instagram) and then reposted on LinkedIn to grab attention [^1^].
- Under 360Brew, native video has declined 70% in reach in some analyses because the model is text-first and reads transcripts; video often suffers from lower completion and slower information density than text [^49^].
- Mismatched video and text is a specifically flagged behavior: if a video has no meaningful connection to the text content and appears designed to drive impressions rather than deliver genuine information, it is penalized [^16^].

**Detection signals**:
- Video with no meaningful connection to accompanying text
- Content proven on other platforms and reposted to LinkedIn
- Generic voiceover paired with attention-grabbing footage
- Low completion rates combined with high initial click counts [^49^]

**Confidence**: MEDIUM — Official confirmation of targeting, but less technical detail available compared to text-based AI slop detection.

### 4. Engagement Bait Detection

**Architecture**: Dedicated classifier trained on patterns that generated high interaction counts without delivering genuine user satisfaction [^16^][^58^].

**How it works**:
- LinkedIn moved from passively deprioritizing engagement bait to actively suppressing it in 2026 [^58^].
- The classifier has been trained on patterns that generated high interaction counts without delivering genuine user satisfaction [^58^].
- Posts asking for specific comment triggers ("Comment YES if...", "Tag someone who needs this", "Double tap if this resonates") are actively filtered [^16^].
- The system interprets these as signals of low content quality, not high engagement [^16^].

**Specific tactics penalized** (2026 status) [^58^]:

| Tactic | Status in 2026 |
|--------|---------------|
| Reaction polling ("Like if agree, Love if disagree") | Penalized |
| "Comment YES if you agree" | Penalized |
| Follow-for-follow requests | Penalized |
| Artificial urgency | Penalized |
| Tagging unrelated people | Flagged |
| Educational hooks with data | Rewarded |

**Performance impact**: Posts with engagement bait trigger distribution restrictions regardless of how strong the account's history is [^58^].

**Confidence**: HIGH — Multiple official sources and explicit confirmation from LinkedIn.

### 5. Quality Filtering & Three-Stage Distribution

**Architecture**: Three sequential phases before content reaches a significant audience [^16^][^36^][^52^].

**Phase 1: Automated Quality Filtering**
- Every post is immediately classified as spam, low quality, or high quality [^16^][^52^]
- Posts violating community policies are removed
- Posts flagged as low quality (engagement bait, repetitive templates, automated content, AI slop) are deprioritized before reaching the ranking stage [^16^]
- Quality classifier assesses content substance, formatting signals, and author credibility [^58^]

**Phase 2: Engagement Testing**
- Posts passing the filter are shown to 2-5% of the poster's network [^37^]
- Algorithm monitors the "golden hour" (first 30-60 minutes) [^36^][^99^]
- If 5-10% of viewers engage, the post advances to Stage 3; below 2% kills the post [^37^]
- Key signals weighted heavily: dwell time (highest weight), comment quality, shares, saves [^37^][^62^]
- Comments carry ~8-15x the algorithmic weight of likes (industry estimates vary) [^15^][^62^]

**Phase 3: Extended Distribution**
- Strong performers shown to 2nd/3rd degree connections, hashtag followers, interest groups [^62^]
- LinkedIn's editorial team may review high-performing posts for quality and authenticity [^36^]
- Posts can resurface for 48-72 hours or more under 360Brew's "long tail visibility" [^75^]

**Confidence**: HIGH — Based on LinkedIn Engineering Blog posts, official interviews, and multiple corroborating third-party analyses.

---

## Human-in-the-Loop Pipeline

### Editorial Annotation Process

**Workflow**:
1. **Human editors and content managers** annotate thousands of posts [^1^]
2. **Each post is labeled** as either generic or original based on detailed definitions of what constitutes low- or high-quality content [^1^]
3. **Multiple reviewers per post** — typically, multiple people review each post to ensure consistency (inter-annotator agreement) [^1^]
4. **Engineering-editorial collaboration**: LinkedIn's engineers collaborated with in-house editorial staff to identify patterns in how members engage, recognizing what adds perspective, context, or expertise versus what simply repeats existing ideas without contributing anything new [^3^][^73^]

### Training Data Pipeline

- Human-labeled examples train machine learning models that identify patterns in content at scale [^1^]
- Models learn by identifying patterns in how members engage, as well as what language adds perspective, context, or expertise [^1^]
- The classifiers can learn over time as new patterns of AI-generated content emerge [^1^]
- LinkedIn uses its own corpus of 1B+ posts, author metadata, engagement patterns, and human labeling of authentic vs. AI-generated content to train 360Brew [^61^]

### Model Deployment & Updates

- 360Brew was trained on data through August 2025, optimized for ChatGPT-4, Claude 3.5 Sonnet, Gemini 2.0-era outputs [^61^]
- LinkedIn updates the model quarterly with calibration adjustments [^61^]
- The system is designed to evolve: "AI slop is just the latest problem. We'll keep paying attention" — Laura Lorenzetti [^1^]

### Fairness & Bias Mitigation

- **LiFT (LinkedIn Fairness Toolkit)**: Open-source Scala/Spark library for measuring fairness and mitigating bias in large-scale ML workflows [^88^]
- Enables measurement of biases in training data, evaluation of fairness metrics for ML models, and detection of statistically significant differences in performance across subgroups [^88^]
- Includes post-processing methods for transforming model scores to ensure equality of opportunity for rankings [^88^]
- Research has identified "structural bias pathways" in LinkedIn's recommendation architecture that can produce unequal visibility outcomes even without intentional discrimination [^42^]

**Confidence**: MEDIUM-HIGH — Official confirmation of human annotation process exists, but specific numbers ( annotator count, inter-rater agreement rates) are not publicly disclosed.

---

## Trends & Signals

- **360Brew represents a paradigm shift** from signal-based ranking to semantic reasoning. The old system ranked posts based on who interacted with what; the new one ranks them based on what they mean [^49^][^46^].
- **The 360Brew deployment (March 2026)** caused median reach per post to drop 47% for many creators — an intentional result of prioritizing relevance over broad distribution [^46^].
- **Vocabulary-based detection evolves rapidly**: When LinkedIn announces a specific pattern (like "contrastive construction"), slop generators adapt, creating an arms race — one tell at a time [^2^].
- **AI-assisted content is not penalized** — only content that lacks original insight, expertise, or perspective. The platform explicitly allows AI-assisted posts with original ideas [^1^][^3^].
- **Content format performance shifted**: Document carousels (PDFs) now generate ~2-3x more dwell time than text or image posts and have the highest engagement rates (~6.6%) [^58^][^78^].
- **Engagement pods are effectively dead**: Accounts in pods have seen reach drop from thousands to hundreds overnight; detection systems identify coordinated patterns with claimed 97% accuracy [^58^][^41^].
- **The em dash episode (early 2026)** demonstrated detection's inherent fragility: em dashes became a focal point after users claimed they signaled AI writing, but LLMs had simply learned the pattern from human writers who loved em dashes [^3^].
- **Data from training AI**: LinkedIn uses public member data to train its AI models; members in the EU/EEA/Switzerland/UK had to opt out by November 2025, while US data collection was already underway [^79^].

---

## Controversies & Conflicting Claims

- **Pattern detection is a treadmill**: Shelly Palmer argues that detecting "contrastive construction" as a signal of AI writing is an example of why pattern-based detection fails — LLMs learned the pattern from human writers who used it for decades. Now that LinkedIn has announced the signal, slop generators will stop using it. "There will be many others" [^2^].
- **The "better writer" problem**: What happens when AI is a better writer than the person using it? Professionals with useful judgment and weak prose benefit from AI assistance. LinkedIn's approach risks removing both the thinkers AND the bots [^2^].
- **False positives are inevitable**: OpenAI discontinued its AI text classifier due to low accuracy rates. Pattern-based detection risks penalizing human writers who happen to use similar structures [^102^][^2^].
- **Platform conflict of interest**: LinkedIn simultaneously cracks down on AI slop while offering prominent "rewrite with AI" buttons in its post composer — a tension that has drawn criticism [^3^][^18^].
- **Structural bias**: Research by Martyn Redstone identified "structural bias pathways" in LinkedIn's recommendation architecture, where the system compresses user identity into embeddings and amplifies signals from professional networks through an 8.6 billion-node graph, potentially disadvantaging users from protected groups [^42^].
- **The 70/30 weighting rule**: Historical engagement receives 70% weight vs. 30% for current relevance, meaning users sidelined in the past continue to be suppressed [^42^].
- **Content is not removed, only suppressed**: This approach avoids accusations of censorship but creates a "shadowban" effect where creators may not realize their content is being limited [^1^][^18^].

---

## Recommended Deep-Dive Areas

1. **360Brew Foundation Model Architecture**: The 150B-parameter decoder-only transformer (arXiv:2501.16450) warrants deep technical analysis — its training data composition, fine-tuning methodology, and how it handles the 30+ predictive tasks across surfaces. Access to the full research paper would provide model architecture details, training hyperparameters, and evaluation metrics. **Why it warrants depth**: This is the core infrastructure powering all content ranking decisions on LinkedIn as of 2026.

2. **LiGNN Graph Neural Network Framework**: The deployed GNN system operating on LinkedIn's heterogeneous graph with up to hundreds of billions of nodes and edges. The KDD 2024 paper and cross-domain extensions (KDD 2025) contain detailed technical specifications. **Why it warrants depth**: GNNs power the embedding-based retrieval that surfaces content recommendations; understanding graph construction, neighbor sampling, and temporal modeling is critical to understanding how content propagates.

3. **LinkSAGE Job Matching Architecture**: While primarily focused on job recommendations, the transfer learning methodology and nearline inference system have implications for content recommendation. **Why it warrants depth**: The approach of decoupling GNN training from DNN serving while maintaining up-to-date signals via transfer learning is a novel architecture that could inform content moderation system design.

4. **Human Annotation Pipeline Details**: Specifics on annotator training, inter-annotator agreement rates, label taxonomy, and how annotations flow into model training. **Why it warrants depth**: The quality of the human-labeled training data directly determines the accuracy of the downstream classifiers; any bias in annotation propagates to production detection.

5. **Fairness in Content Moderation (LiFT + Redstone Analysis)**: The intersection of LinkedIn's Fairness Toolkit with content suppression decisions, and the "structural bias pathways" identified in Redstone's 100-page report. **Why it warrants depth**: Content suppression that disproportionately affects certain demographic groups could create significant legal and ethical liability.

6. **Adversarial Evasion Patterns**: How AI content generators are likely to adapt to LinkedIn's announced detection signals, and what new "tells" will emerge as the arms race continues. **Why it warrants depth**: Understanding evasion patterns is essential for building robust detection systems that don't rely on fragile heuristics.

7. **Performance Metrics & A/B Test Results**: LinkedIn's own internal metrics on detection accuracy, false positive rates, and impact on user engagement from the AI slop crackdown. **Why it warrants depth**: Without published metrics, all third-party accuracy claims are speculative; official data would validate or invalidate the effectiveness of the approach.

---

## Source Index

| Citation | Source | Date | Type |
|----------|--------|------|------|
| [^1^] | Entrepreneur — "LinkedIn Is Fighting Back Against AI Slop" | May 2026 | News |
| [^2^] | Shelly Palmer — "LinkedIn Declares War On AI Slop" | May 2026 | Analysis |
| [^3^] | Engadget — "LinkedIn Doesn't Want Your AI Slop Anymore" | May 2026 | News |
| [^15^] | ViralBrain — "How LinkedIn Detects AI Content" | April 2026 | Analysis |
| [^16^] | ALM Corp — "LinkedIn's Feed Algorithm Now Uses LLMs" | March 2026 | Analysis |
| [^18^] | Media Copilot — "LinkedIn's war on AI filler" | May 2026 | News |
| [^36^] | Stackmatix — "How the LinkedIn Algorithm Works in 2026" | April 2026 | Analysis |
| [^37^] | Teract AI — "LinkedIn Algorithm 2026: How It Really Works" | March 2026 | Technical Analysis |
| [^38^] | Digital Applied — "LinkedIn Algorithm 2026" | February 2026 | Guide |
| [^39^] | Social Media Today — "LinkedIn Updates Feed Algorithm" | May 2022 | News |
| [^41^] | Dev.to — "LinkedIn's Algorithm in 2025" | December 2025 | Analysis |
| [^42^] | Diginomica — "LinkedIn's algorithm uses 'proxy bias'" | January 2026 | Analysis |
| [^46^] | Falia — "360Brew: LinkedIn's New Algorithm Explained" | April 2026 | Analysis |
| [^49^] | Pettauer — "LinkedIn 360Brew: The New Physics of Visibility" | January 2026 | Research Report |
| [^50^] | Ozigi — "How to Make Your LinkedIn Content Stand Out in 2026" | April 2026 | Guide |
| [^52^] | Hootsuite — "How the LinkedIn algorithm works in 2025" | January 2026 | Guide |
| [^55^] | arXiv — "LinkSAGE: Optimizing Job Matching Using GNNs" (KDD 2024) | February 2024 | Academic Paper |
| [^58^] | Digital Applied — "LinkedIn Algorithm 2026: Engagement Strategy Guide" | February 2026 | Guide |
| [^60^] | ACM KDD — "LiGNN: Graph Neural Networks at LinkedIn" | August 2024 | Academic Paper |
| [^61^] | Foundera — "Will LinkedIn Penalize AI-Generated Posts in 2026?" | May 2026 | Analysis |
| [^62^] | Meet Lea — "LinkedIn Algorithm Explained 2026" | April 2026 | Guide |
| [^64^] | Botdog — "5 Biggest LinkedIn Algorithm Changes In 2026" | March 2026 | Analysis |
| [^73^] | Techawave — "LinkedIn Targets AI-Generated Content" | May 2026 | News |
| [^75^] | Fady Ramzy — "Guide to LinkedIn 360Brew" | December 2025 | Analysis |
| [^77^] | ConnectSafely — "LinkedIn Comment Automation Guide 2026" | April 2026 | Guide |
| [^78^] | Buffer — "How LinkedIn's Algorithm Works in 2026" | December 2025 | Guide |
| [^79^] | ClientsFirst — "LinkedIn Is Using Your Data to Train AI" | October 2025 | News |
| [^84^] | arXiv — "Large Scale Retrieval for LinkedIn Feed using Causal Language Models" | October 2025 | Academic Paper |
| [^88^] | OECD.AI — "The LinkedIn Fairness Toolkit (LiFT)" | September 2022 | Technical Tool |
| [^96^] | arXiv — LiGNN Paper (Full Text) | February 2024 | Academic Paper |
| [^102^] | Peerlist — "AI 'Slop' on LinkedIn and X" | March 2026 | Research |

---

*Research compiled: June 2026*
*Confidence assessment methodology: HIGH = multiple corroborating sources including official statements/engineering papers; MEDIUM-HIGH = official confirmation with limited technical detail; MEDIUM = industry analysis with consistent patterns but no official confirmation of specific claims.*
