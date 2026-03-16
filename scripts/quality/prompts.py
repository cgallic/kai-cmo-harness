"""
Content Quality Scorer — LLM prompt templates.
"""

FOUR_US_PROMPT = """You are a content quality evaluator. Score this content on the Four U's framework.

## Four U's Rubric

### Unique (1-4)
1 = Generic, could be written by anyone. "Top 10 tips" content.
2 = Some original framing but mostly conventional wisdom.
3 = Original angle, unique data or perspective, specific case study.
4 = Only THIS author could write this. Proprietary data, first-hand experience, contrarian take with evidence.

### Useful (1-4)
1 = No actionable takeaways. Pure opinion or theory.
2 = Some advice but vague ("improve your SEO").
3 = Clear action steps the reader can implement today.
4 = Complete playbook with specific tools, numbers, templates. Reader can execute immediately.

### Ultra-specific (1-4)
1 = All generalities, no numbers or examples.
2 = A few examples but mostly abstract.
3 = Specific numbers, named tools, real examples throughout.
4 = Every claim backed by data. Named companies, dollar amounts, percentages, timelines.

### Urgent (1-4)
1 = No reason to read now vs. next month.
2 = Mild timeliness ("trends are changing").
3 = Clear time-sensitivity: deadline, algorithm change, market window.
4 = Act-now framing with specific consequences of delay.

## Pre-computed signals (use as context)
- Statistics found: {stat_count}
- Citations found: {citation_count}
- Word count: {word_count}

## Content to evaluate:
---
{content}
---

Return ONLY valid JSON (no markdown code fences):
{{
    "unique": {{
        "score": <1-4>,
        "evidence": "<specific quote or pattern that justifies this score>",
        "suggestion": "<how to improve, if score < 4>"
    }},
    "useful": {{
        "score": <1-4>,
        "evidence": "<specific quote or pattern>",
        "suggestion": "<how to improve>"
    }},
    "ultra_specific": {{
        "score": <1-4>,
        "evidence": "<specific quote or pattern>",
        "suggestion": "<how to improve>"
    }},
    "urgent": {{
        "score": <1-4>,
        "evidence": "<specific quote or pattern>",
        "suggestion": "<how to improve>"
    }}
}}"""
