# Knowledge Cloning Workflow
## A Repeatable System for Extracting, Distilling, and Operationalizing Any Expert's Knowledge

**Version**: 1.0
**Created**: 2026-03-15
**Origin**: Distilled from the process of extracting knowledge from the Preston Rhodes X Space transcript
**Purpose**: Apply to ANY person — influencer, operator, thought leader, investor, founder — to produce a usable playbook of their knowledge.

---

## Table of Contents

1. [Overview & Philosophy](#1-overview--philosophy)
2. [Phase 1: Source Discovery](#2-phase-1-source-discovery)
3. [Phase 2: Knowledge Extraction](#3-phase-2-knowledge-extraction)
4. [Phase 3: Distillation](#4-phase-3-distillation)
5. [Phase 4: Synthesis](#5-phase-4-synthesis)
6. [Phase 5: Operationalization](#6-phase-5-operationalization)
7. [Phase 6: Quality Gates](#7-phase-6-quality-gates)
8. [Master Extraction Prompt Template](#8-master-extraction-prompt-template)
9. [Completeness Checklist](#9-completeness-checklist)
10. [Example: Sam Ovens Full Extraction](#10-example-sam-ovens-full-extraction)
11. [Source-Type Handling Guide](#11-source-type-handling-guide)
12. [Recommended Tools](#12-recommended-tools)
13. [Time & Depth Tiers](#13-time--depth-tiers)

---

## 1. Overview & Philosophy

### What "Knowledge Cloning" Actually Means

This is not summarization. Summaries compress. Cloning extracts the underlying operating system — the mental models, decision heuristics, anti-patterns, and tacit knowledge that make an expert effective.

The goal: after completing this workflow, someone who has never encountered the expert should be able to produce outputs indistinguishable (in quality and reasoning style) from what the expert would produce.

### The Three Layers of Expert Knowledge

Every expert has three layers, and most knowledge extraction only captures the first:

| Layer | What It Looks Like | How Hard to Extract |
|-------|-------------------|---------------------|
| **Explicit** | Frameworks, named tactics, published systems | Easy — they say it out loud |
| **Tacit** | Heuristics, pattern recognition, what they skip over | Hard — need multiple sources |
| **Implicit** | Underlying beliefs, what they refuse to do, worldview | Very hard — inferred, not stated |

A proper clone captures all three.

### Principles for Accurate Extraction

1. **Source before inference** — only claim something is the expert's view if a source backs it. Tag inferences explicitly.
2. **Contradictions are data** — when an expert contradicts themselves across time, note it. That evolution is insight.
3. **Context is non-negotiable** — a tactic that works in one context fails in another. Always capture the conditions.
4. **Anti-patterns first** — what an expert consistently avoids tells you more than what they recommend.
5. **The student is a signal** — how their students describe the teaching reveals the tacit layer.

---

## 2. Phase 1: Source Discovery

**Goal**: Build a complete source map before extracting anything.
**Time**: 1-4 hours depending on how prolific the person is.

### 2.1 The Discovery Stack (run in this order)

**Tier 1 — Their own published work (highest fidelity)**

- [ ] YouTube channel — full video list, note most-viewed and oldest videos
- [ ] Podcast — their own show + their guest appearances on others
- [ ] X (Twitter) — full profile, pinned tweets, Twitter Spaces they hosted
- [ ] LinkedIn — posts, articles, comment threads
- [ ] Newsletter/Substack/blog — especially early posts (rawest thinking)
- [ ] Books, courses, cohorts — the paid/premium material often has the deepest frameworks
- [ ] Webinars, conference talks — search `"[Name]" site:youtube.com` and `"[Name]" filetype:pdf`

**Tier 2 — What others have documented about them**

- [ ] Wikipedia (if notable enough) — useful for verified timeline
- [ ] Crunchbase/PitchBook — business history, funding events, exits
- [ ] Press coverage — Forbes, TechCrunch, niche trades (use Google: `"[Name]" site:forbes.com OR site:techcrunch.com`)
- [ ] Reddit — `site:reddit.com "[Name]"` — especially r/Entrepreneur, r/bigseo, r/marketing etc.
- [ ] Podcasts where they were interviewed — use ListenNotes, Spotify, Apple Podcasts search
- [ ] Twitter threads summarizing their work (often high-signal, community-created)

**Tier 3 — Their network and students (proxy signals)**

- [ ] Their students' social posts — search `"learned from [Name]"`, `"[Name] student"`, `"[Name] changed my"` on X and LinkedIn
- [ ] Alumni/community forums — if they have a paid community, find any public discussions
- [ ] People they consistently cite or credit — these are their intellectual parents
- [ ] People who consistently cite them — these show the downstream influence and often restate the core teaching

**Tier 4 — Context signals**

- [ ] Their company's product/pricing page — what they sell reveals what they believe works
- [ ] Their hiring posts — what roles they build tells you what they value
- [ ] Their public Notion, GitHubs, or resource libraries
- [ ] Testimonials on their sales pages — these are distilled student outcomes

### 2.2 Source Map Template

Create a `source-map.md` file before extracting. Format:

```markdown
# Source Map: [Expert Name]
Last updated: YYYY-MM-DD

## Primary Sources (their own words)
| Type | URL/Reference | Date | Length | Priority | Status |
|------|--------------|------|--------|----------|--------|
| YouTube | [URL] | 2024-03 | 45 min | HIGH | Extracted |
| Podcast | [URL] | 2023-11 | 1h 20m | HIGH | Queued |

## Secondary Sources (about them)
| Type | URL/Reference | Notes | Status |
|------|--------------|-------|--------|

## Student/Alumni Signals
| Source | Key Quote/Insight | Verified? |
|--------|------------------|-----------|

## Open Questions (things to look for)
- [ ] What changed their mind on X?
- [ ] What do they never talk about?
```

### 2.3 Search Queries to Run

Replace `[NAME]` with the person's full name and common handle:

```
# YouTube
"[NAME]" site:youtube.com
"[NAME]" how to
"[NAME]" framework
"[NAME]" strategy

# Podcasts
"[NAME]" podcast interview transcript
"[NAME]" site:listennotes.com

# Press
"[NAME]" site:forbes.com OR site:inc.com OR site:entrepreneur.com

# Reddit
site:reddit.com "[NAME]"
"[NAME]" reddit

# Twitter/X
"[NAME]" -from:[HANDLE] (things said about them)
from:[HANDLE] (min_retweets:50) (their most spread content)

# General
"[NAME]" framework
"[NAME]" system
"[NAME]" method
"[NAME]" taught me
"[NAME]" playbook
```

---

## 3. Phase 2: Knowledge Extraction

**Goal**: From each source, pull the actual substance — frameworks, edges, tactics, principles, anti-patterns.
**Time**: 30 min to 3 hours per source depending on length and density.

### 3.1 The Five Extraction Categories

For each source, look for instances of all five:

**1. Frameworks** — Named or unnamed systems with discrete steps or components
- Signal phrases: "The way I think about it is...", "There are three things...", "I call this..."
- What to capture: Name (coin one if unnamed), purpose, components, sequence, conditions

**2. Edges** — Non-obvious insights that contradict common wisdom or reveal hidden advantages
- Signal phrases: "What most people don't realize...", "The thing nobody talks about...", "Counterintuitively..."
- What to capture: The conventional view, the edge insight, why it's actually true, application

**3. Tactics** — Specific, immediately actionable techniques
- Signal phrases: "What I do is...", "Here's exactly how...", "The move is..."
- What to capture: The action, context it applies in, expected result, tools needed

**4. Principles** — Underlying beliefs that generate tactics (more durable than tactics)
- Signal phrases: "I believe...", "The fundamental truth is...", "At the end of the day..."
- What to capture: The principle stated plainly, where it came from, what behavior it drives

**5. Anti-Patterns** — What they explicitly avoid and why
- Signal phrases: "Never...", "The mistake everyone makes...", "I stopped doing this because...", "Don't..."
- What to capture: The pattern, why it fails, what to do instead

### 3.2 Extraction Prompt (per source)

Use this prompt for any text source (transcript, article, book excerpt):

```
You are extracting knowledge from an expert's content.

SOURCE: [TYPE — transcript/article/book/thread]
EXPERT: [NAME]
CONTENT:
---
[PASTE CONTENT HERE]
---

Extract ONLY what is actually present in the content. Do not infer or hallucinate.

For each item found, use this exact format:

## FRAMEWORK: [Name or coin a name]
**Source**: [timestamp or section]
**Purpose**: One sentence — what problem does this framework solve?
**Components**: List each element
**Steps**: Only if sequential. If not sequential, skip.
**Conditions**: When should you use this? When should you NOT?
**Quote**: The closest direct quote from the source
---

## EDGE: [Short memorable title]
**Source**: [timestamp or section]
**Conventional View**: What most people believe
**The Edge**: What the expert actually believes/does differently
**Why It's True**: Their reasoning (from the source)
**Application**: How to use this practically
---

## TACTIC: [Verb phrase — e.g., "Front-load social proof in cold outreach"]
**Source**: [timestamp or section]
**What**: The specific action
**Why**: The mechanism that makes it work
**How**: Step-by-step if given
**Tools**: Any tools mentioned
**Expected Result**: What outcome they claim
---

## PRINCIPLE: [Stated as a belief]
**Source**: [timestamp or section]
**Stated As**: Direct quote if possible
**Behavior It Drives**: What decisions or actions this principle generates
---

## ANTI-PATTERN: [What NOT to do]
**Source**: [timestamp or section]
**The Trap**: What most people do
**Why It Fails**: Their explanation
**The Fix**: What to do instead
---

After extracting all items, add:

## EVOLUTION SIGNALS
Any sign that this expert's thinking has changed over time — note what changed and approximately when.

## GAPS NOTICED
Topics this expert seems to avoid or underweight given their domain.

## TACIT SIGNALS
Things they seemed to assume the audience already knows — implicit knowledge they didn't explain.
```

### 3.3 Video/Audio Extraction Protocol

For YouTube videos and podcasts:

1. **Get the transcript first** — use `yt-dlp --write-auto-sub --sub-lang en` or paste YouTube URL into `tactiq.io`, `otter.ai`, or `rev.com`
2. **Timestamp the transcript** — keep timestamps; they let you verify quotes later
3. **Run extraction prompt** on full transcript
4. **Flag the best 3-5 clips** — the moments with the densest insight (useful for later reference)

For X Spaces:
- Download audio via `twspace_dl` or `xspaces-dl` CLI tool
- Transcribe via Whisper (`whisper audio.mp3 --model large`)
- Then run extraction prompt

### 3.4 Book/Course Extraction Protocol

Books and courses require chapter-level passes, not one-shot extraction:

1. Read/skim chapter — identify the central claim of each chapter
2. Extract all frameworks, tactics, principles at chapter level
3. Run a cross-chapter synthesis pass — look for the through-line argument
4. Identify the 3-5 "keystone ideas" that everything else depends on

For courses specifically, look at: module titles, worksheet templates, the exercises (these reveal what the expert thinks needs to be practiced most).

---

## 4. Phase 3: Distillation

**Goal**: Convert raw extracted notes into clean, structured reference documents.
**Time**: 1-3 hours.

### 4.1 Framework Documentation Format

Each framework gets its own section (or file if large):

```markdown
# [Framework Name]
**Source**: [Expert Name], [Source URL/Reference], [Date]
**Category**: [Mental Model / Process / Diagnostic / Creative / Decision]

## Purpose
One sentence: what problem does this framework solve, for whom, in what context?

## When to Use
- Situation A
- Situation B
NOT for: [explicit exclusions]

## Components
[If non-sequential — a set of elements:]
- **Element 1**: Description
- **Element 2**: Description

## Process
[If sequential — numbered steps:]
1. Step one — what to do, what to produce
2. Step two
3. Step three

## Example
Walk through one concrete application. Use a real example from the expert's source if possible.

## Common Mistakes
What people get wrong when applying this framework.

## Source Quotes
> "Direct quote that best captures the core idea." — [Name], [Source]

## Related
- Links to related frameworks in this knowledge base
- Frameworks that complement this one
- Frameworks that conflict with this one (and when to use each)
```

### 4.2 Tactical Playbook Format

```markdown
# Playbook: [Tactic Name — Verb Phrase]
**Source**: [Expert Name], [Source], [Date]
**Category**: [Acquisition / Retention / Conversion / Operations / Product]
**Time to Implement**: [hours/days/weeks]
**Difficulty**: [Low / Medium / High]

## The Move
Plain English: what are you actually doing?

## Why It Works
The mechanism. Not "it works because it works" — the causal chain.

## Step-by-Step
1.
2.
3.

## Tools
- Tool name — what it's used for in this tactic

## Expected Results
- What metric moves
- Typical magnitude (if the expert gave numbers)
- Timeframe

## Conditions for Success
What needs to be true for this to work?

## Warning Signs
How do you know if it's not working? When should you stop?

## Source
[Link/reference + relevant timestamp or page]
```

### 4.3 Edge Catalog Format

```markdown
# Edge: [Memorable Short Title]
**Source**: [Expert Name], [Source], [Date]
**Domain**: [SEO / Paid Ads / Outbound / Product / Hiring / etc.]

## The Conventional View
What 80% of practitioners believe and do.

## The Edge
What this expert believes that most don't.

## Evidence / Reasoning
Why is this actually true? (From the source — don't add your own reasoning here.)

## Implication
If this edge is real, what should you do differently?

## Confidence Level
- HIGH: Expert stated directly + provided evidence
- MEDIUM: Consistent with their other views, implied strongly
- LOW: Inferred from behavior/outcomes, not stated

## Counter-Evidence
Any indication this might not hold universally?
```

### 4.4 Principle Collection Format

```markdown
# Principles: [Expert Name]

## Core Beliefs (ordered by centrality to their worldview)

### Principle 1: [State as a belief]
**In Their Words**: Best direct quote
**Implication**: What this belief makes them do that others don't
**Origin**: Where/how they developed this belief (if mentioned)

### Principle 2:
...
```

### 4.5 People/Resource Graph

Track the intellectual ecosystem:

```markdown
# Influence Graph: [Expert Name]

## Who Influenced Them
| Person/Resource | What They Took From It | How Often Cited |
|----------------|----------------------|-----------------|

## Who They've Influenced
| Person | Relationship | How Known |
|--------|-------------|-----------|

## Intellectual Siblings
People with similar worldviews who arrived independently — cross-reference useful.

## Contrarians
People who directly disagree — their disagreements reveal assumptions.
```

---

## 5. Phase 4: Synthesis

**Goal**: Find the actual signal — what's unique, what connects, what's missing.
**Time**: 1-2 hours.

### 5.1 The Novelty Pass

After extraction, run this analysis against your existing knowledge base:

```
Compare the extracted frameworks, tactics, and edges against our existing knowledge base.

For each extracted item, classify as:
- NOVEL: Not represented in our KB at all
- ADDITIVE: Expands on something we have (note what it adds)
- REDUNDANT: We already have this (note the existing file)
- CONTRADICTORY: Conflicts with something we have (note the conflict)

For NOVEL and ADDITIVE items, flag for priority addition to KB.
For CONTRADICTORY items, note BOTH perspectives and the conditions under which each applies.
```

### 5.2 The Connection Map

After extracting multiple experts in the same domain, look for:

**Convergent Frameworks** — Multiple experts independently landed on the same structure. This is the closest thing to verified truth in marketing.

**Complementary Frameworks** — Expert A covers acquisition, Expert B covers retention. Together they cover the full funnel.

**Contradictory Frameworks** — Expert A says X, Expert B says not-X. Find the context that resolves the contradiction (they're usually BOTH right in different situations).

### 5.3 The Hidden Curriculum Extraction

Prompt to run after full extraction:

```
Based on [Expert Name]'s full body of work (all extracted content above), identify:

1. ASSUMED KNOWLEDGE: What do they assume their audience already knows that they never teach?
   These are entry requirements for their frameworks.

2. UNSAID PRINCIPLES: What behaviors do they consistently exhibit that they never explicitly advocate?
   (Watch for: how they talk about competitors, how they describe failure, what they celebrate in students)

3. CONTEXT DEPENDENCIES: Which of their frameworks only work in their specific context?
   (Market, time period, business model, audience size, budget level)

4. THE REAL THESIS: If you had to compress their entire worldview into one sentence that they've never
   literally said but that underlies everything they teach — what would it be?

5. WHAT THEY WON'T TEACH: What topics are conspicuously absent? What would a practitioner in their
   domain need to know that they never cover? (This is both a gap and a signal about their biases.)
```

### 5.4 The Gap Analysis

```
Given [Expert Name]'s domain ([DOMAIN]) and the frameworks they cover, identify:

1. Where does their playbook break down? (What situations would their advice fail?)
2. What comes BEFORE their frameworks in the practitioner journey? (Prerequisites they skip)
3. What comes AFTER? (What do students need to figure out on their own?)
4. Which of their frameworks is most dependent on conditions that existed [year] but may not hold now?
```

---

## 6. Phase 5: Operationalization

**Goal**: Convert distilled knowledge into tools a team member (or AI agent) can actually use.
**Time**: 2-6 hours.

### 6.1 Convert Frameworks into Templates

For each major framework, create:

**Decision Tree** — When do I use this?
```
Is this a [situation A]?
  → YES: Use [Framework X]
  → NO: Is this a [situation B]?
        → YES: Use [Framework Y]
        → NO: Use [Framework Z] or fall back to first principles
```

**Checklist Version** — The framework as a validation checklist:
```
[ ] Step 1 completed
[ ] Condition X verified
[ ] Output matches expected form
[ ] Anti-pattern A avoided
```

**Fill-in-the-Blank Template** — The framework with blanks to fill:
```
We are [AUDIENCE] who struggles with [PROBLEM].
Unlike [ALTERNATIVE], we [UNIQUE APPROACH].
This works because [MECHANISM].
```

### 6.2 AI Prompt Templates

For each major framework, write a prompt that applies it:

```markdown
## Prompt: Apply [Framework Name]

SYSTEM: You are applying [Expert Name]'s [Framework Name] framework.
[Paste the framework documentation here]

USER PROMPT:
Apply [Framework Name] to [SUBJECT/TOPIC].

Context:
- [Variable 1]: {USER_INPUT}
- [Variable 2]: {USER_INPUT}

Produce:
- [Output format]
- [Required sections]
- Flag any places where the framework's conditions are not met.
```

### 6.3 Training Material Format

For onboarding team members to an expert's frameworks:

**One-Page Summary** — The 3 most important things to know
**Framework Quick Reference** — All frameworks on one page with when-to-use triggers
**Practice Exercise** — A worked example for each major framework
**Common Mistakes Card** — The top 5 misapplications of their frameworks

### 6.4 KB Integration Protocol

When adding to the main knowledge base:

1. Add framework files to the appropriate `frameworks/` subdirectory
2. Update `_index.md` with the new frameworks and their "use when" triggers
3. Update `_quick-reference.md` if it's a top-tier framework
4. Cross-reference in related channel guides (`channels/`)
5. Add to relevant checklists if the framework has a validation component

---

## 7. Phase 6: Quality Gates

**Goal**: Verify the extraction is complete, accurate, and usable before closing.

### 7.1 Coverage Check

```
[ ] All major topics the expert is known for are represented in the extraction
[ ] Sources from at least 3 different time periods are included (to catch evolution)
[ ] Both "what to do" AND "what not to do" are captured
[ ] At least one source where they were challenged or pushed back on (reveals depth)
[ ] The expert's best-known frameworks are all present
[ ] Less-known frameworks (often deeper) are also included
```

### 7.2 Depth Check

For each framework, verify:
```
[ ] It's actionable (someone could execute it from the documentation alone)
[ ] It includes conditions (when to use / when NOT to use)
[ ] It includes at least one example
[ ] Anti-patterns are documented
[ ] It's not just a restatement of the source — the distillation adds clarity
```

### 7.3 Accuracy Check

```
[ ] Every framework has a source citation
[ ] Direct quotes are marked as quotes and verified against the source
[ ] Inferences are explicitly labeled as inferences
[ ] Nothing is attributed to the expert that isn't in a source
[ ] Any "they probably believe X" statements are labeled as interpretations
```

### 7.4 Novelty Check

```
[ ] NOVEL items are identified and prioritized
[ ] CONTRADICTORY items are documented with the contradiction and resolution
[ ] The "hidden curriculum" section is complete
[ ] The expert's unique contribution vs. the field is clearly stated
```

### 7.5 Utility Check

```
[ ] A team member unfamiliar with this expert could execute the frameworks from the docs alone
[ ] The AI prompt templates produce usable outputs when tested
[ ] The decision trees cover the most common use cases
[ ] The completeness checklist has been run
```

---

## 8. Master Extraction Prompt Template

This is the copy-pasteable, all-in-one prompt for a single source extraction. Customize the bracketed fields.

```
# Knowledge Extraction: [EXPERT NAME]
# Source Type: [TRANSCRIPT / ARTICLE / BOOK CHAPTER / COURSE MODULE / THREAD]
# Source: [URL or reference]
# Date: [When content was published]

---
[PASTE FULL CONTENT BELOW THIS LINE]


---
[END OF CONTENT]

## Extraction Instructions

You are extracting all knowledge from the above content attributed to [EXPERT NAME].

Rules:
1. Only extract what is actually present. Do not add, infer, or hallucinate.
2. Tag all inferences explicitly as [INFERENCE].
3. Include source timestamps or section references for every item.
4. Coin a memorable name for any unnamed framework (mark it [COINED]).

## Required Output Sections

### 1. FRAMEWORKS
[List all named or unnamed systems, models, processes — use Framework Documentation Format]

### 2. EDGES
[List all non-obvious insights, contrarian takes, hidden advantages — use Edge Catalog Format]

### 3. TACTICS
[List all specific actionable techniques — use Tactical Playbook Format]

### 4. PRINCIPLES
[List all underlying beliefs expressed — use Principle Collection Format]

### 5. ANTI-PATTERNS
[List all explicit "don't do this" lessons with reasoning]

### 6. EVOLUTION SIGNALS
[Any indication this expert's thinking has changed — what, when, why]

### 7. INFLUENCE SIGNALS
[Who they cite, who they push back against, what they've read/studied]

### 8. TACIT KNOWLEDGE
[What they assumed without explaining — the implicit curriculum]

### 9. GAPS
[What's conspicuously absent from this content given the domain]

### 10. TOP 3 MOST VALUABLE INSIGHTS
[Your assessment: what are the 3 highest-signal things in this content?]
```

---

## 9. Completeness Checklist

Run this when closing out an extraction project:

```markdown
# Extraction Completeness Checklist: [Expert Name]
Date completed: ___________
Completed by: ___________

## Source Coverage
[ ] All Tier 1 sources (their own published work) identified
[ ] At least 60% of Tier 1 sources extracted
[ ] Tier 2 sources (about them) cross-checked for consistency
[ ] Student/alumni signals collected
[ ] Source map filed in knowledge folder

## Extraction Completeness
[ ] All five extraction categories covered (Frameworks, Edges, Tactics, Principles, Anti-Patterns)
[ ] Evolution timeline documented
[ ] Influence graph built
[ ] Hidden curriculum identified

## Distillation Quality
[ ] All frameworks in standard documentation format
[ ] All tactics in playbook format
[ ] Edge catalog complete
[ ] Principle collection complete

## Synthesis
[ ] Novelty pass complete (NOVEL / ADDITIVE / REDUNDANT / CONTRADICTORY classifications)
[ ] Connection map to other experts in KB
[ ] Gap analysis complete
[ ] Real thesis statement written

## Operationalization
[ ] Decision trees for major frameworks
[ ] Checklist versions of major frameworks
[ ] AI prompt templates written and tested
[ ] One-page summary created
[ ] KB integration complete (_index.md updated)

## Quality Gates
[ ] Coverage check passed
[ ] Depth check passed
[ ] Accuracy check passed
[ ] Novelty check passed
[ ] Utility check passed (test run by someone unfamiliar with the expert)

## Output Files Created
[ ] source-map.md
[ ] [expert-name]-frameworks.md
[ ] [expert-name]-tactics.md
[ ] [expert-name]-edges.md
[ ] [expert-name]-principles.md
[ ] [expert-name]-synthesis.md
[ ] [expert-name]-quick-reference.md (one-pager)
[ ] [expert-name]-ai-prompts.md

## Known Gaps (unresolved)
-
-
```

---

## 10. Example: Sam Ovens Full Extraction

Sam Ovens is the founder of Consulting.com (formerly SkipBlast) and Skool.com. He built one of the most documented paths from zero to $100M+ through consulting and community, and his content is unusually candid about the frameworks he used.

### 10.1 Source Map (Sam Ovens)

**Tier 1 Primary Sources**

| Type | Source | Priority | Key Content |
|------|--------|----------|-------------|
| YouTube | youtube.com/@samovens | HIGH | 200+ videos on consulting, mindset, business |
| Course | Consulting.com Quantum Mastermind (documented by students) | HIGH | Full consulting system |
| Podcast | Various guest appearances | HIGH | Mental models, business philosophy |
| Blog | samovens.com/blog (archived) | MEDIUM | Early thinking, frameworks |
| Masterminds | Uploaded recordings on YouTube | HIGH | Unscripted, deepest material |
| X/Twitter | @samovens | MEDIUM | Compressed principles |

**Tier 2 Secondary Sources**

| Type | Source | Notes |
|------|--------|-------|
| Reddit | r/consulting, r/Entrepreneur | Students documenting frameworks |
| Press | Various profiles circa 2016-2019 | Founding story, early metrics |
| Skool community | Community posts indexed by students | Evolution to community model |

### 10.2 Frameworks (Sam Ovens)

---

**FRAMEWORK: The Niche Selection Matrix**
**Source**: Consulting.com YouTube, "How to Pick a Profitable Niche" (multiple videos)
**Purpose**: Identify a consulting niche that is monetizable, accessible, and aligned with existing credibility.

**Components**:
- **Pain Specificity**: The niche has a clear, named pain point (not "I help businesses grow")
- **Proven ROI**: The transformation has a clear dollar value or measurable outcome
- **Access**: You can reach this market affordably and directly
- **Credibility Fit**: You have enough background to be credible (not necessarily an expert)

**The Qualification Questions**:
1. Who specifically has this problem? (name the job title, industry, situation)
2. What does this problem cost them? (in dollars, hours, or emotional toll)
3. Where do they already gather? (communities, events, platforms)
4. Why hasn't this been solved for them already?
5. Can you solve it for at least one person THIS MONTH?

**When to Use**: At business formation stage, or when a consulting practice has plateaued.
**NOT For**: Businesses already at product-market fit. This is a discovery tool, not an optimization tool.

**Anti-pattern**: Choosing a niche based on passion or interest rather than proven pain + accessible market.

**Quote**: "The riches are in the niches, but only if the niche has a real problem they'll pay to solve."

---

**FRAMEWORK: The Consulting Value Ladder**
**Source**: Consulting.com course material, documented by multiple students
**Purpose**: Structure offers to maximize LTV without overselling clients.

**Steps**:
1. **Lead Magnet** → Free value that pre-qualifies (video training, case study)
2. **Entry Offer** → Low-ticket, high-value ($497-$2,000) to establish relationship
3. **Core Offer** → High-ticket done-with-you ($5,000-$25,000)
4. **Premium Offer** → Done-for-you or inner circle ($25,000+)
5. **Continuity** → Monthly retainer or community (Skool model)

**Key Insight**: Most consultants skip steps 1-2 and try to sell into step 3 cold. The value ladder works as a trust escalator — each level proves you deliver before the client invests more.

**When to Use**: Designing a new consulting practice OR diagnosing low close rates (usually means skipping rungs).

---

**FRAMEWORK: The Dream Customer Avatar**
**Source**: Multiple YouTube videos and course content
**Purpose**: Identify not just who has the problem but who is MOTIVATED to solve it.

**Components — the "3 Musts"**:
- **Problem-aware**: They know they have the problem (not just bystanders to it)
- **Solution-seeking**: They are actively looking for a solution right now
- **Action-ready**: They have the means and will to invest in a solution

**The Avatar Questions**:
1. What keeps them up at 3am?
2. What do they secretly fear will happen if nothing changes?
3. What do they want to tell their friends/spouse/boss in 90 days?
4. What have they already tried? Why did it fail?
5. What objections do they have to working with someone like you?

**Key Insight**: Most consultants target problem-aware people who are NOT solution-seeking. Marketing becomes infinitely cheaper when you only talk to people already trying to solve the problem.

---

**FRAMEWORK: The Diagnostic Sale**
**Source**: Consulting.com sales training
**Purpose**: Close high-ticket consulting without a "pitch" — instead, diagnose the problem live and prescribe a solution.

**Steps**:
1. **Situation** — establish baseline (what are they doing now, what results are they getting)
2. **Problem** — uncover the actual bottleneck (ask: "what's the biggest thing stopping you from X?")
3. **Implication** — make the cost of inaction explicit ("if this doesn't change, what happens in 12 months?")
4. **Solution** — only after steps 1-3, prescribe YOUR solution as the mechanism
5. **Investment** — present price as an ROI statement, not a cost

**Key Insight**: Prospects who arrive at the solution through their own answers to your questions believe it and buy it. Prospects who are pitched the solution resist it.

**Anti-pattern**: Leading with your offer or methodology before the prospect has articulated their own pain.

---

**FRAMEWORK: The One-Constraint Theory**
**Source**: Sam Ovens YouTube, various interviews
**Purpose**: Diagnose why a business is not growing.

**The Thesis**: At any given moment, a business has EXACTLY ONE true constraint. Every other "problem" is a symptom of that constraint. Solving non-constraint problems yields no growth.

**The Constraints Hierarchy** (most common):
1. Offer clarity — people don't know what you sell or who it's for
2. Lead generation — not enough conversations happening
3. Sales conversion — conversations not converting to paying clients
4. Delivery quality — clients not getting results, killing referrals and retention
5. Operations — delivery bottlenecked by systems/people

**Diagnostic Question**: "If we doubled X, would revenue double?" If yes, X is likely your constraint.

**Anti-pattern**: Optimizing delivery before fixing lead generation. Working on social media when the real constraint is offer clarity.

---

### 10.3 Edges (Sam Ovens)

---

**EDGE: High-Ticket Beats High-Volume**
**Conventional View**: More clients = more revenue. Scale through volume.
**The Edge**: One $10,000 client delivers the same revenue as 100 $100 clients — with 1/10th the complexity. Complexity kills quality of delivery, which kills referrals.
**Evidence**: Sam's own path — $1M revenue with fewer than 30 clients/year at one point.
**Application**: Before scaling volume, exhaust your ability to increase average contract value.
**Confidence**: HIGH

---

**EDGE: The Niche Is the Marketing**
**Conventional View**: Marketing is how you reach people. The niche is just a target audience.
**The Edge**: A tightly defined niche is itself a trust signal. "I work with X who struggle with Y" does the qualification and authority-building automatically — the prospect self-selects, the price resistance drops.
**Evidence**: Sam's case studies consistently show conversion rates 3-5x higher after niche tightening.
**Application**: Tighten the niche BEFORE investing in marketing channels.
**Confidence**: HIGH

---

**EDGE: Webinars as Sales Calls at Scale**
**Conventional View**: Webinars are content delivery tools.
**The Edge**: A properly structured webinar follows the same arc as a perfect sales call — diagnosis, insight, hope, solution, offer. The webinar IS the sales process, not a funnel leading to it.
**Evidence**: Consulting.com built to $25M+ using webinars as the primary close mechanism.
**Application**: Structure webinars as diagnostic conversations, not demonstrations. End with an offer.
**Confidence**: HIGH

---

**EDGE: Specificity = Trust, Generality = Distrust**
**Conventional View**: Broad positioning appeals to more people.
**The Edge**: Broad claims ("I help businesses grow") trigger skepticism automatically. Specific claims ("I help SaaS companies with 10-50 employees reduce churn in their first 90 days") trigger curiosity and credibility.
**Evidence**: Consistently observed across Sam's own positioning shifts and his students' results.
**Application**: The most specific version of your offer that is still true is always better than a broader version.
**Confidence**: HIGH

---

### 10.4 Anti-Patterns (Sam Ovens)

| Anti-Pattern | Why It Fails | The Fix |
|--------------|-------------|---------|
| "I help businesses grow" positioning | No trust signal, no self-qualification, commoditized | Name the exact customer, exact problem, exact outcome |
| Building before selling | Wastes months on a product no one wants | Sell first, build second. Get one client to pay before building the system |
| Competing on price | Races to the bottom, attracts bad clients | Compete on ROI certainty. Show the math. |
| Hiring before constraints are solved | Adds complexity without fixing the root issue | Solve the one constraint yourself first |
| Building too many offers | Splits attention, confuses market | One offer, one audience, one channel until $1M |
| Optimizing funnel before validating offer | Efficient delivery of something nobody wants | Get 10 paying clients before optimizing anything |

---

### 10.5 Principles (Sam Ovens)

1. **"Specificity is the antidote to skepticism."**
   — More specific = more credible. Applies to positioning, case studies, promises.

2. **"Solve a real problem for a specific person. Everything else is vanity."**
   — Business model should derive from pain, not from capability or interest.

3. **"One constraint at a time."**
   — Multi-pronged approaches signal unclear thinking. Find the one thing. Fix it.

4. **"You can't outwork a bad model."**
   — If the business model requires constant hustle to survive, the model is wrong.

5. **"The market doesn't care about your process. It cares about your outcome."**
   — Don't lead with methodology. Lead with transformation.

6. **"Scale through simplicity, not complexity."**
   — His shift from consulting → Skool was a simplicity move: teaching a repeatable model beats custom delivery every time.

---

### 10.6 The Real Thesis (Sam Ovens)

Everything Sam teaches reduces to:

> *Find one specific person with one specific pain they'll pay to eliminate. Remove every distraction — product complexity, audience breadth, channel diversification — until your one offer reliably converts. Only THEN scale.*

He never says this in exactly these words. But every framework, tactic, and principle is a variation of this thesis.

---

### 10.7 Gaps and Context Dependencies

**Gaps in Sam's Framework**:
- Minimal content on paid acquisition (he's primarily organic/webinar focused)
- Limited guidance on outbound at scale (better suited for early-stage validation)
- Little on content moats or community network effects (though Skool addresses this partially)
- Assumes market sophistication — some niches are problem-unaware, not solution-seeking

**Context Dependencies**:
- His frameworks were developed 2014-2020 when webinar CPLs were lower
- High-ticket consulting model works better in certain niches (B2B, professional services) than others (consumer, micro-SaaS)
- The "one constraint" model assumes you can identify the constraint — requires at least 10 clients' worth of data to see patterns

---

## 11. Source-Type Handling Guide

### YouTube Videos

| Step | Action | Tool |
|------|--------|-------|
| 1 | Get transcript | Tactiq.io Chrome extension, or YouTube's own captions |
| 2 | Clean transcript | Remove filler, fix punctuation, add timestamps every 2 min |
| 3 | Run extraction prompt | Claude / GPT-4o with full transcript |
| 4 | Verify against video | Spot-check 3-5 quotes against actual timestamps |

**Tips**:
- Sort by "Most Popular" to find the highest-signal videos first
- Look for videos where they answer questions or push back (more tacit knowledge visible)
- Creator's OLDEST videos often contain the rawest, least polished thinking

---

### Podcast Episodes (guest appearances)

| Step | Action | Tool |
|------|--------|-------|
| 1 | Find all episodes | ListenNotes search, Podchaser, Google: `"[NAME]" podcast` |
| 2 | Prioritize longer episodes | 60+ minutes = more depth |
| 3 | Get transcript | Otter.ai, Descript auto-transcription, or download audio + Whisper |
| 4 | Extract | Same extraction prompt |

**Tips**:
- Host's questions reveal what practitioners care about most
- Push-back moments ("but what about X?") force the guest to defend first principles
- Round-number timestamps often signal "key insight" moments (host cut to a new segment)

---

### Books

| Step | Action | Tool |
|------|--------|-------|
| 1 | Chapter-by-chapter central claim | Read or skim, document the argument |
| 2 | Index all named frameworks | Look for bolded terms, section headers |
| 3 | Extract exercises/worksheets | Often reveal what the expert thinks needs practice |
| 4 | Full synthesis pass | What is the through-line across all chapters? |

**Tips**:
- Introduction and conclusion have the explicit thesis
- Chapter 2-3 usually have the foundational framework everything else builds on
- Footnotes and bibliography reveal intellectual lineage

---

### Online Courses

| Step | Action | Tool |
|------|--------|-------|
| 1 | Curriculum map first | Screenshot module/lesson titles |
| 2 | Extract worksheets and exercises | These are distilled frameworks |
| 3 | Watch intro + outro of each module | Summary moments |
| 4 | Q&A calls within the course | Deepest tacit knowledge |

**Tips**:
- Module structure reveals the expert's pedagogical theory (what they think needs to come first)
- Optional modules are usually the expert's pet theories
- Student questions in Q&As reveal the real obstacles their frameworks encounter

---

### X / Twitter Threads

| Step | Action | Tool |
|------|--------|-------|
| 1 | Find best threads | Typefully, Threadreaderapp, or search: `from:[HANDLE] (min_faves:1000)` |
| 2 | Export | Threadreaderapp "read" URL for clean text |
| 3 | Extract | Run extraction prompt — threads are usually already tight and high-signal |

**Tips**:
- Reply threads are gold — original tweet + debate in comments = framework + stress test
- "Quote tweet storms" (where they pile on someone else's thread) reveal contrarian positions
- Old threads (2+ years) show where their thinking has evolved from

---

### X Spaces / Spaces Recordings

| Step | Action | Tool |
|------|--------|-------|
| 1 | Find recordings | Search X for spaces, or `site:twitter.com [NAME] space` |
| 2 | Download audio | `twspace_dl` (open source), or screen record if no other option |
| 3 | Transcribe | Whisper locally (`whisper audio.mp3 --model large`) or Otter.ai |
| 4 | Speaker-label transcript | Multi-speaker diarization via Pyannote or AssemblyAI |
| 5 | Extract per speaker | Run extraction prompt with speaker labels |

**Tips**:
- Spaces are the least polished format — highest tacit knowledge density
- Host dynamics reveal who respects whom in the space
- Questions from audience reveal the field's open problems

---

### Reddit / Forum Posts

| Step | Action | Tool |
|------|--------|-------|
| 1 | Search | `site:reddit.com "[NAME]"` + relevant subreddits |
| 2 | Collect threads | Copy thread + top comments |
| 3 | Classify | Student reporting frameworks vs. critics vs. Q&As |
| 4 | Extract student reports | These are often the clearest restatements of tacit knowledge |

**Tips**:
- Top-voted student success stories often contain the most actionable version of the frameworks
- Skeptic threads reveal where the expert's claims are weakest
- AMA (Ask Me Anything) posts are goldmines if the expert participated

---

## 12. Recommended Tools

### Transcription

| Tool | Best For | Cost |
|------|----------|------|
| **Whisper** (local) | Any audio file, free, high quality | Free (requires GPU or slow) |
| **Otter.ai** | Live or uploaded audio, speaker labels | Free tier available |
| **Tactiq.io** | YouTube transcripts in-browser | Free tier available |
| **AssemblyAI** | API-based, speaker diarization | Pay per minute |
| **Rev.com** | Human-quality transcription | ~$1.50/min |

### Source Discovery

| Tool | Best For | Cost |
|------|----------|------|
| **ListenNotes** | Podcast episode search | Free |
| **Podchaser** | Podcast guest search | Free |
| **Threadreaderapp** | Twitter thread export | Free |
| **yt-dlp** | YouTube download + subtitles | Free (CLI) |
| **twspace_dl** | X Spaces download | Free (CLI) |

### Extraction & AI

| Tool | Best For | Notes |
|------|----------|-------|
| **Claude (claude.ai)** | Long-form extraction, nuanced synthesis | Best for 100k+ token contexts |
| **GPT-4o** | Extraction + structured output | Strong structured JSON output |
| **NotebookLM** | Multi-source synthesis | Google product, free, good for book-level |
| **Perplexity** | Source discovery + quick facts | Good for supplementing source maps |

### Organization

| Tool | Best For | Notes |
|------|----------|-------|
| **Obsidian** | Knowledge graph across experts | Good for seeing connections |
| **Notion** | Collaborative knowledge base | Good for team access |
| **Plain markdown files** | AI-agent-readable KB | Best for this system |

---

## 13. Time & Depth Tiers

### Tier 1: Quick Scan (2-4 hours)

**Goal**: Get the top 5 frameworks and top 5 edges. Good for a new expert you've just encountered.

**Process**:
1. Source Discovery (30 min) — find top 3 most-viewed videos or most-cited content
2. Extraction (1 hour) — run extraction prompt on top 2-3 sources
3. Distillation (45 min) — framework + edge catalog only
4. Synthesis (30 min) — novelty pass only
5. Output: 1-2 page quick reference doc

**Output Files**: One markdown file: `[name]-quick-extract.md`

---

### Tier 2: Full Extraction (1-2 days)

**Goal**: Complete framework, edge, and principle library. Usable as a reference document.

**Process**:
1. Source Discovery (2-4 hours) — full Tier 1-3 source map
2. Extraction (4-8 hours) — all major sources
3. Distillation (2-3 hours) — all five categories
4. Synthesis (1-2 hours) — novelty, connections, hidden curriculum
5. Operationalization (2-3 hours) — templates and prompts
6. Quality gates (1 hour)

**Output Files**: Full file set (frameworks, tactics, edges, principles, synthesis, quick-reference, AI prompts)

---

### Tier 3: Deep Clone (1 week)

**Goal**: Capture the expert's full operating system including tacit and implicit knowledge. Usable for AI personalization or deep practitioner training.

**Process**: All Tier 2 steps PLUS:
- Secondary source extraction (Reddit, student accounts, press)
- Influence graph built out
- Evolution timeline mapped across years
- Contradiction analysis complete
- Multiple extraction passes per source (initial + adversarial review)
- External review: have someone unfamiliar with the expert try to apply the frameworks

**Output Files**: All Tier 2 files PLUS influence-graph.md, evolution-timeline.md, training-materials/

---

## Appendix: Adapting This Workflow for Different Expert Types

### For Marketing Practitioners (agency owners, CMOs)
- Weight: Tactics > Frameworks > Principles
- Best sources: Client case studies, results posts, process breakdowns
- Watch for: Results that may not transfer (their clients had X, yours have Y)

### For Investors (VCs, angels, fund managers)
- Weight: Principles > Edges > Anti-Patterns
- Best sources: Investment memos, portfolio post-mortems, long-form interviews
- Watch for: Survivorship bias in their examples

### For Operators (CEOs, COOs, scale specialists)
- Weight: Frameworks > Anti-Patterns > Tactics
- Best sources: Team documents they've published, management writing, hiring philosophy
- Watch for: Context-locked advice (works at their scale, not yours)

### For Technical Experts (engineers, data scientists, product managers)
- Weight: Frameworks > Tactics > Principles
- Best sources: GitHub, technical blog, conference talks
- Watch for: Their work often contains more tacit knowledge than their writing

### For Academics / Researchers
- Weight: Principles > Frameworks > Edges
- Best sources: Papers, lectures, response to critics
- Watch for: Practitioners often simplify their frameworks — go back to source for full nuance

---

*Last updated: 2026-03-15*
*Source: Derived from Preston Rhodes X Space extraction process*
*Apply to: Any expert in any domain — adjust source types and category weighting per domain*
