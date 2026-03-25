"""
Taste Rule: Hook Strength (TS-04)

Scores the first sentence/paragraph for impact.
A strong hook has: specificity + pattern interrupt + relevance.
A weak hook starts with generic setup or throat-clearing.

First line determines if anyone reads the rest.
"""

import re

from scripts.quality.parser import Document
from scripts.quality.rules.base import BaseRule
from scripts.quality.rules import register
from scripts.quality.types import Category, RuleResult, Severity, Violation


# Weak hook patterns (throat-clearing, setup, generic openings)
_WEAK_HOOKS = [
    re.compile(r'^in\s+this\s+(article|post|guide|piece)', re.IGNORECASE),
    re.compile(r'^(today|in\s+this\s+article),?\s+(we|i)\s+(will|are going to|\'ll)', re.IGNORECASE),
    re.compile(r'^(welcome|hello|hi|hey)\s', re.IGNORECASE),
    re.compile(r'^(if\s+you\'re\s+like\s+most|like\s+many)', re.IGNORECASE),
    re.compile(r'^(have\s+you\s+ever\s+wondered|did\s+you\s+know)', re.IGNORECASE),
    re.compile(r'^(it\'?s\s+no\s+secret|we\s+all\s+know|as\s+we\s+all\s+know)', re.IGNORECASE),
    re.compile(r'^(in\s+today\'?s\s+(world|age|landscape|market))', re.IGNORECASE),
    re.compile(r'^(marketing|business|technology)\s+is\s+(changing|evolving|growing)', re.IGNORECASE),
    re.compile(r'^(are\s+you\s+tired|do\s+you\s+struggle)', re.IGNORECASE),  # lazy Q format
    re.compile(r'^(introduction|overview|background)\s*:', re.IGNORECASE),
]

# Strong hook signals
_STRONG_SIGNALS = [
    re.compile(r'^\$?\d'),                          # Starts with a number/stat
    re.compile(r'^"[^"]+?"'),                        # Starts with a quote
    re.compile(r'^[A-Z][a-z]+\s+(didn\'t|couldn\'t|wouldn\'t|never|lost|failed)', re.IGNORECASE),  # Named entity + action
    re.compile(r'\b(wrong|mistake|myth|lie|truth|secret|hidden)\b', re.IGNORECASE),  # Pattern interrupt words
    re.compile(r'\b\d+(%|\s*percent)\b'),            # Contains percentage
    re.compile(r'\$\d'),                              # Contains dollar amount
]


@register
class HookStrength(BaseRule):
    """Score the opening hook for impact and specificity."""

    RULE_ID = "TS-04"
    RULE_NAME = "Hook strength"
    CATEGORY = Category.TASTE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "First sentence must grab attention — specific, surprising, or pattern-interrupting."

    def evaluate(self, doc: Document) -> RuleResult:
        violations = []

        if not doc.all_sentences:
            return self._make_result(score=0.5, violations=[], suggestions=["No sentences found"])

        # Get first 1-3 sentences (the hook zone)
        hook_sentences = doc.all_sentences[:3]
        first_sentence = hook_sentences[0].text.strip()

        # Skip markdown headings to find actual first content sentence
        for sent in doc.all_sentences:
            if not sent.text.strip().startswith('#'):
                first_sentence = sent.text.strip()
                hook_sentences = doc.all_sentences[doc.all_sentences.index(sent):doc.all_sentences.index(sent) + 3]
                break

        hook_text = " ".join(s.text for s in hook_sentences)

        # Check for weak hooks
        weak_score = 0
        for pattern in _WEAK_HOOKS:
            if pattern.search(first_sentence):
                weak_score += 1
                violations.append(Violation(
                    line=hook_sentences[0].line if hook_sentences else 1,
                    text=pattern.search(first_sentence).group(0),
                    fix="Replace generic opening with a specific stat, bold claim, or named example",
                    context=first_sentence[:80],
                ))

        # Check for strong signals
        strong_score = 0
        for pattern in _STRONG_SIGNALS:
            if pattern.search(hook_text):
                strong_score += 1

        # Check hook length (short hooks are punchier)
        first_words = len(first_sentence.split())
        length_bonus = 0.1 if first_words <= 15 else 0 if first_words <= 25 else -0.1

        # Score: strong signals boost, weak patterns penalize
        base_score = 0.5
        score = base_score + (strong_score * 0.15) - (weak_score * 0.25) + length_bonus
        score = max(0.0, min(1.0, score))

        return self._make_result(
            score=score,
            violations=violations,
            suggestions=[
                "Strong hooks start with: a number, a name, a bold claim, or a contradiction",
                f"Your hook: \"{first_sentence[:60]}...\"" if len(first_sentence) > 60 else f"Your hook: \"{first_sentence}\"",
                f"Hook signals: {strong_score} strong, {weak_score} weak",
            ] if score < 0.7 else [],
            metadata={"strong_signals": strong_score, "weak_signals": weak_score, "first_sentence_words": first_words},
        )
