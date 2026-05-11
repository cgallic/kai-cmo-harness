"""Unified Meta/Facebook ads script — pull data and execute mutations.

Subcommands:
    pull            Pull comprehensive account data into a local JSON snapshot.
    pause           Pause a campaign, ad set, or ad.
    activate        Activate a campaign, ad set, or ad.
    budget          Change daily budget on an ad set or campaign.
    create-campaign Create a new campaign (PAUSED by default).
    create-adset    Create a new ad set (PAUSED by default).
    create-ad       Create a new ad (PAUSED by default).
    upload-image    Upload an image file, return its hash.
    upload-video    Upload a video file.
    duplicate-adset Duplicate an ad set with new name/budget.

All mutation commands default to --dry-run. Pass --execute to apply.

Usage:
    python scripts/ads/meta.py pull [--date YYYY-MM-DD]
    python scripts/ads/meta.py pause --id <entity_id> [--execute]
    python scripts/ads/meta.py activate --id <entity_id> [--execute]
    python scripts/ads/meta.py budget --id <id> --amount <dollars> [--execute]
    python scripts/ads/meta.py create-campaign --name "..." --objective OUTCOME_LEADS [--execute]
    python scripts/ads/meta.py create-adset --campaign-id X --name "..." --daily-budget 25 ...
    python scripts/ads/meta.py create-ad --adset-id X --name "..." --creative-json '{...}'
    python scripts/ads/meta.py upload-image --file path.png
    python scripts/ads/meta.py upload-video --file path.mp4 [--title "Video name"]
    python scripts/ads/meta.py duplicate-adset --id <adset_id> --name "New name" [--execute]

Requires META_ACCESS_TOKEN and META_AD_ACCOUNT_ID in .env.local.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from _pull_common import (
    REPO_ROOT,
    APIError,
    META_BREAKDOWNS,
    META_DATE_PRESETS,
    META_INSIGHT_FIELDS_STR,
    api_get,
    api_post,
    env,
    has_creds,
    log,
    log_section,
    today_str,
    write_pull,
)

sys.path.insert(0, str(REPO_ROOT))
from kai.runtime.policy import PolicyEngine

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://graph.facebook.com/v21.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _account_id() -> str:
    raw = env("META_AD_ACCOUNT_ID")
    if raw.startswith("act_"):
        return raw
    return f"act_{raw}"


def _token() -> str:
    return env("META_ACCESS_TOKEN")


def _paginate(url: str, params: Optional[Dict[str, Any]] = None, label: str = "") -> List[Dict[str, Any]]:
    """Follow Meta pagination until exhausted. Returns all items."""
    all_items: List[Dict[str, Any]] = []
    resp = api_get(url, params=params, label=label)
    all_items.extend(resp.get("data", []))

    while True:
        next_url = resp.get("paging", {}).get("next")
        if not next_url:
            break
        resp = api_get(next_url, label=f"{label} (page)")
        all_items.extend(resp.get("data", []))

    return all_items


def _get_insights(entity_id: str, date_preset: str, label: str = "",
                  time_increment: Optional[str] = None) -> Any:
    """Pull insights for a single entity. Returns data list or empty list."""
    params: Dict[str, Any] = {
        "fields": META_INSIGHT_FIELDS_STR,
        "date_preset": date_preset,
        "access_token": _token(),
    }
    if time_increment:
        params["time_increment"] = time_increment

    url = f"{BASE_URL}/{entity_id}/insights"
    try:
        resp = api_get(url, params=params, label=label)
        return resp.get("data", [])
    except APIError as e:
        # Some entities have no data for a date range -- not fatal
        if "no data" in str(e).lower() or "does not exist" in str(e).lower():
            log(f"  No insights for {entity_id} ({date_preset}): {e}")
            return []
        raise


def _budget_dollars(cents: Any) -> Optional[float]:
    """Convert Meta budget (string cents) to dollars. Returns None if missing."""
    if cents is None:
        return None
    try:
        return int(cents) / 100.0
    except (ValueError, TypeError):
        return None


def _convert_budgets(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Convert daily_budget and lifetime_budget from cents to dollars in-place."""
    for key in ("daily_budget", "lifetime_budget"):
        if key in obj:
            obj[key] = _budget_dollars(obj[key])
    return obj


# ---------------------------------------------------------------------------
# Audience type detection
# ---------------------------------------------------------------------------

