"""Unified ad upload CLI — single entrypoint across all platforms.

Usage:
    # Dry-run (default): prints intended payload and never hits the live API.
    python -m scripts.ads.upload \\
        --platform meta \\
        --asset /path/to/clip.mp4 \\
        --kind video \\
        --adset-id 120211234567890 \\
        --name "kaicalls-ugc-2026-04-28" \\
        --headline "Stop missing calls" \\
        --description "AI answers your business line, books the lead, texts you the summary." \\
        --link https://kaicalls.com/?ref=ad \\
        --cta SIGN_UP

    # Live: requires an approval id and still creates the ad in PAUSED state.
    # Human approval is required again to flip ACTIVE.
    python -m scripts.ads.upload --platform meta ... --execute --approval-id act_...

Supported platforms (from registry):
    meta       — implemented
    tiktok     — stub (NotImplementedError)
    google     — stub
    linkedin   — stub
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .uploaders import (
    CreativeAsset,
    CreativeSpec,
    UploadError,
    UploadResult,
    get_uploader,
    list_platforms,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="scripts.ads.upload",
                                description="Upload an asset and create a PAUSED ad.")
    p.add_argument("--platform", required=True, choices=list_platforms(),
                   help="Destination ad platform")
    p.add_argument("--asset", required=True, type=Path, help="Path to image/video file")
    p.add_argument("--kind", required=True, choices=["image", "video"])
    p.add_argument("--adset-id", required=True,
                   help="Meta ad-set id / TikTok ad-group id / Google ad-group resource / LinkedIn campaign URN")
    p.add_argument("--name", required=True, help="Ad name (also used as creative name)")
    p.add_argument("--headline", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--link", required=True)
    p.add_argument("--cta", default="LEARN_MORE")
    p.add_argument("--page-id", default=None, help="Meta: FB page id (or set META_PAGE_ID env)")
    p.add_argument("--instagram-user-id", default=None,
                   help="Meta: IG user id (or set META_INSTAGRAM_USER_ID env)")
    p.add_argument("--business-id", default=None, help="Multi-tenant routing key")
    p.add_argument("--title", default=None, help="Asset title in platform library (default: filename stem)")
    p.add_argument("--aspect", default=None, help="Aspect ratio hint: 9:16 / 1:1 / 16:9")
    p.add_argument("--execute", action="store_true",
                   help="Actually create the ad (still PAUSED). Default: dry-run.")
    p.add_argument("--approval-id", default=None,
                   help="Required with --execute. Links this write to a human-approved action.")
    p.add_argument("--evidence", default=None,
                   help="Optional evidence artifact/snapshot linked to the approval.")
    p.add_argument("--rollback-reference", default=None,
                   help="Optional rollback command or runbook reference for the approved write.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON to stdout")

    args = p.parse_args(argv)

    if args.execute and not args.approval_id:
        print("ERROR: --execute requires --approval-id for auditability", file=sys.stderr)
        return 1

    asset = CreativeAsset(
        path=args.asset,
        kind=args.kind,
        title=args.title,
        aspect_ratio=args.aspect,
    )
    spec = CreativeSpec(
        name=args.name,
        headline=args.headline,
        description=args.description,
        link=args.link,
        cta=args.cta,
        page_id=args.page_id,
        instagram_user_id=args.instagram_user_id,
        business_id=args.business_id,
    )

    uploader = get_uploader(args.platform)
    if args.execute and hasattr(uploader, "set_approval_context"):
        uploader.set_approval_context(
            args.approval_id,
            evidence=args.evidence,
            rollback_reference=args.rollback_reference,
        )

    try:
        if args.execute:
            print(f"[1/2] Uploading {args.kind} to {args.platform}: {args.asset}", file=sys.stderr)
            upload = uploader.upload_asset(asset)
            print(f"      → ref={upload.ref}", file=sys.stderr)
        else:
            print(f"[1/2] Dry-run asset preview for {args.platform}: {args.asset}", file=sys.stderr)
            upload = UploadResult(
                platform=args.platform,
                kind=args.kind,
                ref=f"DRY_RUN_{args.kind.upper()}_REF",
                raw={
                    "dry_run": True,
                    "asset": str(args.asset),
                    "guardrail": "No upload performed without --execute and --approval-id",
                },
            )

        print(f"[2/2] Creating ad in {args.adset_id} (execute={args.execute})", file=sys.stderr)
        ad = uploader.create_ad(args.adset_id, spec, upload, execute=args.execute)
        print(f"      → ad_id={ad.ad_id or '(dry-run)'} status={ad.status}", file=sys.stderr)
    except UploadError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except NotImplementedError as e:
        print(f"NOT IMPLEMENTED: {e}", file=sys.stderr)
        return 2
    finally:
        if args.execute and hasattr(uploader, "clear_approval_context"):
            uploader.clear_approval_context()

    if args.json:
        print(json.dumps({
            "platform": ad.platform,
            "asset_ref": upload.ref,
            "ad_id": ad.ad_id,
            "adset_id": ad.adset_id,
            "status": ad.status,
            "approval_id": args.approval_id,
        }))
    else:
        print(f"\nDone. status={ad.status}")
        if ad.status == "DRY_RUN":
            print("No asset was uploaded. Re-run with --execute --approval-id <id> to create the ad PAUSED.")
        else:
            print(f"Ad {ad.ad_id} is PAUSED. Approve via Discord/console to flip ACTIVE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
