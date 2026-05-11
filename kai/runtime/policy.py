"""Policy and Risk Gating for the Kai Marketing OS.

Every proposed marketing action must pass through policy evaluation before
execution. This module classifies actions by risk tier, checks content
compliance, enforces budget limits, validates channel policies, and gates
frequency -- all without external dependencies.
"""

from __future__ import annotations

import re
from typing import Any, Literal, Optional

# ---------------------------------------------------------------------------
# Default risk-tier classification
# ---------------------------------------------------------------------------

RISK_TIER_MAP: dict[tuple[str, str], str] = {
    # Website actions
    ("website", "fix_broken_link"): "low",
    ("website", "fix_tracking"): "low",
    ("website", "update_metadata"): "low",
    ("website", "refresh_approved_section"): "low",
    ("website", "update_page_copy"): "medium",
    ("website", "update_page_section"): "medium",
    ("website", "update_cta"): "medium",
    ("website", "restructure_page"): "high",
    ("website", "change_pricing"): "high",
    ("website", "update_regulated_claims"): "high",
    # Social actions
    ("social", "schedule_approved_post"): "low",
    ("social", "publish_social_post"): "medium",
    ("social", "schedule_social_post"): "medium",
    # Paid media actions
    ("paid_media", "read_performance"): "low",
    ("paid_media", "evaluate_ads"): "low",
    ("paid_media", "generate_recommendations"): "low",
    ("paid_media", "validate_ad_upload"): "low",
    ("paid_media", "publish_approved_variant"): "low",
    ("paid_media", "upload_ad_asset"): "medium",
    ("paid_media", "create_paused_campaign"): "medium",
    ("paid_media", "create_paused_adset"): "medium",
    ("paid_media", "create_paused_ad"): "medium",
    ("paid_media", "create_ad_creative"): "medium",
    ("paid_media", "adjust_bidding"): "medium",
    ("paid_media", "adjust_bid"): "medium",
    ("paid_media", "reduce_bid"): "medium",
    ("paid_media", "increase_bid"): "high",
    ("paid_media", "change_bid_strategy"): "high",
    ("paid_media", "adjust_target_cpa"): "high",
    ("paid_media", "adjust_target_roas"): "high",
    ("paid_media", "adjust_budget"): "high",
    ("paid_media", "reduce_budget"): "high",
    ("paid_media", "increase_budget"): "high",
    ("paid_media", "activate_campaign"): "high",
    ("paid_media", "activate_adset"): "high",
    ("paid_media", "activate_ad"): "high",
    ("paid_media", "pause_campaign"): "high",
    ("paid_media", "pause_adset"): "high",
    ("paid_media", "pause_ad"): "high",
    ("paid_media", "launch_campaign"): "high",
    ("paid_media", "expand_targeting"): "high",
    ("paid_media", "add_keyword"): "high",
    ("paid_media", "add_audience"): "high",
    # Email actions
    ("email", "send_approved_template"): "low",
    ("email", "update_nurture_copy"): "medium",
    ("email", "launch_email_sequence"): "medium",
    ("email", "update_regulated_claims"): "high",
    # Analytics actions
    ("analytics", "fix_tracking"): "low",
    ("analytics", "update_goals"): "medium",
}

# ---------------------------------------------------------------------------
# Banned words -- Tier 1 from the existing quality gate
# ---------------------------------------------------------------------------

BANNED_WORDS: list[str] = [
    "leverage",
    "utilize",
    "utilise",
    "synergy",
    "synergies",
    "innovative",
    "innovation",
    "deep dive",
    "circle back",
    "touch base",
    "moving forward",
    "at the end of the day",
    "it's important to note",
    "in today's rapidly evolving",
    "in today's fast-paced",
    "game-changer",
    "game changer",
    "paradigm shift",
    "thought leader",
    "thought leadership",
    "best practices",
    "cutting-edge",
    "cutting edge",
    "state-of-the-art",
    "state of the art",
    "seamless",
    "robust",
    "scalable",
    "holistic",
    "empower",
    "empowering",
    "transformative",
    "revolutionize",
    "revolutionizing",
    "ecosystem",
    "low-hanging fruit",
    "low hanging fruit",
    "next level",
    "move the needle",
    "value proposition",
    "actionable insights",
    "pain points",
    "in conclusion",
]

# ---------------------------------------------------------------------------
# Regulated-claims keyword sets
# ---------------------------------------------------------------------------

