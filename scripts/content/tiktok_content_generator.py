#!/usr/bin/env python3
"""
TikTok Content Generator

Reads recent research files → generates 12 TikTok posts via Claude → writes:
  - /opt/cmo-analytics/reports/tiktok_posts.json
  - /var/www/cg/tiktok.html  (live at cg.meetkai.xyz/tiktok.html)

Runs daily via cron after research scan.
"""

import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import openai

# ── Config ──────────────────────────────────────────────────────────────────
RESEARCH_DIR   = "/opt/cmo-analytics/research/learnings"
OUTPUT_JSON    = "/opt/cmo-analytics/reports/tiktok_posts.json"
OUTPUT_HTML    = "/var/www/cg/tiktok.html"
ENV_FILE       = "/opt/cmo-analytics/.env"
MAX_FILES      = 15       # most recent research files to include
MAX_CHARS      = 2500     # chars per file (truncate long ones)
RESEARCH_DAYS  = 7        # look back window

EXAMPLE_POST = """{
  "script": ["ai can now design", "entire working robots", "by itself", "it designs the body", "the movement", "the control system", "then tests thousands", "of versions in simulation", "before one is built"],
  "caption": "researchers demonstrated ai systems that design robot bodies and control policies together using simulation before physical construction. source: mit robotics research / nature machine intelligence / march 2026.",
  "hashtags": "#artificialintelligence #robotics #futureofai #techtok #connorgallic",
  "topic": "ai robotics"
}"""


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_env():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


