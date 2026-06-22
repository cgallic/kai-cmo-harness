#!/usr/bin/env python3
"""Policy decision engine — maps a finding to a permitted action class.

This is the rules layer that makes Kai's judgment explicit instead of implied by
agent prose. Every finding gets routed to exactly one action class, and the
chosen class is recorded in the autonomy ledger.

Action classes (ordered least -> most restrictive):
  auto_fix           safe docs, registries, snapshots, dead-link/lint-only changes
  auto_pr            code or content changes that need review before merge
  stage_for_approval emails, client-facing claims, publishing, paid spend, account changes
  escalate           unclear business fit, missing source, ambiguous policy
  block              deception, astroturfing, scraping outside terms, credential misuse, rule evasion

The engine is deliberately conservative: when signals are ambiguous it routes up,
never down. Guardrail matches (block) always win.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Risk vocabulary, ordered low -> high. Shared with the ledger.
RISK_LEVELS: tuple[str, ...] = ("none", "low", "medium", "high", "critical")

# Action classes, ordered least -> most restrictive.
ACTION_CLASSES: tuple[str, ...] = (
    "auto_fix",
    "auto_pr",
    "stage_for_approval",
    "escalate",
    "block",
)

# Substrings that force a hard block regardless of any other signal. These are
# the activities the guardrails forbid Kai from ever automating.
_BLOCK_SIGNALS: tuple[str, ...] = (
    "deception",
    "deceive",
    "astroturf",
    "fake engagement",
    "fake review",
    "bought account",
    "buy followers",
    "hidden ownership",
    "undisclosed ownership",
    "scrape outside",
    "scraping outside",
    "credential misuse",
    "steal credential",
    "rule evasion",
    "evade detection",
    "evade platform",
    "duplicate-content evasion",
    "cloaking",
)

# Action kinds that always need a human before they touch the outside world.
_APPROVAL_ACTIONS: frozenset[str] = frozenset(
    {
        "send_email",
        "outbound_email",
        "cold_email",
        "publish",
        "live_publish",
        "post",
        "client_claim",
        "client_report",
        "paid_spend",
        "paid_media",
        "budget_change",
        "account_change",
        "credential_change",
        "deploy",
        "legal_content",
        "compliance_content",
    }
)

# Conditions that mean we cannot decide safely on our own.
_ESCALATE_SIGNALS: tuple[str, ...] = (
    "unclear business fit",
    "missing source",
    "no source",
    "source missing",
    "ambiguous policy",
    "unresolved",
    "needs manual review",
    "manual review",
)


@dataclass
class DecisionResult:
    """The routed action class plus the reason and any rolled-up risk."""

    action_class: str
    reason: str
    risk_level: str = "low"
    requires_human: bool = field(default=False)

    def __post_init__(self) -> None:
        self.requires_human = self.action_class in {
            "stage_for_approval",
            "escalate",
            "block",
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.action_class,
            "decision_reason": self.reason,
            "risk_level": self.risk_level,
            "requires_human": self.requires_human,
        }


def _haystack(finding: dict[str, Any]) -> str:
    """Flatten the searchable text of a finding for signal matching."""
    parts: list[str] = []
    for key in ("title", "summary", "why_it_matters", "what_changed", "notes", "impact_area"):
        value = finding.get(key)
        if isinstance(value, str):
            parts.append(value)
    for tag in finding.get("tags", []) or []:
        if isinstance(tag, str):
            parts.append(tag)
    return " ".join(parts).lower()


def route_decision(finding: dict[str, Any]) -> DecisionResult:
    """Route a single finding to one action class.

    ``finding`` may carry: ``action_kind`` (what the automation would do),
    ``risk_level``, ``change_type`` ("docs"|"registry"|"snapshot"|"dead_link"|
    "lint"|"code"|"content"), ``source_status`` ("fixed"|"replaced"|
    "unresolved"), and free text fields used for guardrail matching.
    """
    risk = finding.get("risk_level", "low")
    if risk not in RISK_LEVELS:
        risk = "low"
    text = _haystack(finding)
    action_kind = (finding.get("action_kind") or "").strip().lower()
    change_type = (finding.get("change_type") or "").strip().lower()
    source_status = (finding.get("source_status") or "").strip().lower()

    # 1. Guardrails always win.
    for signal in _BLOCK_SIGNALS:
        if signal in text or signal in action_kind:
            return DecisionResult("block", f"guardrail: matched '{signal}'", "critical")

    # 2. Outside-world actions need a person.
    if action_kind in _APPROVAL_ACTIONS:
        return DecisionResult(
            "stage_for_approval",
            f"action '{action_kind}' touches a live/client surface",
            _max_risk(risk, "high"),
        )

    # 3. Unresolved or ambiguous source/policy -> escalate to a human.
    if source_status == "unresolved":
        return DecisionResult("escalate", "source unresolved; needs manual review", _max_risk(risk, "medium"))
    for signal in _ESCALATE_SIGNALS:
        if signal in text:
            return DecisionResult("escalate", f"ambiguous: matched '{signal}'", _max_risk(risk, "medium"))

    # 4. Safe self-service edits the automation can make directly.
    safe_changes = {"docs", "registry", "snapshot", "dead_link", "lint"}
    if change_type in safe_changes and risk in ("none", "low"):
        return DecisionResult("auto_fix", f"safe {change_type} change", risk if risk != "none" else "low")

    # 5. Code/content changes that should go through review.
    if change_type in {"code", "content"} or risk in ("medium", "high", "critical"):
        return DecisionResult("auto_pr", f"{change_type or 'change'} needs review before merge", _max_risk(risk, "medium"))

    # 6. Default: surface for review rather than acting silently.
    return DecisionResult("auto_pr", "unclassified change; defaulting to review", _max_risk(risk, "low"))


def _max_risk(a: str, b: str) -> str:
    """Return the higher of two risk levels."""
    if a not in RISK_LEVELS:
        a = "low"
    if b not in RISK_LEVELS:
        b = "low"
    return a if RISK_LEVELS.index(a) >= RISK_LEVELS.index(b) else b
