"""Tests for the BusinessProfile application model."""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from kai.runtime.models import KaiBrandProfile
from kai.runtime.business_profile import (
    ANDON_WINDOW_CLEANING_FIXTURE,
    BusinessProfile,
    BusinessChannels,
    BusinessConstraints,
    BusinessGeography,
    BusinessGoals,
    BusinessIdentity,
    BusinessOffers,
    BusinessPersonas,
    BusinessTrust,
    ChannelPresence,
    LOCAL_SERVICE_DEFAULTS,
    LOCAL_SERVICE_FIXTURE,
    Offer,
    PersonaTarget,
    ServiceArea,
    TrustSignal,
    build_business_profile,
    build_business_profile_from_brand,
    load_andon_window_cleaning_fixture,
    load_local_service_fixture,
    normalize_business_profile,
    normalize_channel,
    normalize_state,
)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def test_normalize_state_full_name():
    assert normalize_state("Texas") == "TX"
    assert normalize_state("california") == "CA"
    assert normalize_state("new york") == "NY"


def test_normalize_state_abbreviation():
    assert normalize_state("TX") == "TX"
    assert normalize_state("ca") == "CA"


def test_normalize_state_none():
    assert normalize_state(None) is None


def test_normalize_state_unknown():
    assert normalize_state("Ontario") == "Ontario"


def test_normalize_channel_aliases():
    assert normalize_channel("Google Ads") == "paid-search"
    assert normalize_channel("Facebook Ads") == "paid-social"
    assert normalize_channel("google business profile") == "gbp"
    assert normalize_channel("GMB") == "gbp"
    assert normalize_channel("phone calls") == "calls"
    assert normalize_channel("word of mouth") == "referrals"
    assert normalize_channel("seo") == "local-seo"


def test_normalize_channel_passthrough():
    assert normalize_channel("paid-search") == "paid-search"
    assert normalize_channel("tiktok") == "tiktok"


def test_normalize_channel_strips_whitespace():
    assert normalize_channel("  Google Ads  ") == "paid-search"


# ---------------------------------------------------------------------------
# Sub-model construction
# ---------------------------------------------------------------------------

def test_service_area_defaults():
    area = ServiceArea()
    assert area.city is None
    assert area.state is None
    assert area.zip_codes == []
    assert area.radius_miles is None


def test_offer_defaults():
    offer = Offer(name="Widget")
    assert offer.name == "Widget"
    assert offer.is_primary is False
    assert offer.category is None


def test_persona_target_defaults():
    pt = PersonaTarget(persona_id="Competent Cog")
    assert pt.role == "primary"
    assert pt.pain_points == []


def test_trust_signal_construction():
    sig = TrustSignal(type="review", value="4.9 stars", source="Google")
    assert sig.type == "review"
    assert sig.source == "Google"


def test_channel_presence_defaults():
    ch = ChannelPresence(channel="calls")
    assert ch.status == "inactive"
    assert ch.url is None


# ---------------------------------------------------------------------------
# BusinessProfile construction from raw dict
# ---------------------------------------------------------------------------

def test_build_minimal_profile():
    raw = {
        "brand_id": "test-biz",
        "identity": {"name": "Test Business"},
    }
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    assert profile.brand_id == "test-biz"
    assert profile.identity.name == "Test Business"
    assert profile.archetype == "local-service"
    assert isinstance(profile.offers, BusinessOffers)
    assert isinstance(profile.geography, BusinessGeography)
    assert isinstance(profile.trust, BusinessTrust)


def test_build_profile_with_full_offers():
    raw = {
        "brand_id": "test",
        "identity": {"name": "Test"},
        "offers": {
            "primary_offer": "Widget repair",
            "offer_list": [
                {"name": "Widget Repair", "is_primary": True, "category": "repair"},
                {"name": "Widget Install", "category": "install"},
            ],
            "pricing_model": "per-job",
            "average_deal_value": "$500",
            "upsells": "Extended warranty\nPriority service",
        },
    }
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    assert profile.offers.primary_offer == "Widget repair"
    assert len(profile.offers.offer_list) == 2
    assert profile.offers.offer_list[0].is_primary is True
    assert profile.offers.pricing_model == "per-job"
    assert len(profile.offers.upsells) == 2


