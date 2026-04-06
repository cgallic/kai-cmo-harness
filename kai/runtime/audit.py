"""Audit engine — structured diagnosis for business profiles.

Produces AuditFinding and AuditResult objects that downstream layers
(proposal generation, operator review) consume without reinterpreting prose.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from .models import SerializableModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FindingSeverity(str, Enum):
    """How bad is it?"""
    CRITICAL = "critical"     # Actively losing revenue / trust right now
    HIGH = "high"             # Major gap, significant missed opportunity
    MEDIUM = "medium"         # Notable gap, moderate impact
    LOW = "low"               # Minor issue, nice-to-have improvement


class FindingPriority(str, Enum):
    """When should it be fixed?"""
    P0 = "P0"  # Fix this week
    P1 = "P1"  # Fix this month
    P2 = "P2"  # Fix this quarter
    P3 = "P3"  # Backlog


class AuditCategory(str, Enum):
    """Local-service audit categories."""
    OFFER_CLARITY = "offer_clarity"
    TRUST_AND_PROOF = "trust_and_proof"
    CONVERSION_PATH = "conversion_path"
    LOCAL_SEO = "local_seo"
    SPEED_TO_LEAD = "speed_to_lead"
    REVIEWS_REPUTATION = "reviews_reputation"
    CHANNEL_PRESENCE = "channel_presence"
    FOLLOW_UP_GAPS = "follow_up_gaps"


# ---------------------------------------------------------------------------
# Category metadata — weights and display
# ---------------------------------------------------------------------------

CATEGORY_WEIGHTS: Dict[AuditCategory, float] = {
    AuditCategory.OFFER_CLARITY: 3.0,
    AuditCategory.TRUST_AND_PROOF: 5.0,
    AuditCategory.CONVERSION_PATH: 5.0,
    AuditCategory.LOCAL_SEO: 3.0,
    AuditCategory.SPEED_TO_LEAD: 4.0,
    AuditCategory.REVIEWS_REPUTATION: 5.0,
    AuditCategory.CHANNEL_PRESENCE: 2.0,
    AuditCategory.FOLLOW_UP_GAPS: 2.0,
}

CATEGORY_DISPLAY: Dict[AuditCategory, str] = {
    AuditCategory.OFFER_CLARITY: "Offer Clarity",
    AuditCategory.TRUST_AND_PROOF: "Trust & Proof",
    AuditCategory.CONVERSION_PATH: "Conversion Path",
    AuditCategory.LOCAL_SEO: "Local SEO & Local Intent",
    AuditCategory.SPEED_TO_LEAD: "Speed-to-Lead",
    AuditCategory.REVIEWS_REPUTATION: "Reviews & Reputation",
    AuditCategory.CHANNEL_PRESENCE: "Channel Presence",
    AuditCategory.FOLLOW_UP_GAPS: "Follow-Up Gaps",
}

# Severity → priority mapping (default; can be overridden per finding)
_SEVERITY_PRIORITY_MAP: Dict[FindingSeverity, FindingPriority] = {
    FindingSeverity.CRITICAL: FindingPriority.P0,
    FindingSeverity.HIGH: FindingPriority.P1,
    FindingSeverity.MEDIUM: FindingPriority.P2,
    FindingSeverity.LOW: FindingPriority.P3,
}


# ---------------------------------------------------------------------------
# AuditFinding — one diagnosed issue
# ---------------------------------------------------------------------------


def _new_finding_id() -> str:
    return f"fnd_{uuid.uuid4().hex[:12]}"


@dataclass
class AuditFinding(SerializableModel):
    """A single diagnosed issue from an audit.

    Compact and machine-readable so the proposal layer can act on it
    without reinterpreting prose.
    """
    finding_id: str = ""
    category: str = ""              # AuditCategory value
    title: str = ""                 # Short headline (operator-readable)
    summary: str = ""               # 1-2 sentence explanation
    severity: str = "medium"        # FindingSeverity value
    priority: str = "P2"            # FindingPriority value
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommended_direction: str = "" # What type of action should be proposed
    affected_channel: str = ""      # website, gbp, social, paid_media, phone, email, offline
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.finding_id:
            self.finding_id = _new_finding_id()


# ---------------------------------------------------------------------------
# CategoryResult — scored rollup for one category
# ---------------------------------------------------------------------------


@dataclass
class CategoryResult(SerializableModel):
    """Scored result for a single audit category."""
    category: str = ""            # AuditCategory value
    display_name: str = ""
    score: float = 0.0            # 0-100
    weight: float = 1.0
    findings: List[AuditFinding] = field(default_factory=list)

    @property
    def grade(self) -> str:
        if self.score >= 90:
            return "A"
        if self.score >= 75:
            return "B"
        if self.score >= 60:
            return "C"
        if self.score >= 40:
            return "D"
        return "F"

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.CRITICAL.value)


# ---------------------------------------------------------------------------
# AuditResult — the full audit output
# ---------------------------------------------------------------------------


@dataclass
class AuditResult(SerializableModel):
    """Complete audit result for a business profile.

    This is the handoff contract to the proposal layer.  It answers:
    - What is wrong?
    - Why does it matter?
    - How urgent is it?
    - Which channel should be touched?
    - What type of action should be proposed?
    """
    audit_id: str = ""
    brand_id: str = ""
    archetype: str = "local-service"
    overall_score: float = 0.0     # 0-100 weighted
    categories: List[CategoryResult] = field(default_factory=list)
    prioritized_findings: List[AuditFinding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.audit_id:
            self.audit_id = f"aud_{uuid.uuid4().hex[:12]}"

    @property
    def overall_grade(self) -> str:
        if self.overall_score >= 90:
            return "A"
        if self.overall_score >= 75:
            return "B"
        if self.overall_score >= 60:
            return "C"
        if self.overall_score >= 40:
            return "D"
        return "F"

    @property
    def total_findings(self) -> int:
        return len(self.prioritized_findings)

    @property
    def critical_findings(self) -> List[AuditFinding]:
        return [f for f in self.prioritized_findings if f.severity == FindingSeverity.CRITICAL.value]

    @property
    def top_fixes(self) -> List[AuditFinding]:
        """Top 5 findings by priority then severity."""
        return self.prioritized_findings[:5]


# ---------------------------------------------------------------------------
# Prioritization
# ---------------------------------------------------------------------------

_PRIORITY_ORDER = {
    FindingPriority.P0.value: 0,
    FindingPriority.P1.value: 1,
    FindingPriority.P2.value: 2,
    FindingPriority.P3.value: 3,
}

_SEVERITY_ORDER = {
    FindingSeverity.CRITICAL.value: 0,
    FindingSeverity.HIGH.value: 1,
    FindingSeverity.MEDIUM.value: 2,
    FindingSeverity.LOW.value: 3,
}


def prioritize_findings(findings: List[AuditFinding]) -> List[AuditFinding]:
    """Sort findings by priority (P0 first), then severity (critical first)."""
    return sorted(
        findings,
        key=lambda f: (
            _PRIORITY_ORDER.get(f.priority, 99),
            _SEVERITY_ORDER.get(f.severity, 99),
        ),
    )


def severity_to_priority(severity: str) -> str:
    """Map a severity level to a default priority."""
    try:
        sev = FindingSeverity(severity)
    except ValueError:
        return FindingPriority.P2.value
    return _SEVERITY_PRIORITY_MAP[sev].value


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def compute_category_score(checks: List[Dict[str, Any]]) -> float:
    """Compute a 0-100 score from a list of check results.

    Each check is ``{"passed": bool, "weight": float (optional)}``.
    Returns weighted pass rate * 100.
    """
    if not checks:
        return 0.0
    total_weight = 0.0
    weighted_pass = 0.0
    for check in checks:
        w = float(check.get("weight", 1.0))
        total_weight += w
        if check.get("passed"):
            weighted_pass += w
    if total_weight == 0:
        return 0.0
    return round((weighted_pass / total_weight) * 100, 1)


def compute_overall_score(categories: List[CategoryResult]) -> float:
    """Compute weighted overall score from category results."""
    total_weight = 0.0
    weighted_sum = 0.0
    for cat in categories:
        total_weight += cat.weight
        weighted_sum += cat.score * cat.weight
    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 1)


# ---------------------------------------------------------------------------
# Local-service audit engine
# ---------------------------------------------------------------------------


class LocalServiceAuditor:
    """Runs the local-service audit against a business profile.

    The business profile is a plain dict with keys matching the
    local-service checklist sections.  Each section contains check
    results that the auditor scores and converts to findings.
    """

    def audit(self, profile: Dict[str, Any], brand_id: str = "") -> AuditResult:
        """Run the full local-service audit.

        ``profile`` keys (all optional — missing sections score 0):

        - ``offer_clarity``: list of checks
        - ``trust_and_proof``: list of checks
        - ``conversion_path``: list of checks
        - ``local_seo``: list of checks
        - ``speed_to_lead``: list of checks
        - ``reviews_reputation``: list of checks
        - ``channel_presence``: list of checks
        - ``follow_up_gaps``: list of checks

        Each check: ``{"id": str, "label": str, "passed": bool, "weight": float?, "evidence": dict?}``
        """
        all_findings: List[AuditFinding] = []
        category_results: List[CategoryResult] = []

        for cat in AuditCategory:
            checks = profile.get(cat.value, [])
            findings = self._evaluate_category(cat, checks)
            score = compute_category_score(checks) if checks else 0.0
            weight = CATEGORY_WEIGHTS.get(cat, 1.0)
            display = CATEGORY_DISPLAY.get(cat, cat.value)

            cr = CategoryResult(
                category=cat.value,
                display_name=display,
                score=score,
                weight=weight,
                findings=findings,
            )
            category_results.append(cr)
            all_findings.extend(findings)

        # Synthesize missing-section findings for empty categories
        for cat in AuditCategory:
            if not profile.get(cat.value):
                all_findings.append(self._missing_section_finding(cat))

        prioritized = prioritize_findings(all_findings)
        overall = compute_overall_score(category_results)

        return AuditResult(
            brand_id=brand_id,
            archetype="local-service",
            overall_score=overall,
            categories=category_results,
            prioritized_findings=prioritized,
        )

    # ------------------------------------------------------------------
    # Category evaluation
    # ------------------------------------------------------------------

    def _evaluate_category(
        self, category: AuditCategory, checks: List[Dict[str, Any]]
    ) -> List[AuditFinding]:
        """Convert failed checks into findings."""
        findings: List[AuditFinding] = []
        for check in checks:
            if check.get("passed"):
                continue
            findings.append(self._check_to_finding(category, check))
        return findings

    def _check_to_finding(
        self, category: AuditCategory, check: Dict[str, Any]
    ) -> AuditFinding:
        """Convert a single failed check into an AuditFinding."""
        severity = check.get("severity", self._default_severity(category))
        priority = check.get("priority", severity_to_priority(severity))
        return AuditFinding(
            category=category.value,
            title=check.get("label", "Untitled check"),
            summary=check.get("summary", f"Failed: {check.get('label', 'unknown check')}"),
            severity=severity,
            priority=priority,
            evidence=check.get("evidence", {}),
            recommended_direction=check.get(
                "recommended_direction",
                self._default_direction(category),
            ),
            affected_channel=check.get(
                "affected_channel",
                self._default_channel(category),
            ),
            metadata=check.get("metadata", {}),
        )

    def _missing_section_finding(self, category: AuditCategory) -> AuditFinding:
        """Generate a finding for an entirely missing audit section."""
        display = CATEGORY_DISPLAY.get(category, category.value)
        return AuditFinding(
            category=category.value,
            title=f"No data for {display}",
            summary=f"The {display} section was not evaluated. This likely means "
                    f"no data was provided or the section was skipped entirely.",
            severity=FindingSeverity.HIGH.value,
            priority=FindingPriority.P1.value,
            evidence={"section_missing": True},
            recommended_direction=f"Evaluate {display} and provide audit data",
            affected_channel=self._default_channel(category),
        )

    # ------------------------------------------------------------------
    # Defaults per category
    # ------------------------------------------------------------------

    _CATEGORY_SEVERITY: Dict[AuditCategory, str] = {
        AuditCategory.OFFER_CLARITY: FindingSeverity.MEDIUM.value,
        AuditCategory.TRUST_AND_PROOF: FindingSeverity.HIGH.value,
        AuditCategory.CONVERSION_PATH: FindingSeverity.CRITICAL.value,
        AuditCategory.LOCAL_SEO: FindingSeverity.MEDIUM.value,
        AuditCategory.SPEED_TO_LEAD: FindingSeverity.CRITICAL.value,
        AuditCategory.REVIEWS_REPUTATION: FindingSeverity.HIGH.value,
        AuditCategory.CHANNEL_PRESENCE: FindingSeverity.LOW.value,
        AuditCategory.FOLLOW_UP_GAPS: FindingSeverity.MEDIUM.value,
    }

    _CATEGORY_CHANNEL: Dict[AuditCategory, str] = {
        AuditCategory.OFFER_CLARITY: "website",
        AuditCategory.TRUST_AND_PROOF: "website",
        AuditCategory.CONVERSION_PATH: "website",
        AuditCategory.LOCAL_SEO: "gbp",
        AuditCategory.SPEED_TO_LEAD: "phone",
        AuditCategory.REVIEWS_REPUTATION: "gbp",
        AuditCategory.CHANNEL_PRESENCE: "social",
        AuditCategory.FOLLOW_UP_GAPS: "email",
    }

    _CATEGORY_DIRECTION: Dict[AuditCategory, str] = {
        AuditCategory.OFFER_CLARITY: "Clarify service offerings and pricing on website",
        AuditCategory.TRUST_AND_PROOF: "Add trust signals: licenses, insurance, certifications, testimonials",
        AuditCategory.CONVERSION_PATH: "Improve phone CTA visibility and contact form placement",
        AuditCategory.LOCAL_SEO: "Optimize GBP, citations, and local keyword targeting",
        AuditCategory.SPEED_TO_LEAD: "Set up KaiCalls AI receptionist for missed call handling",
        AuditCategory.REVIEWS_REPUTATION: "Implement review generation process after every job",
        AuditCategory.CHANNEL_PRESENCE: "Claim and maintain profiles on key local platforms",
        AuditCategory.FOLLOW_UP_GAPS: "Build post-job follow-up sequence: thank-you, review request, referral ask",
    }

    def _default_severity(self, category: AuditCategory) -> str:
        return self._CATEGORY_SEVERITY.get(category, FindingSeverity.MEDIUM.value)

    def _default_channel(self, category: AuditCategory) -> str:
        return self._CATEGORY_CHANNEL.get(category, "website")

    def _default_direction(self, category: AuditCategory) -> str:
        return self._CATEGORY_DIRECTION.get(category, "Review and remediate")
