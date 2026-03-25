"""
Taste Rule: Emotional Resonance (TS-02)

Scores pain/aspiration language density matched to persona context.
Content that doesn't trigger emotion doesn't convert.

Checks for emotional language in the right proportions:
- Pain language (frustration, fear of loss, stuck)
- Aspiration language (freedom, control, growth, success)
- Urgency language (now, today, before, deadline)
"""

import re

from scripts.quality.parser import Document
from scripts.quality.rules.base import BaseRule
from scripts.quality.rules import register
from scripts.quality.types import Category, RuleResult, Severity, Violation


# Emotional language patterns
_PAIN_PATTERNS = re.compile(
    r'\b(frustrated?|struggling?|losing|missed|failing|broken|overwhelmed|'
    r'stuck|wasted?|costly?|expensive|painful|annoying|nightmare|chaos|'
    r'behind|falling|drowning|burned out|exhausted|desperate)\b',
    re.IGNORECASE,
)

_ASPIRATION_PATTERNS = re.compile(
    r'\b(freedom|control|confident|thriving|growing|scaling|winning|'
    r'effortless|automated|peaceful|protected|secure|saved|earned|'
    r'doubled|tripled|transformed|unlocked|achieved|mastered)\b',
    re.IGNORECASE,
)

_URGENCY_PATTERNS = re.compile(
    r'\b(now|today|immediately|before|deadline|while|still|running out|'
    r'limited|last chance|don\'t wait|time.?sensitive|soon|this week|this month)\b',
    re.IGNORECASE,
)

# Emotionally flat patterns (clinical/passive/detached)
_FLAT_PATTERNS = re.compile(
    r'\b(functionality|implementation|utilization|methodology|'
    r'facilitate|regarding|pertaining|aforementioned|'
    r'it should be noted|it is important|one might consider)\b',
    re.IGNORECASE,
)


@register
class EmotionalResonance(BaseRule):
    """Score emotional language density — content must trigger feeling, not just inform."""

    RULE_ID = "TS-02"
    RULE_NAME = "Emotional resonance"
    CATEGORY = Category.TASTE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Content should trigger emotion (pain, aspiration, urgency). Flat, clinical content doesn't convert."

    def evaluate(self, doc: Document) -> RuleResult:
        violations = []
        full_text = "\n".join(doc.raw_lines)
        total_words = doc.word_count or 1

        pain_hits = len(_PAIN_PATTERNS.findall(full_text))
        aspiration_hits = len(_ASPIRATION_PATTERNS.findall(full_text))
        urgency_hits = len(_URGENCY_PATTERNS.findall(full_text))
        flat_hits = len(_FLAT_PATTERNS.findall(full_text))

        emotional_total = pain_hits + aspiration_hits + urgency_hits
        emotional_density = emotional_total / (total_words / 100)  # per 100 words

        # Target: 2-5 emotional words per 100 words
        # Below 1 = too flat. Above 8 = overwrought.
        if emotional_density < 1.0:
            score_base = emotional_density / 1.0 * 0.5  # 0 to 0.5
        elif emotional_density <= 5.0:
            score_base = 0.5 + (emotional_density - 1.0) / 4.0 * 0.5  # 0.5 to 1.0
        else:
            score_base = max(0.6, 1.0 - (emotional_density - 5.0) / 5.0 * 0.4)  # decrease gently

        # Penalty for flat/clinical language
        flat_penalty = min(flat_hits / (total_words / 100) * 0.15, 0.3)

        # Balance bonus: content with both pain AND aspiration scores higher
        balance_bonus = 0.1 if (pain_hits > 0 and aspiration_hits > 0) else 0

        score = max(0.0, min(1.0, score_base - flat_penalty + balance_bonus))

        if emotional_density < 1.0:
            violations.append(Violation(
                line=1,
                text=f"Emotional density: {emotional_density:.1f} per 100 words (target: 2-5)",
                fix="Add pain points, aspirational outcomes, or urgency triggers",
                context="Content reads as informational rather than persuasive",
            ))

        if flat_hits > 3:
            # Find first flat hit for context
            for i, line in enumerate(doc.raw_lines, 1):
                match = _FLAT_PATTERNS.search(line)
                if match:
                    violations.append(Violation(
                        line=i,
                        text=match.group(0),
                        fix="Replace clinical/passive language with active, emotional alternatives",
                        context=line.strip()[:80],
                    ))
                    break

        return self._make_result(
            score=score,
            violations=violations,
            suggestions=[
                f"Pain words: {pain_hits} | Aspiration: {aspiration_hits} | Urgency: {urgency_hits}",
                f"Emotional density: {emotional_density:.1f}/100 words (target: 2-5)",
                f"Flat/clinical language: {flat_hits} instances",
            ] if score < 0.7 else [],
            metadata={
                "pain": pain_hits, "aspiration": aspiration_hits, "urgency": urgency_hits,
                "flat": flat_hits, "density": round(emotional_density, 2),
            },
        )
