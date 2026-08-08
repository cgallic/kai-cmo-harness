## 8. Third-Party Reverse Engineering: What External Researchers Uncovered

LinkedIn does not publish the weights, thresholds, or feature importance scores that govern its feed-ranking systems. Engineering blog posts, academic papers, and patent filings describe architecture in broad strokes while withholding the parameters that determine which post reaches whom. Into that opacity, a growing ecosystem of independent researchers has inserted data-driven probes. Between 2023 and 2026, at least ten distinct research streams — spanning millions of posts and tens of thousands of creator profiles — produced quantitative maps of algorithmic behavior that LinkedIn itself has never confirmed. This chapter synthesizes the most rigorous of those studies, distinguishes robust observational findings from inferential claims, and examines the critiques that have emerged around detection methodologies and algorithmic suppression.

### 8.1 Large-Scale Observational Studies

Independent research into LinkedIn's distribution patterns operates under a common constraint: no external party has direct access to LinkedIn's internal logs, A/B test infrastructure, or model weights. Every finding is observational — correlations between content characteristics and publicly visible metrics — rather than causal. Within that limitation, three studies stand out for scale and methodological transparency.

#### 8.1.1 Richard van der Blom — 1.8 Million Posts (2025)

Richard van der Blom, in partnership with Just Connecting(TM), published the Algorithm Insights Report 2025, analyzing 1.8 million posts from 58,000 individual profiles and 31,000 company pages over the twelve months ending February 2025 [^168^][^170^]. The study has become the most widely cited independent benchmark for LinkedIn distribution dynamics.

Van der Blom's central finding is stark: organic reach across the platform dropped by nearly 50% during the study period [^169^][^197^]. But the aggregate figure masks an acute distributional shift. "Top Creator" visibility — the share of feed impressions captured by LinkedIn's designated top-performing accounts — climbed from 15% in 2022 to 31% in 2025, while visibility for all other creators collapsed from 57% to 28% [^206^][^208^].

The study also documented a new engagement hierarchy through correlational analysis. Posts that triggered three or more commenters in the first 60 minutes received approximately 5.2x reach amplification [^193^][^206^]. Direct messages sent in response to a post produced an estimated +90% reach boost on the author's next post, while saves generated an +80% creator visibility boost. Likes produced only a +25% reach boost — the weakest measured signal [^168^]. Van der Blom further found that mobile access dominated at 72% (up 10 percentage points from 2024), that PDF carousel documents were the fastest-growing format at +7.5% year-over-year, and that the optimal reading age for maximum engagement was 6–9 years — substantially below the 12+ years commonly assumed [^168^][^170^].

#### 8.1.2 LinkPost / Yannis Haismann — 438,413 Posts

Yannis Haismann, founder of LinkPost, conducted the most detailed NLP-based analysis of LinkedIn content tactics published to date, examining 438,413 posts, 5,291,997 comments, and 7,769,431 metric snapshots from 24,006 distinct creators scraped between 2020 and April 2026 [^167^]. The dataset is skewed 62% French and 15% English — a limitation Haismann discloses explicitly [^167^][^216^].

The study's headline finding on format performance aligns with van der Blom: carousel (PDF document) posts delivered a median reach of 1,410 impressions versus 569–622 for other formats, a 2.3x advantage — the single clearest format-level signal in the data [^167^]. Haismann attributes this to compound engagement mechanics: each slide swipe registers as interaction, dwell time extends across pages, and the format invites saving.

On content tactics, Haismann applied NLP classifiers to the top 1% of posts by engagement score. Hooks appeared in 80% of viral posts — but in 93% of all posts, making hooks near-universal rather than discriminative [^167^]. What distinguished viral content was tactic stacking: viral posts averaged 4–6 detected tactics combined, versus 1–2 for median performers. Quantified proof appeared in 61% of viral posts, open loops in 47%, and polarization in 25% [^167^][^216^]. High-controversy posts (scoring ≥0.7 on a 0–1 NLP divisiveness scale) generated 2.75x more likes and 1.52x more comments than neutral posts, though only 2.8% of posts fell into this band [^167^][^216^]. Contrary to conventional wisdom, posts exceeding 1,500 characters averaged 209 engagement points versus 140 for posts under 300 characters — a 49% gap [^167^].

