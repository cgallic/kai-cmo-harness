# Facet: Third-Party Analysis & Reverse Engineering — LinkedIn AI Systems

## Key Findings

- LinkedIn's algorithm has been the subject of extensive third-party analysis, with independent researchers analyzing millions of posts to reverse-engineer its behavior [^1^][^2^][^3^]
- The most significant third-party finding is that LinkedIn replaced its fragmented algorithmic infrastructure with a unified 150-billion-parameter foundation model called **360Brew**, as documented in an arXiv paper (later withdrawn) and extensively analyzed by Trust Insights, AuthoredUp, and others [^4^][^5^]
- Independent academic audits have found measurable gender and racial bias in LinkedIn's Talent Search and job recommendation systems, with some groups experiencing significant under-representation in early search results [^6^][^7^][^8^]
- AI detection company Originality.ai found that **54% of long-form LinkedIn posts are likely AI-generated**, with AI posts receiving 45% less engagement on average [^9^][^10^]
- Data analyst **Daniel Hall** (SpotAPod) has exposed engagement pod networks affecting 200+ creators, discovering a critical security vulnerability in Lempod that compromised 10,000+ user accounts [^11^][^12^]
- **Shelly Palmer** and other critics argue that LinkedIn's pattern-based AI slop detection is a "neverending game of Whac-A-Mole" that cannot distinguish AI-assisted good writing from bot-generated content [^13^][^14^]
- **Richard van der Blom** (Just Connecting) has conducted the longest-running independent annual analysis of LinkedIn's algorithm, examining 1.8 million+ posts in his 2025 report [^1^]
- **Trust Insights** (Christopher Penn) synthesized ~400,000 words of LinkedIn engineering publications into an "Unofficial LinkedIn Algorithm Guide" using generative AI, identifying 14 distinct AI systems working together [^5^]

---

## Analyses by Type

### 1. Independent Algorithm Analyses (Large-Scale Observational Studies)

#### Richard van der Blom / Just Connecting — Annual Algorithm Research (2021–2025)
- **Author/Org**: Richard van der Blom, Founder of Just Connecting HUB (Netherlands)
- **Methodology**: Annual large-scale observational studies examining 9,500+ posts (2022), scaling to 1.8 million posts by 2025, from 200+ members across 30+ countries. Team spent 1,100+ hours on research.
- **Key Findings**: 
  - Posts between 1,200–1,600 characters perform ~2.4x better in reach and engagement than posts under 1,000 characters
  - Dwell time diminished in importance for special format posts (document posts, video, multiple pictures)
  - Reach dropped ~50% for 95% of creators year-on-year; follower growth fell 31%, engagement down 25%
  - Top Creator visibility climbed from 15% (2022) to 31% (2025) while "Other Creator" visibility collapsed from 57% to 28%
  - Hashtag impact weakened significantly; first 3 hashtags give content an SEO boost but 6+ hashtags split the signal
