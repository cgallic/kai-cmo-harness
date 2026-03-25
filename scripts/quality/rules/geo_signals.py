"""
Content Quality Scorer — GEO/AEO signal counting rules.

Based on academic research showing visibility boosts:
- Citations: +115%
- Quotations: +40%
- Statistics: +37%
- Technical terms: +32.7%
"""

import re

from scripts.quality.parser import Document
from scripts.quality.types import Category, Severity, Violation
from scripts.quality.config import GEO_TARGETS, GEO_BOOSTS, get_geo_targets
from scripts.quality.rules import register
from scripts.quality.rules.base import BaseRule


@register
class CitationCount(BaseRule):
    """GEO-01: Inline citations boost AI search visibility by +115%."""
    RULE_ID = "GEO-01"
    RULE_NAME = "Citation density"
    CATEGORY = Category.GEO_SIGNALS
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Content should include 5+ citations per article for +115% AI search visibility"

    _PATTERNS = [
        re.compile(r'according to\s', re.IGNORECASE),
        re.compile(r'(?:cited|reported|published|found|noted|stated) by\s', re.IGNORECASE),
        re.compile(r'per\s+[A-Z][a-z]+', re.IGNORECASE),
        re.compile(r'(?:research|study|survey|report|data|analysis) (?:from|by|at)\s', re.IGNORECASE),
        re.compile(r'\b(?:Harvard|MIT|Stanford|Google|Microsoft|McKinsey|Gartner|Forrester|HubSpot|Semrush)\b'),
        re.compile(r'\(\d{4}\)'),  # Year in parentheses: (2024)
        re.compile(r'(?:et al\.|doi:|ISSN|ISBN)'),
    ]

    def evaluate(self, doc):
        citations = []
        for s in doc.all_sentences:
            for pattern in self._PATTERNS:
                if pattern.search(s.text):
                    citations.append(s)
                    break

        count = len(citations)
        target = get_geo_targets()["citations"]
        words_k = max(doc.word_count / 1000, 0.5)
        density = count / words_k

        # Score: ratio of actual to target, capped at 1.0
        score = min(count / max(target, 1), 1.0)

        violations = []
        if count < target:
            violations.append(Violation(
                line=0,
                text=f"Found {count} citations (target: {target}+)",
                fix=f'Add {target - count} more inline citations. Each adds {GEO_BOOSTS["citations"]} visibility',
            ))

        return self._make_result(
            score, violations,
            metadata={"count": count, "target": target, "density_per_1k": round(density, 1)},
        )


@register
class QuotationCount(BaseRule):
    """GEO-02: Direct quotations boost AI search visibility by +40%."""
    RULE_ID = "GEO-02"
    RULE_NAME = "Quotation density"
    CATEGORY = Category.GEO_SIGNALS
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Content should include 3+ direct quotations for +40% AI search visibility"

    # Direct quotes >10 chars (not code or attribute values)
    _QUOTE = re.compile(r'["\u201c]([^"\u201d]{10,})["\u201d]')

    def evaluate(self, doc):
        quotes = []
        for s in doc.all_sentences:
            for m in self._QUOTE.finditer(s.text):
                quotes.append((s, m.group(1)))

        count = len(quotes)
        target = get_geo_targets()["quotations"]
        score = min(count / max(target, 1), 1.0)

        violations = []
        if count < target:
            violations.append(Violation(
                line=0,
                text=f"Found {count} quotations (target: {target}+)",
                fix=f'Add {target - count} more expert quotes. Each adds {GEO_BOOSTS["quotations"]} visibility',
            ))

        return self._make_result(
            score, violations,
            metadata={"count": count, "target": target},
        )


@register
class StatisticCount(BaseRule):
    """GEO-03: Statistics boost AI search visibility by +37%."""
    RULE_ID = "GEO-03"
    RULE_NAME = "Statistic density"
    CATEGORY = Category.GEO_SIGNALS
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Content should include 5+ statistics for +37% AI search visibility"

    _PATTERNS = [
        re.compile(r'\d+(?:\.\d+)?%'),               # Percentages: 42%, 3.5%
        re.compile(r'\$[\d,.]+(?:\s*(?:M|B|K|million|billion|thousand))?'),  # Dollar amounts
        re.compile(r'\d+(?:\.\d+)?x\b'),              # Multipliers: 3x, 2.5x
        re.compile(r'\d+(?:,\d{3})+'),                # Large numbers: 1,000,000
        re.compile(r'\d+\s*(?:million|billion|thousand|hundred)', re.IGNORECASE),
        re.compile(r'(?:increased|decreased|grew|fell|rose|dropped|gained)\s+(?:by\s+)?\d+', re.IGNORECASE),
    ]

    def evaluate(self, doc):
        stats = set()
        for s in doc.all_sentences:
            for pattern in self._PATTERNS:
                for m in pattern.finditer(s.text):
                    stats.add((s.line, m.group(0)))

        count = len(stats)
        target = get_geo_targets()["statistics"]
        words_k = max(doc.word_count / 1000, 0.5)
        density = count / words_k

        score = min(count / max(target, 1), 1.0)

        violations = []
        if count < target:
            violations.append(Violation(
                line=0,
                text=f"Found {count} statistics (target: {target}+)",
                fix=f'Add {target - count} more data points. Each adds {GEO_BOOSTS["statistics"]} visibility',
            ))

        return self._make_result(
            score, violations,
            metadata={"count": count, "target": target, "density_per_1k": round(density, 1)},
        )


@register
class TechnicalTermDensity(BaseRule):
    """GEO-04: Technical/domain terms boost visibility by +32.7%."""
    RULE_ID = "GEO-04"
    RULE_NAME = "Technical term density"
    CATEGORY = Category.GEO_SIGNALS
    SEVERITY = Severity.OPPORTUNITY
    DESCRIPTION = "Include domain-specific terminology for +32.7% AI search visibility"

    # Words >10 chars or compound technical terms
    _LONG_WORD = re.compile(r'\b[a-zA-Z]{11,}\b')
    _COMPOUND = re.compile(r'\b[a-z]+-[a-z]+\b')

    def evaluate(self, doc):
        terms = set()
        for s in doc.all_sentences:
            for m in self._LONG_WORD.finditer(s.text):
                terms.add(m.group(0).lower())
            for m in self._COMPOUND.finditer(s.text):
                terms.add(m.group(0).lower())

        count = len(terms)
        target = get_geo_targets()["technical_terms"]
        words_k = max(doc.word_count / 1000, 0.5)
        density = count / words_k

        score = min(count / max(target, 1), 1.0)

        violations = []
        if count < target:
            violations.append(Violation(
                line=0,
                text=f"Found {count} technical terms (target: {target}+)",
                fix=f'Add more domain-specific terminology. Each adds {GEO_BOOSTS["technical_terms"]} visibility',
            ))

        return self._make_result(
            score, violations,
            metadata={
                "count": count,
                "target": target,
                "density_per_1k": round(density, 1),
                "sample_terms": sorted(list(terms))[:10],
            },
        )
