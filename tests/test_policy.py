"""Tests for kai.runtime.policy — Policy and Risk Gating."""

from __future__ import annotations

import sys
import os
import unittest

# Ensure the repo root is on sys.path so `kai` is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kai.runtime.policy import (
    DEFAULT_MAX_BUDGET_INCREASE_PCT,
    BANNED_WORDS,
    REGULATED_CLAIM_KEYWORDS,
    RISK_TIER_MAP,
    PolicyEngine,
)


class TestRiskTierAssessment(unittest.TestCase):
    """Risk tier classification for each channel."""

    def setUp(self) -> None:
        self.engine = PolicyEngine()

    # -- Low risk actions --------------------------------------------------

    def test_website_fix_broken_link_is_low(self) -> None:
        tier = self.engine.assess_risk_tier("website", "fix_broken_link", {})
        self.assertEqual(tier, "low")

    def test_website_fix_tracking_is_low(self) -> None:
        tier = self.engine.assess_risk_tier("website", "fix_tracking", {})
        self.assertEqual(tier, "low")

    def test_website_update_metadata_is_low(self) -> None:
        tier = self.engine.assess_risk_tier("website", "update_metadata", {})
        self.assertEqual(tier, "low")

    def test_social_schedule_approved_post_is_low(self) -> None:
        tier = self.engine.assess_risk_tier("social", "schedule_approved_post", {})
        self.assertEqual(tier, "low")

    def test_paid_media_publish_approved_variant_is_low(self) -> None:
        tier = self.engine.assess_risk_tier("paid_media", "publish_approved_variant", {})
        self.assertEqual(tier, "low")

    def test_analytics_fix_tracking_is_low(self) -> None:
        tier = self.engine.assess_risk_tier("analytics", "fix_tracking", {})
        self.assertEqual(tier, "low")

    # -- Medium risk actions -----------------------------------------------

    def test_website_update_page_copy_is_medium(self) -> None:
        tier = self.engine.assess_risk_tier("website", "update_page_copy", {})
        self.assertEqual(tier, "medium")

    def test_website_update_cta_is_medium(self) -> None:
        tier = self.engine.assess_risk_tier("website", "update_cta", {})
        self.assertEqual(tier, "medium")

    def test_social_publish_post_is_medium(self) -> None:
        tier = self.engine.assess_risk_tier("social", "publish_social_post", {})
        self.assertEqual(tier, "medium")

    def test_paid_media_create_ad_creative_is_medium(self) -> None:
        tier = self.engine.assess_risk_tier("paid_media", "create_ad_creative", {})
        self.assertEqual(tier, "medium")

    def test_paid_media_adjust_bidding_is_medium(self) -> None:
        tier = self.engine.assess_risk_tier("paid_media", "adjust_bidding", {})
        self.assertEqual(tier, "medium")

    def test_email_update_nurture_copy_is_medium(self) -> None:
        tier = self.engine.assess_risk_tier("email", "update_nurture_copy", {})
        self.assertEqual(tier, "medium")

    def test_email_launch_email_sequence_is_medium(self) -> None:
        tier = self.engine.assess_risk_tier("email", "launch_email_sequence", {})
        self.assertEqual(tier, "medium")

    def test_analytics_update_goals_is_medium(self) -> None:
        tier = self.engine.assess_risk_tier("analytics", "update_goals", {})
        self.assertEqual(tier, "medium")

    # -- High risk actions -------------------------------------------------

    def test_website_restructure_page_is_high(self) -> None:
        tier = self.engine.assess_risk_tier("website", "restructure_page", {})
        self.assertEqual(tier, "high")

    def test_website_change_pricing_is_high(self) -> None:
        tier = self.engine.assess_risk_tier("website", "change_pricing", {})
        self.assertEqual(tier, "high")

    def test_paid_media_adjust_budget_is_high(self) -> None:
        tier = self.engine.assess_risk_tier("paid_media", "adjust_budget", {})
        self.assertEqual(tier, "high")

    def test_paid_media_pause_campaign_is_high(self) -> None:
        tier = self.engine.assess_risk_tier("paid_media", "pause_campaign", {})
        self.assertEqual(tier, "high")

    def test_paid_media_launch_campaign_is_high(self) -> None:
        tier = self.engine.assess_risk_tier("paid_media", "launch_campaign", {})
        self.assertEqual(tier, "high")

    def test_email_update_regulated_claims_is_high(self) -> None:
        tier = self.engine.assess_risk_tier("email", "update_regulated_claims", {})
        self.assertEqual(tier, "high")


