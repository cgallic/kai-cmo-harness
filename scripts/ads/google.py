#!/usr/bin/env python3
"""Google Ads unified CLI — pull performance data and execute mutations.

Subcommands:
    pull        Fetch campaign, ad group, ad, search term, audience, and
                keyword quality data via the REST API with GAQL.
    pause       Pause a campaign, ad group, or ad.
    activate    Activate (enable) a campaign, ad group, or ad.
    budget      Change a campaign's daily budget.
    add-negative  Add a negative keyword to a campaign.

Safety:
    ALL mutation subcommands default to --dry-run.  Pass --execute to apply.

Usage:
    python scripts/ads/google.py pull [--date YYYY-MM-DD]
    python scripts/ads/google.py pause --type campaign|ad_group|ad --id <resource_name_or_id> [--execute]
    python scripts/ads/google.py activate --type campaign|ad_group|ad --id <resource_name_or_id> [--execute]
    python scripts/ads/google.py budget --campaign-id <id> --amount <dollars> [--execute]
    python scripts/ads/google.py add-negative --campaign-id <id> --keyword "term" [--match-type BROAD|PHRASE|EXACT] [--execute]

Required env vars (in .env.local, .env, or environment):
    GOOGLE_CREDENTIALS_PATH      Path to service account JSON file
    GOOGLE_ADS_CUSTOMER_ID       Customer ID (format: XXX-XXX-XXXX)
    GOOGLE_ADS_DEVELOPER_TOKEN   API developer token

Optional:
    GOOGLE_ADS_LOGIN_CUSTOMER_ID MCC manager account ID (if using manager account)
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Common utilities
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _pull_common import (
    APIError,
    api_post,
    env,
    log,
    log_section,
    today_str,
    write_pull,
    REPO_ROOT,
)

sys.path.insert(0, str(REPO_ROOT))
from kai.runtime.policy import PolicyEngine

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_VERSION = "v17"
SEARCH_STREAM_URL = (
    "https://googleads.googleapis.com/{version}/customers/{customer_id}/googleAds:searchStream"
)
MUTATE_URL = (
    "https://googleads.googleapis.com/{version}/customers/{customer_id}/googleAds:mutate"
)
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/adwords"

REQUIRED_CREDS = (
    "GOOGLE_CREDENTIALS_PATH",
    "GOOGLE_ADS_CUSTOMER_ID",
    "GOOGLE_ADS_DEVELOPER_TOKEN",
)

MUTATIONS_DIR = REPO_ROOT / "workspace" / "ads" / "mutations"

# ---------------------------------------------------------------------------
# Authentication — JWT -> access token
# ---------------------------------------------------------------------------


def _b64url(data: bytes) -> str:
    """Base64url-encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _load_service_account(path: str) -> Dict[str, Any]:
    """Load and validate a Google service account JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Service account file not found: {path}")
    with open(p, "r", encoding="utf-8") as f:
        sa = json.load(f)
    for key in ("client_email", "private_key", "token_uri"):
        if key not in sa:
            raise ValueError(f"Service account JSON missing required field: {key}")
    return sa


def _make_jwt(sa: Dict[str, Any]) -> str:
    """Create a signed JWT for the service account.

    Tries PyJWT first (``pip install PyJWT cryptography``).  Falls back to
    manual construction with ``cryptography`` alone.  If neither is
    available, raises with a clear install message.
    """
    now = int(time.time())
    payload = {
        "iss": sa["client_email"],
        "scope": SCOPE,
        "aud": sa.get("token_uri", TOKEN_URL),
        "iat": now,
        "exp": now + 3600,
    }

    # --- Attempt 1: PyJWT + cryptography ---
    try:
        import jwt  # PyJWT

        return jwt.encode(payload, sa["private_key"], algorithm="RS256")
    except ImportError:
        pass

    # --- Attempt 2: cryptography alone (manual JWT) ---
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
        claims = _b64url(json.dumps(payload).encode())
        signing_input = f"{header}.{claims}".encode()

        private_key = serialization.load_pem_private_key(
            sa["private_key"].encode(), password=None
        )
        rsa_padding = padding.PKCS1v15()
        hash_alg = hashes.SHA256()
        signature = private_key.sign(signing_input, rsa_padding, hash_alg)  # type: ignore[union-attr,call-arg]
        return f"{header}.{claims}.{_b64url(signature)}"
    except ImportError:
        pass

    raise ImportError(
        "Google Ads authentication requires either:\n"
        "  pip install PyJWT cryptography\n"
        "  pip install cryptography\n"
        "Please install one of these and retry."
    )


def get_google_token() -> str:
    """Exchange a service-account JWT for a Google OAuth2 access token."""
    creds_path = env("GOOGLE_CREDENTIALS_PATH")
    sa = _load_service_account(creds_path)
    assertion = _make_jwt(sa)

    import requests

    resp = requests.post(
        sa.get("token_uri", TOKEN_URL),
        data={
            "grant_type": "urn:ietf:params:oauth:grant_type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()
    token = body.get("access_token")
    if not token:
        raise APIError(f"Token exchange failed: {body}")
    return token


# ---------------------------------------------------------------------------
# GAQL execution
# ---------------------------------------------------------------------------


def _flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """Flatten a nested protobuf-style dict into dot-separated keys.

    Example:
        {"campaign": {"id": "1", "name": "X"}, "metrics": {"clicks": "5"}}
        -> {"campaign.id": "1", "campaign.name": "X", "metrics.clicks": "5"}
    """
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(_flatten(v, full_key))
            elif isinstance(v, list):
                # Keep lists as-is (e.g. RSA headlines/descriptions)
                out[full_key] = v
            else:
                out[full_key] = v
    return out


def _clean_customer_id(cid: str) -> str:
    """Remove dashes from customer ID: '123-456-7890' -> '1234567890'."""
    return cid.replace("-", "")


def run_gaql(
    customer_id: str,
    query: str,
    headers: Dict[str, str],
    label: str = "",
) -> List[Dict[str, Any]]:
    """Execute a GAQL query via searchStream and return flattened results.

    Google Ads searchStream returns an array of batches, each with a
    ``results`` list.  We flatten every result dict so that nested keys
    like ``campaign.name`` and ``metrics.clicks`` become top-level.
    """
    url = SEARCH_STREAM_URL.format(
        version=API_VERSION,
        customer_id=_clean_customer_id(customer_id),
    )

    body = api_post(
        url,
        headers=headers,
        json_body={"query": query},
        label=label or "gaql",
        retries=2,
    )

    # searchStream returns a list of batches (or a single object).
    # api_post is typed as -> Dict, but searchStream returns a JSON array.
    raw = body if isinstance(body, list) else [body]

    rows: List[Dict[str, Any]] = []
    for batch in raw:
        if not isinstance(batch, dict):
            continue
        for result in batch.get("results", []):
            rows.append(_flatten(result))

    return rows


# ---------------------------------------------------------------------------
# Monetary helpers
# ---------------------------------------------------------------------------

_MICROS = 1_000_000


def _policy_preflight(
    args: argparse.Namespace,
    *,
    account_id: str,
    action_type: str,
    proposed_changes: dict[str, Any],
    rollback_reference: str | None = None,
) -> bool:
    """Run paid-media execution through the shared policy guard."""
    if not getattr(args, "execute", False):
        return True
    if not getattr(args, "approval_id", None):
        log("ERROR: --execute requires --approval-id for paid-media auditability")
        return False

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

    log("ERROR: Paid-media policy preflight failed:")
    for violation in result["violations"]:
        log(f"  - {violation}")
    return False


def _micros_to_usd(micros: Any) -> Optional[float]:
    """Convert micros string/int to USD float, or None."""
    if micros is None:
        return None
    try:
        return round(int(micros) / _MICROS, 2)
    except (ValueError, TypeError):
        return None


def _convert_micros_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    """Find all ``*_micros`` fields, add a ``*_usd`` sibling."""
    extras: Dict[str, Any] = {}
    for key, val in row.items():
        if key.endswith("_micros") or key.endswith(".amount_micros"):
            usd_key = key.replace("_micros", "_usd").replace(".amount_micros", "_usd")
            extras[usd_key] = _micros_to_usd(val)
    row.update(extras)
    return row


# ---------------------------------------------------------------------------
# GAQL queries
# ---------------------------------------------------------------------------

QUERY_CAMPAIGNS = """\
SELECT
    campaign.id, campaign.name, campaign.status,
    campaign.advertising_channel_type, campaign.bidding_strategy_type,
    campaign_budget.amount_micros,
    metrics.impressions, metrics.clicks, metrics.cost_micros,
    metrics.ctr, metrics.average_cpc, metrics.conversions,
    metrics.cost_per_conversion, metrics.all_conversions,
    metrics.video_views, metrics.video_quartile_p25_rate,
    metrics.video_quartile_p50_rate, metrics.video_quartile_p75_rate,
    metrics.video_quartile_p100_rate,
    metrics.search_impression_share,
    segments.date
