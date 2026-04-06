"""Anomaly-to-proposal bridge — auto-generates action proposals from analytics anomalies.

When analytics data shows significant changes (traffic drops, conversion dips,
ranking losses), this module creates ActionProposal records automatically.
This closes the observation loop: observe -> interpret -> propose -> approve -> execute.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Anomaly detection thresholds
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLDS = {
    "traffic_drop_pct": 20.0,      # >20% drop in sessions
    "conversion_drop_pct": 15.0,   # >15% drop in conversions
    "bounce_rate_spike_pct": 25.0, # >25% increase in bounce rate
    "position_drop": 5.0,          # Average position worsened by >5
}


# ---------------------------------------------------------------------------
# Anomaly types -> proposal templates
# ---------------------------------------------------------------------------

_PROPOSAL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "traffic_drop": {
        "channel": "website",
        "action_type": "update_metadata",
        "risk_tier": "low",
        "intent_template": "Page {page} traffic dropped {pct:.0f}% — refresh meta title and description",
    },
    "conversion_drop": {
        "channel": "website",
        "action_type": "update_page_copy",
        "risk_tier": "medium",
        "intent_template": "Page {page} conversions dropped {pct:.0f}% — review CTA and copy",
    },
    "bounce_rate_spike": {
        "channel": "website",
        "action_type": "update_page_copy",
        "risk_tier": "medium",
        "intent_template": "Page {page} bounce rate spiked {pct:.0f}% — review above-fold content",
    },
    "ranking_drop": {
        "channel": "website",
        "action_type": "update_metadata",
        "risk_tier": "low",
        "intent_template": "Query '{query}' position dropped by {delta:.1f} — refresh target page SEO",
    },
}


def detect_traffic_anomalies(
    current_metrics: List[Dict[str, Any]],
    previous_metrics: List[Dict[str, Any]],
    thresholds: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Compare two periods of MetricPoint data and detect anomalies.

    Parameters
    ----------
    current_metrics : list of MetricPoint dicts
        Recent period data (e.g., last 7 days).
    previous_metrics : list of MetricPoint dicts
        Comparison period data (e.g., prior 7 days).
    thresholds : dict, optional
        Override default thresholds.

    Returns
    -------
    List of anomaly dicts, each with keys:
        anomaly_type, page/query, current_value, previous_value, pct_change
    """
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    anomalies: List[Dict[str, Any]] = []

    # Group by (metric_name, dimension) for comparison
    def _group(metrics: List[Dict]) -> Dict[str, float]:
        grouped: Dict[str, float] = {}
        for m in metrics:
            key = f"{m.get('metric_name', '')}|{m.get('dimension', '')}"
            grouped[key] = grouped.get(key, 0.0) + m.get("value", 0.0)
        return grouped

    current = _group(current_metrics)
    previous = _group(previous_metrics)

    for key, prev_val in previous.items():
        curr_val = current.get(key, 0.0)
        if prev_val == 0:
            continue

        metric_name, dimension = key.split("|", 1)
        pct_change = ((curr_val - prev_val) / prev_val) * 100

        if metric_name in ("sessions", "active_users") and pct_change < -t["traffic_drop_pct"]:
            anomalies.append({
                "anomaly_type": "traffic_drop",
                "page": dimension,
                "metric": metric_name,
                "current_value": curr_val,
                "previous_value": prev_val,
                "pct_change": pct_change,
            })
        elif metric_name == "conversions" and pct_change < -t["conversion_drop_pct"]:
            anomalies.append({
                "anomaly_type": "conversion_drop",
                "page": dimension,
                "metric": metric_name,
                "current_value": curr_val,
                "previous_value": prev_val,
                "pct_change": pct_change,
            })
        elif metric_name == "bounce_rate" and pct_change > t["bounce_rate_spike_pct"]:
            anomalies.append({
                "anomaly_type": "bounce_rate_spike",
                "page": dimension,
                "metric": metric_name,
                "current_value": curr_val,
                "previous_value": prev_val,
                "pct_change": pct_change,
            })

    return anomalies


def create_proposals_from_anomalies(
    anomalies: List[Dict[str, Any]],
    brand_id: str,
    *,
    action_store: Any = None,
    auto_propose: bool = True,
) -> List[Dict[str, Any]]:
    """Convert detected anomalies into ActionProposal records.

    Parameters
    ----------
    anomalies : list of anomaly dicts from detect_traffic_anomalies().
    brand_id : str
        Brand to create proposals for.
    action_store : ActionStore, optional
        If provided, proposals are persisted. Otherwise, dicts are returned.
    auto_propose : bool
        Whether to actually create proposals (True) or just return templates (False).

    Returns
    -------
    List of proposal dicts.
    """
    proposals: List[Dict[str, Any]] = []

    for anomaly in anomalies:
        atype = anomaly.get("anomaly_type", "")
        template = _PROPOSAL_TEMPLATES.get(atype)
        if template is None:
            continue

        intent = template["intent_template"].format(
            page=anomaly.get("page", "unknown"),
            query=anomaly.get("query", "unknown"),
            pct=abs(anomaly.get("pct_change", 0)),
            delta=abs(anomaly.get("pct_change", 0)),
        )

        proposal = {
            "brand_id": brand_id,
            "channel": template["channel"],
            "action_type": template["action_type"],
            "intent": intent,
            "risk_tier": template["risk_tier"],
            "proposed_changes": {
                "page": anomaly.get("page", ""),
                "anomaly": anomaly,
            },
            "metadata": {
                "source": "anomaly_detection",
                "anomaly_type": atype,
            },
        }

        if auto_propose and action_store is not None:
            try:
                record = action_store.propose_action(proposal)
                proposal["action_id"] = record.get("action_id")
                proposal["approval_state"] = record.get("approval_state")
                logger.info(
                    "Auto-proposed action %s for %s anomaly on %s",
                    record.get("action_id"), atype, anomaly.get("page"),
                )
            except Exception as e:
                logger.warning("Failed to propose action for anomaly: %s", e)
                proposal["error"] = str(e)

        proposals.append(proposal)

    return proposals