class TestUnknownActionTypesDefaultHigh(unittest.TestCase):
    """Unknown (channel, action_type) pairs must default to high risk."""

    def setUp(self) -> None:
        self.engine = PolicyEngine()

    def test_unknown_channel_and_type(self) -> None:
        tier = self.engine.assess_risk_tier("sms", "blast_message", {})
        self.assertEqual(tier, "high")

    def test_known_channel_unknown_type(self) -> None:
        tier = self.engine.assess_risk_tier("website", "delete_entire_site", {})
        self.assertEqual(tier, "high")

    def test_unknown_channel_known_type(self) -> None:
        tier = self.engine.assess_risk_tier("carrier_pigeon", "fix_broken_link", {})
        self.assertEqual(tier, "high")

    def test_empty_strings_default_high(self) -> None:
        tier = self.engine.assess_risk_tier("", "", {})
        self.assertEqual(tier, "high")


class TestBudgetLimits(unittest.TestCase):
    """Budget limit checks -- within limits vs. over limits."""

    def setUp(self) -> None:
        self.engine = PolicyEngine()

    def test_no_budget_fields_passes(self) -> None:
        action = {"channel": "paid_media", "action_type": "adjust_budget"}
        result = self.engine.check_budget_limits(action, {})
        self.assertTrue(result["passed"])

    def test_increase_within_default_limit_passes(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "adjust_budget",
            "proposed_changes": {"budget_increase_pct": 15.0},
        }
        result = self.engine.check_budget_limits(action, {})
        self.assertTrue(result["passed"])

    def test_increase_at_exactly_default_limit_passes(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "adjust_budget",
            "proposed_changes": {"budget_increase_pct": 20.0},
        }
        result = self.engine.check_budget_limits(action, {})
        self.assertTrue(result["passed"])

    def test_increase_over_default_limit_fails(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "adjust_budget",
            "proposed_changes": {"budget_increase_pct": 25.0},
        }
        result = self.engine.check_budget_limits(action, {})
        self.assertFalse(result["passed"])
        self.assertIn("25.0%", result["detail"])
        self.assertIn("20.0%", result["detail"])

    def test_custom_brand_limit_enforced(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "adjust_budget",
            "proposed_changes": {"budget_increase_pct": 12.0},
        }
        brand_policy = {"max_budget_increase_pct": 10.0}
        result = self.engine.check_budget_limits(action, brand_policy)
        self.assertFalse(result["passed"])
        self.assertIn("12.0%", result["detail"])

    def test_daily_budget_within_cap_passes(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "adjust_budget",
            "proposed_changes": {"new_daily_budget": 500},
        }
        brand_policy = {"max_daily_budget": 1000}
        result = self.engine.check_budget_limits(action, brand_policy)
        self.assertTrue(result["passed"])

    def test_daily_budget_over_cap_fails(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "adjust_budget",
            "proposed_changes": {"new_daily_budget": 1500},
        }
        brand_policy = {"max_daily_budget": 1000}
        result = self.engine.check_budget_limits(action, brand_policy)
        self.assertFalse(result["passed"])
        self.assertIn("$1500", result["detail"])
        self.assertIn("$1000", result["detail"])

    def test_budget_violation_escalates_to_high(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "adjust_budget",
            "proposed_changes": {"budget_increase_pct": 50.0},
        }
        result = self.engine.check_budget_limits(action, {})
        self.assertTrue(result.get("escalate_to_high"))


