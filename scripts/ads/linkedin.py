"""Unified LinkedIn Ads CLI — pull data and manage campaigns.

Usage:
    python scripts/ads/linkedin.py pull [--date YYYY-MM-DD]
    python scripts/ads/linkedin.py pause --id <campaign_id> [--execute]
    python scripts/ads/linkedin.py activate --id <campaign_id> [--execute]
    python scripts/ads/linkedin.py budget --id <campaign_id> --amount <dollars> [--execute]

All mutation commands default to --dry-run. Pass --execute to apply changes.

Requires LINKEDINADS_ACCESS_TOKEN and LINKEDINADS_ACCOUNT_ID in .env.local.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from _pull_common import (
    APIError,
    api_get,
    env,
    has_creds,
    log,
    log_section,
    today_str,
    write_pull,
    REPO_ROOT,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REST_BASE = "https://api.linkedin.com/rest"

# Required headers for LinkedIn Marketing API (REST surface)
LINKEDIN_VERSION = "202401"

# Analytics fields to request
ANALYTICS_FIELDS = (
    "impressions,clicks,externalWebsiteConversions,costInLocalCurrency,"
    "totalEngagements,likes,comments,shares,follows,viralImpressions,"
    "viralClicks,oneClickLeads,opens,landingPageClicks,otherEngagements,reactions"
)

# Audience breakdown pivots
AUDIENCE_PIVOTS = [
    ("MEMBER_COMPANY_SIZE", "company_size"),
    ("MEMBER_INDUSTRY", "industry"),
    ("MEMBER_JOB_FUNCTION", "job_function"),
    ("MEMBER_SENIORITY", "seniority"),
    ("MEMBER_COUNTRY", "country"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _account_id() -> str:
    return env("LINKEDINADS_ACCOUNT_ID")


def _token() -> str:
    return env("LINKEDINADS_ACCESS_TOKEN")


def _headers() -> Dict[str, str]:
    """Standard headers for LinkedIn Marketing REST API."""
    return {
        "Authorization": f"Bearer {_token()}",
        "LinkedIn-Version": LINKEDIN_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _date_range_str(start: datetime, end: datetime) -> str:
    """Format a LinkedIn dateRange query parameter."""
    return (
        f"(start:(year:{start.year},month:{start.month},day:{start.day}),"
        f"end:(year:{end.year},month:{end.month},day:{end.day}))"
    )


def _compute_date_ranges(anchor: datetime) -> Dict[str, Tuple[datetime, datetime]]:
    """Compute last-7d, last-14d, and last-28d date ranges ending at anchor."""
    return {
        "7d": (anchor - timedelta(days=7), anchor),
        "14d": (anchor - timedelta(days=14), anchor),
        "28d": (anchor - timedelta(days=28), anchor),
    }


def _budget_float(budget_obj: Any) -> Optional[float]:
    """Extract float dollar amount from LinkedIn budget object {amount, currencyCode}."""
    if not budget_obj or not isinstance(budget_obj, dict):
        return None
    amount = budget_obj.get("amount")
    if amount is None:
        return None
    try:
        return float(amount)
    except (ValueError, TypeError):
        return None


def _li_get(url: str, params: Optional[Dict[str, Any]] = None, label: str = "") -> Dict[str, Any]:
    """LinkedIn API GET with auth headers. Wraps api_get for retry/backoff."""
    return api_get(url, headers=_headers(), params=params, label=label)


def _li_get_safe(url: str, params: Optional[Dict[str, Any]] = None,
                 label: str = "") -> Optional[Dict[str, Any]]:
    """LinkedIn API GET that returns None on 401/403 instead of raising.

    The LinkedIn access token may not have full Marketing API scope.
    This helper lets us degrade gracefully for entity endpoints while
    still raising on unexpected errors.
    """
    try:
        return _li_get(url, params=params, label=label)
    except APIError as e:
        err_str = str(e)
        if "401" in err_str or "403" in err_str or "UNAUTHORIZED" in err_str.upper():
            log(f"  Permission denied for {label}: {e}")
            log("  Hint: the access token may lack Marketing API scope.")
            log("  Required scopes: r_ads, r_ads_reporting, r_organization_social")
            return None
        raise


# ---------------------------------------------------------------------------
# Analytics puller
# ---------------------------------------------------------------------------

def _pull_analytics(
    pivot: str,
    date_range: Tuple[datetime, datetime],
    campaign_urns: Optional[List[str]] = None,
    campaign_group_urns: Optional[List[str]] = None,
    time_granularity: str = "DAILY",
    label: str = "",
) -> List[Dict[str, Any]]:
    """Pull analytics from the adAnalytics endpoint.

    Returns a list of analytics rows, or empty list on failure.
    """
    start, end = date_range

    params: Dict[str, Any] = {
        "q": "analytics",
        "dateRange": _date_range_str(start, end),
        "timeGranularity": time_granularity,
        "pivot": pivot,
        "fields": ANALYTICS_FIELDS,
    }

    # Attach entity filters
    if campaign_urns:
        params["campaigns"] = f"List({','.join(campaign_urns)})"
    if campaign_group_urns:
        params["campaignGroups"] = f"List({','.join(campaign_group_urns)})"

    url = f"{REST_BASE}/adAnalytics"

    try:
        resp = _li_get(url, params=params, label=label)
        return resp.get("elements", [])
    except APIError as e:
        log(f"  Analytics query failed ({label}): {e}")
        return []


def _rows_to_daily(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert analytics rows (with dateRange) to a flat daily list."""
    daily: List[Dict[str, Any]] = []
    for row in rows:
        dr = row.get("dateRange", {})
        start = dr.get("start", {})
        date_str = (
            f"{start.get('year', 0):04d}-{start.get('month', 0):02d}-{start.get('day', 0):02d}"
        )
        entry = {"date": date_str}
        for k, v in row.items():
            if k not in ("dateRange", "pivot", "pivotValue", "pivotValues"):
                entry[k] = v
        daily.append(entry)
    daily.sort(key=lambda x: x.get("date", ""))
    return daily


