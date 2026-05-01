"""Local-service operating-loop primitives.

Watchers emit findings. This module turns those findings into typed actions,
normalizes channel snapshots, and provides a small memory retrieval helper for
the next proposal cycle.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import SerializableModel


@dataclass
class IntegrationCapability(SerializableModel):
    """Provider capability state for local-service arms."""

    provider: str
    channel: str
    connected: bool = False
    configured: bool = False
    read_sync_ok: bool = False
    write_supported: bool = False
    verified: bool = False
    degraded: bool = False
    last_successful_sync: Optional[str] = None
    last_error: Optional[str] = None


@dataclass
class LocalServiceSnapshot(SerializableModel):
    """Normalized local-service marketing state."""

    brand_id: str
    captured_at: str = ""
    website: Dict[str, Any] = field(default_factory=dict)
    gbp: Dict[str, Any] = field(default_factory=dict)
    reviews: Dict[str, Any] = field(default_factory=dict)
    calls: Dict[str, Any] = field(default_factory=dict)
    lead_response: Dict[str, Any] = field(default_factory=dict)
    integrations: List[IntegrationCapability] = field(default_factory=list)


@dataclass
class MemoryEntry(SerializableModel):
    """Approved learning written back after verification."""

    category: str
    source_action: str
    confidence: float
    retrieval_tags: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


LOCAL_SERVICE_ACTIONS: Dict[str, Dict[str, Any]] = {
    "missed_call": {
        "workflow_id": "call-script",
        "channel": "calls",
        "action_type": "setup_kaicalls",
        "risk_tier": "medium",
        "verification": [
            {"metric": "missed_call_rate", "direction": "down"},
            {"metric": "captured_calls", "direction": "up"},
        ],
    },
    "speed_to_lead": {
        "workflow_id": "call-script",
        "channel": "calls",
        "action_type": "improve_speed_to_lead",
        "risk_tier": "medium",
        "verification": [{"metric": "median_first_response_minutes", "direction": "down"}],
    },
    "gbp": {
        "workflow_id": "gbp-post",
        "channel": "gbp",
        "action_type": "publish_gbp_update",
        "risk_tier": "low",
        "verification": [{"metric": "gbp_actions", "direction": "up"}],
    },
    "review": {
        "workflow_id": "review-response",
        "channel": "gbp",
        "action_type": "draft_review_responses",
        "risk_tier": "low",
        "verification": [{"metric": "review_response_rate", "direction": "up"}],
    },
    "review_request": {
        "workflow_id": "review-request-sequence",
        "channel": "gbp",
        "action_type": "launch_review_request_sequence",
        "risk_tier": "medium",
        "verification": [{"metric": "new_reviews_30d", "direction": "up"}],
    },
    "website": {
        "workflow_id": "landing-page",
        "channel": "website",
        "action_type": "update_conversion_asset",
        "risk_tier": "medium",
        "verification": [{"metric": "website_leads", "direction": "up"}],
    },
}


def normalize_snapshot(
    *,
    brand_id: str,
    website: Optional[dict] = None,
    gbp: Optional[dict] = None,
    reviews: Optional[dict] = None,
    calls: Optional[dict] = None,
    lead_response: Optional[dict] = None,
    integrations: Optional[List[dict]] = None,
    captured_at: str = "",
) -> dict:
    """Build a serializable LocalServiceSnapshot."""

    capability_records = []
    for item in integrations or []:
        capability_records.append(
            IntegrationCapability(
                provider=str(item.get("provider", "")),
                channel=str(item.get("channel", "")),
                connected=bool(item.get("connected", False)),
                configured=bool(item.get("configured", False)),
                read_sync_ok=bool(item.get("read_sync_ok", False)),
                write_supported=bool(item.get("write_supported", False)),
                verified=bool(item.get("verified", False)),
                degraded=bool(item.get("degraded", False)),
                last_successful_sync=item.get("last_successful_sync") or item.get("last_sync_at"),
                last_error=item.get("last_error"),
            )
        )

    return LocalServiceSnapshot(
        brand_id=brand_id,
        captured_at=captured_at,
        website=website or {},
        gbp=gbp or {},
        reviews=reviews or {},
        calls=calls or {},
        lead_response=lead_response or {},
        integrations=capability_records,
    ).model_dump()


def classify_finding(finding: dict) -> str:
    """Classify a watcher/audit finding into a local-service action family."""

    text = " ".join(
        str(finding.get(key, ""))
        for key in ("type", "title", "category", "description", "recommendation")
    ).lower()
    if "missed" in text and "call" in text:
        return "missed_call"
    if "speed" in text and ("lead" in text or "response" in text):
        return "speed_to_lead"
    if "review request" in text or "review velocity" in text:
        return "review_request"
    if "review" in text:
        return "review"
    if "google business" in text or "gbp" in text or "local pack" in text:
        return "gbp"
    return "website"


def action_from_finding(finding: dict, *, brand_id: str, source_run_id: Optional[str] = None) -> dict:
    """Convert a watcher finding into an ActionRecord-shaped dict."""

    family = classify_finding(finding)
    spec = LOCAL_SERVICE_ACTIONS[family]
    evidence = finding.get("evidence")
    evidence_list = evidence if isinstance(evidence, list) else [finding]
    title = finding.get("title") or finding.get("type") or spec["action_type"]
    recommendation = finding.get("recommendation") or finding.get("description") or title

    return {
        "brand_id": brand_id,
        "channel": spec["channel"],
        "action_type": spec["action_type"],
        "intent": str(recommendation),
        "proposed_changes": {
            "finding": title,
            "recommendation": recommendation,
            "workflow_id": spec["workflow_id"],
            "local_service_family": family,
        },
        "evidence": evidence_list,
        "source_run_id": source_run_id,
        "risk_tier": spec["risk_tier"],
        "policy_result": {
            "passed": True,
            "checks": ["local_service_action_shape"],
            "violations": [],
        },
        "preview_artifact": {
            "artifact_type": "preview_request",
            "workflow_id": spec["workflow_id"],
        },
        "approval_state": "pending",
        "execution_state": "pending",
        "verification_criteria": spec["verification"],
        "rollback_reference": None,
        "metadata": {
            "operating_state": "gated",
            "archetype": "local-service",
        },
    }


def retrieve_memory_entries(base_dir: Path, *, brand_id: str, tags: Optional[List[str]] = None) -> List[dict]:
    """Load matching local memory entries for future proposal/creative prompts."""

    tags = tags or []
    memory_dir = base_dir / "memory"
    if not memory_dir.exists():
        return []

    matches: List[dict] = []
    for path in memory_dir.glob("*.json"):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if entry.get("brand_id") not in (brand_id, None, ""):
            continue
        retrieval_tags = entry.get("retrieval_tags") or entry.get("tags") or []
        if tags and not set(tags).intersection(set(retrieval_tags)):
            continue
        matches.append(entry)
    return matches