_NAME_PATTERNS = [
    (r"(?i)\blal\b|lookalike", "lookalike"),
    (r"(?i)\bretarget", "custom_retarget"),
    (r"(?i)\bcustom\s*aud", "custom_retarget"),
    (r"(?i)\bengagement", "engagement_retarget"),
    (r"(?i)\bbroad\b", "broad"),
]


def _classify_audience(adset: Dict[str, Any]) -> tuple[str, str]:
    """Classify ad set audience and return (audience_type, audience_detail)."""
    targeting = adset.get("targeting", {}) or {}

    # Check Advantage+ (targeting automation)
    automation = targeting.get("targeting_automation", {}) or {}
    if automation.get("advantage_audience") == 1:
        return "advantage_plus", "Advantage+ Audience (automated targeting)"

    # Check custom audiences
    custom_audiences = targeting.get("custom_audiences", []) or []
    if custom_audiences:
        for aud in custom_audiences:
            subtype = (aud.get("subtype") or "").upper()
            name = aud.get("name", "")

            if subtype == "LOOKALIKE" or "lookalike" in subtype.lower():
                # Extract lookalike spec details
                lal_spec = aud.get("lookalike_spec", {}) or {}
                ratio = lal_spec.get("ratio")
                pct_str = f"{int(ratio * 100)}%" if ratio else "unknown%"
                origin_name = lal_spec.get("origin", [{}])
                if isinstance(origin_name, list) and origin_name:
                    origin_name = origin_name[0].get("name", "unknown source")
                elif isinstance(origin_name, dict):
                    origin_name = origin_name.get("name", "unknown source")
                else:
                    origin_name = "unknown source"
                return f"lookalike_{pct_str}", f"LAL {pct_str} based on {origin_name}"

            if subtype in ("CUSTOM", "WEBSITE"):
                return "custom_retarget", f"Custom audience: {name or 'unnamed'}"

            if subtype == "ENGAGEMENT":
                return "engagement_retarget", f"Engagement audience: {name or 'unnamed'}"

            # Fallback for other subtypes
            if subtype:
                return subtype.lower(), f"{subtype} audience: {name or 'unnamed'}"

        # Custom audiences exist but no subtype info -- tag generically
        names = [a.get("name", "unnamed") for a in custom_audiences[:3]]
        return "custom_retarget", f"Custom audiences: {', '.join(names)}"

    # Check interest targeting
    if targeting.get("interests"):
        interests = targeting["interests"]
        names = [i.get("name", "") for i in interests[:3] if isinstance(i, dict)]
        return "interest", f"Interest targeting: {', '.join(names)}" if names else "interest"

    # Fallback: regex on ad set name
    adset_name = adset.get("name", "")
    for pattern, tag in _NAME_PATTERNS:
        if re.search(pattern, adset_name):
            return tag, f"Detected from name: {adset_name}"

    return "broad", "No specific targeting detected"


# ---------------------------------------------------------------------------
# Section pullers
# ---------------------------------------------------------------------------

def pull_account_insights(account_id: str) -> Dict[str, Any]:
    log_section("Account-Level Insights")
    result: Dict[str, Any] = {}

    for preset in META_DATE_PRESETS:
        log(f"  Pulling {preset}...")
        data = _get_insights(account_id, preset, label=f"account/{preset}")
        result[preset] = data[0] if data else {}

    return result


def pull_campaigns(account_id: str) -> List[Dict[str, Any]]:
    log_section("Campaigns")

    fields = (
        "id,name,objective,status,effective_status,daily_budget,lifetime_budget,"
        "start_time,stop_time,bid_strategy,special_ad_categories"
    )
    filtering = '[{"field":"effective_status","operator":"IN","value":["ACTIVE","PAUSED"]}]'
    params = {
        "fields": fields,
        "filtering": filtering,
        "limit": "100",
        "access_token": _token(),
    }

    url = f"{BASE_URL}/{account_id}/campaigns"
    campaigns = _paginate(url, params=params, label="campaigns")
    log(f"  Found {len(campaigns)} campaigns")

    for i, c in enumerate(campaigns):
        _convert_budgets(c)
        cid = c["id"]
        log(f"  [{i+1}/{len(campaigns)}] {c.get('name', cid)} — insights...")

        # last_7d aggregate
        data_7d = _get_insights(cid, "last_7d", label=f"campaign/{cid}/7d")
        c["insights_7d"] = data_7d[0] if data_7d else {}

        # last_14d daily
        data_daily = _get_insights(cid, "last_14d", label=f"campaign/{cid}/14d_daily",
                                   time_increment="1")
        c["insights_daily"] = data_daily

    return campaigns


