"""Base models for the Kai compliance policy pack system.

Defines PolicyRule, PolicyPack, PolicyRegistry, and supporting enums.
Uses the dataclass + SerializableModel pattern from kai.runtime.models.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Serialization helper (matches kai.runtime.models.SerializableModel)
# ---------------------------------------------------------------------------

class SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RuleSeverity(str, Enum):
    """How severe a policy violation is.

    * violation      -- must be fixed before publishing; creates legal/platform risk
    * warning        -- should be fixed; creates compliance risk but may not be
                        immediately actionable
    * recommendation -- best practice; suggested but not strictly required
    """

    violation = "violation"
    warning = "warning"
    recommendation = "recommendation"


class ContentType(str, Enum):
    """Content formats that policy rules may apply to."""

    website_page = "website_page"
    landing_page = "landing_page"
    blog_post = "blog_post"
    social_post = "social_post"
    social_story = "social_story"
    paid_ad = "paid_ad"
    email_marketing = "email_marketing"
    email_transactional = "email_transactional"
    press_release = "press_release"
    video_script = "video_script"
    podcast_script = "podcast_script"
    case_study = "case_study"
    testimonial = "testimonial"
    review_response = "review_response"


# ---------------------------------------------------------------------------
# PolicyRule
# ---------------------------------------------------------------------------

@dataclass
class PolicyRule(SerializableModel):
    """A single compliance rule inside a policy pack.

    Every rule carries enough metadata for the compliance engine to decide
    whether to apply it to a given piece of content and, if the rule fires,
    to tell the author exactly what to fix.
    """

    rule_id: str
    """Unique identifier, e.g. 'website_accessibility_001'."""

    pack: str
    """Which policy pack this rule belongs to ('website', 'social', 'paid_media', 'email', 'analytics')."""

    category: str
    """Grouping within the pack, e.g. 'accessibility', 'privacy', 'disclosure'."""

    description: str
    """What this rule requires (1-2 sentences)."""

    check_function_name: str
    """Name of the function that would programmatically check this rule."""

    severity: str
    """RuleSeverity enum value ('violation', 'warning', 'recommendation')."""

    applicable_content_types: List[str] = field(default_factory=list)
    """Which ContentType values this rule applies to."""

    applicable_regions: List[str] = field(default_factory=list)
    """ISO country codes where this rule applies.  Empty list means global."""

    applicable_industries: List[str] = field(default_factory=list)
    """Industry slugs where this rule applies.  Empty list means all industries."""

    regulatory_source: Optional[str] = None
    """Which law / regulation / policy this derives from (e.g. 'ADA', 'GDPR')."""

    fix_guidance: str = ""
    """What to do if the rule is violated."""

    examples: List[Dict[str, str]] = field(default_factory=list)
    """List of {violation: str, correction: str} example pairs."""


# ---------------------------------------------------------------------------
# PolicyPack
# ---------------------------------------------------------------------------

@dataclass
class PolicyPack(SerializableModel):
    """A named collection of PolicyRules covering a single compliance domain.

    Typical packs: website, social, paid_media, email, analytics.
    """

    pack_name: str
    description: str
    rules: List[PolicyRule] = field(default_factory=list)

    # -- query helpers -----------------------------------------------------

    def get_rules_for_content_type(self, content_type: str) -> List[PolicyRule]:
        """Return rules that apply to *content_type* (or have no content-type filter)."""
        return [
            r for r in self.rules
            if not r.applicable_content_types or content_type in r.applicable_content_types
        ]

    def get_rules_for_region(self, region: str) -> List[PolicyRule]:
        """Return rules that apply to *region* (including global rules with no region filter)."""
        return [
            r for r in self.rules
            if not r.applicable_regions or region in r.applicable_regions
        ]

    def get_rules_for_industry(self, industry: str) -> List[PolicyRule]:
        """Return rules that apply to *industry* (including universal rules with no industry filter)."""
        return [
            r for r in self.rules
            if not r.applicable_industries or industry in r.applicable_industries
        ]

    def get_rules_by_severity(self, severity: str) -> List[PolicyRule]:
        """Return rules matching the given severity level."""
        return [r for r in self.rules if r.severity == severity]


# ---------------------------------------------------------------------------
# PolicyRegistry
# ---------------------------------------------------------------------------

class PolicyRegistry:
    """Central registry of all loaded PolicyPacks.

    Use ``register()`` to add packs and ``get_applicable_rules()`` to query
    across all packs at once.
    """

    def __init__(self) -> None:
        self._packs: Dict[str, PolicyPack] = {}

    # -- registration ------------------------------------------------------

    def register(self, pack: PolicyPack) -> None:
        """Add a policy pack to the registry (keyed by pack_name)."""
        self._packs[pack.pack_name] = pack

    # -- retrieval ---------------------------------------------------------

    def get_pack(self, pack_name: str) -> Optional[PolicyPack]:
        """Retrieve a single pack by name, or ``None`` if not registered."""
        return self._packs.get(pack_name)

    def get_all_rules(self) -> List[PolicyRule]:
        """Return every rule across every registered pack."""
        rules: List[PolicyRule] = []
        for pack in self._packs.values():
            rules.extend(pack.rules)
        return rules

    def get_applicable_rules(
        self,
        content_type: str,
        platform: Optional[str] = None,
        region: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> List[PolicyRule]:
        """Return rules that match the given filters.

        Parameters
        ----------
        content_type:
            Required.  The ContentType value to filter on.
        platform:
            Optional pack name (e.g. 'paid_media', 'social') to limit to a
            single pack.  When ``None``, all packs are searched.
        region:
            Optional ISO country code.  Global rules are always included.
        industry:
            Optional industry slug.  Universal rules are always included.
        """
        candidates: List[PolicyRule] = []

        if platform:
            pack = self._packs.get(platform)
            if pack:
                candidates = list(pack.rules)
        else:
            candidates = self.get_all_rules()

        results: List[PolicyRule] = []
        for rule in candidates:
            # Content-type filter
            if rule.applicable_content_types and content_type not in rule.applicable_content_types:
                continue
            # Region filter
            if region and rule.applicable_regions and region not in rule.applicable_regions:
                continue
            # Industry filter
            if industry and rule.applicable_industries and industry not in rule.applicable_industries:
                continue
            results.append(rule)

        return results
