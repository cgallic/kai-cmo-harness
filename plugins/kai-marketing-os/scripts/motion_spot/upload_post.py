"""Publish a finished video via Upload-Post. DRY-RUN BY DEFAULT.

Posting is public. Run it with --yes only after the account owner has approved THIS post in chat.
  python upload_post.py spec.json            -> prints the resolved payload, sends nothing
  python upload_post.py spec.json --yes      -> uploads, then polls per-platform status

spec.json:
  {"video": "out/Spot_16x9.mp4", "profile": "<your upload-post profile>",
   "platforms": ["youtube", "tiktok", "x", "linkedin", "facebook", "pinterest"],
   "fields": {"title": "...", "youtube_description": "...", "tiktok_title": "...",
              "target_linkedin_page_id": "...", "facebook_page_id": "...", "pinterest_board_id": "..."}}
Page and board ids belong to the client: list them with GET /api/uploadposts/{facebook/pages|linkedin/pages|
pinterest/boards}?profile=<p> and put them in the spec, never in this file.
Key: UPLOAD_POST_API_KEY from the environment only.
"""
import json
import os
import sys
import time

API = "https://api.upload-post.com/api"
DEFAULTS = {"privacyStatus": "public", "categoryId": "28", "privacy_level": "PUBLIC_TO_EVERYONE",
            "post_mode": "DIRECT_POST", "visibility": "PUBLIC", "facebook_media_type": "VIDEO", "async_upload": "true"}


def main() -> None:
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    if not spec.get("profile"):
        sys.exit("spec.json needs a 'profile' (the Upload-Post profile that owns the social accounts)")
    fields = {**DEFAULTS, **spec.get("fields", {})}
    data = [("user", spec["profile"])] + [("platform[]", p) for p in spec["platforms"]] + list(fields.items())
    if "--yes" not in sys.argv:
        print(json.dumps(data, indent=1, ensure_ascii=False))
        print("DRY RUN - re-run with --yes only after the owner approves this post.")
        return
    import requests
    key = os.environ.get("UPLOAD_POST_API_KEY", "").strip()
    if not key:
        sys.exit("UPLOAD_POST_API_KEY is not set")
    h = {"Authorization": f"Apikey {key}"}
    with open(spec["video"], "rb") as f:
        r = requests.post(f"{API}/upload", headers=h, data=data,
                          files={"video": (os.path.basename(spec["video"]), f, "video/mp4")}, timeout=600)
    print(r.status_code, r.text[:500])
    rid = r.json().get("request_id")
    d = {}
    for _ in range(40):
        d = requests.get(f"{API}/uploadposts/status?request_id={rid}", headers=h, timeout=30).json()
        if d.get("status") != "processing":
            break
        time.sleep(15)
    for x in d.get("results", []):
        print(x.get("platform"), x.get("success"), x.get("post_url") or x.get("url") or x.get("error_message"))


if __name__ == "__main__":
    main()
