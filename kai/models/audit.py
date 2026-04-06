"""Canonical audit data models for the Kai Marketing OS.

This module defines the structured output format that ALL audit engines
(website conversion, local SEO, content, email, ads, social, CRO, etc.)
produce.  Downstream systems -- proposal generation, action planning,
operator review -- consume these models directly without re-parsing prose.

Design principles
-----------------
1. **Structured data, not prose.**  Every finding has an ID, category,
   severity, evidence, recommendation, and estimated impact.
2. **Multi-engine composition.**  Multiple audit engines contribute
   findings to a single ``AuditResult``.
3. **Unknowns preserved.**  Missing data is explicitly flagged via
   ``MissingDataFlag`` so operators know what the audit could *not*
   assess.
4. **Archetype-aware.**  Findings carry archetype and business-stage
   relevance so downstream systems can filter and prioritize.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.

Migration note
--------------
The older prototype at ``kai/runtime/audit.py`` uses stdlib dataclasses +
``SerializableModel``.  The two can coexist during the migration period.
This module does **not** import anything from ``kai/runtime/``.
"""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:
        """Minimal pydantic-like fallback."""

        def __init__(self, **data):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self):
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self):
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ============================================================================
# Enums
# ============================================================================


class FindingSeverity(str, Enum):
    """How bad is it?

    Severity describes the current impact of the issue on the business.
    """

    CRITICAL = "critical"   # Actively losing revenue or trust right now; blocks meaningful operation
    HIGH = "high"           # Significant opportunity loss; major gap in marketing posture
    MEDIUM = "medium"       # Notable optimization opportunity; moderate impact
    LOW = "low"             # Minor polish item; nice-to-have improvement
    INFO = "info"           # Observation or context; no action required


class FindingPriority(str, Enum):
    """When should it be fixed?

    Priority is auto-mapped from severity by default but can be
    overridden when business context warrants a different timeline.
    """

    P0 = "P0"  # Fix this week (maps from CRITICAL)
    P1 = "P1"  # Fix this month (maps from HIGH)
    P2 = "P2"  # Fix this quarter (maps from MEDIUM)
    P3 = "P3"  # Backlog (maps from LOW/INFO)


class FindingSource(str, Enum):
    """How was this finding determined?

    Distinguishes between findings derived from static profile data,
    live connected integrations, indirect inference, and missing data.
    """

    STATIC = "static"           # Determined from profile data alone (no live data needed)
    CONNECTED = "connected"     # Determined from connected integration data (analytics, reviews, etc.)
    INFERRED = "inferred"       # Inferred from indirect signals (not directly observed)
    MISSING_DATA = "missing_data"  # The audit could not assess this area due to missing data


class EffortLevel(str, Enum):
    """How much work does it take to fix?

    Used to identify quick wins and set realistic expectations.
    """

    QUICK_WIN = "quick_win"       # Can be done in under 1 hour
    MODERATE = "moderate"         # Requires 1-8 hours of work
    SIGNIFICANT = "significant"   # Requires a week or more
    ONGOING = "ongoing"           # Requires continuous effort (not a one-time fix)


class ImpactLevel(str, Enum):
    """What is the expected impact of addressing this finding?"""

    HIGH = "high"       # Expected to meaningfully move primary KPIs
    MEDIUM = "medium"   # Expected to improve secondary KPIs or user experience
    LOW = "low"         # Marginal improvement expected


# ============================================================================
# Severity -> Priority mapping
# ============================================================================

_SEVERITY_PRIORITY_MAP: Dict[str, str] = {
    FindingSeverity.CRITICAL.value: FindingPriority.P0.value,
    FindingSeverity.HIGH.value: FindingPriority.P1.value,
    FindingSeverity.MEDIUM.value: FindingPriority.P2.value,
    FindingSeverity.LOW.value: FindingPriority.P3.value,
    FindingSeverity.INFO.value: FindingPriority.P3.value,
}


# ============================================================================
# Data Models
# ============================================================================


