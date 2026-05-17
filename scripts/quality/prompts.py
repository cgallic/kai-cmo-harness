"""
Content Quality Scorer — LLM prompt templates.
"""

FOUR_US_PROMPT = """You are a calibrated content quality evaluator. Score this content on the Four U's framework.

Your job is not to reward polish. Your job is to separate useful, source-grounded specificity from generic copy that only sounds specific.

## Four U's Rubric

### Unique (1-4)
1 = Generic, could be written by anyone. "Top 10 tips" content.
2 = Some original framing but mostly conventional wisdom.
3 = Original angle, unique data or perspective, specific case study.
4 = Only THIS author could write this. Proprietary data, first-hand experience, named customer/process details, or contrarian take with evidence.

### Useful (1-4)
1 = No actionable takeaways. Pure opinion or theory.
2 = Some advice but vague ("improve your SEO").
3 = Clear action steps the reader can implement today.
4 = Complete playbook with specific tools, decisions, templates, and failure modes. Reader can execute immediately.

### Ultra-specific (1-4)
1 = All generalities, no numbers or examples.
2 = A few examples but mostly abstract.
3 = Specific numbers, named tools, source-grounded examples throughout.
4 = Material claims are backed by visible sources or first-party evidence. Named companies, dollar amounts, percentages, dates, constraints, and timelines are credible and relevant.

### Urgent (1-4)
1 = No reason to read now vs. next month.
2 = Mild timeliness ("trends are changing").
3 = Clear time-sensitivity: deadline, algorithm change, market window.
4 = Act-now framing with specific consequences of delay.

## Calibration rules

- Start from 2/4 for each dimension. Move up only when the content proves it.
- A 4 is rare. Give 4 only when the evidence would survive a skeptical editor.
- Do not reward a number, date, quote, ranking, percentage, or named entity just because it appears. Reward it only if the surrounding text shows a source, method, first-party observation, or plausible context.
- Penalize fake specificity: precise numbers without a source, vague "research shows" claims, unverifiable expert quotes, future-dated claims, impossible certainty, or named companies used as decoration.
- Penalize source laundering: a citation label that does not actually support the sentence, a famous source invoked without a linked/report context, or an "according to" claim with no traceable source.
- Separate confidence from score. If the content is too short, truncated, or undersourced, lower confidence even when the writing is strong.
- Use the pre-computed signal counts as clues, not proof.

## Source-grounding guide

- grounded = the dimension's key claims are tied to visible URLs, named reports, documented first-party data, or reproducible methods.
- partly_grounded = some claims are supported, but important claims rely on assertion.
- unsupported = specific claims appear without enough source context.
- not_applicable = no factual or quantitative claims are needed for this dimension.

## Fake-specificity guide

Mark fake_specificity true when the piece uses details that look precise but are not supportable from the text itself: unsourced percentages, fabricated-sounding quotes, future algorithm updates, exact performance lifts without a named dataset, or authority names used without a traceable citation.

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
        "suggestion": "<how to improve, if score < 4>",
        "confidence": "high | medium | low",
        "source_grounding": "grounded | partly_grounded | unsupported | not_applicable",
        "fake_specificity": true | false
    }},
    "useful": {{
        "score": <1-4>,
        "evidence": "<specific quote or pattern>",
        "suggestion": "<how to improve>",
        "confidence": "high | medium | low",
        "source_grounding": "grounded | partly_grounded | unsupported | not_applicable",
        "fake_specificity": true | false
    }},
    "ultra_specific": {{
        "score": <1-4>,
        "evidence": "<specific quote or pattern>",
        "suggestion": "<how to improve>",
        "confidence": "high | medium | low",
        "source_grounding": "grounded | partly_grounded | unsupported | not_applicable",
        "fake_specificity": true | false
    }},
    "urgent": {{
        "score": <1-4>,
        "evidence": "<specific quote or pattern>",
        "suggestion": "<how to improve>",
        "confidence": "high | medium | low",
        "source_grounding": "grounded | partly_grounded | unsupported | not_applicable",
        "fake_specificity": true | false
    }}
}}"""
