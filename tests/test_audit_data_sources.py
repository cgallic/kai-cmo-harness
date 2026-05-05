from pathlib import Path

import pytest

from scripts.audit.data_sources import (
    AuditDataset,
    AuditMetric,
    AuditSource,
    DataGap,
    SourceTier,
    utc_now_iso,
)
from scripts.audit.collect import (
    collect_calls,
    collect_dataforseo_serp,
    collect_ga4,
    collect_gsc,
    collect_kai_data,
    main as collect_main,
    collect_pagespeed,
    collect_places,
    collect_seo_provider,
    collect_third_party_sources,
)


def test_scoreable_metric_requires_real_source() -> None:
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")
    dataset.add_source(
        AuditSource(
            source_id="hypothesis",
            name="Agent hypothesis",
            tier=SourceTier.INFERRED.value,
            access="internal",
            retrieved_at=utc_now_iso(),
            used_for="Internal note",
        )
    )

    with pytest.raises(ValueError, match="not score eligible"):
        dataset.add_metric(
            AuditMetric(
                metric_id="review_count",
                label="Review count",
                value=63,
                unit="reviews",
                source_id="hypothesis",
                source_tier=SourceTier.INFERRED.value,
            )
        )


def test_scoreable_metric_requires_artifact_or_url() -> None:
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")
    dataset.add_source(
        AuditSource(
            source_id="places",
            name="Google Places API",
            tier=SourceTier.CONNECTED.value,
            access="api",
            retrieved_at=utc_now_iso(),
            used_for="Reviews",
        )
    )

    with pytest.raises(ValueError, match="source_url or artifact_path"):
        dataset.add_metric(
            AuditMetric(
                metric_id="review_count",
                label="Review count",
                value=63,
                unit="reviews",
                source_id="places",
                source_tier=SourceTier.CONNECTED.value,
            )
        )


def test_dataset_writes_sources_and_gaps(tmp_path: Path) -> None:
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")
    source = dataset.add_source(
        AuditSource(
            source_id="homepage",
            name="Homepage crawl",
            tier=SourceTier.PUBLIC_OBSERVED.value,
            access="external",
            retrieved_at=utc_now_iso(),
            used_for="Homepage status",
            source_url="https://example.com",
            artifact_path=str(tmp_path / "raw" / "homepage.html"),
        )
    )
    dataset.add_metric(
        AuditMetric(
            metric_id="homepage_status",
            label="Homepage status",
            value=200,
            unit="status_code",
            source_id=source.source_id,
            source_tier=source.tier,
        )
    )
    dataset.add_gap(
        DataGap(
            missing_source="Google Search Console",
            blocks="Query data",
            sales_version_handling="Unavailable in sales",
            onboarding_version_handling="Connect GSC",
        )
    )

    dataset.write(tmp_path)

    assert (tmp_path / "audit-data.json").exists()
    assert (tmp_path / "kai-data.json").exists()
    assert (tmp_path / "audit-data.json").read_text() == (tmp_path / "kai-data.json").read_text()
    assert "Homepage crawl" in (tmp_path / "_data-sources.md").read_text()
    assert "Google Search Console" in (tmp_path / "_data-gaps.md").read_text()


