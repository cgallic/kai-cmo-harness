"""First-run brand policy bootstrap for Kai runtime guardrails.

The bootstrapper creates a conservative policy draft from workspace/onboarding
state. It can record discovered accounts and channels, but it does not grant
write permission. A human has to promote discovered account ids into the
allowlists and set spend caps before paid-media mutations can pass.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from scripts.harness_config import get_config

from .business_profile import BusinessProfile
from .integrations import IntegrationRegistry
from .loader import load_workspace_profile
from .models import KaiBrandProfile


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dump_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return value.model_dump()
    return value


def _json_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=_dump_value)


def policy_dir(base_dir: Optional[Path] = None) -> Path:
    """Return the runtime brand policy directory, creating it if needed."""
    if base_dir is None:
        cfg = get_config()
        base_dir = Path(os.environ.get("KAI_RUNTIME_DIR", str(cfg.data_dir / "runtime")))
    path = Path(base_dir) / "policies"
    path.mkdir(parents=True, exist_ok=True)
    return path


def brand_policy_path(brand_id: str, base_dir: Optional[Path] = None) -> Path:
    """Return the JSON policy path for a brand."""
    return policy_dir(base_dir) / f"{brand_id}.json"


def load_brand_policy(brand_id: str, base_dir: Optional[Path] = None) -> dict[str, Any]:
    """Load a generated brand policy, returning an empty dict when absent."""
    path = brand_policy_path(brand_id, base_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_brand_policy(
    brand_id: str,
    *,
    brand: Optional[KaiBrandProfile | dict[str, Any]] = None,
    business_profile: Optional[BusinessProfile | dict[str, Any]] = None,
    integrations: Optional[Iterable[dict[str, Any]]] = None,
    registry: Optional[IntegrationRegistry] = None,
    base_dir: Optional[Path] = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Create a fail-closed policy draft on first run and return it.

    Existing policies are preserved unless ``overwrite=True``. This prevents
    first-run discovery from accidentally erasing human-approved caps.
    """
    path = brand_policy_path(brand_id, base_dir)
    if path.exists() and not overwrite:
        return load_brand_policy(brand_id, base_dir)

    if brand is None:
        brand = load_workspace_profile().get_brand(brand_id)
    if integrations is None and registry is not None:
        integrations = registry.list_for_brand(brand_id)

    policy = build_initial_brand_policy(
        brand_id,
        brand=brand,
        business_profile=business_profile,
        integrations=integrations or [],
    )
    write_brand_policy(brand_id, policy, base_dir=base_dir)
    return policy


def write_brand_policy(
    brand_id: str,
    policy: dict[str, Any],
    *,
    base_dir: Optional[Path] = None,
) -> Path:
    """Persist a brand policy atomically."""
    path = brand_policy_path(brand_id, base_dir)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(_json_dump(policy), encoding="utf-8")
    tmp_path.replace(path)
    return path


def build_initial_brand_policy(
    brand_id: str,
    *,
    brand: Optional[KaiBrandProfile | dict[str, Any]] = None,
    business_profile: Optional[BusinessProfile | dict[str, Any]] = None,
    integrations: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Build a first-run policy draft from known brand/runtime state."""
    brand_data = _to_dict(brand)
    profile_data = _to_dict(business_profile)
    active_channels = _active_channels(brand_data, profile_data)
    discovered_accounts = _discover_paid_media_accounts(integrations)

    return {
        "brand_id": brand_id,
        "policy_status": "draft",
        "generated_at": _utc_now(),
        "generated_by": "kai.runtime.policy_bootstrap",
        "auto_execute_low_risk": False,
        "allowed_channels": active_channels,
        "paid_media_guardrails": {
            "allowed_accounts": [],
            "allowed_campaigns": [],
            "allowed_adsets": [],
            "allowed_ad_groups": [],
            "discovered_accounts": discovered_accounts,
            "max_budget_increase_pct": 0.0,
            "max_bid_increase_pct": 0.0,
            "max_budget_reduction_pct": 50.0,
            "max_single_budget_change_usd": 50.0,
            "max_daily_budget": 0.0,
            "require_rollback_for_activation": True,
            "require_before_state": True,
            "require_projected_spend": True,
            "require_human_approval_for_activation": True,
        },
        "metadata": {
            "activation_required": True,
            "activation_note": (
                "Review discovered_accounts, set caps, and copy approved ids "
                "into allowed_accounts before live paid-media writes."
            ),
        },
    }


def activate_paid_media_accounts(
    policy: dict[str, Any],
    *,
    allowed_accounts: Iterable[str],
    max_daily_budget: float,
    max_budget_increase_pct: float = 0.0,
    max_bid_increase_pct: float = 0.0,
) -> dict[str, Any]:
    """Return a copy of a draft policy with explicit paid-media account caps."""
    updated = json.loads(json.dumps(policy))
    guardrails = updated.setdefault("paid_media_guardrails", {})
    guardrails["allowed_accounts"] = sorted({str(account) for account in allowed_accounts if str(account).strip()})
    guardrails["max_daily_budget"] = float(max_daily_budget)
    guardrails["max_budget_increase_pct"] = float(max_budget_increase_pct)
    guardrails["max_bid_increase_pct"] = float(max_bid_increase_pct)
    updated["policy_status"] = "active"
    updated.setdefault("metadata", {})["activation_required"] = False
    updated["updated_at"] = _utc_now()
    return updated


def _to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    return _dump_value(value)


def _active_channels(brand: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    channels: set[str] = set()
    for channel in brand.get("active_channels") or []:
        channels.add(str(channel))

    profile_channels = ((profile.get("channels") or {}).get("channels") or [])
    for item in profile_channels:
        if not isinstance(item, dict):
            continue
        if item.get("status") in {"active", "planned"} and item.get("channel"):
            channels.add(str(item["channel"]))

    normalized = sorted(channels)
    return normalized


def _discover_paid_media_accounts(integrations: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    accounts: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for integration in integrations:
        if integration.get("channel") != "paid_media":
            continue
        if integration.get("status") not in {"connected", "degraded"}:
            continue
        if integration.get("kill_switch"):
            continue

        provider = str(integration.get("provider") or "")
        account_id = _integration_account_id(integration)
        if not account_id:
            continue
        key = (provider, account_id)
        if key in seen:
            continue
        seen.add(key)
        accounts.append({
            "provider": provider,
            "account_id": account_id,
            "integration_id": integration.get("integration_id"),
            "write_supported": _write_supported(integration),
            "status": integration.get("status"),
        })

    return accounts


def _integration_account_id(integration: dict[str, Any]) -> str:
    config = integration.get("config") or {}
    metadata = integration.get("metadata") or {}
    candidates = [
        config.get("account_id"),
        config.get("ad_account_id"),
        config.get("customer_id"),
        metadata.get("account_id"),
        metadata.get("ad_account_id"),
        integration.get("connected_account_id"),
    ]
    for value in candidates:
        if value not in (None, ""):
            return str(value)
    return ""


def _write_supported(integration: dict[str, Any]) -> bool:
    capabilities = set(integration.get("capabilities") or [])
    return bool(capabilities.intersection({"write", "publish", "budget"}))