def get_recent_research() -> tuple[str, list[str]]:
    cutoff = datetime.now() - timedelta(days=RESEARCH_DAYS)
    research_path = Path(RESEARCH_DIR)
    files = sorted(
        research_path.glob("*.md"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    parts: list[str] = []
    used_files: list[str] = []
    for f in files[:MAX_FILES]:
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            if len(text) > MAX_CHARS:
                text = text[:MAX_CHARS] + "\n...[truncated]"
            parts.append(f"=== {f.name} ===\n{text}\n")
            used_files.append(f.name)
        except Exception:
            pass

    content = "\n".join(parts) if parts else "No recent research files found."
    return content, used_files


# ── Generation ────────────────────────────────────────────────────────────────

def _word_count(script_lines: list) -> int:
    return len(" ".join(script_lines).replace("\n", " ").split())


def _validate(posts: list) -> tuple[bool, list[str]]:
    """Validate the 'thesis micro-essay' format (structure only, keep it creative)."""
    issues: list[str] = []
    if not isinstance(posts, list) or len(posts) != 12:
        issues.append(f"expected 12 posts, got {0 if not isinstance(posts, list) else len(posts)}")
        return False, issues

    required_tags = ["#futureofai", "#techtok", "#connorgallic"]

    for idx, p in enumerate(posts, 1):
        script = p.get("script", [])
        if not isinstance(script, list) or not script:
            issues.append(f"post {idx}: missing script")
            continue

        # lowercase check
        for line in script:
            if any(c.isupper() for c in str(line)):
                issues.append(f"post {idx}: uppercase detected")
                break

        joined = " ".join(str(x) for x in script).lower()
        if "fast fast pause" in joined:
            issues.append(f"post {idx}: contains banned phrase fast fast pause")
        if "hack #" in joined:
            issues.append(f"post {idx}: contains banned 'hack #' framing")
        if "comment \"connor\"" in str(p.get("caption", "")).lower():
            issues.append(f"post {idx}: contains banned comment cta")

        # structure
        line_count = len(script)
        if line_count < 7 or line_count > 12:
            issues.append(f"post {idx}: line_count {line_count} outside 7-12")

        wc = _word_count([str(x) for x in script])
        if wc < 28 or wc > 70:
            issues.append(f"post {idx}: word_count {wc} outside 28-70")

        if not any(ch.isdigit() for ch in joined):
            issues.append(f"post {idx}: missing a concrete number/year")

        caption = str(p.get("caption", "")).strip().lower()
        if "follow" not in caption:
            issues.append(f"post {idx}: caption missing follow cta")

        h = str(p.get("hashtags", "")).lower()
        for t in required_tags:
            if t not in h:
                issues.append(f"post {idx}: missing required hashtag {t}")

    return len(issues) == 0, issues


def _auto_fix(posts: list, allowed_sources: list[str], default_source: str) -> list:
    """Enforce the 'thesis micro-essay' format + clean CTAs/hashtags."""
    allowed_lower = [s.lower() for s in (allowed_sources or [])]

    required_tags = ["#futureofai", "#techtok", "#connorgallic"]

    fixed = []
    for p in posts:
        script = p.get("script", [])
        if isinstance(script, str):
            script = [ln.strip() for ln in script.split("\n") if ln.strip()]
        if not isinstance(script, list):
            script = []

        script = [str(x).strip().lower() for x in script if str(x).strip()]

        # Hard remove banned phrases
        script = [ln for ln in script if "fast fast pause" not in ln]
        script = [ln for ln in script if "hack #" not in ln]

        # Chunk lines to 2-6 words
        def chunk_line(line: str) -> list[str]:
            words = line.split()
            if len(words) <= 6:
                return [line]
            out = []
            k = 0
            while k < len(words):
                out.append(" ".join(words[k:k+5]))
                k += 5
            return out

        expanded = []
        for line in script:
            expanded.extend(chunk_line(line))
        script = expanded

        # Enforce 7-12 lines by trimming or padding
        if len(script) > 12:
            script = script[:12]
        while len(script) < 7:
            script.append("what this means")

        # Enforce 35-65 words by padding with meaning lines, not filler junk
        def wc(lines):
            return _word_count(lines)

        # Ensure at least one number
        joined = " ".join(script)
        if not any(ch.isdigit() for ch in joined):
            script.insert(3, "2026 changed this")

        # If still too short, expand existing short lines without increasing line count
        bump = ["right now", "in 2026", "at scale", "for builders"]
        bi = 0
        while wc(script) < 35 and bi < len(bump) * 3:
            phrase = bump[bi % len(bump)].split()
            for j in range(len(script)):
                words = script[j].split()
                if len(words) <= 4:
                    new_words = words + phrase
                    if len(new_words) <= 6:
                        script[j] = " ".join(new_words)
                        if wc(script) >= 35:
                            break
            bi += 1
            # safety break
            if bi > 20:
                break

        # Caption: follow CTA, no comment CTA
        cap = str(p.get("caption", "")).strip().lower()
        cap = cap.replace("comment \"connor\"", "")
        cap = cap.replace("comment 'connor'", "")
        cap = cap.replace("comment connor", "")
        cap = cap.strip()
        if "follow" not in cap:
            # keep it in the style of the examples
            cap = (cap.rstrip(".") + ". follow for what this actually means.").strip()

        # Hashtags: strip discord tokens, enforce required, cap 6
        tags = str(p.get("hashtags", "")).strip().lower()
        tags = " ".join(tok for tok in tags.split() if not (tok.startswith("<#") and tok.endswith(">")))
        for t in required_tags:
            if t not in tags:
                tags = (tags + " " + t).strip()
        # add ai baseline
        if "#artificialintelligence" not in tags:
            tags = (tags + " #artificialintelligence").strip()

        seen = set(); out = []
        for t in tags.split():
            if t.startswith('#') and t not in seen:
                seen.add(t); out.append(t)
        tags = " ".join(out[:6])

        # Source metadata
        src = str(p.get("source", "")).strip().lower()
        if not src or (allowed_lower and src not in allowed_lower):
            src = default_source.lower()

        # Special-case: iran dashboard file is a "tweet → shipped product" post, not geopolitics
        if "aixbt-iran-intel-dashboard" in src or "iran-intel" in src:
            script = [
                "a tweet is a prd now",
                "read that again",
                "someone replied to an ai",
                "build me a dashboard",
                "the agent shipped it",
                "no human wrote code",
                "5 panels live in prod",
                "hourly cron refresh",
                "tweet → app → deploy",
                "this is distribution",
            ]
            cap = "a tweet can trigger a full build deploy cycle. this changes who wins distribution. follow for what this actually means."
            tags = "#futureofai #techtok #connorgallic #artificialintelligence #automation #agents"

        # Final clamp on line count
        if len(script) > 12:
            script = script[:12]
        while len(script) < 7:
            script.append("what this means")

        p["script"] = script
        p["caption"] = cap
        p["hashtags"] = tags
        p["source"] = src
        p["topic"] = str(p.get("topic", "")).strip().lower() or "ai"
        fixed.append(p)

    return fixed


def generate_posts(research_content: str, allowed_sources: list[str]) -> list:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    today = datetime.now().strftime("%B %d, %Y")
    default_source = (allowed_sources[0] if allowed_sources else "internal research")
    allowed_sources_str = "\n".join(f"- {s}" for s in allowed_sources[:25])

    base_prompt = f"""write in the exact format that performs on @connorgallic.

this is the format to mimic (style only):
- the era of bigger ai models / is officially over / ...
- ai agents now have a protocol / ... / it's called agent2agent / ...
- the best ai agent benchmark / humans 92% / ai 61% / ...

turn internal ai research into short thesis posts.

write for smart people who are not engineers.


today: {today}

use only these internal files as facts:
{research_content}

allowed sources (choose one per post):
{allowed_sources_str}

OUTPUT: return ONLY valid json array of 12 objects.

HARD BANS:
- do not use "fast fast pause"
- do not use "hack #"
- do not include comment ctas (no "comment \"connor\"")

SCRIPT RULES:
- all lowercase
- 7 to 12 lines
- 2 to 6 words per line
- total words 30 to 65 (forces rewatch)
- write like a human with a take
- start with a strong thesis line (opinionated)
- include one pattern-break line (e.g. "read that again" / "let that sit")
- repeat the key fragment on its own line
- include at least one concrete number or year
- end with a sharp implication (who wins / what changes / what to do)

TONE (MANDATORY):
- no formal verbs like "introduces" "offers" "utilizes" "enables"
- talk like the examples: blunt, contrarian, slightly provocative
- show the move, not the paperwork

JARGON BAN:
- do not use these words/phrases: primitives, sovereign, multimodal, consolidation loop, ingest, structured memories, at scale, leverage, utilize
- avoid infra-speak unless it's the hook
- if you must mention infra (sqlite, vector db), explain it in human terms in the next line

CAPTION RULES:
- 1 to 3 sentences
- explain what it means in plain language
- include a follow cta like "follow for what this actually means"
- no sources in caption
- no corporate phrasing

HASHTAGS:
- must include #futureofai #techtok #connorgallic
- include #artificialintelligence
- add 1-2 specific tags per post

RETURN FIELDS PER OBJECT:
- script: array of lines
- caption: string
- hashtags: string
- topic: 2-4 words
- source: must be exactly one filename from the allowed sources list
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        temperature=0.4,
        messages=[{"role": "user", "content": base_prompt}]
    )

    response_text = response.choices[0].message.content.strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(line for line in lines if not line.strip().startswith("```"))

    posts = json.loads(response_text)
    if isinstance(posts, list) and len(posts) > 12:
        posts = posts[:12]
    posts = _auto_fix(posts, allowed_sources=allowed_sources, default_source=default_source)
    ok, issues = _validate(posts)
    if not ok:
        raise ValueError("validation failed after auto-fix: " + "; ".join(issues[:10]))

    return posts


# ── Output ────────────────────────────────────────────────────────────────────

def write_json(posts: list):
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    data = {
        "generated_at": datetime.now().isoformat(),
        "count": len(posts),
        "posts": posts
    }
    with open(OUTPUT_JSON, "w") as f:
        json.dump(data, f, indent=2)


def escape_js(s: str) -> str:
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def write_html(posts: list):
    generated_at = datetime.now().strftime("%B %d, %Y · %I:%M %p UTC")

    cards = []
    for i, post in enumerate(posts, 1):
        script_lines = post.get("script", [])
        caption      = post.get("caption", "")
        hashtags     = post.get("hashtags", "")
        topic        = post.get("topic", f"Post {i}")
        source       = post.get("source", "")

        script_text   = "\n".join(script_lines)
        full_caption  = f"{caption}\n{hashtags}"
        script_js     = escape_js(script_text)
        caption_js    = escape_js(full_caption)

        lines_html = "".join(
            f'<div class="script-line">{line}</div>'
            for line in script_lines
        )
        caption_html = full_caption.replace("\n", "<br>")
        source_html  = (f"source file: {source}" if source else "")

        cards.append(f"""
        <div class="post-card" id="post-{i}">
          <div class="post-header">
            <span class="post-num">#{i}</span>
            <span class="post-topic">{topic}</span>
          </div>
          <div class="post-section">
            <div class="section-label">
              TEXT OVERLAY
              <button class="copy-btn" onclick="copyText(`{script_js}`, this)">Copy</button>
            </div>
            <div class="script-block">{lines_html}</div>
          </div>
          <div class="post-section">
            <div class="section-label">
              CAPTION + HASHTAGS
              <button class="copy-btn" onclick="copyText(`{caption_js}`, this)">Copy</button>
            </div>
            <div class="caption-block">{caption_html}<div class="source-note">{source_html}</div></div>
          </div>
          <button class="copy-all-btn" onclick="copyAll(`{script_js}`, `{caption_js}`, this)">
            📋 Copy Everything
          </button>
        </div>""")

    cards_html = "\n".join(cards)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TikTok Content | Kai-CMO</title>
  <style>
    :root {{
      --bg:         #0a0a0f;
      --card:       #12121a;
      --accent:     #00d4aa;
      --accent-dim: rgba(0, 212, 170, 0.15);
      --text:       #e0e0e0;
      --text-dim:   #888;
      --border:     #2a2a3a;
      --tiktok:     #ff2d55;
      --green:      #22c55e;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
    }}
    .container {{ max-width: 1400px; margin: 0 auto; }}

    header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid var(--border);
    }}
    h1 {{ color: var(--accent); font-size: 1.5rem; }}
    .meta {{ color: var(--text-dim); font-size: 0.85rem; margin-top: 0.3rem; }}

    .header-actions {{ display: flex; gap: 0.75rem; align-items: center; }}
    .btn {{
      background: var(--accent-dim);
      color: var(--accent);
      border: 1px solid var(--accent);
      border-radius: 8px;
      padding: 0.5rem 1.25rem;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: background 0.15s;
    }}
    .btn:hover {{ background: var(--accent); color: #000; }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 1.5rem;
    }}

    .post-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      transition: border-color 0.2s;
    }}
    .post-card:hover {{ border-color: rgba(0,212,170,0.4); }}

    .post-header {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .post-num {{
      background: var(--accent-dim);
      color: var(--accent);
      font-size: 0.78rem;
      font-weight: 700;
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
    }}
    .post-topic {{
      color: var(--text-dim);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}

    .post-section {{ display: flex; flex-direction: column; gap: 0.5rem; }}
    .section-label {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.68rem;
      font-weight: 700;
      color: var(--text-dim);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}

    .script-block {{
      background: #0d0d15;
      border-radius: 8px;
      padding: 1rem 1.25rem;
      border-left: 3px solid var(--tiktok);
    }}
    .script-line {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
      line-height: 1.85;
    }}

    .caption-block {{
      background: #0d0d15;
      border-radius: 8px;
      padding: 1rem 1.25rem;
      font-size: 0.84rem;
      color: var(--text-dim);
      line-height: 1.7;
      border-left: 3px solid var(--accent);
    }}

    .source-note {{
      margin-top: 0.65rem;
      font-size: 0.72rem;
      color: #666;
      letter-spacing: 0.02em;
    }}

    .copy-btn {{
      background: var(--accent-dim);
      color: var(--accent);
      border: none;
      border-radius: 4px;
      padding: 0.2rem 0.65rem;
      font-size: 0.7rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .copy-btn:hover {{ background: var(--accent); color: #000; }}
    .copy-btn.copied {{ background: var(--green); color: #fff; }}

    .copy-all-btn {{
      background: var(--tiktok);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 0.65rem 1rem;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      margin-top: auto;
      transition: opacity 0.15s;
    }}
    .copy-all-btn:hover {{ opacity: 0.85; }}
    .copy-all-btn.copied {{ background: var(--green); }}

    @media (max-width: 600px) {{
      body {{ padding: 1rem; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>🎵 TikTok Content Queue</h1>
      <div class="meta">Generated {generated_at} · {len(posts)} posts ready · auto-refreshes daily 9am ET</div>
    </div>
    <div class="header-actions">
      <button class="btn" onclick="copyAll12()">Copy All 12</button>
      <a href="/tiktok.html" class="btn">↻ Refresh</a>
    </div>
  </header>
  <div class="grid">
    {cards_html}
  </div>
</div>

<script>
  function copyText(text, btn) {{
    navigator.clipboard.writeText(text).then(() => {{
      const orig = btn.textContent;
      btn.textContent = 'Copied!';
      btn.classList.add('copied');
      setTimeout(() => {{ btn.textContent = orig; btn.classList.remove('copied'); }}, 2000);
    }});
  }}

  function copyAll(script, caption, btn) {{
    const full = script + '\\n\\n---\\n\\n' + caption;
    navigator.clipboard.writeText(full).then(() => {{
      const orig = btn.textContent;
      btn.textContent = '✓ Copied!';
      btn.classList.add('copied');
      setTimeout(() => {{ btn.textContent = orig; btn.classList.remove('copied'); }}, 2000);
    }});
  }}

  function copyAll12() {{
    const cards = document.querySelectorAll('.post-card');
    let output = '';
    cards.forEach((card, i) => {{
      const lines = [...card.querySelectorAll('.script-line')].map(el => el.textContent).join('\\n');
      const caption = card.querySelector('.caption-block').innerText;
      output += `POST ${{i+1}}\\n${{lines}}\\n\\n${{caption}}\\n\\n${{'-'.repeat(40)}}\\n\\n`;
    }});
    navigator.clipboard.writeText(output.trim()).then(() => {{
      const btn = document.querySelector('.header-actions .btn');
      btn.textContent = '✓ Copied All 12';
      setTimeout(() => {{ btn.textContent = 'Copy All 12'; }}, 3000);
    }});
  }}
</script>
</body>
</html>"""

    Path(OUTPUT_HTML).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, "w") as f:
        f.write(html)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    load_env()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Reading research files (last {RESEARCH_DAYS} days)...")
    research, sources = get_recent_research()
    print(f"  → {len(research):,} chars of content loaded")
    print(f"  → {len(sources)} source files")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Calling model to generate posts...")
    try:
        posts = generate_posts(research, allowed_sources=sources)
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parse error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"  ✗ Generation failed: {e}")
        sys.exit(1)
    print(f"  → {len(posts)} posts generated")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Writing output files...")
    write_json(posts)
    write_html(posts)
    print(f"  → JSON: {OUTPUT_JSON}")
    print(f"  → HTML: {OUTPUT_HTML}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Done. Live at https://cg.meetkai.xyz/tiktok.html")


if __name__ == "__main__":
    main()