# ---------------------------------------------------------------------------
# Audience type classification
# ---------------------------------------------------------------------------

def _classify_audience(campaign: Dict[str, Any]) -> Tuple[str, str]:
    """Classify a LinkedIn campaign's targeting into an audience type and detail string."""
    targeting = campaign.get("targetingCriteria") or campaign.get("targeting") or {}

    # Check for matched audiences (custom/LAL equivalent)
    include = targeting.get("include", {})
    exclude = targeting.get("exclude", {})

    # Flatten all facet URNs
    facet_names: List[str] = []
    matched = False

    for clause_group in [include, exclude]:
        if isinstance(clause_group, dict):
            and_list = clause_group.get("and", [])
            for and_clause in and_list:
                or_clause = and_clause.get("or", {})
                for facet_urn in or_clause:
                    facet_short = facet_urn.split(":")[-1] if ":" in facet_urn else facet_urn
                    facet_names.append(facet_short)
                    if "matchedAudience" in facet_urn or "matched" in facet_urn.lower():
                        matched = True

    # Audience expansion
    expansion = campaign.get("audienceExpansionEnabled", False)

    if matched:
        return "matched_audience", f"Matched audience targeting (expansion={'on' if expansion else 'off'})"

    # Determine targeting richness
    professional_facets = {
        "titles", "jobTitle", "jobFunction", "seniorities", "seniority",
        "industries", "industry", "companies", "company", "companySize",
        "memberCompanySize", "skills", "degrees", "fieldsOfStudy",
    }
    found_professional = [f for f in facet_names if any(p in f for p in professional_facets)]

    if found_professional:
        detail_parts: List[str] = []
        for f in found_professional[:5]:
            detail_parts.append(f)
        detail = f"Professional targeting: {', '.join(detail_parts)}"
        if expansion:
            detail += " (expansion on)"
        return "professional_targeting", detail

    if facet_names:
        return "professional_targeting", f"Facets: {', '.join(facet_names[:5])}"

    return "broad", f"Minimal targeting detected (expansion={'on' if expansion else 'off'})"


# ---------------------------------------------------------------------------
# Section pullers
# ---------------------------------------------------------------------------

def pull_campaign_groups(account_id: str) -> Optional[List[Dict[str, Any]]]:
    log_section("Campaign Groups")

    url = (
        f"{REST_BASE}/adAccounts/{account_id}/adCampaignGroups"
        f"?q=search&search=(status:(values:List(ACTIVE,PAUSED,DRAFT)))&count=100"
    )
    resp = _li_get_safe(url, label="campaign_groups")
    if resp is None:
        log("  Skipping campaign groups (insufficient permissions)")
        return None

    groups = resp.get("elements", [])
    log(f"  Found {len(groups)} campaign groups")
    return groups


