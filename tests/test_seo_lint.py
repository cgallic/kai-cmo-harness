from __future__ import annotations

from scripts.quality_gates.seo_lint import lint


BASE_DRAFT = """
# AI Search Optimization for Local Service Businesses

Meta: AI search optimization for local service businesses with source-backed SEO, entity, and agent-readiness checks.

AI search optimization helps local service businesses make public pages easier to crawl, understand, and cite.

## AI Search Optimization Baseline

The baseline is crawlable, indexable, helpful content with visible business facts.

## Measurement

Track repeated samples, dated screenshots, and analytics referrals.

[Related guide](/seo-guide)
[Checklist](/seo-checklist)
"""


def test_seo_lint_rejects_deterministic_llm_ranking_claims() -> None:
    result = lint(BASE_DRAFT + "\nWe guarantee rank in ChatGPT for dental AI receptionist queries.", "AI search optimization")

    assert result["passed"] is False
    assert any("LLM ranking" in error for error in result["errors"])


def test_seo_lint_allows_negative_warning_examples() -> None:
    result = lint(BASE_DRAFT + "\nNever promise to rank in ChatGPT or guarantee AI citations.", "AI search optimization")

    assert result["passed"] is True
