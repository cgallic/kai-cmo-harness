"""Platform-agnostic ad uploader layer.

Wraps the existing per-platform CLIs (meta.py, google.py, linkedin.py, ...) so
the video-ad pipeline can call one interface regardless of destination.

Public surface:
    from scripts.ads.uploaders import get_uploader, CreativeAsset, UploadResult

    uploader = get_uploader("meta")
    asset_ref = uploader.upload_asset(CreativeAsset(path="/tmp/clip.mp4", kind="video"))
    ad_ref    = uploader.create_ad(adset_id="123", creative=spec, asset=asset_ref, execute=False)

The top-level `scripts.ads.upload` CLI does not call `upload_asset` during
dry-run. Live upload/create flows require an approval id and still land PAUSED,
awaiting a separate activation approval.
"""

from .base import (
    AdRef,
    AdUploader,
    ApprovalContext,
    CreativeAsset,
    CreativeSpec,
    UploadError,
    UploadResult,
)
from .registry import get_uploader, list_platforms

__all__ = [
    "AdUploader",
    "ApprovalContext",
    "CreativeAsset",
    "CreativeSpec",
    "UploadResult",
    "AdRef",
    "UploadError",
    "get_uploader",
    "list_platforms",
]
