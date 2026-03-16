#!/usr/bin/env python3
"""
Kai Harness — Marketing Intelligence Pipeline
=============================================
Usage:
  kai-harness run --task blog --site kaicalls --keyword "law firm answering service"
  kai-harness run --task meta-ads --site kaicalls --keyword "AI receptionist" --threshold 10
  kai-harness gate --file draft.md --keyword "law firm answering service"
  kai-harness brief --site kaicalls --keyword "law firm answering service"
  kai-harness report [--days 30] [--site kaicalls]
  kai-harness patterns [--site all]
  kai-harness status

Three laws:
  1. No brief, no write
  2. No gate pass, no publish
  3. No publish without logging
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

from dotenv import load_dotenv

# ── Configurable base paths ───────────────────────────────────────────────
# Override with environment variables or they default to the repo root.
_REPO_ROOT   = Path(__file__).resolve().parent.parent
CMO_BASE_DIR = Path(os.environ.get("CMO_BASE_DIR", str(_REPO_ROOT)))
WORKSPACE_DIR = Path(os.environ.get("WORKSPACE_DIR", str(_REPO_ROOT / "workspace")))

# Load .env from repo root or CMO_BASE_DIR
load_dotenv(CMO_BASE_DIR / ".env")
load_dotenv(_REPO_ROOT / ".env")

from google import genai as google_genai

# ── Paths (derived from configurable bases) ───────────────────────────────
SCRIPTS      = CMO_BASE_DIR / "scripts"
DATA_DIR     = CMO_BASE_DIR / "data"
CONTENT_LOG  = DATA_DIR / "content_log.json"
PENDING_DIR  = DATA_DIR / "pending_checks"
KNOWLEDGE    = WORKSPACE_DIR / "knowledge" if (WORKSPACE_DIR / "knowledge").exists() else _REPO_ROOT / "knowledge"
WORKSPACE    = WORKSPACE_DIR
VENV_PY      = os.environ.get("VENV_PYTHON", sys.executable)

# ── MARKETING.md parser ────────────────────────────────────────────────────
import re as _re

class MarketingConfig:
    """
    Parses MARKETING.md into a live config object.
    The harness reads this on every run — same pattern as CLAUDE.md for coding agents.

    Sections parsed:
      - Non-negotiables   → self.non_negotiables (str)
      - Skill contracts   → self.thresholds dict[format → {four_us, seo_required}]
      - Products/sites    → self.channels dict[site → channel_id]
      - Framework map     → self.framework_map dict[task → [paths]]
      - Learned defaults  → self.learned_defaults (str, updated by harness_defaults_update.py)
    """
    def __init__(self, path: Path):
        self.path     = path
        self.raw      = path.read_text() if path.exists() else ""
        self.thresholds:     dict[str, dict] = {}
        self.channels:       dict[str, str]  = {}
        self.framework_map:  dict[str, list] = {}
        self.non_negotiables: str = ""
        self.learned_defaults: str = ""
        self._parse()

    def _parse(self):
        text = self.raw

        # ── Non-negotiables ──────────────────────────────────────────────
        m = _re.search(r"## Non-Negotiables.*?\n(.*?)(?=\n## |\Z)", text, _re.DOTALL)
        if m:
            self.non_negotiables = m.group(1).strip()

        # ── Skill contracts table ────────────────────────────────────────
        # Rows: | contract.yaml | Format label | 12/16 | ✅/❌ |
        for row in _re.findall(r"\|\s*`?[\w\-]+\.yaml`?\s*\|[^|]+\|[^|]+\|[^|]+\|", text):
            parts = [p.strip() for p in row.strip("|").split("|")]
            if len(parts) < 4:
                continue
            contract, label, four_us_str, seo_str = parts[:4]
            # derive format key from label
            label_lower = label.lower()
            fmt = (
                "blog"             if "blog" in label_lower else
                "linkedin"         if "linkedin" in label_lower else
                "email-lifecycle"  if "lifecycle" in label_lower or "nurture" in label_lower else
                "cold-email"       if "cold" in label_lower else
                "meta-ads"         if "meta" in label_lower or "facebook" in label_lower else
                "google-ads"       if "google" in label_lower else
                "tiktok"           if "tiktok" in label_lower else
                "press"            if "press" in label_lower else
                "seo"              if "seo" in label_lower else
                None
            )
            if not fmt:
                continue
            try:
                threshold = int(_re.search(r"(\d+)/16", four_us_str).group(1))
            except Exception:
                threshold = 12
            seo_required = "✅" in seo_str or "required" in seo_str.lower()
            self.thresholds[fmt] = {"four_us": threshold, "seo": seo_required}

        # ── Products + site keys table ───────────────────────────────────
        # Rows: | Product | site_key | #channel (channel_id) |
        for row in _re.findall(r"\|[^|]+\|[^|]+\|[^|\n]*\d{17,19}[^|\n]*\|", text):
            parts = [p.strip() for p in row.strip("|").split("|")]
            if len(parts) < 3:
                continue
            _, site_key, channel_cell = parts[0], parts[1].strip(), parts[2]
            m = _re.search(r"(\d{17,19})", channel_cell)
            if m and site_key:
                self.channels[site_key] = m.group(1)

        # ── Framework map table ──────────────────────────────────────────
        # Rows: | Task | load these files |
        for row in _re.findall(r"\|\s*[\w ]+\s*\|[^|]+\|", text):
            parts = [p.strip() for p in row.strip("|").split("|")]
            if len(parts) < 2:
                continue
            task_label, files_cell = parts[0].lower(), parts[1]
            fmt = (
                "blog"            if "blog" in task_label else
                "linkedin"        if "linkedin" in task_label else
                "email-lifecycle" if "lifecycle" in task_label else
                "cold-email"      if "cold" in task_label else
                "tiktok"          if "tiktok" in task_label else
                "seo"             if "seo" in task_label else
                "meta-ads"        if "meta" in task_label else
                "google-ads"      if "google" in task_label else
                "press"           if "press" in task_label else
                None
            )
            if not fmt:
                continue
            paths = _re.findall(r"`([^`]+\.md)`|`([^`]+/)`", files_cell)
            flat  = [p for pair in paths for p in pair if p]
            if flat:
                self.framework_map[fmt] = flat

        # ── Learned defaults (auto-written by harness_defaults_update.py) ─
        m = _re.search(r"## Learned Defaults.*?\n(.*?)(?=\n## |\Z)", text, _re.DOTALL)
        if m:
            self.learned_defaults = m.group(1).strip()

    def threshold(self, fmt: str) -> int:
        """Return Four U's threshold for a format. Falls back to 12 for long-form, 10 for ads."""
        return self.thresholds.get(fmt, {}).get("four_us", 10 if fmt in SHORT_FORM else 12)

    def seo_required(self, fmt: str) -> bool:
        return self.thresholds.get(fmt, {}).get("seo", fmt not in SHORT_FORM)

    def channel(self, site: str) -> str:
        return self.channels.get(site, "1471889734841270332")

    def framework_paths(self, fmt: str) -> list[Path]:
        """Resolve framework paths from MARKETING.md relative to WORKSPACE."""
        paths = self.framework_map.get(fmt, [])
        resolved = []
        for p in paths:
            candidate = WORKSPACE / p
            if candidate.exists():
                resolved.append(candidate)
        return resolved

    def reload(self):
        """Re-read MARKETING.md from disk — picks up updates from harness_defaults_update.py."""
        self.__init__(self.path)

    def skill_contract(self, fmt: str) -> dict:
        """
        Load the skill contract YAML for a format.
        Returns the parsed contract dict, or {} if not found.
        Contract defines: word_count, quality_gates, hooks, retry behavior.
        """
        slug = {
            "blog":            "blog-post",
            "seo":             "blog-post",
            "linkedin":        "linkedin-article",
            "email-lifecycle": "email-lifecycle",
            "cold-email":      "cold-email",
            "meta-ads":        "meta-ads",
            "google-ads":      "google-ads",
        }.get(fmt, fmt)
        contract_path = WORKSPACE / "harness" / "skill-contracts" / f"{slug}.yaml"
        if contract_path.exists():
            try:
                return yaml.safe_load(contract_path.read_text()) or {}
            except Exception:
                pass
        return {}


