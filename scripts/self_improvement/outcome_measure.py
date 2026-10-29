#!/usr/bin/env python3
"""Outcome verdict runner — reads due ECO outcome tickets and verifies them.

For each ticket whose verdict window has closed, reads equal-length windows
before and after ship from the ticket's source (GSC, GA4, ads), appends the
read, and has the ECO store compute the verdict as ``kai-measure:<source>``:
worked / partial / didn't work / inconclusive. The actor that shipped the work
never takes the read or issues the verdict.

Missing credentials, an unknown source, or an empty response is a data gap:
the read carries ``{"error": ...}`` and the verdict is inconclusive. A gap is
never recorded as zero (memory/lessons.md 2026-06-09).

Read k uses windows of k x the verdict window, so an underpowered first read
is re-run on more data. Pre window: the span days before the ship date. Post
window: the span days after it. The ship day itself is in neither. Days are
the source's reporting days (Pacific for GSC and GA4), so a pre window never
holds hours from after ship.

Usage:
  python -m scripts.self_improvement.outcome_measure            # read + verify due tickets
  python -m scripts.self_improvement.outcome_measure --dry-run  # show what would be read
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from scripts.quality_gates.eco_core import EcoError, EcoRecordStore, _parse_ts, report_date

Fetcher = Callable[[Dict[str, Any], date, date], Dict[str, Any]]

# eco-floors.yaml source names -> fetcher keys. The key is also the verifier
# suffix: kai-measure:gsc, kai-measure:ga4, kai-measure:ads.
SOURCE_KEYS = {
    "google_search_console": "gsc",
    "gsc": "gsc",
    "analytics_connector": "ga4",
    "ga4": "ga4",
    "ads_connector": "ads",
    "ads": "ads",
}


def windows_for(ticket: Dict[str, Any], read_no: int) -> Tuple[date, date, date, date]:
    """(pre_start, pre_end, post_start, post_end), inclusive dates."""
    shipped = _parse_ts(ticket.get("shipped_at"))
    if shipped is None:
        raise ValueError("ticket has no shipped_at")
    ship_day = report_date(shipped, ticket.get("report_tz"))
    span = int(ticket["window_days"]) * read_no
    return (
        ship_day - timedelta(days=span),
        ship_day - timedelta(days=1),
        ship_day + timedelta(days=1),
        ship_day + timedelta(days=span),
    )


def _target(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """Baseline fields win over receipt fields (the baseline declared the scope)."""
    return {**(ticket.get("receipt") or {}), **(ticket.get("baseline") or {})}


# ---------------------------------------------------------------------------
# Default fetchers — each returns {"value": n, "sample": n} or {"error": str}
# ---------------------------------------------------------------------------


def fetch_gsc(ticket: Dict[str, Any], start: date, end: date) -> Dict[str, Any]:
    """Search Console clicks/impressions for a page (scope=page) or the whole site.

    Uses the same credentials and site map as performance_check.py, but with an
    explicit date range — pull_gsc_data() reads all-time and cannot split
    before from after.
    """
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    if not creds_path or not os.path.exists(creds_path):
        return {"error": "No GSC credentials"}
    target = _target(ticket)
    from scripts.self_improvement.performance_check import SITE_URLS

    site_url = SITE_URLS.get(target.get("site"))
    if not site_url:
        return {"error": f"Unknown site: {target.get('site')}"}
    metric = ticket.get("metric") or "clicks"
    if metric not in ("clicks", "impressions"):
        return {"error": f"GSC cannot read metric {metric!r}"}
    body: Dict[str, Any] = {"startDate": start.isoformat(), "endDate": end.isoformat(), "rowLimit": 1}
    if target.get("scope", "page") == "page":
        if not target.get("url"):
            return {"error": "page-scoped ticket has no url"}
        body["dimensions"] = ["page"]
        body["dimensionFilterGroups"] = [
            {"filters": [{"dimension": "page", "operator": "equals", "expression": target["url"]}]}
        ]
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )
        service = build("searchconsole", "v1", credentials=creds)
        rows = service.searchanalytics().query(siteUrl=site_url, body=body).execute().get("rows", [])
    except Exception as e:
        return {"error": str(e)}
    value = sum(r.get(metric, 0) for r in rows)
    return {"value": value, "sample": value}


_GA4_METRICS = {"key_events": "keyEvents", "conversions": "keyEvents", "sessions": "sessions"}


def fetch_ga4(ticket: Dict[str, Any], start: date, end: date) -> Dict[str, Any]:
    """GA4 key events or sessions for sessions that landed on the ticket's page."""
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    if not creds_path or not os.path.exists(creds_path):
        return {"error": "No GA4 credentials"}
    target = _target(ticket)
    from scripts.self_improvement.performance_check import GA4_PROPERTY_IDS

    property_id = GA4_PROPERTY_IDS.get(target.get("site"))
    if not property_id:
        return {"error": f"No GA4 property ID for site: {target.get('site')}"}
    metric = _GA4_METRICS.get(ticket.get("metric") or "")
    if not metric:
        return {"error": f"GA4 cannot read metric {ticket.get('metric')!r}"}
    if not target.get("url"):
        return {"error": "ticket has no url"}
    try:
        from urllib.parse import urlparse

        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange, Dimension, Filter, FilterExpression, Metric, RunReportRequest,
        )

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        response = BetaAnalyticsDataClient().run_report(RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="landingPage")],
            metrics=[Metric(name=metric)],
            date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
            dimension_filter=FilterExpression(filter=Filter(
                field_name="landingPage",
                string_filter=Filter.StringFilter(match_type="EXACT", value=urlparse(target["url"]).path),
            )),
        ))
    except Exception as e:
        return {"error": str(e)}
    value = sum(float(r.metric_values[0].value) for r in response.rows or [])
    return {"value": value, "sample": value}


