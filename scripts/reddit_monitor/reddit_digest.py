#!/usr/bin/env python3
"""
Reddit Digest — scores posts for comment-worthiness and publishes a daily
review PAGE instead of auto-drafting replies.

Difference from reddit_listener.py:
  - The LLM returns a numeric fit score (0-100) + one-line reason + one-line
    angle. It does NOT write a draft reply. Connor writes the comment himself.
  - Only posts scoring >= score_threshold are kept, sorted high-to-low, capped.
  - Output is an HTML page (served over http) that accumulates the day's finds,
    plus a single Discord ping per day linking to it.

Run it often (hourly); dedup via the seen-file means each post is scored once,
and the day's page just grows. Discord is pinged only on the first run of the
day that has at least one find.

    python reddit_digest.py --profile kaicalls-digest
    python reddit_digest.py --profile kaicalls-digest --dry-run --out-dir /tmp/rd
"""

import argparse
import html
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import feedparser
import requests
from openai import OpenAI
from dotenv import load_dotenv

_here = Path(__file__).parent
for _candidate in (_here / ".env", _here.parent / ".env", _here.parent.parent / ".env"):
    if _candidate.exists():
        load_dotenv(_candidate)
        break


# --------------------------------------------------------------------------- #
# profile
# --------------------------------------------------------------------------- #
def load_profile(profiles_dir: Path, name: str) -> dict:
    path = profiles_dir / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")
    profile = json.loads(path.read_text(encoding="utf-8"))

    required = ["subreddits", "trigger_keywords", "prompt_file", "discord_webhook_env"]
    missing = [k for k in required if k not in profile]
    if missing:
        raise ValueError(f"Profile {name} missing required keys: {missing}")

    profile.setdefault("name", name)
    profile.setdefault("model", "gpt-4o-mini")
    profile.setdefault("page_title", "Reddit opportunities")
    profile.setdefault("seen_limit", 4000)
    profile.setdefault("posts_per_sub", 25)
    profile.setdefault("content_max_chars", 1200)
    profile.setdefault("score_threshold", 70)
    profile.setdefault("max_items", 12)

    prompt_path = profiles_dir / profile["prompt_file"]
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    profile["_prompt_template"] = prompt_path.read_text(encoding="utf-8")
    return profile


# --------------------------------------------------------------------------- #
# small json state helpers
# --------------------------------------------------------------------------- #
def read_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# fetch + filter
# --------------------------------------------------------------------------- #
def matched_triggers(text: str, keywords: list[str]) -> list[str]:
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]


def fetch_subreddit(subreddit: str, limit: int) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/new.rss"
    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        print(f"  ! error fetching r/{subreddit}: {exc}")
        return []
    posts = []
    for entry in feed.entries[:limit]:
        posts.append({
            "id": entry.id,
            "title": entry.title,
            "url": entry.link,
            "subreddit": subreddit,
            "content": entry.get("summary", "")[:1500],
        })
    return posts