REGULATED_CLAIM_KEYWORDS: dict[str, list[str]] = {
    "medical": [
        "cure",
        "cures",
        "diagnose",
        "treat",
        "treatment",
        "clinical",
        "clinically proven",
        "FDA approved",
        "FDA-approved",
        "prescription",
        "medical grade",
        "medical-grade",
        "heals",
        "prevents disease",
        "miracle",
    ],
    "financial": [
        "guaranteed return",
        "guaranteed returns",
        "risk-free",
        "risk free",
        "no risk",
        "double your money",
        "get rich",
        "financial freedom",
        "passive income guaranteed",
        "guaranteed income",
        "guaranteed profit",
    ],
    "legal": [
        "guaranteed outcome",
        "guaranteed settlement",
        "we will win",
        "100% success rate",
        "guaranteed results",
        "never lose",
    ],
}

# Personal-attribute patterns banned in Meta ads
PERSONAL_ATTRIBUTE_PATTERNS: list[str] = [
    r"\byou are\b",
    r"\byou're\b",
    r"\byour (?:race|ethnicity|religion|gender|sexuality|disability|health condition|financial status|criminal record)\b",
]

# ---------------------------------------------------------------------------
# Default budget constraints
# ---------------------------------------------------------------------------

DEFAULT_MAX_BUDGET_INCREASE_PCT: float = 20.0  # >20% increase = high risk
DEFAULT_MAX_BID_INCREASE_PCT: float = 10.0  # >10% bid increase = high risk
DEFAULT_MAX_SINGLE_BUDGET_CHANGE_USD: float = 100.0

PAID_MEDIA_READ_ONLY_ACTIONS: set[str] = {
    "read_performance",
    "evaluate_ads",
    "generate_recommendations",
    "validate_ad_upload",
}

PAID_MEDIA_MUTATION_ACTIONS: set[str] = {
    "publish_approved_variant",
    "upload_ad_asset",
    "create_paused_campaign",
    "create_paused_adset",
    "create_paused_ad",
    "create_ad_creative",
    "adjust_bidding",
    "adjust_bid",
    "increase_bid",
    "reduce_bid",
    "change_bid_strategy",
    "adjust_target_cpa",
    "adjust_target_roas",
    "adjust_budget",
    "increase_budget",
    "reduce_budget",
    "activate_campaign",
    "activate_adset",
    "activate_ad",
    "pause_campaign",
    "pause_adset",
    "pause_ad",
    "launch_campaign",
    "expand_targeting",
    "add_keyword",
    "add_audience",
}

PAID_MEDIA_SPEND_ACTIONS: set[str] = {
    "adjust_bidding",
    "adjust_bid",
    "increase_bid",
    "reduce_bid",
    "change_bid_strategy",
    "adjust_target_cpa",
    "adjust_target_roas",
    "adjust_budget",
    "increase_budget",
    "reduce_budget",
    "activate_campaign",
    "activate_adset",
    "activate_ad",
    "launch_campaign",
}

PAID_MEDIA_BUDGET_ACTIONS: set[str] = {
    "adjust_budget",
    "increase_budget",
    "reduce_budget",
}

PAID_MEDIA_BID_ACTIONS: set[str] = {
    "adjust_bidding",
    "adjust_bid",
    "increase_bid",
    "reduce_bid",
}

# ---------------------------------------------------------------------------
# Default frequency limits (actions per channel per day)
# ---------------------------------------------------------------------------

DEFAULT_FREQUENCY_LIMITS: dict[str, int] = {
    "social": 10,
    "email": 5,
    "paid_media": 20,
    "website": 50,
    "analytics": 100,
}


