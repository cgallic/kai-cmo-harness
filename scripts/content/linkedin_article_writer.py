#!/usr/bin/env python3
"""
LinkedIn Article Writer — runs daily at 8am ET
Picks the next unwritten headline from the bank, writes a full article via OpenAI,
saves to /root/.openclaw/workspace/content/connor-gallic-social/drafts/YYYY-MM-DD.md
Pings Connor in Discord #seo channel with a preview and the file path.

Cluster rotation order: kaicalls → seo → ai-ops → building-in-public → local-biz → validation
Articles written in order within each cluster before rotating.
"""

import os
import json
import sys
import requests
from datetime import datetime
from pathlib import Path
import openai

# ── Config ───────────────────────────────────────────────────────────────────
ENV_FILE       = "/opt/cmo-analytics/.env"
DRAFTS_DIR     = Path("/root/.openclaw/workspace/content/connor-gallic-social/drafts")
PROGRESS_FILE  = Path("/opt/cmo-analytics/data/linkedin_article_progress.json")
HEADLINE_BANK  = Path("/root/.openclaw/workspace/content/connor-gallic-social/linkedin-headline-bank.md")
DISCORD_CHANNEL = "1477363374533775472"  # #seo

CONNOR_VOICE = """
You are writing a LinkedIn article in Connor Gallic's voice. Connor is a bootstrapped founder building 7 AI products simultaneously.

Voice rules (non-negotiable):
- Lead with the data point, the scenario, or the specific problem — never with "I'm excited to share"
- Short paragraphs: 2–4 sentences max
- Conversational but not casual — explains things like to a smart friend, not a conference audience
- Uses real specifics: product names, dollar amounts (no MRR), time of day, exact numbers
- Walks through problems as scenarios: "Someone calls at 11pm. They're in an accident. Three firms get the call. First one to engage wins the case."
- Answers the question before explaining how
- No hype. No adjectives where numbers work better.
- Ends with the product or the so-what — never with an engagement question

Banned phrases (hard block):
leverage, utilize, synergy, innovative, in today's rapidly evolving, it's important to note,
I'd be happy to, great question, as we all know, in conclusion, moving forward, circle back,
touch base, game-changer, thought leader, exciting journey, at the end of the day

Products (reference accurately):
- KaiCalls (kaicalls.com) — AI call answering for law firms + home services, $69.99/mo entry
- BuildWithKai (buildwithkai.com) — AI business idea validator + plan builder
- Zehrava (zehrava.com) — write-path control for AI agents (npm + PyPI)
- Awesome Backyard Parties (awesomebackyardparties.com) — party rental lead marketplace
- Starrs Party (starrsparty.com) — NJ tent + party rental company
- VocalScribe (vocalscribe.xyz) — voice transcription
- MeetKai (meetkai.xyz) — AI CMO agent system showcase

Do NOT include MRR or specific revenue figures.
"""

