# SEO Expert Patent Research Checklist

A comprehensive guide to researching Google patents for SEO insights, extracted from SEO Expert's consulting methodology. Includes key engineers to follow, patent analysis workflow, and understanding core ranking concepts.

---

## Key Google Engineers to Follow

### Tier 1: Essential Engineers (Start Here)

#### Rajan Patel
- **Current Role**: Vice President of Search, Google
- **Focus Areas**: AI systems, link quality scoring, site classification
- **Key Patent**: "Classifying Sites as Low Quality Sites"
- **Why Important**: Currently leading AI Mode development; his older patents reveal foundational ranking concepts
- **LinkedIn Activity**: Very active, shares insights on current search developments
- **Key Concepts Introduced**:
  - Link quality score thresholds
  - Diversity filter for de-duplicating links
  - Site quality classification (vital/good/bad groupings)

#### Jeffrey Dean
- **Focus Areas**: User behavior ranking, click data analysis
- **Key Patent**: "Ranking Documents Based on User Behavior and Feature Data"
- **Why Important**: Father of click-based ranking algorithms
- **Key Concepts**:
  - Selection signals (click, touch, mouse-over)
  - User behavioral weighting
  - Resource quality scoring

#### Stephen Baker
- **Focus Areas**: Featured snippets, passage ranking, web answers
- **Key Data**: C4 (Colossal Clean Crawled Corpus) - Clean Wikipedia
- **Why Important**: His work on C4 dataset forms basis for algorithmic authorship rules
- **Key Contributions**:
  - Web answers/featured snippet extraction
  - Passage ranking methodology
  - Information extraction rule sets
- **LinkedIn**: Very active, shares current developments

### Tier 2: Document Ranking Specialists

#### Naumit Panda (Navneet Panda)
- **Focus Areas**: Quality signals, content evaluation
- **Key Contribution**: Panda algorithm/quality scoring
- **Patent Focus**: Document quality assessment
- **Why Important**: His patents explain how Google evaluates content quality

#### Paul Hall
- **Focus Areas**: Document ranking foundations
- **Era**: 2000s-2010s foundational work
- **Patent Types**: Core ranking algorithms

#### Matt Cutts
- **Focus Areas**: Spam detection, web quality
- **Note**: Former head of webspam team; historical importance
- **Patent Focus**: Quality and spam signals

### Tier 3: Passage & Query Specialists

#### Tristan Upstill
- **Focus Areas**: Navigational queries, homepage identification
- **Key Patent**: "Locally Significant Search Queries"
- **Current Role**: Working on Android (last 5-6 years)
- **Why Important**: Understanding how Google identifies "root" pages and navigational intent
- **Key Concepts**:
  - Query path analysis
  - Homepage/root page identification
  - Navigational query classification

#### Alexander Gruszewski
- **Current Role**: 20+ year Google veteran
- **Position**: Founder and Lead of RankLab (internal Google project)
- **LinkedIn**: Uses Ukrainian spelling "Oleksandr"
- **Why Important**:
  - RankLab is core of Google's ranking development
  - Designs ranking signals, algorithms, ML models
  - "Hidden" engineer - less publicly known but highly influential
- **Focus Areas**:
  - Statistical stemming for query processing
  - Ranking signal design
  - Machine learning models for search

### Patent Focus by Era

| Era | Focus | Key Engineers |
|-----|-------|---------------|
| **2000s** | Foundational ranking | Paul Hall, Matt Cutts |
| **2010s** | Quality signals, Panda/Penguin | Naumit Panda, Jeffrey Dean |
| **2020s** | Passage ranking, AI | Stephen Baker, Rajan Patel |

---

## Patent Analysis Workflow

### Step 1: Find Relevant Patents
- [ ] **Start with engineer names** - Search Google Patents by inventor
  - *Query format*: "[Engineer Name]" inventor:google
  - *Sort by*: Most recent for current relevance

- [ ] **Use topical searches** - Search for specific concepts
  - *Examples*: "ranking documents user behavior", "link quality score", "passage generation"

- [ ] **Check related patents** - Each patent lists related patents
  - *Why*: Engineers often work on related systems together

### Step 2: Use SEO Patent Reader GPT
- [ ] **Upload PDF to GPT** - Use SEO Expert's SEO Patent Reader GPT
  - *Location*: Available in ChatGPT GPT store

- [ ] **Get structured analysis**:
  - Inputs (what goes into the system)
  - Outputs (what the system produces)
  - Variables (what factors affect the outcome)
  - Visual diagrams (flowcharts from patent figures)

- [ ] **Ask follow-up questions** - GPT can reason further on specific aspects
  - *Warning*: Last sections are "chain of reasoning" - AI interpretation, not patent claims

### Step 3: Extract Actionable Insights
- [ ] **Identify key terms** - Patent-specific terminology
  - *Examples*: "diversity filter", "threshold", "scoring", "cluster"

- [ ] **Map to SEO practices** - How does this affect optimization?
  - *Caution*: Patents describe capability, not necessarily current implementation

- [ ] **Document findings** - Add to personal knowledge base

---

## Core Patent Concepts

