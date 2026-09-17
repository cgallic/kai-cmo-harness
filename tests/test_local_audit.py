import json
import struct
from pathlib import Path

import pytest

from scripts.local_audit import analysis as A
from scripts.local_audit import dataset_io as D
from scripts.local_audit import pulls


def _webp(frames: int, duration_ms: int) -> bytes:
    chunks = []
    vp8x = bytes([0x12, 0, 0, 0]) + (719).to_bytes(3, "little") + (1279).to_bytes(3, "little")
    chunks.append(b"VP8X" + struct.pack("<I", len(vp8x)) + vp8x)
    anim = b"\x00\x00\x00\x00" + struct.pack("<H", 0)
    chunks.append(b"ANIM" + struct.pack("<I", len(anim)) + anim)
    for _ in range(frames):
        body = b"\x00" * 12 + duration_ms.to_bytes(3, "little") + b"\x00"
        chunks.append(b"ANMF" + struct.pack("<I", len(body)) + body)
    payload = b"WEBP" + b"".join(chunks)
    return b"RIFF" + struct.pack("<I", len(payload)) + payload


def test_webp_animation_counts_frames_and_duration():
    info = A.webp_animation(_webp(87, 80))
    assert info["frames"] == 87
    assert info["duration_s"] == 6.96
    assert (info["width"], info["height"]) == (720, 1280)
    assert info["loop"] == 0


def test_webp_animation_rejects_other_formats():
    with pytest.raises(ValueError):
        A.webp_animation(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)


def test_share_of_clicks_splits_volume_across_vantage_points():
    serps = [
        {"keyword": "coffee roaster", "group": "roaster", "volume": 100, "organic": [(1, "www.a.com"), (2, "b.com")]},
        {"keyword": "coffee roaster", "group": "roaster", "volume": 100, "organic": [(1, "b.com"), (2, "a.com")]},
    ]
    sov = A.share_of_clicks(serps)
    assert sov["roaster"]["a.com"] == sov["roaster"]["b.com"] == 50.0
    assert sov["ALL"] == sov["roaster"]


def test_share_of_clicks_counts_missing_volume_as_default():
    sov = A.share_of_clicks([{"keyword": "x", "group": "g", "volume": None, "organic": [(1, "a.com")]}])
    assert sov["g"]["a.com"] == 100.0


def test_brand_rank_matches_subdomains_and_ignores_others():
    organic = [(1, "yelp.com"), (4, "shop.example.com"), (5, "example.com")]
    assert A.brand_rank(organic, "www.example.com") == 4
    assert A.brand_rank([(1, "notexample.com")], "example.com") is None


def test_email_auth_status():
    status = A.email_auth_status(['"google-site-verification=abc"'], ['"v=DMARC1;p=none;"'], [])
    assert status == {"spf": "missing", "dkim": "missing", "dmarc": "p=none"}
    ok = A.email_auth_status(['"v=spf1 include:_spf.google.com ~all"'], ['"v=DMARC1; p=quarantine"'], ['"v=DKIM1; k=rsa; p=MIGf"'])
    assert ok == {"spf": "present", "dkim": "present", "dmarc": "p=quarantine"}


def test_instagram_post_date_decodes_shortcode():
    assert A.instagram_post_date("DQwn4qsju5o") == "2025-11-07"


def test_dataset_round_trip_and_rerun_replaces_metrics(tmp_path: Path):
    ds = D.load_or_create(tmp_path, mode="sales_external", url="https://example.com", name="Example")
    src = D.replace_source(ds, D.observed_source("page_assets", "Assets", "Page weight", "https://example.com/", "raw/assets.json"))
    D.metric(ds, src, "page_weight::home", "Page weight", 32.1, "MB")
    ds.write(tmp_path)

    again = D.load_or_create(tmp_path, mode="sales_external", url="https://example.com", name="Example")
    assert [m.metric_id for m in again.metrics] == ["page_weight::home"]
    src2 = D.replace_source(again, D.observed_source("page_assets", "Assets", "Page weight", "https://example.com/", "raw/assets.json"))
    D.metric(again, src2, "page_weight::home", "Page weight", 1.8, "MB")
    again.write(tmp_path)

    data = json.loads((tmp_path / "audit-data.json").read_text(encoding="utf-8"))
    assert [m["value"] for m in data["metrics"]] == [1.8]
    assert (tmp_path / "_data-sources.md").exists() and (tmp_path / "_data-gaps.md").exists()


