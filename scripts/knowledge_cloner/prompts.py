"""
Knowledge Cloner — All LLM prompt templates.

Ported from the knowledge-cloning-workflow.md master document.
"""


# ---------------------------------------------------------------------------
# Phase 2b: Master Extraction Prompt (per source)
# ---------------------------------------------------------------------------

MASTER_EXTRACTION_PROMPT = """# Knowledge Extraction: {expert_name}
# Source Type: {source_type}
# Source: {source_url}
# Date: {source_date}

---
{content}
---
[END OF CONTENT]

## Extraction Instructions

You are extracting all knowledge from the above content attributed to {expert_name}.

Rules:
1. Only extract what is actually present.
2. Do not hallucinate or over-generalize.
3. Tag all inferences explicitly as [INFERENCE].
4. Include timestamps or section references for every item.
5. Coin a memorable name for unnamed frameworks and mark them [COINED].
6. Separate what is explicit, tacit, and implicit.
7. Flag anything that appears context-dependent.

## Required Output Sections

### 1. FRAMEWORKS
[List all systems, models, processes, or diagnostic structures]

For each framework use:
## FRAMEWORK: [Name or coin a name]
**Source**: [timestamp or section]
**Purpose**: One sentence — what problem does this solve?
**Components**: List each element
**Steps**: Only include if sequential. If not sequential, skip.
**Conditions**: When should this be used? When should it NOT be used?
**Quote**: The closest direct quote from the source

### 2. EDGES
[List all non-obvious insights, contrarian takes, or hidden advantages]

For each edge use:
## EDGE: [Short memorable title]
**Source**: [timestamp or section]
**Conventional View**: What most people believe
**The Edge**: What the expert believes or does differently
**Why It's True**: Their reasoning from the source
**Application**: How to use this practically

### 3. TACTICS
[List all actionable techniques]

For each tactic use:
## TACTIC: [Verb phrase]
**Source**: [timestamp or section]
**What**: The specific action
**Why**: The mechanism that makes it work
**How**: Step-by-step if given
**Tools**: Any tools mentioned
**Expected Result**: What outcome they claim
**Failure Mode**: How this can go wrong if misapplied

### 4. PRINCIPLES
[List all durable beliefs and the behaviors they drive]

For each principle use:
## PRINCIPLE: [State as a belief]
**Source**: [timestamp or section]
**Stated As**: Direct quote if possible
**Behavior It Drives**: What decisions or actions this principle generates
**Repeat Signal**: Does this principle appear elsewhere in the content?

### 5. ANTI-PATTERNS
[List all explicit or repeated warnings]

For each anti-pattern use:
## ANTI-PATTERN: [What NOT to do]
**Source**: [timestamp or section]
**The Trap**: What most people do
**Why It Fails**: Their explanation
**The Fix**: What to do instead

### 6. EVOLUTION SIGNALS
[Any indication their thinking changed — what changed, when, and why]

### 7. INFLUENCE SIGNALS
[Who they cite, borrow from, or argue against]

### 8. TACIT KNOWLEDGE
[What they assume without explaining]

### 9. BOUNDARY SIGNALS
[What they refuse to do or consistently reject]

### 10. CONTEXT DEPENDENCIES
[What conditions seem necessary for the advice to work]

### 11. GAPS
[What is missing or conspicuously underweighted]

### 12. TOP 3 MOST VALUABLE INSIGHTS
[Highest-signal takeaways from this source only]"""


# ---------------------------------------------------------------------------
# Phase 2b: Repo-Specific Extraction Prompt (for GitHub repositories)
# Based on arXiv:2603.11808 — Automated Skill Acquisition from Agentic Repos
# ---------------------------------------------------------------------------