def fetch_ads(ticket: Dict[str, Any], start: date, end: date) -> Dict[str, Any]:
    """Ad-entity metrics through the brand's paid_media integration.

    A connector in sandbox mode returns simulated numbers, so it is refused.
    """
    target = _target(ticket)
    entity_id = target.get("entity_id") or target.get("campaign_id") or target.get("ad_id")
    if not entity_id:
        return {"error": "ticket receipt names no ad entity id"}
    try:
        from kai.execution.connector_factory import ConnectorFactory
        from kai.execution.credentials import CredentialStore
        from kai.runtime.integrations import IntegrationRegistry

        integrations = IntegrationRegistry().list_for_brand(ticket.get("brand_id") or "", channel="paid_media")
        provider = target.get("provider")
        integration = next((i for i in integrations if i.get("provider") == provider), None) or (
            integrations[0] if integrations else None
        )
        if integration is None:
            return {"error": f"no paid_media integration for brand {ticket.get('brand_id')!r}"}
        connector = ConnectorFactory(CredentialStore()).create(integration)
        if getattr(connector, "_is_sandbox", lambda: False)():
            return {"error": "ads connector is in sandbox mode — simulated metrics refused"}
        metrics = connector.get_metrics(
            str(entity_id), str(target.get("entity_type") or "campaign"), f"{start.isoformat()}:{end.isoformat()}"
        )
    except Exception as e:
        return {"error": str(e)}
    metric = ticket.get("metric") or "conversions"
    conversions = getattr(metrics, "conversions", None)
    if metric in ("cpa", "cpl", "cac") and not conversions:
        return {"error": f"no conversions in window — {metric} undefined"}
    value = getattr(metrics, "cpa" if metric in ("cpl", "cac") else metric, None)
    if value is None:
        return {"error": f"ads connector has no metric {metric!r}"}
    return {"value": value, "sample": conversions}


def default_fetchers() -> Dict[str, Fetcher]:
    return {"gsc": fetch_gsc, "ga4": fetch_ga4, "ads": fetch_ads}


def _safe_read(fetcher: Optional[Fetcher], source: Any, ticket: Dict[str, Any], start: date, end: date) -> Dict[str, Any]:
    if fetcher is None:
        return {"error": f"no fetcher for source {source!r}"}
    try:
        result = fetcher(ticket, start, end)
    except Exception as e:  # a fetcher crash is a data gap, not a runner crash
        return {"error": str(e)}
    if not isinstance(result, dict):
        return {"error": f"fetcher returned {type(result).__name__}"}
    if result.get("error"):
        return {"error": str(result["error"])}
    value = result.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return {"error": "fetcher returned no numeric value"}
    return {"value": value, "sample": result.get("sample")}


def measure_due(
    store: EcoRecordStore,
    *,
    fetchers: Optional[Dict[str, Fetcher]] = None,
    now: Optional[datetime] = None,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """Read and verify every due ticket. Returns one summary per ticket."""
    fetchers = default_fetchers() if fetchers is None else fetchers
    results = []
    for record in store.due_for_measurement(now):
        ticket = record["ticket"]
        source = ticket.get("source")
        key = SOURCE_KEYS.get(str(source))
        read_no = len(ticket.get("reads") or []) + 1
        pre_start, pre_end, post_start, post_end = windows_for(ticket, read_no)
        summary: Dict[str, Any] = {
            "record_id": record["record_id"],
            "subject_id": record.get("subject_id"),
            "read_no": read_no,
            "source": source,
            "pre_window": [pre_start.isoformat(), pre_end.isoformat()],
            "post_window": [post_start.isoformat(), post_end.isoformat()],
        }
        if dry_run:
            results.append({**summary, "dry_run": True})
            continue
        fetcher = fetchers.get(key) if key else None
        pre = _safe_read(fetcher, source, ticket, pre_start, pre_end)
        post = _safe_read(fetcher, source, ticket, post_start, post_end)
        verifier = f"kai-measure:{key or source}"
        try:  # one bad record (or a read another runner took) never aborts the run
            store.record_read(
                record["record_id"], verifier=verifier, pre=pre, post=post, read_no=read_no,
                pre_window=summary["pre_window"], post_window=summary["post_window"],
            )
            outcome = store.verify(record["record_id"], verifier=verifier, now=now)["computed"]["outcome"]
        except (EcoError, OSError, ValueError) as e:
            results.append({**summary, "error": str(e)})
            continue
        results.append({**summary, "verdict": outcome["verdict"], "final": outcome["final"],
                        "lift": outcome["lift"], "reason": outcome["reason"]})
    return results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Read due ECO outcome tickets and issue verdicts")
    parser.add_argument("--dry-run", action="store_true", help="List due reads without fetching or writing")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results = measure_due(EcoRecordStore(), dry_run=args.dry_run)
    if args.json:
        print(json.dumps(results, indent=2))
        return 0
    if not results:
        print("No outcome tickets due.")
        return 0
    for r in results:
        if r.get("error"):
            verdict = f"error: {r['error']}"
        else:
            verdict = "would read" if r.get("dry_run") else f"{r['verdict']}{' (final)' if r['final'] else ''}"
        print(f"  {r['subject_id']}  read {r['read_no']}  {r['pre_window']} vs {r['post_window']}  -> {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
