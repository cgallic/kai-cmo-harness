"""Tests for the durable business-profile overlay store.

Covers: round-trip persistence, deep-merge precedence (overlay wins over
config, defaults only fill gaps), cache invalidation after save, and
onboarding answers persisting into the overlay.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from kai.runtime.business_profile import (
    build_business_profile,
    build_business_profile_from_brand,
    clear_profile_overlay,
    deep_merge_profile,
    invalidate_profile_overlay_cache,
    load_local_service_fixture,
    load_profile_overlay,
    load_profile_overlay_record,
    profile_overlay_path,
    save_profile_overlay,
)
from kai.runtime.loader import load_workspace_profile
from kai.runtime.models import KaiBrandProfile
from kai.runtime.onboarding import OnboardingFlow, extract_profile_facts


@pytest.fixture()
def runtime_dir(tmp_path, monkeypatch):
    """Point KAI_RUNTIME_DIR at an isolated temp dir for each test."""
    target = tmp_path / "runtime"
    monkeypatch.setenv("KAI_RUNTIME_DIR", str(target))
    invalidate_profile_overlay_cache()
    load_workspace_profile.cache_clear()
    yield target
    invalidate_profile_overlay_cache()
    load_workspace_profile.cache_clear()


# ---------------------------------------------------------------------------
# Deep merge semantics
# ---------------------------------------------------------------------------

def test_deep_merge_nested_dicts_merge_lists_replace():
    base = {
        "identity": {"name": "Old", "tagline": "Keep me"},
        "offers": {"upsells": ["a", "b"]},
        "archetype": "local-service",
    }
    updates = {
        "identity": {"name": "New"},
        "offers": {"upsells": ["c"]},
    }
    merged = deep_merge_profile(base, updates)
    assert merged["identity"]["name"] == "New"
    assert merged["identity"]["tagline"] == "Keep me"
    assert merged["offers"]["upsells"] == ["c"]  # lists replaced
    assert merged["archetype"] == "local-service"
    # Inputs not mutated
    assert base["identity"]["name"] == "Old"
    assert updates["offers"]["upsells"] == ["c"]


# ---------------------------------------------------------------------------
# Round trip
# ---------------------------------------------------------------------------

def test_save_and_load_round_trip(runtime_dir):
    record = save_profile_overlay("test-brand", {"identity": {"tagline": "Learned in session"}})
    assert record["brand_id"] == "test-brand"
    assert record["updated_at"]

    loaded = load_profile_overlay("test-brand")
    assert loaded == {"identity": {"tagline": "Learned in session"}}

    path = profile_overlay_path("test-brand")
    assert path == runtime_dir / "profile" / "test-brand.json"
    assert path.exists()
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["profile"]["identity"]["tagline"] == "Learned in session"


def test_save_deep_merges_into_existing_overlay(runtime_dir):
    save_profile_overlay("test-brand", {
        "identity": {"tagline": "First"},
        "trust": {"review_platforms": ["Google"]},
    })
    first_record = load_profile_overlay_record("test-brand")

    save_profile_overlay("test-brand", {
        "identity": {"year_founded": 2020},
        "trust": {"review_platforms": ["Google", "Yelp"]},
    })
    payload = load_profile_overlay("test-brand")
    assert payload["identity"] == {"tagline": "First", "year_founded": 2020}
    assert payload["trust"]["review_platforms"] == ["Google", "Yelp"]  # lists replaced

    second_record = load_profile_overlay_record("test-brand")
    assert second_record["updated_at"] >= first_record["updated_at"]


def test_save_strips_reserved_keys(runtime_dir):
    save_profile_overlay("test-brand", {
        "brand_id": "spoofed",
        "updated_at": "1999-01-01T00:00:00",
        "identity": {"name": "Real"},
    })
    payload = load_profile_overlay("test-brand")
    assert "brand_id" not in payload
    assert "updated_at" not in payload
    record = load_profile_overlay_record("test-brand")
    assert record["brand_id"] == "test-brand"
    assert record["updated_at"] != "1999-01-01T00:00:00"


def test_load_missing_overlay_returns_empty(runtime_dir):
    assert load_profile_overlay("nobody-here") == {}
    assert load_profile_overlay_record("nobody-here") == {}


def test_save_requires_brand_id(runtime_dir):
    with pytest.raises(ValueError):
        save_profile_overlay("", {"identity": {"name": "x"}})
    with pytest.raises(TypeError):
        save_profile_overlay("test-brand", ["not", "a", "dict"])


def test_brand_id_sanitized_for_filesystem(runtime_dir):
    save_profile_overlay("weird/../brand id", {"identity": {"name": "Weird"}})
    path = profile_overlay_path("weird/../brand id")
    assert path.parent == runtime_dir / "profile"  # no traversal
    assert path.exists()
    assert load_profile_overlay("weird/../brand id")["identity"]["name"] == "Weird"


def test_clear_profile_overlay(runtime_dir):
    save_profile_overlay("test-brand", {"identity": {"name": "X"}})
    assert clear_profile_overlay("test-brand") is True
    assert load_profile_overlay("test-brand") == {}
    assert clear_profile_overlay("test-brand") is False


def test_corrupt_overlay_file_treated_as_empty(runtime_dir):
    path = profile_overlay_path("test-brand")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")
    invalidate_profile_overlay_cache()
    assert load_profile_overlay("test-brand") == {}
    # A save recovers the file
    save_profile_overlay("test-brand", {"identity": {"name": "Recovered"}})
    assert load_profile_overlay("test-brand")["identity"]["name"] == "Recovered"


# ---------------------------------------------------------------------------
# Merge precedence in profile building
# ---------------------------------------------------------------------------

_RAW = {
    "brand_id": "merge-brand",
    "archetype": "local-service",
    "identity": {"name": "Merge Co", "tagline": "From config"},
    "offers": {"pricing_model": "hourly", "upsells": ["config upsell"]},
}


def test_overlay_wins_over_config_values(runtime_dir):
    save_profile_overlay("merge-brand", {
        "identity": {"tagline": "From overlay"},
        "offers": {"pricing_model": "subscription"},
    })
    profile = build_business_profile(dict(_RAW))
    assert profile.identity.tagline == "From overlay"
    assert profile.offers.pricing_model == "subscription"
    # Config siblings not named in the overlay survive
    assert profile.identity.name == "Merge Co"
    assert profile.offers.upsells == ["config upsell"]


def test_overlay_lists_replace_config_lists(runtime_dir):
    save_profile_overlay("merge-brand", {
        "offers": {"upsells": ["overlay upsell"]},
    })
    profile = build_business_profile(dict(_RAW))
    assert profile.offers.upsells == ["overlay upsell"]


def test_defaults_still_fill_gaps_after_overlay(runtime_dir):
    save_profile_overlay("merge-brand", {"identity": {"tagline": "From overlay"}})
    profile = build_business_profile(dict(_RAW), apply_archetype_defaults=True)
    # Archetype defaults fill fields set by neither config nor overlay
    assert profile.goals.primary_kpi == "inbound_calls"
    assert profile.geography.is_mobile is True
    # ...but never overwrite config values
    assert profile.offers.pricing_model == "hourly"


def test_overlay_values_normalized_like_config(runtime_dir):
    save_profile_overlay("merge-brand", {
        "geography": {"primary_location": {"city": "Austin", "state": "Texas"}},
    })
    profile = build_business_profile(dict(_RAW))
    assert profile.geography.primary_location.state == "TX"


def test_apply_overlay_false_bypasses_overlay(runtime_dir):
    save_profile_overlay("merge-brand", {"identity": {"tagline": "From overlay"}})
    profile = build_business_profile(dict(_RAW), apply_overlay=False)
    assert profile.identity.tagline == "From config"


def test_overlay_applies_when_brand_id_derived_from_name(runtime_dir):
    save_profile_overlay("my-cool-biz", {"identity": {"tagline": "Persisted"}})
    profile = build_business_profile({"identity": {"name": "My Cool Biz"}})
    assert profile.brand_id == "my-cool-biz"
    assert profile.identity.tagline == "Persisted"


def test_overlay_applies_for_brand_profile_builds(runtime_dir):
    brand = KaiBrandProfile(
        id="brand-built",
        name="Brand Built",
        primary_archetype="local-service",
    )
    save_profile_overlay("brand-built", {
        "trust": {"review_count": 42},
        "channels": {"phone_number": "(555) 000-1111"},
    })
    profile = build_business_profile_from_brand(brand)
    assert profile.trust.review_count == 42
    assert profile.channels.phone_number == "(555) 000-1111"
    # And bypass still works
    bare = build_business_profile_from_brand(brand, apply_overlay=False)
    assert bare.trust.review_count is None


def test_fixture_loaders_ignore_overlays(runtime_dir):
    save_profile_overlay("truenorth-hvac", {"identity": {"name": "Hijacked"}})
    profile = load_local_service_fixture()
    assert profile.identity.name == "TrueNorth HVAC"


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------

def test_session_sees_its_own_writes(runtime_dir):
    # Prime the read cache with "no overlay"
    first = build_business_profile(dict(_RAW))
    assert first.identity.tagline == "From config"

    save_profile_overlay("merge-brand", {"identity": {"tagline": "Fresh write"}})
    second = build_business_profile(dict(_RAW))
    assert second.identity.tagline == "Fresh write"

    # And updates to an already-read overlay are visible too
    save_profile_overlay("merge-brand", {"identity": {"tagline": "Fresher write"}})
    third = build_business_profile(dict(_RAW))
    assert third.identity.tagline == "Fresher write"


def test_save_busts_workspace_profile_cache(runtime_dir):
    load_workspace_profile()
    assert load_workspace_profile.cache_info().currsize == 1
    save_profile_overlay("merge-brand", {"identity": {"tagline": "x"}})
    assert load_workspace_profile.cache_info().currsize == 0


def test_clear_busts_overlay_cache(runtime_dir):
    save_profile_overlay("merge-brand", {"identity": {"tagline": "From overlay"}})
    assert build_business_profile(dict(_RAW)).identity.tagline == "From overlay"
    clear_profile_overlay("merge-brand")
    assert build_business_profile(dict(_RAW)).identity.tagline == "From config"


# ---------------------------------------------------------------------------
# Onboarding persistence
# ---------------------------------------------------------------------------

def test_extract_profile_facts_maps_flat_answers():
    updates = extract_profile_facts({
        "business_name": "Facts Co",
        "website_url": "https://facts.example",
        "primary_service": "Roof Repair",
        "service_list": "Roof Repair, Gutter Cleaning",
        "pricing_model": "per-job",
        "primary_city": "Denver",
        "state_province": "Colorado",
        "service_radius_miles": 25,
        "phone_number": "(303) 555-0100",
        "monthly_budget_range": "$1,000/month",
        "archetype": "local_service",
        "gbp_verified": True,
        "_errors": ["ignore me"],
        "onboarding_stage": "profile",
        "empty_answer": "  ",
        "none_answer": None,
    })
    assert updates["identity"] == {"name": "Facts Co", "url": "https://facts.example"}
    assert updates["offers"]["primary_offer"] == "Roof Repair"
    assert updates["offers"]["pricing_model"] == "per-job"
    assert updates["offers"]["offer_list"] == [
        {"name": "Roof Repair", "is_primary": True},
        {"name": "Gutter Cleaning", "is_primary": False},
    ]
    assert updates["geography"]["primary_location"] == {
        "city": "Denver", "state": "Colorado", "radius_miles": 25,
    }
    assert updates["channels"] == {"phone_number": "(303) 555-0100"}
    assert updates["goals"] == {"monthly_budget_range": "$1,000/month"}
    assert updates["archetype"] == "local-service"  # normalized
    # Unknown scalar facts land in metadata; transient/blank keys are dropped
    assert updates["metadata"] == {"gbp_verified": True}
    assert "_errors" not in str(updates)


def test_extract_profile_facts_service_list_as_python_list():
    """A real list must be handled element-wise — str(['a','b']) once leaked
    "['a'" tokens into the durable overlay as offer names."""
    updates = extract_profile_facts({
        "primary_service": "Roof Repair",
        "service_list": ["Roof Repair", "  Gutter Cleaning  ", ""],
    })
    assert updates["offers"]["offer_list"] == [
        {"name": "Roof Repair", "is_primary": True},
        {"name": "Gutter Cleaning", "is_primary": False},
    ]
    # No str()-of-list artifacts ever persist
    for offer in updates["offers"]["offer_list"]:
        assert "[" not in offer["name"]
        assert "'" not in offer["name"]


def test_extract_profile_facts_service_list_tuple_and_scalar_elements():
    updates = extract_profile_facts({
        "service_list": ("Plumbing", 24),
    })
    assert updates["offers"]["offer_list"] == [
        {"name": "Plumbing", "is_primary": False},
        {"name": "24", "is_primary": False},
    ]


def test_extract_profile_facts_service_list_comma_string_mixed_whitespace():
    updates = extract_profile_facts({
        "primary_service": "  roof repair ",
        "service_list": " Roof Repair ,  Gutter Cleaning ,, ",
    })
    assert updates["offers"]["offer_list"] == [
        {"name": "Roof Repair", "is_primary": True},
        {"name": "Gutter Cleaning", "is_primary": False},
    ]


def test_extract_profile_facts_service_list_empty_list_ignored():
    updates = extract_profile_facts({"service_list": []})
    assert "offers" not in updates


def test_extract_profile_facts_passes_sections_through():
    updates = extract_profile_facts({
        "trust": {"review_count": 12, "review_platforms": ["Google"]},
        "constraints": {"budget_ceiling": "$500/month"},
    })
    assert updates["trust"]["review_count"] == 12
    assert updates["constraints"]["budget_ceiling"] == "$500/month"


def test_record_profile_answers_persists_to_overlay(runtime_dir):
    flow = OnboardingFlow()
    result = flow.record_profile_answers("onboard-co", {
        "business_name": "Onboard Co",
        "primary_city": "Tampa",
        "state_province": "Florida",
        "phone_number": "(813) 555-0142",
    })
    assert result["persisted"] is True
    assert result["updated_at"]

    # Facts survive into subsequent profile builds (and future processes)
    profile = build_business_profile({"brand_id": "onboard-co", "identity": {"name": "Onboard Co"}})
    assert profile.geography.primary_location.city == "Tampa"
    assert profile.geography.primary_location.state == "FL"
    assert profile.channels.phone_number == "(813) 555-0142"
    assert profile_overlay_path("onboard-co").exists()


def test_record_profile_answers_with_nothing_durable(runtime_dir):
    flow = OnboardingFlow()
    result = flow.record_profile_answers("onboard-co", {"_errors": [], "onboarding_stage": "profile"})
    assert result["persisted"] is False
    assert not profile_overlay_path("onboard-co").exists()


def test_create_brand_stub_persists_identity(runtime_dir):
    flow = OnboardingFlow()
    stub = flow.create_brand_stub(
        brand_id="stub-co",
        name="Stub Co",
        archetype="local_service",
        url="https://stub.example",
    )
    assert stub["onboarding_stage"] == "profile"  # stub shape unchanged

    overlay = load_profile_overlay("stub-co")
    assert overlay["identity"] == {"name": "Stub Co", "url": "https://stub.example"}
    assert overlay["archetype"] == "local-service"  # normalized for the builder

    profile = build_business_profile({"brand_id": "stub-co"})
    assert profile.identity.name == "Stub Co"
    assert profile.identity.url == "https://stub.example"
    assert profile.archetype == "local-service"
    # Normalized archetype means local-service defaults apply
    assert profile.goals.primary_kpi == "inbound_calls"


def test_create_brand_stub_persist_opt_out(runtime_dir):
    flow = OnboardingFlow()
    flow.create_brand_stub(brand_id="quiet-co", name="Quiet Co", persist_profile=False)
    assert not profile_overlay_path("quiet-co").exists()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