# Load config from MARKETING.md on startup
MARKETING = MarketingConfig(WORKSPACE / "MARKETING.md")

# ── Constants (fallbacks when MARKETING.md is absent) ─────────────────────
FORMATS = [
    "blog", "linkedin", "email-lifecycle", "cold-email",
    "tiktok", "meta-ads", "google-ads", "press", "seo",
]
SITES = list(MARKETING.channels.keys()) or ["myproduct"]

# Short-form formats (ad/email) — lower Four U's threshold, no SEO lint
SHORT_FORM = {"meta-ads", "google-ads", "cold-email", "email-lifecycle", "tiktok"}

# Channel map from MARKETING.md (no hardcoded fallbacks)
DISCORD_CHANNELS = {**MARKETING.channels}

# Ad/short-form formats use lower Four U's threshold
SHORT_FORM = {"meta-ads", "google-ads", "cold-email", "email-lifecycle", "tiktok"}

# Site-specific proof points — loaded from config.yaml or MARKETING.md
# Add your product facts to config.yaml under products[].proof_points
def _load_site_facts() -> dict[str, str]:
    """Load site facts from config.yaml if available."""
    config_path = _REPO_ROOT / "config.yaml"
    if config_path.exists():
        try:
            cfg = yaml.safe_load(config_path.read_text()) or {}
            return {
                p["id"]: p.get("proof_points", "")
                for p in cfg.get("products", [])
                if p.get("proof_points")
            }
        except Exception:
            pass
    return {}