FROM campaign
WHERE campaign.status != 'REMOVED'
    AND segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC"""

QUERY_AD_GROUPS = """\
SELECT
    ad_group.id, ad_group.name, ad_group.status,
    ad_group.campaign,
    metrics.impressions, metrics.clicks, metrics.cost_micros,
    metrics.ctr, metrics.average_cpc, metrics.conversions,
    metrics.cost_per_conversion,
    segments.date
FROM ad_group
WHERE ad_group.status != 'REMOVED'
    AND segments.date DURING LAST_14_DAYS
ORDER BY metrics.cost_micros DESC"""

QUERY_ADS = """\
SELECT
    ad_group_ad.ad.id, ad_group_ad.ad.name,
    ad_group_ad.ad.type, ad_group_ad.status,
    ad_group_ad.ad.responsive_search_ad.headlines,
    ad_group_ad.ad.responsive_search_ad.descriptions,
    ad_group.id, campaign.id,
    metrics.impressions, metrics.clicks, metrics.cost_micros,
    metrics.ctr, metrics.average_cpc, metrics.conversions,
    metrics.cost_per_conversion
FROM ad_group_ad
WHERE ad_group_ad.status != 'REMOVED'
    AND segments.date DURING LAST_14_DAYS"""

QUERY_SEARCH_TERMS = """\
SELECT
    search_term_view.search_term,
    search_term_view.status,
    campaign.id, campaign.name,
    ad_group.id, ad_group.name,
    metrics.impressions, metrics.clicks, metrics.cost_micros,
    metrics.ctr, metrics.conversions, metrics.cost_per_conversion