def pull_campaigns(account_id: str) -> Optional[List[Dict[str, Any]]]:
    log_section("Campaigns")

    url = (
        f"{REST_BASE}/adAccounts/{account_id}/adCampaigns"
        f"?q=search&search=(status:(values:List(ACTIVE,PAUSED,DRAFT)))&count=100"
    )
    resp = _li_get_safe(url, label="campaigns")
    if resp is None:
        log("  Skipping campaigns (insufficient permissions)")
        return None

    campaigns = resp.get("elements", [])
    log(f"  Found {len(campaigns)} campaigns")

    for i, c in enumerate(campaigns):
        cid = c.get("id", "?")
        name = c.get("name", cid)

        # Extract budget
        c["daily_budget_usd"] = _budget_float(c.get("dailyBudget"))

        # Classify audience
        audience_type, audience_detail = _classify_audience(c)
        c["audience_type"] = audience_type
        c["audience_detail"] = audience_detail

        log(f"  [{i+1}/{len(campaigns)}] {name} ({audience_type})")

    return campaigns


def pull_creatives(account_id: str, campaign_ids: List[str]) -> Optional[List[Dict[str, Any]]]:
    log_section("Creatives")

    if not campaign_ids:
        log("  No campaigns — skipping creatives")
        return []

    all_creatives: List[Dict[str, Any]] = []

    # Pull creatives per campaign (API requires campaign filter)
    for i, cid in enumerate(campaign_ids):
        urn = f"urn:li:sponsoredCampaign:{cid}"
        url = (
            f"{REST_BASE}/adAccounts/{account_id}/creatives"
            f"?q=search&search=(campaign:(values:List({urn})))&count=100"
        )
        resp = _li_get_safe(url, label=f"creatives/campaign_{cid}")
        if resp is None:
            log("  Skipping creatives (insufficient permissions)")
            return None

        elements = resp.get("elements", [])
        for cr in elements:
            cr["campaign_id"] = cid
        all_creatives.extend(elements)

        if (i + 1) % 10 == 0 or i == len(campaign_ids) - 1:
            log(f"  Processed {i+1}/{len(campaign_ids)} campaigns, {len(all_creatives)} creatives so far")

    log(f"  Found {len(all_creatives)} total creatives")
    return all_creatives


def pull_entity_analytics(
    entity_type: str,
    entity_ids: List[str],
    date_ranges: Dict[str, Tuple[datetime, datetime]],
    pivot: str,
    urn_prefix: str,
) -> Dict[str, Dict[str, Any]]:
    """Pull analytics for a list of entities and return {entity_id: {insights_daily, insights_7d, ...}}."""
    log_section(f"Analytics — {entity_type} level ({pivot})")

    results: Dict[str, Dict[str, Any]] = {}
    if not entity_ids:
        log(f"  No {entity_type} IDs — skipping")
        return results

    # Build URN list
    urns = [f"{urn_prefix}{eid}" for eid in entity_ids]

    # Batch analytics: LinkedIn allows multiple entities in one call
    # Process in chunks of 20 to avoid URL length limits
    chunk_size = 20

    for range_key, (start, end) in date_ranges.items():
        granularity = "DAILY" if range_key == "14d" else "ALL"
        insight_key = f"insights_daily" if granularity == "DAILY" else f"insights_{range_key}"

        for chunk_start in range(0, len(urns), chunk_size):
            chunk_urns = urns[chunk_start:chunk_start + chunk_size]
            _ = entity_ids[chunk_start:chunk_start + chunk_size]  # parallel slice for debugging

            label = f"{entity_type}/{range_key}/chunk_{chunk_start}"
            log(f"  Pulling {range_key} ({granularity}) for {len(chunk_urns)} {entity_type}s...")

            if pivot == "CAMPAIGN":
                rows = _pull_analytics(
                    pivot=pivot,
                    date_range=(start, end),
                    campaign_urns=chunk_urns,
                    time_granularity=granularity,
                    label=label,
                )
            elif pivot == "CAMPAIGN_GROUP":
                rows = _pull_analytics(
                    pivot=pivot,
                    date_range=(start, end),
                    campaign_group_urns=chunk_urns,
                    time_granularity=granularity,
                    label=label,
                )
            elif pivot == "CREATIVE":
                # Creative-level needs campaign filter
                rows = _pull_analytics(
                    pivot=pivot,
                    date_range=(start, end),
                    campaign_urns=chunk_urns,
                    time_granularity=granularity,
                    label=label,
                )
            else:
                rows = []

            # Assign rows to their entity
            for row in rows:
                # Extract entity ID from pivotValue URN
                pivot_val = row.get("pivotValue", "")
                eid = pivot_val.split(":")[-1] if ":" in pivot_val else pivot_val

                if eid not in results:
                    results[eid] = {}

                if granularity == "DAILY":
                    existing = results[eid].get(insight_key, [])
                    existing.append(row)
                    results[eid][insight_key] = existing
                else:
                    results[eid][insight_key] = row

    # Convert daily rows to clean format
    for eid, data in results.items():
        if "insights_daily" in data:
            data["insights_daily"] = _rows_to_daily(data["insights_daily"])

    return results


