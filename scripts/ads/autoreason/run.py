"""CLI for the AutoReason ad loop.

Usage:
    python -m scripts.ads.autoreason.run --site=kaicalls --use-fixture --dry-run
    python -m scripts.ads.autoreason.run --site=kaicalls            # live + post
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load repo .env before importing modules that read env at import time
REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env")

import requests  # noqa: E402

from . import knowledge  # noqa: E402
from .loop import run_loop  # noqa: E402
from .trace import AdCopy, format_discord_trace, trace_to_json  # noqa: E402

DISCORD_MSG_CAP = 1900  # leave headroom under the 2000 hard cap


def _post_discord(channel_id: str, content: str, dry_run: bool) -> None:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if dry_run or not token:
        if dry_run:
            print("\n[DRY RUN — Discord message that WOULD post]:\n")
        else:
            print("\n[no DISCORD_BOT_TOKEN — message that WOULD post]:\n")
        print(content)
        return

    # Chunk the message at line boundaries to stay under Discord's 2000-char cap
    chunks: list[str] = []
    buf = ""
    for line in content.split("\n"):
        if len(buf) + len(line) + 1 > DISCORD_MSG_CAP and buf:
            chunks.append(buf)
            buf = line
        else:
            buf = (buf + "\n" + line) if buf else line
    if buf:
        chunks.append(buf)

    for chunk in chunks:
        r = requests.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers={
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json",
                "User-Agent": "kai-cmo-harness/autoreason 1.0",
            },
            json={"content": chunk},
            timeout=30,
        )
        if r.status_code >= 300:
            print(f"Discord post failed ({r.status_code}): {r.text}", file=sys.stderr)
            return
    print(f"\n  ✓ Posted {len(chunks)} message(s) to Discord channel {channel_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoReason ad loop — pilot runner")
    parser.add_argument("--site", default="kaicalls", choices=["kaicalls"],
                        help="Brand to run on. KaiCalls only for the pilot.")
    parser.add_argument("--ad-set-id", default=None,
                        help="Specific ad set id. If omitted, auto-picks lowest-CTR active KaiCalls ad set.")
    parser.add_argument("--use-fixture", action="store_true",
                        help="Use the built-in fixture instead of live Meta data (good for dry runs).")
    parser.add_argument("--max-passes", type=int, default=5,
                        help="Hard cap on tournament passes (paper avg 3.9).")
    parser.add_argument("--rng-seed", type=int, default=None,
                        help="Optional RNG seed for label-shuffling reproducibility.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print Discord message instead of posting it.")
    parser.add_argument("--discord-channel",
                        default=os.environ.get("AUTOREASON_DISCORD_CHANNEL"),
                        help="Discord channel id for the trace post. "
                             "Defaults to $AUTOREASON_DISCORD_CHANNEL.")
    parser.add_argument("--json-out", default=None,
                        help="Optional path to write the full per-pass trace JSON.")
    args = parser.parse_args()

    # Build the knowledge bundle
    if args.use_fixture:
        bundle = knowledge.fixture_bundle()
    else:
        try:
            bundle = knowledge.live_bundle()
        except RuntimeError as e:
            print(f"Live Meta load failed: {e}", file=sys.stderr)
            print("Falling back to fixture. Pass --use-fixture explicitly to silence this.",
                  file=sys.stderr)
            bundle = knowledge.fixture_bundle()

    print(f"\nAutoReason loop — {bundle['ad_set_name']}")
    print(f"  Incumbent headline: {bundle['incumbent'].headline}")
    print(f"  Perf snapshot:      CTR {bundle['perf'].get('ctr')}  CPL {bundle['perf'].get('cpl', 'n/a')}")
    print(f"  Source:             {'FIXTURE' if bundle['is_fixture'] else 'LIVE Meta'}")
    print()

    def _on_pass(p):
        print(f"  pass {p.pass_index}: borda={p.borda_by_role}  winner={p.winner_role}")

    winner, passes, reason = run_loop(
        incumbent=bundle["incumbent"],
        perf=bundle["perf"],
        top_ads=bundle["top_ads"],
        bottom_ads=bundle["bottom_ads"],
        max_passes=args.max_passes,
        rng_seed=args.rng_seed,
        on_pass_end=_on_pass,
    )

    print(f"\n{reason}")
    print(f"\nFinal winner:")
    print(json.dumps(winner.to_dict(), indent=2))

    if args.json_out:
        Path(args.json_out).write_text(trace_to_json(passes))
        print(f"\nFull trace JSON: {args.json_out}")

    fixture_banner = "  ⚠ FIXTURE DATA — Meta token needs `ads_read` scope for live runs.\n" if bundle["is_fixture"] else ""
    discord_msg = fixture_banner + format_discord_trace(
        passes=passes,
        ad_set_name=bundle["ad_set_name"],
        winner=winner,
        converged_reason=reason,
    )
    if not args.discord_channel and not args.dry_run:
        print("\nNo --discord-channel and no $AUTOREASON_DISCORD_CHANNEL — skipping post.\n"
              "Re-run with --dry-run to print, or set the channel.", file=sys.stderr)
        return 0
    _post_discord(args.discord_channel or "", discord_msg, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