class Evidence(BaseModel):
    """A single piece of evidence supporting an audit finding.

    Evidence is typed so downstream systems can render it appropriately
    (e.g., display a URL as a link, render a metric as a chart).
    """

    evidence_type: str  # "text", "url", "screenshot", "metric", "comparison", "checklist_item", "missing_data"
    value: str          # The evidence content (text, URL, metric value, etc.)
    context: Optional[str] = None        # Additional context explaining why this evidence matters
    source_label: Optional[str] = None   # Where this evidence came from (e.g., "Google Business Profile", "Website homepage")


class AuditFinding(BaseModel):
    """A single diagnosed issue from an audit.

    Every finding is structured data -- not prose.  It has an ID,
    category, severity, evidence, recommendation, and estimated impact.
    Downstream systems should never need to re-parse prose to understand
    what was found.
    """

    id: str
    category: str                                           # Audit category (e.g., "website_conversion", "local_seo")
    subcategory: Optional[str] = None                       # More specific classification within the category
    severity: str                                           # FindingSeverity value
    priority: str                                           # FindingPriority value (auto-mapped from severity, can be overridden)
    title: str                                              # One-line summary (max 100 chars)
    description: str                                        # Detailed explanation of what was found and why it matters
    evidence: List[Evidence] = Field(default_factory=list)  # Supporting evidence
    recommendation: str                                     # Specific, actionable recommendation
    estimated_impact: str = ImpactLevel.MEDIUM.value        # ImpactLevel value
    effort: str = EffortLevel.MODERATE.value                # EffortLevel value
    source: str = FindingSource.STATIC.value                # FindingSource value
    business_stage_relevance: List[str] = Field(default_factory=list)   # Which business stages this is most relevant for
    archetype_relevance: List[str] = Field(default_factory=list)        # Which archetypes this is most relevant for
    related_findings: List[str] = Field(default_factory=list)           # IDs of related findings
    tags: List[str] = Field(default_factory=list)                       # Freeform tags for filtering and grouping
    kaicalls_relevant: bool = False                                     # Whether this relates to phone lead capture
    metadata: Dict[str, Any] = Field(default_factory=dict)              # Catch-all for finding-specific data


class CategoryScorecard(BaseModel):
    """Scored summary for a single audit category.

    Aggregates findings into a score, counts by severity, and surfaces
    the most impactful recommendations and quick wins.
    """

    category: str                                                   # Audit category ID
    category_display_name: str                                      # Human-readable category name
    score: float                                                    # 0-100 score for this category
    max_score: float = 100.0                                        # Maximum possible score
    weight: float = 1.0                                             # Weighting factor for overall score calculation
    findings_count: int = 0                                         # Total findings in this category
    critical_count: int = 0                                         # CRITICAL findings
    high_count: int = 0                                             # HIGH findings
    medium_count: int = 0                                           # MEDIUM findings
    low_count: int = 0                                              # LOW findings
    info_count: int = 0                                             # INFO findings
    missing_data_count: int = 0                                     # MISSING_DATA source findings
    top_recommendations: List[str] = Field(default_factory=list)    # Top 3 recommendations for this category
    quick_wins: List[str] = Field(default_factory=list)             # Quick win finding IDs in this category


class MissingDataFlag(BaseModel):
    """Explicit record of data the audit could not assess.

    Preserves unknowns so operators know exactly what to provide
    for a more complete audit.
    """

    field_path: str                                                 # What data is missing (dot-notation path)
    impact_description: str                                         # What the audit can't assess without this data
    affected_categories: List[str] = Field(default_factory=list)    # Which audit categories are impacted
    how_to_provide: str                                             # Instructions for the operator to provide this data