def test_missing_api_keys_create_data_gaps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name in [
        "GOOGLE_PLACES_API_KEY",
        "DATAFORSEO_LOGIN",
        "DATAFORSEO_PASSWORD",
        "AHREFS_API_KEY",
        "SEMRUSH_API_KEY",
        "MOZ_ACCESS_TOKEN",
        "GSC_PROPERTY",
        "GSC_SERVICE_ACCOUNT_FILE",
        "GA4_PROPERTY_ID",
        "GA4_SERVICE_ACCOUNT_FILE",
        "CALLRAIL_API_KEY",
        "CALLRAIL_ACCOUNT_ID",
        "SERPAPI_KEY",
        "SIMILARWEB_API_KEY",
        "BUILTWITH_API_KEY",
        "WAPPALYZER_API_KEY",
        "YELP_API_KEY",
        "YEXT_API_KEY",
        "YEXT_ENTITY_ID",
        "TRUSTPILOT_API_KEY",
        "FOURSQUARE_API_KEY",
        "MAPBOX_ACCESS_TOKEN",
        "BING_WEBMASTER_API_KEY",
        "GBP_ACCESS_TOKEN",
        "GBP_LOCATION_NAME",
        "GOOGLE_ADS_ACCESS_TOKEN",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CUSTOMER_ID",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
        "META_ADS_ACCESS_TOKEN",
        "META_AD_ACCOUNT_ID",
        "TIKTOK_ADS_ACCESS_TOKEN",
        "TIKTOK_ADVERTISER_ID",
        "LINKEDIN_ADS_ACCESS_TOKEN",
        "LINKEDIN_AD_ACCOUNT_ID",
        "CRUNCHBASE_API_KEY",
        "APOLLO_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "RINGCENTRAL_ACCESS_TOKEN",
        "AIRCALL_API_ID",
        "AIRCALL_API_TOKEN",
        "SEO_PROVIDER_EXPORT_PATH",
        "GSC_EXPORT_PATH",
        "GA4_EXPORT_PATH",
        "CALL_EXPORT_PATH",
    ]:
        monkeypatch.delenv(env_name, raising=False)

    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    raw_dir = tmp_path / "raw"

    collect_places(dataset, raw_dir)
    collect_dataforseo_serp(dataset, raw_dir, keywords="seo audit")
    collect_seo_provider(dataset, raw_dir, provider="auto")
    collect_gsc(dataset, raw_dir, mode="onboarding_connected")
    collect_ga4(dataset, raw_dir, mode="onboarding_connected")
    collect_calls(dataset, raw_dir, mode="onboarding_connected")

    missing = {gap.missing_source for gap in dataset.data_gaps}
    assert "Google Places API" in missing
    assert "DataForSEO SERP API" in missing
    assert "Ahrefs/Semrush/Moz/DataForSEO SEO platform data" in missing
    assert "Google Search Console" in missing
    assert "Google Analytics 4" in missing
    assert "CallRail call tracking" in missing
    assert dataset.metrics == []


def test_missing_third_party_sources_create_data_gaps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name in [
        "SERPAPI_KEY",
        "SIMILARWEB_API_KEY",
        "BUILTWITH_API_KEY",
        "WAPPALYZER_API_KEY",
        "YELP_API_KEY",
        "SERPAPI_EXPORT_PATH",
        "SIMILARWEB_EXPORT_PATH",
        "BUILTWITH_EXPORT_PATH",
        "WAPPALYZER_EXPORT_PATH",
        "YELP_EXPORT_PATH",
    ]:
        monkeypatch.delenv(env_name, raising=False)

    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")

    collect_third_party_sources(dataset, tmp_path / "raw", sources="serpapi,similarweb,builtwith,wappalyzer,yelp")

    missing = {gap.missing_source for gap in dataset.data_gaps}
    assert "SerpApi Google Search API" in missing
    assert "Similarweb" in missing
    assert "BuiltWith" in missing
    assert "Wappalyzer" in missing
    assert "Yelp Fusion" in missing
    assert dataset.metrics == []


def test_mocked_pagespeed_response_creates_sourced_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = {
        "lighthouseResult": {
            "categories": {"performance": {"score": 0.91}},
            "audits": {
                "largest-contentful-paint": {"numericValue": 1200.4},
                "interaction-to-next-paint": {"numericValue": 84},
                "cumulative-layout-shift": {"numericValue": 0.02},
            },
        }
    }

    def fake_fetch(url: str, **kwargs):
        return 200, json_dumps(payload), {}

    monkeypatch.setattr("scripts.audit.collect.fetch_url", fake_fetch)
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")

    collect_pagespeed(dataset, tmp_path / "raw", strategies=("mobile",))

    metric_ids = {metric.metric_id for metric in dataset.metrics}
    assert "pagespeed_mobile_performance_score" in metric_ids
    assert "pagespeed_mobile_largest-contentful-paint" in metric_ids
    assert dataset.metrics[0].source_id == "pagespeed_mobile"
    assert dataset.sources[0].artifact_path


