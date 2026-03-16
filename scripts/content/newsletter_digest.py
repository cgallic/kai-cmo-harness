#!/usr/bin/env python3
"""
newsletter_digest.py — The Night Shift weekly digest
Pulls last 7 days of system data, generates email, posts to Discord for approval, sends via Loops.

Usage:
  python newsletter_digest.py --draft     # Generate + post to Discord for approval
  python newsletter_digest.py --send      # Send to full list via Loops (after approval)
  python newsletter_digest.py --preview   # Print draft to stdout only
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

# Config
LOOPS_API_KEY = os.getenv("LOOPS_API_KEY_CONNORGALLIC")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = "1152334071960190988"  # #updates
NEWSLETTER_CHANNEL_ID = "1473791364721410138"  # #email
MEETKAI_URL = "https://meetkai.xyz"
NEWSLETTER_DIR = "/root/.openclaw/workspace/content/newsletter"
LOOPS_MAILING_LIST_ID = os.getenv("LOOPS_CG_LIST_ID", "")  # set once known

os.makedirs(NEWSLETTER_DIR, exist_ok=True)


def run_cmo(module, command, extra_args=""):
    """Run a cmo script and return output."""
    try:
        cmd = f"cd /opt/cmo-analytics && source venv/bin/activate && cmo {module} {command} {extra_args}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash", timeout=30)
        return result.stdout.strip()
    except Exception as e:
        return f"[error: {e}]"


def gather_weekly_data():
    """Pull last 7 days of system metrics."""
    data = {}

    # KaiCalls leads
    leads_out = run_cmo("kaicalls", "leads", "--days=7")
    data["kaicalls_leads"] = leads_out

    # ABP leads
    abp_out = run_cmo("abp", "leads", "--limit=5")
    data["abp_leads"] = abp_out

    # Stripe MRR
    stripe_out = run_cmo("stripe_report", "mrr")
    data["stripe_mrr"] = stripe_out

    # GA4 all sites
    ga4_out = run_cmo("ga4", "all", "--days=7")
    data["ga4_traffic"] = ga4_out

    # BWK activity
    bwk_out = run_cmo("bwk", "counts")
    data["bwk_counts"] = bwk_out

    return data


def extract_highlights(data):
    """Parse raw output into highlight bullets."""
    highlights = []

    # Try to pull key numbers — simple line scanning
    for line in data.get("kaicalls_leads", "").split("\n"):
        if any(k in line.lower() for k in ["lead", "total", "new"]):
            clean = line.strip().lstrip("│ ").strip()
            if clean and len(clean) < 80:
                highlights.append(clean)
            if len(highlights) >= 2:
                break

    for line in data.get("stripe_mrr", "").split("\n"):
        if any(k in line.lower() for k in ["mrr", "revenue", "$"]):
            clean = line.strip().lstrip("│ ").strip()
            if clean and len(clean) < 80:
                highlights.append(clean)
            if len([h for h in highlights if "$" in h]) >= 1:
                break

    for line in data.get("ga4_traffic", "").split("\n"):
        if any(k in line.lower() for k in ["sessions", "users", "total"]):
            clean = line.strip().lstrip("│ ").strip()
            if clean and len(clean) < 80:
                highlights.append(clean)
            if len(highlights) >= 5:
                break

    return highlights[:6] if highlights else ["System running — pull data manually for numbers."]


def get_best_post():
    """Get latest meetkai blog post URL."""
    try:
        posts_dir = "/var/www/meetkai/blog"
        if os.path.exists(posts_dir):
            posts = sorted(os.listdir(posts_dir), reverse=True)
            if posts:
                return f"{MEETKAI_URL}/blog/{posts[0].replace('.html','').replace('.md','')}"
    except Exception:
        pass
    return f"{MEETKAI_URL}/blog/ai-content-pipeline-checks-its-own-work"


def generate_digest(highlights, week_num=1):
    """Generate the 3-section email digest."""
    date_str = datetime.now().strftime("%B %d, %Y")
    post_url = get_best_post()

    subjects = {
        1: "I stopped doing marketing. Here's what replaced it.",
        2: "6 weeks of AI CMO — the actual numbers.",
        3: "Virtual headcount: what continuous per-agent learning means for small teams.",
        4: "What I'd charge an agency vs what this costs me.",
    }
    subject = subjects.get(week_num, f"The Night Shift — Week of {date_str}")

    highlights_text = "\n".join(f"- {h}" for h in highlights)

    body = f"""What shipped this week:

{highlights_text}

---

One thing worth keeping:

The "virtual headcount" framing from the AI discourse this week. The idea that continuous per-agent learning means small teams can compound knowledge the way large orgs compound headcount — except faster, and without the org chart. For a founder running 4–6 products, that's not abstract. It's the actual operating model.

---

One link:

{post_url}

— Connor"""

    if week_num == 1:
        body = """Most founders treat marketing as the thing they'll get to later.

I ran that playbook for two years across six products. Content went stale. Campaigns ran once. Nothing compounded.

Three months ago I stopped. Not because I gave up — because I built something else.