class PolicyEngine:
    """Evaluates proposed marketing actions against policy dimensions."""

    def __init__(self, brand_policies: Optional[dict[str, Any]] = None) -> None:
        """Initialise with optional per-brand policy overrides.

        ``brand_policies`` may contain:
        - ``risk_tier_overrides``: dict mapping (channel, action_type) -> tier
        - ``max_daily_budget``: float, absolute cap on daily spend
        - ``max_budget_increase_pct``: float, max percentage increase allowed
        - ``frequency_limits``: dict mapping channel -> max actions per day
        - ``allowed_channels``: list of channels the brand may use
        - ``banned_words_extra``: additional banned words beyond the defaults
        - ``auto_execute_low_risk``: bool, whether low-risk actions can skip approval
        - ``paid_media_guardrails``: dict with allowed_accounts,
          allowed_campaigns, allowed_adsets, max_bid_increase_pct,
          max_single_budget_change_usd, and require_rollback_for_activation
        """
        self._brand_policies: dict[str, Any] = brand_policies or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, action: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a proposed action and return a full policy result.

        Parameters
        ----------
        action:
            Must contain at minimum: ``channel``, ``action_type``.
            Optionally: ``proposed_changes``, ``brand_id``, ``action_id``.

        Returns
        -------
        dict with keys: passed, risk_tier, checks, violations,
        auto_eligible, requires_approval.
        """
        channel: str = action.get("channel", "")
        action_type: str = action.get("action_type", "")
        proposed_changes: dict[str, Any] = action.get("proposed_changes", {})

        # 1. Risk tier
        risk_tier = self.assess_risk_tier(channel, action_type, proposed_changes)

        # 2. Run all check dimensions
        checks: list[dict[str, Any]] = []
        violations: list[str] = []

        budget_result = self.check_budget_limits(action, self._brand_policies)
        checks.append(budget_result)
        if not budget_result["passed"]:
            violations.append(budget_result["detail"])

        content_result = self.check_content_compliance(action)
        checks.append(content_result)
        if not content_result["passed"]:
            violations.append(content_result["detail"])

        channel_result = self.check_channel_policy(action)
        checks.append(channel_result)
        if not channel_result["passed"]:
            violations.append(channel_result["detail"])

        paid_media_result = self.check_paid_media_guardrails(action)
        checks.append(paid_media_result)
        if not paid_media_result["passed"]:
            violations.append(paid_media_result["detail"])

        frequency_result = self.check_frequency_limits(action)
        checks.append(frequency_result)
        if not frequency_result["passed"]:
            violations.append(frequency_result["detail"])

        brand_result = self.check_brand_constraints(action, self._brand_policies)
        checks.append(brand_result)
        if not brand_result["passed"]:
            violations.append(brand_result["detail"])

        # 3. Determine overall pass/fail
        all_checks_passed = all(c["passed"] for c in checks)

        # If any check escalated risk, promote the tier
        if risk_tier != "high":
            for check in checks:
                if check.get("escalate_to_high"):
                    risk_tier = "high"
                    break

        passed = all_checks_passed
        auto_execute_allowed = self._brand_policies.get("auto_execute_low_risk", True)
        if channel == "paid_media" and action_type in PAID_MEDIA_MUTATION_ACTIONS:
            # Paid media writes can spend real money or disrupt a working ad
            # account. Even low-risk write helpers stay human-approved.
            auto_execute_allowed = False

        auto_eligible = (
            risk_tier == "low"
            and all_checks_passed
            and auto_execute_allowed
        )
        requires_approval = risk_tier in ("medium", "high") or not all_checks_passed
        if channel == "paid_media" and action_type in PAID_MEDIA_MUTATION_ACTIONS:
            requires_approval = True

        return {
            "passed": passed,
            "risk_tier": risk_tier,
            "checks": checks,
            "violations": violations,
            "auto_eligible": auto_eligible,
            "requires_approval": requires_approval,
        }

    def assess_risk_tier(
        self,
        channel: str,
        action_type: str,
        proposed_changes: dict[str, Any],
    ) -> str:
        """Determine the risk tier for an action based on type and context.

        Checks brand-level overrides first, then the default RISK_TIER_MAP.
        Unknown (channel, action_type) pairs default to ``"high"``.
        """
        # Brand-level overrides take precedence
        overrides: dict[tuple[str, str], str] = self._brand_policies.get(
            "risk_tier_overrides", {}
        )
        key = (channel, action_type)
        if key in overrides:
            return overrides[key]

        tier = RISK_TIER_MAP.get(key, "high")

        # Contextual escalation: a budget increase above the threshold
        # should always be high regardless of the static mapping.
        if "budget_increase_pct" in proposed_changes:
            threshold = self._brand_policies.get(
                "max_budget_increase_pct", DEFAULT_MAX_BUDGET_INCREASE_PCT
            )
            if proposed_changes["budget_increase_pct"] > threshold:
                tier = "high"

        if "bid_increase_pct" in proposed_changes:
            paid_media_policy = self._brand_policies.get("paid_media_guardrails", {})
            threshold = paid_media_policy.get(
                "max_bid_increase_pct", DEFAULT_MAX_BID_INCREASE_PCT
            )
            if proposed_changes["bid_increase_pct"] > threshold:
                tier = "high"

        return tier

    # ------------------------------------------------------------------
    # Individual check dimensions
    # ------------------------------------------------------------------

    def check_budget_limits(
        self, action: dict[str, Any], brand_policy: dict[str, Any]
    ) -> dict[str, Any]:
        """Check if spend changes are within allowed limits.

        Looks at ``proposed_changes`` for ``budget_increase_pct`` and
        ``new_daily_budget``.
        """
        proposed = action.get("proposed_changes", {})
        increase_pct = proposed.get("budget_increase_pct")
        new_daily = proposed.get("new_daily_budget")

        max_increase = brand_policy.get(
            "max_budget_increase_pct", DEFAULT_MAX_BUDGET_INCREASE_PCT
        )
        max_daily = brand_policy.get("max_daily_budget")

        issues: list[str] = []

        if increase_pct is not None and increase_pct > max_increase:
            issues.append(
                f"Budget increase of {increase_pct}% exceeds "
                f"the allowed {max_increase}%"
            )

        if max_daily is not None and new_daily is not None and new_daily > max_daily:
            issues.append(
                f"Proposed daily budget ${new_daily} exceeds "
                f"the cap of ${max_daily}"
            )

        passed = len(issues) == 0
        detail = "; ".join(issues) if issues else "Budget within limits"
        result: dict[str, Any] = {
            "dimension": "budget_limits",
            "passed": passed,
            "detail": detail,
        }
        if not passed:
            result["escalate_to_high"] = True
        return result

    def check_content_compliance(self, action: dict[str, Any]) -> dict[str, Any]:
        """Check for regulated claims, banned words, and compliance issues.

        Scans all string values inside ``proposed_changes`` for:
        - Regulated-claim keywords (medical, financial, legal)
        - Banned marketing words (Tier 1)
        - Personal-attribute assertions (Meta ads policy)
        """
        proposed = action.get("proposed_changes", {})
        text_blob = _extract_text(proposed)

        if not text_blob:
            return {
                "dimension": "content_compliance",
                "passed": True,
                "detail": "No text content to check",
            }

        issues: list[str] = []
        text_lower = text_blob.lower()

        # Regulated claims
        for category, keywords in REGULATED_CLAIM_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw.lower()) + r"\b", text_lower):
                    issues.append(f"Regulated claim ({category}): '{kw}'")

        # Banned words
        extra_banned: list[str] = self._brand_policies.get("banned_words_extra", [])
        all_banned = BANNED_WORDS + extra_banned
        for word in all_banned:
            if re.search(r"\b" + re.escape(word.lower()) + r"\b", text_lower):
                issues.append(f"Banned word: '{word}'")

        # Personal-attribute patterns (Meta ads)
        channel = action.get("channel", "")
        if channel in ("social", "paid_media"):
            for pattern in PERSONAL_ATTRIBUTE_PATTERNS:
                if re.search(pattern, text_blob, re.IGNORECASE):
                    issues.append(
                        f"Personal attribute assertion (policy violation): "
                        f"matches pattern '{pattern}'"
                    )

        passed = len(issues) == 0
        detail = "; ".join(issues) if issues else "Content compliance clear"
        result: dict[str, Any] = {
            "dimension": "content_compliance",
            "passed": passed,
            "detail": detail,
        }
        if not passed:
            # Regulated claims always escalate to high
            if any("Regulated claim" in i for i in issues):
                result["escalate_to_high"] = True
        return result

    def check_channel_policy(self, action: dict[str, Any]) -> dict[str, Any]:
        """Check channel-specific platform policy rules.

        Validates that the brand is allowed to use this channel and that
        the action does not violate known channel constraints.
        """
        channel = action.get("channel", "")
        allowed = self._brand_policies.get("allowed_channels")

        issues: list[str] = []

        if allowed is not None and channel not in allowed:
            issues.append(
                f"Channel '{channel}' is not in the brand's allowed channels: "
                f"{allowed}"
            )

        # Platform-specific guardrails
        proposed = action.get("proposed_changes", {})
        text_blob = _extract_text(proposed)

        if channel == "paid_media" and text_blob:
            # Check for superlatives without proof (Google Ads policy)
            superlative_pattern = r"\b(best|#1|number one|top-rated|guaranteed)\b"
            if re.search(superlative_pattern, text_blob, re.IGNORECASE):
                if not proposed.get("proof_substantiation"):
                    issues.append(
                        "Superlative/guarantee claim without proof_substantiation"
                    )

        passed = len(issues) == 0
        detail = "; ".join(issues) if issues else "Channel policy clear"
        return {
            "dimension": "channel_policy",
            "passed": passed,
            "detail": detail,
        }

    def check_paid_media_guardrails(self, action: dict[str, Any]) -> dict[str, Any]:
        """Enforce paid-media write guardrails before live platform mutation.

        Read/evaluation actions pass through. Any paid-media mutation must
        provide a dry-run preview or diff, cite evidence, stay inside account
        allowlists, and avoid auto-approved execution. Budget and bid changes
        also need numeric before/after values and hard caps.
        """
        channel = action.get("channel", "")
        action_type = action.get("action_type", "")

        if channel != "paid_media":
            return {
                "dimension": "paid_media_guardrails",
                "passed": True,
                "detail": "Not a paid media action",
            }

        if action_type in PAID_MEDIA_READ_ONLY_ACTIONS:
            return {
                "dimension": "paid_media_guardrails",
                "passed": True,
                "detail": "Read-only paid media action",
            }

        if action_type not in PAID_MEDIA_MUTATION_ACTIONS:
            return {
                "dimension": "paid_media_guardrails",
                "passed": False,
                "detail": (
                    f"Unknown paid media action '{action_type}' is blocked "
                    "until classified as read-only or mutation"
                ),
                "escalate_to_high": True,
            }

        proposed = action.get("proposed_changes", {})
        metadata = action.get("metadata", {})
        guardrails = self._brand_policies.get("paid_media_guardrails", {})
        issues: list[str] = []

        approval_state = action.get("approval_state")
        if approval_state == "auto_approved":
            issues.append("Paid media mutations cannot be auto-approved")

        if _truthy(proposed.get("activate_on_create")):
            issues.append("Ads/campaigns must be created paused; activation is a separate approval")

        status = str(proposed.get("status") or proposed.get("target_status") or "").upper()
        if action_type in {
            "create_ad_creative",
            "create_paused_campaign",
            "create_paused_adset",
            "create_paused_ad",
            "upload_ad_asset",
        } and status == "ACTIVE":
            issues.append("Creation/upload actions cannot set ACTIVE status")

        if not _has_preview_or_diff(action):
            issues.append("Missing dry-run preview or before/after change diff")

        if not _has_evidence(action):
            issues.append("Missing evidence source for the recommendation")

        account_id = _first_present(action, proposed, metadata, "account_id", "ad_account_id")
        allowed_accounts = guardrails.get("allowed_accounts")
        if not allowed_accounts:
            issues.append("Missing paid_media_guardrails.allowed_accounts")
        elif account_id not in allowed_accounts:
            issues.append(f"Ad account '{account_id or '(missing)'}' is not allowlisted")

        for field, policy_key in (
            ("campaign_id", "allowed_campaigns"),
            ("adset_id", "allowed_adsets"),
            ("ad_group_id", "allowed_ad_groups"),
        ):
            entity_id = _first_present(action, proposed, metadata, field)
            allowlist = guardrails.get(policy_key)
            if entity_id and allowlist is not None and entity_id not in allowlist:
                issues.append(f"{field} '{entity_id}' is not in {policy_key}")

        if _execution_requested(action) and action_type in PAID_MEDIA_MUTATION_ACTIONS:
            approval_id = _first_present(action, proposed, metadata, "approval_id", "approval-id")
            if not approval_id:
                issues.append("Live paid media mutations require approval_id")

        if action_type in PAID_MEDIA_SPEND_ACTIONS:
            issues.extend(self._paid_media_spend_issues(action, guardrails))

        requires_rollback = guardrails.get("require_rollback_for_activation", True)
        if requires_rollback and action_type in {
            "activate_campaign",
            "activate_adset",
            "activate_ad",
            "launch_campaign",
            "pause_campaign",
            "pause_adset",
            "pause_ad",
        }:
            rollback = action.get("rollback_reference") or proposed.get("rollback_reference")
            if not rollback:
                issues.append("Missing rollback_reference for activation/pause action")

        passed = len(issues) == 0
        result: dict[str, Any] = {
            "dimension": "paid_media_guardrails",
            "passed": passed,
            "detail": "; ".join(issues) if issues else "Paid media guardrails clear",
        }
        if not passed and action_type in PAID_MEDIA_SPEND_ACTIONS:
            result["escalate_to_high"] = True
        return result

    def _paid_media_spend_issues(
        self,
        action: dict[str, Any],
        guardrails: dict[str, Any],
    ) -> list[str]:
        proposed = action.get("proposed_changes", {})
        issues: list[str] = []

        max_daily = guardrails.get("max_daily_budget", self._brand_policies.get("max_daily_budget"))
        max_budget_increase = guardrails.get(
            "max_budget_increase_pct",
            self._brand_policies.get("max_budget_increase_pct", DEFAULT_MAX_BUDGET_INCREASE_PCT),
        )
        max_single_change = guardrails.get(
            "max_single_budget_change_usd",
            DEFAULT_MAX_SINGLE_BUDGET_CHANGE_USD,
        )
        max_bid_increase = guardrails.get(
            "max_bid_increase_pct",
            DEFAULT_MAX_BID_INCREASE_PCT,
        )

        action_type = action.get("action_type")

        if action_type in PAID_MEDIA_BUDGET_ACTIONS:
            current_daily = _to_float(proposed.get("current_daily_budget"))
            new_daily = _to_float(proposed.get("new_daily_budget"))
            increase_pct = _to_float(proposed.get("budget_increase_pct"))
            direction = str(proposed.get("direction") or "").lower()

            if current_daily is None or new_daily is None:
                issues.append("Budget changes require current_daily_budget and new_daily_budget")
            else:
                if action_type == "increase_budget" and new_daily <= current_daily:
                    issues.append("increase_budget must raise new_daily_budget above current_daily_budget")
                if action_type == "reduce_budget" and new_daily >= current_daily:
                    issues.append("reduce_budget must lower new_daily_budget below current_daily_budget")
                if direction == "increase" and new_daily <= current_daily:
                    issues.append("Budget direction=increase must raise the daily budget")
                if direction in {"reduce", "decrease"} and new_daily >= current_daily:
                    issues.append("Budget direction=reduce must lower the daily budget")

                single_change = abs(new_daily - current_daily)
                if single_change > max_single_change:
                    issues.append(
                        f"Budget change ${single_change:g} exceeds per-change cap ${max_single_change:g}"
                    )
                if max_daily is not None and new_daily > float(max_daily):
                    issues.append(
                        f"New daily budget ${new_daily:g} exceeds cap ${float(max_daily):g}"
                    )
                if new_daily > current_daily and increase_pct is None and current_daily > 0:
                    increase_pct = ((new_daily - current_daily) / current_daily) * 100
                if new_daily < current_daily:
                    max_reduction_pct = guardrails.get("max_budget_reduction_pct", 50.0)
                    reduction_pct = ((current_daily - new_daily) / current_daily) * 100 if current_daily > 0 else 0
                    if reduction_pct > max_reduction_pct:
                        issues.append(
                            f"Budget reduction {reduction_pct:g}% exceeds cap {max_reduction_pct:g}%"
                        )

            if increase_pct is not None and increase_pct > max_budget_increase:
                issues.append(
                    f"Budget increase {increase_pct:g}% exceeds cap {max_budget_increase:g}%"
                )

        if action_type in PAID_MEDIA_BID_ACTIONS:
            current_bid = _to_float(proposed.get("current_bid"))
            new_bid = _to_float(proposed.get("new_bid"))
            increase_pct = _to_float(proposed.get("bid_increase_pct"))

            if current_bid is None or new_bid is None:
                issues.append("Bid changes require current_bid and new_bid")
            else:
                if action_type == "increase_bid" and new_bid <= current_bid:
                    issues.append("increase_bid must raise new_bid above current_bid")
                if action_type == "reduce_bid" and new_bid >= current_bid:
                    issues.append("reduce_bid must lower new_bid below current_bid")
                if new_bid > current_bid and increase_pct is None and current_bid > 0:
                    increase_pct = ((new_bid - current_bid) / current_bid) * 100

            if increase_pct is not None and increase_pct > max_bid_increase:
                issues.append(
                    f"Bid increase {increase_pct:g}% exceeds cap {max_bid_increase:g}%"
                )

        if action_type in {"change_bid_strategy", "adjust_target_cpa", "adjust_target_roas"}:
            before = proposed.get("current_bid_strategy") or proposed.get("current_target")
            after = proposed.get("new_bid_strategy") or proposed.get("new_target")
            if before in (None, "") or after in (None, ""):
                issues.append(f"{action_type} requires current and proposed bid strategy/target values")

        return issues

    def check_frequency_limits(self, action: dict[str, Any]) -> dict[str, Any]:
        """Check if action exceeds rate limits for the channel.

        Uses ``proposed_changes.actions_today`` to compare against the
        per-channel frequency cap. The engine itself is stateless -- the
        caller must supply the count.
        """
        channel = action.get("channel", "")
        actions_today = action.get("proposed_changes", {}).get("actions_today")

        brand_freq = self._brand_policies.get("frequency_limits", {})
        limit = brand_freq.get(channel, DEFAULT_FREQUENCY_LIMITS.get(channel))

        if actions_today is not None and limit is not None and actions_today >= limit:
            return {
                "dimension": "frequency_limits",
                "passed": False,
                "detail": (
                    f"Channel '{channel}' has reached {actions_today} actions "
                    f"today (limit: {limit})"
                ),
            }

        return {
            "dimension": "frequency_limits",
            "passed": True,
            "detail": "Within frequency limits",
        }

    def check_brand_constraints(
        self, action: dict[str, Any], brand_policy: dict[str, Any]
    ) -> dict[str, Any]:
        """Check brand voice, offer, and messaging constraints.

        Validates:
        - ``required_disclaimer``: if the brand requires a disclaimer in all
          ad/email copy, check it is present.
        - ``blocked_topics``: topics that must never appear in any content.
        """
        proposed = action.get("proposed_changes", {})
        text_blob = _extract_text(proposed)
        issues: list[str] = []

        # Required disclaimer
        disclaimer = brand_policy.get("required_disclaimer")
        if disclaimer and text_blob and disclaimer.lower() not in text_blob.lower():
            issues.append(
                f"Required brand disclaimer missing: '{disclaimer}'"
            )

        # Blocked topics
        blocked: list[str] = brand_policy.get("blocked_topics", [])
        if text_blob:
            text_lower = text_blob.lower()
            for topic in blocked:
                if topic.lower() in text_lower:
                    issues.append(f"Blocked topic found: '{topic}'")

        passed = len(issues) == 0
        detail = "; ".join(issues) if issues else "Brand constraints clear"
        return {
            "dimension": "brand_constraints",
            "passed": passed,
            "detail": detail,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_text(data: Any, _depth: int = 0) -> str:
    """Recursively extract all string values from a dict/list structure."""
    if _depth > 10:
        return ""
    parts: list[str] = []
    if isinstance(data, str):
        parts.append(data)
    elif isinstance(data, dict):
        for v in data.values():
            parts.append(_extract_text(v, _depth + 1))
    elif isinstance(data, (list, tuple)):
        for item in data:
            parts.append(_extract_text(item, _depth + 1))
    return " ".join(p for p in parts if p)


def _truthy(value: Any) -> bool:
    """Return True for common truthy bool/string values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _to_float(value: Any) -> Optional[float]:
    """Convert a numeric input to float, returning None when absent/invalid."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_present(
    action: dict[str, Any],
    proposed: dict[str, Any],
    metadata: dict[str, Any],
    *keys: str,
) -> Any:
    """Find the first non-empty value across action, proposed changes, metadata."""
    for source in (proposed, metadata, action):
        for key in keys:
            value = source.get(key)
            if value not in (None, ""):
                return value
    return None


def _has_preview_or_diff(action: dict[str, Any]) -> bool:
    proposed = action.get("proposed_changes", {})
    preview = action.get("preview_artifact") or proposed.get("dry_run_preview")
    diff = proposed.get("change_diff") or proposed.get("before_after_diff")
    return bool(preview or diff)


def _has_evidence(action: dict[str, Any]) -> bool:
    evidence = action.get("evidence") or []
    if not evidence:
        return False
    for item in evidence:
        if not isinstance(item, dict):
            continue
        if item.get("source") or item.get("collector") or item.get("path") or item.get("url"):
            return True
    return False


def _execution_requested(action: dict[str, Any]) -> bool:
    metadata = action.get("metadata", {})
    return _truthy(
        action.get("execute")
        or action.get("execution_requested")
        or metadata.get("execute")
        or metadata.get("execution_requested")
        or metadata.get("live_mutation")
    )