REPO_EXTRACTION_PROMPT = """# Procedural Knowledge Extraction: {expert_name}
# Source Type: GitHub Repository
# Source: {source_url}
# Date: {source_date}

---
{content}
---
[END OF REPOSITORY CONTENT]

## Extraction Instructions

You are extracting procedural knowledge from the above GitHub repository attributed to {expert_name}.
This is a code repository — focus on extracting SKILLS, PATTERNS, and ARCHITECTURAL DECISIONS,
not just what the code does but HOW and WHY it does it.

Rules:
1. Only extract what is actually present in the code and documentation.
2. Do not hallucinate features or capabilities.
3. Tag all inferences explicitly as [INFERENCE].
4. Include file paths for every item.
5. Coin a memorable name for unnamed patterns and mark them [COINED].
6. Separate what is explicit (documented), tacit (visible in code but undocumented), and implicit (design decisions).
7. Flag anything that appears environment-dependent or hardcoded.

## Required Output Sections

### 1. SKILLS (Reusable Procedural Patterns)
[Identify discrete, reusable skills — recurring patterns that solve a class of problems]

For each skill use the S = (C, π, T, R) four-tuple format:
## SKILL: [Name or coin a name]
**File(s)**: [file paths where this skill lives]
**Conditions (C)**: When should this skill be activated? What prerequisites must be true?
**Policy (π)**: The step-by-step procedure — what actions does this skill execute?
**Termination (T)**: How do you know the skill completed successfully? What are the success criteria?
**Interface (R)**: What are the inputs, outputs, and composition protocols?
**Recurrence**: Does this pattern appear in multiple contexts?
**Non-obviousness**: What domain expertise was needed to build this?
**Generalizability**: Can this be parameterized for different contexts?

### 2. FRAMEWORKS
[List all systems, models, processes, or architectural patterns]

For each framework use:
## FRAMEWORK: [Name or coin a name]
**File(s)**: [file paths]
**Purpose**: One sentence — what problem does this solve?
**Components**: List each element
**Steps**: Only include if sequential. If not sequential, skip.
**Conditions**: When should this be used? When should it NOT be used?
**Dependencies**: External libraries, APIs, or services required

### 3. EDGES (Non-Obvious Implementation Insights)
[List all non-obvious implementation choices, workarounds, or hidden advantages]

For each edge use:
## EDGE: [Short memorable title]
**File(s)**: [file paths]
**Conventional Approach**: What most developers would do
**The Edge**: What this repo does differently and why
**Why It Works**: Their reasoning or the problem it solves
**Application**: How to reuse this in other contexts

### 4. TACTICS (Actionable Techniques)
[List all actionable techniques visible in the code]

For each tactic use:
## TACTIC: [Verb phrase]
**File(s)**: [file paths]
**What**: The specific technique
**Why**: The mechanism that makes it work
**How**: Step-by-step implementation
**Tools**: Libraries, APIs, or services used
**Failure Mode**: How this can go wrong if misapplied

### 5. ARCHITECTURE DECISIONS
[List key architectural choices and their rationale]

For each decision use:
## DECISION: [What was decided]
**File(s)**: [file paths]
**Context**: What problem or constraint led to this decision
**Decision**: What they chose
**Alternatives Rejected**: What they could have done instead [INFERENCE if not documented]
**Consequences**: Trade-offs of this decision

### 6. ANTI-PATTERNS
[List any code smells, documented warnings, or patterns explicitly avoided]

### 7. DEPENDENCY MAP
[Key external dependencies and what they're used for]

### 8. CONFIGURATION PATTERNS
[How the system is configured, what's parameterized vs hardcoded]

### 9. ERROR HANDLING PATTERNS
[How errors are handled, retry logic, fallback strategies]

### 10. SECURITY PATTERNS
[Authentication, authorization, input validation, secret management]

### 11. GAPS
[What is missing, incomplete, or conspicuously absent]

### 12. TOP 3 MOST VALUABLE SKILLS
[Highest-value reusable skills from this repository — the ones worth extracting into standalone SKILL.md files]"""


# ---------------------------------------------------------------------------
# Phase 3: Distillation Prompts (one per category)
# ---------------------------------------------------------------------------

DISTILL_FRAMEWORKS_PROMPT = """You are distilling frameworks from raw knowledge extractions for {expert_name}.

Below are all raw extraction outputs from multiple sources. Your task:
1. Merge duplicate frameworks — keep the richest version, cite all sources
2. Structure each framework in clean documentation format
3. Include: purpose, components, steps (if sequential), conditions, failure modes, examples, source quotes
4. Order by importance (most fundamental first)
5. Mark any framework that was unnamed in the source as [COINED]

## Raw Extractions:
{content}

## Output Format:
For each framework, use this exact format:

# [Framework Name]
**Source**: [Expert Name], [Sources where found]
**Category**: [Mental Model / Process / Diagnostic / Creative / Decision]

## Purpose
One sentence: what problem does this solve, for whom, and in what context?

## When to Use
- Situation A
- Situation B
NOT for: [explicit exclusions]

## Components
- **Element 1**: Description
- **Element 2**: Description

## Process
[If sequential:]
1. Step one
2. Step two

## Conditions
What must be true for this framework to work?

## Failure Modes
How people misuse it or apply it in the wrong environment.

## Example
Walk through one concrete application.

## Source Quotes
> "Direct quote" — [Source]

---"""