class AuditResult(BaseModel):
    """Complete audit result for a business profile.

    This is the top-level handoff contract.  It answers:
    - What is the overall health of the business's marketing posture?
    - What are the most critical issues?
    - What are the quick wins?
    - What couldn't the audit assess (missing data)?

    Multiple audit engines contribute findings to a single result via
    ``compile_audit_result()``.
    """

    audit_id: str
    business_id: str                                                        # BusinessProfile.id
    audit_type: str                                                         # e.g., "full_marketing_audit", "website_conversion_audit"
    archetype: Optional[str] = None                                         # Archetype used for this audit
    overlays_applied: List[str] = Field(default_factory=list)               # Overlays applied during this audit
    timestamp: str                                                          # ISO timestamp of when the audit was run
    findings: List[AuditFinding] = Field(default_factory=list)              # All findings from all engines
    category_scores: Dict[str, CategoryScorecard] = Field(default_factory=dict)  # Scorecards per category
    overall_health_score: float = 0.0                                       # 0-100 weighted composite score
    missing_data_flags: List[MissingDataFlag] = Field(default_factory=list) # What the audit couldn't assess
    executive_summary: str = ""                                             # 3-5 sentence summary
    top_priorities: List[str] = Field(default_factory=list)                 # Ordered list of top 5 finding IDs
    quick_wins: List[str] = Field(default_factory=list)                     # Finding IDs that are quick wins
    total_findings: int = 0                                                 # Count of all findings
    critical_count: int = 0                                                 # Total CRITICAL findings across all categories
    high_count: int = 0                                                     # Total HIGH findings
    engines_run: List[str] = Field(default_factory=list)                    # Which audit engines contributed
    metadata: Dict[str, Any] = Field(default_factory=dict)                  # Catch-all


# ============================================================================
# Utility Functions
# ============================================================================


def severity_to_priority(severity: str) -> str:
    """Map a severity level to its default priority.

    CRITICAL -> P0, HIGH -> P1, MEDIUM -> P2, LOW -> P3, INFO -> P3.

    Falls back to P2 for unrecognized severity values.
    """
    return _SEVERITY_PRIORITY_MAP.get(severity, FindingPriority.P2.value)


def create_finding(
    category: str,
    severity: str,
    title: str,
    description: str,
    recommendation: str,
    **kwargs: Any,
) -> AuditFinding:
    """Factory function for creating audit findings.

    Auto-generates a UUID-based ID if ``id`` is not provided in kwargs.
    Auto-maps severity to priority unless ``priority`` is explicitly
    provided.

    Parameters
    ----------
    category:
        Audit category this finding belongs to (e.g., "website_conversion").
    severity:
        FindingSeverity value (e.g., "critical", "high").
    title:
        One-line summary of the finding (max 100 chars).
    description:
        Detailed explanation of what was found and why it matters.
    recommendation:
        Specific, actionable recommendation to address this finding.
    **kwargs:
        Any additional ``AuditFinding`` fields (evidence, effort, tags, etc.).

    Returns
    -------
    AuditFinding
        A fully populated finding instance.
    """
    finding_id = kwargs.pop("id", None) or f"fnd_{uuid.uuid4().hex[:12]}"
    priority = kwargs.pop("priority", None) or severity_to_priority(severity)

    return AuditFinding(
        id=finding_id,
        category=category,
        severity=severity,
        priority=priority,
        title=title,
        description=description,
        recommendation=recommendation,
        **kwargs,
    )


def create_missing_data_finding(
    category: str,
    field_path: str,
    impact_description: str,
    how_to_provide: str,
    *,
    critical_gap: bool = False,
) -> AuditFinding:
    """Specialized factory for missing-data findings.

    Creates a finding that explicitly flags data the audit could not
    assess.  These findings are surfaced separately in the final
    ``AuditResult.missing_data_flags``.

    Parameters
    ----------
    category:
        Audit category this missing data affects.
    field_path:
        Dot-notation path of the missing data (e.g., "identity.website_url").
    impact_description:
        What the audit cannot assess without this data.
    how_to_provide:
        Instructions for the operator to provide this data.
    critical_gap:
        If True, sets severity to HIGH (the missing data blocks a
        meaningful assessment).  Otherwise defaults to INFO.

    Returns
    -------
    AuditFinding
        A finding with source = MISSING_DATA and appropriate evidence.
    """
    severity = FindingSeverity.HIGH.value if critical_gap else FindingSeverity.INFO.value

    return create_finding(
        category=category,
        severity=severity,
        title=f"Missing data: {field_path}",
        description=impact_description,
        recommendation=how_to_provide,
        source=FindingSource.MISSING_DATA.value,
        effort=EffortLevel.QUICK_WIN.value,
        estimated_impact=ImpactLevel.MEDIUM.value if critical_gap else ImpactLevel.LOW.value,
        evidence=[
            Evidence(
                evidence_type="missing_data",
                value=field_path,
                context=impact_description,
                source_label="Audit data completeness check",
            ),
        ],
        tags=["missing_data"],
        metadata={
            "field_path": field_path,
            "how_to_provide": how_to_provide,
            "critical_gap": critical_gap,
        },
    )