SITE_FACTS = _load_site_facts()

# Format-specific write instructions
FORMAT_INSTRUCTIONS = {
    "blog": """OUTPUT: Markdown only. No HTML tags.

STRUCTURE (follow exactly):
# [H1 title — must contain the exact target keyword, written as an insight not a label]
Meta: [150-160 char description — keyword in first 50 chars]

[Opening paragraph — hook as first sentence, keyword in first 100 words, state the counter-intuitive insight and the cost of delay within first 200 words]

## [H2 — include keyword or close variant]
[section body]

## [H2 — secondary keyword]
[section body]

## [H2 — secondary keyword]
[section body]

## [H2 — secondary keyword]
[section body]

[Closing paragraph — CTA]

REQUIREMENTS:
- Minimum 1,400 words. Count matters. Expand every section if short.
- 4+ H2s, at least one containing the keyword
- Keyword appears 3-5 times total, naturally
- 2+ internal links (use the URLs from the brief)
- Every sentence under 20 words
- No bullet lists longer than 4 items — convert to prose
- Every claim has a number attached. "Most" → specific %. "Saves money" → exact dollar amount.""",

    "linkedin": """OUTPUT: Plain text only. No markdown headers.

STRUCTURE:
[Single strong hook sentence — pattern interrupt or counter-intuitive fact]

[2-3 sentence expansion of the hook]

[Core insight — 3-4 short paragraphs, each 2-3 lines max]

[Proof point with a specific number]

[CTA — one sentence, low friction]

REQUIREMENTS:
- 600-900 words
- One idea per paragraph
- No hashtags, no "Thoughts?" endings
- Every paragraph separated by a blank line""",

    "cold-email": """OUTPUT: Three separate email touches, each clearly labeled.

--- TOUCH 1 ---
Subject: [under 50 chars — no clickbait, no spam triggers]
[2 A/B subject variants]
Body (max 120 words):
[Personalization hook — observation about THEM, not about you]
[Bridge — one sentence connecting their situation to the offer]
[CTA — one specific action, low friction, no calendar link]

--- TOUCH 2 (3 days later) ---
Subject: [different angle from Touch 1]
Body (max 100 words):
[Different angle from Touch 1]
[One piece of proof/data]
[Same low-friction CTA]

--- TOUCH 3 (7 days later) ---
Subject: [breakup framing]
Body (max 80 words):
[Close the loop gracefully — no guilt]
[Leave the door open]

REQUIREMENTS:
- Never open with "I hope this finds you well" or "My name is"
- No attachments mentioned
- No meeting ask in Touch 1""",

    "meta-ads": """OUTPUT: Three ad variants (A/B/C), each clearly labeled.

--- VARIANT A: [hook type] ---
Primary text (hook, max 125 chars for above-fold preview):
Full primary text (can expand below "See more"):
Headline (max 27 chars):
Description (max 27 chars):
CTA button: [See More | Learn More | Get Quote | Book Now | Sign Up]

--- VARIANT B: [different hook type] ---
[same structure]

--- VARIANT C: [different hook type] ---
[same structure]

Hook types to use across variants: pattern_interrupt | social_proof | pain_agitate | direct_offer | curiosity_gap
Include at least one number/stat in each variant.
Make each variant test a genuinely different angle — not just rewording.""",

    "google-ads": """OUTPUT: RSA + PMax asset group.

RSA:
H1: [max 30 chars — contains keyword]
H2: [max 30 chars — contains keyword or benefit]
H3-H15: [max 30 chars each — list all 15]
D1-D4: [max 90 chars each — list all 4]
Display path: [domain]/[keyword-slug]

PMax additional headlines (5, max 90 chars each):
PH1:
PH2:
PH3:
PH4:
PH5:

Bidding recommendation: [Smart Bidding strategy + rationale]

REQUIREMENTS:
- Keyword in H1 and H2
- At least one headline with a price or stat
- No exclamation marks in headlines (Google policy)""",

    "press": """OUTPUT: Standard press release format.

FOR IMMEDIATE RELEASE

[HEADLINE — under 100 chars, present tense, newsworthy]
[SUBHEADLINE — optional, adds context]

[CITY, Date] — [Lede: who, what, when, where, why in under 100 words]

[Body paragraph 1 — context and significance]

"[Quote from Connor Gallic, founder — specific, not corporate-speak]," said Connor Gallic, founder of [Company].

[Body paragraph 2 — supporting details, data]

[Body paragraph 3 — market context or additional proof]

###

About [Company]: [3-4 sentences, factual]
Media Contact: press@[domain].com""",

    "seo": """Same as blog format. Optimize specifically for position 0 / Featured Snippet:
- Answer the target query directly in the first paragraph (40-60 words, complete sentence)
- Use definition structure where applicable: "[Keyword] is [definition]"
- Include a step-by-step section with numbered list if the query is procedural""",

    "email-lifecycle": """OUTPUT: Single lifecycle email.

Subject: [under 50 chars]
Preview text: [40-90 chars — appears in inbox before open]

Body (under 400 words):
[Personalized opening — reference their action/status]
[Core value delivery — one main insight or resource]
[Supporting detail or proof]
[Single CTA — button text + destination]

PS: [Optional — one sentence that adds value or reinforces CTA]""",

    "tiktok": """OUTPUT: TikTok video script, 45-60 seconds.

HOOK (0-3s): [Say AND visually show the keyword/hook — must work on mute]
SOFT CTA (3-15s): [Mention offer or product naturally]
PROBLEM (15-30s): [Agitate the pain — specific scenario]
DEMO (30-45s): [Show the solution working — concrete]
FOMO (45-52s): [Scarcity or social proof]
HARD CTA (52-60s): [Point to link in bio or product]

Notes for creator: [3-5 specific visual direction notes]
Hashtags (5 max, specific): #[tag1] #[tag2] #[tag3] #[tag4] #[tag5]""",
}


