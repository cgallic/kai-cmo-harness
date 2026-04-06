"""Kai compliance engine.

Evaluates marketing content against applicable policy rules from the
PolicyRegistry (Task 061) and produces structured ComplianceResult objects
with pass/fail status, specific violations, and fix suggestions.

The engine is the automated gatekeeper invoked by the creative QA pipeline
(Task 031), the approval router (Task 064), and the watcher system
(Task 067).  It catches policy violations before content reaches the
platform -- preventing ad disapprovals, regulatory fines, and brand damage.

Usage::

    from kai.compliance.policy_packs import default_registry
    from kai.compliance.engine import ComplianceEngine, ContentForReview

    engine = ComplianceEngine(default_registry)
    content = ContentForReview(
        content_type="paid_ad",
        platform="meta",
        body="Are you struggling with debt? We can help!",
        claims=["#1 rated debt relief service"],
        industry="finance",
        region="US",
    )
    result = engine.check_compliance(content)
    print(result.status)   # "fail"
    print(result.summary)  # "2 violations found: ..."
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .policy_packs.base import PolicyPack, PolicyRegistry, PolicyRule

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Serialization helper (matches kai.runtime.models.SerializableModel)
# ---------------------------------------------------------------------------


class SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ComplianceStatus(str, Enum):
    """Overall result of a compliance check.

    * pass_    -- all rules pass, content is safe to publish
    * fail     -- one or more violation-severity rules failed
    * warning  -- no violations but one or more warnings exist
    * error    -- could not evaluate (missing data, engine error)

    Note: ``pass`` is a Python keyword so the enum member is ``pass_``
    but its *value* is the string ``"pass"`` for serialization.
    """

    pass_ = "pass"
    fail = "fail"
    warning = "warning"
    error = "error"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass
class Violation(SerializableModel):
    """A single policy violation, warning, or recommendation."""

    rule_id: str
    """Which PolicyRule was violated."""

    severity: str
    """One of 'violation', 'warning', 'recommendation'."""

    description: str
    """Human-readable description of the violation."""

    content_snippet: Optional[str] = None
    """The specific part of the content that triggered the violation (max 200 chars)."""

    fix_suggestion: str = ""
    """What to do to fix it."""

    regulatory_reference: Optional[str] = None
    """E.g. 'CAN-SPAM Act, 15 U.S.C. 7701'."""

    auto_fixable: bool = False
    """Whether the system can attempt to fix this automatically."""

    fix_template: Optional[str] = None
    """Template for auto-fix if applicable."""


@dataclass
class RequiredDisclosure(SerializableModel):
    """A disclosure that must be included in the content before publishing."""

    disclosure_type: str
    """E.g. 'unsubscribe_link', 'physical_address', 'sponsored_tag', 'results_disclaimer'."""

    disclosure_text: str
    """The actual text that must be included."""

    placement: str
    """Where it must appear: 'header', 'footer', 'inline', 'beginning', 'end'."""

    source_rule_id: str
    """Which rule requires this."""


@dataclass
class ComplianceResult(SerializableModel):
    """The full result of a compliance check on a piece of content."""

    id: str
    """Format ``comp_{uuid_hex[:12]}``."""

    status: str
    """ComplianceStatus enum value."""

    content_type: str
    """What was checked."""

    platform: Optional[str] = None
    """Target platform if applicable."""

    industry: Optional[str] = None
    """Business industry."""

    region: Optional[str] = None
    """Target region."""

    checked_at: str = ""
    """ISO timestamp."""

    total_rules_checked: int = 0

    violations: List[Violation] = field(default_factory=list)
    """Violation-severity failures."""

    warnings: List[Violation] = field(default_factory=list)
    """Warning-severity issues."""

    recommendations: List[Violation] = field(default_factory=list)
    """Recommendation-severity suggestions."""

    required_disclosures: List[RequiredDisclosure] = field(default_factory=list)
    """Disclosures that must be included."""

    required_modifications: List[str] = field(default_factory=list)
    """Specific changes needed before publishing."""

    summary: str = ""
    """One-sentence summary."""


@dataclass
class ContentForReview(SerializableModel):
    """Content submitted to the compliance engine for evaluation."""

    content_type: str
    """ContentType enum value from policy_packs."""

    body: str
    """Main content text."""

    platform: Optional[str] = None
    """Target platform (e.g. 'google_ads', 'meta', 'email')."""

    headline: Optional[str] = None
    cta: Optional[str] = None

    image_description: Optional[str] = None
    """Description of visual content if any."""

    landing_page_url: Optional[str] = None

    target_audience: Optional[str] = None
    """Audience description for audience-restriction checks."""

    claims: List[str] = field(default_factory=list)
    """Explicit claims made in the content."""

    industry: Optional[str] = None
    region: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pattern constants used by check methods
# ---------------------------------------------------------------------------

# Superlative / results-claim patterns
_SUPERLATIVE_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\b(?:the\s+)?best\b", re.IGNORECASE),
    re.compile(r"\b#\s*1\b", re.IGNORECASE),
    re.compile(r"\bnumber\s+one\b", re.IGNORECASE),
    re.compile(r"\bfastest\b", re.IGNORECASE),
    re.compile(r"\bcheapest\b", re.IGNORECASE),
    re.compile(r"\btop[\s-]rated\b", re.IGNORECASE),
    re.compile(r"\bworld[\s']?s?\s+(?:leading|first|largest|best)\b", re.IGNORECASE),
    re.compile(r"\bguaranteed\s+results?\b", re.IGNORECASE),
    re.compile(r"\b100\s*%\s+(?:guaranteed|satisfaction|success|effective)\b", re.IGNORECASE),
    re.compile(r"\bproven\s+results?\b", re.IGNORECASE),
]

_RESULTS_CLAIM_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\b(?:lose|lost)\s+\d+\s*(?:lbs?|kg|pounds|kilos)\b", re.IGNORECASE),
    re.compile(r"\b(?:earn|made|make|save)\s+\$[\d,]+\b", re.IGNORECASE),
    re.compile(r"\b\d+[xX]\s+(?:ROI|return|growth|increase|more)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*%\s+(?:increase|decrease|growth|reduction|more|less|improvement|boost)\b", re.IGNORECASE),
    re.compile(r"\bin\s+(?:just\s+)?\d+\s+(?:days?|weeks?|hours?|minutes?)\b", re.IGNORECASE),
]

# Meta personal-attributes patterns (second-person questions or assertions about
# personal characteristics)
_PERSONAL_ATTRIBUTE_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\bare\s+you\s+(?:struggling|suffering|overweight|depressed|anxious|lonely|broke|in\s+debt|divorced|disabled|sick|ill|obese|unemployed|addicted)\b", re.IGNORECASE),
    re.compile(r"\bdo\s+you\s+(?:have|suffer|struggle|feel|need|want)\b", re.IGNORECASE),
    re.compile(r"\byou(?:'re|r)\s+(?:overweight|depressed|anxious|broke|in\s+debt|stressed|lonely|sick|struggling|suffering)\b", re.IGNORECASE),
    re.compile(r"\bif\s+you(?:'re|r)\s+(?:a\s+)?(?:single\s+(?:mom|dad|parent)|veteran|senior|minority|immigrant|disabled|diabetic|cancer)\b", re.IGNORECASE),
    re.compile(r"\bas\s+a\s+(?:single\s+(?:mom|dad|parent)|veteran|senior|minority|immigrant|person\s+(?:of\s+color|with\s+a?\s+disabilit))\b", re.IGNORECASE),
    re.compile(r"\byour\s+(?:race|ethnicity|religion|sexual\s+orientation|gender\s+identity|disability|medical\s+condition|health\s+condition|criminal\s+record|financial\s+(?:status|situation|problems?|difficulties?))\b", re.IGNORECASE),
]

# Before/after patterns
_BEFORE_AFTER_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\bbefore\s+(?:and|&|\/)\s*after\b", re.IGNORECASE),
    re.compile(r"\btransformation\s+(?:photo|image|picture|pic|result)\b", re.IGNORECASE),
    re.compile(r"\b(?:lost|dropped)\s+\d+\s*(?:lbs?|kg|pounds?|sizes?)\b", re.IGNORECASE),
    re.compile(r"\b(?:before|after)\s+(?:photo|image|picture|pic|shot|using)\b", re.IGNORECASE),
]

# Special Ad Category keywords (Meta housing/employment/credit)
_HOUSING_KEYWORDS: List[re.Pattern[str]] = [
    re.compile(r"\b(?:apartment|condo|house|home|rent|lease|mortgage|real\s+estate|housing|roommate|property\s+(?:for\s+(?:sale|rent|lease)))\b", re.IGNORECASE),
]
_EMPLOYMENT_KEYWORDS: List[re.Pattern[str]] = [
    re.compile(r"\b(?:job|hiring|career|employment|apply\s+now|we(?:'re|\s+are)\s+hiring|open\s+(?:position|role)|join\s+our\s+team|work\s+(?:from\s+home|with\s+us)|remote\s+(?:job|position|role|work))\b", re.IGNORECASE),
]
_CREDIT_KEYWORDS: List[re.Pattern[str]] = [
    re.compile(r"\b(?:credit\s+(?:card|score|offer|limit|line)|loan|lending|mortgage|refinance|debt\s+consolidation|APR|interest\s+rate|auto\s+financing)\b", re.IGNORECASE),
]

# Misleading subject line patterns
_MISLEADING_SUBJECT_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"^Re:\s", re.IGNORECASE),
    re.compile(r"^Fwd?:\s", re.IGNORECASE),
    re.compile(r"\baction\s+required\b", re.IGNORECASE),
    re.compile(r"\baccount\s+(?:suspended|terminated|closed|locked|alert|warning|notification)\b", re.IGNORECASE),
    re.compile(r"\byour\s+(?:invoice|receipt|order|payment|statement)\b", re.IGNORECASE),
    re.compile(r"\byou(?:'ve|r)?\s+(?:won|been\s+selected|been\s+chosen)\b", re.IGNORECASE),
]

# Platform-specific banned word lists
_PLATFORM_BANNED_WORDS: Dict[str, List[re.Pattern[str]]] = {
    "google_ads": [
        re.compile(r"\bclick\s+here\b", re.IGNORECASE),
        re.compile(r"\b(?:!!!|!!!)\b"),
        re.compile(r"(?:ALL\s+CAPS\s+){2,}"),
        re.compile(r"\bfree\s+(?:money|cash|gift)\b", re.IGNORECASE),
    ],
    "meta": [
        re.compile(r"\b(?:Facebook|FB)\s+(?:approved|official|endorsed)\b", re.IGNORECASE),
        re.compile(r"\bMeta\s+(?:approved|official|endorsed)\b", re.IGNORECASE),
    ],
    "tiktok": [
        re.compile(r"\b(?:political|election|vote\s+for|ballot|candidate)\b", re.IGNORECASE),
    ],
    "linkedin": [
        re.compile(r"\b(?:INSANE|CRAZY|UNBELIEVABLE|OMG|WTF)\b", re.IGNORECASE),
    ],
    "_global": [
        re.compile(r"\b(?:miracle|cure[\s-]all|magic\s+pill|get\s+rich\s+quick)\b", re.IGNORECASE),
        re.compile(r"\b(?:risk[\s-]free|no[\s-]risk|zero[\s-]risk)\b", re.IGNORECASE),
        re.compile(r"\bact\s+now\s+or\s+(?:lose|miss)\b", re.IGNORECASE),
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _truncate_snippet(text: str, max_len: int = 200) -> str:
    """Return *text* truncated to *max_len* chars with an ellipsis if cut."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _all_text(content: ContentForReview) -> str:
    """Concatenate all textual fields of *content* for broad searches."""
    parts: List[str] = []
    if content.headline:
        parts.append(content.headline)
    parts.append(content.body)
    if content.cta:
        parts.append(content.cta)
    return " ".join(parts)


