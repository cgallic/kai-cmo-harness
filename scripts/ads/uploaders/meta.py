"""Meta (Facebook + Instagram) uploader.

Wraps the existing scripts/ads/meta.py CLI by subprocess so we inherit:
- env loading from .env.local
- mutation logging to workspace/ads/mutations/YYYY-MM-DD.jsonl
- the `--execute` dry-run gate
- the proven Marketing API integration

The wrapping CLI is invoked from the repo root as `python scripts/ads/meta.py ...`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from .base import (
    AdRef,
    AdUploader,
    CreativeAsset,
    CreativeSpec,
    UploadError,
    UploadResult,
)
from .registry import register

REPO_ROOT = Path(__file__).resolve().parents[3]
META_CLI = REPO_ROOT / "scripts" / "ads" / "meta.py"


def _run_meta(*args: str, capture: bool = True) -> subprocess.CompletedProcess:
    """Invoke scripts/ads/meta.py with the given args from the repo root.

    The Meta CLI imports `_pull_common` directly (no package), so we must
    chdir into scripts/ads/ before invoking it.
    """
    cmd = [sys.executable, str(META_CLI), *args]
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT / "scripts" / "ads",
        capture_output=capture,
        text=True,
    )
    return proc


def _parse_video_id(stdout: str) -> str:
    """meta.py upload-video prints the full JSON response. Pull `id` out."""
    # The CLI also prints log lines via the `log` helper — those go to stderr.
    # stdout is just the JSON body.
    try:
        body = json.loads(stdout.strip())
    except json.JSONDecodeError as e:
        raise UploadError(f"Could not parse meta.py upload-video output: {e}\n{stdout}")
    vid = body.get("id")
    if not vid:
        raise UploadError(f"upload-video response missing 'id': {body}")
    return vid


def _parse_image_hash(stdout: str) -> str:
    """meta.py upload-image prints the bare image_hash on a line. Last
    non-empty line is the hash (log lines go to stderr)."""
    lines = [ln for ln in stdout.strip().splitlines() if ln.strip()]
    if not lines:
        raise UploadError(f"upload-image returned no stdout")
    return lines[-1].strip()


def _parse_create_ad_id(stdout: str) -> str:
    try:
        body = json.loads(stdout.strip())
    except json.JSONDecodeError as e:
        raise UploadError(f"Could not parse create-ad output: {e}\n{stdout}")
    aid = body.get("id")
    if not aid:
        raise UploadError(f"create-ad response missing 'id': {body}")
    return aid


@register("meta")
class MetaUploader(AdUploader):
    """Upload images/videos and create paused ads on Meta (Facebook + Instagram)."""

    platform = "meta"

    def upload_asset(self, asset: CreativeAsset) -> UploadResult:
        approval = self._require_approval_context("upload_asset")
        title = asset.title or asset.path.stem
        if asset.kind == "video":
            proc = _run_meta(
                "upload-video",
                "--file", str(asset.path),
                "--title", title,
                "--approval-id", approval.approval_id,
            )
            if proc.returncode != 0:
                raise UploadError(f"meta upload-video failed: {proc.stderr or proc.stdout}")
            video_id = _parse_video_id(proc.stdout)
            return UploadResult(
                platform="meta",
                kind="video",
                ref=video_id,
                raw=json.loads(proc.stdout.strip()),
            )

        # image
        proc = _run_meta(
            "upload-image",
            "--file", str(asset.path),
            "--approval-id", approval.approval_id,
        )
        if proc.returncode != 0:
            raise UploadError(f"meta upload-image failed: {proc.stderr or proc.stdout}")
        image_hash = _parse_image_hash(proc.stdout)
        return UploadResult(
            platform="meta",
            kind="image",
            ref=image_hash,
            raw={"hash": image_hash},
        )

    def create_ad(
        self,
        adset_id: str,
        creative: CreativeSpec,
        asset: UploadResult,
        execute: bool = False,
    ) -> AdRef:
        if asset.platform != "meta":
            raise UploadError(f"Asset platform mismatch: {asset.platform!r} for Meta uploader")

        page_id = creative.page_id or os.getenv("META_PAGE_ID")
        if not page_id:
            raise UploadError(
                "creative.page_id (or META_PAGE_ID env) required for Meta ads"
            )

        common_data: dict[str, Any] = {
            "message": creative.description,
            "call_to_action": {
                "type": creative.cta,
                "value": {"link": creative.link},
            },
        }
        if asset.kind == "video":
            thumbnail_hash = asset.raw.get("thumbnail_hash")
            if not thumbnail_hash:
                raise UploadError("Meta video creative requires a thumbnail image/hash")
            object_story_spec: dict[str, Any] = {
                "page_id": page_id,
                "video_data": {
                    **common_data,
                    "video_id": asset.ref,
                    "image_hash": thumbnail_hash,
                    "title": creative.headline,
                },
            }
        else:
            object_story_spec = {
                "page_id": page_id,
                "link_data": {
                    **common_data,
                    "link": creative.link,
                    "name": creative.headline,
                    "image_hash": asset.ref,
                },
            }
        ig_user_id = creative.instagram_user_id or os.getenv("META_INSTAGRAM_USER_ID")
        if ig_user_id:
            # NOTE per harness/references/meta-ads-api-reference.md: use
            # instagram_user_id, NOT instagram_actor_id.
            object_story_spec["instagram_user_id"] = ig_user_id

        creative_payload = {
            "name": creative.name,
            "object_story_spec": object_story_spec,
        }

        meta_args = [
            "create-ad",
            "--adset-id", adset_id,
            "--name", creative.name,
            "--creative-json", json.dumps(creative_payload),
        ]
        if execute:
            approval = self._require_approval_context("create_ad")
            meta_args.append("--execute")
            meta_args.extend(["--approval-id", approval.approval_id])

        proc = _run_meta(*meta_args)
        if proc.returncode != 0:
            raise UploadError(f"meta create-ad failed: {proc.stderr or proc.stdout}")

        if not execute:
            return AdRef(
                platform="meta",
                ad_id="",
                adset_id=adset_id,
                status="DRY_RUN",
                raw={"stdout": proc.stdout, "stderr": proc.stderr},
            )

        ad_id = _parse_create_ad_id(proc.stdout)
        return AdRef(
            platform="meta",
            ad_id=ad_id,
            adset_id=adset_id,
            status="PAUSED",
            raw=json.loads(proc.stdout.strip()),
        )