- **Confidence**: High — longest-running independent study with transparent methodology
- **Source**: [mediarama.io](https://mediarama.io/wp-content/uploads/2023/03/Linkedin-algorithm-research-2023.pdf) [^1^], [3thinkrs.com](https://3thinkrs.com/ten-things-to-know-about-linkedins-algorithm-in-2025/) [^15^]

#### LinkPost / Yannis Haismann — LinkedIn Algorithm Playbook 2026 (438,413 Posts)
- **Author/Org**: Yannis Haismann, founder of LinkPost
- **Methodology**: Research-grade analysis of 438,413 posts and 5,291,997 comments from 24,006 creators (62% French, 15% English, 93% published 2024–2026), using NLP-based tactic detection
- **Key Findings**:
  - Carousel posts deliver highest median reach (1,410 impressions vs. 569–622 for other formats) — a 2.3x advantage
  - Highly controversial posts (score ≥ 0.7) generate 2.75x more likes and 1.52x more comments
  - Posts of 1,500+ characters average 49% more engagement than posts under 300 characters
  - In top 1% viral posts: quantified proof (61%), open-loop (47%), memorable quote (45%), polarization (25%) are most over-represented tactics
  - Viral posts average 4–6 detected tactics stacked together; single-tactic posts rarely cross viral threshold
- **Confidence**: High — largest independent dataset analyzed; author discloses limitations as observational/correlational
- **Source**: [linkpost.gg](https://www.linkpost.gg/en/playbooks/linkedin-algorithm-playbook-2026/study) [^2^]

#### AuthoredUp — Multi-Million Post Analytics (2025–2026)
- **Author/Org**: AuthoredUp platform (participated in van der Blom's research analyzing 600,000+ posts)
- **Methodology**: NLP-aware analysis of 3M+ posts; tracks saves, followers gained per post, and profile views
- **Key Findings**:
  - Saves drive 5x more reach than likes and 2x more than comments under 360Brew
  - Delayed engagement (24–72 hours after publishing) performs 4–6x better because 360Brew sees late engagement as lasting value
  - Comments count "roughly twice as much as likes" with NLP-aware quality scoring — generic "Great post!" replies no longer boost reach
  - Posts that generate comment threads (back-and-forth conversations) trigger "aggressive reach expansion"
  - Takes ~90 days of aligned posting for 360Brew to fully categorize a creator
- **Confidence**: High — commercial platform with access to large-scale post data
- **Source**: [authoredup.com](https://authoredup.com/blog/linkedin-360brew) [^3^], [botdog.co](https://botdog.co/blog-posts/linkedin-algorithm-changes-2026) [^16^]

#### Hootsuite — LinkedIn Algorithm Analysis (2026)
- **Author/Org**: Hootsuite Research
- **Methodology**: Analysis of LinkedIn Engineering Blog and platform behavior
- **Key Findings**:
  - Three-step process: Quality filtering → Engagement testing → Network/relevance ranking
  - LinkedIn now emphasizes expertise more than ever; rewards active creators and subject-matter experts
  - "Golden hour" system refined: strong interaction in first hour leads to 2nd/3rd-degree distribution
  - Prioritizing relevance over recency: older posts (2–3 weeks) shown if more relevant
  - External links significantly deprioritized; native content (text, carousels, video) boosted
- **Confidence**: Medium-High — established social media analytics firm
- **Source**: [blog.hootsuite.com](https://blog.hootsuite.com/linkedin-algorithm/) [^17^]

---

### 2. Reverse Engineering & Technical Architecture Analyses

#### Trust Insights — The Unofficial LinkedIn Algorithm Guide (2025–2026)
- **Author/Org**: Christopher Penn and Trust Insights team
- **Methodology**: Synthesized ~400,000 words of source material from 31+ primary LinkedIn engineering publications (including 20 current 2025–2026 publications), using Google Gemini 2.5 Pro and Anthropic Claude to analyze. Generated a ~275,000-word technical guide.
- **Key Claims**:
  - LinkedIn's feed is not one algorithm but **14 distinct AI systems** working together
  - Under 360Brew, the system uses a two-stage pipeline: (1) LLM-powered retrieval using LLaMA-3 dual encoder generating semantic embeddings, and (2) Generative Recommender sequential transformer processing 1,000+ historical interactions
  - The system creates a "personalized version" of the model for each user by analyzing 2–3 months of activity ("many-shot in-context learning")
  - Language quality determines retrieval; engagement patterns determine ranking
  - Profile data directly feeds both retrieval and ranking models — profile is "foundational input"
  - The LLM-Ranker approach (using LLM to directly score posts) was "evaluated and rejected" for production due to difficulty encoding numeric features and poor performance on network-based recommendations
- **Direct Quote**: "The old game of sending numerical signals to a mechanical system is over. In its place, LinkedIn now uses two complementary systems: an LLM-powered retrieval system that reads language and a sequential ranking system that learns from behaviour over time." [^5^]
- **Confidence**: High — most technically rigorous third-party analysis, with extensive source citations
- **Source**: [trustinsights.ai](https://www.trustinsights.ai/wp-content/uploads/2025/05/the_unofficial_linkedin_algorithm_guide_for_marketers_mid_2025_edition.pdf) [^5^], [christopherspenn.com](https://www.christopherspenn.com/2025/05/almost-timely-news/) [^18^]

#### ViralBrain.ai — How LinkedIn Detects AI Content (Reconstructed Classifier)
- **Author/Org**: ViralBrain.ai
- **Methodology**: Reconstruction of LinkedIn's content classification system based on patent filings, engineering blog posts, and observable behavior
- **Key Claims on LinkedIn's Detection Approach**:
  - **Content-level analysis**: Examines vocabulary distribution, sentence structure variety, transition patterns, and emotional range. "AI content scores as boring at a very high rate."
  - **Account-level pattern matching**: Tracks consistent style across weeks/months — "Real humans have bad days. AI accounts don't have bad days."
  - **Engagement-feedback loops**: "The most powerful 'detector' is simply the engagement data... LinkedIn doesn't need to solve the hard problem of AI detection. They just need to solve the easy problem of quality detection."
- **Direct Quote**: "The best defense against algorithmic suppression isn't 'write everything by hand.' It's 'produce content that generates real engagement.' If you can use AI and still produce engaging, distinctive content, the algorithm won't care." [^19^]
- **Confidence**: Medium — informed speculation based on public sources
- **Source**: [viralbrain.ai](https://www.viralbrain.ai/blog/how-linkedin-detects-ai-content-and-what-happens-when-it-does) [^19^]

#### The Linked Blog / Oleksandr Melnyk — 360Brew Verification Analysis
- **Author/Org**: Oleksandr Melnyk, The Linked Blog
- **Methodology**: Review of official sources vs. online speculation; tracked only confirmed information
- **Key Findings**:
  - No official LinkedIn Engineering Blog post announced a deployment date for 360Brew
  - No official timeline for when 360Brew began influencing the feed
  - No public confirmation that the feed algorithm has fully transitioned to 360Brew
  - "The research describes architecture, performance tests, and capabilities, but not rollout timing"
- **Confidence**: High — careful separation of confirmed facts from speculation
- **Source**: [thelinkedblog.com](https://thelinkedblog.com/2025/360brew-linkedin-algorithm-new-update-3619/) [^20^]

---

### 3. Academic Studies (Peer-Reviewed & Preprint)

#### "360Brew: A Decoder-only Foundation Model for Personalized Ranking and Recommendation" (arXiv 2501.16450)
- **Authors**: Hamed Firooz, Maziar Sanjabi, et al. (23 authors from LinkedIn's Foundation AI Technologies team)
- **Published**: January 27, 2025 (later withdrawn by Hamed Firooz, but widely cited and mirrored)
- **Key Claims**:
  - 150B parameter decoder-only model built on Mixtral 8x22 architecture
  - Trained/fine-tuned on LinkedIn's first-party data (users outside EU)
  - Capable of solving 30+ predictive tasks across 8+ surfaces (feed, jobs, People You May Know, ads, search, notifications)
  - Uses "many-shot in-context learning" — conditions on member profile and interaction history
  - Achieves performance comparable to or exceeding current production systems without task-specific fine-tuning
  - Generalizes to out-of-domain tasks; performs better than production models for "cold-start" members with fewer interactions
  - Performance less affected by temporal distribution shifts vs. baseline models
- **Third-Party Analysis**: Trust Insights noted the paper was withdrawn but the architecture was "heavily drawn from" in LinkedIn's March 2026 engineering blog announcement [^4^][^5^]
- **Confidence**: High (internal research paper, withdrawn but technically credible)
- **Source**: [ar5iv.labs.arxiv.org](https://ar5iv.labs.arxiv.org/html/2501.16450) [^4^], [arxiv.org/abs/2501.16450](https://arxiv.org/abs/2501.16450) [^21^]

#### "An Industrial-Scale Sequential Recommender for LinkedIn Feed Ranking" (arXiv 2026 / Feed SR)
- **Authors**: Lars Hertel, Gaurav Srivastava, et al. (LinkedIn Engineering)
- **Published**: February 2026
- **Key Claims**:
  - Feed SR is a transformer-based sequential ranking model that replaced a DCNv2-based ranker
  - Shows +2.10% time spent improvement in online A/B tests
  - Processes member interaction histories with causal attention mask
  - Uses RoPE (Rotary Position Embedding) for capturing evolving interests
  - Position debiasing via Inverse Propensity Weighting and learned position offsets
  - Daily incremental training on new interaction data
  - **LLM-Ranker was explored and rejected**: "The LLM-Ranker never achieved superior online performance over the existing production model... it was difficult to encode the strength of network relationships in a text prompt"
- **Third-Party Significance**: Confirms that the production system (Feed SR) differs from the 360Brew research model
- **Confidence**: High — peer-reviewed style paper from LinkedIn Engineering
- **Source**: [arxiv.org/html/2602.12354v1](https://arxiv.org/html/2602.12354v1) [^22^]

#### "LiRank: Industrial Large Scale Ranking Models at LinkedIn" (KDD 2024)
- **Authors**: Fedor Borisyuk, Mingzhou Zhou, et al. (LinkedIn)
- **Published**: ACM SIGKDD 2024
- **Key Claims**:
  - Large-scale ranking framework with Residual DCN architecture
  - Deployed for Feed ranking, Job Recommendations, and Ads CTR prediction
  - Results: +0.5% member sessions in Feed, +1.76% qualified job applications, +4.35% Ads CTR
  - Techniques for quantization and vocabulary compression for production deployment
  - Deep learning-based explore/exploit methods
- **Third-Party Significance**: Provides technical foundation for understanding pre-360Brew architecture
- **Confidence**: High — published at top-tier ML conference
- **Source**: [arxiv.org/pdf/2402.06859](https://arxiv.org/pdf/2402.06859) [^23^]

#### "An External Fairness Evaluation of LinkedIn Talent Search" (AAAI 2026)
- **Authors**: Tina Behzad (Stony Brook), Siddartha Devic, Vatsal Sharan (USC), Aleksandra Korolova (Princeton), David Kempe (USC)
- **Published**: AAAI 2026
- **Methodology**: Independent third-party audit using real-world LinkedIn Recruiter Talent Search results; collected rankings across diverse occupational queries; developed demographic inference pipeline; used deviation from group proportions and MinSkew@k metrics
- **Key Findings**:
  - **Under-representation of minority groups in early ranks** across many queries
  - Women show more extreme and variable skew values at early ranks
  - Temporal disparities in exposure and retention — some groups experience greater volatility in ranked positions over multiple days
  - LinkedIn's reported fairness improvements (Geyik et al. 2019) may not fully capture disparities visible in external audit
  - "Demographic disparities in this temporal stability, with some groups experiencing greater volatility"
- **Direct Quote**: "Our analysis reveals an under-representation of minority groups in early ranks across many queries. We further examine potential causes of this disparity, and discuss why they may be difficult or, in some cases, impossible to fully eliminate among the early ranks of queries." [^6^]
- **Confidence**: Very High — independent academic audit from top-tier universities, published at major AI conference
- **Source**: [arxiv.org/html/2511.10752v1](https://arxiv.org/html/2511.10752v1) [^6^]

#### "Choosing an Algorithmic Fairness Metric for an Online Marketplace: Detecting and Quantifying Algorithmic Bias on LinkedIn" (2022)
- **Authors**: YinYin Yu (LinkedIn), Guillaume Saint-Jacques (Apple)
- **Published**: arXiv 2202.07300
- **Key Claims**:
  - Derived fairness metric from "equal opportunity for equally qualified candidates" for two-sided marketplace recommendation algorithms
  - Borrowed from economic literature on discrimination to detect bias solely attributable to the algorithm (not societal inequality or human bias)
  - Measured and quantified algorithmic bias with respect to gender in two LinkedIn algorithms
  - Framework for distinguishing algorithmic bias from human bias on two-sided platforms
  - Discussed shortcomings of common fairness metrics
- **Confidence**: High — authored by LinkedIn researcher but published externally
- **Source**: [arxiv.org/pdf/2202.07300](https://arxiv.org/pdf/2202.07300) [^7^]

#### "Auditing for Discrimination in Algorithms Delivering Job Ads" (WWW 2021)
- **Authors**: Basileal Imana, Aleksandra Korolova, John Heidemann
- **Published**: ACM Web Conference (WWW) 2021
- **Methodology**: Black-box auditing of Facebook and LinkedIn ad delivery algorithms for discrimination; controlled for job qualifications; compared delivery of concurrent ads for similar jobs at companies with different gender distributions
- **Key Findings**:
  - Confirmed skew by gender in ad delivery on **Facebook** that could not be justified by qualification differences
  - **Failed to find skew in ad delivery on LinkedIn**
  - Methodology distinguishes skew due to protected categories from skew due to qualification differences
  - Notes LinkedIn had made "efforts to integrate fairness metrics into some of its recommendation systems"
- **Confidence**: High — published at top conference, rigorous methodology
- **Source**: [dl.acm.org/doi/fullHtml/10.1145/3442381.3450077](https://dl.acm.org/doi/fullHtml/10.1145/3442381.3450077) [^8^]

#### "Utilizing Data Driven Methods to Identify Gender Bias in LinkedIn Profiles" (Information Processing & Management, 2025)
- **Authors**: Academic research team
- **Published**: Information Processing & Management, June 2025
- **Methodology**: Universal Sentence Encoder + kernel two-sample test; TF-IDF with cosine similarity for skill repetition patterns; t-test analysis
- **Key Findings**:
  - Statistically significant gender bias between men and women in most sub-groups of LinkedIn technical positions
  - Gender gaps in textual self-presentation that can affect AI-enabled recruitment systems
  - Number of repeated skills in LinkedIn profiles may impact candidates' ranking
- **Confidence**: High — peer-reviewed journal publication
- **Source**: [sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0306457323001607) [^24^]

#### IZA Discussion Paper: "Measuring Bias in Job Recommender Systems: Auditing..." (2024)
- **Institution**: IZA Institute of Labor Economics
- **Methodology**: Controlled experiment with fictitious profiles on LinkedIn, ZipRecruiter, and Monster; harvested job recommendations across multiple rounds; measured gender differences
- **Key Findings**:
  - Men's profiles are **11.5% more likely to be viewed by recruiters** than identical female profiles
  - Recommendation systems directed different jobs to male vs. female profiles
  - Item-Based Collaborative Filtering (IBCF) can amplify gender gaps if real users disproportionately apply to gender-stereotypical jobs
  - "Recruiters have a strong preference for newly posted resumes"
- **Confidence**: High — academic labor economics institute
- **Source**: [repec.iza.org/dp17245.pdf](https://repec.iza.org/dp17245.pdf) [^25^]

---

### 4. SEO/Content Strategy & Gaming Analyses

#### Originality.ai — LinkedIn AI Content Studies (2024–2025)
- **Author/Org**: Originality.ai (AI detection company led by Jonathan Gillham)
- **Methodology**: Analyzed 8,795 LinkedIn long-form posts (100+ words) from January 2018 to October 2024; updated 2025 study of 3,368 posts from 99 influential profiles
- **Key Findings**:
  - **54% of long-form LinkedIn posts are likely AI-generated** (as of October 2024)
  - 189% surge in AI usage in LinkedIn posts after ChatGPT's release (Jan–Feb 2023)
  - Post length increased by 107% since ChatGPT launched
  - Likely-AI-generated posts received **45% less engagement** than likely-original posts
  - Some industries show extreme AI adoption: Design/Architecture (100%), Wellness (92%)
  - Human-written posts outperform AI in healthcare (+44%) and government/public affairs (+40%)
- **Wired Coverage**: Kate Knibbs (Wired) reported: "From one angle, LinkedIn may have inadvertently created the ideal laboratory for AI writing. Nobody's logging on expecting profundity, hilarity, or sincerity." [^10^]
- **Confidence**: Medium-High — commercial tool with potential detection bias, but large sample sizes
- **Source**: [originality.ai/blog/ai-content-published-linkedin](https://originality.ai/blog/ai-content-published-linkedin) [^9^], [wired.com](https://www.wired.com/story/linkedin-ai-generated-influencers/) [^10^]

#### Daniel Hall / SpotAPod — Engagement Pod Exposé (2020–2024)
- **Author/Org**: Daniel Hall, data analytics expert and founder of SpotAPod
- **Methodology**: Created proprietary algorithm measuring engagement patterns; joined thousands of pods to study from inside; collected data and screenshots as evidence
- **Key Findings**:
  - Discovered vulnerability in Lempod (popular engagement pod tool) allowing hackers to access LinkedIn credentials of 10,000+ users
  - LinkedIn confirmed the vulnerability (April 2024)
  - Has list of 200+ LinkedIn creators found using engagement pods
  - "The platform was riddled with bots talking to themselves"
  - Estimated **25% of LinkedIn traffic may be bots/fake accounts** (citing Lunio study)
  - AI-generated comments in pods use macros pulling in creator first names to appear personalized
- **Direct Quote**: "What if my posts and the things that I posted were fake news about how somebody was committed of treason and I had somebody drop a comment that supported that? All of a sudden, I've completely... destroyed their brand." [^11^]
- **Confidence**: High — demonstrated evidence, vulnerability confirmed by LinkedIn
- **Source**: [thewritereflection.com](https://www.thewritereflection.com/2024/05/23/the-dark-side-of-social-media-engagement-pods/) [^11^], [theaioptimist.com](https://www.theaioptimist.com/p/linkedins-fake-followers-how-25-ai) [^12^]

#### Peerlist — "AI 'Slop' on LinkedIn and X: Evidence, Drivers, Harms, Detection" (2026)
- **Author/Org**: Daniel Sine (Peerlist)
- **Methodology**: Comprehensive analysis of AI slop phenomenon; reviewed SlopScore tool; comparative analysis of detection approaches
- **Key Findings**:
  - Slop creates "synthetic credibility" — generic, confident-sounding explanations without sourcing can mislead at scale
  - Pattern-based detection tools (SlopScore, DeSlop) work better than authorship detectors
  - Key lesson: "OpenAI's classifier sunset is a warning that brittle detectors can do harm; treat detection scores as prompts for review, not verdicts"
  - Practical mitigation: combine content-based features, account-level behavior, interaction anomalies
- **Confidence**: High — balanced analysis with methodological caveats
- **Source**: [peerlist.io/danielsinewe](https://peerlist.io/danielsinewe/articles/ai-slop-on-linkedin-and-x-evidence-drivers-harms-detection-a) [^26^]

---

### 5. Comparative Studies (LinkedIn vs. Other Platforms)

#### WestOwls — LinkedIn vs. X for Founders (2026)
- **Dimensions compared**: 12 (audience quality, organic reach, content longevity, investor reach, speed, format depth, SEO, tech community, platform stability, hiring, customer acquisition, time-to-results)
- **Verdict**: LinkedIn wins 8 of 12 dimensions; X wins 3 (speed, tech/startup community, time-to-results); 1 tie
- **Key Finding**: "For most founders, the right answer is not LinkedIn or X. It is LinkedIn first, then X, if the specific conditions are right." [^27^]
- **Source**: [westowls.com](https://www.westowls.com/post/linkedin-vs-twitter-x-for-founders-which-platform-builds-better-brands) [^27^]

#### HashMeta — LinkedIn vs. X B2B Platform Comparison (2025)
- **Key Findings**: LinkedIn reaches 4 of 5 business decision-makers; generates 3x more B2B leads; higher cost-per-click but better conversion. X lower CPC ($0.50–$2.00) but weaker B2B conversion.
- **Source**: [hashmeta.com](https://hashmeta.com/blog/linkedin-vs-twitter-x-the-ultimate-b2b-platform-comparison-for-strategic-growth/) [^28^]

---

### 6. Algorithm Audits: Bias, Fairness & Transparency

#### LinkedIn's Self-Reported Bias Mitigation (2018–2023)
- **Key Event**: MIT Technology Review reported (June 2021) that LinkedIn discovered its job-matching AI was producing biased results — ranking candidates partly on likelihood to apply, which referred more men than women because men are "often more aggressive at seeking out new opportunities" [^29^]
- **LinkedIn's Response**: Built a separate AI algorithm deployed in 2018 to counteract the bias, ensuring "representative distribution of users across gender" before referring matches
- **Comparison**: Monster and CareerBuilder took different approaches; ZipRecruiter claimed its algorithms don't use names but classify on 64 other information types
- **Criticism**: "Since these platforms don't disclose exactly how their systems work, it's hard for job seekers to know how effective any of these measures are" [^29^]
- **Source**: [technologyreview.com](https://www.technologyreview.com/2021/06/23/1026825/linkedin-ai-bias-ziprecruiter-monster-artificial-intelligence/) [^29^]

#### Clemson's Open Textbook — "Digital Networking: AI Algorithm Biases" (2024)
- **Key Findings**: 
  - LinkedIn's algorithm has "sample bias, preferring male users in STEM disciplines or those from higher-ranking institutions disproportionately" (citing Zhang & Vucetic 2016)
  - LinkedIn's AI suggests job postings based on prior experiences rather than potential, restricting career mobility
  - Profile pictures from underrepresented groups may get reduced engagement due to unconscious biases
- **Source**: [opentextbooks.clemson.edu](https://opentextbooks.clemson.edu/sciencetechnologyandsociety/chapter/digital-networking-ai-algorithm-biases/) [^30^]

#### Social Media Today — LinkedIn Feed Algorithm Update Coverage (March 2026)
- **Key Claims**:
  - LinkedIn's improved ranking system is "designed to be more aligned with evolving news"
  - "When industry news breaks and relevant posts start getting traction, you see them within minutes"
  - New members with limited history will see more relevant recommendations
  - "Improved auditing models will ensure more competitive fairness and a more trustworthy feed"
  - Engagement bait to be reduced over coming months; recycled thought leadership downranked
- **Source**: [socialmediatoday.com](https://www.socialmediatoday.com/news/linkedin-updates-its-feed-algorithm/814638/) [^31^]

---

### 7. Critics & Controversial Voices

#### Shelly Palmer — "LinkedIn Declares War On AI Slop" (May 2026)
- **Credentials**: AI keynote speaker, technology commentator
- **Key Arguments**:
  - Pattern-based detection of "contrastive construction" ("it's not X, it's Y") is flawed because LLMs learned it from human writers who used it for decades
  - "Detecting 'contrastive construction' as a signal of AI writing is a great example of why pattern-based detection fails"
  - Arms race dynamic: "Now that LinkedIn has announced the signal, the slop generators will stop using it"
  - Fundamental problem: "The detection model has no way to tell [AI-assisted human] from a bot that scraped a competitor's post and ran it through a paraphraser. Both look identical from the outside."
  - Harms legitimate users: "A significant percentage of LinkedIn professionals have useful judgment and weak prose. AI assistance helps them communicate better... The fix removes the thinkers and the bots."
- **Direct Quote**: "LinkedIn's heart is in the right place, as its news feed is all but unreadable. The structural fix is to reward original thinking and surface expertise. Pattern detection is a treadmill." [^13^]
- **Confidence**: High — expert commentary with incisive critique
- **Source**: [sasktoday.ca](https://www.sasktoday.ca/opinion/shelly-palmer-linkedin-declares-war-on-ai-slop-12299592) [^13^], [shellypalmer.com](https://shellypalmer.com/2026/05/linkedin-declares-war-on-ai-slop/) [^14^]

#### SlopScore — Third-Party Detection Tool Analysis
- **Product**: Chrome extension ($24/month) that analyzes posts for "AI signals, engagement bait, and formulaic hooks"
- **Methodology**: Pattern-based signals (AI vocabulary, template hooks, engagement bait CTA, stacked formatting); explicitly "not a definitive AI detector"
- **Key Insight**: "Bounded claims" design — scores posts not people, visible samples not hidden histories, to avoid false accusation harms
- **Limitation**: "Style bias risk — 'AI vocabulary' and formatting signals may overlap with legitimate professional writing styles"
- **Source**: [peerlist.io](https://peerlist.io/danielsinewe/articles/ai-slop-on-linkedin-and-x-evidence-drivers-harms-detection-a) [^26^]

#### DeSlop — Open-Source Browser Extension
- **Product**: Open-source Chrome extension (GitHub: HxHippy/DeSlop)
- **Features**: 600+ patterns across 11 languages; three-tier detection; local processing with zero API calls; LinkedIn-specific fixer (blocks auto-play videos, ad tracking)
- **Philosophy**: Pattern-based content filtering that runs entirely in browser
- **Source**: [github.com/HxHippy/DeSlop](https://github.com/HxHippy/DeSlop) [^32^]

---

## Key External Researchers/Organizations

| Researcher/Organization | Work/Relevance | Confidence |
|------------------------|----------------|------------|
| **Richard van der Blom** (Just Connecting) | Annual algorithm studies since 2021; 1.8M+ posts analyzed; longest-running independent research | High |
| **Yannis Haismann** (LinkPost) | 438K-post study with NLP tactic detection; research-grade methodology | High |
| **Christopher Penn** (Trust Insights) | "Unofficial LinkedIn Algorithm Guide" synthesizing 400K words of engineering sources; identified 14 AI systems | High |
| **Daniel Hall** (SpotAPod) | Exposed 200+ creators in engagement pods; discovered Lempod vulnerability; bot traffic research | High |
| **Shelly Palmer** | AI keynote speaker; prominent critic of pattern-based detection; "Whac-A-Mole" framing | High |
| **Originality.ai** (Jonathan Gillham) | Found 54% AI-generated content on LinkedIn; 45% engagement penalty for AI posts | Medium-High |
| **Aleksandra Korolova** (Princeton) | Led external fairness audits of LinkedIn Talent Search (AAAI 2026) and ad delivery (WWW 2021) | Very High |
| **Tina Behzad** (Stony Brook) / **David Kempe** (USC) / **Vatsal Sharan** (USC) | "An External Fairness Evaluation of LinkedIn Talent Search" — independent third-party bias audit | Very High |
| **YinYin Yu** (LinkedIn) / **Guillaume Saint-Jacques** | Derived fairness metrics for LinkedIn's two-sided marketplace algorithms | High |
| **Basileal Imana** / **John Heidemann** | Audited LinkedIn job ad delivery for discrimination (WWW 2021) | High |
| **ViralBrain.ai** | Reconstructed LinkedIn's content classifier from patents and observable behavior | Medium |
| **Daniel Sine** (Peerlist) | Comprehensive analysis of AI slop on LinkedIn and detection methodologies | High |

---

## Trends & Signals

- **Shift from Social Graph to Interest Graph**: Multiple independent sources confirm LinkedIn's algorithm moved from connection-based distribution (who you know) to topic-based distribution (what you know) [^3^][^16^]. This is described as "the most significant algorithmic shift in LinkedIn's history" [^33^].
- **Pattern Detection Arms Race**: Critics like Shelly Palmer and Peerlist's Daniel Sine warn that pattern-based AI detection is fundamentally adversarial — announced signals become obsolete as generators adapt [^13^][^26^].
- **Independent Audits Increasing**: Academic third-party audits of LinkedIn are becoming more sophisticated — from ad delivery (WWW 2021) to Talent Search ranking (AAAI 2026), with explicit frameworks for black-box evaluation [^6^][^8^].
- **Creator Reach Declining**: Multiple independent studies (van der Blom, AuthoredUp, Botdog, TheShieldIndex) confirm 40–50% organic reach drops, with company pages hit hardest (reach from 7% in 2021 to 1–2% in 2024) [^15^][^16^][^34^].
- **Engagement Pods Under Siege**: LinkedIn's 2026 enforcement with claimed 97% detection accuracy has made pods "entirely ineffective" per VP Gyanda Sachdeva; Lempod banned from Chrome Web Store [^35^][^36^].
- **Saves > Likes > Comments**: New engagement hierarchy under 360Brew — saves drive 5x more reach than likes, with delayed engagement (24–72 hours) performing 4–6x better [^3^][^16^].
- **Academic-Industry Gap**: LinkedIn publishes extensive engineering research (360Brew, Feed SR, LiRank, LiGNN) but third-party analyses suggest production systems differ from published research models [^20^][^22^].
- **Video Content Paradox**: Video reach down 72% overall, but native video (30–90s) hitting 5.6% engagement rates — the algorithm is "format-agnostic" but user behavior drives low completion rates [^3^][^37^].

---

## Controversies & Conflicting Claims

1. **360Brew Deployment Status**: Trust Insights and many creator blogs claim 360Brew is actively running LinkedIn's feed, while The Linked Blog's Oleksandr Melnyk notes there is "no official confirmation" and the exact deployment percentage is unknown. The Feed SR paper (Feb 2026) suggests a different model may be in production. [^4^][^5^][^20^][^22^]

2. **AI Detection Accuracy**: Originality.ai claims 54% AI content and 45% engagement penalty, but their commercial AI detector has mixed independent benchmarks. Peerlist's analysis warns that "OpenAI's classifier sunset is a warning that brittle detectors can do harm." Shelly Palmer argues the approach is inherently adversarial. [^9^][^10^][^13^][^26^]

3. **LinkedIn's Bias Claims vs. Independent Audit**: LinkedIn's self-reports (Geyik et al. 2019) claim significant fairness improvements, but the external AAAI 2026 audit by Korolova et al. found "under-representation of minority groups in early ranks" and temporal disparities not captured by internal metrics. [^6^][^29^]

4. **Reach Drop Narrative**: While independent studies consistently report 40–50% reach declines, LinkedIn's official position (via Engineering Blog and product announcements) frames the changes as improving relevance and quality, not reducing distribution. The discrepancy may reflect a shift from broad reach to targeted reach. [^15^][^16^][^31^]

5. **Engagement Pod Effectiveness**: Some marketing blogs (Digital Applied, ConnectSafely) claim pods are "dead" with 97% detection accuracy, while others (LinkedHelper) note they still exist and enforcement is uneven. Daniel Hall's research suggests the problem remains significant. [^35^][^36^][^38^][^11^]

6. **The "14 Algorithms" Claim**: Trust Insights claims there are 14 distinct AI systems, which has been widely repeated. However, this is based on synthesis of engineering publications and may not reflect the actual current production architecture, which may have consolidated under 360Brew/Feed SR. [^5^][^18^]

---

## Recommended Deep-Dive Areas

1. **LinkedIn Talent Search External Fairness Audit (AAAI 2026)**: The Korolova et al. paper represents the most rigorous independent audit of a major platform's hiring algorithm. Its methodology for black-box evaluation, temporal disparity analysis, and comparison against self-reported fairness metrics warrants detailed examination. [^6^]

2. **360Brew vs. Feed SR Architecture Gap**: There is significant confusion about what model actually runs LinkedIn's feed. The 360Brew paper was withdrawn; Feed SR paper describes a different architecture. Understanding what LinkedIn actually deployed requires careful comparison of the arXiv papers, Engineering Blog posts, and third-party technical analyses. [^4^][^22^][^20^]

3. **Engagement Pod Ecosystem & Detection**: Daniel Hall's SpotAPod research represents the most detailed insider investigation of LinkedIn's manipulation ecosystem. The Lempod vulnerability, the 200+ exposed creators, and the estimated 25% bot traffic figure suggest a significant platform integrity issue that warrants deeper analysis. [^11^][^12^]

4. **Pattern-Based Detection Arms Race**: Shelly Palmer's critique and the SlopScore/DeSlop approaches illustrate a fundamental tension in platform moderation. The scholarly analysis by Peerlist provides a framework for understanding why authorship detection fails and what alternatives exist. [^13^][^14^][^26^][^32^]

5. **Trust Insights' Synthesis Methodology**: The use of generative AI (Gemini 2.5 Pro, Claude) to synthesize 400,000 words of engineering material into actionable intelligence represents a novel approach to third-party platform analysis. Its strengths and limitations (the guide itself acknowledges possible "hallucinations") are worth studying. [^5^][^18^]

6. **Job Recommendation Bias Across Platforms**: The IZA paper comparing LinkedIn, ZipRecruiter, and Monster; the MIT Technology Review coverage; and LinkedIn's own bias mitigation efforts form a rich case study in platform self-regulation vs. external accountability. [^25^][^29^]

7. **AI Content Prevalence & Impact**: Originality.ai's finding of 54% AI content, combined with Wired's coverage and the 45% engagement penalty, raises questions about platform content quality and the effectiveness of AI detection. The 107% increase in post length suggests AI is fundamentally changing content norms. [^9^][^10^]

---

## Source Index

[^1^]: Richard van der Blom, "LinkedIn Algorithm Research 2023," Just Connecting HUB. https://mediarama.io/wp-content/uploads/2023/03/Linkedin-algorithm-research-2023.pdf

[^2^]: Yannis Haismann, "LinkedIn Algorithm Playbook 2026 — What 438,413 Posts Reveal About Reach in 2026," LinkPost Research, 2026. https://linkpost.gg/en/playbooks/linkedin-algorithm-playbook-2026/study

[^3^]: "LinkedIn Algorithm Explained 2026: Dwell Time, Comments & Reach," Meet Lea / AuthoredUp analysis, April 2026. https://meet-lea.com/en/blog/linkedin-algorithm-explained

[^4^]: H. Firooz et al., "360Brew: A Decoder-only Foundation Model for Personalized Ranking and Recommendation," arXiv:2501.16450, Jan 2025 (withdrawn). https://ar5iv.labs.arxiv.org/html/2501.16450

[^5^]: Christopher Penn / Trust Insights, "The Unofficial LinkedIn Algorithm Guide for Marketers, Mid 2025 Edition," May 2025. https://www.trustinsights.ai/wp-content/uploads/2025/05/the_unofficial_linkedin_algorithm_guide_for_marketers_mid_2025_edition.pdf

[^6^]: T. Behzad et al., "An External Fairness Evaluation of LinkedIn Talent Search," AAAI 2026, Nov 2025. https://arxiv.org/html/2511.10752v1

[^7^]: Y. Yu and G. Saint-Jacques, "Choosing an Algorithmic Fairness Metric for an Online Marketplace: Detecting and Quantifying Algorithmic Bias on LinkedIn," arXiv:2202.07300, 2022. https://arxiv.org/pdf/2202.07300

[^8^]: B. Imana, A. Korolova, J. Heidemann, "Auditing for Discrimination in Algorithms Delivering Job Ads," WWW 2021. https://dl.acm.org/doi/fullHtml/10.1145/3442381.3450077

[^9^]: J. Gillham, "Over ½ of Long Posts on LinkedIn are Likely AI-Generated Since ChatGPT Launched," Originality.ai, Oct 2025. https://originality.ai/blog/ai-content-published-linkedin

[^10^]: K. Knibbs, "Yes, That Viral LinkedIn Post You Read Was Probably AI-Generated," Wired, Nov 2024. https://www.wired.com/story/linkedin-ai-generated-influencers/

[^11^]: "The Dark Side of Social Media: Engagement Pods," The Write Reflection, May 2024. https://www.thewritereflection.com/2024/05/23/the-dark-side-of-social-media-engagement-pods/

[^12^]: "LinkedIn's Fake Followers: How 25% AI Bots are Flooding Your Feed," The AI Optimist / SpotAPod, Sep 2024. https://www.theaioptimist.com/p/linkedins-fake-followers-how-25-ai

[^13^]: Shelly Palmer, "LinkedIn Declares War On AI Slop," SaskToday, May 2026. https://www.sasktoday.ca/opinion/shelly-palmer-linkedin-declares-war-on-ai-slop-12299592

[^14^]: Shelly Palmer, "LinkedIn Declares War On AI Slop," shellypalmer.com, May 2026. https://shellypalmer.com/2026/05/linkedin-declares-war-on-ai-slop/

[^15^]: "Ten things to know about LinkedIn's algorithm in 2025," 3Thinkrs, May 2025. https://3thinkrs.com/ten-things-to-know-about-linkedins-algorithm-in-2025/

[^16^]: "5 Biggest LinkedIn Algorithm Changes In 2026," Botdog, March 2026. https://botdog.co/blog-posts/linkedin-algorithm-changes-2026

[^17^]: "How the LinkedIn algorithm works in 2025," Hootsuite, Jan 2026. https://blog.hootsuite.com/linkedin-algorithm/

[^18^]: C. Penn, "Almost Timely News: Bringing the LinkedIn Algorithm Guide to Life With AI," May 2025. https://www.christopherspenn.com/2025/05/almost-timely-news/

[^19^]: "How LinkedIn Detects AI Content (And What Happens When It Does)," ViralBrain.ai, Apr 2026. https://www.viralbrain.ai/blog/how-linkedin-detects-ai-content-and-what-happens-when-it-does

[^20^]: O. Melnyk, "360Brew and the LinkedIn Algorithm: What We Know, What's Confirmed, and What Remains Unclear?" The Linked Blog, Oct 2025. https://thelinkedblog.com/2025/360brew-linkedin-algorithm-new-update-3619/

[^21^]: 360Brew arXiv abstract page. https://arxiv.org/abs/2501.16450

[^22^]: L. Hertel et al., "An Industrial-Scale Sequential Recommender for LinkedIn Feed Ranking," arXiv:2602.12354, Feb 2026. https://arxiv.org/html/2602.12354v1

[^23^]: F. Borisyuk et al., "LiRank: Industrial Large Scale Ranking Models at LinkedIn," KDD 2024. https://arxiv.org/pdf/2402.06859

[^24^]: "Utilizing data driven methods to identify gender bias in LinkedIn profiles," Information Processing & Management, June 2025. https://www.sciencedirect.com/science/article/abs/pii/S0306457323001607

[^25^]: "Measuring Bias in Job Recommender Systems: Auditing..." IZA Discussion Paper No. 17245. https://repec.iza.org/dp17245.pdf

[^26^]: D. Sine, "AI 'Slop' on LinkedIn and X: Evidence, Drivers, Harms, Detection," Peerlist, March 2026. https://peerlist.io/danielsinewe/articles/ai-slop-on-linkedin-and-x-evidence-drivers-harms-detection-a

[^27^]: "LinkedIn vs Twitter/X for Founders: Which Platform Builds Better Brands?" WestOwls, May 2026. https://www.westowls.com/post/linkedin-vs-twitter-x-for-founders-which-platform-builds-better-brands

[^28^]: "LinkedIn vs Twitter/X: The Ultimate B2B Platform Comparison," HashMeta, Nov 2025. https://hashmeta.com/blog/linkedin-vs-twitter-x-the-ultimate-b2b-platform-comparison-for-strategic-growth/

[^29^]: R. Metz, "LinkedIn's job-matching AI was biased. The company's solution? More AI," MIT Technology Review, June 2021. https://www.technologyreview.com/2021/06/23/1026825/linkedin-ai-bias-ziprecruiter-monster-artificial-intelligence/

[^30^]: "Digital Networking - AI Algorithm Biases," Clemson Open Textbooks, 2024. https://opentextbooks.clemson.edu/sciencetechnologyandsociety/chapter/digital-networking-ai-algorithm-biases/

[^31^]: "LinkedIn updates its Feed algorithm," Social Media Today, March 2026. https://www.socialmediatoday.com/news/linkedin-updates-its-feed-algorithm/814638/

[^32^]: "DeSlop: Content filtering extension," GitHub HxHippy/DeSlop, Oct 2025. https://github.com/HxHippy/DeSlop

[^33^]: "The 2026 LinkedIn Algorithm," SalesHigher, March 2026. https://saleshigher.com/linkedin-algorithm/

[^34^]: "LinkedIn Algorithm 2026: What Works Now," DataSlayer, Feb 2026. https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now

[^35^]: "LinkedIn Algorithm 2026: Engagement Strategy Guide," Digital Applied, Feb 2026. https://www.digitalapplied.com/blog/linkedin-algorithm-2026-engagement-strategy-guide

[^36^]: "LinkedIn Engagement Pods Crackdown 2026," ConnectSafely, Feb 2026. https://connectsafely.ai/articles/linkedin-engagement-pods-crackdown-2026

[^37^]: "LinkedIn 360Brew: What Actually Changed," AuthoredUp, Nov 2025. https://authoredup.com/blog/linkedin-360brew

[^38^]: "LinkedIn engagement pods experiment: Pros and cons," LinkedHelper, Aug 2024. https://www.linkedhelper.com/blog/linkedin-engagement-pods/
