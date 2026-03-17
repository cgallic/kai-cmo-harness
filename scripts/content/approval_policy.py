"""
Approval Policy — Determines whether content auto-publishes, holds for review, or fails.

Resolves policy from config.yaml overrides (exact match > wildcard > default),
then applies a 3x3 decision matrix against gate status.
"""

from scripts.harness_config import get_config


def resolve_policy(format: str, site: str) -> str:
    """Look up the approval policy for a format+site pair.

    Checks overrides in order: exact match > wildcard site > default.

    Returns:
        "auto", "hold", or "reject_only"
    """
    cfg = get_config()
    policy_cfg = cfg.approval_policy
    overrides = policy_cfg.get("overrides", [])

    # Check overrides: exact match first, then wildcard
    for entry in overrides:
        fmt_match = entry.get("format") == format or entry.get("format") == "*"
        site_match = entry.get("site") == site or entry.get("site") == "*"
        if fmt_match and site_match:
            return entry.get("policy", policy_cfg.get("default", "hold"))

    return policy_cfg.get("default", "hold")


def apply_approval(gate_status: str, policy: str) -> str:
    """Apply the 3x3 decision matrix.

    Args:
        gate_status: "approved", "pending", or "rejected" from quality gate.
        policy: "auto", "hold", or "reject_only" from resolve_policy().

    Returns:
        "approved" — content can publish immediately
        "held"     — content queued for human review
        "failed"   — content rejected, needs revision
    """
    if gate_status == "rejected":
        return "failed"

    if gate_status == "pending":
        return "held"

    # gate_status == "approved"
    if policy == "auto":
        return "approved"
    elif policy == "reject_only":
        return "approved"
    else:  # "hold" or unknown
        return "held"