DISTILL_TACTICS_PROMPT = """You are distilling tactical playbooks from raw knowledge extractions for {expert_name}.

Below are all raw extraction outputs from multiple sources. Your task:
1. Merge duplicate tactics — keep the most detailed version
2. Structure each tactic as an executable playbook
3. Include: what, why, how (steps), tools, expected results, failure modes
4. Group by category (Acquisition / Retention / Conversion / Operations / Product)
5. Order within each category by impact

## Raw Extractions:
{content}

## Output Format:
For each tactic:

# Playbook: [Tactic Name]
**Source**: [Expert Name], [Sources]
**Category**: [Acquisition / Retention / Conversion / Operations / Product / Hiring]
**Difficulty**: [Low / Medium / High]

## The Move
Plain English: what are you actually doing?

## Why It Works
The causal chain.

## Step-by-Step
1.
2.
3.

## Tools
- Tool name — what it is used for

## Expected Results
- What metric changes
- Magnitude if stated

## Warning Signs
How do you know it is failing or being misapplied?

---"""


DISTILL_EDGES_PROMPT = """You are distilling non-obvious insights and edges from raw knowledge extractions for {expert_name}.

Below are all raw extraction outputs. Your task:
1. Merge duplicate edges — keep the strongest evidence
2. Rate confidence: HIGH (stated directly, repeated), MEDIUM (strongly implied), LOW (inferred)
3. Include: conventional view, the edge, evidence, implication, counter-conditions
4. Group by domain

## Raw Extractions:
{content}

## Output Format:
For each edge:

# Edge: [Memorable Short Title]
**Source**: [Expert Name], [Sources]
**Domain**: [Product / Sales / Hiring / Investing / Marketing / etc.]

## The Conventional View
What most practitioners believe.

## The Edge
What this expert believes instead.

## Evidence / Reasoning
Why they think this is true.

## Implication
If this edge is real, what should change in practice?

## Confidence Level
- HIGH / MEDIUM / LOW with justification

## Counter-Conditions
Where might this stop working?

---"""


DISTILL_PRINCIPLES_PROMPT = """You are distilling core principles from raw knowledge extractions for {expert_name}.

Below are all raw extraction outputs. Your task:
1. Merge duplicate principles — combine evidence from all sources
2. Order by importance (most fundamental first)
3. Include: the belief stated clearly, best quote, behaviors it drives, where it repeats
4. Separate explicit principles from inferred ones

## Raw Extractions:
{content}

## Output Format:

# Principles: {expert_name}

## Core Beliefs (ordered by importance)

### Principle 1: [State as a belief]
**In Their Words**: Best direct quote
**Implication**: What this belief causes them to do
**Origin**: Where or how it seems to have formed
**Seen In**: Sources where it repeats
**Confidence**: [Explicit / Inferred]

---"""


DISTILL_ANTIPATTERNS_PROMPT = """You are distilling anti-patterns from raw knowledge extractions for {expert_name}.

Below are all raw extraction outputs. Your task:
1. Merge duplicate anti-patterns
2. Include: the trap, why it fails, what to do instead, source
3. Group by severity (critical mistakes vs minor inefficiencies)

## Raw Extractions:
{content}

## Output Format:

# Anti-Patterns: {expert_name}

## Critical Anti-Patterns
Things that will cause failure if not avoided.

| Anti-Pattern | Why It Fails | What They Do Instead | Source |
|--------------|-------------|----------------------|--------|

## Common Mistakes
Things that reduce effectiveness.

| Anti-Pattern | Why It Fails | What They Do Instead | Source |
|--------------|-------------|----------------------|--------|

## Detailed Anti-Patterns

### ANTI-PATTERN: [What NOT to do]
**Severity**: Critical / Moderate / Minor
**The Trap**: What most people do
**Why It Fails**: Their explanation
**The Fix**: What to do instead
**Source**: [References]

---"""


# ---------------------------------------------------------------------------
# Phase 4: Synthesis Prompts (Claude Sonnet)
# ---------------------------------------------------------------------------

SYNTHESIS_NOVELTY_PROMPT = """Compare the following extracted knowledge from {expert_name} against our existing knowledge base.

## Extracted Knowledge:
{content}

## Existing Knowledge Base Frameworks:
{existing_kb}

For each extracted item, classify as:
- **NOVEL**: Not represented in the KB at all
- **ADDITIVE**: Expands or deepens an existing concept
- **REDUNDANT**: Already covered sufficiently
- **CONTRADICTORY**: Conflicts with an existing framework or principle

For NOVEL and ADDITIVE items, explain what they add.
For CONTRADICTORY items, document both views and identify the conditions under which each is valid.

## Output Format:

# Novelty Analysis: {expert_name}

## NOVEL Items (not in KB)
[List with explanation of what each adds]

## ADDITIVE Items (deepens existing)
[List with what existing concept they expand and how]

## CONTRADICTORY Items (conflicts)
[List with both views and resolution conditions]

## REDUNDANT Items (already covered)
[Brief list]

## Unique Contribution Summary
What does {expert_name} bring that no other source in the KB provides?"""