def test_mocked_places_response_creates_sourced_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test-key")

    def fake_fetch_json(url: str, **kwargs):
        if "findplacefromtext" in url:
            return 200, {"candidates": [{"place_id": "abc"}]}, "{}"
        return 200, {
            "result": {
                "name": "Example Firm",
                "rating": 4.7,
                "user_ratings_total": 63,
                "formatted_address": "1 Main St",
                "formatted_phone_number": "(555) 111-2222",
                "types": ["law_firm"],
                "url": "https://maps.google.com/?cid=1",
            }
        }, "{}"

    monkeypatch.setattr("scripts.audit.collect.fetch_json", fake_fetch_json)
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com", firm_name="Example")

    collect_places(dataset, tmp_path / "raw", location="Denver")

    by_id = {metric.metric_id: metric for metric in dataset.metrics}
    assert by_id["places_review_count"].value == 63
    assert by_id["places_rating"].source_tier == SourceTier.CONNECTED.value


def test_mocked_dataforseo_response_creates_rank_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATAFORSEO_LOGIN", "login")
    monkeypatch.setenv("DATAFORSEO_PASSWORD", "password")

    def fake_fetch_json(url: str, **kwargs):
        return 200, {
            "tasks": [
                {
                    "data": {"keyword": "seo audit"},
                    "result": [
                        {
                            "items": [
                                {"type": "organic", "domain": "competitor.com", "rank_group": 1},
                                {"type": "organic", "domain": "example.com", "rank_group": 2},
                                {"type": "local_pack", "rank_group": 1},
                            ]
                        }
                    ],
                }
            ]
        }, "{}"

    monkeypatch.setattr("scripts.audit.collect.fetch_json", fake_fetch_json)
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")

    collect_dataforseo_serp(dataset, tmp_path / "raw", keywords="seo audit", location="United States")

    by_id = {metric.metric_id: metric for metric in dataset.metrics}
    assert by_id["serp_seo_audit_organic_position"].value == 2
    assert by_id["serp_seo_audit_local_pack_present"].value is True
    assert by_id["serp_seo_audit_competitor_domains"].value == ["competitor.com"]


def test_mocked_serpapi_response_creates_third_party_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERPAPI_KEY", "test-key")

    def fake_fetch(url: str, **kwargs):
        return 200, json_dumps(
            {
                "organic_results": [
                    {"position": 1, "link": "https://competitor.com/"},
                    {"position": 2, "link": "https://example.com/service"},
                ],
                "local_results": {"places": [{"title": "Example"}]},
                "answer_box": {"answer": "Example"},
            }
        ), {}

    monkeypatch.setattr("scripts.audit.collect.fetch_url", fake_fetch)
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")

    collect_third_party_sources(dataset, tmp_path / "raw", sources="serpapi", keywords="seo audit", location="Denver, CO")

    by_id = {metric.metric_id: metric for metric in dataset.metrics}
    assert by_id["serpapi_organic_position"].value == 2
    assert by_id["serpapi_local_pack_present"].value is True
    assert by_id["serpapi_competitor_domains"].value == ["competitor.com"]
    assert by_id["serpapi_organic_position"].source_tier == SourceTier.THIRD_PARTY_ESTIMATE.value


def test_mocked_google_ads_response_creates_third_party_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_ADS_ACCESS_TOKEN", "access")
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "developer")
    monkeypatch.setenv("GOOGLE_ADS_CUSTOMER_ID", "123-456-7890")

    def fake_fetch(url: str, **kwargs):
        return 200, json_dumps(
            [
                {
                    "results": [
                        {
                            "metrics": {
                                "costMicros": "1230000",
                                "impressions": "1000",
                                "clicks": "50",
                                "conversions": "4",
                            }
                        }
                    ]
                }
            ]
        ), {}

    monkeypatch.setattr("scripts.audit.collect.fetch_url", fake_fetch)
    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")

    collect_third_party_sources(dataset, tmp_path / "raw", sources="google-ads", date_from="2026-04-01", date_to="2026-04-30")

    by_id = {metric.metric_id: metric for metric in dataset.metrics}
    assert by_id["google_ads_spend"].value == 1.23
    assert by_id["google_ads_impressions"].value == 1000
    assert by_id["google_ads_conversions"].source_tier == SourceTier.THIRD_PARTY_ESTIMATE.value


