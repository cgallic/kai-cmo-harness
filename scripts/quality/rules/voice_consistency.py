"""
Voice consistency checks using an explicitly supplied customer profile.
No home-directory or global workspace voice is implicitly inherited.
Mechanical constraints complement the separate semantic editorial review.
"""

import re

from scripts.quality.parser import Document
from scripts.quality.rules.base import BaseRule
from scripts.quality.rules import register
from scripts.quality.types import Category, RuleResult, Severity, Violation


# Default voice check patterns (used when no voice profile is loaded)
_DEFAULT_BANNED_PATTERNS = [
    # AI slop phrases
    r"\bin conclusion\b",
    r"\bit'?s important to note\b",
    r"\bin today'?s rapidly evolving\b",
    r"\bthis comprehensive guide\b",
    r"\bwithout further ado\b",
    r"\bit'?s worth noting that\b",
    r"\blet'?s dive in\b",
    r"\bin this article,? we will\b",
    r"\bas we all know\b",
    r"\bneedless to say\b",
]


def _load_voice_profile() -> dict:
    """No ambient home-directory profile: callers must supply scoped context."""
    return {"banned_phrases": [], "configured": False}


@register
class VoiceConsistencyRule(BaseRule):
    """Check content against voice profile and AI slop patterns."""

    RULE_ID = "VC-01"
    RULE_NAME = "Voice Consistency"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Content should match the brand voice profile and avoid AI slop phrases."

    def __init__(self, profile=None):
        self.profile = profile or _load_voice_profile()

    def evaluate(self, doc: Document) -> RuleResult:
        violations = []
        lines = doc.raw_lines

        # Check default AI slop patterns
        for pattern in _DEFAULT_BANNED_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    match = re.search(pattern, line, re.IGNORECASE)
                    violations.append(Violation(
                        line=i,
                        text=match.group(0) if match else "",
                        fix=f"Remove AI slop phrase: '{match.group(0) if match else ''}'",
                        context=line.strip()[:80],
                    ))

        # Check voice profile banned phrases
        voice = self.profile
        from scripts.quality_gates.voice_phrase_check import check_content
        for hit in check_content("\n".join(lines), voice)["violations"]:
            violations.append(Violation(
                line=hit["line"], text=hit["text"],
                fix=f"Voice profile prohibits: '{hit['text']}'",
                context=lines[hit["line"] - 1].strip()[:80],
            ))

        # Score: 1.0 if no violations, decreasing with more
        total_lines = max(len(lines), 1)
        violation_rate = len(violations) / total_lines
        score = max(0.0, 1.0 - (violation_rate * 10))  # 10% violation rate = 0 score

        return self._make_result(
            score=score,
            violations=violations,
            suggestions=["Remove AI slop phrases", "Match brand voice profile"] if violations else [],
            metadata={"violation_count": len(violations), "voice_profile_loaded": bool(voice.get("configured")), "voice_version": voice.get("version"), "brand": voice.get("brand")},
        )