SYNTHESIS_HIDDEN_CURRICULUM_PROMPT = """Based on {expert_name}'s full body of extracted work, identify:

## Distilled Knowledge:
{content}

Analyze the above and identify:

### 1. ASSUMED KNOWLEDGE
What do they assume their audience already knows, but never teach directly?

### 2. UNSAID PRINCIPLES
What behaviors do they consistently exhibit without explicitly recommending them?

### 3. CONTEXT DEPENDENCIES
Which frameworks only work in their specific environment?
(Examples: business model, audience size, capital, brand strength, market timing)

### 4. THE REAL THESIS
Compress their worldview into one sentence they may never have said verbatim but that underlies everything.

### 5. WHAT THEY WON'T TEACH
What is conspicuously absent? What do practitioners still need that this expert never covers?

Be specific. Use evidence from the extracted content to support each point."""


SYNTHESIS_GAP_ANALYSIS_PROMPT = """Given {expert_name}'s domain ({domain}) and the extracted system below, identify gaps.

## Extracted System:
{content}

Analyze and answer:

1. **Where does their playbook break down?**
   What situations, markets, or conditions make their advice fail?

2. **What comes BEFORE their frameworks in the practitioner journey?**
   What prerequisite knowledge or conditions do they assume?

3. **What comes AFTER their frameworks?**
   Where does their system end and what's the next level?

4. **Which ideas depend on specific conditions?**
   Year, market, platform, technology, or business model assumptions?

5. **Which ideas are durable?**
   Likely to survive changing conditions — timeless principles vs dated tactics.

## Output as structured markdown with clear headers for each section."""


SYNTHESIS_REAL_THESIS_PROMPT = """You have the complete extracted and distilled knowledge from {expert_name}.

## Full Distilled Knowledge:
{content}

Your task:
1. Read everything above carefully
2. Identify the 3-5 keystone ideas that everything else depends on
3. Write the expert's REAL THESIS — one sentence that captures their worldview
4. Explain the connection map between their major frameworks
5. Identify their unique contribution vs general field knowledge

## Output Format:

# The Real Thesis: {expert_name}

## One-Sentence Worldview
[The sentence]

## Keystone Ideas
1. [Idea] — why everything else depends on this
2. ...

## Connection Map
How the major frameworks relate to each other and form a system.

## Unique Contribution
What {expert_name} brings that is genuinely theirs vs borrowed/common knowledge.

## Intellectual Lineage
Who influenced them, who they've influenced, and how their ideas fit in the broader landscape."""


# ---------------------------------------------------------------------------
# Phase 5: Operationalization Prompts
# ---------------------------------------------------------------------------

OPERATIONALIZE_QUICK_REFERENCE_PROMPT = """Create a one-page quick reference for {expert_name}'s knowledge system.

## Distilled Knowledge:
{content}

## Output Format:

# Quick Reference: {expert_name}
**Domain**: {domain}

## Top 5 Frameworks
| Framework | Use When | Key Insight |
|-----------|----------|-------------|

## Top 5 Edges
| Edge | Conventional View | Their View |
|------|-------------------|------------|

## Top 5 Tactics
| Tactic | Category | Expected Result |
|--------|----------|-----------------|

## Core Principles (3-5)
1. ...

## Critical Anti-Patterns (3-5)
1. ...

## The Real Thesis
[One sentence]"""


OPERATIONALIZE_DECISION_TREES_PROMPT = """Create decision trees for {expert_name}'s major frameworks.

## Frameworks:
{content}

For each major framework, create a decision tree that helps a practitioner know:
1. Whether to use this framework (qualifying questions)
2. Which variant or path to follow
3. What to do if conditions aren't met

## Output Format:

# Decision Trees: {expert_name}

## [Framework Name] Decision Tree

```
Is [condition A] true?
  → YES: Use [Framework X], start at Step 1
  → NO: Is [condition B] true?
        → YES: Use modified version: [modification]
        → NO: This framework doesn't apply. Consider [alternative]
```

### Prerequisites
- [What must be true before starting]

### Red Flags (stop and reassess)
- [Warning sign 1]
- [Warning sign 2]"""


