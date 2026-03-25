"""
Taste Rule: CTA Clarity (TS-05)

Scores the end-of-content call-to-action for specificity and urgency.
No clear CTA = no conversion.

Checks:
- Does the content end with an actionable CTA?
- Is the CTA specific (not "learn more" or "contact us")?
- Does it include urgency or value proposition?
"""

import re

from scripts.quality.parser import Document
from scripts.quality.rules.base import BaseRule
from scripts.quality.rules import register
from scripts.quality.types import Category, RuleResult, Severity, Violation


# Strong CTA patterns
_STRONG_CTA = [
    re.compile(r'\b(start\s+(your|my|a)\s+free\s+trial)\b', re.IGNORECASE),
    re.compile(r'\b(book\s+(a|your)\s+(demo|call|consultation))\b', re.IGNORECASE),
    re.compile(r'\b(get\s+(your|my|the)\s+free)\b', re.IGNORECASE),
    re.compile(r'\b(sign\s+up\s+(now|today|free))\b', re.IGNORECASE),
    re.compile(r'\b(try\s+it\s+(free|now|today))\b', re.IGNORECASE),
    re.compile(r'\b(download\s+(your|the|our)\s+free)\b', re.IGNORECASE),
    re.compile(r'\b(claim\s+your)\b', re.IGNORECASE),
    re.compile(r'\b(schedule\s+(a|your))\b', re.IGNORECASE),
    re.compile(r'\b(join\s+\d+\+?\s+\w+)\b', re.IGNORECASE),  # "Join 500+ law firms"
]

# Weak CTA patterns (generic, low-urgency)
_WEAK_CTA = [
    re.compile(r'\b(learn\s+more)\b', re.IGNORECASE),
    re.compile(r'\b(contact\s+us)\b', re.IGNORECASE),
    re.compile(r'\b(click\s+here)\b', re.IGNORECASE),
    re.compile(r'\b(visit\s+our\s+website)\b', re.IGNORECASE),
    re.compile(r'\b(for\s+more\s+information)\b', re.IGNORECASE),
    re.compile(r'\b(reach\s+out)\b', re.IGNORECASE),
    re.compile(r'\b(get\s+in\s+touch)\b', re.IGNORECASE),
]

# Urgency boosters in CTA
_URGENCY_CTA = [
    re.compile(r'\b(now|today|this\s+week|limited|only\s+\d+|before|deadline)\b', re.IGNORECASE),
    re.compile(r'\b(free|no\s+credit\s+card|no\s+risk|cancel\s+anytime)\b', re.IGNORECASE),
    re.compile(r'\b(guarantee|money.?back)\b', re.IGNORECASE),
]


@register
class CTAClarity(BaseRule):
    """Score the call-to-action for specificity, urgency, and placement."""

    RULE_ID = "TS-05"
    RULE_NAME = "CTA clarity"
    CATEGORY = Category.TASTE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Content should end with a specific, urgent CTA. 'Learn more' is not a CTA."

    def evaluate(self, doc: Document) -> RuleResult:
        violations = []

        if not doc.all_sentences:
            return self._make_result(score=0.3, violations=[], suggestions=["No content to evaluate"])

        # Check the last 20% of content for CTA
        total = len(doc.all_sentences)
        tail_start = max(0, total - max(total // 5, 3))
        tail_sentences = doc.all_sentences[tail_start:]
        tail_text = " ".join(s.text for s in tail_sentences)

        # Also check full content for any CTA
        full_text = "\n".join(doc.raw_lines)

        # Score components
        has_strong_cta = any(p.search(tail_text) for p in _STRONG_CTA)
        has_weak_cta = any(p.search(tail_text) for p in _WEAK_CTA)
        has_urgency = any(p.search(tail_text) for p in _URGENCY_CTA)
        has_any_cta_in_body = any(p.search(full_text) for p in _STRONG_CTA + _WEAK_CTA)

        # Scoring
        if has_strong_cta and has_urgency:
            score = 1.0  # Perfect: specific CTA + urgency at end
        elif has_strong_cta:
            score = 0.85  # Good: specific CTA at end, no urgency
        elif has_weak_cta and has_urgency:
            score = 0.6  # Meh: generic CTA but with urgency
        elif has_weak_cta:
            score = 0.4  # Weak: generic CTA, no urgency
            violations.append(Violation(
                line=tail_sentences[-1].line if tail_sentences else total,
                text="Weak CTA detected",
                fix="Replace generic CTA ('learn more', 'contact us') with specific action ('Start your free trial', 'Book a demo today')",
                context=tail_text[-80:],
            ))
        elif has_any_cta_in_body:
            score = 0.3  # CTA exists but not at the end
            violations.append(Violation(
                line=tail_sentences[-1].line if tail_sentences else total,
                text="No CTA at end of content",
                fix="Add a clear CTA to the final paragraph — the end is where action happens",
                context="CTA found in body but not in closing section",
            ))
        else:
            score = 0.1  # No CTA at all
            violations.append(Violation(
                line=tail_sentences[-1].line if tail_sentences else total,
                text="No CTA found anywhere in content",
                fix="Every piece of content needs a clear next step for the reader",
                context="Add: 'Start your free trial', 'Book a demo', 'Download the guide'",
            ))

        return self._make_result(
            score=score,
            violations=violations,
            suggestions=[
                "Strong CTAs: 'Start my free trial', 'Book a demo today', 'Join 500+ law firms'",
                "Weak CTAs: 'Learn more', 'Contact us', 'Click here' — too generic to convert",
                "Best: Specific action + urgency + risk reversal ('Try free for 14 days — no card required')",
            ] if score < 0.7 else [],
            metadata={"has_strong_cta": has_strong_cta, "has_weak_cta": has_weak_cta, "has_urgency": has_urgency},
        )
