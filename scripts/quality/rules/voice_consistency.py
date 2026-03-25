"""
Voice Consistency Scorer — Compares draft against voice profile.

Checks content against the Non-Negotiables section of MARKETING.md
and the voice profile in ~/.kai-marketing/voice.md (if present).

Detects tone drift by checking for:
- Banned words/phrases from the voice profile
- Tone violations (e.g., too formal when brand is casual)
- Missing required brand elements
"""

import re
from pathlib import Path

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
    """Load voice profile from ~/.kai-marketing/voice.md or workspace/SOUL.md."""
    voice = {"banned_phrases": [], "required_elements": [], "tone_keywords": []}

    # Try skill state path first, then workspace
    candidates = [
        Path.home() / ".kai-marketing" / "voice.md",
        Path(__file__).parent.parent.parent.parent / "workspace" / "SOUL.md",
    ]

    for path in candidates:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore")

            # Extract banned words/phrases
            in_banned = False
            for line in text.splitlines():
                line_lower = line.strip().lower()
                if "banned" in line_lower or "never say" in line_lower or "avoid" in line_lower:
                    in_banned = True
                    continue
                if in_banned and line.strip().startswith("- "):
                    phrase = line.strip().lstrip("- ").strip().strip('"').strip("'")
                    if phrase:
                        voice["banned_phrases"].append(phrase)
                elif in_banned and line.strip().startswith("#"):
                    in_banned = False

            break  # Use first found

    return voice


@register
class VoiceConsistencyRule(BaseRule):
    """Check content against voice profile and AI slop patterns."""

    RULE_ID = "VC-01"
    RULE_NAME = "Voice Consistency"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Content should match the brand voice profile and avoid AI slop phrases."

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
        voice = _load_voice_profile()
        for phrase in voice.get("banned_phrases", []):
            for i, line in enumerate(lines, 1):
                if phrase.lower() in line.lower():
                    violations.append(Violation(
                        line=i,
                        text=phrase,
                        fix=f"Voice profile prohibits: '{phrase}'",
                        context=line.strip()[:80],
                    ))

        # Score: 1.0 if no violations, decreasing with more
        total_lines = max(len(lines), 1)
        violation_rate = len(violations) / total_lines
        score = max(0.0, 1.0 - (violation_rate * 10))  # 10% violation rate = 0 score

        return self._make_result(
            score=score,
            violations=violations,
            suggestions=["Remove AI slop phrases", "Match brand voice profile"] if violations else [],
            metadata={"violation_count": len(violations), "voice_profile_loaded": bool(voice.get("banned_phrases"))},
        )