def pull_adsets(account_id: str) -> List[Dict[str, Any]]:
    log_section("Ad Sets")

    fields = (
        "id,name,campaign_id,status,effective_status,daily_budget,lifetime_budget,"
        "optimization_goal,billing_event,targeting,promoted_object,start_time,end_time"
    )
    filtering = '[{"field":"effective_status","operator":"IN","value":["ACTIVE","PAUSED"]}]'
    params = {
        "fields": fields,
        "filtering": filtering,
        "limit": "200",
        "access_token": _token(),
    }

    url = f"{BASE_URL}/{account_id}/adsets"
    adsets = _paginate(url, params=params, label="adsets")
    log(f"  Found {len(adsets)} ad sets")

    for i, aset in enumerate(adsets):
        _convert_budgets(aset)
        aid = aset["id"]

        # Audience classification
        audience_type, audience_detail = _classify_audience(aset)
        aset["audience_type"] = audience_type
        aset["audience_detail"] = audience_detail

        log(f"  [{i+1}/{len(adsets)}] {aset.get('name', aid)} ({audience_type}) — insights...")

        # last_7d aggregate
        data_7d = _get_insights(aid, "last_7d", label=f"adset/{aid}/7d")
        aset["insights_7d"] = data_7d[0] if data_7d else {}

        # last_14d daily
        data_daily = _get_insights(aid, "last_14d", label=f"adset/{aid}/14d_daily",
                                   time_increment="1")
        aset["insights_daily"] = data_daily

    return adsets


def pull_ads(account_id: str) -> List[Dict[str, Any]]:
    log_section("Ads")

    fields = (
        "id,name,adset_id,campaign_id,status,effective_status,"
        "creative{id,name,object_story_spec,url_tags}"
    )
    filtering = '[{"field":"effective_status","operator":"IN","value":["ACTIVE","PAUSED"]}]'
    params = {
        "fields": fields,
        "filtering": filtering,
        "limit": "200",
        "access_token": _token(),
    }

    url = f"{BASE_URL}/{account_id}/ads"
    ads = _paginate(url, params=params, label="ads")
    log(f"  Found {len(ads)} ads")

    for i, ad in enumerate(ads):
        ad_id = ad["id"]
        log(f"  [{i+1}/{len(ads)}] {ad.get('name', ad_id)} — insights...")

        # last_7d aggregate
        data_7d = _get_insights(ad_id, "last_7d", label=f"ad/{ad_id}/7d")
        ad["insights_7d"] = data_7d[0] if data_7d else {}

    return ads


def pull_breakdowns(account_id: str) -> Dict[str, Any]:
    log_section("Breakdowns (Account-Level)")

    breakdown_keys = {
        "age,gender": "age_gender",
        "publisher_platform,platform_position": "platform_position",
        "device_platform": "device",
    }
    result: Dict[str, Any] = {}

    for breakdown in META_BREAKDOWNS:
        key = breakdown_keys.get(breakdown, breakdown.replace(",", "_"))
        log(f"  Pulling {key}...")

        params = {
            "fields": META_INSIGHT_FIELDS_STR,
            "date_preset": "last_7d",
            "breakdowns": breakdown,
            "access_token": _token(),
        }
        url = f"{BASE_URL}/{account_id}/insights"

        try:
            items = _paginate(url, params=params, label=f"breakdown/{key}")
            result[key] = items
        except APIError as e:
            log(f"  Warning: breakdown {key} failed: {e}")
            result[key] = []

    return result


# ---------------------------------------------------------------------------
# Pull command
# ---------------------------------------------------------------------------

def pull(date: Optional[str] = None) -> str:
    if not has_creds("META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"):
        print("ERROR: META_ACCESS_TOKEN and META_AD_ACCOUNT_ID required in .env.local", file=sys.stderr)
        sys.exit(1)

    account_id = _account_id()
    date = date or today_str()

    log(f"Meta Ads pull starting for {account_id} (date={date})")

    # Pull all sections
    account_insights = pull_account_insights(account_id)
    campaigns = pull_campaigns(account_id)
    adsets = pull_adsets(account_id)
    ads = pull_ads(account_id)
    breakdowns = pull_breakdowns(account_id)

    # Assemble output
    data = {
        "account_id": account_id,
        "account_insights": account_insights,
        "campaigns": campaigns,
        "adsets": adsets,
        "ads": ads,
        "breakdowns": breakdowns,
    }

    out_path = write_pull("meta", data, date=date)

    # Summary
    log_section("Pull Complete")
    log(f"  Campaigns: {len(campaigns)}")
    log(f"  Ad sets:   {len(adsets)}")
    log(f"  Ads:       {len(ads)}")
    log(f"  Output:    {out_path}")

    return str(out_path)


