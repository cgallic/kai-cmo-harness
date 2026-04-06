"""Brand-specific constraints and regulated-claims handling.

Captures per-business rules -- what claims a business can and cannot make, how
it talks about competitors, what guarantees it offers, which testimonials it
has permission to use -- so the creative engine never produces content that
contradicts the business's own policies or makes unsubstantiated claims.

The ``RegulatedClaimsHandler`` scans content for language patterns (superlatives,
results claims, certifications, guarantees, comparisons, endorsements, time
claims, award claims) and flags anything that needs evidence, disclaimers, or
removal before publishing.

Uses the dataclass + ``SerializableModel`` pattern from ``kai.runtime.models``.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


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

class CompetitorMentionPolicy(str, Enum):
    """Controls how content may reference competitor brands."""

    never = "never"
    """Never mention competitors by name."""

    comparison_ok = "comparison_ok"
    """Factual feature comparisons allowed."""

    aggressive = "aggressive"
    """Direct competitive positioning allowed."""


class ClaimType(str, Enum):
    """Categories of regulated claims that require evidence or disclaimers."""

    superlative = "superlative"
    """'best', 'fastest', '#1', 'leading'."""

    results_claim = "results_claim"
    """Specific outcomes with numbers ('lose 10 lbs', 'save $5000')."""

    certification_claim = "certification_claim"
    """'certified', 'licensed', 'accredited', 'board-certified'."""

    guarantee_claim = "guarantee_claim"
    """'guaranteed', 'risk-free', 'money back', '100% satisfaction'."""

    comparison_claim = "comparison_claim"
    """'better than', 'unlike competitors', 'more than Brand X'."""

    endorsement_claim = "endorsement_claim"
    """'recommended by', 'as seen on', 'endorsed by'."""

    time_claim = "time_claim"
    """'same-day', '24-hour', 'within 1 hour'."""

    award_claim = "award_claim"
    """'award-winning', 'voted best', 'top rated'."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ApprovedClaim(SerializableModel):
    """A specific claim the business has evidence for and is allowed to use."""

    claim_text: str
    """The specific claim (e.g., 'Licensed and insured in all 50 states')."""

    evidence_source: str
    """Where the evidence is (e.g., 'State licensing database, license #12345')."""

    valid_until: Optional[str] = None
    """ISO date when this claim expires (e.g., license renewal date)."""

    approved_by: Optional[str] = None
    """Who approved this claim."""

    content_types_allowed: List[str] = field(default_factory=list)
    """Where this claim can be used (e.g., ['website_page', 'paid_ad', 'social_post'])."""


@dataclass
class ProhibitedClaim(SerializableModel):
    """A claim pattern the business must never make."""

    claim_pattern: str
    """The pattern to avoid (e.g., 'cheapest in town', 'guaranteed results')."""

    reason: str
    """Why this is prohibited (e.g., 'Cannot substantiate lowest price claim')."""

    alternative: Optional[str] = None
    """What to say instead (e.g., 'competitive pricing' instead of 'cheapest')."""


@dataclass
class RequiredDisclaimer(SerializableModel):
    """A disclaimer that must be included when certain content conditions are met."""

    trigger: str
    """What content triggers this disclaimer (e.g., 'any pricing mention')."""

    disclaimer_text: str
    """The exact disclaimer text."""

    placement: str
    """Where the disclaimer goes: 'footer', 'inline', or 'adjacent'."""

    applicable_to: List[str] = field(default_factory=list)
    """Content types where this applies."""


@dataclass
class TestimonialPolicy(SerializableModel):
    """Rules governing how the business may use customer testimonials."""

    can_use_customer_names: bool = True
    require_consent_form: bool = True
    anonymous_allowed: bool = True
    video_testimonials_allowed: bool = True
    must_include_disclaimer: bool = True
    disclaimer_text: str = "Individual results may vary."
    max_age_months: Optional[int] = None
    """Testimonials older than this should be refreshed."""

    approved_testimonials: List[Dict[str, str]] = field(default_factory=list)
    """List of {customer_name, quote, date, consent_status} dicts."""