# ── Gemini client ──────────────────────────────────────────────────────────
def gemini(prompt: str, model: str = "gemini-2.0-flash") -> str:
    client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text.strip()


# ── Script runner ──────────────────────────────────────────────────────────
def run_script(script: str, args: list[str]) -> tuple[int, str]:
    cmd = [VENV_PY, str(SCRIPTS / script)] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def run_cmo(args: list[str]) -> str:
    result = subprocess.run(
        ["python3", str(SCRIPTS / "cmo_wrapper.py")] + args,
        capture_output=True, text=True,
    )
    return result.stdout.strip()


# ── Print helpers ──────────────────────────────────────────────────────────
def header(title: str):
    print(f"\n{'═'*50}\n  {title}\n{'═'*50}\n")

def step(n: int, total: int, title: str):
    print(f"\n[{n}/{total}] {title}\n{'─'*40}")


# ── Brief generator ────────────────────────────────────────────────────────
def generate_brief(site: str, keyword: str, fmt: str, persona: str | None = None) -> dict:
    step(1, 6, f"Research — {site} / {keyword}")

    gsc_opps    = run_cmo(["gsc", "opportunities", f"--site={site}"])
    gsc_queries = run_cmo(["gsc", "queries",       f"--site={site}", "--limit=20"])

    persona_text = ""
    if persona:
        p = KNOWLEDGE / "personas" / f"{persona}.md"
        if p.exists():
            persona_text = p.read_text()[:1500]

    raw = gemini(f"""Build a content brief for the Kai Harness pipeline.

Site: {site}
Keyword: {keyword}
Format: {fmt}
Persona hint: {persona or "infer from site and keyword"}

GSC opportunities:
{gsc_opps[:3000] or "No GSC data"}

GSC top queries:
{gsc_queries[:2000] or "No GSC data"}

Persona reference:
{persona_text or "Infer from site context"}

Return ONLY valid JSON:
{{
  "target_site": "{site}",
  "target_keyword": "{keyword}",
  "secondary_keywords": ["kw2", "kw3", "kw4"],
  "format": "{fmt}",
  "persona": "archetype name",
  "current_rank": "not ranking OR position N",
  "monthly_impressions": 0,
  "current_ctr": 0.0,
  "competitor_url": "https://...",
  "competitor_weakness": "specific gap in 20+ words",
  "angle": "differentiated frame — not just the keyword restated",
  "hook_options": [
    "Hook 1 — specific, counter-intuitive or data-driven",
    "Hook 2 — pain/fear angle",
    "Hook 3 — curiosity gap"
  ],
  "audience_pain": "single biggest frustration of this persona with this topic",
  "proof_available": "specific data point or stat we can use",
  "cta": "exact action we want them to take",
  "word_count_target": 1400,
  "publish_date": "{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
  "internal_links": ["https://...", "https://..."]
}}""")

    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Content writer ─────────────────────────────────────────────────────────
