"""TikTok Ads uploader — TikTok Marketing API v1.3.

Endpoints (per https://business-api.tiktok.com/portal/docs):
- Video upload: POST /open_api/v1.3/file/video/ad/upload/
    multipart, fields: advertiser_id, upload_type=UPLOAD_BY_FILE,
                       video_file (file), video_signature (md5 hex of file bytes)
    response: {"code":0, "data":[{"video_id":"v0...","width":...,"height":...,
                                  "duration":...,"format":"MP4", ...}]}
- Image upload: POST /open_api/v1.3/file/image/ad/upload/
    multipart, fields: advertiser_id, upload_type=UPLOAD_BY_FILE,
                       image_file (file), image_signature (md5 hex)
    response: {"code":0, "data":{"image_id":"ad-site-i18n-sg/...", ...}}
- Ad create:    POST /open_api/v1.3/ad/create/
    JSON, body: {advertiser_id, adgroup_id, creatives: [{ad_name, ad_format,
                  video_id, image_ids, ad_text, call_to_action,
                  landing_page_url, identity_id, identity_type,
                  display_name, status: "DISABLE"|"ENABLE"}]}

Status enum: "DISABLE" = paused, "ENABLE" = active. We always create as DISABLE.

Required env:
    TIKTOK_ACCESS_TOKEN
    TIKTOK_ADVERTISER_ID
    TIKTOK_IDENTITY_ID         (custom identity id; required for spark/branded ads)
    TIKTOK_IDENTITY_TYPE       (CUSTOMIZED_USER | AUTH_CODE | TT_USER, default CUSTOMIZED_USER)

Policy reference: harness/references/tiktok-ads-policy-reference.md
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from .base import (
    AdRef,
    AdUploader,
    CreativeAsset,
    CreativeSpec,
    UploadError,
    UploadResult,
)
from .registry import register

API_BASE = "https://business-api.tiktok.com/open_api/v1.3"


def _md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _env(name: str, required: bool = True) -> str:
    v = os.getenv(name)
    if required and not v:
        raise UploadError(f"Missing env: {name}")
    return v or ""


def _log_mutation(command: str, entity_id: str, payload: dict, result: dict) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    log_dir = repo_root / "workspace" / "ads" / "mutations"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "tiktok",
        "command": command,
        "entity_id": entity_id,
        "payload": payload,
        "result": result,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


@register("tiktok")
class TikTokUploader(AdUploader):
    platform = "tiktok"

    def __init__(self):
        self.token = _env("TIKTOK_ACCESS_TOKEN")
        self.advertiser_id = _env("TIKTOK_ADVERTISER_ID")

    def _headers_json(self) -> dict[str, str]:
        return {
            "Access-Token": self.token,
            "Content-Type": "application/json",
        }

    def _headers_multipart(self) -> dict[str, str]:
        # Don't set Content-Type — requests sets the multipart boundary itself.
        return {"Access-Token": self.token}

    def upload_asset(self, asset: CreativeAsset) -> UploadResult:
        approval = self._require_approval_context("upload_asset")
        # Verified against AdsMCP/tiktok-ads-mcp-server/src/tiktok_ads_mcp/tiktok_client.py:
        # advertiser_id rides in the URL query string, NOT the multipart body. The
        # MD5 signature is optional (omitted by AdsMCP) but we keep it for upload
        # integrity. Form fields are snake_case: image_file/video_file, upload_type.
        if asset.path is None:
            raise UploadError("TikTok upload_asset requires asset.path (no external_id path)")

        sig = _md5_file(asset.path)
        qs = f"advertiser_id={self.advertiser_id}"

        if asset.kind == "video":
            url = f"{API_BASE}/file/video/ad/upload/?{qs}"
            with open(asset.path, "rb") as f:
                resp = requests.post(
                    url,
                    headers=self._headers_multipart(),
                    data={
                        "upload_type": "UPLOAD_BY_FILE",
                        "video_signature": sig,
                    },
                    files={"video_file": (asset.path.name, f, "video/mp4")},
                    timeout=600,
                )
            body = resp.json()
            if body.get("code") != 0:
                raise UploadError(f"TikTok video upload failed: {body}")
            data = body.get("data") or []
            if not data:
                raise UploadError(f"TikTok video upload empty data: {body}")
            video_id = data[0].get("video_id")
            if not video_id:
                raise UploadError(f"TikTok video upload missing video_id: {body}")
            _log_mutation(
                "upload-video",
                video_id,
                {"file": str(asset.path), "approval_id": approval.approval_id},
                body,
            )
            return UploadResult(platform="tiktok", kind="video", ref=video_id, raw=body)

        # image
        url = f"{API_BASE}/file/image/ad/upload/?{qs}"
        with open(asset.path, "rb") as f:
            resp = requests.post(
                url,
                headers=self._headers_multipart(),
                data={
                    "upload_type": "UPLOAD_BY_FILE",
                    "image_signature": sig,
                },
                files={"image_file": (asset.path.name, f, "image/jpeg")},
                timeout=300,
            )
        body = resp.json()
        if body.get("code") != 0:
            raise UploadError(f"TikTok image upload failed: {body}")
        image_id = (body.get("data") or {}).get("image_id")
        if not image_id:
            raise UploadError(f"TikTok image upload missing image_id: {body}")
        _log_mutation(
            "upload-image",
            image_id,
            {"file": str(asset.path), "approval_id": approval.approval_id},
            body,
        )
        return UploadResult(platform="tiktok", kind="image", ref=image_id, raw=body)

    def create_ad(
        self,
        adset_id: str,  # TikTok adgroup_id
        creative: CreativeSpec,
        asset: UploadResult,
        execute: bool = False,
    ) -> AdRef:
        if asset.platform != "tiktok":
            raise UploadError(f"Asset platform mismatch: {asset.platform!r} for TikTok uploader")

        identity_id = creative.extras.get("identity_id") or os.getenv("TIKTOK_IDENTITY_ID")
        identity_type = (
            creative.extras.get("identity_type")
            or os.getenv("TIKTOK_IDENTITY_TYPE")
            or "CUSTOMIZED_USER"
        )
        if not identity_id:
            raise UploadError(
                "TikTok create_ad requires creative.extras['identity_id'] "
                "(or TIKTOK_IDENTITY_ID env)"
            )

        creative_item: dict[str, Any] = {
            "ad_name": creative.name,
            "ad_text": creative.description,
            "call_to_action": creative.cta,  # SIGN_UP, LEARN_MORE, SHOP_NOW, ...
            "landing_page_url": creative.link,
            "identity_id": identity_id,
            "identity_type": identity_type,
            "status": "DISABLE",  # always paused on creation
        }

        if asset.kind == "video":
            # Video ad needs a cover image; TikTok auto-extracts one if image_ids
            # is empty AND the cover_url is omitted. For reliability, callers
            # SHOULD pass extras['cover_image_id'] from a prior image upload.
            creative_item["ad_format"] = "SINGLE_VIDEO"
            creative_item["video_id"] = asset.ref
            cover = creative.extras.get("cover_image_id")
            if cover:
                creative_item["image_ids"] = [cover]
        else:
            creative_item["ad_format"] = "SINGLE_IMAGE"
            creative_item["image_ids"] = [asset.ref]

        if creative.extras.get("display_name"):
            creative_item["display_name"] = creative.extras["display_name"]

        # Per TikTok docs: advertiser_id is a top-level body field on /ad/create/
        # (NOT a query string param like file uploads).
        body = {
            "advertiser_id": self.advertiser_id,
            "adgroup_id": adset_id,
            "creatives": [creative_item],
        }

        if not execute:
            return AdRef(
                platform="tiktok",
                ad_id="",
                adset_id=adset_id,
                status="DRY_RUN",
                raw={"would_post": f"{API_BASE}/ad/create/", "body": body},
            )

        approval = self._require_approval_context("create_ad")
        resp = requests.post(
            f"{API_BASE}/ad/create/",
            headers=self._headers_json(),
            json=body,
            timeout=60,
        )
        result = resp.json()
        if result.get("code") != 0:
            raise UploadError(f"TikTok ad/create failed: {result}")

        # Response shape: {"code":0, "data":{"ad_ids":["<id>"]}}
        ad_ids = (result.get("data") or {}).get("ad_ids") or []
        if not ad_ids:
            raise UploadError(f"TikTok ad/create returned no ad_ids: {result}")
        ad_id = ad_ids[0]
        _log_mutation(
            "create-ad",
            ad_id,
            {"body": body, "approval_id": approval.approval_id},
            result,
        )
        return AdRef(
            platform="tiktok",
            ad_id=ad_id,
            adset_id=adset_id,
            status="PAUSED",
            raw=result,
        )