class TestContentCompliance(unittest.TestCase):
    """Content compliance -- regulated claims and banned words."""

    def setUp(self) -> None:
        self.engine = PolicyEngine()

    def test_clean_content_passes(self) -> None:
        action = {
            "channel": "website",
            "action_type": "update_page_copy",
            "proposed_changes": {
                "headline": "Ship faster with better tooling",
                "body": "Our product helps teams move quickly.",
            },
        }
        result = self.engine.check_content_compliance(action)
        self.assertTrue(result["passed"])

    def test_no_content_passes(self) -> None:
        action = {"channel": "website", "action_type": "fix_broken_link"}
        result = self.engine.check_content_compliance(action)
        self.assertTrue(result["passed"])

    def test_medical_claim_detected(self) -> None:
        action = {
            "channel": "website",
            "action_type": "update_page_copy",
            "proposed_changes": {
                "body": "Our supplement is clinically proven to cure headaches.",
            },
        }
        result = self.engine.check_content_compliance(action)
        self.assertFalse(result["passed"])
        self.assertIn("Regulated claim (medical)", result["detail"])

    def test_financial_claim_detected(self) -> None:
        action = {
            "channel": "email",
            "action_type": "update_nurture_copy",
            "proposed_changes": {
                "body": "Invest now for guaranteed returns with no risk.",
            },
        }
        result = self.engine.check_content_compliance(action)
        self.assertFalse(result["passed"])
        self.assertIn("Regulated claim (financial)", result["detail"])

    def test_legal_claim_detected(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "create_ad_creative",
            "proposed_changes": {
                "body": "We guarantee a guaranteed settlement for every case.",
            },
        }
        result = self.engine.check_content_compliance(action)
        self.assertFalse(result["passed"])
        self.assertIn("Regulated claim (legal)", result["detail"])

    def test_banned_word_leverage_detected(self) -> None:
        action = {
            "channel": "social",
            "action_type": "publish_social_post",
            "proposed_changes": {
                "caption": "Leverage our platform for seamless results.",
            },
        }
        result = self.engine.check_content_compliance(action)
        self.assertFalse(result["passed"])
        self.assertIn("Banned word: 'leverage'", result["detail"])
        self.assertIn("Banned word: 'seamless'", result["detail"])

    def test_banned_word_synergy_detected(self) -> None:
        action = {
            "channel": "website",
            "action_type": "update_page_copy",
            "proposed_changes": {"headline": "Create synergy across teams."},
        }
        result = self.engine.check_content_compliance(action)
        self.assertFalse(result["passed"])
        self.assertIn("Banned word: 'synergy'", result["detail"])

    def test_personal_attribute_detected_on_social(self) -> None:
        action = {
            "channel": "social",
            "action_type": "publish_social_post",
            "proposed_changes": {
                "caption": "You're struggling with your health condition? We can help.",
            },
        }
        result = self.engine.check_content_compliance(action)
        self.assertFalse(result["passed"])
        self.assertIn("Personal attribute assertion", result["detail"])

    def test_personal_attribute_not_checked_on_website(self) -> None:
        """Personal-attribute patterns only apply to social/paid_media."""
        action = {
            "channel": "website",
            "action_type": "update_page_copy",
            "proposed_changes": {
                "body": "You're going to love our new features.",
            },
        }
        result = self.engine.check_content_compliance(action)
        # "you're" alone on website should not trigger (website is not social/paid_media)
        # Check that no personal attribute violation is raised
        self.assertNotIn("Personal attribute assertion", result.get("detail", ""))

    def test_regulated_claim_escalates_to_high(self) -> None:
        action = {
            "channel": "website",
            "action_type": "update_page_copy",
            "proposed_changes": {"body": "FDA approved treatment for all conditions."},
        }
        result = self.engine.check_content_compliance(action)
        self.assertTrue(result.get("escalate_to_high"))

    def test_extra_banned_words_from_brand_policy(self) -> None:
        engine = PolicyEngine(brand_policies={"banned_words_extra": ["foobar"]})
        action = {
            "channel": "website",
            "action_type": "update_page_copy",
            "proposed_changes": {"body": "Try our foobar approach to marketing."},
        }
        result = engine.check_content_compliance(action)
        self.assertFalse(result["passed"])
        self.assertIn("Banned word: 'foobar'", result["detail"])

    def test_nested_proposed_changes_text_extracted(self) -> None:
        action = {
            "channel": "email",
            "action_type": "launch_email_sequence",
            "proposed_changes": {
                "emails": [
                    {"subject": "Hello", "body": "Normal content here."},
                    {"subject": "Buy now", "body": "This is clinically proven!"},
                ],
            },
        }
        result = self.engine.check_content_compliance(action)
        self.assertFalse(result["passed"])
        self.assertIn("Regulated claim (medical)", result["detail"])