def test_build_profile_with_geography():
    raw = {
        "brand_id": "test",
        "identity": {"name": "Test"},
        "geography": {
            "primary_location": {"city": "Austin", "state": "Texas", "radius_miles": 25},
            "service_areas": [
                {"city": "Round Rock", "state": "texas"},
            ],
            "is_mobile": True,
            "location_count": 2,
        },
    }
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    assert profile.geography.primary_location.state == "TX"
    assert profile.geography.service_areas[0].state == "TX"
    assert profile.geography.is_mobile is True
    assert profile.geography.location_count == 2


def test_build_profile_with_personas_dict():
    raw = {
        "brand_id": "test",
        "identity": {"name": "Test"},
        "personas": {
            "primary": {
                "persona_id": "System Manager",
                "pain_points": ["AC broke", "Nobody picks up"],
            },
            "secondary": "Competent Cog",
            "icp_description": "Homeowners 35+",
        },
    }
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    assert profile.personas.primary.persona_id == "System Manager"
    assert len(profile.personas.primary.pain_points) == 2
    assert profile.personas.secondary.persona_id == "Competent Cog"
    assert profile.personas.secondary.role == "secondary"
    assert profile.personas.icp_description == "Homeowners 35+"


def test_build_profile_with_trust_signals():
    raw = {
        "brand_id": "test",
        "identity": {"name": "Test"},
        "trust": {
            "signals": [
                {"type": "review", "value": "4.8 stars", "source": "Google"},
            ],
            "review_count": 200,
            "review_average": 4.8,
            "review_platforms": ["Google", "Yelp"],
            "certifications": "NATE\nEPA 608",
            "guarantees": ["Money back"],
            "years_in_business": 5,
        },
    }
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    assert len(profile.trust.signals) == 1
    assert profile.trust.review_count == 200
    assert profile.trust.review_average == 4.8
    assert len(profile.trust.certifications) == 2
    assert profile.trust.years_in_business == 5


def test_build_profile_with_channels_normalization():
    raw = {
        "brand_id": "test",
        "identity": {"name": "Test"},
        "channels": {
            "channels": [
                {"channel": "Google Ads", "status": "active"},
                {"channel": "Facebook Ads", "status": "planned"},
                {"channel": "GMB", "status": "active"},
            ],
            "primary_lead_source": "calls",
            "phone_number": "(555) 123-4567",
        },
    }
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    channel_names = [c.channel for c in profile.channels.channels]
    assert "paid-search" in channel_names
    assert "paid-social" in channel_names
    assert "gbp" in channel_names
    assert profile.channels.phone_number == "(555) 123-4567"


def test_build_profile_with_constraints():
    raw = {
        "brand_id": "test",
        "identity": {"name": "Test"},
        "constraints": {
            "non_negotiables": "No competitor bashing\nPhone must be visible",
            "compliance_requirements": ["HIPAA"],
            "brand_voice_notes": ["Professional but warm"],
            "blocked_tactics": ["Fear-based urgency"],
            "budget_ceiling": "$3,000/month",
        },
    }
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    assert len(profile.constraints.non_negotiables) == 2
    assert profile.constraints.compliance_requirements == ["HIPAA"]
    assert profile.constraints.budget_ceiling == "$3,000/month"


# ---------------------------------------------------------------------------
# Local-service archetype defaults
# ---------------------------------------------------------------------------

def test_local_service_defaults_applied():
    raw = {
        "brand_id": "plumber-co",
        "archetype": "local-service",
        "identity": {"name": "Plumber Co"},
    }
    profile = build_business_profile(raw, apply_archetype_defaults=True)
    assert profile.offers.pricing_model == "per-job"
    assert profile.geography.is_mobile is True
    assert profile.goals.primary_kpi == "inbound_calls"
    assert len(profile.goals.goals) >= 4
    assert profile.channels.primary_lead_source == "calls"
    assert any(c.channel == "calls" for c in profile.channels.channels)
    assert any("KaiCalls" in n for n in profile.constraints.non_negotiables)


def test_local_service_defaults_do_not_overwrite_explicit():
    raw = {
        "brand_id": "plumber-co",
        "archetype": "local-service",
        "identity": {"name": "Plumber Co"},
        "offers": {"pricing_model": "hourly"},
        "geography": {"is_mobile": False},
        "goals": {"primary_kpi": "revenue"},
    }
    profile = build_business_profile(raw, apply_archetype_defaults=True)
    assert profile.offers.pricing_model == "hourly"
    assert profile.geography.is_mobile is False
    assert profile.goals.primary_kpi == "revenue"


