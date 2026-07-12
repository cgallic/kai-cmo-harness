from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ads import upload
from scripts.ads import google as google_cli
from scripts.ads import meta as meta_cli
from scripts.ads.uploaders import AdRef, UploadError, UploadResult
from scripts.ads.uploaders.tiktok import TikTokUploader


class _DummyUploader:
    def __init__(self) -> None:
        self.upload_called = False
        self.create_called = False

    def upload_asset(self, asset):
        self.upload_called = True
        return UploadResult(platform="meta", kind=asset.kind, ref="LIVE_REF", raw={})

    def create_ad(self, adset_id, creative, asset, execute=False):
        self.create_called = True
        return AdRef(
            platform="meta",
            ad_id="ad_1" if execute else "",
            adset_id=adset_id,
            status="PAUSED" if execute else "DRY_RUN",
            raw={"asset_ref": asset.ref, "execute": execute},
        )


def _args(asset: Path, *extra: str) -> list[str]:
    return [
        "--platform", "meta",
        "--asset", str(asset),
        "--kind", "image",
        "--adset-id", "adset_1",
        "--name", "Variant A",
        "--headline", "Answer every call",
        "--description", "AI receptionist for missed calls.",
        "--link", "https://kaicalls.com",
        *extra,
    ]


def test_upload_cli_dry_run_does_not_upload_asset(monkeypatch, tmp_path):
    asset = tmp_path / "ad.png"
    asset.write_bytes(b"fake")
    dummy = _DummyUploader()
    monkeypatch.setattr(upload, "get_uploader", lambda platform: dummy)

    exit_code = upload.main(_args(asset))

    assert exit_code == 0
    assert dummy.upload_called is False
    assert dummy.create_called is True


def test_upload_cli_execute_requires_approval_id(monkeypatch, tmp_path):
    asset = tmp_path / "ad.png"
    asset.write_bytes(b"fake")
    dummy = _DummyUploader()
    monkeypatch.setattr(upload, "get_uploader", lambda platform: dummy)

    exit_code = upload.main(_args(asset, "--execute"))

    assert exit_code == 1
    assert dummy.upload_called is False
    assert dummy.create_called is False


def test_upload_cli_execute_with_approval_uploads_and_creates_paused(monkeypatch, tmp_path):
    asset = tmp_path / "ad.png"
    asset.write_bytes(b"fake")
    dummy = _DummyUploader()
    monkeypatch.setattr(upload, "get_uploader", lambda platform: dummy)

    exit_code = upload.main(_args(asset, "--execute", "--approval-id", "act_123"))

    assert exit_code == 0
    assert dummy.upload_called is True
    assert dummy.create_called is True


def test_google_cli_execute_requires_approval_id_before_credentials():
    args = google_cli.argparse.Namespace(
        type="campaign",
        id="123",
        execute=True,
        approval_id=None,
    )

    assert google_cli.cmd_pause(args) == 1


def test_meta_cli_execute_requires_approval_id_before_api_call():
    args = meta_cli.argparse.Namespace(
        id="123",
        execute=True,
        approval_id=None,
    )

    with pytest.raises(SystemExit) as exc:
        meta_cli.cmd_pause(args)

    assert exc.value.code == 1


def test_meta_campaign_create_rejects_active_status():
    args = meta_cli.argparse.Namespace(
        name="Launch",
        objective="OUTCOME_LEADS",
        special_ad_category=None,
        status="ACTIVE",
        execute=False,
        approval_id=None,
    )

    with pytest.raises(SystemExit) as exc:
        meta_cli.cmd_create_campaign(args)

    assert exc.value.code == 1


def test_meta_campaign_create_disables_adset_budget_sharing(monkeypatch):
    captured = {}
    monkeypatch.setenv("META_AD_ACCOUNT_ID", "act_123")
    monkeypatch.setenv("META_ACCESS_TOKEN", "token")
    monkeypatch.setattr(
        meta_cli,
        "_dry_run_banner",
        lambda method, url, payload: captured.update(payload),
    )
    args = meta_cli.argparse.Namespace(
        name="Leads",
        objective="OUTCOME_LEADS",
        special_ad_category=None,
        status="PAUSED",
        execute=False,
        approval_id=None,
    )

    meta_cli.cmd_create_campaign(args)

    assert captured["is_adset_budget_sharing_enabled"] == "false"


def test_meta_adset_create_uses_lowest_cost_without_cap(monkeypatch):
    captured = {}
    monkeypatch.setenv("META_AD_ACCOUNT_ID", "act_123")
    monkeypatch.setenv("META_ACCESS_TOKEN", "token")
    monkeypatch.setattr(
        meta_cli,
        "_dry_run_banner",
        lambda method, url, payload: captured.update(payload),
    )
    args = meta_cli.argparse.Namespace(
        campaign_id="campaign_1",
        name="Lead test",
        daily_budget="2",
        optimization_goal="OFFSITE_CONVERSIONS",
        targeting='{"geo_locations":{"countries":["US"]}}',
        promoted_object='{"pixel_id":"pixel_1","custom_event_type":"LEAD"}',
        execute=False,
        approval_id=None,
    )

    meta_cli.cmd_create_adset(args)

    assert captured["bid_strategy"] == "LOWEST_COST_WITHOUT_CAP"


def test_tiktok_uploader_upload_asset_requires_approval_context(monkeypatch, tmp_path):
    asset = tmp_path / "ad.png"
    asset.write_bytes(b"fake")
    monkeypatch.setenv("TIKTOK_ACCESS_TOKEN", "token")
    monkeypatch.setenv("TIKTOK_ADVERTISER_ID", "advertiser")

    uploader = TikTokUploader()

    with pytest.raises(UploadError, match="requires approval context"):
        uploader.upload_asset(upload.CreativeAsset(path=asset, kind="image"))
