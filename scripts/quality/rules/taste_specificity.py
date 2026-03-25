"""
Taste Rule: Specificity Density (TS-01)

Scores what % of claims are backed by numbers, named entities, or concrete examples.
Vague content = generic content = no edge.

Checks for:
- Numbers (stats, percentages, dollar amounts, timeframes)
- Named entities (company names, product names, person names)
- Concrete examples vs abstract statements
"""

import re

from scripts.quality.parser import Document
from scripts.quality.rules.base import BaseRule
from scripts.quality.rules import register
from scripts.quality.types import Category, RuleResult, Severity, Violation


# Patterns that indicate specificity
_NUMBER_PATTERN = re.compile(
    r'\b\d+[\d,.]*\s*(%|percent|dollars?|\$|hours?|minutes?|seconds?|days?|weeks?|months?|years?|x|times|users?|customers?|clients?|calls?|leads?)\b',
    re.IGNORECASE,
)
_DOLLAR_PATTERN = re.compile(r'\$\d[\d,.]*')
_PERCENTAGE_PATTERN = re.compile(r'\b\d+(\.\d+)?%')
_TIMEFRAME_PATTERN = re.compile(r'\b(in|within|under|after)\s+\d+\s+(seconds?|minutes?|hours?|days?|weeks?|months?)\b', re.IGNORECASE)

# Patterns that indicate vagueness
_VAGUE_PATTERNS = [
    re.compile(r'\b(many|several|various|numerous|a lot of|tons of|plenty of)\b', re.IGNORECASE),
    re.compile(r'\b(significantly|substantially|dramatically|greatly|tremendously)\b', re.IGNORECASE),
    re.compile(r'\b(good|better|best|great|amazing|wonderful|excellent)\b', re.IGNORECASE),
    re.compile(r'\b(helps? you|allows? you to|enables? you to|lets? you)\b', re.IGNORECASE),
    re.compile(r'\b(easy|simple|seamless|effortless|intuitive)\b', re.IGNORECASE),
]


@register
class SpecificityDensity(BaseRule):
    """Score the density of specific, concrete claims vs vague ones."""

    RULE_ID = "TS-01"
    RULE_NAME = "Specificity density"
    CATEGORY = Category.TASTE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Content should be specific — numbers, names, examples. Vague claims erode trust."

    def evaluate(self, doc: Document) -> RuleResult:
        violations = []
        total_sentences = max(len(doc.all_sentences), 1)
        specific_count = 0
        vague_count = 0

        for sent in doc.all_sentences:
            text = sent.text

            # Check for specificity signals
            has_number = bool(_NUMBER_PATTERN.search(text) or _DOLLAR_PATTERN.search(text) or _PERCENTAGE_PATTERN.search(text))
            has_timeframe = bool(_TIMEFRAME_PATTERN.search(text))

            if has_number or has_timeframe:
                specific_count += 1

            # Check for vagueness signals
            for vp in _VAGUE_PATTERNS:
                if vp.search(text):
                    vague_count += 1
                    if not has_number:  # Only flag if not redeemed by a number
                        violations.append(Violation(
                            line=sent.line,
                            text=vp.search(text).group(0),
                            fix=f"Replace vague language with a specific number, name, or example",
                            context=text[:80],
                        ))
                    break

        # Score: ratio of specific sentences to total, penalized by vague sentences
        specificity_ratio = specific_count / total_sentences
        vagueness_penalty = min(vague_count / total_sentences * 2, 0.5)  # max 50% penalty

        # Target: at least 20% of sentences should have specificity signals
        score = min(1.0, specificity_ratio / 0.20) - vagueness_penalty
        score = max(0.0, min(1.0, score))

        return self._make_result(
            score=score,
            violations=violations[:10],  # Cap at 10 most impactful
            suggestions=[
                f"Specificity: {specific_count}/{total_sentences} sentences have numbers/names ({specificity_ratio:.0%})",
                f"Vagueness: {vague_count} vague qualifiers found",
                "Replace adjectives with data: 'fast' → '0.4 seconds', 'many' → '500+'",
            ] if score < 0.8 else [],
            metadata={"specific_count": specific_count, "vague_count": vague_count, "total_sentences": total_sentences},
        )
