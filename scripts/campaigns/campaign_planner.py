#!/usr/bin/env python3
"""
Kai CMO Harness — Campaign Planner
=====================================
Generate all assets for a multi-channel marketing campaign.

Usage:
  python scripts/campaigns/campaign_planner.py --goal "product launch" --product myproduct --keyword "ai crm"
  python scripts/campaigns/campaign_planner.py --goal "webinar" --product myproduct --keyword "sales automation" --save campaigns/q1-webinar/

Campaign types: launch, promotion, webinar, seasonal, awareness
Generates: landing page copy, 5-email sequence, 3 social variants, 3 ad variants, content calendar
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE = REPO_ROOT / "knowledge"


def _slugify(text: str) -> str:
    """Lowercase slug: alphanumerics joined by hyphens."""
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def mint_campaign_id(goal: str, keyword: str = "", when: datetime | None = None) -> str:
    """Mint the shared campaign identity: ``cmp-YYYYMMDD-<slug>``.

    This is THE join key across the five campaign stores: planner
    manifest.json, campaign_tracker SQLite, RuntimeStore ``campaign_plan``
    artifacts, editorial calendar items, and content_log entries
    (threaded via ``engine.generate(campaign_id=...)``).
    """
    when = when or datetime.now(timezone.utc)
    slug = _slugify(goal) or _slugify(keyword) or "campaign"
    return f"cmp-{when.strftime('%Y%m%d')}-{slug[:48].strip('-')}"


def _record_campaign_plan_artifact(manifest: dict, save_dir: str) -> str | None:
    """Record a ``campaign_plan`` artifact in the RuntimeStore.

    Uses the artifact type declared in kai/runtime/models.py. Local
    workspace state only — nothing here touches a live channel.
    Returns the artifact_id, or None if the runtime store is unavailable.
    """
    try:
        from kai.runtime import get_default_runtime_store

        store = get_default_runtime_store()
        artifact = store.record_artifact(
            {
                "artifact_type": "campaign_plan",
                "brand_id": manifest.get("product", ""),
                "workflow": "campaign-plan",
                "data": {
                    "campaign_id": manifest.get("campaign_id"),
                    "manifest": manifest,
                    "assets_dir": str(save_dir),
                },
            }
        )
        return artifact.get("artifact_id")
    except Exception as e:  # never let bookkeeping kill the asset save
        print(f"  Warning: could not record campaign_plan artifact: {e}")
        return None


def _load_config() -> dict:
    config_path = REPO_ROOT / "config.yaml"
    if config_path.exists():
        return yaml.safe_load(config_path.read_text()) or {}
    return {}


def _get_product_context(product_id: str) -> str:
    config = _load_config()
    for p in config.get("products", []):
        if p.get("id") == product_id:
            return f"Product: {p.get('name', product_id)}\nURL: {p.get('url', '')}\nProof points:\n{p.get('proof_points', '')}"
    return f"Product: {product_id}"


def _load_framework(path: str) -> str:
    fp = KNOWLEDGE / path
    if fp.exists():
        return fp.read_text()[:2000]
    return ""


def _gemini(prompt: str) -> str:
    from google.genai import Client as GenaiClient
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: Set GEMINI_API_KEY")
        sys.exit(1)
    client = GenaiClient(api_key=api_key)
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text.strip()


CAMPAIGN_TEMPLATES = {
    "launch": {
        "description": "Product launch campaign — build awareness, generate signups, convert early adopters",
        "timeline": "8 weeks pre-launch to 4 weeks post-launch",
        "assets": ["landing_page", "email_sequence", "social_posts", "ads", "press_release", "content_calendar"],
    },
    "promotion": {
        "description": "Time-limited promotion — drive urgency, maximize conversions within window",
        "timeline": "2 weeks pre-promotion to 1 week post",
        "assets": ["landing_page", "email_sequence", "social_posts", "ads", "content_calendar"],
    },
    "webinar": {
        "description": "Webinar campaign — drive registrations, maximize attendance, follow up for conversion",
        "timeline": "4 weeks pre-webinar to 2 weeks post",
        "assets": ["landing_page", "email_sequence", "social_posts", "ads", "content_calendar"],
    },
    "seasonal": {
        "description": "Seasonal/holiday campaign — capitalize on timing, themed messaging",
        "timeline": "6 weeks pre to 1 week post",
        "assets": ["landing_page", "email_sequence", "social_posts", "ads", "content_calendar"],
    },
    "awareness": {
        "description": "Brand awareness campaign — thought leadership, reach, share of voice",
        "timeline": "Ongoing, 90-day sprints",
        "assets": ["social_posts", "content_calendar", "blog_series"],
    },
}


def generate_campaign(
    goal: str,
    product_id: str,
    keyword: str,
    campaign_type: str = "launch",
    save_dir: str | None = None,
    campaign_id: str | None = None,
) -> dict:
    """Generate all campaign assets.

    ``campaign_id`` is minted (``cmp-YYYYMMDD-<slug>``) when not supplied.
    With ``save_dir``, it is written into manifest.json, a tracker row is
    auto-created (campaign_tracker.create_campaign), and a ``campaign_plan``
    artifact is recorded in the RuntimeStore — one join key across all
    campaign stores.
    """

    campaign_id = campaign_id or mint_campaign_id(goal, keyword)
    template = CAMPAIGN_TEMPLATES.get(campaign_type, CAMPAIGN_TEMPLATES["launch"])
    product_context = _get_product_context(product_id)
    pe_framework = _load_framework("frameworks/content-copywriting/perception-engineering.md")
    email_framework = _load_framework("channels/email-lifecycle.md")
    headline_framework = _load_framework("frameworks/content-copywriting/headline-formulas.md")

    print(f"\n{'═'*60}")
    print(f"  Campaign Planner — {campaign_type.upper()}")
    print(f"  Campaign ID: {campaign_id}")
    print(f"  Goal: {goal}")
    print(f"  Product: {product_id} | Keyword: {keyword}")
    print(f"{'═'*60}")

    assets = {}

    # ── 1. Landing Page ──────────────────────────────────────────────────
    if "landing_page" in template["assets"]:
        print("\n  [1] Generating landing page copy...")
        assets["landing_page"] = _gemini(f"""Write landing page copy for this campaign.