@dataclass
class BrandConstraints(SerializableModel):
    """Per-business brand constraints governing what content can say and how.

    Loaded from a ``BusinessProfile`` via ``load_brand_constraints()``.
    """

    business_id: str

    approved_claims: List[ApprovedClaim] = field(default_factory=list)
    prohibited_claims: List[ProhibitedClaim] = field(default_factory=list)
    required_disclaimers: List[RequiredDisclaimer] = field(default_factory=list)

    competitor_mention_policy: str = CompetitorMentionPolicy.never.value
    """CompetitorMentionPolicy enum value."""

    named_competitors: List[str] = field(default_factory=list)
    """Specific competitor names (for detection)."""

    pricing_display_rules: Dict[str, Any] = field(default_factory=lambda: {
        "show_exact_prices": False,
        "show_ranges": True,
        "starting_from_allowed": True,
        "free_consultation_allowed": True,
        "discount_rules": "",
    })

    guarantee_language: Dict[str, Any] = field(default_factory=lambda: {
        "can_offer_guarantee": False,
        "guarantee_text": "",
        "guarantee_terms_url": "",
        "guarantee_duration": "",
    })

    testimonial_policy: TestimonialPolicy = field(default_factory=TestimonialPolicy)

    tone_constraints: Dict[str, Any] = field(default_factory=lambda: {
        "formality_level": "professional",
        "humor_allowed": False,
        "emoji_allowed": False,
        "slang_allowed": False,
    })

    content_restrictions: List[str] = field(default_factory=list)
    """Topics to never discuss (e.g., 'competitor lawsuits', 'pending litigation')."""


@dataclass
class ClaimFlag(SerializableModel):
    """A single flagged claim detected in content by the RegulatedClaimsHandler."""

    claim_text: str
    """The detected claim in the content."""

    claim_type: str
    """ClaimType enum value."""

    location: str
    """Where in the content (e.g., 'headline', 'body paragraph 2', 'CTA')."""

    severity: str
    """'block' (cannot publish), 'review' (should be reviewed), 'info' (awareness only)."""

    required_action: str
    """What must happen: 'add_disclaimer', 'provide_evidence', 'remove_claim', 'get_approval', 'verify_current'."""

    suggested_disclaimer: Optional[str] = None
    """Suggested disclaimer text if applicable."""

    matching_approved_claim: Optional[str] = None
    """If this matches an approved claim, reference it."""

    matching_prohibited_claim: Optional[str] = None
    """If this matches a prohibited claim, reference it."""


# ---------------------------------------------------------------------------
# load_brand_constraints
# ---------------------------------------------------------------------------