def pull_audience_breakdowns(
    campaign_ids: List[str],
    date_range: Tuple[datetime, datetime],
) -> Dict[str, List[Dict[str, Any]]]:
    """Pull audience breakdown analytics across all campaigns."""
    log_section("Audience Breakdowns")

    breakdowns: Dict[str, List[Dict[str, Any]]] = {}
    urns = [f"urn:li:sponsoredCampaign:{cid}" for cid in campaign_ids]

    if not urns:
        log("  No campaigns — skipping breakdowns")
        return breakdowns

    for pivot_name, key in AUDIENCE_PIVOTS:
        log(f"  Pulling {key}...")
        rows = _pull_analytics(
            pivot=pivot_name,
            date_range=date_range,
            campaign_urns=urns,
            time_granularity="ALL",
            label=f"breakdown/{key}",
        )

        # Clean up rows
        clean: List[Dict[str, Any]] = []
        for row in rows:
            entry: Dict[str, Any] = {}
            pivot_val = row.get("pivotValue", "")
            entry["pivot_value"] = pivot_val
            # Extract readable name from URN
            entry["label"] = pivot_val.split(":")[-1] if ":" in pivot_val else pivot_val
            for k, v in row.items():
                if k not in ("dateRange", "pivot", "pivotValue", "pivotValues"):
                    entry[k] = v
            clean.append(entry)
        breakdowns[key] = clean

    return breakdowns


# ---------------------------------------------------------------------------
# Pull main
# ---------------------------------------------------------------------------