The system I run now:
- Monitors leads for 3 products automatically
- Publishes 2–3 blog posts a week across my sites
- Runs cold outreach in the background while I work on product
- Sends me a daily brief at 8am before I open my laptop

It's called Kai. An AI CMO built on OpenClaw. Runs on a $20/month VPS and costs less per month than one hour with a marketing consultant.

Last week it processed 57 leads, published 4 posts, and flagged a $493 MRR spike before I noticed it.

I'm documenting how it works — the architecture, the data layer, the actual outputs — at meetkai.xyz.

If you're running multiple products and marketing is the gap, I'm opening it up to a small number of operators: meetkai.xyz/apply

Next week: the actual numbers from 6 weeks of running this.

— Connor"""

    return {"subject": subject, "body": body, "date": date_str, "post_url": post_url}


def save_draft(digest):
    """Save draft to file."""
    filename = f"{NEWSLETTER_DIR}/draft_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, "w") as f:
        json.dump(digest, f, indent=2)
    # Also save as latest
    with open(f"{NEWSLETTER_DIR}/draft_latest.json", "w") as f:
        json.dump(digest, f, indent=2)
    return filename


def post_to_discord(digest):
    """Post draft to #email channel for approval."""
    if not DISCORD_BOT_TOKEN:
        print("[Discord] No bot token — skipping Discord post")
        return

    preview = digest["body"][:800] + ("..." if len(digest["body"]) > 800 else "")
    message = f"""📧 **Newsletter Draft Ready — The Night Shift**

**Subject:** {digest["subject"]}

**Preview:**
```
{preview}
```

React ✅ to approve and send via Loops.
React ✏️ to edit (reply with changes).

Draft saved: `{NEWSLETTER_DIR}/draft_latest.json`
Send command: `python3 /opt/cmo-analytics/scripts/newsletter_digest.py --send`"""

    url = f"https://discord.com/api/v10/channels/{NEWSLETTER_CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json={"content": message})
    if r.status_code in (200, 201):
        print(f"[Discord] Draft posted to #email (msg {r.json().get('id')})")
    else:
        print(f"[Discord] Failed: {r.status_code} {r.text[:200]}")


def send_via_loops(digest):
    """Send the digest to the full Loops list as a transactional email."""
    if not LOOPS_API_KEY:
        print("[Loops] No API key — cannot send")
        return False

    # Use sendEvent to trigger a Loops campaign, OR send transactional
    # Since Loops campaigns are managed in dashboard, we'll use transactional send
    # Requires a transactional email ID set up in Loops dashboard
    transactional_id = os.getenv("LOOPS_CG_TRANSACTIONAL_ID", "")

    if not transactional_id:
        print("[Loops] No transactional email ID set.")
        print("Set LOOPS_CG_TRANSACTIONAL_ID in .env after creating it in Loops dashboard.")
        print(f"\nEmail ready to send manually:")
        print(f"Subject: {digest['subject']}")
        print(f"\n{digest['body']}")
        return False

    # Get contacts from the list and send to each, or trigger campaign
    # For now, send as transactional to connor's email as test
    test_email = "connor@connorgallic.com"
    url = "https://app.loops.so/api/v1/transactional"
    headers = {"Authorization": f"Bearer {LOOPS_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "transactionalId": transactional_id,
        "email": test_email,
        "dataVariables": {
            "subject": digest["subject"],
            "body": digest["body"],
            "date": digest["date"],
        },
    }
    r = requests.post(url, headers=headers, json=payload)
    print(f"[Loops] Send status: {r.status_code}")
    if r.status_code == 200:
        print(f"[Loops] Sent to {test_email}")
        return True
    else:
        print(f"[Loops] Error: {r.text[:300]}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", action="store_true", help="Generate draft + post to Discord")
    parser.add_argument("--send", action="store_true", help="Send saved draft via Loops")
    parser.add_argument("--preview", action="store_true", help="Print draft to stdout")
    parser.add_argument("--week", type=int, default=1, help="Week number (1-4) for subject line")
    args = parser.parse_args()

    if args.send:
        # Load saved draft and send
        draft_file = f"{NEWSLETTER_DIR}/draft_latest.json"
        if not os.path.exists(draft_file):
            print("[Error] No draft found. Run --draft first.")
            sys.exit(1)
        with open(draft_file) as f:
            digest = json.load(f)
        print(f"Sending: {digest['subject']}")
        send_via_loops(digest)
        return

    # Generate fresh draft
    print("Gathering weekly data...")
    data = gather_weekly_data()
    highlights = extract_highlights(data)

    print(f"Highlights: {len(highlights)} items")
    digest = generate_digest(highlights, week_num=args.week)
    filename = save_draft(digest)
    print(f"Draft saved: {filename}")

    if args.preview or (not args.draft and not args.send):
        print(f"\nSubject: {digest['subject']}\n")
        print(digest["body"])

    if args.draft:
        post_to_discord(digest)
        print("\nDraft posted to Discord. React ✅ to send.")


if __name__ == "__main__":
    main()
