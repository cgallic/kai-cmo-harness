"""Platform-agnostic ad uploader layer.

Wraps the existing per-platform CLIs (meta.py, google.py, linkedin.py, ...) so
the video-ad pipeline can call one interface regardless of destination.

Public surface:
    from scripts.ads.uploaders import get_uploader, CreativeAsset, UploadResult

    uploader = get_uploader("meta")
    asset_ref = uploader.upload_asset(CreativeAsset(path="/tmp/clip.mp4", kind="video"))
    ad_ref    = uploader.create_ad(adset_id="123", creative=spec, asset=asset_ref, execute=False)

All `create_ad` calls default `execute=False` (dry-run). Pass `execute=True`
to actually publish — and even then the ad lands PAUSED, awaiting human approval.
"""

from .base import AdUploader, CreativeAsset, CreativeSpec, UploadResult, AdRef, UploadError
from .registry import get_uploader, list_platforms

__all__ = [
    "AdUploader",
    "CreativeAsset",
    "CreativeSpec",
    "UploadResult",
    "AdRef",
    "UploadError",
    "get_uploader",
    "list_platforms",
]