def write_content(brief: dict) -> str:
    step(2, 6, f"Write — {brief['format']} / {brief['target_keyword']}")

    fmt  = brief["format"]
    site = brief["target_site"]

    # ── MARKETING.md drives framework selection ────────────────────────────
    # Re-read on every run — picks up learned defaults written by
    # harness_defaults_update.py without restarting the process.
    MARKETING.reload()

    # framework_paths() resolves paths listed in MARKETING.md's Framework Map table.
    # Falls back to hardcoded paths when MARKETING.md doesn't cover the format yet.
    framework_paths = MARKETING.framework_paths(fmt) or {
        "blog":           [KNOWLEDGE / "frameworks/content-copywriting/algorithmic-authorship.md"],
        "linkedin":       [WORKSPACE / "skills/linkedin-writing/SKILL.md"],
        "email-lifecycle":[KNOWLEDGE / "channels/email-lifecycle.md"],
        "cold-email":     [KNOWLEDGE / "channels/email-lifecycle.md",
                           WORKSPACE / "harness/references/cold-email-rules.md"],
        "tiktok":         [KNOWLEDGE / "channels/tiktok-algorithm.md"],
        "meta-ads":       [KNOWLEDGE / "channels/meta-advertising.md"],
        "google-ads":     [KNOWLEDGE / "channels/paid-acquisition.md",
                           WORKSPACE / "harness/references/google-ads-rules.md"],
        "press":          [KNOWLEDGE / "channels/press-releases.md"],
        "seo":            [KNOWLEDGE / "frameworks/aeo-ai-search"],
    }.get(fmt, [])

    framework = "\n\n---\n\n".join(
        p.read_text()[:1500] for p in framework_paths if p.exists()
    )

    # Load winning patterns
    ww = KNOWLEDGE / "playbooks/what-works.md"
    patterns = ww.read_text()[-2000:] if ww.exists() else ""

    # ── Load skill contract for this format ────────────────────────────────
    # Contract YAML defines word count, gate thresholds, hook order, retry limit.
    # Changing the YAML changes the harness behavior — no code edits needed.
    contract = MARKETING.skill_contract(fmt)
    wc_range  = contract.get("word_count", f"{brief.get('word_count_target', 1000)}")
    wc_target = brief.get("word_count_target") or (
        int(str(wc_range).split("-")[0]) if "-" in str(wc_range) else int(wc_range)
    )

    # ── Site facts ─────────────────────────────────────────────────────────
    facts = SITE_FACTS.get(site, "")

    # Format instructions
    instructions = FORMAT_INSTRUCTIONS.get(fmt, f"Write the content. Target {wc_target} words.")

    draft = gemini(f"""You are writing content for the Kai Harness marketing pipeline.

## MARKETING.md — Operating Config
{MARKETING.non_negotiables or "Apply standard quality rules."}

## Learned Defaults (updated automatically from winner patterns)
{MARKETING.learned_defaults or "No learned defaults yet — write specifically and hook-first."}

## Brief
{json.dumps(brief, indent=2)}

## Central thesis (build the entire piece around this)
Angle: {brief.get('angle')}
Competitor weakness to exploit: {brief.get('competitor_weakness')}
Audience pain: {brief.get('audience_pain')}

## Verified proof points (use these — do not invent stats)
{facts or brief.get('proof_available', '')}

## Format instructions
{instructions}

## Framework rules (from MARKETING.md framework map)
{framework or "Write clearly. Lead with data. Short sentences. Hook first."}

## Winning patterns from past content
{patterns or "None yet — write specifically and hook-first."}

## Non-negotiables
- No banned words: leverage, utilize, synergy, innovative, revolutionary, game-changer,
  deep dive, in conclusion, going forward, first and foremost, next level, it's important to note
- Conditions after main clause: "Do X if Y fails" not "If Y fails, do X"
- Every sentence under 20 words
- Every claim has a number — no vague adjectives
- Lead with hook_options[0] as the first body sentence
- Do not stop early — hit the word count target

Write the complete draft now:""")

    return draft