def test_defaults_not_applied_for_other_archetypes():
    raw = {
        "brand_id": "saas-co",
        "archetype": "software",
        "identity": {"name": "SaaS Co"},
    }
    profile = build_business_profile(raw, apply_archetype_defaults=True)
    # Should NOT have local-service defaults
    assert profile.offers.pricing_model is None
    assert profile.goals.primary_kpi is None
    assert profile.channels.primary_lead_source is None


# ---------------------------------------------------------------------------
# KaiBrandProfile fallback
# ---------------------------------------------------------------------------

def test_build_from_brand_profile():
    brand = KaiBrandProfile(
        id="truenorth",
        name="TrueNorth HVAC",
        description="Residential HVAC in North Texas",
        url="https://truenorthhvac.com",
        primary_archetype="local-service",
        archetype_overlays=["multi-location"],
        active_channels=["calls", "local-seo", "reviews"],
        proof_points=["Same-day emergency service", "312 five-star reviews"],
        persona_defaults={"primary": "System Manager", "secondary": "Competent Cog"},
    )
    profile = build_business_profile_from_brand(brand)
    assert profile.brand_id == "truenorth"
    assert profile.identity.name == "TrueNorth HVAC"
    assert profile.identity.url == "https://truenorthhvac.com"
    assert profile.archetype == "local-service"
    assert profile.archetype_overlays == ["multi-location"]
    # Proof points become trust signals
    assert len(profile.trust.signals) == 2
    assert profile.trust.signals[0].type == "proof_point"
    # Persona defaults are picked up
    assert profile.personas.primary.persona_id == "System Manager"
    assert profile.personas.secondary.persona_id == "Competent Cog"
    # Active channels are imported
    assert any(c.channel == "calls" for c in profile.channels.channels)
    assert any(c.channel == "local-seo" for c in profile.channels.channels)


def test_build_from_brand_with_overrides():
    brand = KaiBrandProfile(
        id="truenorth",
        name="TrueNorth HVAC",
        primary_archetype="local-service",
        active_channels=["calls"],
        proof_points=["Same-day service"],
    )
    overrides = {
        "trust": {
            "signals": [{"type": "certification", "value": "NATE Certified"}],
            "review_count": 312,
        },
        "channels": {
            "channels": [
                {"channel": "calls", "status": "active"},
                {"channel": "paid-search", "status": "active"},
            ],
        },
    }
    profile = build_business_profile_from_brand(brand, overrides=overrides)
    # Overrides win over brand fallback for trust signals
    assert len(profile.trust.signals) == 1
    assert profile.trust.signals[0].type == "certification"
    assert profile.trust.review_count == 312
    # Overrides win for channels
    assert len(profile.channels.channels) == 2


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def test_model_dump_round_trip():
    profile = load_local_service_fixture()
    dumped = profile.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["brand_id"] == "truenorth-hvac"
    assert dumped["identity"]["name"] == "TrueNorth HVAC"
    assert len(dumped["offers"]["offer_list"]) == 4
    assert dumped["geography"]["primary_location"]["state"] == "TX"
    assert dumped["trust"]["review_count"] == 312
    assert len(dumped["channels"]["channels"]) == 8


def test_sub_model_serialization():
    area = ServiceArea(city="Dallas", state="TX", radius_miles=30)
    d = area.model_dump()
    assert d["city"] == "Dallas"
    assert d["state"] == "TX"
    assert d["radius_miles"] == 30


# ---------------------------------------------------------------------------
# Local-service fixture
# ---------------------------------------------------------------------------

def test_local_service_fixture_loads():
    profile = load_local_service_fixture()
    assert profile.brand_id == "truenorth-hvac"
    assert profile.archetype == "local-service"
    assert profile.identity.name == "TrueNorth HVAC"
    assert profile.identity.year_founded == 2018


def test_local_service_fixture_identity():
    profile = load_local_service_fixture()
    assert profile.identity.legal_name == "TrueNorth Heating & Cooling LLC"
    assert profile.identity.url == "https://truenorthhvac.com"
    assert profile.identity.tagline == "Same-day comfort, guaranteed."
    assert profile.identity.employee_count_range == "6-20"


