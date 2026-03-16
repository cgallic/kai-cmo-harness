#!/usr/bin/env python3
"""
Kai Harness — Discord Command Handler

Handles !harness commands from Discord and posts results back to the channel.
Designed to be called by OpenClaw when a message matches the prefix.

Supported commands:
  !harness status                                    — harness status card
  !harness run <format> <site> <keyword>             — full pipeline (async, posts when done)
  !harness brief <site> <keyword>                    — generate brief only
  !harness gate <url_or_recent>                      — gate check on most recent draft
  !harness report [site] [--days=30]                 — performance report
  !harness patterns [site]                           — surface patterns
  !harness queue                                     — show what's pending approval
  !harness help                                      — show commands

Usage (called by OpenClaw agent):
  python3 harness_discord.py --command "run blog kaicalls law firm call answering" --channel 1469307381103198382
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")

VENV_PYTHON = "/opt/cmo-analytics/venv/bin/python3"
HARNESS = "/opt/cmo-analytics/scripts/kai_harness.py"
CONTENT_LOG = "/opt/cmo-analytics/data/content_log.json"
PENDING_DIR = "/opt/cmo-analytics/data/pending_checks"

FORMATS = ["blog", "linkedin", "email-lifecycle", "cold-email", "tiktok", "meta-ads", "google-ads", "press", "seo"]
SITES = ["kaicalls", "buildwithkai", "abp", "meetkai", "connorgallic", "vocalscribe"]


def run_harness(args: list[str], capture: bool = True) -> tuple[int, str]:
    cmd = [VENV_PYTHON, HARNESS] + args
    result = subprocess.run(cmd, capture_output=capture, text=True, timeout=300)
    out = (result.stdout + result.stderr) if capture else ""
    return result.returncode, out


def load_log() -> list:
    if not os.path.exists(CONTENT_LOG):
        return []
    with open(CONTENT_LOG) as f:
        return json.load(f)


def format_status() -> str:
    rc, out = run_harness(["status"])
    log = load_log()
    pending = list(Path(PENDING_DIR).glob("*.json")) if Path(PENDING_DIR).exists() else []
    pending_count = sum(1 for f in pending if json.loads(f.read_text()).get("status") == "pending")

    winners = [e for e in log if e.get("performance_30d", {}).get("grade") == "winner"]
    total = len(log)

    lines = [
        "**🧠 Kai Harness Status**",
        f"Tracked: {total} pieces | Winners: {len(winners)} | Pending 30d checks: {pending_count}",
        "",
        "**Gate Scripts:** ✅ four_us_score · banned_word_check · seo_lint",
        "**Crons:** 2am daily (perf checks) · Mon 2pm (patterns)",
        "",
        f"Run content: `!harness run <format> <site> <keyword>`",
        f"Formats: {', '.join(FORMATS)}",
    ]
    return "\n".join(lines)


def format_report(site: str = "all", days: int = 30) -> str:
    log = load_log()
    if site != "all":
        log = [e for e in log if e.get("site") == site]

    if not log:
        return f"No content tracked for site={site}. Run `!harness run` to start."

    by_grade: dict[str, list] = {"winner": [], "average": [], "underperformer": [], "pending": []}
    for e in log:
        perf = e.get("performance_30d")
        grade = perf.get("grade", "average") if perf else "pending"
        by_grade[grade].append(e)

    lines = [f"**📊 Content Report** — {site} ({days}d)\n"]
    emoji = {"winner": "🏆", "average": "📊", "underperformer": "⚠️", "pending": "⏳"}
    for grade, entries in by_grade.items():
        if entries:
            lines.append(f"{emoji[grade]} **{grade.upper()}** ({len(entries)})")
            for e in entries[:5]:  # cap at 5 per grade for Discord readability
                title = (e.get("title") or e.get("keyword") or "—")[:50]
                lines.append(f"  · [{e.get('site')}] {title}")
            if len(entries) > 5:
                lines.append(f"  · …and {len(entries) - 5} more")
    return "\n".join(lines)


def format_queue() -> str:
    drafts = list(Path("/tmp").glob("harness_draft*.md"))
    brief_file = Path("/tmp/harness_brief.json")

    if not drafts and not brief_file.exists():
        return "No drafts pending. Run `!harness run <format> <site> <keyword>` to generate one."

    lines = ["**📝 Harness Queue**"]
    if brief_file.exists():
        try:
            brief = json.loads(brief_file.read_text())
            lines.append(f"Active brief: [{brief.get('target_site')}] {brief.get('target_keyword')} ({brief.get('format')})")
        except Exception:
            pass

    for d in drafts:
        stat = d.stat()
        age_min = int((datetime.now().timestamp() - stat.st_mtime) / 60)
        lines.append(f"Draft: `{d.name}` — {age_min}m ago")

    lines.append("\nReact ✅ on the approval message in your product channel to publish.")
    return "\n".join(lines)


def format_help() -> str:
    return """\
**🧠 Kai Harness Commands**

`!harness status` — system status + tracked content count
`!harness run <format> <site> <keyword>` — full pipeline (brief → write → gate → approval)
`!harness brief <site> <keyword>` — generate research brief only
`!harness gate` — re-run gate on most recent draft
`!harness report [site]` — 30-day performance report
`!harness patterns [site]` — surface content patterns from winners
`!harness queue` — show pending drafts and approvals
`!harness help` — this message

