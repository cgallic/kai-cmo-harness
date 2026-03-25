"""
Specificity Scorer — Count specific vs vague claims in text.

Reusable component extracted from taste_specificity quality rule.
Can be used independently of the quality gate pipeline.

Usage:
    result = score_specificity("We helped 500+ law firms save 12 hours per week")
    # result = {"specific": 2, "vague": 0, "ratio": 1.0}
"""

import re


_NUMBER_PATTERNS = [
    re.compile(r'\b\d+[\d,.]*\s*(%|percent|dollars?|\$|hours?|minutes?|seconds?|days?|weeks?|months?|years?|x|times)', re.IGNORECASE),
    re.compile(r'\$\d[\d,.]*'),
    re.compile(r'\b\d+(\.\d+)?%'),
]

_VAGUE_PATTERNS = [
    re.compile(r'\b(many|several|various|numerous|a lot of|tons of)\b', re.IGNORECASE),
    re.compile(r'\b(significantly|substantially|dramatically|greatly)\b', re.IGNORECASE),
    re.compile(r'\b(good|better|best|great|amazing|wonderful|excellent)\b', re.IGNORECASE),
    re.compile(r'\b(easy|simple|seamless|effortless|intuitive)\b', re.IGNORECASE),
]


def score_specificity(text: str) -> dict:
    """Score text for specificity. Returns counts and ratio."""
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    specific = 0
    vague = 0

    for sent in sentences:
        is_specific = any(p.search(sent) for p in _NUMBER_PATTERNS)
        is_vague = any(p.search(sent) for p in _VAGUE_PATTERNS)

        if is_specific:
            specific += 1
        if is_vague and not is_specific:
            vague += 1

    total = max(len(sentences), 1)
    return {
        "specific": specific,
        "vague": vague,
        "total_sentences": total,
        "ratio": specific / total,
        "score": max(0.0, min(1.0, (specific / total) / 0.20 - vague / total * 2)),
    }


def find_vague_phrases(text: str) -> list[dict]:
    """Find all vague phrases in text with line numbers and suggestions."""
    results = []
    for i, line in enumerate(text.splitlines(), 1):
        for pattern in _VAGUE_PATTERNS:
            match = pattern.search(line)
            if match:
                results.append({
                    "line": i,
                    "phrase": match.group(0),
                    "context": line.strip()[:80],
                    "fix": "Replace with a specific number, name, or example",
                })
    return results
