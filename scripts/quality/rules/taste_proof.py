"""
Taste Rule: Proof Density (TS-06)

Scores named proof points per 500 words.
Claims without proof = trust erosion.

Checks for: named case studies, specific statistics, testimonial markers,
named tools/companies, and cited sources.
"""

import re

from scripts.quality.parser import Document
from scripts.quality.rules.base import BaseRule
from scripts.quality.rules import register
from scripts.quality.types import Category, RuleResult, Severity, Violation


# Proof point patterns
_PROOF_PATTERNS = {
    "statistic": re.compile(r'\b\d+(\.\d+)?(%|\s*percent)\b'),
    "dollar_amount": re.compile(r'\$\d[\d,.]+'),
    "named_entity": re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'),  # Capitalized multi-word (company/person names)
    "citation": re.compile(r'\b(according to|per|based on|source:|study|research|report|survey)\b', re.IGNORECASE),
    "testimonial": re.compile(r'["""\u201c\u201d].{20,}["""\u201c\u201d]'),  # Quoted text 20+ chars
    "case_study": re.compile(r'\b(case study|success story|how\s+\w+\s+(uses?|saves?|grew|achieved))\b', re.IGNORECASE),
    "specific_result": re.compile(r'\b(increased|decreased|reduced|improved|grew|saved)\s+\w*\s*by\s+\d', re.IGNORECASE),
    "timeframe_result": re.compile(r'\b(in|within|after)\s+\d+\s+(days?|weeks?|months?|hours?)\b', re.IGNORECASE),
}


@register
class ProofDensity(BaseRule):
    """Score the density of named proof points (evidence backing claims)."""

    RULE_ID = "TS-06"
    RULE_NAME = "Proof density"
    CATEGORY = Category.TASTE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Every major claim needs proof — stats, names, examples, citations. Claims without proof erode trust."

    def evaluate(self, doc: Document) -> RuleResult:
        violations = []
        total_words = doc.word_count or 1
        proof_count = 0
        proof_types_found = set()

        full_text = "\n".join(doc.raw_lines)

        for proof_type, pattern in _PROOF_PATTERNS.items():
            matches = pattern.findall(full_text)
            if matches:
                proof_count += len(matches)
                proof_types_found.add(proof_type)

        # Target: 1 proof point per 200 words (5 per 1000 words)
        expected_proofs = max(1, total_words // 200)
        proof_ratio = proof_count / expected_proofs

        # Diversity bonus: more types of proof = more credible
        diversity_bonus = min(len(proof_types_found) * 0.05, 0.2)

        score = min(1.0, proof_ratio * 0.8 + diversity_bonus)
        score = max(0.0, score)

        # Flag sections with no proof
        if proof_count < expected_proofs:
            violations.append(Violation(
                line=1,
                text=f"{proof_count} proof points found, expected {expected_proofs}+",
                fix="Add specific stats, named examples, or citations to support claims",
                context=f"Word count: {total_words}, proof density: {proof_count}/{expected_proofs}",
            ))

        missing_types = {"statistic", "named_entity", "specific_result"} - proof_types_found
        if missing_types:
            violations.append(Violation(
                line=1,
                text=f"Missing proof types: {', '.join(missing_types)}",
                fix="Add at least one statistic, one named entity, and one specific result",
                context="Diverse proof builds more trust than one type repeated",
            ))

        return self._make_result(
            score=score,
            violations=violations,
            suggestions=[
                f"Proof points: {proof_count} found (target: {expected_proofs}+)",
                f"Proof types: {', '.join(sorted(proof_types_found)) or 'none'}",
                "Add: specific percentages, named companies, dollar amounts, timeframed results",
            ] if score < 0.8 else [],
            metadata={"proof_count": proof_count, "expected": expected_proofs, "types": list(proof_types_found)},
        )