Campaign: {goal}
Type: {campaign_type} — {template['description']}
{product_context}
Keyword: {keyword}

Perception Engineering framework (use this):
{pe_framework[:1000]}

Structure your output EXACTLY as:
# HEADLINE
[Under 70 chars, contains keyword]

## SUBHEADLINE
[Expands on headline, 1-2 sentences]

## HERO SECTION
[2-3 sentences describing the core value proposition]
CTA: [Primary button text]

## PROBLEM SECTION
[3-4 bullet points describing the pain this solves, with specific numbers]

## SOLUTION SECTION
[How the product solves each pain point, with proof]

## SOCIAL PROOF
[3 testimonial placeholders with specific result metrics]
[Logo bar: list 5-6 company types]

## FEATURES/BENEFITS
[4-6 benefit blocks, each with: icon suggestion, headline, 2-sentence description]

## FAQ
[5 questions and answers, objection-handling]

## FINAL CTA
[Urgency-driven closing, primary CTA button text]

Requirements:
- No banned words (leverage, innovative, game-changer, etc.)
- Every claim has a specific number
- Lead with benefit, not feature""")

    # ── 2. Email Sequence ────────────────────────────────────────────────
    if "email_sequence" in template["assets"]:
        print("  [2] Generating 5-email sequence...")
        assets["email_sequence"] = _gemini(f"""Write a 5-email nurture sequence for this campaign.

Campaign: {goal}
Type: {campaign_type}
{product_context}
Keyword: {keyword}

Email framework:
{email_framework[:1000]}

Write EXACTLY 5 emails:

--- EMAIL 1: HOOK (Day 0 — immediately after signup/trigger) ---
Subject: [under 50 chars]
Preview: [40-90 chars]
Body: [under 300 words — introduce the problem, hint at solution]
CTA: [single action]

--- EMAIL 2: VALUE (Day 2) ---
Subject:
Preview:
Body: [deliver one concrete insight or resource, build trust]
CTA:

--- EMAIL 3: PROOF (Day 4) ---
Subject:
Preview:
Body: [case study or data point showing results]
CTA:

--- EMAIL 4: OBJECTION (Day 6) ---
Subject:
Preview:
Body: [address the #1 reason people don't buy/act]
CTA:

--- EMAIL 5: URGENCY (Day 8) ---
Subject:
Preview:
Body: [deadline, scarcity, or cost-of-delay angle]
CTA: [strongest CTA]

Requirements:
- Each subject under 50 chars
- Each body under 300 words
- One CTA per email
- No banned words
- Specific numbers in every email""")

    # ── 3. Social Posts ──────────────────────────────────────────────────
    if "social_posts" in template["assets"]:
        print("  [3] Generating social post variants...")
        assets["social_posts"] = _gemini(f"""Write social media posts for this campaign across 3 platforms.

Campaign: {goal}
{product_context}
Keyword: {keyword}

Write 3 variants for EACH platform:

## LINKEDIN (3 posts)
[Each 150-300 words, professional tone, pattern-interrupt hook, no hashtags]

## TWITTER/X (3 tweets)
[Each under 280 chars, punchy, with hook]

## INSTAGRAM (3 captions)
[Each 100-200 words, conversational, end with CTA, 3-5 hashtags]

Each variant should test a different angle:
- Variant A: Data/stat-driven
- Variant B: Pain/problem-driven
- Variant C: Story/narrative-driven

No banned words. Every post has a specific number or proof point.""")

    # ── 4. Ad Variants ───────────────────────────────────────────────────
    if "ads" in template["assets"]:
        print("  [4] Generating ad variants...")
        assets["ads"] = _gemini(f"""Write ad copy for this campaign.

Campaign: {goal}
{product_context}
Keyword: {keyword}

{headline_framework[:800]}

Write for TWO platforms:

## META ADS (3 variants)
--- VARIANT A: [hook type] ---
Primary text (max 125 chars):
Full primary text:
Headline (max 27 chars):
Description (max 27 chars):
CTA: [Learn More | Sign Up | Get Quote]

--- VARIANT B ---
[same structure]

--- VARIANT C ---
[same structure]

## GOOGLE ADS (RSA)
H1-H5: [max 30 chars each, keyword in H1-H2]
D1-D2: [max 90 chars each]

Each variant tests a different hook. Include numbers/stats.""")

    # ── 5. Content Calendar ──────────────────────────────────────────────
    print("  [5] Generating content calendar...")
    assets["content_calendar"] = _gemini(f"""Create a content calendar for this campaign.

Campaign: {goal}
Type: {campaign_type}
Timeline: {template['timeline']}
{product_context}

Create a week-by-week calendar in markdown table format:

| Week | Date Range | Channel | Asset | Status |
|------|-----------|---------|-------|--------|
| -4 | ... | Blog | Teaser post | Draft |
| -4 | ... | Social | Countdown series | Scheduled |
...

Include:
- Pre-campaign buildup (awareness, teaser content)
- Launch week (all channels firing)
- Post-campaign follow-up (nurture, retarget)
- Specific dates relative to today ({datetime.now().strftime('%Y-%m-%d')})
- Which email in the sequence goes out when
- Ad start/stop dates
- Social posting schedule""")

    # ── 6. Press Release (launch only) ───────────────────────────────────
    if "press_release" in template["assets"]:
        print("  [6] Generating press release...")
        assets["press_release"] = _gemini(f"""Write a press release for this campaign.

Campaign: {goal}
{product_context}
Keyword: {keyword}

FOR IMMEDIATE RELEASE
[HEADLINE — under 100 chars, newsworthy]
[CITY, DATE] — [Lede: who, what, when, where, why]
[Body with quote]
[About section]
Media Contact: press@example.com

Requirements: Standard AP style, no banned words, specific numbers.""")

    # ── Save or print ────────────────────────────────────────────────────
    if save_dir:
        out = Path(save_dir)
        out.mkdir(parents=True, exist_ok=True)

        # Save each asset
        for name, content in assets.items():
            (out / f"{name}.md").write_text(content)

        # Save campaign manifest — campaign_id is the cross-store join key
        manifest = {
            "campaign_id": campaign_id,
            "campaign_type": campaign_type,
            "goal": goal,
            "product": product_id,
            "keyword": keyword,
            "created": datetime.now(timezone.utc).isoformat(),
            "assets": list(assets.keys()),
            "timeline": template["timeline"],
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2))

        print(f"\n  Saved {len(assets)} assets to {out}/")
        for name in assets:
            print(f"    {name}.md")
        print(f"    manifest.json")

        # Auto-create the tracker row so the campaign is joinable from day 0
        # (previously a prose-only hook in harness/skill-contracts/campaign.yaml).
        try:
            from scripts.campaigns.campaign_tracker import create_campaign

            create_campaign(
                campaign_id,
                assets_dir=str(out),
                campaign_type=campaign_type,
                goal=goal,
                product=product_id,
                keyword=keyword,
                campaign_id=campaign_id,
            )
        except Exception as e:
            print(f"  Warning: could not create campaign tracker row: {e}")

        # Record the campaign_plan artifact (declared in kai/runtime/models.py).
        artifact_id = _record_campaign_plan_artifact(manifest, str(out))
        if artifact_id:
            print(f"  RuntimeStore campaign_plan artifact: {artifact_id}")
    else:
        for name, content in assets.items():
            print(f"\n{'═'*60}")
            print(f"  {name.upper().replace('_', ' ')}")
            print(f"{'═'*60}")
            print(content[:1500])
            if len(content) > 1500:
                print(f"\n  ... [{len(content) - 1500} more chars]")

    print(f"\n  Campaign: {len(assets)} assets generated")
    return assets


def main():
    parser = argparse.ArgumentParser(description="Generate multi-channel campaign assets")
    parser.add_argument("--goal", required=True, help="Campaign goal (e.g., 'product launch', 'Q1 webinar')")
    parser.add_argument("--product", required=True, help="Product ID from config.yaml")
    parser.add_argument("--keyword", required=True, help="Primary keyword/topic")
    parser.add_argument("--type", default="launch", choices=list(CAMPAIGN_TEMPLATES.keys()),
                        help="Campaign type")
    parser.add_argument("--save", help="Directory to save campaign assets")
    parser.add_argument("--campaign-id", help="Reuse an existing campaign id (default: mint cmp-YYYYMMDD-<slug>)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    assets = generate_campaign(
        goal=args.goal,
        product_id=args.product,
        keyword=args.keyword,
        campaign_type=args.type,
        save_dir=args.save,
        campaign_id=args.campaign_id,
    )

    if args.json:
        print(json.dumps({k: v[:500] + "..." for k, v in assets.items()}, indent=2))


if __name__ == "__main__":
    main()
