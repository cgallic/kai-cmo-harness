"""LinkedIn Ads uploader — Marketing API (Videos API + Creatives API).

Per https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api
and https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives

Required headers on all calls:
    LinkedIn-Version: YYYYMM (we default to 202604)
    X-Restli-Protocol-Version: 2.0.0
    Authorization: Bearer {token}
    Content-Type: application/json (where applicable)

Required env:
    LINKEDINADS_ACCESS_TOKEN
    LINKEDINADS_ACCOUNT_ID         (numeric ad account id used in /rest/adAccounts/{id}/creatives)
    LINKEDINADS_OWNER_URN          (urn:li:organization:N — owns the uploaded video)

Optional env:
    LINKEDINADS_VERSION            (default "202604")

Conventions:
- The `adset_id` parameter on create_ad is the LinkedIn campaign URN
  (urn:li:sponsoredCampaign:N). Plain numeric ids are auto-prefixed.
- Videos are uploaded in 4MB chunks per the spec. We always create with
  uploadCaptions=false / uploadThumbnail=false; subtitles are burn-in.
- Creatives are created with intendedStatus="DRAFT" — equivalent to PAUSED
  on Meta. Human flips to ACTIVE later.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

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

API_BASE = "https://api.linkedin.com/rest"
CHUNK_SIZE = 4 * 1024 * 1024  # 4 MiB per LinkedIn spec


def _env(name: str, required: bool = True) -> str:
    v = os.getenv(name)
    if required and not v:
        raise UploadError(f"Missing env: {name}")
    return v or ""


def _normalize_campaign_urn(campaign: str) -> str:
    if campaign.startswith("urn:li:sponsoredCampaign:"):
        return campaign
    if campaign.isdigit():
        return f"urn:li:sponsoredCampaign:{campaign}"
    raise UploadError(f"Unrecognized LinkedIn campaign id: {campaign!r}")


def _log_mutation(command: str, entity_id: str, payload: dict, result: dict) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    log_dir = repo_root / "workspace" / "ads" / "mutations"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
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


@register("linkedin")
class LinkedInUploader(AdUploader):
    platform = "linkedin"

    def __init__(self):
        self.token = _env("LINKEDINADS_ACCESS_TOKEN")
        self.account_id = _env("LINKEDINADS_ACCOUNT_ID")
        self.owner_urn = _env("LINKEDINADS_OWNER_URN")
        self.version = os.getenv("LINKEDINADS_VERSION", "202604")

    def _headers(self, content_json: bool = True) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self.token}",
            "LinkedIn-Version": self.version,
            "X-Restli-Protocol-Version": "2.0.0",
        }
        if content_json:
            h["Content-Type"] = "application/json"
        return h

    # ------------------------------------------------------------------ video
    def _upload_video(self, path: Path) -> tuple[str, dict]:
        size = path.stat().st_size
        init_body = {
            "initializeUploadRequest": {
                "owner": self.owner_urn,
                "fileSizeBytes": size,
                "uploadCaptions": False,
                "uploadThumbnail": False,
            }
        }
        init_resp = requests.post(
            f"{API_BASE}/videos?action=initializeUpload",
            headers=self._headers(),
            json=init_body,
            timeout=60,
        )
        if init_resp.status_code != 200:
            raise UploadError(f"LinkedIn initializeUpload failed: {init_resp.status_code} {init_resp.text}")
        init = init_resp.json().get("value") or {}
        video_urn = init.get("video")
        upload_token = init.get("uploadToken", "")
        instructions = init.get("uploadInstructions") or []
        if not video_urn or not instructions:
            raise UploadError(f"LinkedIn initializeUpload bad response: {init}")

        etags: list[str] = []
        with open(path, "rb") as f:
            for inst in instructions:
                first = inst["firstByte"]
                last = inst["lastByte"]
                f.seek(first)
                chunk = f.read(last - first + 1)
                put_resp = requests.put(
                    inst["uploadUrl"],
                    data=chunk,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=600,
                )
                if put_resp.status_code != 200:
                    raise UploadError(
                        f"LinkedIn chunk upload failed [{first}-{last}]: "
                        f"{put_resp.status_code} {put_resp.text}"
                    )
                etag = put_resp.headers.get("etag") or put_resp.headers.get("ETag")
                if not etag:
                    raise UploadError(f"LinkedIn chunk upload missing ETag header [{first}-{last}]")
                etags.append(etag.strip('"'))

        finalize_body = {
            "finalizeUploadRequest": {
                "video": video_urn,
                "uploadToken": upload_token,
                "uploadedPartIds": etags,
            }
        }
        fin_resp = requests.post(
            f"{API_BASE}/videos?action=finalizeUpload",
            headers=self._headers(),
            json=finalize_body,
            timeout=60,
        )
        if fin_resp.status_code != 200:
            raise UploadError(f"LinkedIn finalizeUpload failed: {fin_resp.status_code} {fin_resp.text}")

        return video_urn, {"init": init, "finalize_status": fin_resp.status_code}

    # ------------------------------------------------------------------ image
    def _upload_image(self, path: Path) -> tuple[str, dict]:
        # LinkedIn /rest/images?action=initializeUpload returns a single uploadUrl;
        # we PUT the whole file once, then the image URN is immediately usable.
        init_body = {"initializeUploadRequest": {"owner": self.owner_urn}}
        init_resp = requests.post(
            f"{API_BASE}/images?action=initializeUpload",
            headers=self._headers(),
            json=init_body,
            timeout=60,
        )
        if init_resp.status_code != 200:
            raise UploadError(f"LinkedIn image initializeUpload failed: {init_resp.status_code} {init_resp.text}")
        init = init_resp.json().get("value") or {}
        image_urn = init.get("image")
        upload_url = init.get("uploadUrl")
        if not image_urn or not upload_url:
            raise UploadError(f"LinkedIn image initializeUpload bad response: {init}")

        with open(path, "rb") as f:
            put_resp = requests.put(
                upload_url,
                data=f.read(),
                headers={"Content-Type": "application/octet-stream"},
                timeout=300,
            )
        if put_resp.status_code not in (200, 201):
            raise UploadError(f"LinkedIn image PUT failed: {put_resp.status_code} {put_resp.text}")

        return image_urn, {"init": init}

    # ------------------------------------------------------------------ public
    def upload_asset(self, asset: CreativeAsset) -> UploadResult:
        if asset.path is None:
            raise UploadError("LinkedIn upload_asset requires asset.path")

        if asset.kind == "video":
            video_urn, raw = self._upload_video(asset.path)
            _log_mutation("upload-video", video_urn, {"file": str(asset.path)}, raw)
            return UploadResult(platform="linkedin", kind="video", ref=video_urn, raw=raw)

        image_urn, raw = self._upload_image(asset.path)
        _log_mutation("upload-image", image_urn, {"file": str(asset.path)}, raw)
        return UploadResult(platform="linkedin", kind="image", ref=image_urn, raw=raw)

    def create_ad(
        self,
        adset_id: str,
        creative: CreativeSpec,
        asset: UploadResult,
        execute: bool = False,
    ) -> AdRef:
        if asset.platform != "linkedin":
            raise UploadError(f"Asset platform mismatch: {asset.platform!r} for LinkedIn uploader")

        campaign_urn = _normalize_campaign_urn(adset_id)
        author_urn = creative.extras.get("author_urn") or self.owner_urn

        # Build inline ugcPost. Direct Sponsored Content (dscAdAccount) so the
        # post never appears on the company page — it's an ad-only post.
        post = {
            "adContext": {
                "dscAdAccount": f"urn:li:sponsoredAccount:{self.account_id}",
                "dscStatus": "ACTIVE",
            },
            "author": author_urn,
            "commentary": creative.description,
            "visibility": "PUBLIC",
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": True,
            "content": {
                "media": {
                    "title": creative.headline,
                    "id": asset.ref,  # urn:li:video:... or urn:li:image:...
                }
            },
        }
        body = {
            "creative": {
                "inlineContent": {"post": post},
                "campaign": campaign_urn,
                "intendedStatus": "DRAFT",  # LinkedIn's paused-pre-review state
                "name": creative.name,
            }
        }

        url = f"{API_BASE}/adAccounts/{self.account_id}/creatives?action=createInline"

        if not execute:
            return AdRef(
                platform="linkedin",
                ad_id="",
                adset_id=campaign_urn,
                status="DRY_RUN",
                raw={"would_post": url, "body": body},
            )

        resp = requests.post(url, headers=self._headers(), json=body, timeout=60)
        if resp.status_code not in (200, 201):
            raise UploadError(
                f"LinkedIn createInline failed: {resp.status_code} {resp.text}"
            )

        # Per docs: 201 Created with the creative URN in `x-restli-id` response header.
        creative_urn = resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id") or ""
        try:
            result_body = resp.json()
        except json.JSONDecodeError:
            result_body = {"raw_text": resp.text}

        _log_mutation("create-ad", creative_urn, body, result_body)
        return AdRef(
            platform="linkedin",
            ad_id=creative_urn,
            adset_id=campaign_urn,
            status="PAUSED",  # we set DRAFT; surface as PAUSED in our shape
            raw={"headers": dict(resp.headers), "body": result_body},
        )