def collect_candidates(profile: dict, seen_path: Path) -> list[dict]:
    seen = read_json(seen_path, {"posts": [], "last_check": None})
    seen_ids = set(seen.get("posts", []))
    new_seen = list(seen_ids)

    candidates = []
    for subreddit in profile["subreddits"]:
        for post in fetch_subreddit(subreddit, profile["posts_per_sub"]):
            if post["id"] in seen_ids:
                continue
            new_seen.append(post["id"])
            text = f"{post['title']} {post['content']}"
            if matched_triggers(text, profile["trigger_keywords"]):
                candidates.append(post)

    seen["posts"] = new_seen[-profile["seen_limit"]:]
    seen["last_check"] = datetime.now().isoformat()
    write_json(seen_path, seen)
    return candidates


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #
def llm_score(client: OpenAI, profile: dict, post: dict) -> dict:
    prompt = profile["_prompt_template"].format(
        subreddit=post["subreddit"],
        title=post["title"],
        content=post["content"][:profile["content_max_chars"]],
    )
    try:
        resp = client.chat.completions.create(
            model=profile["model"],
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        data = json.loads((resp.choices[0].message.content or "").strip())
        return {
            "score": int(data.get("score", 0)),
            "reason": (data.get("reason") or "").strip(),
            "angle": (data.get("angle") or "").strip(),
        }
    except Exception as exc:
        print(f"    ! score error: {exc}")
        return {"score": 0, "reason": f"score error: {exc}", "angle": ""}


# --------------------------------------------------------------------------- #
# html page
# --------------------------------------------------------------------------- #
def score_class(score: int) -> str:
    if score >= 90:
        return "s-hot"
    if score >= 80:
        return "s-good"
    return "s-ok"


def render_html(profile: dict, items: list[dict], day: str) -> str:
    cards = []
    for it in items:
        sc = int(it["score"])
        cards.append(f"""
      <article class="card">
        <div class="badge {score_class(sc)}">{sc}</div>
        <div class="body">
          <div class="sub">r/{html.escape(it['subreddit'])}</div>
          <a class="title" href="{html.escape(it['url'])}" target="_blank" rel="noopener">{html.escape(it['title'])}</a>
          <div class="why"><span>Why</span> {html.escape(it.get('reason',''))}</div>
          <div class="angle"><span>Angle</span> {html.escape(it.get('angle',''))}</div>
        </div>
      </article>""")
    body = "\n".join(cards) if cards else '<p class="empty">No comment-worthy threads found yet today.</p>'
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(profile['page_title'])} — {day}</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font:16px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         background:#0d1117; color:#e6edf3; padding:24px; }}
  header {{ max-width:820px; margin:0 auto 18px; }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .meta {{ color:#8b949e; font-size:13px; }}
  main {{ max-width:820px; margin:0 auto; display:flex; flex-direction:column; gap:12px; }}
  .card {{ display:flex; gap:14px; background:#161b22; border:1px solid #30363d;
          border-radius:10px; padding:14px 16px; }}
  .badge {{ flex:0 0 46px; height:46px; border-radius:8px; display:flex; align-items:center;
           justify-content:center; font-weight:700; font-size:17px; color:#0d1117; }}
  .s-hot {{ background:#3fb950; }} .s-good {{ background:#d29922; }} .s-ok {{ background:#58a6ff; }}
  .body {{ flex:1; min-width:0; }}
  .sub {{ color:#8b949e; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
  .title {{ display:block; color:#e6edf3; font-weight:600; font-size:16px; text-decoration:none; margin:2px 0 8px; }}
  .title:hover {{ color:#58a6ff; text-decoration:underline; }}
  .why, .angle {{ font-size:14px; color:#c9d1d9; margin-top:3px; }}
  .why span, .angle span {{ display:inline-block; min-width:46px; color:#8b949e; font-size:11px;
            text-transform:uppercase; letter-spacing:.04em; }}
  .empty {{ color:#8b949e; text-align:center; padding:40px; }}
  footer {{ max-width:820px; margin:24px auto 0; color:#6e7681; font-size:12px; }}
</style>
</head>
<body>
  <header>
    <h1>{html.escape(profile['page_title'])}</h1>
    <div class="meta">{day} &middot; {len(items)} threads worth a comment &middot; updated {updated}</div>
  </header>
  <main>{body}
  </main>
  <footer>Scored by fit (90+ = direct, 80s = strong, 70s = worth a look). You write the comment.</footer>
</body>
</html>"""


def post_to_discord(webhook: str, content: str) -> bool:
    try:
        r = requests.post(webhook, json={"content": content}, timeout=10)
        r.raise_for_status()
        return True
    except Exception as exc:
        print(f"    ! discord error: {exc}")
        return False


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Reddit Digest (scored review page)")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--profiles-dir", default=str(_here / "profiles"))
    ap.add_argument("--state-dir", default=str(_here / ".seen"))
    ap.add_argument("--out-dir", default="/srv/video-visuals/reddit-opps",
                    help="dir served over http; page written here")
    ap.add_argument("--base-url", default="http://agent:8090/reddit-opps",
                    help="public url that maps to --out-dir")
    ap.add_argument("--dry-run", action="store_true", help="no discord; still writes page")
    ap.add_argument("--min-score", type=int, default=None, help="override score_threshold")
    args = ap.parse_args()

    try:
        profile = load_profile(Path(args.profiles_dir), args.profile)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    threshold = args.min_score if args.min_score is not None else profile["score_threshold"]
    out_dir = Path(args.out_dir)
    data_dir = out_dir / "data"
    seen_path = Path(args.state_dir) / f"{profile['name']}.json"

    webhook = os.environ.get(profile["discord_webhook_env"])
    if not webhook and not args.dry_run:
        print(f"error: {profile['discord_webhook_env']} not set (use --dry-run)", file=sys.stderr)
        return 2

    client = OpenAI()
    day = date.today().isoformat()

    print(f"[{datetime.now()}] profile={profile['name']} subs={len(profile['subreddits'])} "
          f"thr={threshold} day={day}")

    candidates = collect_candidates(profile, seen_path)
    print(f"found {len(candidates)} new keyword matches, scoring...")

    fresh = []
    for post in candidates:
        res = llm_score(client, profile, post)
        mark = "✓" if res["score"] >= threshold else "·"
        print(f"  {mark} {res['score']:>3}  r/{post['subreddit']} — {post['title'][:55]}")
        if res["score"] >= threshold:
            post.update(res)
            post["found_at"] = datetime.now().isoformat()
            fresh.append(post)

    # accumulate into today's bucket (so frequent runs grow one page)
    bucket_path = data_dir / f"{day}.json"
    bucket = read_json(bucket_path, [])
    have = {b["url"] for b in bucket}
    added = [p for p in fresh if p["url"] not in have]
    bucket.extend({
        "score": p["score"], "reason": p["reason"], "angle": p["angle"],
        "subreddit": p["subreddit"], "title": p["title"], "url": p["url"],
        "found_at": p["found_at"],
    } for p in added)
    bucket.sort(key=lambda b: b["score"], reverse=True)
    bucket = bucket[:profile["max_items"]]
    write_json(bucket_path, bucket)

    # render page (dated archive + index = latest)
    page_html = render_html(profile, bucket, day)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{day}.html").write_text(page_html, encoding="utf-8")
    (out_dir / "index.html").write_text(page_html, encoding="utf-8")

    print(f"added {len(added)} new (today total {len(bucket)}) → {out_dir/'index.html'}")

    # one discord ping per day, only when there's something to look at
    ping_path = data_dir / "last_ping.json"
    last_ping = read_json(ping_path, {"date": None}).get("date")
    if added and last_ping != day and webhook and not args.dry_run:
        url = f"{args.base_url}/{day}.html"
        msg = (f"📋 **Reddit opportunities — {day}**\n"
               f"{len(bucket)} threads worth a comment today. You write the reply.\n{url}")
        if post_to_discord(webhook, msg):
            write_json(ping_path, {"date": day})
            print(f"→ pinged discord: {url}")
    elif args.dry_run:
        print(f"(dry-run) would link: {args.base_url}/{day}.html")

    return 0


if __name__ == "__main__":
    sys.exit(main())
