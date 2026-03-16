"""Tests for GEO signal rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.quality.parser import parse_markdown
from scripts.quality.rules.geo_signals import (
    CitationCount,
    QuotationCount,
    StatisticCount,
    TechnicalTermDensity,
)


def _doc(text):
    return parse_markdown(text)


def test_citation_count_detects():
    doc = _doc(
        "According to Google research, this works. "
        "Research from Harvard shows improvement. "
        "A study by McKinsey confirms the trend."
    )
    rule = CitationCount()
    result = rule.evaluate(doc)
    assert result.metadata["count"] >= 3


def test_citation_count_zero():
    doc = _doc("This is content without any citations or references to external sources.")
    rule = CitationCount()
    result = rule.evaluate(doc)
    assert result.metadata["count"] == 0
    assert len(result.violations) > 0


def test_quotation_count_detects():
    doc = _doc(
        '"The future of SEO is entity-based," says John Mueller. '
        '"Content quality matters more than quantity," notes Lily Ray.'
    )
    rule = QuotationCount()
    result = rule.evaluate(doc)
    assert result.metadata["count"] >= 2


def test_statistic_count_detects():
    doc = _doc(
        "Traffic increased by 42%. Revenue hit $1,000,000. "
        "That's a 3x improvement over baseline. "
        "Click-through rates rose 28%."
    )
    rule = StatisticCount()
    result = rule.evaluate(doc)
    assert result.metadata["count"] >= 3


def test_technical_terms_detects():
    doc = _doc(
        "Implement cross-domain entity reconciliation for knowledge-graph optimization. "
        "Use schema-markup and structured-data for entity-disambiguation."
    )
    rule = TechnicalTermDensity()
    result = rule.evaluate(doc)
    assert result.metadata["count"] >= 3


if __name__ == "__main__":
    test_citation_count_detects()
    test_citation_count_zero()
    test_quotation_count_detects()
    test_statistic_count_detects()
    test_technical_terms_detects()
    print("All GEO signal tests passed!")