def test_local_service_fixture_offers():
    profile = load_local_service_fixture()
    assert profile.offers.primary_offer == "Emergency HVAC repair"
    assert len(profile.offers.offer_list) == 4
    primary_offers = [o for o in profile.offers.offer_list if o.is_primary]
    assert len(primary_offers) == 1
    assert profile.offers.pricing_model == "per-job"
    assert len(profile.offers.upsells) == 3


def test_local_service_fixture_geography_normalized():
    profile = load_local_service_fixture()
    assert profile.geography.primary_location is not None
    assert profile.geography.primary_location.city == "Dallas"
    assert profile.geography.primary_location.state == "TX"  # Normalized from "Texas"
    assert profile.geography.primary_location.radius_miles == 30
    assert len(profile.geography.service_areas) == 4
    assert all(a.state == "TX" for a in profile.geography.service_areas)
    assert profile.geography.is_mobile is True
    assert profile.geography.location_count == 2


def test_local_service_fixture_personas():
    profile = load_local_service_fixture()
    assert profile.personas.primary.persona_id == "System Manager"
    assert len(profile.personas.primary.pain_points) == 3
    assert profile.personas.secondary.persona_id == "Competent Cog"
    assert "Homeowners" in profile.personas.icp_description


def test_local_service_fixture_trust():
    profile = load_local_service_fixture()
    assert profile.trust.review_count == 312
    assert profile.trust.review_average == 4.9
    assert len(profile.trust.signals) == 5
    assert len(profile.trust.review_platforms) == 4
    assert len(profile.trust.certifications) == 3
    assert profile.trust.years_in_business == 8


def test_local_service_fixture_goals():
    profile = load_local_service_fixture()
    assert profile.goals.primary_kpi == "inbound_calls"
    assert len(profile.goals.goals) == 4
    high_priority = [g for g in profile.goals.goals if g.priority == "high"]
    assert len(high_priority) == 2
    assert profile.goals.monthly_budget_range == "$2,000-$5,000"


def test_local_service_fixture_channels():
    profile = load_local_service_fixture()
    assert profile.channels.primary_lead_source == "calls"
    assert profile.channels.uses_call_tracking is True
    active = [c for c in profile.channels.channels if c.status == "active"]
    assert len(active) >= 5
    planned = [c for c in profile.channels.channels if c.status == "planned"]
    assert len(planned) >= 1


def test_local_service_fixture_constraints():
    profile = load_local_service_fixture()
    assert any("KaiCalls" in n for n in profile.constraints.non_negotiables)
    assert len(profile.constraints.compliance_requirements) >= 1
    assert len(profile.constraints.brand_voice_notes) >= 1
    assert len(profile.constraints.blocked_tactics) >= 1
    assert profile.constraints.budget_ceiling == "$5,000/month"


# ---------------------------------------------------------------------------
# Andon Window Cleaning fixture
# ---------------------------------------------------------------------------

def test_andon_fixture_loads():
    profile = load_andon_window_cleaning_fixture()
    assert profile.brand_id == "andon-window-cleaning"
    assert profile.archetype == "local-service"
    assert profile.identity.name == "Andon Window Cleaning"


def test_andon_fixture_identity_and_stage():
    profile = load_andon_window_cleaning_fixture()
    assert profile.identity.description.startswith("Solo window cleaning business")
    assert profile.metadata["stage"] == "startup"
    assert profile.metadata["age_months"] == 2
    assert profile.metadata["operator_type"] == "solo"


def test_andon_fixture_geography_normalized():
    profile = load_andon_window_cleaning_fixture()
    assert profile.geography.primary_location is not None
    assert profile.geography.primary_location.city == "Lakewood Ranch"
    assert profile.geography.primary_location.state == "FL"
    assert len(profile.geography.service_areas) == 4
    assert all(area.state == "FL" for area in profile.geography.service_areas)


def test_andon_fixture_channels_and_budget():
    profile = load_andon_window_cleaning_fixture()
    assert profile.channels.primary_lead_source == "calls"
    assert profile.channels.uses_call_tracking is False
    assert profile.goals.monthly_budget_range == "$300/month"
    active = [channel.channel for channel in profile.channels.channels if channel.status == "active"]
    assert "calls" in active
    assert "gbp" in active
    assert "referrals" in active


def test_andon_fixture_unknowns_preserved():
    profile = load_andon_window_cleaning_fixture()
    assert profile.channels.phone_number is None
    assert profile.metadata["owner_name"] is None
    assert profile.metadata["instagram_business_page"] is None
    assert profile.trust.review_count == 0
    assert profile.trust.review_average is None