class TestFullEvaluate(unittest.TestCase):
    """Full evaluate() returning correct structure."""

    def setUp(self) -> None:
        self.engine = PolicyEngine()

    def test_evaluate_returns_required_keys(self) -> None:
        action = {
            "channel": "website",
            "action_type": "fix_broken_link",
            "proposed_changes": {},
        }
        result = self.engine.evaluate(action)
        required_keys = {
            "passed", "risk_tier", "checks", "violations",
            "auto_eligible", "requires_approval",
        }
        self.assertEqual(required_keys, required_keys & set(result.keys()))

    def test_clean_low_risk_action_passes(self) -> None:
        action = {
            "channel": "website",
            "action_type": "fix_broken_link",
            "proposed_changes": {},
        }
        result = self.engine.evaluate(action)
        self.assertTrue(result["passed"])
        self.assertEqual(result["risk_tier"], "low")
        self.assertEqual(result["violations"], [])

    def test_medium_risk_requires_approval(self) -> None:
        action = {
            "channel": "website",
            "action_type": "update_page_copy",
            "proposed_changes": {"body": "New headline for the page."},
        }
        result = self.engine.evaluate(action)
        self.assertTrue(result["passed"])
        self.assertEqual(result["risk_tier"], "medium")
        self.assertTrue(result["requires_approval"])
        self.assertFalse(result["auto_eligible"])

    def test_violation_causes_failure(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "create_ad_creative",
            "proposed_changes": {
                "body": "Guaranteed returns with our innovative platform.",
            },
        }
        result = self.engine.evaluate(action)
        self.assertFalse(result["passed"])
        self.assertTrue(len(result["violations"]) > 0)
        self.assertTrue(result["requires_approval"])

    def test_checks_list_has_all_dimensions(self) -> None:
        action = {
            "channel": "social",
            "action_type": "schedule_approved_post",
            "proposed_changes": {"caption": "Check out our blog post!"},
        }
        result = self.engine.evaluate(action)
        dimensions = {c["dimension"] for c in result["checks"]}
        expected = {
            "budget_limits",
            "content_compliance",
            "channel_policy",
            "frequency_limits",
            "brand_constraints",
        }
        self.assertEqual(dimensions, expected)

    def test_regulated_claim_escalates_risk_in_evaluate(self) -> None:
        """A medium-risk action with a regulated claim gets escalated to high."""
        action = {
            "channel": "website",
            "action_type": "update_page_copy",  # normally medium
            "proposed_changes": {
                "body": "Our product is FDA approved for treating all conditions.",
            },
        }
        result = self.engine.evaluate(action)
        self.assertEqual(result["risk_tier"], "high")
        self.assertFalse(result["passed"])


