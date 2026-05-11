"""Google Ads uploader — Google Ads API v17 REST.

Endpoint: POST https://googleads.googleapis.com/v17/customers/{cid}/googleAds:mutate
Body shape: {"mutateOperations": [{<resource>Operation: {create: {...}}}]}

Google Ads requires VIDEO assets to be hosted on YouTube — we register a
YouTubeVideoAsset using a `youtube_video_id` passed via CreativeAsset.external_id.
The actual mp4 upload to YouTube is out of scope for this uploader.

Image assets upload directly as base64-encoded bytes via ImageAsset.

Auth: service-account JWT → OAuth2 access token. Same pattern as
scripts/ads/google.py — code is duplicated here intentionally so this
uploader is import-safe from any CWD. If touched a third time, extract
to scripts/ads/_google_auth.py.

Required env (existing in scripts/ads/google.py):
    GOOGLE_CREDENTIALS_PATH
    GOOGLE_ADS_CUSTOMER_ID
    GOOGLE_ADS_DEVELOPER_TOKEN
Optional:
    GOOGLE_ADS_LOGIN_CUSTOMER_ID   (MCC manager id)
    GOOGLE_ADS_API_VERSION         (default v17)

Policy reference: harness/references/google-ads-policy-reference.md
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


_MIME_TO_GADS_ENUM = {
    "image/jpeg": "IMAGE_JPEG",
    "image/jpg": "IMAGE_JPEG",
    "image/png": "IMAGE_PNG",
    "image/gif": "IMAGE_GIF",
}


def _detect_mime_type(path: Path) -> str:
    """Map a file path to a Google Ads MimeTypeEnum string."""
    mt, _ = mimetypes.guess_type(str(path))
    return _MIME_TO_GADS_ENUM.get(mt or "", "IMAGE_JPEG")

from .base import (
    AdRef,
    AdUploader,
    CreativeAsset,
    CreativeSpec,
    UploadError,
    UploadResult,
)
from .registry import register

API_VERSION = os.getenv("GOOGLE_ADS_API_VERSION", "v17")
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/adwords"
MUTATE_URL_TMPL = (
    "https://googleads.googleapis.com/{version}/customers/{cid}/googleAds:mutate"
)


def _env(name: str, required: bool = True) -> str:
    v = os.getenv(name)
    if required and not v:
        raise UploadError(f"Missing env: {name}")
    return v or ""


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _make_jwt(sa: dict) -> str:
    """Sign an RS256 JWT for the service account.

    DUPLICATE of scripts/ads/google.py:_make_jwt — kept here so this uploader
    works without import-path tricks. If you touch this a third time, extract.
    """
    now = int(time.time())
    payload = {
        "iss": sa["client_email"],
        "scope": SCOPE,
        "aud": sa.get("token_uri", TOKEN_URL),
        "iat": now,
        "exp": now + 3600,
    }
    try:
        import jwt  # PyJWT
        return jwt.encode(payload, sa["private_key"], algorithm="RS256")
    except ImportError:
        pass
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
        claims = _b64url(json.dumps(payload).encode())
        signing_input = f"{header}.{claims}".encode()
        priv = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
        sig = priv.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())  # type: ignore[union-attr,call-arg]
        return f"{header}.{claims}.{_b64url(sig)}"
    except ImportError as e:
        raise UploadError(
            "Google auth needs PyJWT or cryptography. pip install PyJWT cryptography"
        ) from e


def _get_access_token() -> str:
    creds_path = _env("GOOGLE_CREDENTIALS_PATH")
    p = Path(creds_path)
    if not p.exists():
        raise UploadError(f"Service account file not found: {creds_path}")
    sa = json.loads(p.read_text())
    for k in ("client_email", "private_key"):
        if k not in sa:
            raise UploadError(f"Service account JSON missing field: {k}")
    assertion = _make_jwt(sa)
    resp = requests.post(
        sa.get("token_uri", TOKEN_URL),
        data={
            "grant_type": "urn:ietf:params:oauth:grant_type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise UploadError(f"Token exchange returned no access_token: {resp.json()}")
    return token


def _clean_cid(cid: str) -> str:
    return cid.replace("-", "")


def _log_mutation(command: str, entity_id: str, payload: dict, result: dict) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    log_dir = repo_root / "workspace" / "ads" / "mutations"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "google",
        "command": command,
        "entity_id": entity_id,
        "payload": payload,
        "result": result,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


@register("google")
class GoogleUploader(AdUploader):
    platform = "google"

    def __init__(self):
        self.customer_id = _clean_cid(_env("GOOGLE_ADS_CUSTOMER_ID"))
        self.developer_token = _env("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")

    def _mutate_headers(self) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {_get_access_token()}",
            "developer-token": self.developer_token,
            "Content-Type": "application/json",
        }
        if self.login_customer_id:
            h["login-customer-id"] = _clean_cid(self.login_customer_id)
        return h

    def _mutate(self, ops: list[dict], label: str) -> dict:
        url = MUTATE_URL_TMPL.format(version=API_VERSION, cid=self.customer_id)
        resp = requests.post(
            url,
            headers=self._mutate_headers(),
            json={"mutateOperations": ops},
            timeout=60,
        )
        if resp.status_code >= 400:
            raise UploadError(f"Google Ads {label} failed: {resp.status_code} {resp.text}")
        return resp.json()

    def upload_asset(self, asset: CreativeAsset) -> UploadResult:
        approval = self._require_approval_context("upload_asset")
        # YouTube video registration path (no file upload — already on YouTube).
        if asset.kind == "video":
            yt_id = asset.external_id
            if not yt_id:
                raise UploadError(
                    "Google Ads videos must be hosted on YouTube. "
                    "Pass CreativeAsset(kind='video', external_id=<youtube_video_id>). "
                    "Upload the mp4 to YouTube (unlisted is fine) before calling this uploader."
                )
            op = {
                "assetOperation": {
                    "create": {
                        "name": (asset.title or f"yt_video_{yt_id}")[:128],
                        "type": "YOUTUBE_VIDEO",
                        "youtubeVideoAsset": {"youtubeVideoId": yt_id},
                    }
                }
            }
            result = self._mutate([op], label="upload-video")
            resource_name = self._extract_resource_name(result, "assetResult")
            _log_mutation(
                "upload-video",
                resource_name,
                {"youtube_video_id": yt_id, "approval_id": approval.approval_id},
                result,
            )
            return UploadResult(platform="google", kind="video", ref=resource_name, raw=result)

        # Image: upload bytes inline as base64.
        # Field shape verified against googleads/google-ads-python
        # examples/assets/upload_image_asset.py:
        #   asset.image_asset.data       = bytes      (REST: base64-encoded string)
        #   asset.image_asset.file_size  = int
        #   asset.image_asset.mime_type  = MimeTypeEnum string ("IMAGE_JPEG", ...)
        # We omit full_size (height/width) — the API can derive it server-side.
        if asset.path is None:
            raise UploadError("Google Ads image upload_asset requires asset.path")
        raw_bytes = asset.path.read_bytes()
        data_b64 = base64.b64encode(raw_bytes).decode("ascii")
        op = {
            "assetOperation": {
                "create": {
                    "name": (asset.title or asset.path.stem)[:128],
                    "type": "IMAGE",
                    "imageAsset": {
                        "data": data_b64,
                        "fileSize": len(raw_bytes),
                        "mimeType": _detect_mime_type(asset.path),
                    },
                }
            }
        }
        result = self._mutate([op], label="upload-image")
        resource_name = self._extract_resource_name(result, "assetResult")
        _log_mutation(
            "upload-image",
            resource_name,
            {"file": str(asset.path), "approval_id": approval.approval_id},
            result,
        )
        return UploadResult(platform="google", kind="image", ref=resource_name, raw=result)

    def create_ad(
        self,
        adset_id: str,
        creative: CreativeSpec,
        asset: UploadResult,
        execute: bool = False,
    ) -> AdRef:
        if asset.platform != "google":
            raise UploadError(f"Asset platform mismatch: {asset.platform!r} for Google uploader")

        ad_group_resource = (
            adset_id
            if adset_id.startswith("customers/")
            else f"customers/{self.customer_id}/adGroups/{adset_id}"
        )

        # Google Ads ads need many fields. We support two minimal shapes:
        # - VIDEO_RESPONSIVE_AD when asset is a YouTube video
        # - RESPONSIVE_DISPLAY_AD when asset is an image (with companion fields)
        # Callers can pass additional fields via creative.extras to fill in
        # marketing_images, square_images, logo_images, headlines, descriptions,
        # long_headline, business_name — required for full ad creation.
        ad_payload: dict[str, Any] = {"finalUrls": [creative.link]}

        headlines = creative.extras.get("headlines") or [{"text": creative.headline[:30]}]
        descriptions = creative.extras.get("descriptions") or [{"text": creative.description[:90]}]
        long_headline = creative.extras.get("long_headline") or {"text": creative.headline[:90]}
        business_name = creative.extras.get("business_name") or "KaiCalls"

        if asset.kind == "video":
            ad_payload["videoResponsiveAd"] = {
                "videos": [{"asset": asset.ref}],
                "headlines": headlines,
                "descriptions": descriptions,
                "longHeadlines": [long_headline],
                "callToActions": creative.extras.get("calls_to_action")
                    or [{"text": "Learn more"}],
                "businessName": business_name,
            }
        else:
            # Responsive Display Ad needs marketing + square + (optionally) logo images.
            # Caller is expected to upload those separately and pass resource_names.
            marketing_images = (
                creative.extras.get("marketing_image_resources")
                or [{"asset": asset.ref}]
            )
            square_images = creative.extras.get("square_image_resources") or marketing_images
            ad_payload["responsiveDisplayAd"] = {
                "headlines": headlines,
                "descriptions": descriptions,
                "longHeadline": long_headline,
                "businessName": business_name,
                "marketingImages": marketing_images,
                "squareMarketingImages": square_images,
            }
            if creative.extras.get("logo_image_resources"):
                ad_payload["responsiveDisplayAd"]["logoImages"] = creative.extras["logo_image_resources"]

        op = {
            "adGroupAdOperation": {
                "create": {
                    "adGroup": ad_group_resource,
                    "status": "PAUSED",
                    "ad": ad_payload,
                }
            }
        }

        if not execute:
            url = MUTATE_URL_TMPL.format(version=API_VERSION, cid=self.customer_id)
            return AdRef(
                platform="google",
                ad_id="",
                adset_id=ad_group_resource,
                status="DRY_RUN",
                raw={"would_post": url, "body": {"mutateOperations": [op]}},
            )

        approval = self._require_approval_context("create_ad")
        result = self._mutate([op], label="create-ad")
        resource_name = self._extract_resource_name(result, "adGroupAdResult")
        _log_mutation(
            "create-ad",
            resource_name,
            {"operation": op, "approval_id": approval.approval_id},
            result,
        )
        return AdRef(
            platform="google",
            ad_id=resource_name,
            adset_id=ad_group_resource,
            status="PAUSED",
            raw=result,
        )

    @staticmethod
    def _extract_resource_name(mutate_result: dict, result_key: str) -> str:
        """Pull resource_name out of a googleAds:mutate response.

        Response shape:
            {"mutateOperationResponses": [{"<result_key>": {"resourceName": "..."}}]}
        """
        for r in mutate_result.get("mutateOperationResponses", []):
            sub = r.get(result_key) or {}
            rn = sub.get("resourceName")
            if rn:
                return rn
        raise UploadError(
            f"Google Ads mutate response missing resourceName for {result_key}: {mutate_result}"
        )