def compute_category_scorecard(
    category: str,
    findings: List[AuditFinding],
    display_name: str,
    weight: float = 1.0,
) -> CategoryScorecard:
    """Compute a scorecard for a single audit category.

    Scoring formula::

        score = 100 - (critical * 25 + high * 15 + medium * 8 + low * 3)

    Score is clamped to the range [0, 100].

    Parameters
    ----------
    category:
        Audit category ID.
    findings:
        All findings belonging to this category.
    display_name:
        Human-readable category name.
    weight:
        Weighting factor for overall score calculation.

    Returns
    -------
    CategoryScorecard
        Fully computed scorecard with severity counts, top recommendations,
        and quick win IDs.
    """
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    info_count = 0
    missing_data_count = 0

    for f in findings:
        sev = f.severity
        if sev == FindingSeverity.CRITICAL.value:
            critical_count += 1
        elif sev == FindingSeverity.HIGH.value:
            high_count += 1
        elif sev == FindingSeverity.MEDIUM.value:
            medium_count += 1
        elif sev == FindingSeverity.LOW.value:
            low_count += 1
        elif sev == FindingSeverity.INFO.value:
            info_count += 1

        # Count MISSING_DATA source findings separately
        src = f.source if hasattr(f, "source") else FindingSource.STATIC.value
        if src == FindingSource.MISSING_DATA.value:
            missing_data_count += 1

    # Compute raw score: 100 - penalty
    penalty = (critical_count * 25) + (high_count * 15) + (medium_count * 8) + (low_count * 3)
    score = max(0.0, min(100.0, 100.0 - penalty))

    # Extract top 3 recommendations from highest-severity findings
    # Sort findings by severity order for recommendation extraction
    severity_order = {
        FindingSeverity.CRITICAL.value: 0,
        FindingSeverity.HIGH.value: 1,
        FindingSeverity.MEDIUM.value: 2,
        FindingSeverity.LOW.value: 3,
        FindingSeverity.INFO.value: 4,
    }
    sorted_findings = sorted(
        findings,
        key=lambda f: severity_order.get(f.severity, 99),
    )
    top_recommendations = [
        f.recommendation for f in sorted_findings[:3] if f.recommendation
    ]

    # Extract quick win IDs: effort = QUICK_WIN and impact = HIGH or MEDIUM
    quick_win_ids = [
        f.id
        for f in findings
        if (
            f.effort == EffortLevel.QUICK_WIN.value
            and f.estimated_impact in (ImpactLevel.HIGH.value, ImpactLevel.MEDIUM.value)
        )
    ]

    return CategoryScorecard(
        category=category,
        category_display_name=display_name,
        score=round(score, 1),
        weight=weight,
        findings_count=len(findings),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        info_count=info_count,
        missing_data_count=missing_data_count,
        top_recommendations=top_recommendations,
        quick_wins=quick_win_ids,
    )


