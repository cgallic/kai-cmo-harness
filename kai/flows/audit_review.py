"""Audit review flow -- run audits, summarize, drill down, and generate proposals.

Provides a structured workflow for reviewing marketing audit results:

1. Start an audit review (full or scoped to a category)
2. Get an executive summary with overall score and top findings
3. Drill down into specific categories for detailed analysis
4. Generate proposals from audit findings

The flow loads audit data from the workspace directory and compiles
it into review-ready structures.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None on failure."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# State model
# ---------------------------------------------------------------------------

@dataclass
class AuditReviewState:
    """Serializable state for the audit review flow."""

    business_id: str = ""
    audit_result: Optional[Dict[str, Any]] = None
    review_bundle: Optional[Dict[str, Any]] = None
    operator_notes: List[str] = field(default_factory=list)
    drill_down_category: Optional[str] = None

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Default audit categories and scoring rubrics
# ---------------------------------------------------------------------------

_DEFAULT_AUDIT_CATEGORIES: List[Dict[str, Any]] = [
    {"name": "seo", "label": "SEO & Organic Search", "weight": 1.5},
    {"name": "content", "label": "Content Quality", "weight": 1.2},
    {"name": "website", "label": "Website & UX", "weight": 1.3},
    {"name": "email", "label": "Email Marketing", "weight": 1.0},
    {"name": "social", "label": "Social Media", "weight": 0.8},
    {"name": "paid", "label": "Paid Advertising", "weight": 1.0},
    {"name": "reviews", "label": "Reviews & Reputation", "weight": 1.1},
    {"name": "analytics", "label": "Analytics & Tracking", "weight": 0.9},
    {"name": "lead_capture", "label": "Lead Capture & CRO", "weight": 1.4},
    {"name": "gbp", "label": "Google Business Profile", "weight": 1.2},
]


# ---------------------------------------------------------------------------
# AuditReviewFlow
# ---------------------------------------------------------------------------

class AuditReviewFlow:
    """Run audits, build summaries, drill down, and generate proposals.

    Usage::

        flow = AuditReviewFlow(workspace_dir="workspace")
        state = flow.start("biz_abc123", scope="full")
        summary = flow.get_executive_summary(state)
        detail = flow.drill_down(state, "seo")
        proposals = flow.generate_proposals_from_audit(state)
    """

    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = workspace_dir

    # -- lifecycle -------------------------------------------------------

    def start(self, business_id: str, scope: str = "full") -> AuditReviewState:
        """Run or load audits and compile a review bundle.

        Attempts to load existing audit data from the workspace.  If
        none is found, builds a default audit structure with empty
        scores that downstream audit engines can populate.
        """
        audit_result = self._load_or_build_audit(business_id, scope)

        review_bundle = self._compile_review_bundle(audit_result)

        return AuditReviewState(
            business_id=business_id,
            audit_result=audit_result,
            review_bundle=review_bundle,
        )

    # -- executive summary -----------------------------------------------

    def get_executive_summary(self, state: AuditReviewState) -> Dict[str, Any]:
        """Return a high-level executive summary of the audit results.

        Returns
        -------
        dict with keys:
            overall_score, category_scores, top_3_critical_findings,
            top_3_quick_wins, recommended_focus_area
        """
        audit = state.audit_result or {}
        categories = audit.get("categories", [])

        category_scores: Dict[str, Any] = {}
        all_findings: List[Dict[str, Any]] = []
        total_score = 0
        total_max = 0

        for cat in categories:
            cat_name = cat.get("category", cat.get("name", "unknown"))
            score = cat.get("score", 0)
            max_score = cat.get("max_score", 100)
            category_scores[cat_name] = {
                "score": score,
                "max_score": max_score,
                "pct": round((score / max_score * 100), 1) if max_score > 0 else 0.0,
            }
            total_score += score
            total_max += max_score

            for finding in cat.get("findings", []):
                finding_copy = dict(finding)
                finding_copy["category"] = cat_name
                all_findings.append(finding_copy)

        # Separate critical findings and quick wins
        critical = sorted(
            [f for f in all_findings if f.get("severity") == "critical"],
            key=lambda f: f.get("impact_score", 0),
            reverse=True,
        )
        quick_wins = sorted(
            [f for f in all_findings if f.get("effort") == "low" and f.get("impact_score", 0) > 0],
            key=lambda f: f.get("impact_score", 0) / max(f.get("effort_score", 1), 1),
            reverse=True,
        )

        # Determine recommended focus area: the category with the lowest pct score
        focus_area = "seo"  # default
        lowest_pct = 100.0
        for cat_name, info in category_scores.items():
            if info["pct"] < lowest_pct:
                lowest_pct = info["pct"]
                focus_area = cat_name

        overall_pct = round((total_score / total_max * 100), 1) if total_max > 0 else 0.0

        return {
            "overall_score": overall_pct,
            "category_scores": category_scores,
            "top_3_critical_findings": [self._summarize_finding(f) for f in critical[:3]],
            "top_3_quick_wins": [self._summarize_finding(f) for f in quick_wins[:3]],
            "recommended_focus_area": focus_area,
        }

    # -- drill-down ------------------------------------------------------

    def drill_down(self, state: AuditReviewState, category: str) -> Dict[str, Any]:
        """Show all findings for a specific category with details.

        Returns
        -------
        dict with keys:
            category_score, findings (sorted by severity),
            recommendation_count
        """
        audit = state.audit_result or {}
        categories = audit.get("categories", [])

        target_cat: Optional[Dict[str, Any]] = None
        for cat in categories:
            cat_name = cat.get("category", cat.get("name", ""))
            if cat_name == category:
                target_cat = cat
                break

        if target_cat is None:
            return {
                "category_score": {"score": 0, "max_score": 100, "pct": 0.0},
                "findings": [],
                "recommendation_count": 0,
                "error": f"Category '{category}' not found in audit results.",
            }

        score = target_cat.get("score", 0)
        max_score = target_cat.get("max_score", 100)
        findings = list(target_cat.get("findings", []))

        # Sort findings by severity: critical > high > medium > low
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda f: severity_order.get(f.get("severity", "low"), 4))

        # Update drill-down state
        state.drill_down_category = category

        return {
            "category_score": {
                "score": score,
                "max_score": max_score,
                "pct": round((score / max_score * 100), 1) if max_score > 0 else 0.0,
            },
            "findings": findings,
            "recommendation_count": sum(
                1 for f in findings if f.get("recommendation")
            ),
        }

    # -- proposal generation ---------------------------------------------

    def generate_proposals_from_audit(self, state: AuditReviewState) -> Dict[str, Any]:
        """Generate actionable proposals from audit findings.

        Walks through each category's findings and creates proposals
        for items that have recommendations.  Groups proposals by
        priority and estimates total effort.
        """
        audit = state.audit_result or {}
        categories = audit.get("categories", [])

        proposals: List[Dict[str, Any]] = []

        for cat in categories:
            cat_name = cat.get("category", cat.get("name", "unknown"))
            for finding in cat.get("findings", []):
                recommendation = finding.get("recommendation", "")
                if not recommendation:
                    continue

                severity = finding.get("severity", "medium")
                priority = {
                    "critical": "urgent",
                    "high": "high",
                    "medium": "medium",
                    "low": "low",
                }.get(severity, "medium")

                effort = finding.get("effort", "medium")
                effort_hours = {"low": 2, "medium": 8, "high": 24}.get(effort, 8)

                proposals.append({
                    "proposal_id": _new_id("prop"),
                    "category": cat_name,
                    "title": finding.get("title", recommendation[:60]),
                    "description": recommendation,
                    "priority": priority,
                    "estimated_effort_hours": effort_hours,
                    "risk_tier": "low" if severity in ("low", "medium") else "medium",
                    "source_finding": finding.get("finding_id", ""),
                    "impact_estimate": finding.get("impact_score", 0),
                })

        # Group by priority
        proposals_by_priority: Dict[str, List[Dict[str, Any]]] = {}
        for p in proposals:
            prio = p["priority"]
            proposals_by_priority.setdefault(prio, []).append(p)

        total_effort = sum(p["estimated_effort_hours"] for p in proposals)

        return {
            "proposal_count": len(proposals),
            "proposals_by_priority": proposals_by_priority,
            "estimated_total_effort_hours": total_effort,
        }

    # -- private helpers -------------------------------------------------

    def _load_or_build_audit(self, business_id: str, scope: str) -> Dict[str, Any]:
        """Load an existing audit from disk or build an empty structure."""
        audit_dir = os.path.join(self.workspace_dir, "audits", business_id)
        if os.path.isdir(audit_dir):
            files = sorted(
                [f for f in os.listdir(audit_dir) if f.endswith(".json")],
                reverse=True,
            )
            for fname in files:
                data = _load_json_file(os.path.join(audit_dir, fname))
                if data is not None:
                    if scope != "full" and data.get("audit_type", "full") != scope:
                        continue
                    return data

        # Build a default empty audit structure
        categories: List[Dict[str, Any]] = []
        for cat_info in _DEFAULT_AUDIT_CATEGORIES:
            categories.append({
                "category": cat_info["name"],
                "label": cat_info["label"],
                "score": 0,
                "max_score": 100,
                "findings": [],
                "critical_issues": 0,
                "quick_wins": 0,
            })

        return {
            "audit_id": _new_id("audit"),
            "business_id": business_id,
            "audit_type": scope,
            "overall_score": 0,
            "max_score": 100,
            "categories": categories,
            "critical_findings": [],
            "quick_wins": [],
            "audit_date": _utc_now(),
        }

    def _compile_review_bundle(self, audit_result: Dict[str, Any]) -> Dict[str, Any]:
        """Build the review bundle from audit results."""
        categories = audit_result.get("categories", [])
        total_findings = sum(len(c.get("findings", [])) for c in categories)
        critical_count = sum(c.get("critical_issues", 0) for c in categories)
        quick_win_count = sum(c.get("quick_wins", 0) for c in categories)

        return {
            "audit_id": audit_result.get("audit_id", ""),
            "overall_score": audit_result.get("overall_score", 0),
            "max_score": audit_result.get("max_score", 100),
            "total_findings": total_findings,
            "critical_findings_count": critical_count,
            "quick_wins_count": quick_win_count,
            "categories_audited": len(categories),
            "compiled_at": _utc_now(),
        }

    @staticmethod
    def _summarize_finding(finding: Dict[str, Any]) -> Dict[str, Any]:
        """Return a compact summary of a finding."""
        return {
            "finding_id": finding.get("finding_id", ""),
            "category": finding.get("category", ""),
            "title": finding.get("title", ""),
            "severity": finding.get("severity", ""),
            "recommendation": finding.get("recommendation", ""),
        }