def load_brand_constraints(business_profile: Any) -> BrandConstraints:
    """Extract brand constraints from a ``BusinessProfile`` object.

    Sets sensible defaults where data is missing:

    - ``competitor_mention_policy`` defaults to ``"never"``
    - ``testimonial_policy`` defaults to: ``require_consent_form=True``,
      ``must_include_disclaimer=True``
    - ``pricing_display_rules`` defaults to: ``show_ranges=True``,
      ``starting_from_allowed=True``
    - ``guarantee_language`` defaults to: ``can_offer_guarantee=False``

    Parameters
    ----------
    business_profile:
        A ``BusinessProfile`` instance (from ``kai.models.business_profile``).
        Accessed via attribute access with ``getattr`` fallbacks so the
        function tolerates partial or evolving schemas.

    Returns
    -------
    BrandConstraints
        A fully populated constraints object ready for the
        ``RegulatedClaimsHandler``.
    """

    # -- helpers to safely pull nested attrs ---------------------------------

    def _get(obj: Any, attr: str, default: Any = None) -> Any:
        """Safe attribute access that also handles dict-like objects."""
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    def _dump(obj: Any) -> Any:
        """Call model_dump if available, otherwise return the object as-is."""
        if obj is None:
            return {}
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if isinstance(obj, dict):
            return obj
        return {}

    # -- extract top-level id ------------------------------------------------

    business_id = _get(business_profile, "id", "unknown")

    # -- constraints sub-object (BusinessConstraints) ------------------------

    bp_constraints = _get(business_profile, "constraints")
    claims_restrictions: List[str] = list(_get(bp_constraints, "claims_restrictions", []) or [])
    topics_to_avoid: List[str] = list(_get(bp_constraints, "topics_to_avoid", []) or [])
    brand_voice_notes: Optional[str] = _get(bp_constraints, "brand_voice_notes")

    # -- trust sub-object (TrustProfile) -------------------------------------

    bp_trust = _get(business_profile, "trust")
    certifications: List[str] = list(_get(bp_trust, "certifications", []) or [])
    licenses: List[str] = list(_get(bp_trust, "licenses", []) or [])
    awards: List[str] = list(_get(bp_trust, "awards", []) or [])
    testimonials_raw = list(_get(bp_trust, "testimonials", []) or [])

    # -- brand_voice sub-object (BrandVoice) ---------------------------------

    bp_voice = _get(business_profile, "brand_voice")
    tone_descriptors: List[str] = list(_get(bp_voice, "tone_descriptors", []) or [])
    competitor_differentiation: Optional[str] = _get(bp_voice, "competitor_differentiation")

    # -- build approved claims from trust data -------------------------------

    approved_claims: List[ApprovedClaim] = []

    for cert in certifications:
        approved_claims.append(ApprovedClaim(
            claim_text=cert,
            evidence_source="Business certifications on file",
            content_types_allowed=["website_page", "paid_ad", "social_post", "email_marketing"],
        ))

    for lic in licenses:
        approved_claims.append(ApprovedClaim(
            claim_text=lic,
            evidence_source="Business licenses on file",
            content_types_allowed=["website_page", "paid_ad", "social_post", "email_marketing"],
        ))

    for award in awards:
        approved_claims.append(ApprovedClaim(
            claim_text=award,
            evidence_source="Awards documentation on file",
            content_types_allowed=["website_page", "social_post", "case_study"],
        ))

    years_in_business = _get(bp_trust, "years_in_business")
    if years_in_business is not None:
        approved_claims.append(ApprovedClaim(
            claim_text=f"{years_in_business}+ years in business",
            evidence_source="Business registration records",
            content_types_allowed=["website_page", "paid_ad", "social_post", "email_marketing"],
        ))

    insurance_details = _get(bp_trust, "insurance_details")
    if insurance_details:
        approved_claims.append(ApprovedClaim(
            claim_text=f"Insured: {insurance_details}",
            evidence_source="Insurance documentation on file",
            content_types_allowed=["website_page", "paid_ad", "social_post"],
        ))

    # -- build prohibited claims from restrictions ---------------------------

    prohibited_claims: List[ProhibitedClaim] = []

    for restriction in claims_restrictions:
        prohibited_claims.append(ProhibitedClaim(
            claim_pattern=restriction,
            reason="Listed in business claims restrictions",
        ))

    # -- build testimonial policy from trust data ----------------------------

    approved_testimonials: List[Dict[str, str]] = []
    for t in testimonials_raw:
        t_data = _dump(t)
        approved_testimonials.append({
            "customer_name": t_data.get("source", "Anonymous"),
            "quote": t_data.get("content", ""),
            "date": t_data.get("date", ""),
            "consent_status": "assumed",
        })

    testimonial_policy = TestimonialPolicy(
        can_use_customer_names=True,
        require_consent_form=True,
        anonymous_allowed=True,
        video_testimonials_allowed=True,
        must_include_disclaimer=True,
        disclaimer_text="Individual results may vary.",
        approved_testimonials=approved_testimonials,
    )

    # -- determine tone constraints from brand voice -------------------------

    formality_level = "professional"
    if tone_descriptors:
        lower_descriptors = [d.lower() for d in tone_descriptors]
        # Check formal first (strongest constraint), then professional, then casual
        if any(word in lower_descriptors for word in ("formal", "authoritative", "corporate")):
            formality_level = "formal"
        elif any(word in lower_descriptors for word in ("professional", "expert", "trustworthy")):
            formality_level = "professional"
        elif any(word in lower_descriptors for word in ("casual", "playful", "fun", "witty")):
            formality_level = "casual"

    humor_allowed = formality_level == "casual"
    emoji_allowed = formality_level == "casual"
    slang_allowed = formality_level == "casual"

    tone_constraints: Dict[str, Any] = {
        "formality_level": formality_level,
        "humor_allowed": humor_allowed,
        "emoji_allowed": emoji_allowed,
        "slang_allowed": slang_allowed,
    }

    # -- build pricing display defaults --------------------------------------

    pricing_display_rules: Dict[str, Any] = {
        "show_exact_prices": False,
        "show_ranges": True,
        "starting_from_allowed": True,
        "free_consultation_allowed": True,
        "discount_rules": "",
    }

    # Check metadata for overrides
    bp_metadata = _get(business_profile, "metadata", {}) or {}
    pricing_overrides = _get(bp_metadata, "pricing_display_rules")
    if isinstance(pricing_overrides, dict):
        pricing_display_rules.update(pricing_overrides)

    # -- build guarantee language defaults -----------------------------------

    guarantee_language: Dict[str, Any] = {
        "can_offer_guarantee": False,
        "guarantee_text": "",
        "guarantee_terms_url": "",
        "guarantee_duration": "",
    }

    guarantee_overrides = _get(bp_metadata, "guarantee_language")
    if isinstance(guarantee_overrides, dict):
        guarantee_language.update(guarantee_overrides)

    # -- required disclaimers (seed from regulated industry flag) -------------

    required_disclaimers: List[RequiredDisclaimer] = []
    regulated_industry = _get(bp_constraints, "regulated_industry", False)
    if regulated_industry:
        required_disclaimers.append(RequiredDisclaimer(
            trigger="any health or safety claim",
            disclaimer_text="This information is for general purposes only and does not constitute professional advice. Consult a qualified professional for guidance specific to your situation.",
            placement="footer",
            applicable_to=["website_page", "blog_post", "paid_ad", "email_marketing", "social_post"],
        ))

    disclaimer_overrides = _get(bp_metadata, "required_disclaimers")
    if isinstance(disclaimer_overrides, list):
        for d in disclaimer_overrides:
            if isinstance(d, dict):
                required_disclaimers.append(RequiredDisclaimer(
                    trigger=d.get("trigger", ""),
                    disclaimer_text=d.get("disclaimer_text", ""),
                    placement=d.get("placement", "footer"),
                    applicable_to=d.get("applicable_to", []),
                ))

    # -- competitor data from metadata or brand voice ------------------------

    named_competitors: List[str] = list(_get(bp_metadata, "named_competitors", []) or [])
    competitor_mention_policy = _get(
        bp_metadata, "competitor_mention_policy", CompetitorMentionPolicy.never.value
    )

    # Validate the policy value
    valid_policies = {e.value for e in CompetitorMentionPolicy}
    if competitor_mention_policy not in valid_policies:
        competitor_mention_policy = CompetitorMentionPolicy.never.value

    # -- assemble and return -------------------------------------------------

    return BrandConstraints(
        business_id=business_id,
        approved_claims=approved_claims,
        prohibited_claims=prohibited_claims,
        required_disclaimers=required_disclaimers,
        competitor_mention_policy=competitor_mention_policy,
        named_competitors=named_competitors,
        pricing_display_rules=pricing_display_rules,
        guarantee_language=guarantee_language,
        testimonial_policy=testimonial_policy,
        tone_constraints=tone_constraints,
        content_restrictions=topics_to_avoid,
    )


