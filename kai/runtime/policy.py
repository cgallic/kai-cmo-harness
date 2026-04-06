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
    ("paid_media", "publish_approved_variant"): "low",
    ("paid_media", "create_ad_creative"): "medium",
    ("paid_media", "adjust_bidding"): "medium",
    ("paid_media", "adjust_budget"): "high",
    ("paid_media", "pause_campaign"): "high",
    ("paid_media", "launch_campaign"): "high",
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
        auto_eligible = (
            risk_tier == "low"
            and all_checks_passed
            and self._brand_policies.get("auto_execute_low_risk", True)
        )
        requires_approval = risk_tier in ("medium", "high") or not all_checks_passed

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