**Formats:** blog · linkedin · email-lifecycle · cold-email · tiktok · meta-ads · google-ads · press · seo
**Sites:** kaicalls · buildwithkai · abp · meetkai · connorgallic · vocalscribe

**Example:**
`!harness run blog kaicalls law firm answering service after hours`"""


def parse_and_respond(command_str: str, channel_id: str) -> str:
    """Parse a !harness command string and return the response text."""
    parts = command_str.strip().split()
    if not parts:
        return format_help()

    cmd = parts[0].lower()

    if cmd == "help" or cmd == "?":
        return format_help()

    elif cmd == "status":
        return format_status()

    elif cmd == "queue":
        return format_queue()

    elif cmd == "report":
        site = parts[1] if len(parts) > 1 and parts[1] in SITES else "all"
        days = 30
        for p in parts:
            if p.startswith("--days="):
                try:
                    days = int(p.split("=")[1])
                except ValueError:
                    pass
        return format_report(site, days)

    elif cmd == "patterns":
        site = parts[1] if len(parts) > 1 and parts[1] in SITES else "all"
        rc, out = run_harness(["patterns", f"--site={site}"])
        if not out.strip():
            return f"No patterns yet for site={site}. Need at least 3 winners first."
        return f"**📈 Patterns ({site}):**\n```\n{out[:1500]}\n```"

    elif cmd == "gate":
        draft_file = "/tmp/harness_draft.md"
        if not Path(draft_file).exists():
            return "No draft found at `/tmp/harness_draft.md`. Run `!harness run` first."
        keyword_hint = " ".join(parts[1:]) if len(parts) > 1 else "content"
        rc, out = run_harness(["gate", "--file", draft_file, "--keyword", keyword_hint])
        status = "✅ Gate passed." if rc == 0 else "❌ Gate failed."
        return f"**{status}**\n```\n{out[:1200]}\n```"

    elif cmd == "brief":
        if len(parts) < 3:
            return "Usage: `!harness brief <site> <keyword>`\nExample: `!harness brief kaicalls law firm call answering`"
        site = parts[1] if parts[1] in SITES else "meetkai"
        keyword = " ".join(parts[2:])
        rc, out = run_harness(["brief", "--site", site, "--keyword", keyword])
        # Try to parse and format the JSON brief nicely
        try:
            brief_file = Path("/tmp/harness_brief.json")
            if brief_file.exists():
                brief = json.loads(brief_file.read_text())
                lines = [
                    f"**📋 Brief: {keyword}** ({site})",
                    f"Angle: {brief.get('angle', '—')}",
                    f"Hook 1: {brief.get('hook_options', ['—'])[0]}",
                    f"Persona: {brief.get('persona', '—')}",
                    f"Pain: {brief.get('audience_pain', '—')}",
                    f"CTA: {brief.get('cta', '—')}",
                    f"Word count target: {brief.get('word_count_target', '—')}",
                    f"\nFull brief saved to `/tmp/harness_brief.json`",
                    f"Run `!harness run blog {site} {keyword}` to write it.",
                ]
                return "\n".join(lines)
        except Exception:
            pass
        return f"Brief generated.\n```\n{out[:800]}\n```"

    elif cmd == "run":
        if len(parts) < 4:
            return ("Usage: `!harness run <format> <site> <keyword>`\n"
                    "Example: `!harness run blog kaicalls law firm call answering`\n"
                    f"Formats: {', '.join(FORMATS)}")
        fmt = parts[1]
        site = parts[2]

        if fmt not in FORMATS:
            return f"Unknown format `{fmt}`. Valid: {', '.join(FORMATS)}"
        if site not in SITES:
            return f"Unknown site `{site}`. Valid: {', '.join(SITES)}"

        keyword = " ".join(parts[3:])

        # Post "starting" message first
        start_msg = (f"🚀 **Harness running:** `{fmt}` · `{site}` · `{keyword}`\n"
                     f"Pipeline: research brief → write → gate → approval\n"
                     f"ETA: ~2-3 minutes. I'll post the draft here when gate passes.")

        # Run in background — spawn subprocess
        log_file = f"/tmp/harness_run_{datetime.now(timezone.utc).strftime('%H%M%S')}.log"
        bg_cmd = (
            f"cd /opt/cmo-analytics && source venv/bin/activate && "
            f"python3 {HARNESS} run --task {fmt} --site {site} --keyword \"{keyword}\" "
            f"--skip-approval > {log_file} 2>&1 && "
            f"openclaw message send --channel discord --target {channel_id} "
            f"--message \"✅ Harness done: {fmt}/{site}/{keyword}. Draft at /tmp/harness_draft.md. "
            f"Gate report in {log_file}. React ✅ to approve.\""
        )
        subprocess.Popen(bg_cmd, shell=True, executable="/bin/bash")

        return start_msg

    else:
        return f"Unknown command `{cmd}`. Try `!harness help`."


def main():
    parser = argparse.ArgumentParser(description="Kai Harness Discord Handler")
    parser.add_argument("--command", required=True, help="Command string after !harness")
    parser.add_argument("--channel", required=True, help="Discord channel ID to respond to")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    response = parse_and_respond(args.command, args.channel)

    if args.dry_run:
        print(response)
    else:
        # Post to Discord via openclaw
        safe = response.replace('"', "'")
        os.system(f'openclaw message send --channel discord --target {args.channel} --message "{safe}"')


if __name__ == "__main__":
    main()