def pull(date: Optional[str] = None) -> str:
    if not has_creds("LINKEDINADS_ACCESS_TOKEN", "LINKEDINADS_ACCOUNT_ID"):
        print(
            "ERROR: LINKEDINADS_ACCESS_TOKEN and LINKEDINADS_ACCOUNT_ID required in .env.local",
            file=sys.stderr,
        )
        sys.exit(1)

    account_id = _account_id()
    date = date or today_str()

    log(f"LinkedIn Ads pull starting for account {account_id} (date={date})")

    # Parse anchor date for date range computation
    try:
        anchor = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        anchor = datetime.now(timezone.utc)
    date_ranges = _compute_date_ranges(anchor)

    # --- Pull entity data ---
    campaign_groups = pull_campaign_groups(account_id)
    campaigns = pull_campaigns(account_id)
    campaign_ids = [str(c.get("id", "")) for c in (campaigns or []) if c.get("id")]
    creative_data = pull_creatives(account_id, campaign_ids)

    # --- Pull analytics ---
    # Campaign group level
    group_ids = [str(g.get("id", "")) for g in (campaign_groups or []) if g.get("id")]
    group_analytics = pull_entity_analytics(
        entity_type="campaign_group",
        entity_ids=group_ids,
        date_ranges={"7d": date_ranges["7d"], "28d": date_ranges["28d"], "14d": date_ranges["14d"]},
        pivot="CAMPAIGN_GROUP",
        urn_prefix="urn:li:sponsoredCampaignGroup:",
    )

    # Campaign level
    campaign_analytics = pull_entity_analytics(
        entity_type="campaign",
        entity_ids=campaign_ids,
        date_ranges={"7d": date_ranges["7d"], "14d": date_ranges["14d"]},
        pivot="CAMPAIGN",
        urn_prefix="urn:li:sponsoredCampaign:",
    )

    # Creative level (uses campaign pivot to pull, then groups by creative)
    creative_ids = list({str(cr.get("id", "")) for cr in (creative_data or []) if cr.get("id")})
    # For creatives, pull with CREATIVE pivot scoped to all campaigns
    creative_analytics: Dict[str, Dict[str, Any]] = {}
    if campaign_ids and creative_ids:
        log_section("Analytics — creative level (CREATIVE)")
        for range_key in ("7d",):
            start, end = date_ranges[range_key]
            urns = [f"urn:li:sponsoredCampaign:{cid}" for cid in campaign_ids]
            # Chunk campaigns
            chunk_size = 20
            for chunk_start in range(0, len(urns), chunk_size):
                chunk = urns[chunk_start:chunk_start + chunk_size]
                rows = _pull_analytics(
                    pivot="CREATIVE",
                    date_range=(start, end),
                    campaign_urns=chunk,
                    time_granularity="ALL",
                    label=f"creative/{range_key}/chunk_{chunk_start}",
                )
                for row in rows:
                    pv = row.get("pivotValue", "")
                    crid = pv.split(":")[-1] if ":" in pv else pv
                    if crid not in creative_analytics:
                        creative_analytics[crid] = {}
                    creative_analytics[crid][f"insights_{range_key}"] = row

    # Audience breakdowns (last 28d)
    breakdowns = pull_audience_breakdowns(campaign_ids, date_ranges["28d"])

    # --- Merge analytics into entities ---

    # Campaign groups
    out_groups: List[Dict[str, Any]] = []
    for g in (campaign_groups or []):
        gid = str(g.get("id", ""))
        entry = {
            "id": gid,
            "name": g.get("name", ""),
            "status": g.get("status", ""),
        }
        ga = group_analytics.get(gid, {})
        entry["insights_daily"] = ga.get("insights_daily", [])
        entry["insights_7d"] = ga.get("insights_7d", {})
        entry["insights_28d"] = ga.get("insights_28d", {})
        out_groups.append(entry)

    # Campaigns
    out_campaigns: List[Dict[str, Any]] = []
    for c in (campaigns or []):
        cid = str(c.get("id", ""))
        entry = {
            "id": cid,
            "name": c.get("name", ""),
            "status": c.get("status", ""),
            "objective": c.get("objectiveType", ""),
            "cost_type": c.get("costType", ""),
            "daily_budget_usd": c.get("daily_budget_usd"),
            "audience_type": c.get("audience_type", ""),
            "audience_detail": c.get("audience_detail", ""),
            "targeting": c.get("targetingCriteria") or c.get("targeting") or {},
            "campaign_group": c.get("campaignGroup", ""),
            "type": c.get("type", ""),
        }
        ca = campaign_analytics.get(cid, {})
        entry["insights_daily"] = ca.get("insights_daily", [])
        entry["insights_7d"] = ca.get("insights_7d", {})
        out_campaigns.append(entry)

    # Creatives
    out_creatives: List[Dict[str, Any]] = []
    for cr in (creative_data or []):
        crid = str(cr.get("id", ""))
        entry = {
            "id": crid,
            "campaign_id": cr.get("campaign_id", ""),
            "status": cr.get("status", ""),
        }
        cra = creative_analytics.get(crid, {})
        entry["insights_7d"] = cra.get("insights_7d", {})
        out_creatives.append(entry)

    # --- Assemble output ---
    data: Dict[str, Any] = {
        "account_id": account_id,
        "campaign_groups": out_groups,
        "campaigns": out_campaigns,
        "creatives": out_creatives,
        "breakdowns": breakdowns,
    }

    out_path = write_pull("linkedin", data, date=date)

    # Summary
    log_section("Pull Complete")
    log(f"  Campaign groups: {len(out_groups)}")
    log(f"  Campaigns:       {len(out_campaigns)}")
    log(f"  Creatives:       {len(out_creatives)}")
    log(f"  Breakdowns:      {len(breakdowns)} pivots")
    log(f"  Output:          {out_path}")

    return str(out_path)


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
        "platform": "linkedin",
        "command": command,
        "entity_id": entity_id,
        "payload": payload,
        "result": result,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


# ---------------------------------------------------------------------------
# Mutation commands
# ---------------------------------------------------------------------------