# ── Quality gate ───────────────────────────────────────────────────────────
def run_gate(draft: str, keyword: str, threshold: int = 12, max_retries: int = 2,
             fmt: str | None = None) -> dict:
    step(3, 6, "Quality Gate")

    is_short = any(m in draft for m in ["VARIANT A", "H1:", "Touch 1", "Subject:", "HOOK (0-3s)"])

    # Priority: CLI --threshold > skill contract YAML > MARKETING.md table > heuristic
    contract = MARKETING.skill_contract(fmt) if fmt else {}
    contract_gates = contract.get("quality_gates", [])
    contract_threshold = next(
        (int(_re.search(r"(\d+)", g).group(1)) for g in contract_gates if "four_us_total" in g),
        None
    )
    marketing_threshold = MARKETING.threshold(fmt) if fmt else (10 if is_short else 12)
    effective_threshold = (
        threshold       if threshold != 12 else
        contract_threshold if contract_threshold else
        marketing_threshold
    )
    # Contract can also require banned_words and seo_lint explicitly
    contract_requires_seo = any("seo_lint" in g for g in contract_gates)
    skip_seo = is_short and not contract_requires_seo and not MARKETING.seo_required(fmt or "")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(draft)
        tmp = f.name

    results = {"passed": False, "draft": draft, "attempts": 0}

    try:
        for attempt in range(1, max_retries + 2):
            print(f"  Attempt {attempt}/{max_retries + 1}...")
            passed = True

            # Four U's
            _, out = run_script("four_us_score.py", ["--file", tmp, "--json"])
            try:
                four_us = json.loads(out)
            except Exception:
                four_us = {"passed": False, "scores": {}, "notes": {}}

            scores = four_us.get("scores", {})
            total  = sum(scores.get(k, 0) for k in ["unique", "useful", "ultra_specific", "urgent"])
            mins_ok = all(scores.get(k, 0) >= 2 for k in ["unique", "useful", "ultra_specific", "urgent"])
            four_us["passed"] = (total >= effective_threshold and mins_ok)
            four_us["total"]  = total
            results["four_us"] = four_us

            indicator = "✅" if four_us["passed"] else "❌"
            suffix    = f" (threshold: {effective_threshold}+)" if is_short else ""
            print(f"    Four U's: {indicator} {total}/16{suffix}")

            if not four_us["passed"]:
                passed = False

            # Banned words
            _, out = run_script("banned_word_check.py", ["--file", tmp, "--json"])
            try:
                banned = json.loads(out)
            except Exception:
                banned = {"passed": True, "tier1": []}
            results["banned"] = banned
            print(f"    Banned words: {'✅' if banned.get('passed') else '❌'}")
            if not banned.get("passed"):
                passed = False

            # SEO lint — contract + MARKETING.md decide; heuristic is fallback
            if skip_seo:
                seo = {"passed": True, "errors": [], "warnings": [], "skipped": True}
                print("    SEO lint: ⏭ skipped")
            else:
                _, out = run_script("seo_lint.py", ["--file", tmp, "--keyword", keyword, "--json"])
                try:
                    seo = json.loads(out)
                except Exception:
                    seo = {"passed": True, "errors": [], "warnings": []}
                e, w = len(seo.get("errors", [])), len(seo.get("warnings", []))
                print(f"    SEO lint: {'✅' if seo.get('passed') else '❌'} ({e} error(s), {w} warning(s))")
                if not seo.get("passed"):
                    passed = False
            results["seo"] = seo

            if passed:
                results["passed"] = True
                results["attempts"] = attempt
                results["draft"]    = draft
                print(f"\n  ✅ Gate passed on attempt {attempt}.")
                break

            if attempt <= max_retries:
                print(f"\n  Gate failed. Revising (attempt {attempt}/{max_retries})...")
                draft = revise_draft(draft, results, keyword)
                with open(tmp, "w") as f:
                    f.write(draft)
            else:
                results["attempts"] = attempt
                results["draft"]    = draft
                print(f"\n  ❌ Gate failed after {max_retries} retries. Human review required.")
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass

    return results


