from __future__ import annotations

from kai.audits.creator_commerce import (
    audit_creator_commerce_ops,
    score_creator_commerce_ops,
    summarize_creator_commerce_findings,
)


def _healthy_fixture() -> dict:
    return {
        "creators": [
            {
                "creator_id": "c-001",
                "name": "Taylor North",
                "platform": "instagram",
                "follower_count": 24000,
                "engagement_rate": 0.034,
            },
            {
                "creator_id": "c-002",
                "name": "Alex Ridge",
                "platform": "youtube",
                "follower_count": 91000,
                "engagement_rate": 0.027,
            },
        ],
        "rate_cards": [
            {
                "creator_id": "c-001",
                "deliverables": "2 reels + 3 stories",
                "rate_usd": 900,
                "usage_rights_days": 30,
                "whitelisting_allowed": True,
            },
            {
                "creator_id": "c-002",
                "deliverables": "1 integration + 1 short",
                "rate_usd": 2400,
                "usage_rights_days": 45,
                "whitelisting_allowed": True,
            },
        ],
        "rights_policy": {
            "usage_rights_required": True,
            "platform_disclosure_required": True,
            "ftc_disclosure_template": "Paid partnership with {{brand}}. Affiliate links may apply.",
        },
        "affiliate": {
            "enabled": True,
            "tracking_template": "https://example.com/?utm_source=creator&utm_campaign={{creator_id}}",
            "payout_terms": "Net 30 monthly payout",
        },
        "performance": {
            "attributed_gmv": 12500.0,
            "order_count": 203,
            "attribution_window_days": 7,
        },
    }


def test_creator_commerce_healthy_fixture_scores_cleanly() -> None:
    findings = audit_creator_commerce_ops(_healthy_fixture())
    summary = summarize_creator_commerce_findings(findings)

    assert findings == []
    assert score_creator_commerce_ops(findings) == 100.0
    assert summary["counts"]["high"] == 0
    assert summary["counts"]["missing_data"] == 0


def test_creator_commerce_missing_inputs_create_expected_findings() -> None:
    findings = audit_creator_commerce_ops({})
    summary = summarize_creator_commerce_findings(findings)

    subcategories = {finding.subcategory for finding in findings}
    missing_field_paths = {
        finding.metadata.get("field_path")
        for finding in findings
        if finding.source == "missing_data"
    }

    assert "creators" in missing_field_paths
    assert "rate_cards" in missing_field_paths
    assert "performance.attributed_gmv" in missing_field_paths
    assert "rights_disclosure" in subcategories
    assert "affiliate_tracking" in subcategories
    assert summary["counts"]["high"] >= 2
    assert summary["score"] < 100.0


def test_low_engagement_is_flagged_when_metrics_exist() -> None:
    fixture = _healthy_fixture()
    fixture["creators"][0]["engagement_rate"] = 0.004

    findings = audit_creator_commerce_ops(fixture)
    subcategories = {finding.subcategory for finding in findings}

    assert "audience_quality" in subcategories