def cmd_pause(args: argparse.Namespace) -> None:
    """Pause a LinkedIn campaign."""
    if not has_creds("LINKEDINADS_ACCESS_TOKEN", "LINKEDINADS_ACCOUNT_ID"):
        print(
            "ERROR: LINKEDINADS_ACCESS_TOKEN and LINKEDINADS_ACCOUNT_ID required in .env.local",
            file=sys.stderr,
        )
        sys.exit(1)

    account_id = _account_id()
    campaign_id = args.id
    url = f"{REST_BASE}/adAccounts/{account_id}/adCampaigns/{campaign_id}"
    payload = {"status": "PAUSED"}

    if not args.execute:
        log(f"DRY RUN: PATCH {url}")
        log(f"  Payload: {json.dumps(payload)}")
        log(f"  Add --execute to apply.")
        return

    import requests
    resp = requests.patch(
        url,
        headers={**_headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json() if resp.text else {}
    _log_mutation("pause", campaign_id, payload, result)
    log(f"Paused campaign: {campaign_id}")


def cmd_activate(args: argparse.Namespace) -> None:
    """Activate a LinkedIn campaign."""
    if not has_creds("LINKEDINADS_ACCESS_TOKEN", "LINKEDINADS_ACCOUNT_ID"):
        print(
            "ERROR: LINKEDINADS_ACCESS_TOKEN and LINKEDINADS_ACCOUNT_ID required in .env.local",
            file=sys.stderr,
        )
        sys.exit(1)

    account_id = _account_id()
    campaign_id = args.id
    url = f"{REST_BASE}/adAccounts/{account_id}/adCampaigns/{campaign_id}"
    payload = {"status": "ACTIVE"}

    if not args.execute:
        log(f"DRY RUN: PATCH {url}")
        log(f"  Payload: {json.dumps(payload)}")
        log(f"  Add --execute to apply.")
        return

    import requests
    resp = requests.patch(
        url,
        headers={**_headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json() if resp.text else {}
    _log_mutation("activate", campaign_id, payload, result)
    log(f"Activated campaign: {campaign_id}")


def cmd_budget(args: argparse.Namespace) -> None:
    """Update the daily budget of a LinkedIn campaign."""
    if not has_creds("LINKEDINADS_ACCESS_TOKEN", "LINKEDINADS_ACCOUNT_ID"):
        print(
            "ERROR: LINKEDINADS_ACCESS_TOKEN and LINKEDINADS_ACCOUNT_ID required in .env.local",
            file=sys.stderr,
        )
        sys.exit(1)

    account_id = _account_id()
    campaign_id = args.id
    amount = float(args.amount)
    url = f"{REST_BASE}/adAccounts/{account_id}/adCampaigns/{campaign_id}"
    payload = {
        "dailyBudget": {
            "amount": str(amount),
            "currencyCode": "USD",
        }
    }

    if not args.execute:
        log(f"DRY RUN: PATCH {url}")
        log(f"  Payload: {json.dumps(payload)}")
        log(f"  New daily budget: ${amount:.2f} USD")
        log(f"  Add --execute to apply.")
        return

    import requests
    resp = requests.patch(
        url,
        headers={**_headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json() if resp.text else {}
    _log_mutation("budget", campaign_id, payload, result)
    log(f"Updated budget for campaign {campaign_id}: ${amount:.2f} USD/day")


# ---------------------------------------------------------------------------
# CLI — argparse with subcommands
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified LinkedIn Ads CLI — pull data and manage campaigns.",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # --- pull ---
    p_pull = sub.add_parser("pull", help="Pull LinkedIn Ads data into a local JSON snapshot")
    p_pull.add_argument(
        "--date", type=str, default=None,
        help="Override output date directory (YYYY-MM-DD, default: today UTC)",
    )

    # --- pause ---
    p_pause = sub.add_parser("pause", help="Pause a LinkedIn campaign (dry-run by default)")
    p_pause.add_argument("--id", required=True, help="Campaign ID to pause")
    p_pause.add_argument(
        "--execute", action="store_true", default=False,
        help="Actually apply the change (default: dry-run)",
    )

    # --- activate ---
    p_activate = sub.add_parser("activate", help="Activate a LinkedIn campaign (dry-run by default)")
    p_activate.add_argument("--id", required=True, help="Campaign ID to activate")
    p_activate.add_argument(
        "--execute", action="store_true", default=False,
        help="Actually apply the change (default: dry-run)",
    )

    # --- budget ---
    p_budget = sub.add_parser("budget", help="Update daily budget for a LinkedIn campaign (dry-run by default)")
    p_budget.add_argument("--id", required=True, help="Campaign ID to update")
    p_budget.add_argument("--amount", required=True, help="New daily budget in USD (e.g. 50.00)")
    p_budget.add_argument(
        "--execute", action="store_true", default=False,
        help="Actually apply the change (default: dry-run)",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "pull":
            path = pull(date=args.date)
            print(path)

        elif args.command == "pause":
            cmd_pause(args)

        elif args.command == "activate":
            cmd_activate(args)

        elif args.command == "budget":
            cmd_budget(args)

        else:
            parser.print_help()
            sys.exit(1)

    except APIError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
