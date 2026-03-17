"""
Writer — Pure functions for content generation and revision.

Extracted from harness_cli.py to allow reuse by the Outcome Engine
without importing the CLI module (which triggers Gemini client init at module level).

All LLM calls go through an injected `gemini_fn` callable — no module-level side effects.
"""

import json

# Short-form formats (ad/email) — lower Four U's threshold, no SEO lint
SHORT_FORM = {"meta-ads", "google-ads", "cold-email", "email-lifecycle", "tiktok"}

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

# Format → quality gate policy mapping
FORMAT_TO_POLICY = {
    "blog":            "blog-publish",
    "seo":             "blog-publish",
    "linkedin":        "linkedin-article",
    "email-lifecycle": "cold-email",
    "cold-email":      "cold-email",
    "press":           "press-release",
    "tiktok":          "tiktok-script",
    "meta-ads":        "meta-ad",
    "google-ads":      "google-ad",
}


def assemble_write_prompt(
    brief: dict,
    framework_texts: str,
    patterns: str,
    contract: dict,
    site_facts: str,
    learned_defaults: str,
    non_negotiables: str,
    format_instructions: str | None = None,
) -> str:
    """Build the full write prompt from all context pieces. Pure function."""
    fmt = brief.get("format", "blog")
    wc_range = contract.get("word_count", f"{brief.get('word_count_target', 1000)}")
    wc_target = brief.get("word_count_target") or (
        int(str(wc_range).split("-")[0]) if "-" in str(wc_range) else int(wc_range)
    )
    instructions = format_instructions or FORMAT_INSTRUCTIONS.get(
        fmt, f"Write the content. Target {wc_target} words."
    )

    return f"""You are writing content for the Kai Harness marketing pipeline.

## MARKETING.md — Operating Config
{non_negotiables or "Apply standard quality rules."}

## Learned Defaults (updated automatically from winner patterns)
{learned_defaults or "No learned defaults yet — write specifically and hook-first."}

## Brief
{json.dumps(brief, indent=2)}

## Central thesis (build the entire piece around this)
Angle: {brief.get('angle')}
Competitor weakness to exploit: {brief.get('competitor_weakness')}
Audience pain: {brief.get('audience_pain')}

## Verified proof points (use these — do not invent stats)
{site_facts or brief.get('proof_available', '')}

## Format instructions
{instructions}

## Framework rules (from MARKETING.md framework map)
{framework_texts or "Write clearly. Lead with data. Short sentences. Hook first."}

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

Write the complete draft now:"""


def write_content(prompt: str, gemini_fn) -> str:
    """Generate content from a write prompt using the provided LLM callable."""
    return gemini_fn(prompt)


def assemble_revision_prompt(draft: str, gate_results: dict, keyword: str) -> str:
    """Build a surgical revision prompt from gate failures. Pure function."""
    failures = []

    for fix in gate_results.get("violations", gate_results.get("top_fixes", [])):
        rule_id = fix.get("rule_id", "")
        rule_name = fix.get("rule_name", "")
        suggestion = fix.get("suggestion", "")
        v = fix.get("first_violation", {})
        line = v.get("line", "?")
        text = v.get("text", "")
        fix_text = v.get("fix", suggestion)
        count = fix.get("violation_count", 1)

        failures.append(
            f"[{rule_id}] {rule_name} (line {line}, {count} occurrence(s)): "
            f'"{text[:100]}" → Fix: {fix_text}'
        )

    if not failures:
        return draft  # Nothing to fix

    word_count = len(draft.split())
    score = gate_results.get("score", "?")

    return f"""Revise this content draft. Current quality score: {score}/100. Fix ONLY the listed issues.

ISSUES TO FIX (from quality scorer — each has rule ID, line number, and exact fix):
{chr(10).join(f"- {f}" for f in failures)}

HARD CONSTRAINTS:
- Keep at least {word_count} words — do NOT shorten
- Do NOT remove numbers, data points, or specific examples
- Do NOT introduce: leverage, utilize, synergy, revolutionary, game-changer, next level, in conclusion
- For SEO title errors: rewrite the # H1 to contain "{keyword}" — keep the hook as the first body paragraph
- Fix every listed issue. Change nothing else.

DRAFT:
{draft}

Return ONLY the revised draft — no preamble, no explanation:"""


def revise_content(prompt: str, gemini_fn) -> str:
    """Revise content using the provided LLM callable."""
    return gemini_fn(prompt)
