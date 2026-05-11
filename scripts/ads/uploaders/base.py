"""ABC + dataclasses for the platform-agnostic ad uploader layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional


AssetKind = Literal["image", "video"]
Platform = Literal["meta", "tiktok", "google", "linkedin", "x", "snapchat", "pinterest", "amazon"]


class UploadError(RuntimeError):
    """Raised when a platform upload or create-ad call fails."""


@dataclass
class ApprovalContext:
    """Human approval metadata required for live paid-media writes."""

    approval_id: str
    evidence: Optional[str] = None
    rollback_reference: Optional[str] = None


@dataclass
class CreativeAsset:
    """A media file to be uploaded to a platform's ad library.

    `kind` decides which platform endpoint is used (image vs video).
    Subtitles, when present, are burned in by the video pipeline before
    upload — the platform receives a single mp4 with captions baked in.

    `external_id` carries a platform-side identifier when the asset already
    lives on an external service. The canonical use is Google Ads videos:
    Google requires videos to be hosted on YouTube, so callers pass the
    youtube_video_id here and `path` may be unset.
    """
    path: Optional[Path] = None
    kind: AssetKind = "image"
    duration_s: Optional[float] = None  # videos only
    aspect_ratio: Optional[str] = None  # "9:16", "1:1", "16:9"
    title: Optional[str] = None  # display name in the platform asset library
    external_id: Optional[str] = None  # YouTube video id, third-party CDN ref, etc.

    def __post_init__(self):
        if self.path is not None:
            self.path = Path(self.path)
            if not self.path.exists():
                raise FileNotFoundError(f"Asset not found: {self.path}")
        elif not self.external_id:
            raise ValueError("CreativeAsset requires either path or external_id")
        if self.kind not in ("image", "video"):
            raise ValueError(f"kind must be 'image' or 'video', got {self.kind!r}")


@dataclass
class CreativeSpec:
    """Platform-neutral creative copy. Each uploader maps these fields onto
    platform-specific creative shapes (Meta object_story_spec, TikTok
    AdInfo, Google ResponsiveDisplayAd, etc.)."""
    name: str
    headline: str
    description: str
    link: str
    cta: str = "LEARN_MORE"  # platforms normalize this; passed through best-effort

    # Optional platform overrides — uploaders may use these if present, ignore otherwise.
    page_id: Optional[str] = None       # Meta: FB page id
    instagram_user_id: Optional[str] = None  # Meta: IG actor id (use instagram_user_id, NOT instagram_actor_id)
    business_id: Optional[str] = None   # Multi-tenant routing key
    extras: dict = field(default_factory=dict)  # Free-form per-platform escape hatch


@dataclass
class UploadResult:
    """Returned by AdUploader.upload_asset — opaque platform-side reference
    that create_ad consumes."""
    platform: str
    kind: AssetKind
    ref: str  # Meta: image_hash or video_id; TikTok: video_id; etc.
    raw: dict  # Full platform response, for debugging.


@dataclass
class AdRef:
    """Returned by AdUploader.create_ad. Status is always PAUSED on creation."""
    platform: str
    ad_id: str
    adset_id: str
    status: Literal["PAUSED", "DRY_RUN"]
    raw: dict


class AdUploader(ABC):
    """Per-platform ad uploader. Default-PAUSED, never auto-publishes.

    Implementations should:
    - Use the platform's existing CLI (scripts/ads/{platform}.py) where possible.
    - Default `execute=False` (dry-run) at the orchestration layer; dry-run must
      not upload assets or create platform objects.
    - Live calls still produce PAUSED ads and must be tied to a human approval id.
    - Append every mutation to workspace/ads/mutations/YYYY-MM-DD.jsonl via the
      underlying CLI's mutation log.
    """

    platform: str  # subclasses set this
    _approval_context: Optional[ApprovalContext] = None

    def set_approval_context(
        self,
        approval_id: str,
        *,
        evidence: Optional[str] = None,
        rollback_reference: Optional[str] = None,
    ) -> None:
        """Attach human approval metadata before any live upload/create call."""
        if not approval_id or not approval_id.strip():
            raise UploadError("Live ad writes require a non-empty approval_id")
        self._approval_context = ApprovalContext(
            approval_id=approval_id.strip(),
            evidence=evidence,
            rollback_reference=rollback_reference,
        )

    def clear_approval_context(self) -> None:
        """Clear approval metadata after a live mutation scope ends."""
        self._approval_context = None

    def _require_approval_context(self, operation: str) -> ApprovalContext:
        """Fail closed when an importer tries a live write without approval."""
        if self._approval_context is None:
            raise UploadError(
                f"{self.platform}.{operation} requires approval context. "
                "Call set_approval_context(approval_id=...) before live writes."
            )
        return self._approval_context

    @abstractmethod
    def upload_asset(self, asset: CreativeAsset) -> UploadResult:
        """Upload an image or video to the platform.

        This method performs a live platform write. Callers must not invoke it
        during dry-run previews.
        """

    @abstractmethod
    def create_ad(
        self,
        adset_id: str,
        creative: CreativeSpec,
        asset: UploadResult,
        execute: bool = False,
    ) -> AdRef:
        """Create a PAUSED ad in the given ad set / ad group.

        execute=False  → dry-run, prints intended payload, returns AdRef with status=DRY_RUN.
        execute=True   → live call, ad lands PAUSED, returns AdRef with status=PAUSED.
                         Human approval is required before flipping to ACTIVE.
        """