OPERATIONALIZE_CHECKLISTS_PROMPT = """Create execution checklists for {expert_name}'s major frameworks and tactics.

## Distilled Knowledge:
{content}

For each major framework and tactic, create a checklist version that someone can follow step-by-step.

## Output Format:

# Checklists: {expert_name}

## [Framework/Tactic Name] Checklist

### Pre-Conditions
- [ ] [Condition 1 verified]
- [ ] [Condition 2 verified]

### Execution Steps
- [ ] Step 1: [specific action]
- [ ] Step 2: [specific action]

### Quality Check
- [ ] [Output matches expected form]
- [ ] [Anti-pattern A avoided]
- [ ] [Expected result achieved]"""


OPERATIONALIZE_AI_PROMPTS_PROMPT = """Create AI prompt templates for applying {expert_name}'s major frameworks.

## Distilled Knowledge:
{content}

For each major framework, create a prompt template that an AI system can use to apply it.

## Output Format:

# AI Prompts: {expert_name}

## Prompt: Apply [Framework Name]

**When to use**: [trigger conditions]

```
SYSTEM: You are applying {expert_name}'s [Framework Name] framework.
[Paste the framework documentation]

USER PROMPT:
Apply [Framework Name] to [SUBJECT/TOPIC].

Context:
- [Variable 1]: {{user_input_1}}
- [Variable 2]: {{user_input_2}}

Produce:
- [Output format]
- [Required sections]
- Any missing prerequisites
- Any conditions not met
- Any anti-pattern risks
```"""


# ---------------------------------------------------------------------------
# Phase 6: Quality Gate Prompts
# ---------------------------------------------------------------------------

QUALITY_GATE_PROMPT = """You are evaluating the quality of a knowledge extraction for {expert_name}.

## Source Map:
{source_map}

## Distilled Knowledge:
{distilled}

## Synthesis:
{synthesis}

## Operational Outputs:
{operational}

Score each quality gate PASS or FAIL with specific evidence.

## Quality Gates

### 1. Coverage Check
- [ ] All major topics the expert is known for are represented
- [ ] Sources from at least 3 time periods are included
- [ ] Both recommendations and anti-patterns are captured
- [ ] Best-known frameworks are present
- [ ] Less-known but deeper frameworks are also present
- [ ] Both polished and unpolished sources were reviewed

### 2. Depth Check
For each major framework:
- [ ] It is actionable
- [ ] It includes use conditions
- [ ] It includes non-use conditions
- [ ] It includes at least one example
- [ ] Anti-patterns or misuse cases are documented

### 3. Accuracy Check
- [ ] Every framework has a source citation
- [ ] Inferences are labeled
- [ ] No unsupported claims are attributed to the expert
- [ ] Interpretations are clearly separated from stated views

### 4. Novelty Check
- [ ] NOVEL items are identified
- [ ] ADDITIVE items are linked to existing knowledge
- [ ] CONTRADICTORY items are documented with resolution conditions
- [ ] Hidden curriculum is identified
- [ ] The expert's unique contribution is clearly stated

### 5. Utility Check
- [ ] A team member unfamiliar with the expert could use the docs
- [ ] AI prompts produce usable outputs
- [ ] Decision trees cover common use cases
- [ ] Checklists are usable in execution

## Output Format:

# Quality Report: {expert_name}

## Overall Score: [X/5 gates passed]

### Gate 1: Coverage — [PASS/FAIL]
[Evidence and specific gaps]

### Gate 2: Depth — [PASS/FAIL]
[Evidence and specific gaps]

### Gate 3: Accuracy — [PASS/FAIL]
[Evidence and specific gaps]

### Gate 4: Novelty — [PASS/FAIL]
[Evidence and specific gaps]

### Gate 5: Utility — [PASS/FAIL]
[Evidence and specific gaps]

## Recommended Actions
[Specific steps to address any failures]"""


# ---------------------------------------------------------------------------
# Transcription prompt (for Gemini audio fallback)
# ---------------------------------------------------------------------------

TRANSCRIPTION_PROMPT = """Transcribe the following audio content accurately.

Rules:
1. Transcribe everything spoken, including filler words
2. Use proper punctuation and paragraph breaks
3. If multiple speakers, label them (Speaker 1, Speaker 2, etc.)
4. Include approximate timestamps every few minutes in [MM:SS] format
5. Note any unclear audio as [inaudible]
6. Do not summarize — transcribe verbatim

Output the full transcript as clean text with paragraph breaks."""
