#!/usr/bin/env python3
"""
Reddit Listener — profile-driven.

Loads a JSON profile that specifies: subreddits, trigger keywords, LLM prompt
file, model, and the Discord webhook env var. Fetches /r/<sub>/new.rss for
each sub, keyword-filters new posts, runs an LLM eval against the profile's
prompt template, and posts passing drafts to the profile's Discord webhook.

Usage:
    python reddit_listener.py --profile kaicalls
    python reddit_listener.py --profile kaicalls --dry-run
    python reddit_listener.py --profile kaicalls --profiles-dir ./profiles

Profile JSON schema:
    {
      "name": "kaicalls",
      "subreddits": ["AIReceptionists", "..."],
      "trigger_keywords": ["voice ai", "..."],
      "prompt_file": "kaicalls.prompt.md",
      "model": "gpt-4o-mini",
      "discord_webhook_env": "REDDIT_MONITOR_DISCORD_WEBHOOK_KAICALLS",
      "alert_title": "Reddit Opportunity",
      "seen_limit": 2000,
      "posts_per_sub": 25,
      "content_max_chars": 1200
    }

Prompt file: plain text/markdown with {subreddit}, {title}, {content}
placeholders. Must instruct the model to return JSON with keys pass (bool),
reason (str), angle (str|null), draft_response (str|null).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import feedparser
import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# env loading — try sibling, parent, and repo root in that order
# ---------------------------------------------------------------------------
from dotenv import load_dotenv

_here = Path(__file__).parent
for _candidate in (_here / ".env", _here.parent / ".env", _here.parent.parent / ".env"):
    if _candidate.exists():
        load_dotenv(_candidate)
        break


# ---------------------------------------------------------------------------
# profile loading
# ---------------------------------------------------------------------------
def load_profile(profiles_dir: Path, name: str) -> dict:
    path = profiles_dir / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")
    with open(path) as f:
        profile = json.load(f)

    required = ["subreddits", "trigger_keywords", "prompt_file", "discord_webhook_env"]
    missing = [k for k in required if k not in profile]
    if missing:
        raise ValueError(f"Profile {name} missing required keys: {missing}")

    profile.setdefault("name", name)
    profile.setdefault("model", "gpt-4o-mini")
    profile.setdefault("alert_title", "Reddit Opportunity")
    profile.setdefault("seen_limit", 2000)
    profile.setdefault("posts_per_sub", 25)
    profile.setdefault("content_max_chars", 1200)

    prompt_path = profiles_dir / profile["prompt_file"]
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    profile["_prompt_template"] = prompt_path.read_text(encoding="utf-8")

    return profile


# ---------------------------------------------------------------------------
# seen-post state (per profile)
# ---------------------------------------------------------------------------
def seen_path_for(state_dir: Path, profile_name: str) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f"{profile_name}.json"


def load_seen(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"posts": [], "last_check": None}


def save_seen(path: Path, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# core pipeline
# ---------------------------------------------------------------------------
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
            "author": entry.get("author", "unknown"),
            "published": entry.get("published", ""),
            "content": entry.get("summary", "")[:1500],
        })
    return posts


def collect_candidates(profile: dict, seen_path: Path) -> list[dict]:
    seen = load_seen(seen_path)
    seen_ids = set(seen.get("posts", []))

    candidates = []
    new_seen = list(seen_ids)

    for subreddit in profile["subreddits"]:
        for post in fetch_subreddit(subreddit, profile["posts_per_sub"]):
            if post["id"] in seen_ids:
                continue
            new_seen.append(post["id"])

            text = f"{post['title']} {post['content']}"
            matches = matched_triggers(text, profile["trigger_keywords"])
            if matches:
                post["matched_keywords"] = matches
                candidates.append(post)

    seen["posts"] = new_seen[-profile["seen_limit"]:]
    seen["last_check"] = datetime.now().isoformat()
    save_seen(seen_path, seen)

    return candidates


def llm_eval(client: OpenAI, profile: dict, post: dict) -> dict:
    prompt = profile["_prompt_template"].format(
        subreddit=post["subreddit"],
        title=post["title"],
        content=post["content"][:profile["content_max_chars"]],
    )
    try:
        response = client.chat.completions.create(
            model=profile["model"],
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        text = (response.choices[0].message.content or "").strip()
        return json.loads(text)
    except Exception as exc:
        print(f"    ! eval error: {exc}")
        return {"pass": False, "reason": f"eval error: {exc}", "angle": None, "draft_response": None}


def format_alert(profile: dict, post: dict, result: dict) -> str:
    return (
        f"🎯 **{profile['alert_title']} in r/{post['subreddit']}**\n\n"
        f"**{post['title']}**\n\n"
        f"**Angle:** {result.get('angle')}\n"
        f"**Why:** {result.get('reason')}\n\n"
        f"---\n"
        f"**Draft Response:**\n"
        f"```\n{result.get('draft_response')}\n```\n"
        f"---\n\n"
        f"🔗 {post['url']}"
    )


def post_to_discord(webhook: str, content: str) -> bool:
    try:
        r = requests.post(webhook, json={"content": content}, timeout=10)
        r.raise_for_status()
        return True
    except Exception as exc:
        print(f"    ! discord error: {exc}")
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Reddit Listener (profile-driven)")
    parser.add_argument("--profile", required=True, help="Profile name (filename stem in profiles dir)")
    parser.add_argument("--profiles-dir", default=str(_here / "profiles"), help="Directory with <name>.json profiles")
    parser.add_argument("--state-dir", default=str(_here / ".seen"), help="Directory for per-profile seen-post state")
    parser.add_argument("--dry-run", action="store_true", help="Skip Discord posting; print drafts only")
    args = parser.parse_args()

    profiles_dir = Path(args.profiles_dir)
    state_dir = Path(args.state_dir)

    try:
        profile = load_profile(profiles_dir, args.profile)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    import os as _os  # local import keeps module-level clean
    webhook = _os.environ.get(profile["discord_webhook_env"])
    if not webhook and not args.dry_run:
        print(f"error: {profile['discord_webhook_env']} not set in env (use --dry-run to skip discord)", file=sys.stderr)
        return 2

    seen_path = seen_path_for(state_dir, profile["name"])
    client = OpenAI()

    print(f"[{datetime.now()}] profile={profile['name']} subs={len(profile['subreddits'])} kws={len(profile['trigger_keywords'])}")

    candidates = collect_candidates(profile, seen_path)
    if not candidates:
        print("no keyword matches.")
        return 0

    print(f"found {len(candidates)} keyword matches, running llm eval...")

    passed = []
    for post in candidates:
        print(f"  r/{post['subreddit']} — {post['title'][:60]}...")
        result = llm_eval(client, profile, post)

        if result.get("pass"):
            print(f"    ✓ pass: {result.get('reason')}")
            post["eval"] = result
            passed.append(post)

            alert = format_alert(profile, post, result)
            if args.dry_run or webhook is None:
                print(f"--- alert (dry-run) ---\n{alert}\n-----------------------")
            elif post_to_discord(webhook, alert):
                print("    → posted to discord")
        else:
            print(f"    ✗ reject: {result.get('reason')}")

    print(f"\nresult: {len(passed)}/{len(candidates)} passed eval")
    print(f"ALERTS_JSON:{json.dumps([{'url': p['url'], 'subreddit': p['subreddit'], 'title': p['title']} for p in passed])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