FROM search_term_view
WHERE segments.date DURING LAST_7_DAYS
ORDER BY metrics.cost_micros DESC
LIMIT 100"""

QUERY_AUDIENCES = """\
SELECT
    campaign.id, campaign.name,
    campaign_audience_view.resource_name,
    metrics.impressions, metrics.clicks, metrics.cost_micros,
    metrics.conversions
FROM campaign_audience_view
WHERE segments.date DURING LAST_14_DAYS
ORDER BY metrics.cost_micros DESC"""

QUERY_KEYWORD_QUALITY = """\
SELECT
    ad_group_criterion.keyword.text,
    ad_group_criterion.keyword.match_type,
    ad_group_criterion.quality_info.quality_score,
    ad_group_criterion.quality_info.creative_quality_score,
    ad_group_criterion.quality_info.post_click_quality_score,
    ad_group_criterion.quality_info.search_predicted_ctr,
    ad_group.id, campaign.id,
    metrics.impressions, metrics.clicks, metrics.cost_micros
FROM keyword_view
WHERE segments.date DURING LAST_14_DAYS
    AND ad_group_criterion.status != 'REMOVED'
ORDER BY metrics.impressions DESC
LIMIT 200"""


# ---------------------------------------------------------------------------
# Data shaping — campaigns with daily insights
# ---------------------------------------------------------------------------


def _shape_campaigns(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group campaign rows by campaign ID, nest daily insights."""
    by_campaign: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        cid = row.get("campaign.id", "")
        if cid not in by_campaign:
            budget_micros = row.get("campaignBudget.amount_micros") or row.get(
                "campaign_budget.amount_micros"
            )
            by_campaign[cid] = {
                "id": cid,
                "name": row.get("campaign.name", ""),
                "status": row.get("campaign.status", ""),
                "channel_type": row.get("campaign.advertising_channel_type", ""),
                "bidding_strategy": row.get("campaign.bidding_strategy_type", ""),
                "budget_daily_usd": _micros_to_usd(budget_micros),
                "insights_daily": [],
            }

        day = {
            "date": row.get("segments.date", ""),
            "impressions": _int(row.get("metrics.impressions")),
            "clicks": _int(row.get("metrics.clicks")),
            "spend_micros": _int(row.get("metrics.cost_micros")),
            "spend_usd": _micros_to_usd(row.get("metrics.cost_micros")),
            "ctr": _float(row.get("metrics.ctr")),
            "avg_cpc_micros": _int(row.get("metrics.average_cpc")),
            "avg_cpc_usd": _micros_to_usd(row.get("metrics.average_cpc")),
            "conversions": _float(row.get("metrics.conversions")),
            "cost_per_conversion_micros": _int(row.get("metrics.cost_per_conversion")),
            "cost_per_conversion_usd": _micros_to_usd(row.get("metrics.cost_per_conversion")),
            "all_conversions": _float(row.get("metrics.all_conversions")),
            "video_views": _int(row.get("metrics.video_views")),
            "video_p25_rate": _float(row.get("metrics.video_quartile_p25_rate")),
            "video_p50_rate": _float(row.get("metrics.video_quartile_p50_rate")),
            "video_p75_rate": _float(row.get("metrics.video_quartile_p75_rate")),
            "video_p100_rate": _float(row.get("metrics.video_quartile_p100_rate")),
            "search_impression_share": _float(row.get("metrics.search_impression_share")),
        }
        by_campaign[cid]["insights_daily"].append(day)

    # Sort daily insights by date and compute 14-day rollup
    for camp in by_campaign.values():
        camp["insights_daily"].sort(key=lambda d: d["date"])
        camp["insights_14d"] = _rollup(camp["insights_daily"][-14:])

    return list(by_campaign.values())