def cmd_pull(args: argparse.Namespace) -> None:
    """Handler for the 'pull' subcommand."""
    try:
        path = pull(date=args.date)
        print(path)
    except APIError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Mutation log
# ---------------------------------------------------------------------------

def _log_mutation(command: str, entity_id: str, payload: dict, result: dict) -> None:
    """Append a mutation record to workspace/ads/mutations/YYYY-MM-DD.jsonl."""
    log_dir = REPO_ROOT / "workspace" / "ads" / "mutations"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{today_str()}.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "entity_id": entity_id,
        "payload": payload,
        "result": result,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


# ---------------------------------------------------------------------------
# Dry-run helper
# ---------------------------------------------------------------------------

def _dry_run_banner(method: str, url: str, payload: dict) -> None:
    """Print what a mutation WOULD do, then remind the user to pass --execute."""
    # Build a sanitized payload for display (strip access_token)
    display = {k: v for k, v in payload.items() if k != "access_token"}
    log(f"DRY RUN: {method} {url}")
    log(f"  Payload: {json.dumps(display, indent=2, default=str)}")
    log(f"  Add --execute to apply this change.")


def _require_approval_id(args: argparse.Namespace) -> bool:
    """Return False when a live paid-media write lacks approval metadata."""
    if not getattr(args, "approval_id", None):
        print("ERROR: live paid-media writes require --approval-id", file=sys.stderr)
        return False
    return True