#### 8.1.3 AuthoredUp — 3 Million Posts

AuthoredUp analyzed over 3 million posts to measure the 360Brew algorithm's impact on content distribution [^173^][^229^]. Its findings provide the most widely cited engagement-hierarchy benchmarks.

The study documented that one save produces approximately 5x the reach of one like, and 2x the reach of one comment [^173^][^178^][^229^]. Posts receiving substantive saves and comments 24–72 hours after publishing performed 4–6x better in "Suggested" feeds than those whose engagement peaked in the first hour [^173^][^178^][^229^]. A case study of the Botdog founder illustrated the mechanism: average engagement in the first 48 hours, then nearly 100,000 views once saves accumulated around hour 72 [^178^][^229^]. This marks a structural shift from the velocity-based ranking paradigm that prevailed through 2023.

AuthoredUp also quantified aggregate impression decline: median impressions fell 47%, from 1,211 in June 2024 to 636 in May 2025 [^223^]. The decline was not uniform — creators producing niche, expert-level content reported better targeted audiences despite fewer total impressions [^218^] — but the direction was consistent across the dataset.

The following table compares parameters and reach findings across all three studies:

| Study (Researcher) | Posts Analyzed | Time Period | Key Reach Finding | Format/Tactic Insight |
|---|---|---|---|---|
| van der Blom [^168^] | 1,800,000 | Feb 2024–Feb 2025 | ~50% organic reach drop; Top Creator share 15%→31% [^169^][^197^][^206^] | Carousels +7.5% YoY; reading age 6–9 optimal [^170^] |
| LinkPost / Haismann [^167^] | 438,413 | 2020–Apr 2026 | Carousel 2.3x median reach vs. text/image | Viral posts stack 4–6 tactics; 1,500+ chars = +49% engagement [^216^] |
| AuthoredUp [^173^] | 3,000,000+ | Through May 2025 | 47% median impression decline (1,211→636) [^223^] | Saves = 5x reach of likes; delayed engagement 24–72h = 4–6x [^229^] |

The convergence across these studies — despite differing methodologies and compositions — strengthens confidence in the underlying patterns. All three found carousel formats outperforming static content. All three documented substantial aggregate reach declines. All three identified saves and substantive comments as dominant distribution signals, with likes relegated to a minor role.

The next table isolates reach and engagement coefficient estimates from independent research, expressed as multipliers relative to baseline:

| Signal or Tactic | Reach/Engagement Impact | Source(s) | Confidence |
|---|---|---|---|
| 1 Save | 5x reach of 1 like | AuthoredUp [^173^][^229^] | Medium — single commercial source |
| 1 Comment (substantive) | 2x reach of 1 like; ~15x raw weight pre-NLP scoring | AuthoredUp [^173^]; van der Blom [^168^] | Medium — conflicting estimates |
| 3+ commenters in first 60 min | ~5.2x reach amplification | van der Blom [^193^][^206^] | Medium — correlational |
| DM sent from post | +90% reach boost on next post | van der Blom [^168^] | Medium — survey-derived |
| Carousel (PDF) format | 2.3x median impressions; 6.60% avg engagement | LinkPost [^167^]; multiple [^219^] | High — 2+ studies confirm |
| High-controversy content | 2.75x likes, 1.52x comments vs. neutral | LinkPost [^167^][^216^] | Medium — 2.8% of posts |
| Posts 1,500+ characters | +49% engagement vs. <300 chars | LinkPost [^167^] | Medium — language-skewed |
| Delayed engagement (24–72h) | 4–6x better "Suggested" feed performance | AuthoredUp [^173^][^178^] | Medium — limited case studies |
| External link in post body | ~–60% reach penalty | Multiple [^180^][^219^] | High — 3+ sources |
| Daily posting (vs. 2–3x/week) | –26% average reach per post | Industry analysis [^220^] | Medium — single source |