### Diversity Filter
- **Definition**: De-duplicating near-identical endorsements (links)
- **Source**: Rajan Patel patents
- **Implication**:
  - 50 identical links from link building agency = 1 link value
  - Only "best representative" link is kept
  - Link variety matters more than volume

### Link Quality Scoring
- **Categories**: Vital, Good, Bad
- **Threshold System**: Links must exceed quality threshold to count
- **Source**: Jeffrey Dean, Rajan Patel patents
- **Components**:
  - Boilerplate link removal (header/footer/sidebar)
  - Diversity filtering
  - Quality scoring per link
  - Weighted ratio calculation

### Document vs Passage vs Passage Generation
- [ ] **Document Ranking** - Whole page evaluation
  - *Engineers*: Paul Hall, Matt Cutts, Naumit Panda, Jeffrey Dean
  - *Focus*: Overall page quality, authority, relevance

- [ ] **Passage Ranking** - Section-level evaluation
  - *Engineers*: Stephen Baker, Tristan Upstill
  - *Focus*: Specific passage relevance for featured snippets

- [ ] **Passage Generation** - Creating answers from passages
  - *Current focus*: AI Overviews, answer extraction
  - *Relevance*: Algorithmic authorship rules apply here

### Query Path/Query Logs
- **Concept**: Understanding query sequences users follow
- **Source**: Alexander Gruszewski patents
- **Application**:
  - Autocomplete manipulation
  - Query-to-document mapping
  - User journey optimization

### Threshold Systems
- **Universal pattern**: All Google systems use thresholds
- **Examples**:
  - Link quality thresholds
  - Content quality thresholds
  - Trust thresholds
- **Implication**: Must exceed thresholds; incremental improvements may not help until threshold crossed

---

## Patent Research Resources

### Primary Sources
| Resource | URL | Purpose |
|----------|-----|---------|
| **Google Patents** | patents.google.com | Primary patent database |
| **Google Research Publications** | research.google/pubs | Academic papers, not patents |
| **Google AI Research** | ai.google/research | AI/ML specific research |
| **Google DeepMind** | deepmind.com/research | Gemini-related research |

### Secondary Sources
| Resource | Purpose |
|----------|---------|
| **LinkedIn** | Follow engineers for current insights |
| **SEO Patent Reader GPT** | Simplify patent analysis |
| **SEO Expert's Passage Ranking SOP** | List of 10-15 key patents |

---

## Patent Analysis Template

### Basic Information
```
Patent Number: US________
Title:
Inventor(s):
Filing Date:
Priority Date:
Assignee: Google LLC
```

### Technical Summary
```
INPUTS:
- What data/signals go into this system?

OUTPUTS:
- What does the system produce/decide?

VARIABLES:
- What factors can be adjusted?
- What thresholds exist?

DIAGRAM INTERPRETATION:
- Key figure numbers and what they show
```

### SEO Implications
```
ACTIONABLE INSIGHTS:
1.
2.
3.

WHAT THIS MEANS FOR:
- Content:
- Links:
- Technical:

RELATED PATENTS TO READ:
-
-
```

---

## Common Mistakes in Patent Research

| Mistake | Impact | Fix |
|---------|--------|-----|
| Asking AI about patents directly | Hallucination, fake patent numbers | Upload PDF to SEO Patent Reader |
| Treating patents as current implementation | Over-optimization for unused systems | Cross-reference with observed behavior |
| Ignoring threshold concepts | Missing the "why" of rankings | Understand all systems use thresholds |
| Only reading recent patents | Missing foundational concepts | Study 2000s-2010s for basics |
| Not tracking engineer careers | Missing connections between systems | Follow engineers across patents |

---

## Study Path Recommendations

### Beginner (First Month)
1. Read Rajan Patel's "Classifying Sites as Low Quality Sites"
2. Read Jeffrey Dean's "Ranking Documents Based on User Behavior"
3. Use SEO Patent Reader GPT for both
4. Focus on understanding threshold and scoring concepts

### Intermediate (Months 2-3)
1. Study Stephen Baker's featured snippet patents
2. Explore passage ranking patents
3. Connect patents to algorithmic authorship rules
4. Start following engineers on LinkedIn

### Advanced (Ongoing)
1. Join patent study cohorts (SEO Expert's coaching program has one)
2. Study Alexander Gruszewski's RankLab work
3. Cross-reference patents with Google API leaks
4. Track new patents from key engineers

---

## Google Business Profile Patents (To Research)

- [ ] **Identify GBP-specific engineers** - Research needed
- [ ] **Map/Query side patents** - Different from organic search
- [ ] **Local ranking factors** - May have separate patent lineage

*Note: SEO Expert mentioned this as a to-do item for further research*

---

## Key Quotes from SEO Expert on Patents

> "I'm going from the engineer. I'm checking what they published."

> "If you go to the Stephen Baker's LinkedIn account, you are going to see that actually he started to, again changing here. He is very active on LinkedIn."

> "Alexander Gruszewski - this is a kind of hidden Google engineer. His name is not there. I must tell the reasons maybe later."

> "Always there is a threshold, either for link quality, either for something else. Always you are going to see this specific concept."

---

*Source: SEO Expert Tugberk Gubur SEO Consulting Sessions, 2025*