def test_exports_create_sourced_connected_onboarding_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seo_export = tmp_path / "seo.json"
    gsc_export = tmp_path / "gsc.json"
    ga4_export = tmp_path / "ga4.json"
    call_export = tmp_path / "calls.json"
    seo_export.write_text(
        json_dumps(
            {
                "domain_rating": 42,
                "referring_domains": 120,
                "backlinks": 500,
                "organic_keywords": 900,
                "organic_traffic": 1500,
                "top_pages": ["/"],
            }
        )
    )
    gsc_export.write_text(json_dumps([{"clicks": 10, "impressions": 100, "ctr": 0.1, "position": 3.4}]))
    ga4_export.write_text(
        json_dumps(
            [
                {"metric_name": "sessions", "value": 200},
                {"metric_name": "active_users", "value": 120},
                {"metric_name": "conversions", "value": 8},
            ]
        )
    )
    call_export.write_text(json_dumps([{"status": "answered", "source": "google"}, {"status": "missed", "source": "google"}]))
    monkeypatch.setenv("SEO_PROVIDER_EXPORT_PATH", str(seo_export))
    monkeypatch.setenv("GSC_EXPORT_PATH", str(gsc_export))
    monkeypatch.setenv("GA4_EXPORT_PATH", str(ga4_export))
    monkeypatch.setenv("CALL_EXPORT_PATH", str(call_export))

    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    raw_dir = tmp_path / "raw"
    collect_seo_provider(dataset, raw_dir, provider="auto")
    collect_gsc(dataset, raw_dir, mode="onboarding_connected")
    collect_ga4(dataset, raw_dir, mode="onboarding_connected")
    collect_calls(dataset, raw_dir, mode="onboarding_connected")

    by_id = {metric.metric_id: metric for metric in dataset.metrics}
    assert by_id["seo_domain_authority"].value == 42
    assert by_id["gsc_clicks"].value == 10
    assert by_id["ga4_conversion_rate"].value == 0.04
    assert by_id["calls_total"].value == 2
    assert all(metric.source_id for metric in dataset.metrics)
    assert all(metric.source_tier for metric in dataset.metrics)
    assert all(metric.unit for metric in dataset.metrics)


