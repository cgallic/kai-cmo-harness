# LinkedIn AI Systems Deep Dive

> **Use when:** Planning LinkedIn content, reverse-engineering LinkedIn reach changes, writing about LinkedIn AI/patents, or designing posts/articles that need to survive AI-content suppression and semantic feed ranking.

Source packet: `knowledge/research/linkedin-ai-systems/`.

---

## The Core Correction

Most public commentary says LinkedIn's feed is ranked by **360Brew**, LinkedIn's 150B-parameter foundation model. The research packet says that is wrong.

High-confidence finding: LinkedIn evaluated the LLM ranker and rejected it for feed ranking because numeric features lost precision when verbalized, member histories became too token-heavy, and relationship/network signals degraded when converted to text. The production feed architecture is better understood as a cascaded recommendation system:

1. **L0 candidate generation** — fine-tuned LLaMA-3 3B dual encoder for retrieval.
2. **L1 light ranking** — LightGBM/XGBoost-style calibration.
3. **L2 rich ranking** — Feed-SR, a compact decoder-only transformer sequential recommender.
4. **Re-ranking** — LiGR setwise attention, LiFT fairness adjustments, policy/business filtering.

Implication: write for **retrieval + semantic relevance + dwell**, not for a mythical monolithic 150B ranker.

---

## Operator Model for LinkedIn Content

### What the feed appears to reward

- **Semantic relevance over network proximity.** The system increasingly routes content by topic/interest fit, not just who follows whom.
- **Saves and delayed engagement.** Research cites saves as a stronger reach signal than likes and delayed 24-72 hour engagement as more valuable than shallow first-hour spikes.
- **Long dwell.** Feed-SR and content-quality systems optimize for time spent and meaningful interaction.
- **Original expertise signals.** Posts that add a specific operator insight, source trail, metric, workflow, or contrarian correction beat generic commentary.
- **Entity-rich specificity.** Named systems, papers, patents, organizations, model names, dates, and mechanisms help retrieval and reader trust.

### What likely suppresses reach

- Generic AI-written phrasing and uniform structure.
- Engagement-pod velocity patterns.
- Attention-bait videos or posts with high click/open and low dwell.
- Overly broad thought-leadership claims without concrete proof.
- External links in the body when the post needs feed reach.
- Content that looks like a template: identical paragraph lengths, predictable contrastive phrasing, boilerplate endings.

---

## LinkedIn AI-Content Detection Signals

The research describes an "AI solving AI" framework: editorial annotation plus machine classifiers. Distribution suppression is more common than removal.

Use this as a writing QA model:

| Signal layer | Bad pattern | Kai correction |
|---|---|---|
| Pattern | "It's not X, it's Y" repeated; LinkedIn broetry | Vary syntax; use real mechanism-first sentences. |
| Vocabulary | Delve, tapestry, leverage, unlock, transform, game-changer | Use concrete nouns and verbs from the actual system. |
| Structure | Same-length paragraphs, generic intro/body/conclusion | Mix paragraph lengths; include source-backed specifics early. |
| Engagement | High impressions but weak dwell/saves | Make the post bookmarkable: checklists, diagrams, exact steps. |
| Account | Sudden style shift or robotic cadence | Preserve Connor/Kai voice and publish fewer, stronger artifacts. |

---

## Strategic Plays for Kai

### 1. Retrieval-first thought leadership

Use LinkedIn's retrieval-ranking split against itself: make posts easy to retrieve by entities and hard to dismiss as generic.

Minimum ingredients:

- One named mechanism: e.g. Feed-SR, LiGR, LLaMA-3 dual encoder, Economic Graph, AI solving AI.
- One falsifiable claim: e.g. "360Brew is not the production feed ranker."
- One operator implication: what marketers/founders should do differently.
- One artifact worth saving: checklist, diagram, teardown, table, decision rule.

### 2. Anti-slop positioning

LinkedIn is suppressing generic AI content, not AI assistance itself. Kai content should explicitly show human judgment:

- mention what the source trail changed your mind about;
- include the decision rule you would use in practice;
- name the false public narrative;
- show the boring operational consequence.

### 3. Build posts from research packets

The strongest LinkedIn assets should come from research packets like this one, not from generic prompts.

Recommended pipeline:

1. Load `research/linkedin_ai_cross_verification.md` for confidence-ranked facts.
2. Pick one surprising correction, not the whole report.
3. Convert it into a 700-1,000 word LinkedIn article or 250-500 word post.
4. Run Four U's and banned-word gates.
5. Add external links only in the first comment unless the goal is citation more than reach.

---

## Claim Hygiene

When citing this packet, separate confidence tiers:

- **High confidence:** Feed-SR production role, LLaMA-3 3B retrieval, 360Brew rejection for feed ranking, LinkedIn's human+ML content detection, distribution suppression, major infrastructure stats like Kafka/Pinot scale.
- **Medium confidence:** third-party reach-drop estimates, exact save/like multipliers, independent engagement studies, pod-detection recovery timelines.
- **Use carefully:** black-box claims about secret ranking weights, exact suppression thresholds, claims without primary-source backing.

---

## Related Files

- `knowledge/research/linkedin-ai-systems/linkedin_ai_report.agent.final.md`
- `knowledge/research/linkedin-ai-systems/research/linkedin_ai_cross_verification.md`
- `knowledge/research/linkedin-ai-systems/research/linkedin_ai_insight.md`
- `knowledge/channels/linkedin-articles.md`
- `knowledge/checklists/linkedin-ai-content-detection-and-feed-checklist.md`