def _policy_preflight(
    args: argparse.Namespace,
    *,
    action_type: str,
    proposed_changes: dict[str, Any],
    rollback_reference: str | None = None,
) -> bool:
    """Run live Meta writes through the shared paid-media policy engine."""
    if not getattr(args, "execute", False) and action_type not in {"upload_ad_asset"}:
        return True
    if not _require_approval_id(args):
        return False

    account_id = _account_id()
    proposed = {
        "account_id": account_id,
        **proposed_changes,
    }
    if rollback_reference:
        proposed["rollback_reference"] = rollback_reference

    result = PolicyEngine(
        brand_policies={
            "paid_media_guardrails": {
                "allowed_accounts": [account_id],
            }
        }
    ).evaluate({
        "channel": "paid_media",
        "action_type": action_type,
        "execution_requested": True,
        "metadata": {"approval_id": args.approval_id},
        "proposed_changes": proposed,
        "evidence": [{"source": f"approval:{args.approval_id}"}],
    })

    if result["passed"]:
        return True

    print("ERROR: Paid-media policy preflight failed:", file=sys.stderr)
    for violation in result["violations"]:
        print(f"  - {violation}", file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# Mutation commands
# ---------------------------------------------------------------------------

def cmd_pause(args: argparse.Namespace) -> None:
    """Pause a campaign, ad set, or ad."""
    if args.execute and not _require_approval_id(args):
        sys.exit(1)

    entity_id = args.id
    url = f"{BASE_URL}/{entity_id}"
    payload = {"status": "PAUSED", "access_token": _token()}
    if not _policy_preflight(
        args,
        action_type="pause_campaign",
        proposed_changes={
            "campaign_id": entity_id,
            "target_status": "PAUSED",
            "change_diff": {"status": {"before": "ACTIVE", "after": "PAUSED"}},
        },
        rollback_reference=args.rollback_reference,
    ):
        sys.exit(1)

    if not args.execute:
        _dry_run_banner("POST", url, payload)
        return

    resp = api_post(url, data=payload, label=f"pause/{entity_id}")
    log(f"Paused: {entity_id}")
    _log_mutation("pause", entity_id, {"status": "PAUSED", "approval_id": args.approval_id}, resp)
    print(json.dumps(resp, indent=2))


def cmd_activate(args: argparse.Namespace) -> None:
    """Activate a campaign, ad set, or ad."""
    if args.execute and not _require_approval_id(args):
        sys.exit(1)

    entity_id = args.id
    url = f"{BASE_URL}/{entity_id}"
    payload = {"status": "ACTIVE", "access_token": _token()}
    if not _policy_preflight(
        args,
        action_type="activate_campaign",
        proposed_changes={
            "campaign_id": entity_id,
            "target_status": "ACTIVE",
            "change_diff": {"status": {"before": "PAUSED", "after": "ACTIVE"}},
        },
        rollback_reference=args.rollback_reference,
    ):
        sys.exit(1)

    if not args.execute:
        _dry_run_banner("POST", url, payload)
        return

    resp = api_post(url, data=payload, label=f"activate/{entity_id}")
    log(f"Activated: {entity_id}")
    _log_mutation("activate", entity_id, {"status": "ACTIVE", "approval_id": args.approval_id}, resp)
    print(json.dumps(resp, indent=2))


def cmd_budget(args: argparse.Namespace) -> None:
    """Change daily budget on an ad set or campaign. Amount in dollars."""
    if args.execute and not _require_approval_id(args):
        sys.exit(1)

    entity_id = args.id
    amount_cents = int(float(args.amount) * 100)
    url = f"{BASE_URL}/{entity_id}"
    payload = {"daily_budget": str(amount_cents), "access_token": _token()}

    if not args.execute:
        _dry_run_banner("POST", url, payload)
        log(f"  (${args.amount} = {amount_cents} cents)")
        return

    before = api_get(
        f"{BASE_URL}/{entity_id}?fields=daily_budget,status,effective_status&access_token={_token()}",
        label=f"budget_before/{entity_id}",
    )
    current_cents = int(before.get("daily_budget") or 0)
    current_daily = current_cents / 100
    new_daily = amount_cents / 100
    if current_cents <= 0:
        print("ERROR: Cannot verify current daily budget before mutation; failing closed.", file=sys.stderr)
        sys.exit(1)
    if not _policy_preflight(
        args,
        action_type="adjust_budget",
        proposed_changes={
            "campaign_id": entity_id,
            "direction": "increase" if new_daily > current_daily else "reduce",
            "current_daily_budget": current_daily,
            "new_daily_budget": new_daily,
            "campaign_status": before.get("effective_status") or before.get("status"),
            "change_diff": {"daily_budget": {"before": current_daily, "after": new_daily}},
        },
    ):
        sys.exit(1)

    resp = api_post(url, data=payload, label=f"budget/{entity_id}")
    log(f"Budget updated: {entity_id} -> ${args.amount}/day ({amount_cents} cents)")
    _log_mutation(
        "budget",
        entity_id,
        {"daily_budget": amount_cents, "approval_id": args.approval_id},
        resp,
    )
    print(json.dumps(resp, indent=2))


def cmd_create_campaign(args: argparse.Namespace) -> None:
    """Create a new campaign. Always PAUSED by default."""
    if args.status and args.status.upper() == "ACTIVE":
        print("ERROR: Meta campaign create cannot use ACTIVE status; create PAUSED and activate separately.", file=sys.stderr)
        sys.exit(1)
    if args.execute and not _require_approval_id(args):
        sys.exit(1)

    url = f"{BASE_URL}/{_account_id()}/campaigns"
    payload = {
        "name": args.name,
        "objective": args.objective,
        "status": args.status or "PAUSED",
        "special_ad_categories": f"[{args.special_ad_category}]" if args.special_ad_category else "[]",
        "access_token": _token(),
    }

    if not args.execute:
        _dry_run_banner("POST", url, payload)
        return
    if not _policy_preflight(
        args,
        action_type="create_paused_campaign",
        proposed_changes={
            "status": payload["status"],
            "change_diff": {"campaign": {"before": None, "after": {"name": args.name}}},
        },
    ):
        sys.exit(1)

    resp = api_post(url, data=payload, label="create-campaign")
    campaign_id = resp.get("id", "unknown")
    log(f"Campaign created: {campaign_id} ({args.name})")
    log_payload = {k: v for k, v in payload.items() if k != "access_token"}
    log_payload["approval_id"] = args.approval_id
    _log_mutation("create-campaign", campaign_id, log_payload, resp)
    print(json.dumps(resp, indent=2))


def cmd_create_adset(args: argparse.Namespace) -> None:
    """Create a new ad set. Budget in dollars, converted to cents."""
    if args.execute and not _require_approval_id(args):
        sys.exit(1)

    url = f"{BASE_URL}/{_account_id()}/adsets"
    budget_cents = int(float(args.daily_budget) * 100)
    payload = {
        "name": args.name,
        "campaign_id": args.campaign_id,
        "daily_budget": str(budget_cents),
        "billing_event": "IMPRESSIONS",
        "optimization_goal": args.optimization_goal,
        "targeting": args.targeting,  # JSON string
        "status": "PAUSED",
        "access_token": _token(),
    }
    if args.promoted_object:
        payload["promoted_object"] = args.promoted_object

    if not args.execute:
        _dry_run_banner("POST", url, payload)
        log(f"  (${args.daily_budget}/day = {budget_cents} cents)")
        return
    if not _policy_preflight(
        args,
        action_type="create_paused_adset",
        proposed_changes={
            "campaign_id": args.campaign_id,
            "status": "PAUSED",
            "change_diff": {"adset": {"before": None, "after": {"name": args.name}}},
        },
    ):
        sys.exit(1)

    resp = api_post(url, data=payload, label="create-adset")
    adset_id = resp.get("id", "unknown")
    log(f"Ad set created: {adset_id} ({args.name})")
    log_payload = {k: v for k, v in payload.items() if k != "access_token"}
    log_payload["approval_id"] = args.approval_id
    _log_mutation("create-adset", adset_id, log_payload, resp)
    print(json.dumps(resp, indent=2))


def cmd_create_ad(args: argparse.Namespace) -> None:
    """Create a new ad in an ad set. Creative spec as JSON string."""
    if args.execute and not _require_approval_id(args):
        sys.exit(1)

    url = f"{BASE_URL}/{_account_id()}/ads"
    payload = {
        "name": args.name,
        "adset_id": args.adset_id,
        "creative": args.creative_json,  # JSON string with object_story_spec
        "status": "PAUSED",
        "access_token": _token(),
    }

    if not args.execute:
        _dry_run_banner("POST", url, payload)
        return
    if not _policy_preflight(
        args,
        action_type="create_paused_ad",
        proposed_changes={
            "adset_id": args.adset_id,
            "status": "PAUSED",
            "change_diff": {"ad": {"before": None, "after": {"name": args.name}}},
        },
    ):
        sys.exit(1)

    resp = api_post(url, data=payload, label="create-ad")
    ad_id = resp.get("id", "unknown")
    log(f"Ad created: {ad_id} ({args.name})")
    log_payload = {k: v for k, v in payload.items() if k != "access_token"}
    log_payload["approval_id"] = args.approval_id
    _log_mutation("create-ad", ad_id, log_payload, resp)
    print(json.dumps(resp, indent=2))


def cmd_upload_image(args: argparse.Namespace) -> None:
    """Upload an image file. Returns image_hash. Not dry-runnable (safe operation)."""
    if not _policy_preflight(
        args,
        action_type="upload_ad_asset",
        proposed_changes={
            "status": "PAUSED",
            "change_diff": {"asset": {"before": None, "after": args.file}},
        },
    ):
        sys.exit(1)

    import requests as req

    url = f"{BASE_URL}/{_account_id()}/adimages"
    log(f"Uploading image: {args.file}")

    with open(args.file, "rb") as f:
        resp = req.post(url, data={"access_token": _token()}, files={"filename": f}, timeout=60)
    resp.raise_for_status()
    body = resp.json()

    if "error" in body and isinstance(body["error"], dict):
        err = body["error"]
        print(f"ERROR: [{err.get('code', '?')}] {err.get('message', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    images = body.get("images", {})
    for fname, data in images.items():
        log(f"Uploaded: {fname}")
        log(f"Hash: {data['hash']}")
        _log_mutation(
            "upload-image",
            data["hash"],
            {"file": args.file, "approval_id": args.approval_id},
            {"hash": data["hash"], "filename": fname},
        )
        print(data["hash"])  # stdout: machine-readable
        return

    # Fallback if images dict is empty
    log("Warning: upload succeeded but no image hash returned.")
    print(json.dumps(body, indent=2))


def cmd_upload_video(args: argparse.Namespace) -> None:
    """Upload a video file. Not dry-runnable (safe operation)."""
    if not _policy_preflight(
        args,
        action_type="upload_ad_asset",
        proposed_changes={
            "status": "PAUSED",
            "change_diff": {"asset": {"before": None, "after": args.file}},
        },
    ):
        sys.exit(1)

    import requests as req

    url = f"{BASE_URL}/{_account_id()}/advideos"
    log(f"Uploading video: {args.file}")

    form_data = {"access_token": _token()}
    if args.title:
        form_data["title"] = args.title

    with open(args.file, "rb") as f:
        resp = req.post(url, data=form_data, files={"source": f}, timeout=300)
    resp.raise_for_status()
    body = resp.json()

    if "error" in body and isinstance(body["error"], dict):
        err = body["error"]
        print(f"ERROR: [{err.get('code', '?')}] {err.get('message', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    video_id = body.get("id", "unknown")
    log(f"Uploaded video: {video_id}")
    _log_mutation(
        "upload-video",
        video_id,
        {"file": args.file, "title": args.title, "approval_id": args.approval_id},
        body,
    )
    print(json.dumps(body, indent=2))


def cmd_duplicate_adset(args: argparse.Namespace) -> None:
    """Duplicate an ad set: read source config, create new with different name/budget."""
    if args.execute and not _require_approval_id(args):
        sys.exit(1)

    # Read source ad set
    source_url = (
        f"{BASE_URL}/{args.id}"
        f"?fields=campaign_id,targeting,optimization_goal,billing_event,promoted_object,daily_budget"
        f"&access_token={_token()}"
    )
    log(f"Reading source ad set: {args.id}")
    source = api_get(source_url, label=f"read_adset/{args.id}")

    # Build new ad set payload
    budget = int(float(args.daily_budget) * 100) if args.daily_budget else source.get("daily_budget")
    payload = {
        "name": args.name,
        "campaign_id": source["campaign_id"],
        "daily_budget": str(budget),
        "billing_event": source.get("billing_event", "IMPRESSIONS"),
        "optimization_goal": source.get("optimization_goal", "LEAD_GENERATION"),
        "targeting": json.dumps(source.get("targeting", {})),
        "status": "PAUSED",
        "access_token": _token(),
    }
    if source.get("promoted_object"):
        payload["promoted_object"] = json.dumps(source["promoted_object"])

    url = f"{BASE_URL}/{_account_id()}/adsets"

    if not args.execute:
        _dry_run_banner("POST", url, payload)
        log(f"  Source ad set: {args.id}")
        log(f"  Budget: ${int(budget) / 100:.2f}/day" if budget else "  Budget: (inherited from source)")
        return
    if not _policy_preflight(
        args,
        action_type="create_paused_adset",
        proposed_changes={
            "campaign_id": source["campaign_id"],
            "status": "PAUSED",
            "change_diff": {"adset": {"before": args.id, "after": {"name": args.name}}},
        },
    ):
        sys.exit(1)

    resp = api_post(url, data=payload, label=f"duplicate-adset/{args.id}")
    new_id = resp.get("id", "unknown")
    log(f"Ad set duplicated: {args.id} -> {new_id} ({args.name})")
    log_payload = {k: v for k, v in payload.items() if k != "access_token"}
    log_payload["approval_id"] = args.approval_id
    _log_mutation("duplicate-adset", new_id, log_payload, resp)
    print(json.dumps(resp, indent=2))


# ---------------------------------------------------------------------------
# Argparse setup
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="meta.py",
        description="Unified Meta/Facebook ads — pull data and execute mutations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand")

    # ---- pull ----
    p_pull = subparsers.add_parser("pull", help="Pull comprehensive account data into a local JSON snapshot")
    p_pull.add_argument("--date", type=str, default=None,
                        help="Override output date directory (YYYY-MM-DD, default: today UTC)")
    p_pull.set_defaults(func=cmd_pull)

    # ---- pause ----
    p_pause = subparsers.add_parser("pause", help="Pause a campaign, ad set, or ad")
    p_pause.add_argument("--id", required=True, help="Entity ID to pause")
    p_pause.add_argument("--execute", action="store_true", default=False,
                         help="Actually execute (default: dry run)")
    p_pause.add_argument("--approval-id", default=None,
                         help="Required with --execute. Links the write to a human-approved action.")
    p_pause.add_argument("--rollback-reference", default=None,
                         help="Required with --execute. Command/runbook to reverse the pause.")
    p_pause.set_defaults(func=cmd_pause)

    # ---- activate ----
    p_activate = subparsers.add_parser("activate", help="Activate a campaign, ad set, or ad")
    p_activate.add_argument("--id", required=True, help="Entity ID to activate")
    p_activate.add_argument("--execute", action="store_true", default=False,
                            help="Actually execute (default: dry run)")
    p_activate.add_argument("--approval-id", default=None,
                            help="Required with --execute. Links the write to a human-approved action.")
    p_activate.add_argument("--rollback-reference", default=None,
                            help="Required with --execute. Command/runbook to reverse the activation.")
    p_activate.set_defaults(func=cmd_activate)

    # ---- budget ----
    p_budget = subparsers.add_parser("budget", help="Change daily budget (dollars)")
    p_budget.add_argument("--id", required=True, help="Ad set or campaign ID")
    p_budget.add_argument("--amount", required=True, help="Daily budget in dollars (e.g. 25.00)")
    p_budget.add_argument("--execute", action="store_true", default=False,
                          help="Actually execute (default: dry run)")
    p_budget.add_argument("--approval-id", default=None,
                          help="Required with --execute. Links the write to a human-approved action.")
    p_budget.set_defaults(func=cmd_budget)

    # ---- create-campaign ----
    p_cc = subparsers.add_parser("create-campaign", help="Create a new campaign (PAUSED by default)")
    p_cc.add_argument("--name", required=True, help="Campaign name")
    p_cc.add_argument("--objective", required=True,
                      help="Campaign objective (e.g. OUTCOME_LEADS, OUTCOME_TRAFFIC, OUTCOME_AWARENESS)")
    p_cc.add_argument("--special-ad-category", default=None,
                      help="Special ad category (e.g. HOUSING, EMPLOYMENT, CREDIT)")
    p_cc.add_argument("--status", default=None,
                      help="Initial status (default: PAUSED)")
    p_cc.add_argument("--execute", action="store_true", default=False,
                      help="Actually execute (default: dry run)")
    p_cc.add_argument("--approval-id", default=None,
                      help="Required with --execute. Links the write to a human-approved action.")
    p_cc.set_defaults(func=cmd_create_campaign)

    # ---- create-adset ----
    p_cas = subparsers.add_parser("create-adset", help="Create a new ad set (PAUSED by default)")
    p_cas.add_argument("--campaign-id", required=True, help="Parent campaign ID")
    p_cas.add_argument("--name", required=True, help="Ad set name")
    p_cas.add_argument("--daily-budget", required=True, help="Daily budget in dollars (e.g. 25)")
    p_cas.add_argument("--optimization-goal", required=True,
                       help="Optimization goal (e.g. LEAD_GENERATION, LINK_CLICKS, IMPRESSIONS)")
    p_cas.add_argument("--targeting", required=True,
                       help='Targeting JSON string (e.g. \'{"age_min":25,"geo_locations":{"countries":["US"]}}\')')
    p_cas.add_argument("--promoted-object", default=None,
                       help='Promoted object JSON string (e.g. \'{"page_id":"123456"}\')')
    p_cas.add_argument("--execute", action="store_true", default=False,
                       help="Actually execute (default: dry run)")
    p_cas.add_argument("--approval-id", default=None,
                       help="Required with --execute. Links the write to a human-approved action.")
    p_cas.set_defaults(func=cmd_create_adset)

    # ---- create-ad ----
    p_ca = subparsers.add_parser("create-ad", help="Create a new ad (PAUSED by default)")
    p_ca.add_argument("--adset-id", required=True, help="Parent ad set ID")
    p_ca.add_argument("--name", required=True, help="Ad name")
    p_ca.add_argument("--creative-json", required=True,
                      help='Creative JSON string (e.g. \'{"object_story_spec":{...}}\')')
    p_ca.add_argument("--execute", action="store_true", default=False,
                      help="Actually execute (default: dry run)")
    p_ca.add_argument("--approval-id", default=None,
                      help="Required with --execute. Links the write to a human-approved action.")
    p_ca.set_defaults(func=cmd_create_ad)

    # ---- upload-image ----
    p_ui = subparsers.add_parser("upload-image", help="Upload an image file (returns image_hash)")
    p_ui.add_argument("--file", required=True, help="Path to image file (png, jpg, etc.)")
    p_ui.add_argument("--approval-id", required=True,
                      help="Required. Links the live upload to a human-approved action.")
    p_ui.set_defaults(func=cmd_upload_image)

    # ---- upload-video ----
    p_uv = subparsers.add_parser("upload-video", help="Upload a video file")
    p_uv.add_argument("--file", required=True, help="Path to video file (mp4, etc.)")
    p_uv.add_argument("--title", default=None, help="Video title/name")
    p_uv.add_argument("--approval-id", required=True,
                      help="Required. Links the live upload to a human-approved action.")
    p_uv.set_defaults(func=cmd_upload_video)

    # ---- duplicate-adset ----
    p_dup = subparsers.add_parser("duplicate-adset", help="Duplicate an ad set with new name/budget")
    p_dup.add_argument("--id", required=True, help="Source ad set ID to duplicate")
    p_dup.add_argument("--name", required=True, help="Name for the new ad set")
    p_dup.add_argument("--daily-budget", default=None,
                       help="New daily budget in dollars (default: same as source)")
    p_dup.add_argument("--execute", action="store_true", default=False,
                       help="Actually execute (default: dry run)")
    p_dup.add_argument("--approval-id", default=None,
                       help="Required with --execute. Links the write to a human-approved action.")
    p_dup.set_defaults(func=cmd_duplicate_adset)

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except APIError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