# ── Cluster definitions (ordered) ────────────────────────────────────────────
CLUSTERS = [
    {
        "id": "tent-rental-biz",
        "name": "Tent Rental Companies — KaiCalls Vertical",
        "context": """
Real industry pain points (grounded in research):
- The owner IS the delivery crew — during Saturday setup, the person who'd answer the phone is lifting a 40x60 frame tent
- InflatableOffice (party rental software) sells a paid Phone Integration add-on — the industry already pays for call management
- Double bookings are a top complaint: same item promised verbally to two customers during high-volume periods
- Jan–March is booking season for spring/summer events; April–October is delivery/setup season when crews are in the field
- First to call back wins — party rental is commoditized; response speed is the differentiator, not price
- Customers who call instead of emailing convert at much higher rates — and they call on Saturday afternoons
- Voicemail in party rental = lost booking. Customers call 3 companies; first one to engage gets it.
- Crew answering phones = distracted crew = setup mistakes and customer complaints
- Small operators (2–5 trucks) can't afford a full-time office person but are missing 30–40% of inbound inquiries
""",
        "headlines": [
            "The Owner IS the Delivery Crew. That's Why Tent Rental Companies Miss So Many Calls.",
            "Why Party Rental Companies Lose Their Best Leads on Saturday Afternoons",
            "The Double Booking Problem in Party Rentals Starts With a Phone Call Nobody Logged",
            "What Happens When the Person Who Should Answer Your Phone Is Setting Up a 40x60 Tent",
            "January Through March Is When You Book Your Season. It's Also When Calls Go Unanswered.",
            "First to Call Back Wins the Wedding Tent Job. Most Companies Call Back Monday.",
            "Why Voicemail Is a Booking Killer for Event Rental Companies",
            "The Real Cost of a Missed Party Rental Inquiry (It's Not Just One Booking)",
            "How Two-Truck Tent Rental Operations Lose 30% of Inbound Leads Before Noon",
            "Why Customers Who Call a Party Rental Company Convert 3x Better Than Email — And Still Go to Voicemail",
            "The Crew-on-Site Problem: Who Answers the Phone When Everyone's on a Job?",
            "How Seasonal Party Rental Companies Handle Peak Booking Volume Without Hiring",
            "Why the Busiest Week of the Season Is Also Your Worst Week for Answering Phones",
            "What Party Rental Customers Actually Do When They Hit Voicemail (The Answer Is Bad)",
            "How AI Call Answering Fixes the Tent Rental Industry's Oldest Problem",
        ]
    },
    {
        "id": "kaicalls",
        "name": "AI Call Answering (KaiCalls)",
        "headlines": [
            "The After-Hours Call Problem Nobody in Legal Talks About",
            "Why Personal Injury Firms Lose Cases at 11pm",
            "What Happens When a Law Firm's Phone Goes to Voicemail on Saturday",
            "The Back-and-Forth Tax: How Voicemail Is Costing Small Law Firms Real Clients",
            "We Analyzed 1,000 After-Hours Calls. Here's What We Found.",
            "How a Solo Practice Handles Inbound Calls Like a 10-Person Firm",
            "Why the First Firm to Call Back Wins the Case (And What That Means for After-Hours Coverage)",
            "The True Cost of a Human Receptionist vs. an AI One — Full Breakdown",
            "HVAC Companies Miss 40% of After-Hours Calls. Here's What That Costs.",
            "AI Phone Agents for Law Firms: What Works, What Doesn't, and What to Watch Out For",
            "What '24/7 Coverage' Actually Means When You're a Two-Attorney PI Firm",
            "How Medical Offices Handle After-Hours Calls Without Hiring a Night Shift",
            "The Intake Call Is the Most Important Call Your Practice Takes. Most Firms Blow It.",
            "Why We Priced an AI Receptionist at $69.99 When the Competition Charges $650",
            "What Good AI Call Handling Sounds Like (and What Red Flags to Listen For)",
        ]
    },
    {
        "id": "seo",
        "name": "SEO + Programmatic Content",
        "headlines": [
            "The Page-1 Rankings That Were Getting Zero Clicks (And the 5-Minute Fix)",
            "How We Built a Topical SEO Map Across 9 Sites in One Session",
            "Programmatic Geo Pages: How to Rank in 500 Cities Without Writing 500 Articles",
            "The Next.js SEO Mistake That's Killing Your Rankings on Every Page",
            "Why Fixing What Already Ranks Is Faster Than Building New Content",
            "What Google Search Console Tells You That Keyword Research Can't",
            "The Topical Map Framework I Use Before Writing a Single Word of Content",
            "Pillar Pages vs. Topic Clusters: The Distinction That Actually Matters",
            "How a Local Business Can Compete With National Brands in Search",
            "A 30-Year-Old NJ Rental Company Had 5 Page-1 Rankings and Zero Clicks. Here's Why.",
            "What AI Overviews Mean for Long-Tail SEO (Real Data, Not Speculation)",
            "The Redirect Audit That Recovered 18 Months of Lost Link Equity",
            "Why Most SEO Audits Produce PDFs Nobody Implements",
            "Structured Data Is Not Optional Anymore — Here's What to Add First",
            "The Monthly SEO Refresh Pipeline I Built to Run Without Me",
        ]
    },
    {
        "id": "ai-ops",
        "name": "AI Agent Architecture + Ops",
        "headlines": [
            "Write-Path Control: The AI Architecture Layer Nobody Talks About",
            "Why Your AI Agent Should Ask for Permission Before It Does Anything Consequential",
            "The Read Path vs. the Write Path: How to Deploy AI Agents Without Getting Burned",
            "How I Run Business Operations With One AI Agent and a Cron Job",
            "The Stack I Use to Run 7 Products Without Employees",
            "What Responsible AI Deployment Looks Like in a Small Business Context",
            "Why I Built a Gating System Instead of Just Trusting My AI Agent",
            "How an AI Agent Preps My Vendor Calls Before I Open My Laptop",
            "The Calendar Trigger That Replaced Half My Morning Routine",
            "What Happens When You Let an AI Agent Manage Your Ops Ungated (And How to Fix It)",
            "Agent Orchestration at the Indie Founder Level: What's Actually Practical",
            "How to Know Which Tasks to Automate and Which Ones to Keep",
            "The Daily Report That Runs at 8am Whether I'm Awake or Not",
            "Why Discord Is My Ops Dashboard (And How That Setup Works)",
            "What 'AI CMO' Actually Means in Practice — No Hype Version",
        ]
    },
    {
        "id": "building-in-public",
        "name": "Building in Public / Multi-Product Founder",
        "headlines": [
            "I Run 7 Products. Here's How I Don't Go Insane.",
            "What Building in Public Actually Looks Like When Things Aren't Going Well",
            "The Attention Tax of Running Multiple Products at Once",
            "Two Products, Not Seven: What I'd Tell Myself at the Start",
            "How to Know When a Side Project Should Become the Main Thing",
            "What 'Bootstrapped' Actually Means When You're Three Products In",
            "The Difference Between a Product and a Business (I Learned This the Hard Way)",
            "Why I Build AI Products to Run Themselves",
            "Validation Is a Step, Not a Phase: How to Know if Your Idea Has a Market",
            "The Compounding Cost of Skipping the Validation Step",
            "What I Stopped Doing as a Founder That Made Everything Else Work Better",
            "How I Decide Which Product Gets My Time This Week",
            "The Case for Building a Boring Product Nobody Talks About",
            "Revenue vs. Traction: Which One Actually Matters When You're Early",
            "What 90 Days of 'Building in Public' Taught Me About Accountability",
        ]
    },
    {
        "id": "local-biz",
        "name": "Local Business + AI",
        "headlines": [
            "What a 30-Year-Old NJ Family Business Learned From an AI Audit",
            "How Local Businesses Win Search Without a Marketing Budget",
            "The Google Ranking Signals Local Businesses Are Leaving on the Table",
            "Why Local SEO and AI Are a Better Combination Than Most People Realize",
            "How a Party Rental Company Gets 400+ Leads a Month Without Sales Staff",
            "What 'Going Digital' Actually Requires for a Service Business",
            "The AI Tools That Made Sense for a Seasonal Local Business",
            "How to Get Your Local Business to Page 1 Without Hiring an Agency",
            "What Happens When You Build a Marketplace for an Industry Nobody Has Digitized",
            "The Vendor Side of a Marketplace: Why Supply Is Harder Than Demand",
            "How Small Service Businesses Can Use AI for Intake Without Losing the Human Touch",
            "Why 'Local' Is a Moat, Not a Limitation",
            "The Difference Between a Lead and a Customer for a Service Business",
            "What a 461-Lead Waitlist Tells You About an Underserved Market",
            "How One Friday Sync Call Became a Systemized Operation",
        ]
    },
    {
        "id": "validation",
        "name": "Product Validation + BuildWithKai",
        "headlines": [
            "How to Validate a Business Idea in 48 Hours Without Building Anything",
            "The $50 Test That Saves 6 Months of Building the Wrong Thing",
            "Why No Competition in a Market Is a Red Flag, Not an Opportunity",
            "The Problem Statement Test: If You Can't Write It in One Sentence, Keep Going",
            "What a 4% Waitlist Conversion Rate Actually Means",
            "How to Know if Your Pricing Is in the Right Range Before You Build",
            "The Go-to-Market Question Most Founders Skip Until It's Too Late",
            "Why the Idea Isn't the Problem (And What Is)",
            "How to Use Search Data to Validate Demand Before Writing a Line of Code",
            "What the Competitive Landscape Actually Tells You About Your Market Timing",
            "The Founder's Math: How Many Customers Do You Actually Need?",
            "How to Turn a Business Idea Into a Testable Hypothesis in One Afternoon",
            "Why Most Business Plans Don't Survive Contact With Real Customers",
            "What AI Can and Can't Tell You About Whether Your Idea Will Work",
            "The Fastest Way to Know if Strangers Would Pay for What You're Building",
        ]
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_env():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    # Initialize: cluster_idx=0, article_idx=0 for each cluster
    return {"cluster_idx": 0, "written": {c["id"]: 0 for c in CLUSTERS}}


def save_progress(p: dict):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(p, indent=2))


def next_headline(progress: dict) -> tuple[str, str, str, str]:
    """Returns (cluster_id, cluster_name, headline, context)"""
    start = progress["cluster_idx"] % len(CLUSTERS)

    for offset in range(len(CLUSTERS)):
        idx = (start + offset) % len(CLUSTERS)
        cluster = CLUSTERS[idx]
        written = progress["written"].get(cluster["id"], 0)
        if written < len(cluster["headlines"]):
            progress["cluster_idx"] = idx
            headline = cluster["headlines"][written]
            progress["written"][cluster["id"]] = written + 1
            if progress["written"][cluster["id"]] >= len(cluster["headlines"]):
                progress["cluster_idx"] = (idx + 1) % len(CLUSTERS)
            context = cluster.get("context", "")
            return cluster["id"], cluster["name"], headline, context

    return None, None, None, None  # all exhausted


def write_article(headline: str, cluster_name: str, cluster_context: str = "") -> str:
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    context_block = f"\n\nIndustry context to ground the article in real pain points:\n{cluster_context}" if cluster_context else ""

    prompt = f"""Write a LinkedIn article with this headline: "{headline}"

Cluster topic: {cluster_name}{context_block}

Requirements:
- 900–1,200 words
- Start with a specific scenario, data point, or concrete problem — NOT "I'm excited to share" or any opener about yourself
- Short paragraphs (2–4 sentences max)
- Use bold headers (##) to break the article into 4–6 sections
- Each section delivers one concrete insight — no padding
- End with a specific so-what or product mention (if relevant to the topic)
- Follow all voice rules exactly

Output the full article in markdown. Include the title as an H1 at the top."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CONNOR_VOICE},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()


def post_discord(channel_id: str, message: str):
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print(f"[discord] {message}")
        return
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"content": message})
    if resp.status_code not in (200, 201):
        print(f"[discord error] {resp.status_code}: {resp.text}")


def main():
    load_env()

    today = datetime.now().strftime("%Y-%m-%d")
    draft_path = DRAFTS_DIR / f"{today}.md"

    # Skip if already wrote today
    if draft_path.exists():
        print(f"[linkedin_writer] Draft already exists for {today}, skipping.")
        return

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    progress = load_progress()
    cluster_id, cluster_name, headline, cluster_context = next_headline(progress)

    if not headline:
        print("[linkedin_writer] All headlines exhausted.")
        return

    print(f"[linkedin_writer] Writing: {headline}")
    article = write_article(headline, cluster_name, cluster_context)

    # Add metadata header
    output = f"""---
date: {today}
cluster: {cluster_name}
status: draft
---

{article}
"""

    draft_path.write_text(output)
    save_progress(progress)

    print(f"[linkedin_writer] Saved to {draft_path}")

    # Get first 3 lines of article body for preview (skip frontmatter + title)
    lines = [l for l in article.split("\n") if l.strip() and not l.startswith("#")]
    preview = lines[0][:200] if lines else headline

    msg = (
        f"📝 **LinkedIn article draft ready** — {today}\n"
        f"**{headline}**\n"
        f"*Cluster: {cluster_name}*\n\n"
        f"> {preview}...\n\n"
        f"File: `content/connor-gallic-social/drafts/{today}.md`\n"
        f"Review → post to LinkedIn when ready."
    )
    post_discord(DISCORD_CHANNEL, msg)


if __name__ == "__main__":
    main()