These coefficients should be interpreted as directional estimates. No independent researcher has access to LinkedIn's actual feature importance vectors. Where estimates diverge — notably comment weights ranging from 2x to 15x — the difference may reflect different scoring stages: raw comment count may carry high weight in initial retrieval, while NLP quality scoring reduces effective weight for generic comments in ranking.

### 8.2 Technical Reverse Engineering

Beyond observational content studies, several efforts have reconstructed LinkedIn's algorithmic architecture from patents, engineering publications, and behavioral experiments.

#### 8.2.1 Trust Insights / Christopher Penn — The Unofficial Guide

Christopher Penn and the Trust Insights team publish "The Unofficial LinkedIn Algorithm Guide for Marketers," a quarterly synthesis of LinkedIn engineering publications into actionable intelligence [^176^][^224^]. The guide processes roughly 120,000 words of raw source material (31 primary publications, 20 from LinkedIn engineering papers) through LLMs (Gemini 2.5 Pro, Claude) to produce approximately 400,000 words of analysis [^176^][^217^]. An independent review confirmed that "technical claims are traced back to official LinkedIn publications," though it cautioned the guide "remains an independent interpretation of partial public evidence" [^217^].

Penn's central claim: "there is no such thing as the LinkedIn algorithm" as a singular system. LinkedIn operates as an ensemble of 12–15 distinct technologies, each making independent decisions about annotation, candidate generation, ranking, re-ranking, and trust-and-safety filtering [^176^][^224^]. His five-stage reconstruction — Annotation (feature extraction), L0 Candidate Generation, L1 Light Ranking, L2 Rich Ranking / SPR, and Re-ranking / Finalization — aligns broadly with LinkedIn's own disclosures of multiple retrieval and scoring layers [^176^][^222^].

#### 8.2.2 ViralBrain.ai — Content Classifier Reconstruction

ViralBrain.ai reconstructed LinkedIn's content classifier from patent filings and behavioral experiments. Its researchers found that 360Brew performs what they describe as a semantic "audition" between a creator's profile (headline, About, Experience) and their posts [^211^]. A "Graphic Designer" posting about "Crypto Trading" triggers an expertise-mismatch penalty; a "RevOps Director" writing about "Salesforce Integration" receives a consistency reward [^211^]. This alignment signal operates independently of engagement — a high-quality post on a mismatched topic may be suppressed even with strong predicted engagement.

#### 8.2.3 Daniel Hall / SpotAPod — Pod Detection and Vulnerabilities

Daniel Hall's SpotAPod project represents the most consequential security-focused reverse engineering of LinkedIn's engagement ecosystem. Hall developed a proprietary algorithm measuring reciprocal comment-section engagement and used it to expose more than 200 LinkedIn creators in engagement pods [^181^].

His most significant finding was a critical vulnerability in Lempod — the largest engagement-pod Chrome extension — that allowed unauthorized access to the LinkedIn credentials of all pod members [^181^]. With 10,000+ Lempod users, the exposure scope was substantial. Hall reported it to LinkedIn, which patched the issue by April 2024 [^181^]. He described it thus: "Imagine giving your keys to a valet... A stranger tells the valet his car is in the same lot yours is in, so the valet gives him the keys to all the cars in that lot" [^181^].

Hall also identified chatbots conversing on LinkedIn live streams and, in October 2023, began publishing evidence against creators who "sell engagement systems to others who hope to achieve the same success on LinkedIn without knowing their idols are getting their fake engagement numbers through pod participation" [^181^]. By February 2026, Lempod was banned from the Chrome Web Store, and LinkedIn's pod detection accuracy was reported at 97% [^191^][^195^]. The pod ecosystem that operated with minimal detection from 2018 through 2024 has been effectively neutralized.