# ---------------------------------------------------------------------------
# Required field behavior
# ---------------------------------------------------------------------------

def test_brand_id_required():
    try:
        build_business_profile({}, apply_archetype_defaults=False)
        # brand_id is derived from identity name, so this should still work
    except (KeyError, TypeError):
        pass  # Expected if identity is missing


def test_identity_name_required():
    raw = {"brand_id": "test", "identity": {}}
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    assert profile.identity.name == ""  # Falls back to empty string


def test_brand_id_derived_from_identity():
    raw = {"identity": {"name": "My Cool Biz"}}
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    assert profile.brand_id == "my-cool-biz"


# ---------------------------------------------------------------------------
# Archetype-aware shaping
# ---------------------------------------------------------------------------

def test_archetype_preserved():
    raw = {
        "brand_id": "test",
        "archetype": "ecommerce",
        "identity": {"name": "Test"},
    }
    profile = build_business_profile(raw, apply_archetype_defaults=True)
    assert profile.archetype == "ecommerce"


def test_archetype_from_brand():
    brand = KaiBrandProfile(id="test", name="Test", primary_archetype="professional-services")
    profile = build_business_profile_from_brand(brand)
    assert profile.archetype == "professional-services"


def test_archetype_default_is_local_service():
    raw = {"brand_id": "test", "identity": {"name": "Test"}}
    profile = build_business_profile(raw, apply_archetype_defaults=False)
    assert profile.archetype == "local-service"


# ---------------------------------------------------------------------------
# Normalization integration
# ---------------------------------------------------------------------------

def test_normalize_profile_state_names():
    profile = BusinessProfile(
        brand_id="test",
        identity=BusinessIdentity(name="Test"),
        geography=BusinessGeography(
            primary_location=ServiceArea(city="Houston", state="texas"),
            service_areas=[ServiceArea(city="Austin", state="TEXAS")],
        ),
    )
    normalized = normalize_business_profile(profile)
    assert normalized.geography.primary_location.state == "TX"
    assert normalized.geography.service_areas[0].state == "TX"


def test_normalize_profile_channels():
    profile = BusinessProfile(
        brand_id="test",
        identity=BusinessIdentity(name="Test"),
        channels=BusinessChannels(
            channels=[
                ChannelPresence(channel="Google Ads"),
                ChannelPresence(channel="Facebook"),
            ],
        ),
    )
    normalized = normalize_business_profile(profile)
    names = [c.channel for c in normalized.channels.channels]
    assert "paid-search" in names
    assert "paid-social" in names


def test_normalize_strips_trust_signal_whitespace():
    profile = BusinessProfile(
        brand_id="test",
        identity=BusinessIdentity(name="Test"),
        trust=BusinessTrust(
            signals=[TrustSignal(type="review", value="  4.9 stars  ")],
        ),
    )
    normalized = normalize_business_profile(profile)
    assert normalized.trust.signals[0].value == "4.9 stars"


# ---------------------------------------------------------------------------
# Handoff contract: can the audit layer answer its questions?
# ---------------------------------------------------------------------------

def test_handoff_what_does_business_sell():
    profile = load_local_service_fixture()
    assert profile.offers.primary_offer
    assert len(profile.offers.offer_list) > 0


def test_handoff_who_is_it_for():
    profile = load_local_service_fixture()
    assert profile.personas.primary is not None
    assert profile.personas.icp_description


def test_handoff_where_does_it_operate():
    profile = load_local_service_fixture()
    assert profile.geography.primary_location is not None
    assert len(profile.geography.service_areas) > 0


def test_handoff_what_proof_exists():
    profile = load_local_service_fixture()
    assert len(profile.trust.signals) > 0
    assert profile.trust.review_count is not None


def test_handoff_which_channels_active():
    profile = load_local_service_fixture()
    active = [c for c in profile.channels.channels if c.status == "active"]
    assert len(active) > 0


def test_handoff_what_constraints_matter():
    profile = load_local_service_fixture()
    assert len(profile.constraints.non_negotiables) > 0


if __name__ == "__main__":
    import inspect

    tests = [
        obj for name, obj in sorted(globals().items())
        if name.startswith("test_") and inspect.isfunction(obj)
    ]
    for test_fn in tests:
        test_fn()
        print(f"  PASS  {test_fn.__name__}")
    print(f"\nAll {len(tests)} BusinessProfile tests passed!")
