#!/usr/bin/env python3
"""Collect source-backed Kai data before generated work uses metrics.

The module lives under ``scripts.audit`` for backward compatibility with the
existing audit skills, but the dataset is intentionally workflow-neutral. Audit,
SEO, CRO, analytics, and planning workflows can consume ``kai-data.json`` or the
legacy ``audit-data.json`` alias. Missing integrations create data gaps instead
of guessed metrics.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from scripts.audit.data_sources import (
    AuditDataset,
    AuditMetric,
    AuditMode,
    AuditSource,
    DataGap,
    SourceTier,
    utc_now_iso,
)


USER_AGENT = "kai-data-collector/1.1 (+https://github.com/cgallic/kai-cmo-harness)"


def fetch_url(
    url: str,
    timeout: int = 20,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    basic_auth: tuple[str, str] | None = None,
) -> tuple[int, str, dict[str, str]]:
    request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
    if basic_auth:
        token = base64.b64encode(f"{basic_auth[0]}:{basic_auth[1]}".encode("utf-8")).decode("ascii")
        request_headers["Authorization"] = f"Basic {token}"
    req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return exc.code, body, dict(exc.headers or {})
    except Exception as exc:
        return -1, str(exc), {}


def fetch_json(
    url: str,
    timeout: int = 30,
    *,
    method: str = "GET",
    payload: Any | None = None,
    headers: dict[str, str] | None = None,
    basic_auth: tuple[str, str] | None = None,
) -> tuple[int, Any, str]:
    data = None
    request_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    status, body, _ = fetch_url(
        url,
        timeout=timeout,
        method=method,
        data=data,
        headers=request_headers,
        basic_auth=basic_auth,
    )
    try:
        return status, json.loads(body), body
    except json.JSONDecodeError:
        return status, {}, body


def normalize_base_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    return f"{parsed.scheme}://{parsed.netloc}"


def target_domain(url: str) -> str:
    return urllib.parse.urlparse(normalize_base_url(url)).netloc.lower().removeprefix("www.")


def redact_url(url: str, secret_params: set[str] | None = None) -> str:
    secret_params = secret_params or {"key", "token", "access_token", "api_key"}
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted = [(k, "REDACTED" if k.lower() in secret_params else v) for k, v in query]
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(redacted)))


def artifact_name(source_hint: str, suffix: str) -> str:
    parsed = urllib.parse.urlparse(source_hint)
    stem_hint = parsed.path.strip("/") or parsed.netloc or source_hint
    stem = re.sub(r"[^a-zA-Z0-9]+", "-", stem_hint).strip("-").lower()[:80] or "artifact"
    digest = hashlib.sha1(source_hint.encode("utf-8")).hexdigest()[:8]
    return f"{stem}-{digest}.{suffix}"


def save_artifact(raw_dir: Path, source_hint: str, body: Any, suffix: str) -> str:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / artifact_name(source_hint, suffix)
    if suffix == "json" and not isinstance(body, str):
        path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        path.write_text(str(body), encoding="utf-8", errors="replace")
    return str(path)


def load_artifact(path: Path) -> Any:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    return path.read_text(encoding="utf-8", errors="replace")


def copy_input_artifact(raw_dir: Path, path: Path, source_id: str) -> str:
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / f"{source_id}{path.suffix.lower() or '.txt'}"
    dest.write_bytes(path.read_bytes())
    return str(dest)


def add_gap(
    dataset: AuditDataset,
    missing_source: str,
    blocks: str,
    sales_version_handling: str,
    onboarding_version_handling: str,
    required_access: str = "",
) -> None:
    dataset.add_gap(
        DataGap(
            missing_source=missing_source,
            blocks=blocks,
            sales_version_handling=sales_version_handling,
            onboarding_version_handling=onboarding_version_handling,
            required_access=required_access,
        )
    )


def add_metric(
    dataset: AuditDataset,
    source: AuditSource,
    metric_id: str,
    label: str,
    value: Any,
    unit: str,
    *,
    confidence: str = "high",
    notes: str = "",
) -> bool:
    if value is None or value == "":
        return False
    dataset.add_metric(
        AuditMetric(
            metric_id=metric_id,
            label=label,
            value=value,
            unit=unit,
            source_id=source.source_id,
            source_tier=source.tier,
            confidence=confidence,
            notes=notes,
        )
    )
    return True


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def coalesce_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def parse_table(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(text.splitlines(), dialect=dialect))


def dataforseo_response_ok(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    status_code = int(data.get("status_code") or 0)
    return status_code == 0 or 20000 <= status_code < 30000


def dataforseo_task_ok(task: Any) -> bool:
    if not isinstance(task, dict):
        return False
    status_code = int(task.get("status_code") or 0)
    return status_code == 0 or 20000 <= status_code < 30000


def source_metric_ids(dataset: AuditDataset, source_id: str) -> set[str]:
    return {metric.metric_id for metric in dataset.metrics if metric.source_id == source_id}


def env_key(source_id: str, suffix: str) -> str:
    return f"{source_id.upper().replace('-', '_')}_{suffix}"


def parse_source_list(value: str) -> list[str]:
    return [item.strip().lower().replace("_", "-") for item in value.split(",") if item.strip()]


def text_without_scripts(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def html_attr_value(tag: str, attr: str) -> str:
    pattern = rf"\b{re.escape(attr)}\s*=\s*(['\"])(.*?)\1"
    match = re.search(pattern, tag, flags=re.IGNORECASE)
    return match.group(2).strip() if match else ""


def jsonld_blocks(html: str) -> list[Any]:
    blocks = []
    for match in re.finditer(
        r"<script\b[^>]*type\s*=\s*['\"]application/ld\+json['\"][^>]*>([\s\S]*?)</script>",
        html,
        flags=re.IGNORECASE,
    ):
        raw = match.group(1).strip()
        if not raw:
            continue
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            blocks.append({"_parse_error": True, "_raw_preview": raw[:500]})
    return blocks


def collect_schema_types(node: Any) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        value = node.get("@type")
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, list):
            found.extend(str(item) for item in value)
        for key in ("@graph", "itemListElement"):
            found.extend(collect_schema_types(node.get(key)))
        for value in node.values():
            if isinstance(value, (dict, list)):
                found.extend(collect_schema_types(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(collect_schema_types(item))
    return sorted(set(found))


def collect_public_site(dataset: AuditDataset, raw_dir: Path) -> None:
    base = normalize_base_url(dataset.target_url)
    retrieved_at = utc_now_iso()

    homepage_status, homepage_body, _ = fetch_url(base)
    homepage_artifact = save_artifact(raw_dir, base, homepage_body, "html")
    homepage_source = dataset.add_source(
        AuditSource(
            source_id="public_homepage",
            name="Homepage crawl",
            tier=SourceTier.PUBLIC_OBSERVED.value,
            access="external",
            retrieved_at=retrieved_at,
            used_for="Homepage status, visible text, metadata, canonical, and schema",
            source_url=base,
            artifact_path=homepage_artifact,
            status="ok" if homepage_status > 0 else "error",
        )
    )

    title_count = len(re.findall(r"<title\b", homepage_body, flags=re.IGNORECASE))
    meta_description_count = len(
        re.findall(r"<meta\b[^>]*name\s*=\s*['\"]description['\"]", homepage_body, flags=re.IGNORECASE)
    )
    h1_count = len(re.findall(r"<h1\b", homepage_body, flags=re.IGNORECASE))
    canonical_match = re.search(
        r"<link\b[^>]*rel\s*=\s*['\"]canonical['\"][^>]*>",
        homepage_body,
        flags=re.IGNORECASE,
    )
    canonical_url = html_attr_value(canonical_match.group(0), "href") if canonical_match else ""
    blocks = jsonld_blocks(homepage_body)
    schema_types = collect_schema_types(blocks)

    for metric_id, label, value, unit in [
        ("homepage_status_code", "Homepage HTTP status", homepage_status, "status_code"),
        (
            "homepage_visible_word_count",
            "Homepage visible word count without JavaScript",
            len(text_without_scripts(homepage_body).split()) if homepage_status == 200 else 0,
            "words",
        ),
        ("homepage_title_count", "Homepage title tag count", title_count, "tags"),
        ("homepage_meta_description_count", "Homepage meta description count", meta_description_count, "tags"),
        ("homepage_h1_count", "Homepage H1 count", h1_count, "tags"),
        ("homepage_jsonld_block_count", "Homepage JSON-LD block count", len(blocks), "blocks"),
        ("homepage_schema_types", "Homepage schema types", schema_types, "json_array"),
        ("homepage_canonical_url", "Homepage canonical URL", canonical_url, "url"),
    ]:
        add_metric(dataset, homepage_source, metric_id, label, value, unit)

    schema_artifact = save_artifact(raw_dir, f"{base}#jsonld", blocks, "json")
    dataset.add_source(
        AuditSource(
            source_id="public_homepage_jsonld",
            name="Homepage JSON-LD blocks",
            tier=SourceTier.PUBLIC_OBSERVED.value,
            access="external",
            retrieved_at=retrieved_at,
            used_for="Raw structured data extraction",
            source_url=base,
            artifact_path=schema_artifact,
            status="ok",
        )
    )

    for path, source_id, label in [
        ("/robots.txt", "public_robots", "robots.txt"),
        ("/sitemap.xml", "public_sitemap", "XML sitemap"),
    ]:
        url = urllib.parse.urljoin(base, path)
        status, body, _ = fetch_url(url)
        suffix = "xml" if path.endswith(".xml") else "txt"
        artifact = save_artifact(raw_dir, url, body, suffix)
        source = dataset.add_source(
            AuditSource(
                source_id=source_id,
                name=label,
                tier=SourceTier.PUBLIC_OBSERVED.value,
                access="external",
                retrieved_at=utc_now_iso(),
                used_for=f"{label} status and content",
                source_url=url,
                artifact_path=artifact,
                status="ok" if status == 200 else "unavailable",
            )
        )
        add_metric(dataset, source, f"{source_id}_status_code", f"{label} HTTP status", status, "status_code")
        if path.endswith(".xml") and status == 200:
            loc_count = len(re.findall(r"<loc\b", body, flags=re.IGNORECASE))
            add_metric(dataset, source, "sitemap_url_count", "Sitemap URL count", loc_count, "urls")


def collect_pagespeed(dataset: AuditDataset, raw_dir: Path, strategies: tuple[str, ...] = ("mobile", "desktop")) -> None:
    api_key = os.getenv("PAGESPEED_API_KEY", "")
    for strategy in strategies:
        params = {
            "url": normalize_base_url(dataset.target_url),
            "strategy": strategy,
            "category": "performance",
        }
        if api_key:
            params["key"] = api_key
        endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(params)
        status, body, _ = fetch_url(endpoint, timeout=45)
        if status != 200:
            add_gap(
                dataset,
                f"PageSpeed Insights ({strategy})",
                "Core Web Vitals and Lighthouse performance scoring",
                "Do not score performance for this strategy; list PageSpeed as unavailable",
                "Run PageSpeed Insights or provide Lighthouse/PageSpeed export",
                "PAGESPEED_API_KEY optional; public endpoint acceptable",
            )
            continue

        artifact = save_artifact(raw_dir, endpoint, body, "json")
        source = dataset.add_source(
            AuditSource(
                source_id=f"pagespeed_{strategy}",
                name=f"PageSpeed Insights ({strategy})",
                tier=SourceTier.PUBLIC_OBSERVED.value,
                access="external_api",
                retrieved_at=utc_now_iso(),
                used_for="Performance score, Core Web Vitals, and Lighthouse audits",
                source_url=redact_url(endpoint),
                artifact_path=artifact,
            )
        )

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            add_gap(
                dataset,
                f"PageSpeed Insights ({strategy})",
                "Core Web Vitals and Lighthouse performance scoring",
                "Do not score performance because the response was not valid JSON",
                "Provide valid Lighthouse/PageSpeed export",
                "Valid PageSpeed response",
            )
            continue
        lighthouse = data.get("lighthouseResult") if isinstance(data, dict) else {}
        if not isinstance(lighthouse, dict):
            add_gap(
                dataset,
                f"PageSpeed Insights ({strategy})",
                "Core Web Vitals and Lighthouse performance scoring",
                "PageSpeed response did not include lighthouseResult; do not score performance",
                "Provide a valid Lighthouse/PageSpeed export",
                "Valid PageSpeed lighthouseResult",
            )
            continue

        categories = lighthouse.get("categories", {})
        perf_score = categories.get("performance", {}).get("score")
        perf_value = to_float(perf_score)
        if perf_value is not None:
            add_metric(
                dataset,
                source,
                f"pagespeed_{strategy}_performance_score",
                f"PageSpeed {strategy} performance score",
                round(perf_value * 100),
                "score_0_100",
            )

        audits = lighthouse.get("audits")
        if not isinstance(audits, dict) or not audits:
            add_gap(
                dataset,
                f"PageSpeed Insights ({strategy}) Lighthouse audits",
                "LCP, INP, CLS, and raw Lighthouse audits",
                "PageSpeed response had no audits object; do not use Lighthouse metrics",
                "Provide a valid Lighthouse/PageSpeed export with audits",
                "lighthouseResult.audits",
            )
            continue

        audits_artifact = save_artifact(raw_dir, f"{endpoint}#lighthouse-audits", audits, "json")
        dataset.add_source(
            AuditSource(
                source_id=f"pagespeed_{strategy}_lighthouse_audits",
                name=f"Raw Lighthouse audits ({strategy})",
                tier=SourceTier.PUBLIC_OBSERVED.value,
                access="external_api",
                retrieved_at=utc_now_iso(),
                used_for="Raw Lighthouse audit payload",
                source_url=redact_url(endpoint),
                artifact_path=audits_artifact,
            )
        )
        add_metric(
            dataset,
            source,
            f"pagespeed_{strategy}_lighthouse_audit_count",
            f"Lighthouse audit count ({strategy})",
            len(audits),
            "audits",
        )
        lab_metric_count = 0
        for audit_id, label, unit in [
            ("largest-contentful-paint", "Largest Contentful Paint", "ms"),
            ("interaction-to-next-paint", "Interaction to Next Paint", "ms"),
            ("experimental-interaction-to-next-paint", "Interaction to Next Paint", "ms"),
            ("cumulative-layout-shift", "Cumulative Layout Shift", "score"),
        ]:
            value = audits.get(audit_id, {}).get("numericValue") if isinstance(audits.get(audit_id), dict) else None
            numeric = to_float(value)
            if value is not None:
                metric_name = "inp" if "interaction-to-next-paint" in audit_id else audit_id
                if add_metric(
                    dataset,
                    source,
                    f"pagespeed_{strategy}_{metric_name}",
                    f"{label} ({strategy})",
                    round(numeric, 3) if numeric is not None else None,
                    unit,
                ):
                    lab_metric_count += 1
        if lab_metric_count == 0:
            add_gap(
                dataset,
                f"PageSpeed Insights ({strategy}) lab CWV metrics",
                "LCP, INP, and CLS",
                "PageSpeed response lacked recognizable lab CWV audit values; do not use lab CWV metrics",
                "Provide a valid Lighthouse/PageSpeed export with LCP, INP, and CLS audits",
                "lighthouseResult.audits largest-contentful-paint, interaction-to-next-paint, cumulative-layout-shift",
            )

        field_metrics = data.get("loadingExperience", {}).get("metrics", {}) if isinstance(data, dict) else {}
        if not isinstance(field_metrics, dict) or not field_metrics:
            add_gap(
                dataset,
                f"PageSpeed Insights ({strategy}) field data",
                "Field Core Web Vitals from Chrome UX Report",
                "No field CWV metrics were returned; do not claim real-user CWV performance",
                "Use PageSpeed/CrUX when field data is available",
                "loadingExperience.metrics",
            )
            continue
        for key, metric_name, label, unit, divisor in [
            ("LARGEST_CONTENTFUL_PAINT_MS", "field_lcp", "Field LCP", "ms", 1),
            ("INTERACTION_TO_NEXT_PAINT", "field_inp", "Field INP", "ms", 1),
            ("CUMULATIVE_LAYOUT_SHIFT_SCORE", "field_cls", "Field CLS", "score", 100),
        ]:
            raw_value = field_metrics.get(key, {}).get("percentile") if isinstance(field_metrics.get(key), dict) else None
            numeric = to_float(raw_value)
            add_metric(
                dataset,
                source,
                f"pagespeed_{strategy}_{metric_name}",
                f"{label} ({strategy})",
                round(numeric / divisor, 3) if numeric is not None else None,
                unit,
                notes="From PageSpeed loadingExperience.metrics percentile",
            )


def collect_places(dataset: AuditDataset, raw_dir: Path, *, location: str = "") -> None:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    if not api_key:
        add_gap(
            dataset,
            "Google Places API",
            "GBP review count, rating, business name, address, phone, category, and place URL",
            "Do not claim reviews, ratings, categories, or GBP/local facts without a Places response",
            "Connect Google Places or GBP owner data before using GBP metrics",
            "GOOGLE_PLACES_API_KEY",
        )
        return

    query = " ".join(part for part in [dataset.firm_name, location, target_domain(dataset.target_url)] if part).strip()
    params = {
        "input": query or normalize_base_url(dataset.target_url),
        "inputtype": "textquery",
        "fields": "place_id,name,formatted_address",
        "key": api_key,
    }
    find_endpoint = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?" + urllib.parse.urlencode(params)
    status, data, raw_find = fetch_json(find_endpoint)
    candidates = data.get("candidates") or []
    places_status = data.get("status") if isinstance(data, dict) else ""
    if status != 200 or (places_status and places_status != "OK") or not candidates:
        save_artifact(raw_dir, find_endpoint, raw_find, "json")
        add_gap(
            dataset,
            "Google Places API",
            "GBP public profile metrics",
            "No matching Places response; do not estimate GBP metrics",
            "Confirm Place ID or connect GBP owner data",
            "GOOGLE_PLACES_API_KEY and matching business/location query",
        )
        return

    place_id = candidates[0].get("place_id", "")
    details_params = {
        "place_id": place_id,
        "fields": "name,rating,user_ratings_total,formatted_address,formatted_phone_number,types,url,website",
        "key": api_key,
    }
    details_endpoint = "https://maps.googleapis.com/maps/api/place/details/json?" + urllib.parse.urlencode(details_params)
    status, details, raw_details = fetch_json(details_endpoint)
    combined = {"find_place": data, "details": details}
    artifact = save_artifact(raw_dir, details_endpoint, combined, "json")
    details_status = details.get("status") if isinstance(details, dict) else ""
    if status != 200 or (details_status and details_status != "OK") or "result" not in details:
        add_gap(
            dataset,
            "Google Places API",
            "GBP public profile metrics",
            "Places details response was unavailable; do not estimate GBP metrics",
            "Confirm Place ID or connect GBP owner data",
            "GOOGLE_PLACES_API_KEY and Places details access",
        )
        return

    source = dataset.add_source(
        AuditSource(
            source_id="google_places",
            name="Google Places API",
            tier=SourceTier.CONNECTED.value,
            access="api_key",
            retrieved_at=utc_now_iso(),
            used_for="GBP public business details, review count, and rating",
            source_url=redact_url(details_endpoint),
            artifact_path=artifact,
        )
    )
    result = details["result"]
    primary_category = (result.get("types") or [""])[0]
    metrics = [
        ("places_review_count", "Google Places review count", result.get("user_ratings_total"), "reviews"),
        ("places_rating", "Google Places rating", result.get("rating"), "stars"),
        ("places_business_name", "Google Places business name", result.get("name"), "text"),
        ("places_address", "Google Places address", result.get("formatted_address"), "address"),
        ("places_phone", "Google Places phone", result.get("formatted_phone_number"), "phone_number"),
        ("places_primary_category", "Google Places primary category", primary_category, "category"),
        ("places_url", "Google Places URL", result.get("url"), "url"),
    ]
    for metric_id, label, value, unit in metrics:
        add_metric(dataset, source, metric_id, label, value, unit)


def split_keywords(keywords: str) -> list[str]:
    return [kw.strip() for kw in keywords.split(",") if kw.strip()]


def collect_dataforseo_serp(dataset: AuditDataset, raw_dir: Path, *, keywords: str = "", location: str = "") -> None:
    login = os.getenv("DATAFORSEO_LOGIN", "")
    password = os.getenv("DATAFORSEO_PASSWORD", "")
    keyword_list = split_keywords(keywords)
    domain = target_domain(dataset.target_url)
    if not login or not password:
        add_gap(
            dataset,
            "DataForSEO SERP API",
            "Target keyword rankings, local pack presence, organic position, SERP features, and competitor domains",
            "Do not claim keyword ranks or local pack placement without a SERP collector response",
            "Connect DataForSEO or provide a SERP export",
            "DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD",
        )
        return
    if not keyword_list:
        add_gap(
            dataset,
            "DataForSEO SERP API keywords",
            "Target keyword rankings and SERP feature collection",
            "No keyword-specific rank claims can be made",
            "Run collector with --keywords \"kw1,kw2\"",
            "--keywords",
        )
        return

    endpoint = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    payload = [
        {
            "keyword": keyword,
            "target": domain,
            "location_name": location or "United States",
            "language_code": "en",
            "device": "desktop",
            "os": "windows",
            "depth": 100,
        }
        for keyword in keyword_list
    ]
    status, data, raw = fetch_json(endpoint, method="POST", payload=payload, basic_auth=(login, password), timeout=60)
    artifact = save_artifact(raw_dir, endpoint, data or raw, "json")
    if status != 200 or not dataforseo_response_ok(data):
        add_gap(
            dataset,
            "DataForSEO SERP API",
            "Target keyword rankings, SERP features, and competitor domains",
            "DataForSEO request failed; do not claim ranks",
            "Fix DataForSEO credentials/request or provide export",
            "Successful DataForSEO API response",
        )
        return

    source = dataset.add_source(
        AuditSource(
            source_id="dataforseo_serp",
            name="DataForSEO SERP API",
            tier=SourceTier.CONNECTED.value,
            access="api",
            retrieved_at=utc_now_iso(),
            used_for="Keyword rankings, local pack presence, SERP features, and competitors",
            source_url=endpoint,
            artifact_path=artifact,
        )
    )
    tasks = data.get("tasks", []) if isinstance(data, dict) else []
    if not tasks:
        add_gap(
            dataset,
            "DataForSEO SERP API",
            "Target keyword rankings, SERP features, and competitor domains",
            "DataForSEO response contained no tasks; do not claim ranks",
            "Provide a DataForSEO response with task results",
            "tasks[]",
        )
        return
    for task in tasks:
        if not dataforseo_task_ok(task):
            add_gap(
                dataset,
                "DataForSEO SERP API task",
                "Keyword rankings and SERP features for one requested keyword",
                "A DataForSEO task returned an error; do not use metrics from that task",
                "Fix the keyword/location request or provide a valid SERP export",
                "Task status_code 20000-29999",
            )
            continue
        task_data = (task.get("data") or {})
        keyword = task_data.get("keyword") or task.get("keyword") or "keyword"
        safe_kw = re.sub(r"[^a-z0-9]+", "_", keyword.lower()).strip("_")[:60]
        results = task.get("result") or []
        items = []
        item_types = []
        target_rankings = []
        for result in results:
            if not isinstance(result, dict):
                continue
            keyword = result.get("keyword") or keyword
            item_types.extend(result.get("item_types") or [])
            target_rankings.extend(result.get("target_rankings") or [])
            items.extend(result.get("items") or [])

        if not results or (not items and not item_types and not target_rankings):
            add_gap(
                dataset,
                f"DataForSEO SERP API results for {keyword}",
                "Keyword rankings, local pack presence, SERP features, and competitors",
                "Task had no parseable SERP results; do not claim ranks or SERP features for this keyword",
                "Provide a valid advanced SERP response with items or target_rankings",
                "tasks[].result[].items or target_rankings",
            )
            continue

        features = sorted(set([str(item_type) for item_type in item_types if item_type] + [str(item.get("type")) for item in items if item.get("type")]))
        organic_items = [item for item in items if item.get("type") == "organic"]
        local_pack_items = [item for item in items if "local" in str(item.get("type", "")).lower()]
        local_pack_present = any("local" in feature.lower() for feature in features)
        local_pack_ranks = [
            rank
            for rank in (item.get("rank_group") or item.get("rank_absolute") for item in local_pack_items)
            if rank not in (None, "")
        ]
        competitors = []
        organic_position = None
        for ranking in target_rankings:
            if isinstance(ranking, dict):
                organic_position = coalesce_present(ranking.get("rank_group"), ranking.get("rank_absolute"), organic_position)
                if organic_position is not None:
                    break
        for item in organic_items:
            item_domain = str(item.get("domain") or urllib.parse.urlparse(item.get("url", "")).netloc).lower()
            clean_domain = item_domain.removeprefix("www.")
            rank = item.get("rank_group") or item.get("rank_absolute")
            if domain in clean_domain and organic_position is None:
                organic_position = rank
            elif clean_domain and clean_domain not in competitors:
                competitors.append(clean_domain)
        add_metric(dataset, source, f"serp_{safe_kw}_organic_position", f"Organic position for {keyword}", organic_position, "rank")
        add_metric(dataset, source, f"serp_{safe_kw}_local_pack_present", f"Local pack presence for {keyword}", local_pack_present, "boolean")
        add_metric(dataset, source, f"serp_{safe_kw}_local_pack_ranks", f"Local pack ranks for {keyword}", local_pack_ranks, "ranks")
        add_metric(dataset, source, f"serp_{safe_kw}_features", f"SERP features for {keyword}", features, "json_array")
        add_metric(dataset, source, f"serp_{safe_kw}_competitor_domains", f"Competitor domains for {keyword}", competitors[:10], "domains")


def recursive_find(data: Any, keys: tuple[str, ...]) -> Any:
    normalized = {key.lower().replace(" ", "_") for key in keys}
    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower().replace(" ", "_") in normalized and value not in ("", None):
                return value
        for value in data.values():
            found = recursive_find(value, keys)
            if found not in ("", None):
                return found
    elif isinstance(data, list):
        for item in data:
            found = recursive_find(item, keys)
            if found not in ("", None):
                return found
    return None


def pick_seo_provider(requested: str) -> str:
    requested = (requested or "auto").lower()
    if requested != "auto":
        return requested
    if os.getenv("AHREFS_API_KEY"):
        return "ahrefs"
    if os.getenv("SEMRUSH_API_KEY"):
        return "semrush"
    if os.getenv("MOZ_ACCESS_TOKEN"):
        return "moz"
    if os.getenv("DATAFORSEO_LOGIN") and os.getenv("DATAFORSEO_PASSWORD"):
        return "dataforseo"
    return ""


def seo_metric_value(data: Any, keys: tuple[str, ...], provider: str) -> Any:
    provider_aliases: dict[str, dict[str, tuple[str, ...]]] = {
        "ahrefs": {
            "domain_authority": ("domain_rating", "domainRating", "dr"),
            "referring_domains": ("refdomains", "refdomains_live", "referring_domains"),
            "backlinks": ("backlinks", "backlinks_live", "external_links"),
            "organic_keywords": ("organic_keywords", "org_keywords"),
            "organic_traffic": ("organic_traffic", "org_traffic"),
            "top_pages": ("top_pages", "pages_by_traffic", "pages"),
        },
        "semrush": {
            "organic_keywords": ("Or", "organic_keywords", "organic_keywords_count"),
            "organic_traffic": ("Ot", "organic_traffic", "traffic"),
        },
        "moz": {
            "domain_authority": ("domain_authority", "domain_authority_score", "domainAuthority"),
            "referring_domains": ("root_domains_to_root_domain", "root_domains_to_page", "referring_domains"),
            "backlinks": ("external_pages_to_root_domain", "external_pages_to_page", "backlinks"),
        },
        "dataforseo": {
            "domain_authority": ("rank", "domain_rank"),
            "referring_domains": ("referring_domains", "referring_main_domains"),
            "backlinks": ("backlinks", "backlinks_count"),
        },
    }
    expanded: list[str] = list(keys)
    aliases = provider_aliases.get(provider, {})
    for key in keys:
        expanded.extend(aliases.get(key, ()))
    return recursive_find(data, tuple(expanded))


def collect_seo_provider(dataset: AuditDataset, raw_dir: Path, *, provider: str = "auto") -> None:
    export_path = os.getenv("SEO_PROVIDER_EXPORT_PATH", "")
    selected = pick_seo_provider(provider)
    data: Any = {}
    source_url = ""
    source_name = ""
    access = "api"

    if export_path:
        path = Path(export_path)
        if not path.exists():
            add_gap(dataset, "SEO platform export", "Authority, backlink, and traffic metrics", "Export path missing", "Provide valid export", "SEO_PROVIDER_EXPORT_PATH")
            return
        data = load_artifact(path)
        artifact = copy_input_artifact(raw_dir, path, "seo_provider_export")
        source_name = "SEO platform export"
        selected = selected or "export"
        access = "user_export"
        source_url = str(path)
    else:
        if not selected:
            add_gap(
                dataset,
                "Ahrefs/Semrush/Moz/DataForSEO SEO platform data",
                "Domain Rating or authority, referring domains, backlinks, organic keyword count, traffic estimate, and top pages",
                "Do not make authority, backlink, keyword, or traffic claims without an SEO platform response",
                "Connect Ahrefs, Semrush, Moz, DataForSEO, or provide an export",
                "AHREFS_API_KEY, SEMRUSH_API_KEY, MOZ_ACCESS_TOKEN, or DATAFORSEO_LOGIN/PASSWORD",
            )
            return
        domain = target_domain(dataset.target_url)
        if selected == "ahrefs":
            key = os.getenv("AHREFS_API_KEY", "")
            endpoint = "https://api.ahrefs.com/v3/site-explorer/overview?" + urllib.parse.urlencode({"target": domain, "mode": "domain"})
            status, data, raw = fetch_json(endpoint, headers={"Authorization": f"Bearer {key}"}, timeout=45)
            source_url = endpoint
            source_name = "Ahrefs Site Explorer API"
        elif selected == "semrush":
            key = os.getenv("SEMRUSH_API_KEY", "")
            params = {"type": "domain_ranks", "key": key, "export_columns": "Dn,Rk,Or,Ot,Oc,Ad,At", "domain": domain, "database": "us"}
            endpoint = "https://api.semrush.com/?" + urllib.parse.urlencode(params)
            status, raw, _headers = fetch_url(endpoint, timeout=45)
            data = parse_table(raw)
            source_url = redact_url(endpoint)
            source_name = "Semrush API"
        elif selected == "moz":
            token = os.getenv("MOZ_ACCESS_TOKEN", "")
            endpoint = "https://lsapi.seomoz.com/v2/url_metrics"
            status, data, raw = fetch_json(
                endpoint,
                method="POST",
                payload={"targets": [domain]},
                headers={"Authorization": f"Bearer {token}"},
                timeout=45,
            )
            source_url = endpoint
            source_name = "Moz URL Metrics API"
        else:
            login = os.getenv("DATAFORSEO_LOGIN", "")
            password = os.getenv("DATAFORSEO_PASSWORD", "")
            endpoint = "https://api.dataforseo.com/v3/backlinks/summary/live"
            status, data, raw = fetch_json(
                endpoint,
                method="POST",
                payload=[{"target": domain, "include_subdomains": True, "rank_scale": "one_hundred"}],
                basic_auth=(login, password),
                timeout=60,
            )
            source_url = endpoint
            source_name = "DataForSEO Backlinks API"
        artifact = save_artifact(raw_dir, source_url or selected, data or raw, "json")
        if status != 200 or (selected == "dataforseo" and not dataforseo_response_ok(data)):
            add_gap(
                dataset,
                source_name or "SEO platform API",
                "Authority, backlink, keyword, traffic, and top-page metrics",
                "SEO platform request failed; do not use SEO platform metrics",
                "Fix provider credentials/request or provide export",
                f"{selected} API access",
            )
            return

    source = dataset.add_source(
        AuditSource(
            source_id=f"seo_provider_{selected}",
            name=source_name or f"{selected} SEO provider",
            tier=SourceTier.USER_PROVIDED.value if access == "user_export" else SourceTier.CONNECTED.value,
            access=access,
            retrieved_at=utc_now_iso(),
            used_for="Authority, backlink, organic keyword, traffic estimate, and top-page metrics",
            source_url=source_url,
            artifact_path=artifact,
        )
    )
    metric_specs = [
        ("seo_domain_authority", "Domain Rating or authority equivalent", ("domain_authority", "domain_rating", "authority_score"), "score"),
        ("seo_referring_domains", "Referring domains", ("referring_domains", "refdomains", "referring_domains_count"), "domains"),
        ("seo_backlinks", "Backlinks", ("backlinks", "backlinks_count", "external_links"), "links"),
        ("seo_organic_keywords", "Organic keyword count", ("organic_keywords", "organic_keyword_count", "organic_keywords_count"), "keywords"),
        ("seo_traffic_estimate", "Organic traffic estimate", ("organic_traffic", "traffic_estimate", "organic_traffic_estimate", "traffic"), "visits"),
        ("seo_top_pages", "Top pages", ("top_pages", "pages"), "json_array"),
    ]
    added = 0
    for metric_id, label, keys, unit in metric_specs:
        if add_metric(dataset, source, metric_id, label, seo_metric_value(data, keys, selected), unit, confidence="medium"):
            added += 1
    semrush_rank = seo_metric_value(data, ("semrush_rank", "Rk"), selected)
    if semrush_rank is not None:
        if add_metric(dataset, source, "seo_semrush_rank", "Semrush Rank", semrush_rank, "rank", confidence="medium"):
            added += 1
    if added == 0:
        add_gap(
            dataset,
            source_name or f"{selected} SEO provider",
            "Authority, backlink, keyword, traffic, and top-page metrics",
            "Provider response had no recognizable canonical metrics; do not use SEO platform claims",
            "Provide an export/API response containing recognized authority, backlink, keyword, traffic, or page fields",
            "Recognized SEO provider metric fields",
        )


def default_date_range(date_from: str = "", date_to: str = "") -> tuple[str, str]:
    end = date_to or date.today().isoformat()
    start = date_from or (date.fromisoformat(end) - timedelta(days=30)).isoformat()
    return start, end


def collect_gsc(dataset: AuditDataset, raw_dir: Path, *, mode: str, date_from: str = "", date_to: str = "") -> None:
    if mode != AuditMode.ONBOARDING_CONNECTED.value:
        add_gap(dataset, "Google Search Console", "Clicks, impressions, CTR, average position, top queries, and top pages", "GSC is onboarding-only; do not use GSC metrics in external sales audits", "Run with --mode onboarding_connected after access is granted", "onboarding_connected mode")
        return
    export_path = os.getenv("GSC_EXPORT_PATH", "")
    start, end = default_date_range(date_from, date_to)
    if export_path:
        path = Path(export_path)
        if not path.exists():
            add_gap(dataset, "Google Search Console export", "GSC metrics", "Export path missing", "Provide a valid GSC export", "GSC_EXPORT_PATH")
            return
        rows = load_artifact(path)
        artifact = copy_input_artifact(raw_dir, path, "gsc_export")
        source_tier = SourceTier.USER_PROVIDED.value
        source_url = str(path)
    else:
        property_id = os.getenv("GSC_PROPERTY", "")
        service_account = os.getenv("GSC_SERVICE_ACCOUNT_FILE", "")
        if not property_id or not service_account:
            add_gap(dataset, "Google Search Console", "Clicks, impressions, CTR, average position, top queries, and top pages", "Not available in sales_external; do not estimate search performance", "Set GSC_PROPERTY and GSC_SERVICE_ACCOUNT_FILE or provide GSC_EXPORT_PATH", "GSC_PROPERTY and GSC_SERVICE_ACCOUNT_FILE")
            return
        try:
            from kai.connectors.analytics.base import ConnectorConfig
            from kai.connectors.analytics.gsc import GSCConnector
        except ImportError as exc:
            add_gap(dataset, "Google Search Console", "GSC API collection", "Connector unavailable", f"Install connector dependency: {exc}", "google-api-python-client")
            return
        connector = GSCConnector(
            ConnectorConfig(
                connector_type="gsc",
                credentials={"type": "service_account_file", "path": service_account},
                property_id=property_id,
            )
        )
        try:
            query_rows = connector._query(start, end, ["query"], row_limit=100)
            page_rows = connector._query(start, end, ["page"], row_limit=100)
        except Exception as exc:
            add_gap(dataset, "Google Search Console", "GSC API collection", "GSC request failed", f"Fix GSC credentials/access: {exc}", "Valid GSC access")
            return
        rows = {"top_queries": query_rows, "top_pages": page_rows, "date_range": {"from": start, "to": end}}
        artifact = save_artifact(raw_dir, "gsc_api", rows, "json")
        source_tier = SourceTier.CONNECTED.value
        source_url = property_id

    source = dataset.add_source(
        AuditSource(
            source_id="gsc",
            name="Google Search Console",
            tier=source_tier,
            access="connected" if source_tier == SourceTier.CONNECTED.value else "user_export",
            retrieved_at=utc_now_iso(),
            used_for="Search clicks, impressions, CTR, average position, top queries, and top pages",
            source_url=source_url,
            artifact_path=artifact,
        )
    )
    row_list = rows if isinstance(rows, list) else rows.get("top_queries", [])
    valid_rows = [
        row
        for row in row_list
        if isinstance(row, dict)
        and any(row.get(key) not in (None, "") for key in ("clicks", "impressions", "ctr", "position"))
    ]
    if not valid_rows:
        add_gap(
            dataset,
            "Google Search Console",
            "Clicks, impressions, CTR, average position, top queries, and top pages",
            "GSC response/export had no parseable metric rows; do not use search performance metrics",
            "Provide a GSC export/API response with clicks, impressions, CTR, or position",
            "GSC metric rows",
        )
        return
    clicks = sum(to_float(row.get("clicks")) or 0 for row in valid_rows)
    impressions = sum(to_float(row.get("impressions")) or 0 for row in valid_rows)
    ctr = clicks / impressions if impressions else None
    positions = [value for value in (to_float(row.get("position")) for row in valid_rows) if value is not None]
    add_metric(dataset, source, "gsc_clicks", "GSC clicks", clicks, "clicks")
    add_metric(dataset, source, "gsc_impressions", "GSC impressions", impressions, "impressions")
    add_metric(dataset, source, "gsc_ctr", "GSC CTR", ctr, "ratio")
    add_metric(dataset, source, "gsc_average_position", "GSC average position", sum(positions) / len(positions) if positions else None, "rank")
    add_metric(dataset, source, "gsc_top_queries", "GSC top queries", row_list[:25], "json_array")
    add_metric(dataset, source, "gsc_top_pages", "GSC top pages", rows.get("top_pages", [])[:25] if isinstance(rows, dict) else [], "json_array")
    add_metric(dataset, source, "gsc_date_range", "GSC date range", {"from": start, "to": end}, "date_range")


def collect_ga4(dataset: AuditDataset, raw_dir: Path, *, mode: str, date_from: str = "", date_to: str = "") -> None:
    if mode != AuditMode.ONBOARDING_CONNECTED.value:
        add_gap(dataset, "Google Analytics 4", "Sessions, users, conversions, conversion rate, landing pages, and channels", "GA4 is onboarding-only; do not estimate analytics metrics", "Run with --mode onboarding_connected after GA4 access is granted", "onboarding_connected mode")
        return
    export_path = os.getenv("GA4_EXPORT_PATH", "")
    start, end = default_date_range(date_from, date_to)
    if export_path:
        path = Path(export_path)
        if not path.exists():
            add_gap(dataset, "Google Analytics 4 export", "GA4 metrics", "Export path missing", "Provide a valid GA4 export", "GA4_EXPORT_PATH")
            return
        rows = load_artifact(path)
        artifact = copy_input_artifact(raw_dir, path, "ga4_export")
        source_tier = SourceTier.USER_PROVIDED.value
        source_url = str(path)
    else:
        property_id = os.getenv("GA4_PROPERTY_ID", "")
        service_account = os.getenv("GA4_SERVICE_ACCOUNT_FILE", "")
        if not property_id or not service_account:
            add_gap(dataset, "Google Analytics 4", "Sessions, users, conversions, conversion rate, landing pages, and channels", "Not available in sales_external; do not estimate analytics", "Set GA4_PROPERTY_ID and GA4_SERVICE_ACCOUNT_FILE or provide GA4_EXPORT_PATH", "GA4_PROPERTY_ID and GA4_SERVICE_ACCOUNT_FILE")
            return
        try:
            from kai.connectors.analytics.base import ConnectorConfig, DateRange
            from kai.connectors.analytics.ga4 import GA4Connector
        except ImportError as exc:
            add_gap(dataset, "Google Analytics 4", "GA4 API collection", "Connector unavailable", f"Install connector dependency: {exc}", "google-analytics-data")
            return
        connector = GA4Connector(
            ConnectorConfig(
                connector_type="ga4",
                credentials={"type": "service_account_file", "path": service_account},
                property_id=property_id,
            )
        )
        try:
            date_range = DateRange(start_date=start, end_date=end)
            rows = [point.model_dump() for point in connector.get_metrics(date_range, ["traffic_source"], ["sessions", "active_users", "conversions", "session_conversion_rate"])]
            rows.extend(point.model_dump() for point in connector.get_landing_page_performance(date_range))
        except Exception as exc:
            add_gap(dataset, "Google Analytics 4", "GA4 API collection", "GA4 request failed", f"Fix GA4 credentials/access: {exc}", "Valid GA4 access")
            return
        artifact = save_artifact(raw_dir, "ga4_api", {"rows": rows, "date_range": {"from": start, "to": end}}, "json")
        source_tier = SourceTier.CONNECTED.value
        source_url = property_id

    source = dataset.add_source(
        AuditSource(
            source_id="ga4",
            name="Google Analytics 4",
            tier=source_tier,
            access="connected" if source_tier == SourceTier.CONNECTED.value else "user_export",
            retrieved_at=utc_now_iso(),
            used_for="Sessions, users, conversions, conversion rate, top landing pages, and channel grouping",
            source_url=source_url,
            artifact_path=artifact,
        )
    )
    row_list = rows if isinstance(rows, list) else rows.get("rows", [])
    if not any(isinstance(row, dict) for row in row_list):
        add_gap(
            dataset,
            "Google Analytics 4",
            "Sessions, users, conversions, conversion rate, landing pages, and channels",
            "GA4 response/export had no parseable metric rows; do not use analytics metrics",
            "Provide a GA4 export/API response with sessions, users, or conversions",
            "GA4 metric rows",
        )
        return
    recognized_ga4_values = False

    def sum_metric(*names: str) -> float:
        nonlocal recognized_ga4_values
        wanted = {name.lower() for name in names}
        total = 0.0
        for row in row_list:
            if not isinstance(row, dict):
                continue
            metric_name = str(row.get("metric_name") or row.get("metric") or "").lower()
            if metric_name in wanted:
                value = to_float(row.get("value"))
                if value is not None:
                    recognized_ga4_values = True
                    total += value
            for key in wanted:
                if key in row:
                    value = to_float(row.get(key))
                    if value is not None:
                        recognized_ga4_values = True
                        total += value
        return total

    sessions = sum_metric("sessions")
    users = sum_metric("active_users", "users", "total_users")
    conversions = sum_metric("conversions")
    if not recognized_ga4_values:
        add_gap(
            dataset,
            "Google Analytics 4",
            "Sessions, users, conversions, conversion rate, landing pages, and channels",
            "GA4 rows contained no recognized metric values; do not use analytics metrics",
            "Provide GA4 rows with recognized metric names or columns",
            "sessions, active_users/users, conversions",
        )
        return
    add_metric(dataset, source, "ga4_sessions", "GA4 sessions", sessions, "sessions")
    add_metric(dataset, source, "ga4_users", "GA4 users", users, "users")
    add_metric(dataset, source, "ga4_conversions", "GA4 conversions", conversions, "conversions")
    add_metric(dataset, source, "ga4_conversion_rate", "GA4 conversion rate", conversions / sessions if sessions else None, "ratio")
    add_metric(dataset, source, "ga4_top_landing_pages", "GA4 top landing pages", row_list[:25], "json_array")
    add_metric(dataset, source, "ga4_channel_grouping", "GA4 channel grouping", row_list[:25], "json_array")
    add_metric(dataset, source, "ga4_date_range", "GA4 date range", {"from": start, "to": end}, "date_range")


def collect_calls(dataset: AuditDataset, raw_dir: Path, *, mode: str, date_from: str = "", date_to: str = "") -> None:
    if mode != AuditMode.ONBOARDING_CONNECTED.value:
        add_gap(dataset, "Call tracking / phone logs", "Total calls, missed calls, answered calls, after-hours calls, and response time", "Call metrics are onboarding-only unless a public call test is run", "Run with --mode onboarding_connected after call tracking access is granted", "onboarding_connected mode")
        return
    export_path = os.getenv("CALL_EXPORT_PATH", "")
    start, end = default_date_range(date_from, date_to)
    source_url = ""
    if export_path:
        path = Path(export_path)
        if not path.exists():
            add_gap(dataset, "Call tracking export", "Call metrics", "Export path missing", "Provide a valid call tracking export", "CALL_EXPORT_PATH")
            return
        data = load_artifact(path)
        artifact = copy_input_artifact(raw_dir, path, "call_tracking_export")
        source_tier = SourceTier.USER_PROVIDED.value
        source_url = str(path)
        source_name = "Call tracking export"
        access = "user_export"
    else:
        api_key = os.getenv("CALLRAIL_API_KEY", "")
        account_id = os.getenv("CALLRAIL_ACCOUNT_ID", "")
        if not api_key or not account_id:
            add_gap(dataset, "CallRail call tracking", "Total calls, missed calls, answered calls, after-hours calls, first response time, and source/channel", "Do not claim call volume or missed-call rates without call tracking data", "Set CALLRAIL_API_KEY and CALLRAIL_ACCOUNT_ID or provide CALL_EXPORT_PATH", "CALLRAIL_API_KEY and CALLRAIL_ACCOUNT_ID")
            return
        base = f"https://api.callrail.com/v3/a/{account_id}"
        summary_endpoint = base + "/calls/summary.json?" + urllib.parse.urlencode({"start_date": start, "end_date": end})
        calls_endpoint = base + "/calls.json?" + urllib.parse.urlencode({"start_date": start, "end_date": end, "per_page": 250})
        headers = {"Authorization": f"Token token={api_key}"}
        summary_status, summary, summary_raw = fetch_json(summary_endpoint, headers=headers, timeout=45)
        calls_status, calls, calls_raw = fetch_json(calls_endpoint, headers=headers, timeout=45)
        data = {"summary": summary if summary_status == 200 else summary_raw, "calls": calls if calls_status == 200 else calls_raw}
        artifact = save_artifact(raw_dir, "callrail_calls", data, "json")
        if summary_status != 200 and calls_status != 200:
            add_gap(dataset, "CallRail call tracking", "Call metrics", "CallRail request failed", "Fix CallRail access or provide export", "Valid CallRail API access")
            return
        source_tier = SourceTier.CONNECTED.value
        source_url = redact_url(summary_endpoint)
        source_name = "CallRail API"
        access = "api"

    source = dataset.add_source(
        AuditSource(
            source_id="call_tracking",
            name=source_name,
            tier=source_tier,
            access=access,
            retrieved_at=utc_now_iso(),
            used_for="Call volume, missed calls, answered calls, after-hours calls, first response time, and source/channel",
            source_url=source_url,
            artifact_path=artifact,
        )
    )

    calls_list = []
    summary = {}
    if isinstance(data, dict):
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else data
        calls_blob = data.get("calls") if isinstance(data.get("calls"), dict) else {}
        calls_list = calls_blob.get("calls") if isinstance(calls_blob, dict) else []
    elif isinstance(data, list):
        calls_list = data
    calls_list = calls_list or []
    valid_call_rows = [call for call in calls_list if isinstance(call, dict)]
    if not isinstance(summary, dict):
        summary = {}
    if not summary and not valid_call_rows:
        add_gap(
            dataset,
            "Call tracking / phone logs",
            "Total calls, missed calls, answered calls, after-hours calls, and response time",
            "Call tracking response/export had no parseable summary or call rows; do not use call metrics",
            "Provide call tracking summary data or call rows",
            "Call summary or calls[] rows",
        )
        return

    total_calls = coalesce_present(recursive_find(summary, ("total_calls", "total", "calls")), len(valid_call_rows) if valid_call_rows else None)
    missed_calls = coalesce_present(
        recursive_find(summary, ("missed_calls", "missed")),
        sum(
            1
            for call in valid_call_rows
            if str(call.get("answered", "")).lower() == "false"
            or str(call.get("status", "")).lower() in {"missed", "voicemail", "abandoned"}
        )
        if valid_call_rows
        else None,
    )
    answered_calls = coalesce_present(
        recursive_find(summary, ("answered_calls", "answered")),
        int(total_calls) - int(missed_calls) if total_calls is not None and missed_calls is not None else None,
    )
    after_hours_calls = coalesce_present(
        recursive_find(summary, ("after_hours_calls", "after_hours")),
        sum(
            1
            for call in valid_call_rows
            if call.get("business_phone_number") and str(call.get("business_hours", "")).lower() == "false"
        )
        if valid_call_rows
        else None,
    )
    first_response_time = recursive_find(summary, ("first_response_time", "average_response_time", "avg_response_time_seconds"))
    sources = sorted(set(str(call.get("source") or call.get("utm_source") or call.get("campaign") or "") for call in valid_call_rows if call.get("source") or call.get("utm_source") or call.get("campaign")))

    add_metric(dataset, source, "calls_total", "Total calls", total_calls, "calls")
    add_metric(dataset, source, "calls_missed", "Missed calls", missed_calls, "calls")
    add_metric(dataset, source, "calls_answered", "Answered calls", answered_calls, "calls")
    add_metric(dataset, source, "calls_after_hours", "After-hours calls", after_hours_calls, "calls")
    add_metric(dataset, source, "calls_first_response_time", "First response time", first_response_time, "seconds")
    add_metric(dataset, source, "calls_source_channels", "Call source/channel values", sources, "json_array")
    add_metric(dataset, source, "calls_date_range", "Call tracking date range", {"from": start, "to": end}, "date_range")


THIRD_PARTY_SOURCE_ORDER = [
    "serpapi",
    "brightlocal",
    "similarweb",
    "builtwith",
    "wappalyzer",
    "yext",
    "yelp",
    "trustpilot",
    "foursquare",
    "mapbox",
    "bing-webmaster",
    "google-business-profile",
    "google-ads",
    "meta-ads",
    "tiktok-ads",
    "linkedin-ads",
    "crunchbase",
    "apollo",
    "whatconverts",
    "twilio",
    "ringcentral",
    "aircall",
]


THIRD_PARTY_SOURCE_ALIASES = {
    "bright-local": "brightlocal",
    "built-with": "builtwith",
    "wappalyzer": "wappalyzer",
    "serp-api": "serpapi",
    "gbp": "google-business-profile",
    "business-profile": "google-business-profile",
    "bing": "bing-webmaster",
    "googleads": "google-ads",
    "meta": "meta-ads",
    "facebook-ads": "meta-ads",
    "instagram-ads": "meta-ads",
    "tiktok": "tiktok-ads",
    "linkedin": "linkedin-ads",
    "what-converts": "whatconverts",
}


THIRD_PARTY_SOURCE_LABELS = {
    "serpapi": "SerpApi Google Search API",
    "brightlocal": "BrightLocal",
    "similarweb": "Similarweb",
    "builtwith": "BuiltWith",
    "wappalyzer": "Wappalyzer",
    "yext": "Yext",
    "yelp": "Yelp Fusion",
    "trustpilot": "Trustpilot",
    "foursquare": "Foursquare Places",
    "mapbox": "Mapbox Search Box",
    "bing-webmaster": "Bing Webmaster Tools",
    "google-business-profile": "Google Business Profile API",
    "google-ads": "Google Ads API",
    "meta-ads": "Meta Marketing API",
    "tiktok-ads": "TikTok Business API",
    "linkedin-ads": "LinkedIn Marketing API",
    "crunchbase": "Crunchbase API",
    "apollo": "Apollo API",
    "whatconverts": "WhatConverts",
    "twilio": "Twilio",
    "ringcentral": "RingCentral",
    "aircall": "Aircall",
}


THIRD_PARTY_METRIC_ALIASES = {
    "serpapi": [
        ("organic_position", "Organic position", ("organic_position", "rank", "position"), "rank"),
        ("local_pack_present", "Local pack presence", ("local_pack_present", "local_results_present"), "boolean"),
        ("features", "SERP features", ("features", "serp_features", "answer_box", "knowledge_graph"), "json_array"),
        ("competitor_domains", "Competitor domains", ("competitor_domains", "organic_domains"), "domains"),
    ],
    "brightlocal": [
        ("average_rank", "Average local rank", ("average_rank", "avg_rank", "rank_average"), "rank"),
        ("citation_count", "Citation count", ("citation_count", "citations", "listing_count"), "citations"),
        ("review_count", "Review count", ("review_count", "reviews", "total_reviews"), "reviews"),
        ("rating", "Average rating", ("rating", "average_rating", "star_rating"), "stars"),
    ],
    "similarweb": [
        ("visits", "Estimated visits", ("visits", "total_visits", "estimated_visits"), "visits"),
        ("traffic_channels", "Estimated traffic channels", ("traffic_channels", "channels", "traffic_sources"), "json_object"),
        ("engagement_rate", "Estimated engagement rate", ("engagement_rate", "bounce_rate"), "ratio"),
    ],
    "builtwith": [
        ("technologies", "Detected technologies", ("technologies", "tech", "groups", "results"), "json_array"),
        ("analytics_tags", "Analytics tags", ("analytics_tags", "analytics", "measurement"), "json_array"),
        ("ad_pixels", "Ad pixels", ("ad_pixels", "pixels", "advertising"), "json_array"),
    ],
    "wappalyzer": [
        ("technologies", "Detected technologies", ("technologies", "applications"), "json_array"),
        ("categories", "Detected technology categories", ("categories",), "json_array"),
    ],
    "yext": [
        ("listing_count", "Listings count", ("listing_count", "listings", "entities_count"), "listings"),
        ("review_count", "Review count", ("review_count", "reviews", "total_reviews"), "reviews"),
        ("rating", "Average rating", ("rating", "average_rating"), "stars"),
    ],
    "yelp": [
        ("review_count", "Yelp review count", ("review_count",), "reviews"),
        ("rating", "Yelp rating", ("rating",), "stars"),
        ("businesses", "Yelp matching businesses", ("businesses",), "json_array"),
    ],
    "trustpilot": [
        ("review_count", "Trustpilot review count", ("numberOfReviews", "review_count", "reviews"), "reviews"),
        ("rating", "Trustpilot rating", ("trustScore", "rating", "score"), "stars"),
    ],
    "foursquare": [
        ("place_count", "Matching places", ("place_count", "results"), "places"),
        ("categories", "Place categories", ("categories",), "json_array"),
    ],
    "mapbox": [
        ("suggestion_count", "Matching place suggestions", ("suggestion_count", "suggestions"), "places"),
        ("categories", "Place categories", ("categories",), "json_array"),
    ],
    "bing-webmaster": [
        ("clicks", "Bing clicks", ("clicks",), "clicks"),
        ("impressions", "Bing impressions", ("impressions",), "impressions"),
        ("average_position", "Bing average position", ("average_position", "position"), "rank"),
    ],
    "google-business-profile": [
        ("calls", "GBP calls", ("calls", "phone_calls"), "calls"),
        ("website_clicks", "GBP website clicks", ("website_clicks", "websiteActions"), "clicks"),
        ("direction_requests", "GBP direction requests", ("direction_requests", "drivingDirectionsRequests"), "requests"),
        ("review_count", "GBP review count", ("review_count", "totalReviewCount", "user_ratings_total"), "reviews"),
        ("rating", "GBP rating", ("rating", "averageRating"), "stars"),
    ],
    "google-ads": [
        ("spend", "Google Ads spend", ("spend", "cost", "cost_micros"), "currency"),
        ("impressions", "Google Ads impressions", ("impressions",), "impressions"),
        ("clicks", "Google Ads clicks", ("clicks",), "clicks"),
        ("conversions", "Google Ads conversions", ("conversions",), "conversions"),
    ],
    "meta-ads": [
        ("spend", "Meta Ads spend", ("spend",), "currency"),
        ("impressions", "Meta Ads impressions", ("impressions",), "impressions"),
        ("clicks", "Meta Ads clicks", ("clicks", "inline_link_clicks"), "clicks"),
        ("conversions", "Meta Ads conversions", ("conversions", "actions"), "conversions"),
    ],
    "tiktok-ads": [
        ("spend", "TikTok Ads spend", ("spend",), "currency"),
        ("impressions", "TikTok Ads impressions", ("impressions",), "impressions"),
        ("clicks", "TikTok Ads clicks", ("clicks",), "clicks"),
        ("conversions", "TikTok Ads conversions", ("conversions", "conversion"), "conversions"),
    ],
    "linkedin-ads": [
        ("spend", "LinkedIn Ads spend", ("spend", "costInUsd"), "currency"),
        ("impressions", "LinkedIn Ads impressions", ("impressions",), "impressions"),
        ("clicks", "LinkedIn Ads clicks", ("clicks",), "clicks"),
        ("conversions", "LinkedIn Ads conversions", ("conversions",), "conversions"),
    ],
    "crunchbase": [
        ("employee_count", "Employee count", ("employee_count", "num_employees_enum"), "employees"),
        ("funding_total", "Funding total", ("funding_total", "total_funding_usd"), "currency"),
        ("company_rank", "Company rank", ("rank", "cb_rank"), "rank"),
    ],
    "apollo": [
        ("employee_count", "Employee count", ("employee_count", "estimated_num_employees"), "employees"),
        ("annual_revenue", "Annual revenue", ("annual_revenue", "estimated_annual_revenue"), "currency"),
        ("contacts", "Matching contacts", ("contacts", "people"), "json_array"),
    ],
    "whatconverts": [
        ("leads_total", "WhatConverts leads", ("leads_total", "total_leads", "leads"), "leads"),
        ("calls_total", "WhatConverts calls", ("calls_total", "phone_calls", "calls"), "calls"),
        ("conversions", "WhatConverts conversions", ("conversions",), "conversions"),
    ],
    "twilio": [
        ("calls_total", "Twilio calls", ("calls_total", "calls"), "calls"),
        ("calls_missed", "Twilio missed calls", ("calls_missed", "missed_calls"), "calls"),
        ("average_duration", "Twilio average call duration", ("average_duration", "avg_duration"), "seconds"),
    ],
    "ringcentral": [
        ("calls_total", "RingCentral calls", ("calls_total", "calls"), "calls"),
        ("calls_missed", "RingCentral missed calls", ("calls_missed", "missed_calls"), "calls"),
        ("average_duration", "RingCentral average call duration", ("average_duration", "avg_duration"), "seconds"),
    ],
    "aircall": [
        ("calls_total", "Aircall calls", ("calls_total", "calls"), "calls"),
        ("calls_missed", "Aircall missed calls", ("calls_missed", "missed_calls"), "calls"),
        ("average_duration", "Aircall average call duration", ("average_duration", "avg_duration"), "seconds"),
    ],
}


THIRD_PARTY_REQUIRED_ACCESS = {
    "serpapi": "SERPAPI_KEY or SERPAPI_EXPORT_PATH",
    "brightlocal": "BRIGHTLOCAL_EXPORT_PATH or BrightLocal API export",
    "similarweb": "SIMILARWEB_API_KEY or SIMILARWEB_EXPORT_PATH",
    "builtwith": "BUILTWITH_API_KEY or BUILTWITH_EXPORT_PATH",
    "wappalyzer": "WAPPALYZER_API_KEY or WAPPALYZER_EXPORT_PATH",
    "yext": "YEXT_API_KEY and YEXT_ENTITY_ID or YEXT_EXPORT_PATH",
    "yelp": "YELP_API_KEY or YELP_EXPORT_PATH",
    "trustpilot": "TRUSTPILOT_API_KEY or TRUSTPILOT_EXPORT_PATH",
    "foursquare": "FOURSQUARE_API_KEY or FOURSQUARE_EXPORT_PATH",
    "mapbox": "MAPBOX_ACCESS_TOKEN or MAPBOX_EXPORT_PATH",
    "bing-webmaster": "BING_WEBMASTER_API_KEY or BING_WEBMASTER_EXPORT_PATH",
    "google-business-profile": "GBP_ACCESS_TOKEN and GBP_LOCATION_NAME or GOOGLE_BUSINESS_PROFILE_EXPORT_PATH",
    "google-ads": "GOOGLE_ADS_ACCESS_TOKEN, GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CUSTOMER_ID, and optional GOOGLE_ADS_LOGIN_CUSTOMER_ID or GOOGLE_ADS_EXPORT_PATH",
    "meta-ads": "META_ADS_ACCESS_TOKEN and META_AD_ACCOUNT_ID or META_ADS_EXPORT_PATH",
    "tiktok-ads": "TIKTOK_ADS_ACCESS_TOKEN and TIKTOK_ADVERTISER_ID or TIKTOK_ADS_EXPORT_PATH",
    "linkedin-ads": "LINKEDIN_ADS_ACCESS_TOKEN and LINKEDIN_AD_ACCOUNT_ID or LINKEDIN_ADS_EXPORT_PATH",
    "crunchbase": "CRUNCHBASE_API_KEY or CRUNCHBASE_EXPORT_PATH",
    "apollo": "APOLLO_API_KEY or APOLLO_EXPORT_PATH",
    "whatconverts": "WHATCONVERTS_EXPORT_PATH or connected WhatConverts API export",
    "twilio": "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN or TWILIO_EXPORT_PATH",
    "ringcentral": "RINGCENTRAL_ACCESS_TOKEN or RINGCENTRAL_EXPORT_PATH",
    "aircall": "AIRCALL_API_ID and AIRCALL_API_TOKEN or AIRCALL_EXPORT_PATH",
}


def canonical_third_party_sources(sources: str) -> list[str]:
    if not sources:
        return []
    requested = parse_source_list(sources)
    if "all" in requested:
        return list(THIRD_PARTY_SOURCE_ORDER)
    canonical = []
    for source_id in requested:
        normalized = THIRD_PARTY_SOURCE_ALIASES.get(source_id, source_id)
        if normalized not in THIRD_PARTY_SOURCE_ORDER:
            raise ValueError(f"Unknown third-party source: {source_id}")
        if normalized not in canonical:
            canonical.append(normalized)
    return canonical


def third_party_export_env(source_id: str) -> str:
    if source_id == "google-business-profile":
        return "GOOGLE_BUSINESS_PROFILE_EXPORT_PATH"
    return env_key(source_id, "EXPORT_PATH")


def load_third_party_export(source_id: str, raw_dir: Path) -> tuple[Any, str, str] | None:
    export_path = os.getenv(third_party_export_env(source_id), "")
    if not export_path:
        return None
    path = Path(export_path)
    if not path.exists():
        return None
    data = load_artifact(path)
    artifact = copy_input_artifact(raw_dir, path, f"third_party_{source_id.replace('-', '_')}_export")
    return data, str(path), artifact


def third_party_api_request(source_id: str, dataset: AuditDataset, keywords: str, location: str, date_from: str, date_to: str) -> tuple[str, str, dict[str, str], Any | None, str] | None:
    domain = target_domain(dataset.target_url)
    base_url = normalize_base_url(dataset.target_url)
    query = split_keywords(keywords)[0] if keywords else domain
    business_query = " ".join(part for part in [dataset.firm_name, location, domain] if part).strip() or domain
    start, end = default_date_range(date_from, date_to)

    if source_id == "serpapi" and os.getenv("SERPAPI_KEY"):
        params = {"engine": "google", "q": query, "api_key": os.getenv("SERPAPI_KEY", "")}
        if location:
            params["location"] = location
        return "GET", "https://serpapi.com/search.json?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "similarweb" and os.getenv("SIMILARWEB_API_KEY"):
        params = {"api_key": os.getenv("SIMILARWEB_API_KEY", ""), "start_date": start[:7], "end_date": end[:7], "country": "world", "main_domain_only": "false", "format": "json"}
        return "GET", f"https://api.similarweb.com/v1/website/{urllib.parse.quote(domain)}/total-traffic-and-engagement/visits?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "builtwith" and os.getenv("BUILTWITH_API_KEY"):
        params = {"KEY": os.getenv("BUILTWITH_API_KEY", ""), "LOOKUP": domain}
        return "GET", "https://api.builtwith.com/v21/api.json?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "wappalyzer" and os.getenv("WAPPALYZER_API_KEY"):
        return "POST", "https://api.wappalyzer.com/v2/lookup/", {"x-api-key": os.getenv("WAPPALYZER_API_KEY", "")}, {"urls": [base_url]}, "json"
    if source_id == "yext" and os.getenv("YEXT_API_KEY") and os.getenv("YEXT_ENTITY_ID"):
        params = {"api_key": os.getenv("YEXT_API_KEY", ""), "v": date.today().strftime("%Y%m%d")}
        return "GET", f"https://api.yext.com/v2/accounts/me/entities/{urllib.parse.quote(os.getenv('YEXT_ENTITY_ID', ''))}?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "yelp" and os.getenv("YELP_API_KEY"):
        params = {"term": business_query, "limit": "3"}
        if location:
            params["location"] = location
        return "GET", "https://api.yelp.com/v3/businesses/search?" + urllib.parse.urlencode(params), {"Authorization": f"Bearer {os.getenv('YELP_API_KEY', '')}"}, None, "json"
    if source_id == "trustpilot" and os.getenv("TRUSTPILOT_API_KEY"):
        params = {"name": domain, "apikey": os.getenv("TRUSTPILOT_API_KEY", "")}
        return "GET", "https://api.trustpilot.com/v1/business-units/find?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "foursquare" and os.getenv("FOURSQUARE_API_KEY"):
        params = {"query": business_query, "limit": "5"}
        if location:
            params["near"] = location
        return "GET", "https://api.foursquare.com/v3/places/search?" + urllib.parse.urlencode(params), {"Authorization": os.getenv("FOURSQUARE_API_KEY", "")}, None, "json"
    if source_id == "mapbox" and os.getenv("MAPBOX_ACCESS_TOKEN"):
        params = {"q": business_query, "access_token": os.getenv("MAPBOX_ACCESS_TOKEN", ""), "session_token": hashlib.sha1(business_query.encode("utf-8")).hexdigest()[:16]}
        return "GET", "https://api.mapbox.com/search/searchbox/v1/suggest?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "bing-webmaster" and os.getenv("BING_WEBMASTER_API_KEY"):
        params = {"apikey": os.getenv("BING_WEBMASTER_API_KEY", ""), "siteUrl": base_url}
        return "GET", "https://ssl.bing.com/webmaster/api.svc/json/GetQueryStats?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "google-business-profile" and os.getenv("GBP_ACCESS_TOKEN") and os.getenv("GBP_LOCATION_NAME"):
        params = {"readMask": "title,storefrontAddress,phoneNumbers,categories,websiteUri,metadata"}
        return "GET", f"https://mybusinessbusinessinformation.googleapis.com/v1/{os.getenv('GBP_LOCATION_NAME', '')}?" + urllib.parse.urlencode(params), {"Authorization": f"Bearer {os.getenv('GBP_ACCESS_TOKEN', '')}"}, None, "json"
    if source_id == "google-ads" and os.getenv("GOOGLE_ADS_ACCESS_TOKEN") and os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN") and os.getenv("GOOGLE_ADS_CUSTOMER_ID"):
        customer_id = re.sub(r"[^0-9]", "", os.getenv("GOOGLE_ADS_CUSTOMER_ID", ""))
        headers = {
            "Authorization": f"Bearer {os.getenv('GOOGLE_ADS_ACCESS_TOKEN', '')}",
            "developer-token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
        }
        if os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"):
            headers["login-customer-id"] = re.sub(r"[^0-9]", "", os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""))
        query = (
            "SELECT metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions "
            f"FROM customer WHERE segments.date BETWEEN '{start}' AND '{end}'"
        )
        return "POST", f"https://googleads.googleapis.com/v18/customers/{customer_id}/googleAds:searchStream", headers, {"query": query}, "json"
    if source_id == "meta-ads" and os.getenv("META_ADS_ACCESS_TOKEN") and os.getenv("META_AD_ACCOUNT_ID"):
        params = {"access_token": os.getenv("META_ADS_ACCESS_TOKEN", ""), "time_range": json.dumps({"since": start, "until": end}), "fields": "spend,impressions,clicks,inline_link_clicks,actions"}
        return "GET", f"https://graph.facebook.com/v20.0/act_{os.getenv('META_AD_ACCOUNT_ID', '')}/insights?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "tiktok-ads" and os.getenv("TIKTOK_ADS_ACCESS_TOKEN") and os.getenv("TIKTOK_ADVERTISER_ID"):
        params = {"advertiser_id": os.getenv("TIKTOK_ADVERTISER_ID", ""), "start_date": start, "end_date": end, "metrics": json.dumps(["spend", "impressions", "clicks", "conversion"])}
        return "GET", "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/?" + urllib.parse.urlencode(params), {"Access-Token": os.getenv("TIKTOK_ADS_ACCESS_TOKEN", "")}, None, "json"
    if source_id == "linkedin-ads" and os.getenv("LINKEDIN_ADS_ACCESS_TOKEN") and os.getenv("LINKEDIN_AD_ACCOUNT_ID"):
        params = {"q": "analytics", "pivot": "ACCOUNT", "accounts": f"List(urn:li:sponsoredAccount:{os.getenv('LINKEDIN_AD_ACCOUNT_ID', '')})", "dateRange.start.year": start[:4], "dateRange.end.year": end[:4]}
        return "GET", "https://api.linkedin.com/v2/adAnalyticsV2?" + urllib.parse.urlencode(params), {"Authorization": f"Bearer {os.getenv('LINKEDIN_ADS_ACCESS_TOKEN', '')}"}, None, "json"
    if source_id == "crunchbase" and os.getenv("CRUNCHBASE_API_KEY"):
        params = {"user_key": os.getenv("CRUNCHBASE_API_KEY", ""), "query": dataset.firm_name or domain}
        return "GET", "https://api.crunchbase.com/api/v4/searches/organizations?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "apollo" and os.getenv("APOLLO_API_KEY"):
        return "POST", "https://api.apollo.io/v1/organizations/enrich", {"Cache-Control": "no-cache", "X-Api-Key": os.getenv("APOLLO_API_KEY", "")}, {"domain": domain}, "json"
    if source_id == "twilio" and os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"):
        params = {"StartTime>": start, "EndTime<": end, "PageSize": "1000"}
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        return "GET", f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json?" + urllib.parse.urlencode(params), {}, None, "json"
    if source_id == "ringcentral" and os.getenv("RINGCENTRAL_ACCESS_TOKEN"):
        params = {"dateFrom": start, "dateTo": end}
        return "GET", "https://platform.ringcentral.com/restapi/v1.0/account/~/call-log?" + urllib.parse.urlencode(params), {"Authorization": f"Bearer {os.getenv('RINGCENTRAL_ACCESS_TOKEN', '')}"}, None, "json"
    if source_id == "aircall" and os.getenv("AIRCALL_API_ID") and os.getenv("AIRCALL_API_TOKEN"):
        return "GET", "https://api.aircall.io/v1/calls", {}, None, "json"
    return None


def normalize_serpapi_data(data: Any, domain: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    organic_results = data.get("organic_results") if isinstance(data.get("organic_results"), list) else []
    competitors = []
    organic_position = None
    for result in organic_results:
        if not isinstance(result, dict):
            continue
        result_domain = urllib.parse.urlparse(result.get("link", "")).netloc.lower().removeprefix("www.")
        position = result.get("position")
        if domain in result_domain and organic_position is None:
            organic_position = position
        elif result_domain and result_domain not in competitors:
            competitors.append(result_domain)
    local_results = data.get("local_results") or data.get("local_map")
    return {
        "organic_position": organic_position,
        "local_pack_present": bool(local_results),
        "features": sorted(key for key in ("answer_box", "knowledge_graph", "local_results", "shopping_results", "top_stories") if key in data),
        "competitor_domains": competitors[:10],
    }


def normalize_ads_data(data: Any) -> dict[str, Any]:
    rows = []
    if isinstance(data, dict):
        for key in ("data", "rows", "results", "elements"):
            value = data.get(key)
            if isinstance(value, list):
                rows = value
                break
        if not rows:
            rows = [data]
    elif isinstance(data, list):
        rows = data
    result = {"spend": 0.0, "impressions": 0.0, "clicks": 0.0, "conversions": 0.0}
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        spend = to_float(recursive_find(row, ("spend", "cost", "cost_micros", "costMicros", "costInUsd")))
        if spend is not None:
            if recursive_find(row, ("cost_micros", "costMicros")) is not None:
                spend = spend / 1_000_000
            result["spend"] += spend
            seen.add("spend")
        for key, aliases in [
            ("impressions", ("impressions",)),
            ("clicks", ("clicks", "inline_link_clicks")),
            ("conversions", ("conversions", "conversion")),
        ]:
            value = recursive_find(row, aliases)
            if isinstance(value, list):
                value = sum(to_float(item.get("value")) or 0 for item in value if isinstance(item, dict))
            numeric = to_float(value)
            if numeric is not None:
                result[key] += numeric
                seen.add(key)
    return {key: value for key, value in result.items() if key in seen}


def normalize_calls_data(data: Any) -> dict[str, Any]:
    rows = []
    if isinstance(data, dict):
        for key in ("calls", "records", "items", "data"):
            value = data.get(key)
            if isinstance(value, list):
                rows = value
                break
        if not rows:
            rows = [data]
    elif isinstance(data, list):
        rows = data
    call_rows = [row for row in rows if isinstance(row, dict)]
    if not call_rows:
        return {}
    missed = sum(1 for row in call_rows if str(row.get("status") or row.get("result") or "").lower() in {"missed", "no-answer", "no_answer", "abandoned"} or str(row.get("answered", "")).lower() == "false")
    durations = [to_float(row.get("duration") or row.get("duration_seconds")) for row in call_rows]
    durations = [value for value in durations if value is not None]
    return {
        "calls_total": len(call_rows),
        "calls_missed": missed,
        "average_duration": sum(durations) / len(durations) if durations else None,
    }


def normalize_place_count(data: Any, list_keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    rows = []
    for key in list_keys:
        value = data.get(key)
        if isinstance(value, list):
            rows = value
            break
    categories = []
    for row in rows:
        if isinstance(row, dict):
            raw_categories = row.get("categories") or row.get("category")
            if isinstance(raw_categories, list):
                categories.extend(raw_categories)
            elif raw_categories:
                categories.append(raw_categories)
    return {
        "place_count": len(rows) if rows else None,
        "suggestion_count": len(rows) if rows else None,
        "categories": categories[:20] if categories else None,
    }


def normalize_third_party_payload(source_id: str, dataset: AuditDataset, data: Any) -> Any:
    domain = target_domain(dataset.target_url)
    if source_id == "serpapi":
        return normalize_serpapi_data(data, domain)
    if source_id in {"google-ads", "meta-ads", "tiktok-ads", "linkedin-ads"}:
        return normalize_ads_data(data)
    if source_id in {"twilio", "ringcentral", "aircall"}:
        return normalize_calls_data(data)
    if source_id in {"foursquare", "mapbox"}:
        return normalize_place_count(data, ("results", "suggestions", "features"))
    return data


def collect_third_party_source(dataset: AuditDataset, raw_dir: Path, source_id: str, *, keywords: str = "", location: str = "", date_from: str = "", date_to: str = "") -> None:
    label = THIRD_PARTY_SOURCE_LABELS[source_id]
    export = load_third_party_export(source_id, raw_dir)
    access = "third_party_export"
    tier = SourceTier.USER_PROVIDED.value
    source_url = ""
    data: Any = None
    artifact = ""

    if export:
        data, source_url, artifact = export
    else:
        request = third_party_api_request(source_id, dataset, keywords, location, date_from, date_to)
        if request is None:
            add_gap(
                dataset,
                label,
                "Third-party data source metrics",
                f"{label} was not connected; do not use its metrics or estimates",
                f"Connect {label} or provide an export",
                THIRD_PARTY_REQUIRED_ACCESS[source_id],
            )
            return
        method, endpoint, headers, payload, suffix = request
        status, body, _ = fetch_url(
            endpoint,
            timeout=60,
            method=method,
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers={"Content-Type": "application/json", **headers} if payload is not None else headers,
            basic_auth=(os.getenv("TWILIO_ACCOUNT_SID", ""), os.getenv("TWILIO_AUTH_TOKEN", "")) if source_id == "twilio" else (os.getenv("AIRCALL_API_ID", ""), os.getenv("AIRCALL_API_TOKEN", "")) if source_id == "aircall" else None,
        )
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = parse_table(body)
            suffix = "csv"
        source_url = redact_url(endpoint)
        artifact = save_artifact(raw_dir, endpoint, data if suffix == "json" else body, suffix)
        access = "third_party_api"
        tier = SourceTier.THIRD_PARTY_ESTIMATE.value
        if status != 200:
            add_gap(
                dataset,
                label,
                "Third-party data source metrics",
                f"{label} request failed; do not use its metrics or estimates",
                f"Fix {label} access or provide an export",
                THIRD_PARTY_REQUIRED_ACCESS[source_id],
            )
            return

    source = dataset.add_source(
        AuditSource(
            source_id=f"third_party_{source_id.replace('-', '_')}",
            name=label,
            tier=tier,
            access=access,
            retrieved_at=utc_now_iso(),
            used_for="Third-party sourced metrics and estimates",
            source_url=source_url,
            artifact_path=artifact,
            notes="Third-party data may be vendor-modeled; cite as third_party_estimate unless export is user-provided.",
        )
    )
    normalized = normalize_third_party_payload(source_id, dataset, data)
    added = 0
    for suffix, metric_label, aliases, unit in THIRD_PARTY_METRIC_ALIASES[source_id]:
        if add_metric(
            dataset,
            source,
            f"{source_id.replace('-', '_')}_{suffix}",
            metric_label,
            recursive_find(normalized, aliases),
            unit,
            confidence="medium" if tier == SourceTier.THIRD_PARTY_ESTIMATE.value else "high",
            notes="Third-party sourced value; do not treat vendor-modeled estimates as client-owned analytics.",
        ):
            added += 1
    if added == 0:
        add_gap(
            dataset,
            label,
            "Third-party data source metrics",
            f"{label} response/export had no recognized canonical metrics; do not use its data",
            f"Provide a {label} export/API response with recognized fields",
            "Recognized third-party metric fields",
        )


def collect_third_party_sources(dataset: AuditDataset, raw_dir: Path, *, sources: str = "", keywords: str = "", location: str = "", date_from: str = "", date_to: str = "") -> None:
    for source_id in canonical_third_party_sources(sources):
        collect_third_party_source(
            dataset,
            raw_dir,
            source_id,
            keywords=keywords,
            location=location,
            date_from=date_from,
            date_to=date_to,
        )


def collect_kai_data(
    url: str,
    firm_name: str,
    out_dir: Path,
    mode: str = AuditMode.SALES_EXTERNAL.value,
    *,
    workflow: str = "all",
    pagespeed: bool = False,
    places: bool = False,
    dataforseo: bool = False,
    seo_provider: str = "",
    gsc: bool = False,
    ga4: bool = False,
    calls: bool = False,
    third_party_sources: str = "",
    keywords: str = "",
    location: str = "",
    date_from: str = "",
    date_to: str = "",
) -> AuditDataset:
    if mode not in {m.value for m in AuditMode}:
        raise ValueError(f"Unknown audit mode: {mode}")
    dataset = AuditDataset(audit_mode=mode, target_url=normalize_base_url(url), firm_name=firm_name, workflow=workflow)
    raw_dir = out_dir / "raw"
    dataset.raw_artifacts_dir = str(raw_dir)

    collect_public_site(dataset, raw_dir)
    if pagespeed:
        collect_pagespeed(dataset, raw_dir)
    if places:
        collect_places(dataset, raw_dir, location=location)
    if dataforseo:
        collect_dataforseo_serp(dataset, raw_dir, keywords=keywords, location=location)
    if seo_provider:
        collect_seo_provider(dataset, raw_dir, provider=seo_provider)
    if gsc:
        collect_gsc(dataset, raw_dir, mode=mode, date_from=date_from, date_to=date_to)
    if ga4:
        collect_ga4(dataset, raw_dir, mode=mode, date_from=date_from, date_to=date_to)
    if calls:
        collect_calls(dataset, raw_dir, mode=mode, date_from=date_from, date_to=date_to)
    if third_party_sources:
        collect_third_party_sources(
            dataset,
            raw_dir,
            sources=third_party_sources,
            keywords=keywords,
            location=location,
            date_from=date_from,
            date_to=date_to,
        )

    dataset.write(out_dir)
    return dataset


def collect_audit_data(
    url: str,
    firm_name: str,
    out_dir: Path,
    mode: str = AuditMode.SALES_EXTERNAL.value,
    pagespeed: bool = False,
    **kwargs: Any,
) -> AuditDataset:
    return collect_kai_data(
        url=url,
        firm_name=firm_name,
        out_dir=out_dir,
        mode=mode,
        workflow=kwargs.pop("workflow", "audit"),
        pagespeed=pagespeed,
        **kwargs,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect source-backed Kai data")
    parser.add_argument("--url", required=True, help="Website URL to collect data for")
    parser.add_argument("--firm-name", default="", help="Firm/business name")
    parser.add_argument("--out", default="workspace/marketing-data", help="Output directory")
    parser.add_argument(
        "--mode",
        choices=[m.value for m in AuditMode],
        default=AuditMode.SALES_EXTERNAL.value,
        help="Data access mode",
    )
    parser.add_argument("--workflow", default="all", help="Workflow consuming the data, e.g. audit, seo-audit, cro, plan")
    parser.add_argument("--pagespeed", action="store_true", help="Call PageSpeed Insights for mobile and desktop")
    parser.add_argument("--places", action="store_true", help="Collect Google Places/GBP public data")
    parser.add_argument("--dataforseo", action="store_true", help="Collect DataForSEO SERP observations")
    parser.add_argument("--seo-provider", nargs="?", const="auto", default="", help="Collect SEO platform data: auto, ahrefs, semrush, moz, dataforseo")
    parser.add_argument("--gsc", action="store_true", help="Collect Google Search Console onboarding data")
    parser.add_argument("--ga4", action="store_true", help="Collect Google Analytics 4 onboarding data")
    parser.add_argument("--calls", action="store_true", help="Collect call tracking onboarding data")
    parser.add_argument("--third-party-sources", default="", help='Collect third-party sources: "all" or comma-separated ids like "serpapi,similarweb,builtwith"')
    parser.add_argument("--keywords", default="", help='Comma-separated keywords, e.g. "kw1,kw2,kw3"')
    parser.add_argument("--location", default="", help="Location for local SERP/Places queries")
    parser.add_argument("--date-from", default="", help="Start date for onboarding data, YYYY-MM-DD")
    parser.add_argument("--date-to", default="", help="End date for onboarding data, YYYY-MM-DD")
    args = parser.parse_args()

    try:
        dataset = collect_kai_data(
            url=args.url,
            firm_name=args.firm_name,
            out_dir=Path(args.out),
            mode=args.mode,
            workflow=args.workflow,
            pagespeed=args.pagespeed,
            places=args.places,
            dataforseo=args.dataforseo,
            seo_provider=args.seo_provider,
            gsc=args.gsc,
            ga4=args.ga4,
            calls=args.calls,
            third_party_sources=args.third_party_sources,
            keywords=args.keywords,
            location=args.location,
            date_from=args.date_from,
            date_to=args.date_to,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Kai data written: {Path(args.out) / 'kai-data.json'}")
    print(f"Audit data alias written: {Path(args.out) / 'audit-data.json'}")
    print(f"Sources: {len(dataset.sources)}   Metrics: {len(dataset.metrics)}   Gaps: {len(dataset.data_gaps)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