def test_example_config_is_valid(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    cfg = pulls.load_config(str(root / "examples" / "local-audit-config.example.json"))
    for k in cfg["keywords"]:
        assert set(k.get("points", [])) <= set(cfg["points"])
    assert cfg["mode"] in {"sales_external", "onboarding_connected", "internal_demo"}


def test_serp_command_registers_metrics_without_network(tmp_path: Path, monkeypatch):
    cfg = {
        "business": "Example", "domain": "example.com", "mode": "sales_external",
        "points": {"Town": "18.0,-67.0"},
        "keywords": [{"keyword": "coffee roaster", "lang": "en", "group": "roaster", "volume": 100}],
    }
    response = {"tasks": [{"status_code": 20000, "result": [{"items": [
        {"type": "local_pack", "title": "Café Uno"},
        {"type": "organic", "rank_group": 1, "domain": "yelp.com"},
        {"type": "organic", "rank_group": 2, "domain": "www.example.com"},
        {"type": "people_also_ask", "items": [{"title": "Where to buy coffee?"}]},
    ]}]}]}
    run = pulls.Run(cfg, tmp_path)
    monkeypatch.setattr(run.client, "call", lambda path, payload=None, cache=None: (response, "raw/x.json"))
    pulls.cmd_serp(run)
    run.save()
    data = json.loads((tmp_path / "audit-data.json").read_text(encoding="utf-8"))
    values = {m["metric_id"]: m["value"] for m in data["metrics"]}
    assert values["serp_rank::coffee_roaster::town"] == 2
    assert values["share_of_clicks::roaster::example_com"] == pytest.approx(34.9, abs=0.1)
    summary = json.loads((tmp_path / "local-audit" / "serp.json").read_text(encoding="utf-8"))
    assert summary["local_pack_counts"] == [["Café Uno", 1]]
    assert summary["paa"] == [["Where to buy coffee?", 1]]


def _visit(browser="Chrome", urls=(), device="Smartphone", referrer="Google"):
    return {"browserName": browser, "deviceType": device, "referrerName": referrer,
            "actionDetails": [{"type": "action", "url": u} for u in urls]}


def test_matomo_classifies_noise_out_of_real_visits():
    from scripts.local_audit import matomo
    visits = [
        _visit(urls=["https://www.example.com/"]),
        _visit(urls=["https://example.com/order_forms/new", "https://example.com/"]),
        _visit(browser="Headless Chrome", urls=["https://www.example.com/"]),
        _visit(urls=["http://127.0.0.1:37461/order_forms/new"]),
        _visit(urls=["https://shop.example.com/web-pixels@abc/custom/sandbox/modern/products/x"]),
        _visit(urls=["http://203.0.113.10/"]),
    ]
    stats = matomo.summarize(visits, "example.com")
    assert stats["buckets"] == {
        "real visit": 2,
        "automation and bots": 1,
        "developer machine": 1,
        "storefront pixel": 1,
        "other host (staging or origin IP)": 1,
    }
    assert stats["real_visits"] == 2
    assert stats["real_single_page_visits"] == 1
    assert stats["unexpected_hosts"] == [("203.0.113.10", 1)]


def test_matomo_requires_a_token_and_never_defaults_one(monkeypatch):
    from scripts.local_audit import matomo
    monkeypatch.delenv("MATOMO_TOKEN", raising=False)
    with pytest.raises(matomo.MatomoError):
        matomo.api({"base_url": "https://analytics.example.com/index.php", "id_site": 1}, "VisitsSummary.get")