def compute_overall_score(scorecards: Dict[str, CategoryScorecard]) -> float:
    """Compute the weighted overall health score from category scorecards.

    Returns a 0-100 weighted average using each scorecard's ``weight``
    field.  Returns 0.0 if no scorecards are provided or total weight
    is zero.

    Parameters
    ----------
    scorecards:
        Dictionary mapping category ID to ``CategoryScorecard``.

    Returns
    -------
    float
        Weighted average score in the range [0, 100].
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for scorecard in scorecards.values():
        total_weight += scorecard.weight
        weighted_sum += scorecard.score * scorecard.weight

    if total_weight == 0.0:
        return 0.0

    return round(weighted_sum / total_weight, 1)


def compile_audit_result(
    business_id: str,
    audit_type: str,
    engine_findings: Dict[str, List[AuditFinding]],
    archetype: Optional[str] = None,
    overlays: Optional[List[str]] = None,
    *,
    category_display_names: Optional[Dict[str, str]] = None,
    category_weights: Optional[Dict[str, float]] = None,
) -> AuditResult:
    """Assemble a complete AuditResult from multi-engine findings.

    This is the main assembly function.  It takes findings from multiple
    audit engines (keyed by engine name), computes category scorecards,
    extracts missing data flags, generates an executive summary, and
    identifies top priorities and quick wins.

    Parameters
    ----------
    business_id:
        The ``BusinessProfile.id`` being audited.
    audit_type:
        Audit type label (e.g., "full_marketing_audit").
    engine_findings:
        Dictionary mapping engine name to that engine's list of findings.
    archetype:
        Archetype used for this audit (optional).
    overlays:
        Overlays applied during this audit (optional).
    category_display_names:
        Optional mapping of category ID to human-readable name.
        Defaults to title-cased, underscore-replaced category ID.
    category_weights:
        Optional mapping of category ID to weight.  Defaults to 1.0.

    Returns
    -------
    AuditResult
        A fully assembled audit result with scores, flags, and summaries.
    """
    if category_display_names is None:
        category_display_names = {}
    if category_weights is None:
        category_weights = {}

    # Flatten all findings and track engine names
    all_findings: List[AuditFinding] = []
    engines_run: List[str] = []

    for engine_name, findings in engine_findings.items():
        engines_run.append(engine_name)
        all_findings.extend(findings)

    # Group findings by category
    findings_by_category: Dict[str, List[AuditFinding]] = {}
    for finding in all_findings:
        cat = finding.category
        if cat not in findings_by_category:
            findings_by_category[cat] = []
        findings_by_category[cat].append(finding)

    # Compute category scorecards
    category_scores: Dict[str, CategoryScorecard] = {}
    for cat, cat_findings in findings_by_category.items():
        display_name = category_display_names.get(
            cat, cat.replace("_", " ").title()
        )
        weight = category_weights.get(cat, 1.0)
        category_scores[cat] = compute_category_scorecard(
            category=cat,
            findings=cat_findings,
            display_name=display_name,
            weight=weight,
        )

    # Compute overall health score
    overall_health_score = compute_overall_score(category_scores)

    # Extract missing data flags from MISSING_DATA source findings
    missing_data_flags: List[MissingDataFlag] = []
    for finding in all_findings:
        if finding.source == FindingSource.MISSING_DATA.value:
            field_path = finding.metadata.get("field_path", finding.title) if hasattr(finding, "metadata") else finding.title
            how_to_provide = finding.metadata.get("how_to_provide", finding.recommendation) if hasattr(finding, "metadata") else finding.recommendation
            missing_data_flags.append(
                MissingDataFlag(
                    field_path=field_path,
                    impact_description=finding.description,
                    affected_categories=[finding.category],
                    how_to_provide=how_to_provide,
                )
            )

    # Count totals
    total_findings = len(all_findings)
    total_critical = sum(1 for f in all_findings if f.severity == FindingSeverity.CRITICAL.value)
    total_high = sum(1 for f in all_findings if f.severity == FindingSeverity.HIGH.value)

    # Identify top priorities: sort by severity (critical first), then impact (high first)
    severity_order = {
        FindingSeverity.CRITICAL.value: 0,
        FindingSeverity.HIGH.value: 1,
        FindingSeverity.MEDIUM.value: 2,
        FindingSeverity.LOW.value: 3,
        FindingSeverity.INFO.value: 4,
    }
    impact_order = {
        ImpactLevel.HIGH.value: 0,
        ImpactLevel.MEDIUM.value: 1,
        ImpactLevel.LOW.value: 2,
    }
    prioritized = sorted(
        all_findings,
        key=lambda f: (
            severity_order.get(f.severity, 99),
            impact_order.get(f.estimated_impact, 99),
        ),
    )
    top_priorities = [f.id for f in prioritized[:5]]

    # Identify quick wins: high or medium impact, quick_win effort
    quick_wins = [
        f.id
        for f in all_findings
        if (
            f.effort == EffortLevel.QUICK_WIN.value
            and f.estimated_impact in (ImpactLevel.HIGH.value, ImpactLevel.MEDIUM.value)
        )
    ]

    # Generate executive summary
    executive_summary = _generate_executive_summary(
        overall_health_score=overall_health_score,
        total_findings=total_findings,
        total_critical=total_critical,
        total_high=total_high,
        category_scores=category_scores,
        missing_data_count=len(missing_data_flags),
        quick_win_count=len(quick_wins),
    )

    # Build the timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    return AuditResult(
        audit_id=f"aud_{uuid.uuid4().hex[:12]}",
        business_id=business_id,
        audit_type=audit_type,
        archetype=archetype,
        overlays_applied=overlays or [],
        timestamp=timestamp,
        findings=prioritized,
        category_scores=category_scores,
        overall_health_score=overall_health_score,
        missing_data_flags=missing_data_flags,
        executive_summary=executive_summary,
        top_priorities=top_priorities,
        quick_wins=quick_wins,
        total_findings=total_findings,
        critical_count=total_critical,
        high_count=total_high,
        engines_run=engines_run,
    )


def format_finding_summary(finding: AuditFinding) -> str:
    """Format a finding as a one-line summary string.

    Output format::

        [SEVERITY] [CATEGORY] -- TITLE (EFFORT, IMPACT)

    Suitable for CLI display or plain-text reports.

    Parameters
    ----------
    finding:
        The ``AuditFinding`` to format.

    Returns
    -------
    str
        A single-line formatted summary.
    """
    severity_label = finding.severity.upper()
    category_label = finding.category.upper().replace("_", " ")
    effort_label = finding.effort.replace("_", " ").title()
    impact_label = finding.estimated_impact.replace("_", " ").title()

    return f"[{severity_label}] [{category_label}] -- {finding.title} ({effort_label}, {impact_label})"


# ============================================================================
# Internal helpers
# ============================================================================


def _generate_executive_summary(
    overall_health_score: float,
    total_findings: int,
    total_critical: int,
    total_high: int,
    category_scores: Dict[str, CategoryScorecard],
    missing_data_count: int,
    quick_win_count: int,
) -> str:
    """Generate a 3-5 sentence executive summary of the audit results.

    The summary is deterministic and based on score thresholds and
    finding counts -- not LLM-generated prose.
    """
    parts: List[str] = []

    # Overall health assessment
    if overall_health_score >= 80:
        parts.append(
            f"Marketing health score is {overall_health_score}/100 -- the business has a strong marketing posture with room for optimization."
        )
    elif overall_health_score >= 60:
        parts.append(
            f"Marketing health score is {overall_health_score}/100 -- the business has a functional marketing foundation but notable gaps exist."
        )
    elif overall_health_score >= 40:
        parts.append(
            f"Marketing health score is {overall_health_score}/100 -- significant marketing gaps are limiting growth potential."
        )
    else:
        parts.append(
            f"Marketing health score is {overall_health_score}/100 -- critical marketing infrastructure issues require immediate attention."
        )

    # Finding counts
    parts.append(
        f"The audit identified {total_findings} findings across {len(category_scores)} categories."
    )

    # Critical/high urgency callout
    if total_critical > 0 and total_high > 0:
        parts.append(
            f"{total_critical} critical and {total_high} high-severity issues need priority resolution."
        )
    elif total_critical > 0:
        parts.append(
            f"{total_critical} critical issue{'s' if total_critical != 1 else ''} need{'s' if total_critical == 1 else ''} immediate attention."
        )
    elif total_high > 0:
        parts.append(
            f"{total_high} high-severity issue{'s' if total_high != 1 else ''} should be addressed this month."
        )

    # Weakest category
    if category_scores:
        weakest = min(category_scores.values(), key=lambda sc: sc.score)
        if weakest.score < 60:
            parts.append(
                f"{weakest.category_display_name} is the weakest area at {weakest.score}/100 and should be the primary focus."
            )

    # Quick wins and missing data
    addendum_parts: List[str] = []
    if quick_win_count > 0:
        addendum_parts.append(f"{quick_win_count} quick win{'s' if quick_win_count != 1 else ''} available")
    if missing_data_count > 0:
        addendum_parts.append(f"{missing_data_count} data gap{'s' if missing_data_count != 1 else ''} limited the audit scope")
    if addendum_parts:
        parts.append(f"{'; '.join(addendum_parts)}.")

    return " ".join(parts)