def _generate_id() -> str:
    """Generate a ``comp_<12-hex-chars>`` compliance result id."""
    return f"comp_{uuid.uuid4().hex[:12]}"


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# ComplianceEngine
# ---------------------------------------------------------------------------


class ComplianceEngine:
    """Evaluate marketing content against applicable compliance rules.

    Parameters
    ----------
    registry:
        The :class:`PolicyRegistry` containing all loaded policy packs.
        Typically ``default_registry`` from :mod:`kai.compliance.policy_packs`.
    """

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

        # Map check_function_name -> bound method so _evaluate_rule can
        # dispatch dynamically without brittle if/elif chains.
        self._check_dispatch: Dict[str, Callable[..., Optional[Violation]]] = {
            # Core nine check methods
            "check_banned_words": self._check_banned_words,
            "check_claims_substantiation": self._check_claims_substantiation,
            "check_meta_personal_attributes": self._check_personal_attributes,
            "check_personal_attributes": self._check_personal_attributes,
            "check_meta_before_after_images": self._check_before_after,
            "check_before_after": self._check_before_after,
            "check_meta_special_ad_category": self._check_special_ad_category,
            "check_special_ad_category": self._check_special_ad_category,
            "check_disclosure_present": self._check_disclosure_present,
            "check_unsubscribe_link": self._check_unsubscribe_link,
            "check_physical_address_present": self._check_physical_address,
            "check_physical_address": self._check_physical_address,
            "check_subject_line_accuracy": self._check_misleading_subject,
            "check_misleading_subject": self._check_misleading_subject,

            # Aliases used by specific policy-pack rules
            "check_google_superlative_claims": self._check_claims_substantiation,
            "check_linkedin_claim_substantiation": self._check_claims_substantiation,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_compliance(self, content: ContentForReview) -> ComplianceResult:
        """Run all applicable rules against *content* and return a structured result.

        Steps:
        1. Determine applicable rules from the registry based on content fields.
        2. Append industry-specific rules if *content.industry* is set.
        3. Evaluate each rule, collecting violations/warnings/recommendations.
        4. Determine required disclosures.
        5. Set status and generate a summary string.
        """
        # 1. Gather applicable rules from the registry ------------------
        applicable_rules = self._registry.get_applicable_rules(
            content_type=content.content_type,
            platform=content.platform,
            region=content.region,
            industry=content.industry,
        )

        # 2. Merge in industry-specific rules ---------------------------
        if content.industry:
            industry_rules = get_industry_rules(content.industry)
            # Deduplicate by rule_id
            existing_ids = {r.rule_id for r in applicable_rules}
            for rule in industry_rules:
                if rule.rule_id not in existing_ids:
                    applicable_rules.append(rule)
                    existing_ids.add(rule.rule_id)

        # 3. Evaluate each rule -----------------------------------------
        violations: List[Violation] = []
        warnings: List[Violation] = []
        recommendations: List[Violation] = []

        for rule in applicable_rules:
            result = self._evaluate_rule(rule, content)
            if result is None:
                continue  # rule passed
            if result.severity == "violation":
                violations.append(result)
            elif result.severity == "warning":
                warnings.append(result)
            else:
                recommendations.append(result)

        # 4. Required disclosures ---------------------------------------
        required_disclosures = self._get_required_disclosures(applicable_rules, content)

        # Check that each required disclosure is actually present; if not,
        # add a violation.
        for disclosure in required_disclosures:
            disc_violation = self._check_disclosure_present(
                content,
                required_disclosure=disclosure.disclosure_text,
                disclosure_obj=disclosure,
            )
            if disc_violation is not None:
                # Avoid duplicates if a specific rule already caught this
                if not any(v.rule_id == disc_violation.rule_id for v in violations):
                    violations.append(disc_violation)

        # 5. Required modifications list --------------------------------
        required_modifications: List[str] = []
        for v in violations:
            if v.fix_suggestion:
                required_modifications.append(v.fix_suggestion)

        # 6. Determine status -------------------------------------------
        if violations:
            status = ComplianceStatus.fail.value
        elif warnings:
            status = ComplianceStatus.warning.value
        else:
            status = ComplianceStatus.pass_.value

        # 7. Generate summary -------------------------------------------
        summary = self._build_summary(violations, warnings, recommendations)

        return ComplianceResult(
            id=_generate_id(),
            status=status,
            content_type=content.content_type,
            platform=content.platform,
            industry=content.industry,
            region=content.region,
            checked_at=_now_iso(),
            total_rules_checked=len(applicable_rules),
            violations=violations,
            warnings=warnings,
            recommendations=recommendations,
            required_disclosures=required_disclosures,
            required_modifications=required_modifications,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Rule evaluation dispatcher
    # ------------------------------------------------------------------

    def _evaluate_rule(
        self, rule: PolicyRule, content: ContentForReview
    ) -> Optional[Violation]:
        """Dispatch to the appropriate check method based on *rule.check_function_name*.

        Returns a :class:`Violation` if the rule fails, ``None`` if it passes.
        If the check function name is not implemented, log a debug message and
        skip -- never crash.
        """
        check_fn = self._check_dispatch.get(rule.check_function_name)
        if check_fn is None:
            logger.debug(
                "No check implementation for '%s' (rule %s) -- skipping.",
                rule.check_function_name,
                rule.rule_id,
            )
            return None

        try:
            violation = check_fn(content, _rule=rule)
            return violation
        except Exception:
            logger.exception(
                "Error evaluating rule %s (check: %s). Skipping.",
                rule.rule_id,
                rule.check_function_name,
            )
            return None

    # ------------------------------------------------------------------
    # Required disclosures
    # ------------------------------------------------------------------

    def _get_required_disclosures(
        self,
        applicable_rules: List[PolicyRule],
        content: ContentForReview,
    ) -> List[RequiredDisclosure]:
        """Determine which disclosures are required based on content type, platform, and rules."""
        disclosures: List[RequiredDisclosure] = []

        ct = content.content_type
        platform = (content.platform or "").lower()

        # -- Email (CAN-SPAM) disclosures --------------------------------
        if ct in ("email_marketing",):
            disclosures.append(
                RequiredDisclosure(
                    disclosure_type="unsubscribe_link",
                    disclosure_text="Unsubscribe",
                    placement="footer",
                    source_rule_id="email_canspam_002",
                )
            )
            disclosures.append(
                RequiredDisclosure(
                    disclosure_type="physical_address",
                    disclosure_text="[Physical mailing address]",
                    placement="footer",
                    source_rule_id="email_canspam_001",
                )
            )
            disclosures.append(
                RequiredDisclosure(
                    disclosure_type="sender_identification",
                    disclosure_text="[Business name and contact information]",
                    placement="header",
                    source_rule_id="email_canspam_005",
                )
            )

        # -- Social / Sponsored disclosures (FTC) -----------------------
        if ct in ("social_post", "social_story") and content.metadata.get("sponsored"):
            disclosures.append(
                RequiredDisclosure(
                    disclosure_type="sponsored_tag",
                    disclosure_text="#ad",
                    placement="beginning",
                    source_rule_id="paid_media_general_001",
                )
            )

        # -- Paid ad disclosures ----------------------------------------
        if ct == "paid_ad":
            # FTC endorsement disclosure for influencer/sponsored content
            if content.metadata.get("influencer") or content.metadata.get("sponsored"):
                disclosures.append(
                    RequiredDisclosure(
                        disclosure_type="sponsored_tag",
                        disclosure_text="Ad" if platform != "tiktok" else "#ad",
                        placement="beginning",
                        source_rule_id="paid_media_general_001",
                    )
                )

            # TikTok AI content disclosure
            if platform == "tiktok" and content.metadata.get("ai_generated"):
                disclosures.append(
                    RequiredDisclosure(
                        disclosure_type="ai_content_label",
                        disclosure_text="Created with AI tools",
                        placement="inline",
                        source_rule_id="paid_media_tiktok_003",
                    )
                )

        # -- Results disclaimer for specific industries ------------------
        if content.industry in ("finance", "lending", "insurance", "investment"):
            disclosures.append(
                RequiredDisclosure(
                    disclosure_type="results_disclaimer",
                    disclosure_text="Past performance does not guarantee future results.",
                    placement="footer",
                    source_rule_id="industry_financial_002",
                )
            )
        if content.industry in ("healthcare", "pharma", "medical", "health"):
            disclosures.append(
                RequiredDisclosure(
                    disclosure_type="results_disclaimer",
                    disclosure_text=(
                        "Results may vary. This information is not intended as "
                        "medical advice. Consult your healthcare provider."
                    ),
                    placement="footer",
                    source_rule_id="industry_healthcare_001",
                )
            )
        if content.industry in ("legal", "law"):
            disclosures.append(
                RequiredDisclosure(
                    disclosure_type="results_disclaimer",
                    disclosure_text=(
                        "Prior results do not guarantee a similar outcome. "
                        "This is not legal advice."
                    ),
                    placement="footer",
                    source_rule_id="industry_legal_001",
                )
            )
        if content.industry in ("real_estate",):
            disclosures.append(
                RequiredDisclosure(
                    disclosure_type="equal_opportunity",
                    disclosure_text="Equal Housing Opportunity",
                    placement="footer",
                    source_rule_id="industry_real_estate_002",
                )
            )
        if content.industry in ("alcohol", "cannabis", "alcohol_cannabis"):
            disclosures.append(
                RequiredDisclosure(
                    disclosure_type="age_gate",
                    disclosure_text="Must be 21+ to purchase. Please drink responsibly.",
                    placement="footer",
                    source_rule_id="industry_alcohol_cannabis_001",
                )
            )

        return disclosures

    # ------------------------------------------------------------------
    # Summary builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(
        violations: List[Violation],
        warnings: List[Violation],
        recommendations: List[Violation],
    ) -> str:
        """Generate a concise one-sentence summary of the compliance result."""
        parts: List[str] = []
        if violations:
            descs = ", ".join(v.description[:60] for v in violations[:5])
            parts.append(f"{len(violations)} violation(s) found: {descs}")
        if warnings:
            parts.append(f"{len(warnings)} warning(s)")
        if recommendations:
            parts.append(f"{len(recommendations)} recommendation(s)")
        if not parts:
            return "All compliance checks passed."
        return "; ".join(parts) + "."

    # ==================================================================
    # Check methods
    # ==================================================================

    # ------------------------------------------------------------------
    # 1. Banned words
    # ------------------------------------------------------------------

    def _check_banned_words(
        self,
        content: ContentForReview,
        *,
        _rule: Optional[PolicyRule] = None,
    ) -> Optional[Violation]:
        """Check for prohibited words/phrases per platform and globally."""
        text = _all_text(content)
        platform = (content.platform or "").lower()

        patterns_to_check: List[re.Pattern[str]] = list(_PLATFORM_BANNED_WORDS.get("_global", []))
        if platform in _PLATFORM_BANNED_WORDS:
            patterns_to_check.extend(_PLATFORM_BANNED_WORDS[platform])

        found_snippets: List[str] = []
        for pattern in patterns_to_check:
            match = pattern.search(text)
            if match:
                found_snippets.append(match.group(0))

        if not found_snippets:
            return None

        snippet = _truncate_snippet(", ".join(found_snippets))
        rule_id = _rule.rule_id if _rule else "check_banned_words"
        return Violation(
            rule_id=rule_id,
            severity=_rule.severity if _rule else "warning",
            description=f"Prohibited word(s)/phrase(s) detected: {snippet}",
            content_snippet=snippet,
            fix_suggestion=(
                _rule.fix_guidance if _rule else
                "Remove or replace the flagged words/phrases with compliant alternatives."
            ),
            regulatory_reference=_rule.regulatory_source if _rule else None,
            auto_fixable=True,
            fix_template="Remove or rephrase: {snippet}",
        )

    # ------------------------------------------------------------------
    # 2. Claims substantiation
    # ------------------------------------------------------------------

    def _check_claims_substantiation(
        self,
        content: ContentForReview,
        *,
        _rule: Optional[PolicyRule] = None,
    ) -> Optional[Violation]:
        """Detect superlative claims and results claims without evidence.

        Catches patterns like 'best', '#1', 'fastest', as well as numeric
        results claims ('lose 30 lbs', 'earn $10,000', '500% growth').
        """
        text = _all_text(content)
        # Also check explicit claims list
        claims_text = " ".join(content.claims) if content.claims else ""
        combined = f"{text} {claims_text}"

        found: List[str] = []

        for pattern in _SUPERLATIVE_PATTERNS:
            match = pattern.search(combined)
            if match:
                found.append(match.group(0))

        for pattern in _RESULTS_CLAIM_PATTERNS:
            match = pattern.search(combined)
            if match:
                found.append(match.group(0))

        if not found:
            return None

        snippet = _truncate_snippet(", ".join(found))
        rule_id = _rule.rule_id if _rule else "check_claims_substantiation"
        return Violation(
            rule_id=rule_id,
            severity=_rule.severity if _rule else "warning",
            description=(
                f"Unsubstantiated claim(s) detected: {snippet}. "
                "Superlatives and results claims require third-party evidence."
            ),
            content_snippet=snippet,
            fix_suggestion=(
                _rule.fix_guidance if _rule else
                "Remove superlatives or add verifiable third-party evidence. "
                "Link to the source on the landing page."
            ),
            regulatory_reference=_rule.regulatory_source if _rule else "FTC Act Section 5",
            auto_fixable=False,
        )

    # ------------------------------------------------------------------
    # 3. Personal attributes (Meta-specific)
    # ------------------------------------------------------------------

    def _check_personal_attributes(
        self,
        content: ContentForReview,
        *,
        _rule: Optional[PolicyRule] = None,
    ) -> Optional[Violation]:
        """Meta-specific: detect 'Are you...', 'Do you...', and other personal attribute phrasing.

        Meta Advertising Standards prohibit ads that assert or imply knowledge
        of a user's personal attributes including race, ethnicity, religion,
        sexual orientation, health conditions, or financial status.
        """
        text = _all_text(content)
        found: List[str] = []

        for pattern in _PERSONAL_ATTRIBUTE_PATTERNS:
            match = pattern.search(text)
            if match:
                # Capture surrounding context for a useful snippet
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 40)
                found.append(text[start:end].strip())

        if not found:
            return None

        snippet = _truncate_snippet("; ".join(found))
        rule_id = _rule.rule_id if _rule else "check_personal_attributes"
        return Violation(
            rule_id=rule_id,
            severity=_rule.severity if _rule else "violation",
            description=(
                "Personal attribute assertion detected. Meta ads must not assert "
                "or imply knowledge of the user's personal attributes."
            ),
            content_snippet=snippet,
            fix_suggestion=(
                _rule.fix_guidance if _rule else
                "Rewrite ad copy to avoid second-person questions or statements about "
                "personal characteristics. Frame around the solution, not the user's situation."
            ),
            regulatory_reference=(
                _rule.regulatory_source if _rule else
                "Meta Advertising Standards (Personal Attributes Section)"
            ),
            auto_fixable=True,
            fix_template=(
                "Replace personal attribute language with solution-focused copy. "
                'E.g. instead of "Are you struggling with debt?", '
                'use "Many people face unexpected financial challenges."'
            ),
        )

    # ------------------------------------------------------------------
    # 4. Before/after claims
    # ------------------------------------------------------------------

    def _check_before_after(
        self,
        content: ContentForReview,
        *,
        _rule: Optional[PolicyRule] = None,
    ) -> Optional[Violation]:
        """Detect before/after claims in restricted platforms (Meta, TikTok).

        Meta and TikTok prohibit before-and-after imagery and claims for
        health, weight loss, and body appearance products.
        """
        text = _all_text(content)
        # Also check image description
        if content.image_description:
            text = f"{text} {content.image_description}"

        found: List[str] = []
        for pattern in _BEFORE_AFTER_PATTERNS:
            match = pattern.search(text)
            if match:
                start = max(0, match.start() - 15)
                end = min(len(text), match.end() + 30)
                found.append(text[start:end].strip())

        if not found:
            return None

        snippet = _truncate_snippet("; ".join(found))
        rule_id = _rule.rule_id if _rule else "check_before_after"
        return Violation(
            rule_id=rule_id,
            severity=_rule.severity if _rule else "violation",
            description=(
                "Before/after content detected. This is prohibited on Meta and "
                "restricted on TikTok for health and appearance products."
            ),
            content_snippet=snippet,
            fix_suggestion=(
                _rule.fix_guidance if _rule else
                "Remove before/after imagery and language. Show the product in use "
                "or use text-only customer testimonials instead."
            ),
            regulatory_reference=(
                _rule.regulatory_source if _rule else
                "Meta Advertising Standards (Health and Appearance Section)"
            ),
            auto_fixable=False,
        )

    # ------------------------------------------------------------------
    # 5. Special Ad Category (Meta housing/employment/credit)
    # ------------------------------------------------------------------

    def _check_special_ad_category(
        self,
        content: ContentForReview,
        *,
        _rule: Optional[PolicyRule] = None,
    ) -> Optional[Violation]:
        """Meta: detect if content falls under housing, employment, or credit categories.

        If the ad pertains to these categories, it MUST be marked as a Special
        Ad Category with restricted targeting (no age, gender, or zip code targeting).
        """
        text = _all_text(content)
        detected_categories: List[str] = []

        for pattern in _HOUSING_KEYWORDS:
            if pattern.search(text):
                detected_categories.append("Housing")
                break
        for pattern in _EMPLOYMENT_KEYWORDS:
            if pattern.search(text):
                detected_categories.append("Employment")
                break
        for pattern in _CREDIT_KEYWORDS:
            if pattern.search(text):
                detected_categories.append("Credit")
                break

        if not detected_categories:
            return None

        # If the content already declares the special ad category in metadata, pass
        declared = content.metadata.get("special_ad_category")
        if declared:
            declared_lower = declared.lower() if isinstance(declared, str) else ""
            for cat in detected_categories:
                if cat.lower() in declared_lower:
                    detected_categories.remove(cat)
        if not detected_categories:
            return None

        cats = ", ".join(detected_categories)
        rule_id = _rule.rule_id if _rule else "check_special_ad_category"
        return Violation(
            rule_id=rule_id,
            severity=_rule.severity if _rule else "violation",
            description=(
                f"Content appears to fall under Meta Special Ad Category: {cats}. "
                "This ad must be flagged in Ads Manager with restricted targeting."
            ),
            content_snippet=_truncate_snippet(cats),
            fix_suggestion=(
                _rule.fix_guidance if _rule else
                f"Set the appropriate Special Ad Category ({cats}) in Meta Ads Manager. "
                "Accept restricted targeting options (no age, gender, or zip code targeting)."
            ),
            regulatory_reference=(
                _rule.regulatory_source if _rule else
                "Meta Advertising Standards / Fair Housing Act / Equal Employment Opportunity Act"
            ),
            auto_fixable=False,
        )

    # ------------------------------------------------------------------
    # 6. Disclosure present
    # ------------------------------------------------------------------

    def _check_disclosure_present(
        self,
        content: ContentForReview,
        *,
        required_disclosure: Optional[str] = None,
        disclosure_obj: Optional[RequiredDisclosure] = None,
        _rule: Optional[PolicyRule] = None,
    ) -> Optional[Violation]:
        """Check if required disclosure text is in the content.

        This is a generic helper called both as a rule check and by the
        required-disclosure logic.
        """
        if required_disclosure is None:
            return None

        text = _all_text(content).lower()

        # For template disclosures (e.g. "[Physical mailing address]"), we
        # check for the *type* of disclosure rather than literal text.
        disclosure_lower = required_disclosure.lower()

        # Literal check first
        if disclosure_lower in text:
            return None

        # Type-specific heuristics
        if disclosure_obj:
            dtype = disclosure_obj.disclosure_type
            if dtype == "unsubscribe_link":
                if any(kw in text for kw in ("unsubscribe", "opt out", "opt-out", "manage preferences", "email preferences")):
                    return None
            elif dtype == "physical_address":
                # Look for something that resembles a US street address pattern
                if re.search(r"\d+\s+\w+\s+(?:st|ave|blvd|rd|dr|ln|ct|way|pl|pkwy)\b", text, re.IGNORECASE):
                    return None
                # P.O. Box
                if re.search(r"p\.?o\.?\s*box\s+\d+", text, re.IGNORECASE):
                    return None
            elif dtype == "sender_identification":
                # Just needs some form of business name -- hard to verify programmatically
                return None
            elif dtype == "sponsored_tag":
                if any(kw in text for kw in ("#ad", "#sponsored", "sponsored", "advertisement", "paid partnership")):
                    return None
            elif dtype == "results_disclaimer":
                if any(kw in text for kw in ("results may vary", "not guaranteed", "past performance", "no guarantee", "individual results")):
                    return None
            elif dtype == "equal_opportunity":
                if "equal housing" in text or "equal opportunity" in text:
                    return None
            elif dtype == "age_gate":
                if any(kw in text for kw in ("21+", "must be 21", "must be of legal", "legal drinking age")):
                    return None
            elif dtype == "ai_content_label":
                if any(kw in text for kw in ("ai tools", "ai-generated", "ai generated", "created with ai")):
                    return None

        source_rule = disclosure_obj.source_rule_id if disclosure_obj else "check_disclosure_present"
        dtype_label = disclosure_obj.disclosure_type if disclosure_obj else "required disclosure"
        return Violation(
            rule_id=_rule.rule_id if _rule else source_rule,
            severity=_rule.severity if _rule else "violation",
            description=f"Required {dtype_label} is missing from content.",
            content_snippet=None,
            fix_suggestion=(
                _rule.fix_guidance if _rule else
                f"Add the required disclosure: '{required_disclosure}' "
                f"in the {disclosure_obj.placement if disclosure_obj else 'appropriate'} section."
            ),
            regulatory_reference=_rule.regulatory_source if _rule else None,
            auto_fixable=True,
            fix_template=f"Add '{required_disclosure}' to the content {disclosure_obj.placement if disclosure_obj else 'footer'}.",
        )

    # ------------------------------------------------------------------
    # 7. Unsubscribe link (email)
    # ------------------------------------------------------------------

    def _check_unsubscribe_link(
        self,
        content: ContentForReview,
        *,
        _rule: Optional[PolicyRule] = None,
    ) -> Optional[Violation]:
        """Email: check for an unsubscribe mechanism.

        CAN-SPAM requires a clear, conspicuous, and functioning unsubscribe
        mechanism in every commercial email.
        """
        text = _all_text(content).lower()
        unsubscribe_indicators = (
            "unsubscribe",
            "opt out",
            "opt-out",
            "manage preferences",
            "email preferences",
            "stop receiving",
            "remove me",
            "manage subscription",
        )
        for indicator in unsubscribe_indicators:
            if indicator in text:
                return None

        rule_id = _rule.rule_id if _rule else "check_unsubscribe_link"
        return Violation(
            rule_id=rule_id,
            severity=_rule.severity if _rule else "violation",
            description=(
                "No unsubscribe mechanism detected. CAN-SPAM requires a clear, "
                "conspicuous unsubscribe link in every commercial email."
            ),
            content_snippet=None,
            fix_suggestion=(
                _rule.fix_guidance if _rule else
                "Add a clearly labeled 'Unsubscribe' link in the email footer."
            ),
            regulatory_reference=(
                _rule.regulatory_source if _rule else
                "CAN-SPAM Act (15 U.S.C. 7704(a)(3))"
            ),
            auto_fixable=True,
            fix_template=(
                "Add to email footer: 'If you no longer wish to receive these emails, "
                "click here to unsubscribe.'"
            ),
        )

    # ------------------------------------------------------------------
    # 8. Physical address (email)
    # ------------------------------------------------------------------

    def _check_physical_address(
        self,
        content: ContentForReview,
        *,
        _rule: Optional[PolicyRule] = None,
    ) -> Optional[Violation]:
        """Email: check for physical postal address.

        CAN-SPAM requires a valid physical postal address in every commercial email.
        """
        text = _all_text(content)

        # US street address pattern (number + street name + type)
        if re.search(r"\d+\s+\w+\s+(?:St|Ave|Blvd|Rd|Dr|Ln|Ct|Way|Pl|Pkwy|Street|Avenue|Boulevard|Road|Drive|Lane|Court|Place|Highway|Hwy)\b", text, re.IGNORECASE):
            return None
        # P.O. Box
        if re.search(r"P\.?O\.?\s*Box\s+\d+", text, re.IGNORECASE):
            return None
        # Suite / Ste pattern with preceding address
        if re.search(r"(?:Suite|Ste|Unit|Apt)\.?\s+\w+", text, re.IGNORECASE) and re.search(r"\d{5}", text):
            return None
        # 5-digit zip code at minimum as a weak fallback (must also have a state abbreviation)
        if re.search(r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b", text):
            return None

        rule_id = _rule.rule_id if _rule else "check_physical_address"
        return Violation(
            rule_id=rule_id,
            severity=_rule.severity if _rule else "violation",
            description=(
                "No physical postal address detected. CAN-SPAM requires a "
                "valid physical address in every commercial email."
            ),
            content_snippet=None,
            fix_suggestion=(
                _rule.fix_guidance if _rule else
                "Add the sender's physical postal address to the email footer. "
                "A P.O. Box or registered CMRA address is acceptable."
            ),
            regulatory_reference=(
                _rule.regulatory_source if _rule else
                "CAN-SPAM Act (15 U.S.C. 7704(a)(5)(A))"
            ),
            auto_fixable=True,
            fix_template=(
                "Add to email footer: '[Business Name], [Street Address], "
                "[City, State ZIP]'"
            ),
        )

    # ------------------------------------------------------------------
    # 9. Misleading subject line (email)
    # ------------------------------------------------------------------

    def _check_misleading_subject(
        self,
        content: ContentForReview,
        *,
        _rule: Optional[PolicyRule] = None,
    ) -> Optional[Violation]:
        """Email: detect deceptive or misleading subject lines.

        CAN-SPAM prohibits subject lines that mislead the recipient about the
        contents or subject matter of the message.
        """
        headline = content.headline or ""
        if not headline:
            return None  # No subject line to check

        found: List[str] = []
        for pattern in _MISLEADING_SUBJECT_PATTERNS:
            match = pattern.search(headline)
            if match:
                found.append(match.group(0))

        if not found:
            return None

        snippet = _truncate_snippet(f"Subject: {headline}")
        rule_id = _rule.rule_id if _rule else "check_misleading_subject"
        return Violation(
            rule_id=rule_id,
            severity=_rule.severity if _rule else "violation",
            description=(
                f"Potentially misleading subject line detected: {', '.join(found)}. "
                "CAN-SPAM prohibits deceptive subject lines in marketing emails."
            ),
            content_snippet=snippet,
            fix_suggestion=(
                _rule.fix_guidance if _rule else
                "Rewrite the subject line to honestly represent the email content. "
                "Do not use 'Re:', 'Fwd:', or urgency language for marketing emails."
            ),
            regulatory_reference=(
                _rule.regulatory_source if _rule else
                "CAN-SPAM Act (15 U.S.C. 7704(a)(2))"
            ),
            auto_fixable=True,
            fix_template="Rewrite subject line to accurately reflect email content.",
        )


# ======================================================================
# Regulated industry rule generators
# ======================================================================


def _get_healthcare_rules() -> List[PolicyRule]:
    """Return compliance rules specific to the healthcare industry.

    Covers HIPAA considerations, medical claims restrictions, before/after
    image bans, and testimonial restrictions for health products.
    """
    return [
        PolicyRule(
            rule_id="industry_healthcare_001",
            pack="industry_healthcare",
            category="medical_claims",
            description=(
                "Health-related marketing must not make disease cure or treatment claims "
                "without FDA approval. Structure/function claims require a disclaimer."
            ),
            check_function_name="check_claims_substantiation",
            severity="violation",
            applicable_content_types=[],
            applicable_industries=["healthcare", "pharma", "health", "medical", "supplements"],
            regulatory_source="FTC Health Claims Policy / FDA 21 CFR 101.93",
            fix_guidance=(
                "Remove disease-specific claims unless the product has FDA approval. "
                "For supplements, use only structure/function claims with the required "
                "disclaimer: 'These statements have not been evaluated by the Food and "
                "Drug Administration. This product is not intended to diagnose, treat, "
                "cure, or prevent any disease.'"
            ),
        ),
        PolicyRule(
            rule_id="industry_healthcare_002",
            pack="industry_healthcare",
            category="hipaa",
            description=(
                "Marketing content must not include Protected Health Information (PHI). "
                "Patient names, medical record numbers, photos, or any identifiable "
                "health data must not appear in marketing materials."
            ),
            check_function_name="check_banned_words",
            severity="violation",
            applicable_content_types=[],
            applicable_industries=["healthcare", "pharma", "medical", "telemedicine"],
            regulatory_source="HIPAA Privacy Rule (45 CFR Part 160 and 164)",
            fix_guidance=(
                "Audit all marketing content for PHI. Remove patient names, "
                "medical record numbers, dates of service, and identifiable photos. "
                "Use only de-identified data or obtain a valid HIPAA authorization."
            ),
        ),
        PolicyRule(
            rule_id="industry_healthcare_003",
            pack="industry_healthcare",
            category="testimonials",
            description=(
                "Health product testimonials must include a 'results not typical' "
                "disclaimer and must not imply guaranteed outcomes."
            ),
            check_function_name="check_claims_substantiation",
            severity="warning",
            applicable_content_types=["paid_ad", "social_post", "landing_page", "testimonial"],
            applicable_industries=["healthcare", "health", "fitness", "supplements", "weight_loss"],
            regulatory_source="FTC Endorsement Guides (16 CFR Part 255)",
            fix_guidance=(
                "Add a clear disclaimer near testimonials: 'Individual results may "
                "vary. These testimonials are not intended to represent or guarantee "
                "that anyone will achieve the same or similar results.' Include the "
                "generally expected results."
            ),
        ),
        PolicyRule(
            rule_id="industry_healthcare_004",
            pack="industry_healthcare",
            category="before_after",
            description=(
                "Before-and-after images for health, weight loss, cosmetic, and "
                "dental products are banned on Meta and restricted on other platforms."
            ),
            check_function_name="check_before_after",
            severity="violation",
            applicable_content_types=["paid_ad", "social_post", "social_story"],
            applicable_industries=["healthcare", "health", "fitness", "dental", "cosmetic_surgery", "weight_loss", "beauty"],
            regulatory_source="Meta Advertising Standards / TikTok Advertising Policies",
            fix_guidance=(
                "Remove before/after imagery. Use lifestyle photos, product-in-use "
                "imagery, or text-based testimonials instead."
            ),
        ),
        PolicyRule(
            rule_id="industry_healthcare_005",
            pack="industry_healthcare",
            category="telehealth",
            description=(
                "Telehealth and telemedicine advertising must comply with state "
                "licensing requirements. Ads must not imply availability in states "
                "where the provider is not licensed."
            ),
            check_function_name="check_claims_substantiation",
            severity="violation",
            applicable_content_types=["paid_ad", "landing_page"],
            applicable_industries=["healthcare", "telemedicine", "medical"],
            regulatory_source="State Medical Practice Acts / Ryan Haight Act (online prescribing)",
            fix_guidance=(
                "Clearly state which states/regions the telehealth service is "
                "available in. Add a disclaimer: 'Available in [states]. Licensing "
                "restrictions apply.' Do not advertise prescription services without "
                "complying with the Ryan Haight Act."
            ),
        ),
        PolicyRule(
            rule_id="industry_healthcare_006",
            pack="industry_healthcare",
            category="platform_certification",
            description=(
                "Google Ads and Meta require pre-certification before running ads "
                "for healthcare, pharmaceuticals, and addiction treatment services."
            ),
            check_function_name="check_banned_words",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_industries=["healthcare", "pharma", "addiction_services"],
            regulatory_source="Google Ads Healthcare and Medicines Policy / Meta Advertising Standards",
            fix_guidance=(
                "Apply for platform healthcare certification before launching ads. "
                "Google requires application at ads.google.com/aw/healthcert. "
                "Meta requires documentation for pharmaceutical advertisers."
            ),
        ),
    ]


def _get_financial_rules() -> List[PolicyRule]:
    """Return compliance rules specific to the financial industry.

    Covers SEC/FINRA disclaimers, APR disclosures, risk warnings, and
    past performance disclaimers.
    """
    return [
        PolicyRule(
            rule_id="industry_financial_001",
            pack="industry_financial",
            category="disclosures",
            description=(
                "Financial product ads must include APR, fees, repayment terms, and "
                "total cost examples. Missing disclosures violate Truth in Lending."
            ),
            check_function_name="check_claims_substantiation",
            severity="violation",
            applicable_content_types=["paid_ad", "landing_page", "email_marketing"],
            applicable_industries=["finance", "lending", "insurance", "investment"],
            regulatory_source="Truth in Lending Act (TILA) / Regulation Z (12 CFR Part 226)",
            fix_guidance=(
                "Include in all financial ads: (1) APR range, (2) minimum/maximum "
                "amounts, (3) repayment period, (4) representative cost example with "
                "total repayable amount, (5) any fees."
            ),
        ),
        PolicyRule(
            rule_id="industry_financial_002",
            pack="industry_financial",
            category="disclaimers",
            description=(
                "Investment advertising must include a 'past performance' disclaimer. "
                "No guarantee of future results may be stated or implied."
            ),
            check_function_name="check_claims_substantiation",
            severity="violation",
            applicable_content_types=["paid_ad", "landing_page", "social_post", "email_marketing"],
            applicable_industries=["investment", "finance"],
            regulatory_source="SEC Rule 156 / FINRA Rule 2210",
            fix_guidance=(
                "Add a prominent disclaimer: 'Past performance does not guarantee "
                "future results. Investment involves risk; you may lose some or all "
                "of your investment.' Position this near any performance data."
            ),
        ),
        PolicyRule(
            rule_id="industry_financial_003",
            pack="industry_financial",
            category="testimonials",
            description=(
                "FINRA prohibits the use of testimonials in investment advertising "
                "unless accompanied by specific disclosures about compensation and "
                "the possibility of different results."
            ),
            check_function_name="check_claims_substantiation",
            severity="warning",
            applicable_content_types=["paid_ad", "social_post", "landing_page", "testimonial"],
            applicable_industries=["investment", "finance"],
            regulatory_source="FINRA Rule 2210(d)(6) / SEC Marketing Rule",
            fix_guidance=(
                "If using testimonials: (1) disclose if the person was compensated, "
                "(2) state that other clients may have different experiences, "
                "(3) do not cherry-pick results. The SEC Marketing Rule (effective "
                "Nov 2022) allows testimonials with proper disclosures."
            ),
        ),
        PolicyRule(
            rule_id="industry_financial_004",
            pack="industry_financial",
            category="crypto",
            description=(
                "Cryptocurrency and digital asset advertising faces platform-level "
                "restrictions. Google requires certification; Meta restricts targeting."
            ),
            check_function_name="check_banned_words",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_industries=["crypto", "defi", "finance"],
            regulatory_source="Google Ads Cryptocurrency Policy / Meta Financial Products Policy",
            fix_guidance=(
                "Obtain platform certification before running crypto ads. Google "
                "requires registration through their crypto certification program. "
                "Add risk disclosures: 'Cryptocurrency is volatile and you can lose "
                "money. Not FDIC insured.'"
            ),
        ),
        PolicyRule(
            rule_id="industry_financial_005",
            pack="industry_financial",
            category="insurance",
            description=(
                "Insurance advertising must not misrepresent coverage, costs, or "
                "terms. State insurance regulations require specific disclosures "
                "in all marketing materials."
            ),
            check_function_name="check_claims_substantiation",
            severity="violation",
            applicable_content_types=["paid_ad", "landing_page", "email_marketing"],
            applicable_industries=["insurance"],
            regulatory_source="State Insurance Advertising Regulations / NAIC Model Regulation 570",
            fix_guidance=(
                "Include: (1) the insurance company's full legal name, (2) policy "
                "form number, (3) clear statement of what is and is not covered, "
                "(4) 'This is a solicitation of insurance' where required by state law."
            ),
        ),
        PolicyRule(
            rule_id="industry_financial_006",
            pack="industry_financial",
            category="payday_lending",
            description=(
                "Payday and short-term lending ads are banned or severely restricted "
                "on most platforms. Google bans payday loans with repayment within "
                "60 days or APR above 36%."
            ),
            check_function_name="check_banned_words",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_industries=["lending", "payday"],
            regulatory_source="Google Ads Financial Products Policy / CFPB Payday Lending Rule",
            fix_guidance=(
                "Do not advertise payday loans, title loans, or short-term high-APR "
                "lending on Google Ads. For other platforms, check each platform's "
                "specific lending restrictions. Verify all loan terms comply with "
                "state usury laws."
            ),
        ),
    ]


def _get_legal_rules() -> List[PolicyRule]:
    """Return compliance rules specific to the legal industry.

    Covers bar association rules, no guarantee of outcomes, jurisdiction
    requirements, and prior results disclaimers.
    """
    return [
        PolicyRule(
            rule_id="industry_legal_001",
            pack="industry_legal",
            category="disclaimers",
            description=(
                "Legal advertising must include a 'prior results do not guarantee "
                "a similar outcome' disclaimer. No promise of results is permitted."
            ),
            check_function_name="check_claims_substantiation",
            severity="violation",
            applicable_content_types=[],
            applicable_industries=["legal", "law"],
            regulatory_source="ABA Model Rule 7.1 / State Bar Advertising Rules",
            fix_guidance=(
                "Add a disclaimer: 'Prior results do not guarantee a similar outcome.' "
                "Do not use words like 'guaranteed', 'winning', or '100% success rate' "
                "in any legal advertising."
            ),
        ),
        PolicyRule(
            rule_id="industry_legal_002",
            pack="industry_legal",
            category="jurisdiction",
            description=(
                "Legal ads must specify the jurisdiction(s) where the attorney is "
                "licensed to practice. Implying availability in unlicensed states "
                "is an ethics violation."
            ),
            check_function_name="check_claims_substantiation",
            severity="violation",
            applicable_content_types=["paid_ad", "landing_page", "social_post"],
            applicable_industries=["legal", "law"],
            regulatory_source="ABA Model Rule 7.1, 7.2 / State Bar Rules",
            fix_guidance=(
                "Include: 'Licensed to practice in [State(s)]' on all advertising. "
                "If the firm operates in multiple states, list all jurisdictions. "
                "Do not imply national practice unless licensed in all 50 states."
            ),
        ),
        PolicyRule(
            rule_id="industry_legal_003",
            pack="industry_legal",
            category="specialization",
            description=(
                "Attorneys must not claim to be 'specialists' or 'experts' unless "
                "certified by an approved state or ABA-accredited organization."
            ),
            check_function_name="check_claims_substantiation",
            severity="warning",
            applicable_content_types=[],
            applicable_industries=["legal", "law"],
            regulatory_source="ABA Model Rule 7.2(c) / State Bar Specialization Rules",
            fix_guidance=(
                "Replace 'specialist' or 'expert' with 'focuses on' or 'practices in' "
                "unless the attorney holds board certification from a qualifying body. "
                "If certified, include: 'Board Certified by [Organization] in [Area].'"
            ),
        ),
        PolicyRule(
            rule_id="industry_legal_004",
            pack="industry_legal",
            category="solicitation",
            description=(
                "Direct solicitation of accident victims, hospitalized persons, or "
                "individuals in distressing circumstances is prohibited within a "
                "set time period after the event (typically 30-45 days)."
            ),
            check_function_name="check_banned_words",
            severity="violation",
            applicable_content_types=["email_marketing", "paid_ad"],
            applicable_industries=["legal", "law"],
            regulatory_source="ABA Model Rule 7.3 / State Anti-Barratry Statutes",
            fix_guidance=(
                "Do not target individuals within 30-45 days of an accident or "
                "injury event (exact period varies by state). Use general brand "
                "advertising instead of direct-to-victim targeting."
            ),
        ),
        PolicyRule(
            rule_id="industry_legal_005",
            pack="industry_legal",
            category="fees",
            description=(
                "Legal advertising that mentions fees must clearly explain the fee "
                "structure (contingency, hourly, flat fee) and any costs the client "
                "may still owe if the case is lost."
            ),
            check_function_name="check_claims_substantiation",
            severity="warning",
            applicable_content_types=["paid_ad", "landing_page"],
            applicable_industries=["legal", "law"],
            regulatory_source="ABA Model Rule 1.5 / State Bar Fee Advertising Rules",
            fix_guidance=(
                "If mentioning fees: (1) state the fee type clearly, (2) explain "
                "contingency terms, (3) note that 'No fee unless we win' still means "
                "the client may owe court costs and expenses, (4) include 'Free "
                "consultation' only if genuinely free with no obligation."
            ),
        ),
    ]


def _get_real_estate_rules() -> List[PolicyRule]:
    """Return compliance rules specific to the real estate industry.

    Covers Fair Housing Act, Equal Opportunity logo, MLS compliance, and
    accurate property descriptions.
    """
    return [
        PolicyRule(
            rule_id="industry_real_estate_001",
            pack="industry_real_estate",
            category="fair_housing",
            description=(
                "All real estate advertising must comply with the Fair Housing Act. "
                "Ads must not discriminate based on race, color, national origin, "
                "religion, sex, familial status, or disability."
            ),
            check_function_name="check_personal_attributes",
            severity="violation",
            applicable_content_types=[],
            applicable_industries=["real_estate"],
            regulatory_source="Fair Housing Act (42 U.S.C. 3601-3619)",
            fix_guidance=(
                "Do not include language that indicates preference, limitation, or "
                "discrimination based on protected classes. Avoid: 'perfect for young "
                "professionals', 'no children', 'walking distance to [church/mosque]', "
                "'exclusive neighborhood'. Use neutral, property-focused language."
            ),
        ),
        PolicyRule(
            rule_id="industry_real_estate_002",
            pack="industry_real_estate",
            category="equal_opportunity",
            description=(
                "Real estate ads must include the Equal Housing Opportunity logo "
                "or the statement 'Equal Housing Opportunity' per HUD guidelines."
            ),
            check_function_name="check_disclosure_present",
            severity="violation",
            applicable_content_types=["paid_ad", "landing_page", "social_post", "email_marketing"],
            applicable_industries=["real_estate"],
            regulatory_source="HUD Fair Housing Advertising Guidelines (24 CFR Part 109)",
            fix_guidance=(
                "Include the Equal Housing Opportunity logo or text statement in all "
                "real estate advertising. For print/display: use the standard logo. "
                "For text ads: include 'Equal Housing Opportunity' in the ad."
            ),
        ),
        PolicyRule(
            rule_id="industry_real_estate_003",
            pack="industry_real_estate",
            category="mls_compliance",
            description=(
                "Property listings in ads must accurately reflect MLS data. Price, "
                "square footage, bedroom/bathroom count, and status must match the "
                "listing as of the ad date."
            ),
            check_function_name="check_claims_substantiation",
            severity="warning",
            applicable_content_types=["paid_ad", "social_post", "email_marketing"],
            applicable_industries=["real_estate"],
            regulatory_source="NAR MLS Policy / State Real Estate Commission Rules",
            fix_guidance=(
                "Verify all property data matches the current MLS listing. Include "
                "the listing date and broker attribution. Update or pause ads "
                "immediately when listings change status."
            ),
        ),
        PolicyRule(
            rule_id="industry_real_estate_004",
            pack="industry_real_estate",
            category="broker_attribution",
            description=(
                "Real estate ads must identify the brokerage by name. Individual "
                "agents must include their brokerage affiliation."
            ),
            check_function_name="check_disclosure_present",
            severity="warning",
            applicable_content_types=["paid_ad", "social_post", "landing_page"],
            applicable_industries=["real_estate"],
            regulatory_source="NAR Code of Ethics Article 12 / State Real Estate Commission Rules",
            fix_guidance=(
                "Include the brokerage name prominently in all advertising. "
                "Individual agents must use their licensed name and brokerage: "
                "'Jane Smith, Broker Associate, ABC Realty.'"
            ),
        ),
        PolicyRule(
            rule_id="industry_real_estate_005",
            pack="industry_real_estate",
            category="meta_special_category",
            description=(
                "Real estate ads on Meta must use the Housing Special Ad Category "
                "with restricted targeting (no age, gender, or zip code targeting)."
            ),
            check_function_name="check_meta_special_ad_category",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_industries=["real_estate"],
            regulatory_source="Meta Advertising Standards / Fair Housing Act",
            fix_guidance=(
                "When running Meta ads for real estate: (1) select 'Housing' Special "
                "Ad Category, (2) accept restricted targeting (no age, gender, zip), "
                "(3) use Special Ad Audiences instead of standard lookalikes."
            ),
        ),
        PolicyRule(
            rule_id="industry_real_estate_006",
            pack="industry_real_estate",
            category="property_description",
            description=(
                "Property descriptions must be accurate and not misleading. "
                "Overstating features, condition, or neighborhood attributes "
                "exposes the agent and brokerage to misrepresentation liability."
            ),
            check_function_name="check_claims_substantiation",
            severity="warning",
            applicable_content_types=["landing_page", "social_post", "paid_ad"],
            applicable_industries=["real_estate"],
            regulatory_source="State Real Estate License Law / NAR Code of Ethics Article 12",
            fix_guidance=(
                "Ensure all property descriptions are factually accurate. Avoid "
                "subjective claims presented as facts. Use 'Updated kitchen' instead "
                "of 'Brand new kitchen' if only partial updates were made."
            ),
        ),
    ]


def _get_alcohol_cannabis_rules() -> List[PolicyRule]:
    """Return compliance rules specific to the alcohol and cannabis industries.

    Covers age-gating requirements, jurisdiction restrictions, no health
    claims, and responsible messaging.
    """
    return [
        PolicyRule(
            rule_id="industry_alcohol_cannabis_001",
            pack="industry_alcohol_cannabis",
            category="age_gate",
            description=(
                "All alcohol and cannabis advertising must include age-gating. "
                "Ads must not target or appeal to individuals under the legal "
                "purchasing age."
            ),
            check_function_name="check_banned_words",
            severity="violation",
            applicable_content_types=[],
            applicable_industries=["alcohol", "cannabis", "alcohol_cannabis"],
            regulatory_source="TTB Advertising Regulations (27 CFR Part 4, 5, 7) / State Cannabis Laws",
            fix_guidance=(
                "Implement age-gating: (1) target ads only to 21+ audiences on all "
                "platforms, (2) use age-gate landing pages, (3) include 'Must be 21+ "
                "to purchase' in all ads, (4) do not use imagery or language that "
                "appeals to minors (cartoons, candy flavors, slang)."
            ),
        ),
        PolicyRule(
            rule_id="industry_alcohol_cannabis_002",
            pack="industry_alcohol_cannabis",
            category="health_claims",
            description=(
                "Alcohol and cannabis advertising must not make health or therapeutic "
                "claims. No claims about health benefits, curing conditions, or "
                "medical properties."
            ),
            check_function_name="check_claims_substantiation",
            severity="violation",
            applicable_content_types=[],
            applicable_industries=["alcohol", "cannabis", "alcohol_cannabis"],
            regulatory_source="TTB Advertising Regulations / FTC Act Section 5 / State Cannabis Laws",
            fix_guidance=(
                "Do not claim health benefits for alcohol or cannabis products. "
                "Remove language like 'medicinal', 'therapeutic', 'helps with anxiety', "
                "'heart-healthy', or any disease/condition claims. Focus on product "
                "attributes (flavor, origin, process) instead."
            ),
        ),
        PolicyRule(
            rule_id="industry_alcohol_cannabis_003",
            pack="industry_alcohol_cannabis",
            category="responsible_messaging",
            description=(
                "Alcohol ads must include responsible drinking messaging. "
                "Ads must not encourage excessive consumption or depict "
                "intoxicated behavior positively."
            ),
            check_function_name="check_banned_words",
            severity="warning",
            applicable_content_types=["paid_ad", "social_post", "video_script"],
            applicable_industries=["alcohol"],
            regulatory_source="Distilled Spirits Council (DISCUS) Code / Beer Institute Code / TTB Regulations",
            fix_guidance=(
                "Include responsible messaging: 'Please drink responsibly' or "
                "'Enjoy responsibly'. Do not show excessive consumption, drinking "
                "games, or intoxicated behavior. Do not associate alcohol with "
                "driving, operating machinery, or athletic performance."
            ),
        ),
        PolicyRule(
            rule_id="industry_alcohol_cannabis_004",
            pack="industry_alcohol_cannabis",
            category="jurisdiction",
            description=(
                "Cannabis advertising is restricted to jurisdictions where cannabis "
                "is legal. Ads must not target or be visible in states/countries "
                "where cannabis is illegal."
            ),
            check_function_name="check_banned_words",
            severity="violation",
            applicable_content_types=["paid_ad", "social_post"],
            applicable_industries=["cannabis"],
            regulatory_source="State Cannabis Advertising Regulations / Federal Controlled Substances Act",
            fix_guidance=(
                "Restrict cannabis ad targeting to states/regions where cannabis "
                "is legal for the applicable use (medical or recreational). Add "
                "geo-targeting restrictions. Note: Google Ads and Meta ban most "
                "cannabis advertising regardless of state legality."
            ),
        ),
        PolicyRule(
            rule_id="industry_alcohol_cannabis_005",
            pack="industry_alcohol_cannabis",
            category="platform_restrictions",
            description=(
                "Most major ad platforms severely restrict or ban alcohol and "
                "cannabis advertising. Verify platform eligibility before launching."
            ),
            check_function_name="check_banned_words",
            severity="warning",
            applicable_content_types=["paid_ad"],
            applicable_industries=["alcohol", "cannabis", "alcohol_cannabis"],
            regulatory_source="Platform-specific alcohol/cannabis advertising policies",
            fix_guidance=(
                "Before launching: Google Ads allows alcohol with age-gating in "
                "approved countries; Meta allows alcohol with age restrictions; "
                "TikTok bans alcohol in most regions; Pinterest bans cannabis. "
                "Cannabis ads are banned on all major platforms except through "
                "specialized cannabis ad networks."
            ),
        ),
        PolicyRule(
            rule_id="industry_alcohol_cannabis_006",
            pack="industry_alcohol_cannabis",
            category="labeling",
            description=(
                "Alcohol advertising must include mandatory labeling information "
                "in certain contexts: alcohol content, country of origin, and "
                "government warnings (for US retail)."
            ),
            check_function_name="check_disclosure_present",
            severity="warning",
            applicable_content_types=["landing_page", "paid_ad"],
            applicable_industries=["alcohol"],
            regulatory_source="TTB Advertising Regulations (27 CFR Part 4, 5, 7) / Alcohol Beverage Labeling Act",
            fix_guidance=(
                "For e-commerce and direct-to-consumer: include alcohol content "
                "(ABV), country/region of origin, and the Surgeon General's warning "
                "where required: 'GOVERNMENT WARNING: According to the Surgeon "
                "General, women should not drink alcoholic beverages during pregnancy "
                "because of the risk of birth defects.'"
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Module-level industry dispatcher
# ---------------------------------------------------------------------------

_INDUSTRY_DISPATCH: Dict[str, Callable[[], List[PolicyRule]]] = {
    "healthcare": _get_healthcare_rules,
    "pharma": _get_healthcare_rules,
    "medical": _get_healthcare_rules,
    "health": _get_healthcare_rules,
    "telemedicine": _get_healthcare_rules,
    "supplements": _get_healthcare_rules,
    "fitness": _get_healthcare_rules,
    "weight_loss": _get_healthcare_rules,
    "dental": _get_healthcare_rules,
    "cosmetic_surgery": _get_healthcare_rules,
    "addiction_services": _get_healthcare_rules,

    "finance": _get_financial_rules,
    "lending": _get_financial_rules,
    "insurance": _get_financial_rules,
    "investment": _get_financial_rules,
    "crypto": _get_financial_rules,
    "defi": _get_financial_rules,
    "payday": _get_financial_rules,

    "legal": _get_legal_rules,
    "law": _get_legal_rules,

    "real_estate": _get_real_estate_rules,

    "alcohol": _get_alcohol_cannabis_rules,
    "cannabis": _get_alcohol_cannabis_rules,
    "alcohol_cannabis": _get_alcohol_cannabis_rules,
}


def get_industry_rules(industry: str) -> List[PolicyRule]:
    """Return compliance rules specific to *industry*.

    Routes to the correct industry rule set based on the industry slug.
    Returns an empty list for unrecognized industries.

    Parameters
    ----------
    industry:
        An industry slug, e.g. ``'healthcare'``, ``'finance'``, ``'legal'``,
        ``'real_estate'``, ``'alcohol'``, ``'cannabis'``.
    """
    builder = _INDUSTRY_DISPATCH.get(industry.lower())
    if builder is None:
        return []
    return builder()