### 8.3 Critiques and Controversies

External research on LinkedIn's algorithm has itself become subject to methodological and ethical debate. Three controversies expose the limits of third-party analysis and the unintended consequences of enforcement.

#### 8.3.1 Shelly Palmer — The Pattern-Detection Treadmill

Shelly Palmer — Professor of Advanced Media at Syracuse University — published a pointed critique in May 2026 of LinkedIn's campaign against "AI slop" [^228^]. LinkedIn had identified "contrastive construction" ("it's not X, it's Y") as a signature of AI-generated content. Palmer countered that LLMs "picked up that pattern from human writers who used it for decades before ChatGPT existed" and that "now that LinkedIn has announced the signal, the slop generators will stop using it" [^228^]. The announcement degrades the signal's usefulness, creating what Palmer calls a "treadmill" — platforms announce detection targets and generators immediately adapt.

Palmer's deeper concern is epistemic ambiguity: "Where do we draw the line between AI slop, AI assisted slop, and plain bad writing?" A professional who drafts in their own words and uses AI to tighten prose produces more readable content than they could alone, yet "the detection model has no way to tell that user from a bot that scraped a competitor's post and ran it through a paraphraser. Both look identical from the outside" [^228^]. The structural fix is "rewarding original thinking and surfacing expertise" — a quality-based rather than authorship-based approach [^228^].

#### 8.3.2 Originality.ai — The 54% AI Content Finding

Originality.ai, an AI detection startup, conducted two major studies measuring AI content prevalence. The first analyzed 8,795 long-form posts (100+ words) from January 2018 through October 2024; the second examined 3,368 posts from 99 influential profiles during January–November 2025 [^166^][^174^][^175^].

Both studies converged on ~54% AI-assistance prevalence [^166^][^175^]. AI use was "negligible" through end of 2022, spiked 189% from January to February 2023 (the ChatGPT launch), then plateaued at ~50% [^174^][^175^][^179^]. Average post length tracked adoption: from below 500 words to ~1,500 words [^174^]. The 2025 study found AI posts underperformed human posts by 45% on average, though penalties varied by industry: AI-generated leadership content outperformed human by 75%, while human-written healthcare and government posts outperformed AI by 44% and 40% [^166^].

The critical caveat is Originality.ai's commercial interest. The 54% figure combines AI-generated posts with AI-edited human writing, and the company acknowledges that "the extent of pure replacement vs. augmentation remains a mystery" [^174^]. The detector treats "Human Written and Heavily AI Edited" as AI-generated — a classification that may overstate pure AI authorship [^179^]. The directional finding of massive post-ChatGPT adoption is nonetheless consistent across both studies.

#### 8.3.3 The "Better Writer" Problem

Palmer's critique and Originality.ai's findings converge on a problem no detection system has resolved: AI-assisted professionals with genuine expertise but weak prose are indistinguishable from bots to pattern-based classifiers [^228^]. "A significant percentage of LinkedIn professionals have useful judgment and weak prose," Palmer noted. "AI assistance helps them communicate better than they could on their own. The fix removes the thinkers and the bots" [^228^].

This creates structural tension in LinkedIn's enforcement strategy. The platform suppresses flagged content (limiting it to first-degree connections) without notification or recourse [^175^][^207^]. A professional who uses AI to polish an original insight may see reach constrained without learning why, while a scraping bot evades detection by varying patterns. The arms-race dynamics suggest pattern-based suppression will remain behind generation indefinitely; the sustainable solution is a ranking system valuing quality signals — dwell time, saves, substantive comments — regardless of production method.

LinkedIn's trajectory partially aligns with this reasoning. The production ranking system weights engagement quality and semantic relevance over authorship detection [^207^][^211^]. Whether that weighting is sufficient to avoid collateral damage against legitimate AI-assisted creators — or whether pattern-based suppression continues eroding their reach — remains an open question independent researchers can monitor but not resolve.