def _shape_ad_groups(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group ad group rows by ad_group.id with daily breakdown."""
    by_ag: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        agid = row.get("ad_group.id", "")
        if agid not in by_ag:
            # campaign ref can come as resource name or nested id
            campaign_ref = row.get("ad_group.campaign", "")
            campaign_id = campaign_ref.rsplit("/", 1)[-1] if "/" in str(campaign_ref) else campaign_ref
            by_ag[agid] = {
                "id": agid,
                "name": row.get("ad_group.name", ""),
                "status": row.get("ad_group.status", ""),
                "campaign_id": campaign_id,
                "insights_daily": [],
            }

        day = {
            "date": row.get("segments.date", ""),
            "impressions": _int(row.get("metrics.impressions")),
            "clicks": _int(row.get("metrics.clicks")),
            "spend_micros": _int(row.get("metrics.cost_micros")),
            "spend_usd": _micros_to_usd(row.get("metrics.cost_micros")),
            "ctr": _float(row.get("metrics.ctr")),
            "avg_cpc_usd": _micros_to_usd(row.get("metrics.average_cpc")),
            "conversions": _float(row.get("metrics.conversions")),
            "cost_per_conversion_usd": _micros_to_usd(row.get("metrics.cost_per_conversion")),
        }
        by_ag[agid]["insights_daily"].append(day)

    for ag in by_ag.values():
        ag["insights_daily"].sort(key=lambda d: d["date"])
        ag["insights_14d"] = _rollup(ag["insights_daily"])

    return list(by_ag.values())


def _shape_ads(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate ad-level rows (14-day aggregate, no daily breakdown)."""
    by_ad: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        aid = row.get("ad_group_ad.ad.id", "")
        if aid not in by_ad:
            by_ad[aid] = {
                "id": aid,
                "name": row.get("ad_group_ad.ad.name", ""),
                "type": row.get("ad_group_ad.ad.type", ""),
                "status": row.get("ad_group_ad.status", ""),
                "rsa_headlines": row.get(
                    "ad_group_ad.ad.responsive_search_ad.headlines", []
                ),
                "rsa_descriptions": row.get(
                    "ad_group_ad.ad.responsive_search_ad.descriptions", []
                ),
                "ad_group_id": row.get("ad_group.id", ""),
                "campaign_id": row.get("campaign.id", ""),
                "_rows": [],
            }
        by_ad[aid]["_rows"].append(row)

    results = []
    for ad in by_ad.values():
        ad_rows = ad.pop("_rows")
        days = [
            {
                "impressions": _int(r.get("metrics.impressions")),
                "clicks": _int(r.get("metrics.clicks")),
                "spend_micros": _int(r.get("metrics.cost_micros")),
                "spend_usd": _micros_to_usd(r.get("metrics.cost_micros")),
                "conversions": _float(r.get("metrics.conversions")),
            }
            for r in ad_rows
        ]
        ad["insights_14d"] = _rollup(days)
        results.append(ad)

    return results


def _shape_search_terms(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean search term rows into a flat list."""
    out = []
    for row in rows:
        out.append(
            {
                "search_term": row.get("search_term_view.search_term", ""),
                "status": row.get("search_term_view.status", ""),
                "campaign_id": row.get("campaign.id", ""),
                "campaign_name": row.get("campaign.name", ""),
                "ad_group_id": row.get("ad_group.id", ""),
                "ad_group_name": row.get("ad_group.name", ""),
                "impressions": _int(row.get("metrics.impressions")),
                "clicks": _int(row.get("metrics.clicks")),
                "spend_micros": _int(row.get("metrics.cost_micros")),
                "spend_usd": _micros_to_usd(row.get("metrics.cost_micros")),
                "ctr": _float(row.get("metrics.ctr")),
                "conversions": _float(row.get("metrics.conversions")),
                "cost_per_conversion_usd": _micros_to_usd(
                    row.get("metrics.cost_per_conversion")
                ),
            }
        )
    return out


def _shape_audiences(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean audience segment rows."""
    out = []
    for row in rows:
        out.append(
            {
                "campaign_id": row.get("campaign.id", ""),
                "campaign_name": row.get("campaign.name", ""),
                "resource_name": row.get(
                    "campaign_audience_view.resource_name", ""
                ),
                "impressions": _int(row.get("metrics.impressions")),
                "clicks": _int(row.get("metrics.clicks")),
                "spend_micros": _int(row.get("metrics.cost_micros")),
                "spend_usd": _micros_to_usd(row.get("metrics.cost_micros")),
                "conversions": _float(row.get("metrics.conversions")),
            }
        )
    return out


def _shape_keyword_quality(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean keyword quality score rows."""
    out = []
    for row in rows:
        out.append(
            {
                "keyword": row.get("ad_group_criterion.keyword.text", ""),
                "match_type": row.get("ad_group_criterion.keyword.match_type", ""),
                "quality_score": _int(
                    row.get("ad_group_criterion.quality_info.quality_score")
                ),
                "creative_quality": row.get(
                    "ad_group_criterion.quality_info.creative_quality_score", ""
                ),
                "post_click_quality": row.get(
                    "ad_group_criterion.quality_info.post_click_quality_score", ""
                ),
                "predicted_ctr": row.get(
                    "ad_group_criterion.quality_info.search_predicted_ctr", ""
                ),
                "ad_group_id": row.get("ad_group.id", ""),
                "campaign_id": row.get("campaign.id", ""),
                "impressions": _int(row.get("metrics.impressions")),
                "clicks": _int(row.get("metrics.clicks")),
                "spend_micros": _int(row.get("metrics.cost_micros")),
                "spend_usd": _micros_to_usd(row.get("metrics.cost_micros")),
            }
        )
    return out


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------


def _int(val: Any) -> int:
    """Coerce to int, default 0."""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _float(val: Any) -> float:
    """Coerce to float, default 0.0."""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _rollup(day_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sum impressions/clicks/spend across a list of daily dicts."""
    total_impressions = sum(d.get("impressions", 0) for d in day_rows)
    total_clicks = sum(d.get("clicks", 0) for d in day_rows)
    total_spend_micros = sum(d.get("spend_micros", 0) for d in day_rows)
    total_conversions = sum(d.get("conversions", 0) for d in day_rows)

    spend_usd = round(total_spend_micros / _MICROS, 2) if total_spend_micros else 0.0
    ctr = round(total_clicks / total_impressions, 4) if total_impressions else 0.0
    cpc_usd = round(spend_usd / total_clicks, 2) if total_clicks else 0.0
    cost_per_conv_usd = round(spend_usd / total_conversions, 2) if total_conversions else 0.0

    return {
        "impressions": total_impressions,
        "clicks": total_clicks,
        "spend_micros": total_spend_micros,
        "spend_usd": spend_usd,
        "ctr": ctr,
        "avg_cpc_usd": cpc_usd,
        "conversions": total_conversions,
        "cost_per_conversion_usd": cost_per_conv_usd,
    }


# ---------------------------------------------------------------------------
# Credential check
# ---------------------------------------------------------------------------


def check_credentials() -> Optional[str]:
    """Return an error message if credentials are missing, else None."""
    missing = [k for k in REQUIRED_CREDS if not env(k)]
    if missing:
        lines = [
            "Google Ads credentials missing. Set the following env vars",
            "(in .env.local, .env, or your shell environment):\n",
        ]
        for k in missing:
            hint = {
                "GOOGLE_CREDENTIALS_PATH": "Path to service account JSON file",
                "GOOGLE_ADS_CUSTOMER_ID": "Google Ads customer ID (XXX-XXX-XXXX)",
                "GOOGLE_ADS_DEVELOPER_TOKEN": "Google Ads API developer token",
            }.get(k, "")
            lines.append(f"  {k}  — {hint}")
        lines.append(
            "\nOptional: GOOGLE_ADS_LOGIN_CUSTOMER_ID (MCC manager account ID)"
        )
        return "\n".join(lines)
    return None


# ---------------------------------------------------------------------------
# Pull orchestrator
# ---------------------------------------------------------------------------


def pull(date: Optional[str] = None) -> int:
    """Pull all Google Ads data. Returns exit code (0 success, 1 failure)."""
    date = date or today_str()

    # -- Credential check --
    cred_error = check_credentials()
    if cred_error:
        log(f"ERROR: {cred_error}")
        return 1

    customer_id = env("GOOGLE_ADS_CUSTOMER_ID")
    developer_token = env("GOOGLE_ADS_DEVELOPER_TOKEN")
    login_customer_id = env("GOOGLE_ADS_LOGIN_CUSTOMER_ID")

    log_section("Google Ads Pull")
    log(f"  Customer ID : {customer_id}")
    log(f"  Date        : {date}")
    if login_customer_id:
        log(f"  Manager ID  : {login_customer_id}")

    # -- Authenticate --
    log("\n  Authenticating...")
    try:
        token = get_google_token()
    except FileNotFoundError as e:
        log(f"ERROR: {e}")
        return 1
    except ImportError as e:
        log(f"ERROR: {e}")
        return 1
    except Exception as e:
        log(f"ERROR: Authentication failed: {e}")
        return 1
    log("  Token acquired.")

    # -- Build headers --
    headers = {
        "Authorization": f"Bearer {token}",
        "developer-token": developer_token,
        "Content-Type": "application/json",
    }
    if login_customer_id:
        headers["login-customer-id"] = _clean_customer_id(login_customer_id)

    # -- Run queries --
    queries = [
        ("campaigns", QUERY_CAMPAIGNS, _shape_campaigns),
        ("ad_groups", QUERY_AD_GROUPS, _shape_ad_groups),
        ("ads", QUERY_ADS, _shape_ads),
        ("search_terms", QUERY_SEARCH_TERMS, _shape_search_terms),
        ("audience_segments", QUERY_AUDIENCES, _shape_audiences),
        ("keyword_quality", QUERY_KEYWORD_QUALITY, _shape_keyword_quality),
    ]

    output: Dict[str, Any] = {"customer_id": customer_id}
    errors: List[str] = []

    for name, query, shaper in queries:
        log(f"\n  Fetching {name}...")
        try:
            raw_rows = run_gaql(customer_id, query, headers, label=name)
            # Convert micros fields in each raw row
            raw_rows = [_convert_micros_fields(r) for r in raw_rows]
            shaped = shaper(raw_rows)
            output[name] = shaped
            log(f"  {name}: {len(shaped)} records")
        except APIError as e:
            msg = f"{name}: {e}"
            log(f"  WARNING: {msg}")
            errors.append(msg)
            output[name] = []
        except Exception as e:
            msg = f"{name}: {e}"
            log(f"  WARNING: {msg}")
            errors.append(msg)
            output[name] = []

    if errors:
        output["_errors"] = errors

    # -- Write output --
    out_path = write_pull("google", output, date=date)
    log(f"\n  Written to: {out_path}")

    # Print path to stdout (machine-readable)
    print(str(out_path))

    if errors:
        log(f"\n  Completed with {len(errors)} warning(s).")
    else:
        log("\n  Done — all queries succeeded.")

    return 0


# ---------------------------------------------------------------------------
# Mutation helpers
# ---------------------------------------------------------------------------


def _get_mutate_headers() -> Dict[str, str]:
    """Build HTTP headers for Google Ads mutate requests."""
    token = get_google_token()
    developer_token = env("GOOGLE_ADS_DEVELOPER_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "developer-token": developer_token,
        "Content-Type": "application/json",
    }
    login_customer_id = env("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if login_customer_id:
        headers["login-customer-id"] = _clean_customer_id(login_customer_id)
    return headers


def _log_mutation(
    action: str,
    entity_id: str,
    payload: Dict[str, Any],
    response: Dict[str, Any],
) -> None:
    """Append a mutation record to workspace/ads/mutations/YYYY-MM-DD.jsonl."""
    MUTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = MUTATIONS_DIR / f"{date_str}.jsonl"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "google",
        "action": action,
        "entity_id": entity_id,
        "payload": payload,
        "response": response,
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")

    log(f"  Mutation logged to: {log_path}")


def _execute_mutate(
    clean_cid: str,
    payload: Dict[str, Any],
    label: str,
) -> Dict[str, Any]:
    """Send a mutate request to the Google Ads API."""
    url = MUTATE_URL.format(version=API_VERSION, customer_id=clean_cid)
    headers = _get_mutate_headers()
    resp = api_post(
        url,
        headers=headers,
        json_body=payload,
        label=label,
    )
    return resp


# ---------------------------------------------------------------------------
# Mutation commands
# ---------------------------------------------------------------------------


def _build_status_payload(
    clean_cid: str,
    resource_type: str,
    entity_id: str,
    status: str,
) -> tuple:
    """Build the mutate payload for a status change (pause/activate).

    Returns (operation_key, resource_name, payload).
    """
    if resource_type == "campaign":
        resource_name = f"customers/{clean_cid}/campaigns/{entity_id}"
        operation_key = "campaignOperation"
    elif resource_type == "ad_group":
        resource_name = f"customers/{clean_cid}/adGroups/{entity_id}"
        operation_key = "adGroupOperation"
    elif resource_type == "ad":
        # Ads need ad_group context — accept "ad_group_id/ad_id" format
        resource_name = f"customers/{clean_cid}/adGroupAds/{entity_id}"
        operation_key = "adGroupAdOperation"
    else:
        raise ValueError(f"Unknown resource type: {resource_type}")

    payload = {
        "mutateOperations": [
            {
                operation_key: {
                    "update": {
                        "resourceName": resource_name,
                        "status": status,
                    },
                    "updateMask": "status",
                }
            }
        ]
    }

    return operation_key, resource_name, payload


def cmd_pause(args: argparse.Namespace) -> int:
    """Pause a campaign, ad group, or ad."""
    if args.execute and not args.approval_id:
        log("ERROR: --execute requires --approval-id for paid-media auditability")
        return 1

    cred_error = check_credentials()
    if cred_error:
        log(f"ERROR: {cred_error}")
        return 1

    customer_id = env("GOOGLE_ADS_CUSTOMER_ID")
    clean_cid = _clean_customer_id(customer_id)
    resource_type = args.type
    entity_id = args.id

    _, resource_name, payload = _build_status_payload(
        clean_cid, resource_type, entity_id, "PAUSED"
    )
    policy_entity = "adset" if resource_type == "ad_group" else resource_type
    if not _policy_preflight(
        args,
        account_id=clean_cid,
        action_type=f"pause_{policy_entity}",
        proposed_changes={
            "campaign_id": entity_id if resource_type == "campaign" else None,
            "change_diff": {"status": {"before": "ENABLED", "after": "PAUSED"}},
            "target_status": "PAUSED",
        },
        rollback_reference=args.rollback_reference,
    ):
        return 1

    url = MUTATE_URL.format(version=API_VERSION, customer_id=clean_cid)

    if not args.execute:
        log_section("Google Ads — Pause (DRY RUN)")
        log(f"  POST {url}")
        log(f"  Resource: {resource_name}")
        log(f"  Operation:\n{json.dumps(payload, indent=2)}")
        log("\n  Add --execute to apply this change.")
        return 0

    log_section("Google Ads — Pause")
    log(f"  Pausing {resource_type}: {entity_id}")

    try:
        resp = _execute_mutate(clean_cid, payload, label=f"pause/{resource_type}/{entity_id}")
    except APIError as e:
        log(f"ERROR: {e}")
        return 1

    _log_mutation("pause", entity_id, {**payload, "approval_id": args.approval_id}, resp)
    log(f"  Paused {resource_type}: {entity_id}")
    print(json.dumps(resp, indent=2))
    return 0


def cmd_activate(args: argparse.Namespace) -> int:
    """Activate (enable) a campaign, ad group, or ad."""
    if args.execute and not args.approval_id:
        log("ERROR: --execute requires --approval-id for paid-media auditability")
        return 1

    cred_error = check_credentials()
    if cred_error:
        log(f"ERROR: {cred_error}")
        return 1

    customer_id = env("GOOGLE_ADS_CUSTOMER_ID")
    clean_cid = _clean_customer_id(customer_id)
    resource_type = args.type
    entity_id = args.id

    _, resource_name, payload = _build_status_payload(
        clean_cid, resource_type, entity_id, "ENABLED"
    )
    policy_entity = "adset" if resource_type == "ad_group" else resource_type
    if not _policy_preflight(
        args,
        account_id=clean_cid,
        action_type=f"activate_{policy_entity}",
        proposed_changes={
            "campaign_id": entity_id if resource_type == "campaign" else None,
            "change_diff": {"status": {"before": "PAUSED", "after": "ENABLED"}},
            "target_status": "ENABLED",
        },
        rollback_reference=args.rollback_reference,
    ):
        return 1

    url = MUTATE_URL.format(version=API_VERSION, customer_id=clean_cid)

    if not args.execute:
        log_section("Google Ads — Activate (DRY RUN)")
        log(f"  POST {url}")
        log(f"  Resource: {resource_name}")
        log(f"  Operation:\n{json.dumps(payload, indent=2)}")
        log("\n  Add --execute to apply this change.")
        return 0

    log_section("Google Ads — Activate")
    log(f"  Activating {resource_type}: {entity_id}")

    try:
        resp = _execute_mutate(clean_cid, payload, label=f"activate/{resource_type}/{entity_id}")
    except APIError as e:
        log(f"ERROR: {e}")
        return 1

    _log_mutation("activate", entity_id, {**payload, "approval_id": args.approval_id}, resp)
    log(f"  Activated {resource_type}: {entity_id}")
    print(json.dumps(resp, indent=2))
    return 0


def cmd_budget(args: argparse.Namespace) -> int:
    """Change a campaign's daily budget."""
    if args.execute and not args.approval_id:
        log("ERROR: --execute requires --approval-id for paid-media auditability")
        return 1

    cred_error = check_credentials()
    if cred_error:
        log(f"ERROR: {cred_error}")
        return 1

    customer_id = env("GOOGLE_ADS_CUSTOMER_ID")
    clean_cid = _clean_customer_id(customer_id)
    campaign_id = args.campaign_id
    amount_usd = float(args.amount)
    amount_micros = int(amount_usd * _MICROS)

    # First, query for the campaign's budget resource name
    budget_query = f"""
    SELECT campaign_budget.resource_name, campaign_budget.amount_micros
    FROM campaign_budget
    WHERE campaign.id = {campaign_id}
    LIMIT 1
    """

    if not args.execute:
        log_section("Google Ads — Budget Change (DRY RUN)")
        log(f"  Campaign ID : {campaign_id}")
        log(f"  New amount  : ${amount_usd:.2f}/day ({amount_micros} micros)")
        log(f"\n  Step 1: Query campaign_budget resource name:")
        log(f"    {budget_query.strip()}")
        log(f"\n  Step 2: Mutate campaign_budget.amount_micros = {amount_micros}")
        log(f"\n  POST {MUTATE_URL.format(version=API_VERSION, customer_id=clean_cid)}")
        log("\n  Add --execute to apply this change.")
        return 0

    log_section("Google Ads — Budget Change")
    log(f"  Campaign ID : {campaign_id}")
    log(f"  New amount  : ${amount_usd:.2f}/day ({amount_micros} micros)")

    # Authenticate and build read headers
    try:
        token = get_google_token()
    except Exception as e:
        log(f"ERROR: Authentication failed: {e}")
        return 1

    developer_token = env("GOOGLE_ADS_DEVELOPER_TOKEN")
    read_headers = {
        "Authorization": f"Bearer {token}",
        "developer-token": developer_token,
        "Content-Type": "application/json",
    }
    login_customer_id = env("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if login_customer_id:
        read_headers["login-customer-id"] = _clean_customer_id(login_customer_id)

    # Query for the budget resource name
    log("\n  Looking up budget resource...")
    try:
        budget_rows = run_gaql(customer_id, budget_query, read_headers, label="budget_lookup")
    except APIError as e:
        log(f"ERROR: Failed to look up budget: {e}")
        return 1

    if not budget_rows:
        log(f"ERROR: No budget found for campaign {campaign_id}")
        return 1

    budget_resource = budget_rows[0].get("campaign_budget.resource_name", "")
    old_micros = budget_rows[0].get("campaign_budget.amount_micros")
    old_usd = _micros_to_usd(old_micros)

    if not budget_resource:
        log(f"ERROR: Budget resource name not found in response: {budget_rows[0]}")
        return 1

    log(f"  Budget resource: {budget_resource}")
    log(f"  Current amount : ${old_usd}/day ({old_micros} micros)")
    if not _policy_preflight(
        args,
        account_id=clean_cid,
        action_type="adjust_budget",
        proposed_changes={
            "campaign_id": campaign_id,
            "direction": "increase" if amount_usd > old_usd else "reduce",
            "current_daily_budget": old_usd,
            "new_daily_budget": amount_usd,
            "change_diff": {"daily_budget": {"before": old_usd, "after": amount_usd}},
        },
    ):
        return 1

    # Build the mutate payload
    payload = {
        "mutateOperations": [
            {
                "campaignBudgetOperation": {
                    "update": {
                        "resourceName": budget_resource,
                        "amountMicros": str(amount_micros),
                    },
                    "updateMask": "amount_micros",
                }
            }
        ]
    }

    try:
        resp = _execute_mutate(clean_cid, payload, label=f"budget/{campaign_id}")
    except APIError as e:
        log(f"ERROR: {e}")
        return 1

    _log_mutation("budget", campaign_id, {**payload, "approval_id": args.approval_id}, resp)
    log(f"  Budget updated: ${old_usd} -> ${amount_usd:.2f}/day")
    print(json.dumps(resp, indent=2))
    return 0


def cmd_add_negative(args: argparse.Namespace) -> int:
    """Add a negative keyword to a campaign."""
    if args.execute and not args.approval_id:
        log("ERROR: --execute requires --approval-id for paid-media auditability")
        return 1

    cred_error = check_credentials()
    if cred_error:
        log(f"ERROR: {cred_error}")
        return 1

    customer_id = env("GOOGLE_ADS_CUSTOMER_ID")
    clean_cid = _clean_customer_id(customer_id)
    campaign_id = args.campaign_id
    keyword = args.keyword
    match_type = (args.match_type or "BROAD").upper()

    if match_type not in ("BROAD", "PHRASE", "EXACT"):
        log(f"ERROR: Invalid match type '{match_type}'. Must be BROAD, PHRASE, or EXACT.")
        return 1

    payload = {
        "mutateOperations": [
            {
                "campaignCriterionOperation": {
                    "create": {
                        "campaign": f"customers/{clean_cid}/campaigns/{campaign_id}",
                        "negative": True,
                        "keyword": {
                            "text": keyword,
                            "matchType": match_type,
                        },
                    }
                }
            }
        ]
    }

    url = MUTATE_URL.format(version=API_VERSION, customer_id=clean_cid)
    if not _policy_preflight(
        args,
        account_id=clean_cid,
        action_type="add_keyword",
        proposed_changes={
            "campaign_id": campaign_id,
            "keyword": keyword,
            "negative": True,
            "change_diff": {"negative_keyword": {"before": None, "after": keyword}},
        },
    ):
        return 1

    if not args.execute:
        log_section("Google Ads — Add Negative Keyword (DRY RUN)")
        log(f"  Campaign ID : {campaign_id}")
        log(f"  Keyword     : \"{keyword}\"")
        log(f"  Match type  : {match_type}")
        log(f"\n  POST {url}")
        log(f"  Operation:\n{json.dumps(payload, indent=2)}")
        log("\n  Add --execute to apply this change.")
        return 0

    log_section("Google Ads — Add Negative Keyword")
    log(f"  Campaign ID : {campaign_id}")
    log(f"  Keyword     : \"{keyword}\"")
    log(f"  Match type  : {match_type}")

    try:
        resp = _execute_mutate(clean_cid, payload, label=f"add-negative/{campaign_id}/{keyword}")
    except APIError as e:
        log(f"ERROR: {e}")
        return 1

    _log_mutation("add-negative", campaign_id, {**payload, "approval_id": args.approval_id}, resp)
    log(f"  Negative keyword added: \"{keyword}\" ({match_type})")
    print(json.dumps(resp, indent=2))
    return 0


# ---------------------------------------------------------------------------
# CLI — argparse with subcommands
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Google Ads CLI — pull performance data and execute mutations.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ---- pull ----
    pull_parser = subparsers.add_parser(
        "pull",
        help="Fetch campaign, ad group, ad, search term, audience, and keyword quality data.",
    )
    pull_parser.add_argument(
        "--date",
        default=None,
        help="Pull date label (YYYY-MM-DD). Defaults to today UTC.",
    )

    # ---- pause ----
    pause_parser = subparsers.add_parser(
        "pause",
        help="Pause a campaign, ad group, or ad.",
    )
    pause_parser.add_argument(
        "--type",
        required=True,
        choices=["campaign", "ad_group", "ad"],
        help="Entity type to pause.",
    )
    pause_parser.add_argument(
        "--id",
        required=True,
        help="Resource ID (or ad_group_id/ad_id for ads).",
    )
    pause_parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually execute the mutation (default: dry-run).",
    )
    pause_parser.add_argument(
        "--approval-id",
        default=None,
        help="Required with --execute. Links the write to a human-approved action.",
    )
    pause_parser.add_argument(
        "--rollback-reference",
        default=None,
        help="Required with --execute for pause actions. Command/runbook to reverse the change.",
    )

    # ---- activate ----
    activate_parser = subparsers.add_parser(
        "activate",
        help="Activate (enable) a campaign, ad group, or ad.",
    )
    activate_parser.add_argument(
        "--type",
        required=True,
        choices=["campaign", "ad_group", "ad"],
        help="Entity type to activate.",
    )
    activate_parser.add_argument(
        "--id",
        required=True,
        help="Resource ID (or ad_group_id/ad_id for ads).",
    )
    activate_parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually execute the mutation (default: dry-run).",
    )
    activate_parser.add_argument(
        "--approval-id",
        default=None,
        help="Required with --execute. Links the write to a human-approved action.",
    )
    activate_parser.add_argument(
        "--rollback-reference",
        default=None,
        help="Required with --execute for activation. Command/runbook to reverse the change.",
    )

    # ---- budget ----
    budget_parser = subparsers.add_parser(
        "budget",
        help="Change a campaign's daily budget.",
    )
    budget_parser.add_argument(
        "--campaign-id",
        required=True,
        dest="campaign_id",
        help="Campaign ID whose budget to change.",
    )
    budget_parser.add_argument(
        "--amount",
        required=True,
        help="New daily budget in USD (e.g. 50.00).",
    )
    budget_parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually execute the mutation (default: dry-run).",
    )
    budget_parser.add_argument(
        "--approval-id",
        default=None,
        help="Required with --execute. Links the write to a human-approved action.",
    )

    # ---- add-negative ----
    neg_parser = subparsers.add_parser(
        "add-negative",
        help="Add a negative keyword to a campaign.",
    )
    neg_parser.add_argument(
        "--campaign-id",
        required=True,
        dest="campaign_id",
        help="Campaign ID to add the negative keyword to.",
    )
    neg_parser.add_argument(
        "--keyword",
        required=True,
        help="Negative keyword text.",
    )
    neg_parser.add_argument(
        "--match-type",
        default="BROAD",
        dest="match_type",
        choices=["BROAD", "PHRASE", "EXACT"],
        help="Keyword match type (default: BROAD).",
    )
    neg_parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually execute the mutation (default: dry-run).",
    )
    neg_parser.add_argument(
        "--approval-id",
        default=None,
        help="Required with --execute. Links the write to a human-approved action.",
    )

    # ---- Parse and dispatch ----
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "pull":
        sys.exit(pull(date=args.date))
    elif args.command == "pause":
        sys.exit(cmd_pause(args))
    elif args.command == "activate":
        sys.exit(cmd_activate(args))
    elif args.command == "budget":
        sys.exit(cmd_budget(args))
    elif args.command == "add-negative":
        sys.exit(cmd_add_negative(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