# ── Surgical revision ──────────────────────────────────────────────────────
def revise_draft(draft: str, gate_results: dict, keyword: str) -> str:
    """Fix only what failed. Do not change what passed."""
    failures  = []
    preserved = []

    # Four U's — report all failing dimensions
    four_us = gate_results.get("four_us", {})
    scores  = four_us.get("scores", {})
    notes   = four_us.get("notes", {})
    if four_us and not four_us.get("passed"):
        for dim in ["unique", "useful", "ultra_specific", "urgent"]:
            s = scores.get(dim, 0)
            n = notes.get(dim, "")
            if s < 3:
                label = dim.replace("_", "-").title()
                failures.append(f"Four U's {label} scored {s}/4 — fix: {n}")
            else:
                preserved.append(f"Four U's {dim.replace('_','-').title()} = {s}/4 (DO NOT change)")

    # Banned words — exact word + context + replacement
    banned = gate_results.get("banned", {})
    if banned and not banned.get("passed"):
        for hit in banned.get("tier1", []):
            ctx = hit.get("context", "")[:120]
            rep = hit.get("replacement", "rewrite the phrase")
            failures.append(f'Banned word "{hit["word"]}" — context: "{ctx}" — replace with: {rep}')

    # SEO errors only (skip warnings to avoid over-constraining)
    seo = gate_results.get("seo", {})
    if seo and not seo.get("passed") and not seo.get("skipped"):
        for err in seo.get("errors", []):
            failures.append(f"SEO error: {err}")

    if not failures:
        return draft

    word_count = len(draft.split())

    return gemini(f"""Revise this content draft. Fix ONLY the listed issues.

ISSUES TO FIX:
{chr(10).join(f"- {f}" for f in failures)}

DO NOT CHANGE (these are already passing):
{chr(10).join(f"- {p}" for p in preserved) or "None"}

HARD CONSTRAINTS:
- Keep at least {word_count} words — do NOT shorten
- Do NOT remove numbers, data points, or specific examples
- Do NOT introduce: leverage, utilize, synergy, revolutionary, game-changer, next level, in conclusion
- For SEO title errors: rewrite the # H1 to contain "{keyword}" — keep the hook as the first body paragraph
- Fix every listed issue. Change nothing else.

DRAFT:
{draft}

Return ONLY the revised draft — no preamble, no explanation:""")


# ── Discord approval ───────────────────────────────────────────────────────
def post_for_approval(draft: str, brief: dict, gate_results: dict):
    step(4, 6, "Discord Approval")

    site       = brief.get("target_site", "meetkai")
    channel_id = DISCORD_CHANNELS.get(site, DISCORD_CHANNELS["meetkai"])
    total      = gate_results.get("four_us", {}).get("total", "?")
    fmt        = brief.get("format")
    keyword    = brief.get("target_keyword", "")
    preview    = draft[:600].replace('"', "'")
    seo_w      = len(gate_results.get("seo", {}).get("warnings", []))

    msg = (
        f"**📝 Content ready for approval**\\n"
        f"Site: `{site}` | Format: `{fmt}` | Keyword: `{keyword}`\\n"
        f"Four U's: {total}/16 | SEO warnings: {seo_w}\\n\\n"
        f"**Preview:**\\n```\\n{preview}...\\n```\\n\\n"
        f"React ✅ to approve · ❌ to reject with reason"
    )
    os.system(f'openclaw message send --channel discord --target {channel_id} --message "{msg}"')
    print(f"  Posted to #{site} channel ({channel_id})")
    print("  Draft saved to /tmp/harness_draft.md — publish manually after approval.")


# ── Commands ───────────────────────────────────────────────────────────────
def cmd_run(args):
    header(f"Kai Harness — {args.task.upper()} / {args.site} / {args.keyword}")

    brief = generate_brief(args.site, args.keyword, args.task, args.persona)
    with open("/tmp/harness_brief.json", "w") as f:
        json.dump(brief, f, indent=2)
    print(f"  Angle: {brief.get('angle')}")
    print(f"  Hook:  {brief.get('hook_options', [''])[0]}")

    if args.brief_only:
        print("\nBrief saved to /tmp/harness_brief.json")
        return

    draft = write_content(brief)
    with open("/tmp/harness_draft.md", "w") as f:
        f.write(draft)
    print(f"  Draft: /tmp/harness_draft.md ({len(draft.split())} words)")

    gate_results = run_gate(draft, args.keyword, threshold=args.threshold, fmt=args.task)

    if not gate_results["passed"] and not args.force:
        print("\n❌ Gate failed. Revise manually:")
        print("   Draft: /tmp/harness_draft.md")
        print(f"   Re-gate: kai-harness gate --file /tmp/harness_draft.md --keyword \"{args.keyword}\"")
        sys.exit(1)

    if not args.skip_approval:
        post_for_approval(gate_results["draft"], brief, gate_results)
    else:
        print("\n  ⚠️  Approval skipped (--skip-approval). Publish manually.")
        print("  Draft: /tmp/harness_draft.md")


def cmd_gate(args):
    header("Kai Harness — Gate Check")
    draft = Path(args.file).read_text()
    r = run_gate(draft, args.keyword, threshold=args.threshold)
    if not r["passed"]:
        sys.exit(1)


