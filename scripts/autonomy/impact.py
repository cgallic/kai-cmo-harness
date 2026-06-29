#!/usr/bin/env python3
"""Impact classifier — turn raw change signals into practical impact cards.

Monitors used to report "hash changed" or "status 404". That is a log, not a
decision. This module upgrades a change signal into an impact card answering the
questions an operator actually has:

  what changed · why it matters · action taken · remaining risk · confidence ·
  source url · next recommended gate/registry/doc update

It also classifies broken sources as ``fixed``, ``replaced``, or ``unresolved``
manual-review items, so a dead link never silently rots in the registry.
"""

from __future__ import annotations

from typing import Any

from scripts.autonomy.decisions import route_decision

# Map a registry category to the operational area it affects and a plain-language
# consequence. Categories come from
# harness/references/social-platform-source-registry.json.
_CATEGORY_IMPACT: dict[str, tuple[str, str]] = {
    "policy": (
        "allowed content",
        "allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate",
    ),
    "ai_policy": (
        "AI/synthetic media labels",
        "AI/synthetic media disclosure rules may have changed; the pre-publish gate may need an AI/synthetic-media question",
    ),
    "ads_policy": (
        "paid amplification",
        "ad eligibility or prohibited-content rules may have changed; recheck ad copy gates before the next paid run",
    ),
    "commercial_policy": (
        "commercial disclosure",
        "branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules",
    ),
    "data_policy": (
        "privacy/data use",
        "data-use or privacy terms may have changed; recheck what data automations may collect or store",
    ),
    "automation": (
        "API automation",
        "automation rules may have changed; the scheduler or write actions may need updated guardrails",
    ),
    "developer": (
        "API automation",
        "developer terms may have changed; API usage limits or content-usage rules may affect automations",
    ),
    "changelog": (
        "scheduling/rate limits",
        "an API change may affect posting limits, required upload fields, or the scheduler",
    ),
    "recommendation": (
        "recommendation eligibility",
        "ranking or eligibility guidance may have changed; recheck distribution playbooks",
    ),
    "monetization": (
        "paid amplification",
        "monetization or eligibility rules may have changed; recheck program assumptions",
    ),
    "terms": (
        "community-specific rules",
        "platform terms may have changed; recheck the owner doc for new prohibited behavior",
    ),
}

_DEFAULT_IMPACT = (
    "allowed content",
    "platform guidance may have changed; recheck the owner doc",
)


def classify_source_status(result: dict[str, Any]) -> str:
    """Classify a broken/recovered source as fixed, replaced, or unresolved.

    - ``fixed``      — source errored before but fetched cleanly this run
    - ``replaced``   — source is still broken but the registry names a replacement
    - ``unresolved`` — source is broken with no known replacement (manual review)
    - ``ok``         — source fetched cleanly and was not previously broken
    """
    ok = result.get("ok") or result.get("monitor_status") not in {"error", None}
    if result.get("monitor_status") == "error" or result.get("ok") is False:
        ok = False
    previous_error = bool(result.get("previous_error"))
    if ok:
        return "fixed" if previous_error else "ok"
    if result.get("replacement_url"):
        return "replaced"
    return "unresolved"


def _confidence(status: str, source_status: str) -> str:
    """How sure are we that the impact assessment is right?"""
    if source_status == "unresolved":
        return "high"  # we are sure the source is broken
    if status == "changed":
        return "medium"  # we know it changed, not yet what changed
    if status == "new":
        return "medium"
    return "high"


def build_impact_card(result: dict[str, Any]) -> dict[str, Any]:
    """Build one practical impact card from a monitor source result.

    ``result`` is a registry source merged with fetch outcome, carrying at least
    ``platform``, ``category``, ``title``, ``url``, ``monitor_status`` and the
    optional ``owner_file`` / ``previous_error`` / ``replacement_url`` fields.
    """
    status = result.get("monitor_status", "unchanged")
    category = result.get("category", "")
    impact_area, consequence = _CATEGORY_IMPACT.get(category, _DEFAULT_IMPACT)
    source_status = classify_source_status(result)
    owner_file = result.get("owner_file", "")

    # what changed
    if status == "error" or source_status in {"unresolved", "replaced"}:
        what = f"Source unreachable ({result.get('error') or result.get('status_code') or 'fetch failed'})"
    elif status == "changed":
        prev = (result.get("previous_hash") or "")[:12]
        cur = (result.get("content_hash") or "")[:12]
        what = f"Content hash changed ({prev} -> {cur})"
    elif status == "new":
        what = "New source added to monitoring; baseline captured"
    elif source_status == "fixed":
        what = "Previously broken source is reachable again"
    else:
        what = "No change since last run"

    # action taken + remaining risk + next step, by situation
    if source_status == "unresolved":
        action_taken = "Flagged for manual review; registry entry left unchanged"
        remaining_risk = "Guidance for this source cannot be verified until the link is fixed or replaced"
        next_step = f"Find a canonical replacement URL for `{result.get('id')}` or mark the registry entry deprecated"
        change_type = "dead_link"
    elif source_status == "replaced":
        action_taken = "Replacement URL recorded for review"
        remaining_risk = "New URL must be confirmed canonical before the registry is updated"
        next_step = f"Confirm replacement `{result.get('replacement_url')}` and update the registry entry"
        change_type = "registry"
    elif status == "changed":
        action_taken = "Snapshot hash updated; change logged for owner-doc review"
        remaining_risk = "The specific rule change is not yet read into the owner doc"
        next_step = (
            f"Review `{owner_file}` against the live page and update it" if owner_file else "Assign an owner doc for this source"
        )
        change_type = "docs"
    elif status == "new":
        action_taken = "Baseline snapshot captured"
        remaining_risk = "No prior baseline to diff against yet"
        next_step = "Confirm the owner doc reflects current guidance"
        change_type = "snapshot"
    elif source_status == "fixed":
        action_taken = "Snapshot refreshed now that the source is reachable"
        remaining_risk = "Confirm the recovered page still matches the owner doc"
        next_step = f"Spot-check `{owner_file}`" if owner_file else "Assign an owner doc for this source"
        change_type = "snapshot"
    else:
        action_taken = "Snapshot hash confirmed unchanged"
        remaining_risk = "None"
        next_step = "No action needed"
        change_type = "snapshot"

    why = consequence if status in {"changed", "new", "error"} or source_status in {"fixed", "unresolved", "replaced"} else "No operational impact this run"

    finding = {
        "id": result.get("id"),
        "platform": result.get("platform"),
        "category": category,
        "title": result.get("title"),
        "monitor_status": status,
        "source_status": source_status,
        "impact_area": impact_area,
        "what_changed": what,
        "why_it_matters": why,
        "action_taken": action_taken,
        "remaining_risk": remaining_risk,
        "confidence": _confidence(status, source_status),
        "source_url": result.get("url"),
        "next_step": next_step,
        "owner_file": owner_file,
        "change_type": change_type,
        "resolved_url": result.get("resolved_url"),
    }
    decision = route_decision(finding)
    finding.update(decision.as_dict())
    return finding
