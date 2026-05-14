"""Kai Marketing OS audit engines.

Each engine examines a specific dimension of a business's marketing
posture and returns structured ``AuditFinding`` objects.  Engines are
designed for composition: ``compile_audit_result()`` in
``kai.models.audit`` merges findings from multiple engines into a
single ``AuditResult``.

Available engines
-----------------
- **website_conversion** -- CTA clarity, trust signals, phone visibility,
  form optimization, mobile readiness, page speed, and archetype-specific
  conversion checks.
- **local_seo** -- GBP completeness, NAP consistency, citations, local
  schema markup, service area pages, location pages, local keyword
  targeting, and per-location scoring for multi-location businesses.
- **trust_proof** -- Testimonials, case studies, credentials, team
  visibility, guarantees, insurance, affiliations, Google reviews, social
  proof specificity, and KaiCalls phone lead capture assessment.
- **review_reputation** -- Online review health: count, rating, velocity,
  recency, response rate, platform distribution, negative patterns, and
  review-generation system detection.
- **creative_readiness** -- Photography, video, logo, brand colors,
  testimonial content, case studies, before/after documentation, team
  headshots, social content library, and asset-to-channel gap analysis.
- **crm_hygiene** -- Contact list size, segmentation quality, email
  deliverability (bounce/spam/inbox), unsubscribe rate, data completeness,
  duplicate detection, engagement recency, consent/opt-in compliance,
  data source tracking, and overall CRM health scoring.
- **lifecycle_followup** -- Email capture, welcome sequences, post-service
  follow-up, review request automation, referral systems, dormant customer
  reactivation, quote/proposal follow-up, speed to lead, after-hours
  lead capture (KaiCalls), and CAN-SPAM/TCPA compliance advisory.
- **paid_media_readiness** -- Conversion tracking, landing pages, ad account
  status, pixel/tag verification, audience definitions, budget allocation,
  creative assets, offer/CTA clarity, competitor landscape advisory,
  compliance pre-check, and per-platform readiness assessments.
- **offer_architecture** -- Competitor funnel-hack evidence, offer/pricing
  matrix capture, conversion mechanics extraction, and A/B test hypotheses for
  ecommerce/CRO audits.
"""

# Lazy imports to avoid ImportError when a sibling engine file has not
# been created yet (engines are built incrementally across tasks).

__all__: list = []

try:
    from kai.audits.website_conversion import (
        audit_website_conversion,
        get_archetype_weights,
        score_website_conversion,
    )
    __all__ += [
        "audit_website_conversion",
        "get_archetype_weights",
        "score_website_conversion",
    ]
except ImportError:
    pass

try:
    from kai.audits.local_seo import (
        assess_location_completeness,
        audit_local_seo,
        score_local_seo,
    )
    __all__ += [
        "audit_local_seo",
        "score_local_seo",
        "assess_location_completeness",
    ]
except ImportError:
    pass

try:
    from kai.audits.trust_proof import (
        audit_trust_proof,
        score_trust_proof,
    )
    __all__ += [
        "audit_trust_proof",
        "score_trust_proof",
    ]
except ImportError:
    pass

try:
    from kai.audits.review_reputation import (
        audit_review_reputation,
        parse_review_metrics,
        score_review_reputation,
    )
    __all__ += [
        "audit_review_reputation",
        "parse_review_metrics",
        "score_review_reputation",
    ]
except ImportError:
    pass

try:
    from kai.audits.creative_readiness import (
        audit_creative_readiness,
        map_assets_to_channels,
        score_creative_readiness,
    )
    __all__ += [
        "audit_creative_readiness",
        "map_assets_to_channels",
        "score_creative_readiness",
    ]
except ImportError:
    pass

try:
    from kai.audits.crm_hygiene import (
        assess_list_health_tier,
        audit_crm_hygiene,
        score_crm_hygiene,
    )
    __all__ += [
        "audit_crm_hygiene",
        "score_crm_hygiene",
        "assess_list_health_tier",
    ]
except ImportError:
    pass

try:
    from kai.audits.lifecycle_followup import (
        audit_lifecycle_followup,
        score_lifecycle_followup,
    )
    __all__ += [
        "audit_lifecycle_followup",
        "score_lifecycle_followup",
    ]
except ImportError:
    pass

try:
    from kai.audits.paid_media_readiness import (
        audit_paid_media_readiness,
        get_platform_prerequisites,
        score_paid_media_readiness,
    )
    __all__ += [
        "audit_paid_media_readiness",
        "get_platform_prerequisites",
        "score_paid_media_readiness",
    ]
except ImportError:
    pass

try:
    from kai.audits.offer_architecture import (
        audit_offer_architecture,
        build_offer_pricing_matrix,
        extract_conversion_mechanics,
        generate_ab_test_hypotheses,
        score_offer_architecture,
    )
    __all__ += [
        "audit_offer_architecture",
        "build_offer_pricing_matrix",
        "extract_conversion_mechanics",
        "generate_ab_test_hypotheses",
        "score_offer_architecture",
    ]
except ImportError:
    pass