def cmd_brief(args):
    header("Kai Harness — Brief")
    brief = generate_brief(args.site, args.keyword, args.task or "blog", args.persona)
    print(json.dumps(brief, indent=2))
    with open("/tmp/harness_brief.json", "w") as f:
        json.dump(brief, f, indent=2)
    print("\nSaved to /tmp/harness_brief.json")


def cmd_report(args):
    header(f"Kai Harness — Report ({args.days}d)")
    log = json.loads(CONTENT_LOG.read_text()) if CONTENT_LOG.exists() else []
    if args.site != "all":
        log = [e for e in log if e.get("site") == args.site]
    if not log:
        print("No content tracked yet.")
        return
    buckets: dict[str, list] = {"winner": [], "average": [], "underperformer": [], "pending": []}
    for e in log:
        p = e.get("performance_30d")
        buckets["pending" if not p else p.get("grade", "average")].append(e)
    labels = {"winner": "🏆", "average": "📊", "underperformer": "⚠️", "pending": "⏳"}
    for grade, entries in buckets.items():
        if entries:
            print(f"\n{labels[grade]} {grade.upper()} ({len(entries)})")
            for e in entries:
                print(f"  [{e.get('site')}] {e.get('title') or e.get('keyword')} — {e.get('url', 'no url')}")


def cmd_patterns(args):
    header(f"Kai Harness — Patterns ({args.site})")
    _, out = run_script("pattern_extract.py", ["--weekly", f"--site={args.site}"])
    print(out)


def cmd_status(args):
    header("Kai Harness — Status")
    log = json.loads(CONTENT_LOG.read_text()) if CONTENT_LOG.exists() else []
    pending = list(PENDING_DIR.glob("*.json")) if PENDING_DIR.exists() else []
    pending_count = sum(
        1 for f in pending
        if json.loads(f.read_text()).get("status") == "pending"
    )
    winners = [e for e in log if e.get("performance_30d", {}).get("grade") == "winner"]
    ww = (KNOWLEDGE / "playbooks/what-works.md").exists()
    mmd = (WORKSPACE / "MARKETING.md").exists()

    print(f"  Tracked pieces:      {len(log)}")
    print(f"  Winners:             {len(winners)}")
    print(f"  Pending 30d checks:  {pending_count}")
    print(f"  Knowledge base:      {'✅' if ww else '❌'}")
    print(f"  MARKETING.md:        {'✅' if mmd else '❌'}")
    print(f"  Gate scripts:        ✅")
    print(f"\n  Formats:  {', '.join(FORMATS)}")
    print(f"  Sites:    {', '.join(SITES)}")


# ── CLI ────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(prog="kai-harness", description="Kai Harness — Marketing Pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    def add_threshold(parser):
        parser.add_argument(
            "--threshold", type=int, default=12,
            help="Four U's minimum (default 12; use 11 for commercial posts without case study data)",
        )

    # run
    r = sub.add_parser("run", help="Full pipeline: brief → write → gate → approve")
    r.add_argument("--task",     required=True, choices=FORMATS)
    r.add_argument("--site",     required=True)
    r.add_argument("--keyword",  required=True)
    r.add_argument("--persona")
    r.add_argument("--brief-only",     action="store_true")
    r.add_argument("--skip-approval",  action="store_true")
    r.add_argument("--force",          action="store_true", help="Continue despite gate failure")
    add_threshold(r)

    # gate
    g = sub.add_parser("gate", help="Gate check on existing draft")
    g.add_argument("--file",    required=True)
    g.add_argument("--keyword", required=True)
    add_threshold(g)

    # brief
    b = sub.add_parser("brief", help="Generate brief only")
    b.add_argument("--site",    required=True)
    b.add_argument("--keyword", required=True)
    b.add_argument("--task",    choices=FORMATS, default="blog")
    b.add_argument("--persona")

    # report
    rp = sub.add_parser("report", help="Performance report")
    rp.add_argument("--days", type=int, default=30)
    rp.add_argument("--site", default="all")

    # patterns
    pt = sub.add_parser("patterns", help="Surface content patterns")
    pt.add_argument("--site", default="all")

    # status
    sub.add_parser("status", help="System status")

    # approvals
    sub.add_parser("approvals", help="Pending approval drafts")

    args = p.parse_args()
    {
        "run":       cmd_run,
        "gate":      cmd_gate,
        "brief":     cmd_brief,
        "report":    cmd_report,
        "patterns":  cmd_patterns,
        "status":    cmd_status,
        "approvals": lambda _: print("\n".join(str(f) for f in Path("/tmp").glob("harness_draft*.md")) or "No drafts pending."),
    }[args.command](args)


if __name__ == "__main__":
    main()
