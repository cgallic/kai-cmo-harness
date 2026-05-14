from kai.audits.offer_architecture import (
    audit_offer_architecture,
    build_offer_pricing_matrix,
    extract_conversion_mechanics,
    generate_ab_test_hypotheses,
    score_offer_architecture,
)
from kai.audits import audit_offer_architecture as exported_audit_offer_architecture
from kai.models.audit import FindingSource
from kai.models.business_profile import (
    BusinessClassification,
    BusinessIdentity,
    BusinessProfile,
    Offer,
)


def _ecommerce_profile() -> BusinessProfile:
    return BusinessProfile(
        id="brand",
        identity=BusinessIdentity(
            business_name="Sample DTC",
            website_url="https://example.com",
        ),
        classification=BusinessClassification(
            archetype="ecommerce",
            business_model="product",
        ),
        offers=[
            Offer(
                name="Daily Greens",
                description="Powdered daily supplement.",
                price_range="$59/mo",
                is_primary=True,
                primary_cta="Buy Now",
            )
        ],
    )


def _im8_like_funnel():
    return {
        "name": "IM8",
        "source_urls": [
            "https://www.tiktok.com/@brendenbuilds/video/7639399895471901966",
        ],
        "landing_page_url": "https://example.com/im8-archive",
        "pricing": [
            {
                "path": "90-day subscription",
                "price": "$99",
                "billing_model": "subscription",
                "quantity": "90-day supply",
                "is_default": True,
                "bonuses": ["free shaker", "travel pack"],
                "retention_incentive": "continued subscription unlocks more gifts",
                "risk_reversal": "cancel anytime",
            },
            {
                "path": "One-time purchase",
                "price": "$149",
                "billing_model": "one-time",
                "quantity": "30-day supply",
            },
        ],
        "notes": (
            "Subscription is the default and one-time purchase is priced high "
            "as an anchor. Bonus stack and continued subscription gifts push "
            "the 90-day path."
        ),
    }


def test_missing_competitor_funnels_is_critical_gap_for_ecommerce():
    assert exported_audit_offer_architecture is audit_offer_architecture

    findings = audit_offer_architecture(_ecommerce_profile())

    assert len(findings) == 1
    assert findings[0].source == FindingSource.MISSING_DATA.value
    assert findings[0].severity == "high"
    assert "funnel_data.competitors" in findings[0].metadata["field_path"]


def test_offer_matrix_extracts_subscription_paths_and_sources():
    matrix = build_offer_pricing_matrix([_im8_like_funnel()])

    assert len(matrix) == 2
    assert matrix[0]["competitor"] == "IM8"
    assert matrix[0]["default_path"] is True
    assert matrix[0]["billing_model"] == "subscription"
    assert matrix[0]["bonuses"] == ["free shaker", "travel pack"]
    assert matrix[0]["source_url"].startswith("https://www.tiktok.com/")


def test_mechanics_generate_test_hypotheses():
    mechanics = extract_conversion_mechanics(_im8_like_funnel())
    hypotheses = generate_ab_test_hypotheses(mechanics)

    assert "subscription_framing" in mechanics
    assert "price_anchoring" in mechanics
    assert "bonus_stacking" in mechanics
    assert any(item["mechanic"] == "subscription_framing" for item in hypotheses)
    assert all(item["primary_metric"] == "purchase_conversion_rate" for item in hypotheses)


def test_audit_summary_contains_matrix_mechanics_and_ab_tests():
    findings = audit_offer_architecture(
        _ecommerce_profile(),
        {"competitors": [_im8_like_funnel()]},
    )

    summary = next(
        finding for finding in findings if finding.subcategory == "funnel_hack_summary"
    )

    assert summary.metadata["offer_pricing_matrix"]
    assert summary.metadata["mechanics_by_competitor"]["IM8"]
    assert summary.metadata["ab_test_hypotheses"]
    assert score_offer_architecture(findings) == 100.0


def test_audit_flags_unsourced_teardown():
    funnel = _im8_like_funnel()
    funnel.pop("source_urls")
    funnel.pop("landing_page_url")

    findings = audit_offer_architecture(_ecommerce_profile(), {"competitors": [funnel]})

    assert any(finding.subcategory == "source_evidence" for finding in findings)
    assert score_offer_architecture(findings) == 85.0