class TestAutoEligibility(unittest.TestCase):
    """Low risk + all checks pass = auto_eligible."""

    def setUp(self) -> None:
        self.engine = PolicyEngine()

    def test_low_risk_clean_action_is_auto_eligible(self) -> None:
        action = {
            "channel": "website",
            "action_type": "fix_broken_link",
            "proposed_changes": {},
        }
        result = self.engine.evaluate(action)
        self.assertTrue(result["auto_eligible"])
        self.assertFalse(result["requires_approval"])

    def test_low_risk_with_violation_not_auto_eligible(self) -> None:
        action = {
            "channel": "analytics",
            "action_type": "fix_tracking",  # low risk
            "proposed_changes": {
                "script": "leverage this tracking pixel for seamless data",
            },
        }
        result = self.engine.evaluate(action)
        self.assertFalse(result["auto_eligible"])

    def test_medium_risk_clean_not_auto_eligible(self) -> None:
        action = {
            "channel": "website",
            "action_type": "update_page_copy",
            "proposed_changes": {"body": "Clean copy with no issues."},
        }
        result = self.engine.evaluate(action)
        self.assertFalse(result["auto_eligible"])

    def test_auto_execute_disabled_by_brand_policy(self) -> None:
        engine = PolicyEngine(brand_policies={"auto_execute_low_risk": False})
        action = {
            "channel": "website",
            "action_type": "fix_broken_link",
            "proposed_changes": {},
        }
        result = engine.evaluate(action)
        self.assertFalse(result["auto_eligible"])


class TestBrandPolicyOverrides(unittest.TestCase):
    """Custom risk tier mapping per brand."""

    def test_override_promotes_low_to_high(self) -> None:
        engine = PolicyEngine(
            brand_policies={
                "risk_tier_overrides": {
                    ("website", "fix_broken_link"): "high",
                },
            }
        )
        tier = engine.assess_risk_tier("website", "fix_broken_link", {})
        self.assertEqual(tier, "high")

    def test_override_demotes_high_to_medium(self) -> None:
        engine = PolicyEngine(
            brand_policies={
                "risk_tier_overrides": {
                    ("paid_media", "adjust_budget"): "medium",
                },
            }
        )
        tier = engine.assess_risk_tier("paid_media", "adjust_budget", {})
        self.assertEqual(tier, "medium")

    def test_override_unknown_action_to_low(self) -> None:
        engine = PolicyEngine(
            brand_policies={
                "risk_tier_overrides": {
                    ("sms", "send_notification"): "low",
                },
            }
        )
        tier = engine.assess_risk_tier("sms", "send_notification", {})
        self.assertEqual(tier, "low")

    def test_override_not_affected_by_budget_escalation(self) -> None:
        """Brand override takes precedence; budget escalation still applies
        when the override is not present."""
        engine = PolicyEngine(
            brand_policies={"max_budget_increase_pct": 5.0}
        )
        # No override for this key, so default map + budget escalation apply
        tier = engine.assess_risk_tier(
            "paid_media",
            "adjust_bidding",  # default medium
            {"budget_increase_pct": 10.0},
        )
        self.assertEqual(tier, "high")

    def test_allowed_channels_enforced(self) -> None:
        engine = PolicyEngine(
            brand_policies={"allowed_channels": ["website", "email"]}
        )
        action = {
            "channel": "social",
            "action_type": "publish_social_post",
            "proposed_changes": {"caption": "Hello world"},
        }
        result = engine.check_channel_policy(action)
        self.assertFalse(result["passed"])
        self.assertIn("not in the brand's allowed channels", result["detail"])

    def test_required_disclaimer_enforced(self) -> None:
        engine = PolicyEngine(
            brand_policies={"required_disclaimer": "Results may vary."}
        )
        action = {
            "channel": "paid_media",
            "action_type": "create_ad_creative",
            "proposed_changes": {"body": "Try our product today!"},
        }
        result = engine.check_brand_constraints(action, engine._brand_policies)
        self.assertFalse(result["passed"])
        self.assertIn("Required brand disclaimer missing", result["detail"])

    def test_required_disclaimer_present_passes(self) -> None:
        engine = PolicyEngine(
            brand_policies={"required_disclaimer": "Results may vary."}
        )
        action = {
            "channel": "paid_media",
            "action_type": "create_ad_creative",
            "proposed_changes": {"body": "Try our product today! Results may vary."},
        }
        result = engine.check_brand_constraints(action, engine._brand_policies)
        self.assertTrue(result["passed"])

    def test_blocked_topics_enforced(self) -> None:
        engine = PolicyEngine(
            brand_policies={"blocked_topics": ["competitor_x", "lawsuit"]}
        )
        action = {
            "channel": "social",
            "action_type": "publish_social_post",
            "proposed_changes": {"caption": "Unlike Competitor_X, we deliver."},
        }
        result = engine.check_brand_constraints(action, engine._brand_policies)
        self.assertFalse(result["passed"])
        self.assertIn("Blocked topic found", result["detail"])