def test_invalid_pagespeed_response_creates_gap_not_metric(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_fetch(url: str, **kwargs):
        return 200, json_dumps({"id": "https://example.com"}), {}

    monkeypatch.setattr("scripts.audit.collect.fetch_url", fake_fetch)
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")

    collect_pagespeed(dataset, tmp_path / "raw", strategies=("desktop",))

    assert dataset.metrics == []
    assert any("PageSpeed Insights (desktop)" in gap.missing_source for gap in dataset.data_gaps)


def test_dataforseo_task_error_creates_gap_not_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATAFORSEO_LOGIN", "login")
    monkeypatch.setenv("DATAFORSEO_PASSWORD", "password")

    def fake_fetch_json(url: str, **kwargs):
        return 200, {
            "status_code": 20000,
            "tasks": [
                {
                    "status_code": 40501,
                    "status_message": "Invalid Field",
                    "data": {"keyword": "seo audit"},
                    "result": None,
                }
            ],
        }, "{}"

    monkeypatch.setattr("scripts.audit.collect.fetch_json", fake_fetch_json)
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")

    collect_dataforseo_serp(dataset, tmp_path / "raw", keywords="seo audit")

    assert dataset.metrics == []
    assert any(gap.missing_source == "DataForSEO SERP API task" for gap in dataset.data_gaps)


def test_invalid_exports_create_gaps_not_zero_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gsc_export = tmp_path / "gsc.json"
    ga4_export = tmp_path / "ga4.json"
    call_export = tmp_path / "calls.json"
    gsc_export.write_text(json_dumps([{"query": "missing metrics"}]))
    ga4_export.write_text(json_dumps([{"metric_name": "unknown_metric", "value": "n/a"}]))
    call_export.write_text(json_dumps([]))
    monkeypatch.setenv("GSC_EXPORT_PATH", str(gsc_export))
    monkeypatch.setenv("GA4_EXPORT_PATH", str(ga4_export))
    monkeypatch.setenv("CALL_EXPORT_PATH", str(call_export))

    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    raw_dir = tmp_path / "raw"
    collect_gsc(dataset, raw_dir, mode="onboarding_connected")
    collect_ga4(dataset, raw_dir, mode="onboarding_connected")
    collect_calls(dataset, raw_dir, mode="onboarding_connected")

    assert dataset.metrics == []
    missing = {gap.missing_source for gap in dataset.data_gaps}
    assert "Google Search Console" in missing
    assert "Google Analytics 4" in missing
    assert "Call tracking / phone logs" in missing


def test_invalid_third_party_export_creates_gap_not_metric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    export = tmp_path / "similarweb.json"
    export.write_text(json_dumps({"unexpected": "shape"}))
    monkeypatch.setenv("SIMILARWEB_EXPORT_PATH", str(export))
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")

    collect_third_party_sources(dataset, tmp_path / "raw", sources="similarweb")

    assert dataset.metrics == []
    assert any(gap.missing_source == "Similarweb" for gap in dataset.data_gaps)


def test_collect_kai_data_writes_identical_aliases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_public(dataset: AuditDataset, raw_dir: Path) -> None:
        source = dataset.add_source(
            AuditSource(
                source_id="public_homepage",
                name="Homepage crawl",
                tier=SourceTier.PUBLIC_OBSERVED.value,
                access="external",
                retrieved_at=utc_now_iso(),
                used_for="Homepage status",
                source_url="https://example.com",
                artifact_path=str(raw_dir / "homepage.html"),
            )
        )
        dataset.add_metric(
            AuditMetric(
                metric_id="homepage_status_code",
                label="Homepage HTTP status",
                value=200,
                unit="status_code",
                source_id=source.source_id,
                source_tier=source.tier,
            )
        )

    monkeypatch.setattr("scripts.audit.collect.collect_public_site", fake_public)

    collect_kai_data("https://example.com", "Example", tmp_path, workflow="plan")

    assert (tmp_path / "kai-data.json").read_text() == (tmp_path / "audit-data.json").read_text()


def test_kai_data_alias_exports_shared_collector() -> None:
    from kai.source_data import collect_kai_data as alias_collect_kai_data

    assert alias_collect_kai_data is collect_kai_data


def test_cli_flags_call_intended_collectors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    called = []

    def record(name: str):
        def inner(*args, **kwargs):
            called.append(name)

        return inner

    monkeypatch.setattr("scripts.audit.collect.collect_public_site", record("public"))
    monkeypatch.setattr("scripts.audit.collect.collect_pagespeed", record("pagespeed"))
    monkeypatch.setattr("scripts.audit.collect.collect_places", record("places"))
    monkeypatch.setattr("scripts.audit.collect.collect_dataforseo_serp", record("dataforseo"))
    monkeypatch.setattr("scripts.audit.collect.collect_seo_provider", record("seo_provider"))
    monkeypatch.setattr("scripts.audit.collect.collect_gsc", record("gsc"))
    monkeypatch.setattr("scripts.audit.collect.collect_ga4", record("ga4"))
    monkeypatch.setattr("scripts.audit.collect.collect_calls", record("calls"))
    monkeypatch.setattr("scripts.audit.collect.collect_third_party_sources", record("third_party"))
    monkeypatch.setattr(
        "sys.argv",
        [
            "collect.py",
            "--url",
            "https://example.com",
            "--out",
            str(tmp_path),
            "--mode",
            "onboarding_connected",
            "--workflow",
            "audit",
            "--pagespeed",
            "--places",
            "--dataforseo",
            "--seo-provider",
            "auto",
            "--gsc",
            "--ga4",
            "--calls",
            "--third-party-sources",
            "serpapi,similarweb",
            "--keywords",
            "seo audit",
        ],
    )

    assert collect_main() == 0
    assert called == ["public", "pagespeed", "places", "dataforseo", "seo_provider", "gsc", "ga4", "calls", "third_party"]


def json_dumps(value) -> str:
    import json

    return json.dumps(value)
