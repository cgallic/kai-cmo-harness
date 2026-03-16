#!/usr/bin/env python3
"""
Ad Loop — Full automated ad iteration pipeline.

1. Pull Meta performance data
2. Flag underperforming ads (CTR, CPL, frequency)
3. Generate copy variants via Kai Harness
4. Render creatives with Remotion
5. Upload to Meta as PAUSED ads
6. Post to Discord for approval

Usage:
  python3 ad_loop.py --site=kaicalls --days=7 --channel=1469307381103198382
  python3 ad_loop.py --site=kaicalls --days=7 --dry-run   # No uploads, just show what would happen
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/cmo-analytics")
from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")

VENV = "/opt/cmo-analytics/venv/bin/python3"
HARNESS = "/opt/cmo-analytics/scripts/kai_harness.py"
AD_FLAG = "/opt/cmo-analytics/scripts/ad_flag.py"
META_CREATE = "/opt/cmo-analytics/scripts/meta_ads_create.py"
SHORTS_STUDIO = "/opt/shorts-studio"
PENDING_DIR = Path("/opt/cmo-analytics/data/pending_ads")
PENDING_DIR.mkdir(parents=True, exist_ok=True)

SITE_LINKS = {
    "kaicalls":    "https://kaicalls.com",
    "abp":         "https://awesomebackyardparties.com",
    "bwk":         "https://buildwithkai.com",
    "vocalscribe": "https://vocalscribe.xyz",
    "meetkai":     "https://meetkai.xyz",
}

CHANNEL_MAP = {
    "kaicalls": "1469307381103198382",
    "abp":      "1469310748290191441",
    "bwk":      "1469307544454566020",
}


def run(cmd, capture=True, check=True):
    r = subprocess.run(cmd, capture_output=capture, text=True)
    if check and r.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(r.stderr, file=sys.stderr)
    return r


def step_flag(days, dry_run):
    """Step 1: Flag underperforming campaigns."""
    print(f"\n{'='*60}")
    print(f"Step 1 — Flagging underperformers (last {days} days)")
    print('='*60)

    r = run([VENV, AD_FLAG, f"--days={days}", "--json"])
    if r.returncode != 0:
        print("Could not fetch Meta data. Check META_ACCESS_TOKEN and META_AD_ACCOUNT_ID.")
        return []

    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        print("No ad data returned — account may have no campaigns yet.")
        return []

    flagged = data.get("flagged", [])
    if not flagged:
        print("✅ No underperforming ads found.")
        return []

    print(f"🚨 {len(flagged)} campaign(s) flagged:")
    for f in flagged:
        print(f"  - {f['name']}: {', '.join(f['flag_reasons'])}")
    return flagged


def step_generate_variants(flagged, site, dry_run):
    """Step 2: Generate 3 copy variants per flagged ad via Harness."""
    print(f"\n{'='*60}")
    print(f"Step 2 — Generating copy variants")
    print('='*60)

    variants = []
    for ad in flagged:
        keyword = ad["name"]  # Use campaign name as seed keyword
        print(f"\nGenerating variants for: {ad['name']}")

        if dry_run:
            # Fake variants for dry run
            variants.append({
                "campaign_id": ad["campaign_id"],
                "campaign_name": ad["name"],
                "headline": f"[DRY RUN] AI Call Answering for Law Firms",
                "description": f"[DRY RUN] 24/7 AI receptionist. Never miss a lead. Try free.",
                "site": site,
                "keyword": keyword,
            })
            print("  [DRY run] Skipping harness, using placeholder copy.")
            continue

        # Run harness in meta-ads mode
        r = run([VENV, HARNESS, "run", "--task=meta-ads",
                 f"--site={site}", f"--keyword={keyword}", "--output=json"])

        if r.returncode != 0 or not r.stdout.strip():
            print(f"  Harness failed for: {keyword}")
            continue

        try:
            output = json.loads(r.stdout)
            headline = output.get("headline", "")
            description = output.get("description", "")
            if headline and description:
                variants.append({
                    "campaign_id": ad["campaign_id"],
                    "campaign_name": ad["name"],
                    "headline": headline,
                    "description": description,
                    "site": site,
                    "keyword": keyword,
                })
                print(f"  ✓ Headline: {headline[:60]}")
                print(f"  ✓ Description: {description[:80]}")
        except json.JSONDecodeError:
            print(f"  Could not parse harness output for: {keyword}")

    return variants


def step_render(variants, dry_run):
    """Step 3: Render Remotion AdCreative for each variant."""
    print(f"\n{'='*60}")
    print(f"Step 3 — Rendering creatives")
    print('='*60)

    output_dir = Path("/tmp/ad_renders")
    output_dir.mkdir(exist_ok=True)
    rendered = []

    for i, v in enumerate(variants):
        out_file = output_dir / f"ad_{i}_{v['site']}.png"
        props = json.dumps({
            "headline": v["headline"],
            "description": v["description"],
            "cta": "Get Started Free",
            "site": v["site"],
            "format": "square",
        })

        if dry_run:
            print(f"  [DRY RUN] Would render: {out_file}")
            v["render_path"] = str(out_file)
            v["rendered"] = False
            rendered.append(v)
            continue

        # Check if AdCreative composition exists
        r = run(["npx", "remotion", "render", "AdCreative", str(out_file),
                 f"--props={props}"], capture=True, check=False)

        if r.returncode == 0:
            print(f"  ✓ Rendered: {out_file}")
            v["render_path"] = str(out_file)
            v["rendered"] = True
        else:
            print(f"  ⚠ Render failed (AdCreative composition not built yet). Using copy-only ad.")
            v["render_path"] = None
            v["rendered"] = False

        rendered.append(v)

    return rendered


def step_upload_and_queue(variants, site, channel_id, dry_run):
    """Step 4: Upload to Meta as PAUSED, save to pending_ads/, post to Discord."""
    print(f"\n{'='*60}")
    print(f"Step 4 — Uploading and queuing for approval")
    print('='*60)

    link = SITE_LINKS.get(site, f"https://{site}.com")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    for i, v in enumerate(variants):
        pending_id = f"ad_{timestamp}_{i}"
        pending_file = PENDING_DIR / f"{pending_id}.json"

        if dry_run:
            record = {**v, "pending_id": pending_id, "status": "pending", "ad_id": None, "dry_run": True}
            pending_file.write_text(json.dumps(record, indent=2))
            print(f"  [DRY RUN] Queued: {pending_id}")
            print(f"    Headline: {v['headline']}")
            print(f"    Description: {v['description']}")
            continue

        # Upload image if rendered
        image_hash = None
        if v.get("render_path") and v.get("rendered"):
            r = run([VENV, META_CREATE, "upload-image", f"--file={v['render_path']}"])
            for line in r.stdout.splitlines():
                if line.startswith("Hash: "):
                    image_hash = line.split("Hash: ")[1].strip()

        # Create creative
        creative_args = [
            VENV, META_CREATE, "create-creative",
            f"--name={pending_id}",
            f"--headline={v['headline']}",
            f"--description={v['description']}",
            f"--link={link}",
            "--cta=LEARN_MORE",
        ]
        if image_hash:
            creative_args.append(f"--image-hash={image_hash}")

        r = run(creative_args)
        creative_id = None
        for line in r.stdout.splitlines():
            if line.startswith("Creative ID: "):
                creative_id = line.split("Creative ID: ")[1].strip()

        # Create paused ad (if we have a campaign/adset)
        ad_id = None
        if creative_id and v.get("campaign_id"):
            # Note: need adset_id — get the first adset for the campaign
            r2 = run([VENV, META_CREATE, "list-adsets", f"--campaign-id={v['campaign_id']}"])
            # In production, parse adset id from output and create ad

        record = {
            **v,
            "pending_id": pending_id,
            "status": "pending",
            "creative_id": creative_id,
            "ad_id": ad_id,
            "image_hash": image_hash,
            "link": link,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        pending_file.write_text(json.dumps(record, indent=2))
        print(f"  ✓ Queued: {pending_id} | Creative: {creative_id}")

    # Post to Discord
    if channel_id:
        _post_discord(list(PENDING_DIR.glob(f"ad_{timestamp}_*.json")), channel_id, dry_run)


def _post_discord(pending_files, channel_id, dry_run):
    """Post pending ads to Discord for approval."""
    if not pending_files:
        return

    lines = ["**🔄 Ad Variants Ready for Approval**\n"]
    for f in pending_files:
        r = json.loads(f.read_text())
        lines.append(f"**{r['pending_id']}**")
        lines.append(f"Campaign: {r.get('campaign_name', 'N/A')}")
        lines.append(f"Headline: {r['headline']}")
        lines.append(f"Description: {r['description']}")
        lines.append(f"Link: {r.get('link', '')}")
        if r.get("dry_run"):
            lines.append("*(dry run — no actual upload)*")
        lines.append("\nReact ✅ to publish, ❌ to discard.\n")

    message = "\n".join(lines)

    try:
        import requests
        token = os.getenv("DISCORD_BOT_TOKEN")
        if token and not dry_run:
            requests.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers={"Authorization": f"Bot {token}", "Content-Type": "application/json"},
                json={"content": message}
            )
            print(f"\n  ✓ Posted to Discord channel {channel_id}")
        else:
            print(f"\n  [Discord message that would be posted]:\n{message}")
    except Exception as e:
        print(f"\n  Discord post failed: {e}")
        print(f"  Message:\n{message}")


def main():
    parser = argparse.ArgumentParser(description="Full ad iteration loop")
    parser.add_argument("--site", default="kaicalls", choices=list(SITE_LINKS.keys()))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--channel", help="Discord channel ID for approval posts")
    parser.add_argument("--dry-run", action="store_true", help="No uploads, no Meta API writes")
    args = parser.parse_args()

    channel = args.channel or CHANNEL_MAP.get(args.site)

    print(f"\nKai Ad Loop — {args.site} | {args.days}d window | {'DRY RUN' if args.dry_run else 'LIVE'}")

    flagged = step_flag(args.days, args.dry_run)
    if not flagged:
        print("\nNothing to do. All ads healthy.")
        return

    variants = step_generate_variants(flagged, args.site, args.dry_run)
    if not variants:
        print("\nNo variants generated.")
        return

    rendered = step_render(variants, args.dry_run)
    step_upload_and_queue(rendered, args.site, channel, args.dry_run)

    print(f"\n{'='*60}")
    print(f"✅ Loop complete. {len(rendered)} variant(s) queued for approval.")
    if not args.dry_run:
        print(f"Check Discord → react ✅ to publish, ❌ to discard.")


if __name__ == "__main__":
    main()