class TestChannelPolicy(unittest.TestCase):
    """Channel-specific platform policy checks."""

    def setUp(self) -> None:
        self.engine = PolicyEngine()

    def test_superlative_without_proof_fails(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "create_ad_creative",
            "proposed_changes": {"body": "The best marketing tool available."},
        }
        result = self.engine.check_channel_policy(action)
        self.assertFalse(result["passed"])
        self.assertIn("Superlative", result["detail"])

    def test_superlative_with_proof_passes(self) -> None:
        action = {
            "channel": "paid_media",
            "action_type": "create_ad_creative",
            "proposed_changes": {
                "body": "The best marketing tool available.",
                "proof_substantiation": "Rated #1 by G2 in Q1 2026",
            },
        }
        result = self.engine.check_channel_policy(action)
        self.assertTrue(result["passed"])

    def test_non_paid_media_superlative_not_checked(self) -> None:
        action = {
            "channel": "website",
            "action_type": "update_page_copy",
            "proposed_changes": {"body": "We are the best in the industry."},
        }
        result = self.engine.check_channel_policy(action)
        self.assertTrue(result["passed"])


class TestFrequencyLimits(unittest.TestCase):
    """Frequency limit checks."""

    def setUp(self) -> None:
        self.engine = PolicyEngine()

    def test_no_count_supplied_passes(self) -> None:
        action = {
            "channel": "social",
            "action_type": "publish_social_post",
            "proposed_changes": {},
        }
        result = self.engine.check_frequency_limits(action)
        self.assertTrue(result["passed"])

    def test_under_limit_passes(self) -> None:
        action = {
            "channel": "social",
            "action_type": "publish_social_post",
            "proposed_changes": {"actions_today": 5},
        }
        result = self.engine.check_frequency_limits(action)
        self.assertTrue(result["passed"])

    def test_at_limit_fails(self) -> None:
        action = {
            "channel": "social",
            "action_type": "publish_social_post",
            "proposed_changes": {"actions_today": 10},
        }
        result = self.engine.check_frequency_limits(action)
        self.assertFalse(result["passed"])
        self.assertIn("10 actions", result["detail"])

    def test_over_limit_fails(self) -> None:
        action = {
            "channel": "email",
            "action_type": "launch_email_sequence",
            "proposed_changes": {"actions_today": 8},
        }
        result = self.engine.check_frequency_limits(action)
        self.assertFalse(result["passed"])

    def test_custom_brand_frequency_limit(self) -> None:
        engine = PolicyEngine(
            brand_policies={"frequency_limits": {"social": 3}}
        )
        action = {
            "channel": "social",
            "action_type": "publish_social_post",
            "proposed_changes": {"actions_today": 3},
        }
        result = engine.check_frequency_limits(action)
        self.assertFalse(result["passed"])


class TestRiskTierMapCoverage(unittest.TestCase):
    """Verify the RISK_TIER_MAP constant is well-formed."""

    def test_all_values_are_valid_tiers(self) -> None:
        valid = {"low", "medium", "high"}
        for key, tier in RISK_TIER_MAP.items():
            self.assertIn(tier, valid, f"Invalid tier '{tier}' for {key}")

    def test_all_keys_are_channel_action_tuples(self) -> None:
        for key in RISK_TIER_MAP:
            self.assertIsInstance(key, tuple)
            self.assertEqual(len(key), 2)
            self.assertIsInstance(key[0], str)
            self.assertIsInstance(key[1], str)


if __name__ == "__main__":
    unittest.main()
