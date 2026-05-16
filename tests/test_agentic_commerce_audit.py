from __future__ import annotations

from kai.audits.agentic_commerce import (
    audit_agentic_commerce_readiness,
    score_agentic_commerce_readiness,
    summarize_agentic_commerce_findings,
)
from scripts.quality_gates.agent_commerce_lint import verdict


def _healthy_fixture() -> dict:
    return {
        "schema": {
            "product": [
                {"id": "sku-1", "name": "Widget"},
                {"id": "sku-2", "name": "Widget Plus"},
            ]
        },
        "catalog": {
            "products": [
                {
                    "id": "sku-1",
                    "title": "Widget",
                    "sku": "W-1",
                    "price": "29.00",
                    "sale_price": "24.00",
                    "currency": "USD",
                    "availability": "in_stock",
                    "url": "https://example.com/widget",
                },
                {
                    "id": "sku-2",
                    "title": "Widget Plus",
                    "sku": "W-2",
                    "price": "49.00",
                    "currency": "USD",
                    "availability": "in_stock",
                    "url": "https://example.com/widget-plus",
                },
            ]
        },
        "policies": {
            "shipping": "Ships in 2-4 days in the US.",
            "returns": "30-day returns for unopened products.",
        },
        "proof": {"review_count": 114, "average_rating": 4.7},
        "checkout": {
            "checkout_url": "https://example.com/checkout",
            "guest_checkout": True,
            "payment_methods": ["card", "shop_pay"],
        },
        "crawler": {
            "robots_txt": "User-agent: *\nAllow: /",
            "llms_txt": "# Example\n> Summary\n## Products",
            "ai_policy": "Allowed bots listed with licensing notes.",
        },
        "offers": [
            {
                "title": "Spring Bundle",
                "eligibility": "US only, first order.",
                "expiration": "2026-06-01",
            }
        ],
        "protocols": {"acp": True, "ucp": True, "ap2": False, "x402": False},
        "connected_sources": {"credentials_available": True, "merchant_center": False},
    }


def test_audit_scores_healthy_fixture_without_critical_findings() -> None:
    findings = audit_agentic_commerce_readiness(_healthy_fixture())
    summary = summarize_agentic_commerce_findings(findings)

    assert findings == []
    assert score_agentic_commerce_readiness(findings) == 100.0
    assert summary["counts"]["critical"] == 0
    assert verdict(summary) == ("PASS", 0)


def test_missing_catalog_and_checkout_generate_findings() -> None:
    findings = audit_agentic_commerce_readiness({})
    summary = summarize_agentic_commerce_findings(findings)

    subcategories = {finding.subcategory for finding in findings}
    missing_field_paths = {
        finding.metadata.get("field_path")
        for finding in findings
        if finding.source == "missing_data"
    }

    assert "product_schema" in subcategories
    assert "shipping_return_policy" in subcategories
    assert "checkout_readiness" in subcategories
    assert "catalog.products" in missing_field_paths
    assert summary["counts"]["high"] >= 1
    assert verdict(summary)[1] in {1, 2}


def test_unavailable_credentials_are_reported_as_data_gap() -> None:
    fixture = _healthy_fixture()
    fixture["connected_sources"]["credentials_available"] = False

    findings = audit_agentic_commerce_readiness(fixture)
    data_gap_paths = [
        finding.metadata.get("field_path")
        for finding in findings
        if finding.source == "missing_data"
    ]

    assert "connected_sources.credentials_available" in data_gap_paths