# ---------------------------------------------------------------------------
# RegulatedClaimsHandler
# ---------------------------------------------------------------------------

class RegulatedClaimsHandler:
    """Scans content for regulated claims and flags anything that needs
    evidence, disclaimers, or removal before publishing.

    Parameters
    ----------
    constraints:
        The ``BrandConstraints`` for the business whose content is being
        scanned.

    Usage::

        handler = RegulatedClaimsHandler(constraints)
        flags = handler.scan_content(article_text, content_type="blog_post")

        for flag in flags:
            print(f"[{flag.severity}] {flag.claim_type}: {flag.claim_text}")
            print(f"  Action: {flag.required_action}")
    """

    def __init__(self, constraints: BrandConstraints) -> None:
        self.constraints = constraints

        # Pre-compile competitor patterns once for performance
        self._competitor_patterns: List[re.Pattern[str]] = []
        for name in self.constraints.named_competitors:
            escaped = re.escape(name)
            self._competitor_patterns.append(
                re.compile(rf"\b{escaped}\b", re.IGNORECASE)
            )

    # -- public API ----------------------------------------------------------

    def scan_content(self, content_text: str, content_type: str) -> List[ClaimFlag]:
        """Scan *content_text* for all regulated claim types.

        For each detected claim, checks it against ``approved_claims``
        (OK to use) and ``prohibited_claims`` (must remove).

        Parameters
        ----------
        content_text:
            The full text of the content to scan.
        content_type:
            A ``ContentType`` value describing the format (e.g.,
            ``"blog_post"``, ``"paid_ad"``).

        Returns
        -------
        list[ClaimFlag]
            All flagged claims, sorted by severity (block first, then
            review, then info).
        """
        flags: List[ClaimFlag] = []

        # Map each detection method to its ClaimType
        detectors: List[Tuple[ClaimType, List[Tuple[str, int]]]] = [
            (ClaimType.superlative, self._detect_superlatives(content_text)),
            (ClaimType.results_claim, self._detect_results_claims(content_text)),
            (ClaimType.certification_claim, self._detect_certification_claims(content_text)),
            (ClaimType.guarantee_claim, self._detect_guarantee_claims(content_text)),
            (ClaimType.comparison_claim, self._detect_comparison_claims(content_text)),
            (ClaimType.endorsement_claim, self._detect_endorsement_claims(content_text)),
            (ClaimType.time_claim, self._detect_time_claims(content_text)),
            (ClaimType.award_claim, self._detect_award_claims(content_text)),
        ]

        for claim_type, detections in detectors:
            for matched_text, position in detections:
                flag = self._build_flag(
                    matched_text, claim_type, position, content_text, content_type
                )
                flags.append(flag)

        # Check for competitor name mentions if policy is "never"
        if self.constraints.competitor_mention_policy == CompetitorMentionPolicy.never.value:
            for pattern in self._competitor_patterns:
                for match in pattern.finditer(content_text):
                    location = self._estimate_location(match.start(), content_text)
                    flags.append(ClaimFlag(
                        claim_text=match.group(),
                        claim_type=ClaimType.comparison_claim.value,
                        location=location,
                        severity="block",
                        required_action="remove_claim",
                        matching_prohibited_claim=(
                            f"Competitor mention policy is 'never'; "
                            f"remove reference to '{match.group()}'"
                        ),
                    ))

        # Sort: block first, then review, then info
        severity_order = {"block": 0, "review": 1, "info": 2}
        flags.sort(key=lambda f: severity_order.get(f.severity, 3))

        return flags

    # -- detection methods ---------------------------------------------------

    def _detect_superlatives(self, text: str) -> List[Tuple[str, int]]:
        """Detect superlative claims like 'best', 'fastest', '#1'."""
        pattern = re.compile(
            r"\b(?:"
            r"best|fastest|cheapest|(?:\#|number\s+)(?:one|1)|leading|"
            r"top[\-\s]?rated|premier|unmatched|unrivaled|unparalleled|"
            r"most\s+(?:trusted|reliable|affordable|popular|advanced)|"
            r"highest[\-\s]?rated|lowest[\-\s]?priced|"
            r"industry[\-\s]?leading|world[\-\s]?class|best[\-\s]?in[\-\s]?class"
            r")\b",
            re.IGNORECASE,
        )
        return [(m.group(), m.start()) for m in pattern.finditer(text)]

    def _detect_results_claims(self, text: str) -> List[Tuple[str, int]]:
        """Detect claims with specific numeric outcomes."""
        pattern = re.compile(
            r"(?:"
            # "save $X", "earn $X", "make $X"
            r"(?:save|earn|make|generate|recover|recoup)\s+\$[\d,]+(?:\.\d{2})?|"
            # "lose X lbs/pounds/kg"
            r"lose\s+\d+\s*(?:lbs?|pounds?|kg|kilos?)|"
            # "increase/decrease/reduce/boost/grow X%"
            r"(?:increase|decrease|reduce|boost|grow|improve|raise|lower|cut)\s+(?:by\s+)?\d+(?:\.\d+)?\s*%|"
            # "X% faster/more/better/cheaper"
            r"\d+(?:\.\d+)?\s*%\s*(?:faster|more|better|cheaper|higher|lower|less|greater)|"
            # "X times more/better/faster"
            r"\d+(?:\.\d+)?[xX]\s*(?:more|better|faster|cheaper|greater|higher|improvement)|"
            # "$X,XXX in savings/revenue/profit"
            r"\$[\d,]+(?:\.\d{2})?\s+(?:in\s+)?(?:savings?|revenue|profit|income|earnings)"
            r")",
            re.IGNORECASE,
        )
        return [(m.group(), m.start()) for m in pattern.finditer(text)]

    def _detect_certification_claims(self, text: str) -> List[Tuple[str, int]]:
        """Detect claims about certifications, licenses, or accreditations."""
        pattern = re.compile(
            r"\b(?:"
            r"certified|licensed|accredited|board[\-\s]?certified|"
            r"registered|approved|authorized|"
            r"(?:state|nationally|federally)[\-\s]?(?:licensed|certified|accredited|registered)|"
            r"fully[\-\s]?(?:licensed|certified|insured|bonded|accredited)"
            r")\b",
            re.IGNORECASE,
        )
        return [(m.group(), m.start()) for m in pattern.finditer(text)]

    def _detect_guarantee_claims(self, text: str) -> List[Tuple[str, int]]:
        """Detect guarantee and risk-elimination language."""
        pattern = re.compile(
            r"\b(?:"
            r"guaranteed|guarantee|risk[\-\s]?free|money[\-\s]?back|"
            r"100\s*%\s*satisfaction|no[\-\s]?risk|zero[\-\s]?risk|"
            r"free[\-\s]?trial|satisfaction[\-\s]?guaranteed|"
            r"unconditional(?:ly)?[\-\s]?(?:guarantee[ds]?)?|"
            r"money[\-\s]?back[\-\s]?guarantee|"
            r"full[\-\s]?refund|hassle[\-\s]?free[\-\s]?(?:return|refund)"
            r")\b",
            re.IGNORECASE,
        )
        return [(m.group(), m.start()) for m in pattern.finditer(text)]

    def _detect_comparison_claims(self, text: str) -> List[Tuple[str, int]]:
        """Detect comparative claims and competitor mentions."""
        results: List[Tuple[str, int]] = []

        # Generic comparison language
        pattern = re.compile(
            r"\b(?:"
            r"better\s+than|unlike\s+(?:other|competing|competitor)|"
            r"compared\s+to|outperforms?|outpaces?|outshines?|"
            r"surpasses?|beats?|exceeds?|leaves?\s+(?:behind|in\s+the\s+dust)|"
            r"more\s+(?:reliable|effective|affordable|powerful)\s+than|"
            r"superior\s+to|inferior\s+to|"
            r"switch\s+from|switch\s+away\s+from|"
            r"not\s+like\s+(?:other|the\s+rest)"
            r")\b",
            re.IGNORECASE,
        )
        results.extend((m.group(), m.start()) for m in pattern.finditer(text))

        # Named competitor mentions (always flagged as comparison context)
        for comp_pattern in self._competitor_patterns:
            for m in comp_pattern.finditer(text):
                # Avoid duplicate entries if competitor name already captured
                already_covered = any(
                    abs(m.start() - pos) < len(m.group()) for _, pos in results
                )
                if not already_covered:
                    results.append((m.group(), m.start()))

        return results

    def _detect_endorsement_claims(self, text: str) -> List[Tuple[str, int]]:
        """Detect endorsement and social proof claims."""
        pattern = re.compile(
            r"\b(?:"
            r"recommended\s+by|endorsed\s+by|as\s+seen\s+on|"
            r"featured\s+in|trusted\s+by|backed\s+by|"
            r"approved\s+by|preferred\s+by|chosen\s+by|"
            r"used\s+by\s+(?:\d[\d,]*\+?\s+)?(?:businesses|companies|professionals|customers|clients)|"
            r"as\s+(?:featured|seen|heard|mentioned)\s+(?:in|on)"
            r")\b",
            re.IGNORECASE,
        )
        return [(m.group(), m.start()) for m in pattern.finditer(text)]

    def _detect_time_claims(self, text: str) -> List[Tuple[str, int]]:
        """Detect time-based service promises."""
        pattern = re.compile(
            r"\b(?:"
            r"same[\-\s]?day|next[\-\s]?day|overnight|"
            r"24[\-\s]?hour|48[\-\s]?hour|72[\-\s]?hour|"
            r"within\s+\d+\s*(?:hour|minute|day|business\s+day)s?|"
            r"instant(?:ly)?[\-\s]?(?:available|access|delivery|response)?|"
            r"immediate(?:ly)?[\-\s]?(?:available|response)?|"
            r"real[\-\s]?time|on[\-\s]?demand|"
            r"\d+[\-\s]?(?:minute|hour|day)\s+(?:turnaround|response|delivery|service|guarantee)"
            r")\b",
            re.IGNORECASE,
        )
        return [(m.group(), m.start()) for m in pattern.finditer(text)]

    def _detect_award_claims(self, text: str) -> List[Tuple[str, int]]:
        """Detect award and accolade claims."""
        pattern = re.compile(
            r"\b(?:"
            r"award[\-\s]?winning|voted\s+best|top[\-\s]?rated|"
            r"prize[\-\s]?winning|decorated|recognized\s+(?:as|by|for)|"
            r"recipient\s+of|winner\s+of|finalist\s+(?:for|in)|"
            r"(?:gold|silver|bronze|platinum)\s+(?:award|winner|medal)|"
            r"best\s+of\s+\d{4}|"
            r"(?:five|5)[\-\s]?star(?:[\-\s]?rated)?|"
            r"rated\s+(?:\#\s*)?\d+(?:\s+in|\s+on|\s+by)"
            r")\b",
            re.IGNORECASE,
        )
        return [(m.group(), m.start()) for m in pattern.finditer(text)]

    # -- matching helpers ----------------------------------------------------

    def _check_against_approved(self, claim_text: str) -> Optional[ApprovedClaim]:
        """Fuzzy-match *claim_text* against approved claims (case-insensitive).

        Returns the matching ``ApprovedClaim`` if found, otherwise ``None``.
        Matching uses normalized substring containment in both directions:
        the detected claim is in the approved claim text, or vice versa.
        """
        claim_lower = claim_text.lower().strip()
        for approved in self.constraints.approved_claims:
            approved_lower = approved.claim_text.lower().strip()
            # Bi-directional containment: either the detected text is part
            # of an approved claim, or the approved claim text appears in
            # the detected text.
            if claim_lower in approved_lower or approved_lower in claim_lower:
                return approved
            # Word-overlap heuristic: if 60%+ of words in the detected claim
            # appear in the approved claim, consider it a match.
            claim_words = set(claim_lower.split())
            approved_words = set(approved_lower.split())
            if claim_words and approved_words:
                overlap = len(claim_words & approved_words)
                if overlap / len(claim_words) >= 0.6:
                    return approved
        return None

    def _check_against_prohibited(self, claim_text: str) -> Optional[ProhibitedClaim]:
        """Match *claim_text* against prohibited claim patterns (case-insensitive).

        Returns the matching ``ProhibitedClaim`` if found, otherwise ``None``.
        """
        claim_lower = claim_text.lower().strip()
        for prohibited in self.constraints.prohibited_claims:
            pattern_lower = prohibited.claim_pattern.lower().strip()
            # Direct containment match
            if pattern_lower in claim_lower or claim_lower in pattern_lower:
                return prohibited
            # Try the pattern as a regex (graceful fallback if it's not valid regex)
            try:
                if re.search(pattern_lower, claim_lower, re.IGNORECASE):
                    return prohibited
            except re.error:
                pass
        return None

    # -- internal helpers ----------------------------------------------------

    def _build_flag(
        self,
        matched_text: str,
        claim_type: ClaimType,
        position: int,
        full_text: str,
        content_type: str,
    ) -> ClaimFlag:
        """Build a ``ClaimFlag`` for a single detection, applying business rules."""

        location = self._estimate_location(position, full_text)

        # Check against prohibited claims first (highest severity)
        prohibited = self._check_against_prohibited(matched_text)
        if prohibited is not None:
            return ClaimFlag(
                claim_text=matched_text,
                claim_type=claim_type.value,
                location=location,
                severity="block",
                required_action="remove_claim",
                suggested_disclaimer=None,
                matching_approved_claim=None,
                matching_prohibited_claim=prohibited.claim_pattern,
            )

        # Check against approved claims
        approved = self._check_against_approved(matched_text)
        if approved is not None:
            # Approved but check content type restrictions
            if approved.content_types_allowed and content_type not in approved.content_types_allowed:
                return ClaimFlag(
                    claim_text=matched_text,
                    claim_type=claim_type.value,
                    location=location,
                    severity="review",
                    required_action="get_approval",
                    suggested_disclaimer=None,
                    matching_approved_claim=approved.claim_text,
                    matching_prohibited_claim=None,
                )
            # Check if the approved claim has expired
            if approved.valid_until:
                return ClaimFlag(
                    claim_text=matched_text,
                    claim_type=claim_type.value,
                    location=location,
                    severity="info",
                    required_action="verify_current",
                    suggested_disclaimer=None,
                    matching_approved_claim=approved.claim_text,
                    matching_prohibited_claim=None,
                )
            return ClaimFlag(
                claim_text=matched_text,
                claim_type=claim_type.value,
                location=location,
                severity="info",
                required_action="verify_current",
                suggested_disclaimer=None,
                matching_approved_claim=approved.claim_text,
                matching_prohibited_claim=None,
            )

        # Unmatched claim -- severity and action depend on claim type
        severity, action, disclaimer = self._default_severity_and_action(claim_type)
        return ClaimFlag(
            claim_text=matched_text,
            claim_type=claim_type.value,
            location=location,
            severity=severity,
            required_action=action,
            suggested_disclaimer=disclaimer,
            matching_approved_claim=None,
            matching_prohibited_claim=None,
        )

    def _default_severity_and_action(
        self, claim_type: ClaimType
    ) -> Tuple[str, str, Optional[str]]:
        """Return (severity, required_action, suggested_disclaimer) defaults
        for an unmatched claim based on its type."""

        if claim_type == ClaimType.superlative:
            return (
                "review",
                "provide_evidence",
                "Results may vary. Claims based on available data.",
            )

        if claim_type == ClaimType.results_claim:
            return (
                "review",
                "provide_evidence",
                "Individual results may vary. Past performance does not guarantee future results.",
            )

        if claim_type == ClaimType.certification_claim:
            return (
                "review",
                "provide_evidence",
                None,
            )

        if claim_type == ClaimType.guarantee_claim:
            if not self.constraints.guarantee_language.get("can_offer_guarantee", False):
                return (
                    "block",
                    "remove_claim",
                    None,
                )
            return (
                "review",
                "add_disclaimer",
                self.constraints.guarantee_language.get("guarantee_text", "Terms and conditions apply."),
            )

        if claim_type == ClaimType.comparison_claim:
            if self.constraints.competitor_mention_policy == CompetitorMentionPolicy.never.value:
                return ("block", "remove_claim", None)
            return (
                "review",
                "provide_evidence",
                "Based on publicly available information as of the date of publication.",
            )

        if claim_type == ClaimType.endorsement_claim:
            return (
                "review",
                "provide_evidence",
                None,
            )

        if claim_type == ClaimType.time_claim:
            return (
                "review",
                "provide_evidence",
                "Service times may vary based on location, availability, and other factors.",
            )

        if claim_type == ClaimType.award_claim:
            return (
                "review",
                "provide_evidence",
                None,
            )

        # Fallback for any future claim types
        return ("review", "provide_evidence", None)

    @staticmethod
    def _estimate_location(position: int, full_text: str) -> str:
        """Estimate a human-readable location from a character position.

        Splits the text into logical sections and returns a label like
        'headline', 'body paragraph 3', 'CTA', or 'closing'.
        """
        if not full_text:
            return "unknown"

        text_length = len(full_text)
        relative_pos = position / text_length if text_length > 0 else 0

        # Check for common structural markers
        lines = full_text[:position].split("\n")
        line_number = len(lines)

        # Heuristic: first line or first 5% is headline territory
        if line_number <= 1 or relative_pos < 0.05:
            return "headline"

        # Last 10% is CTA / closing territory
        if relative_pos > 0.90:
            return "closing / CTA"

        # Count non-empty lines to estimate paragraph number
        paragraphs_before = 0
        current_text = full_text[:position]
        for block in re.split(r"\n\s*\n", current_text):
            if block.strip():
                paragraphs_before += 1

        if paragraphs_before <= 1:
            return "opening paragraph"

        return f"body paragraph {paragraphs_before}"
