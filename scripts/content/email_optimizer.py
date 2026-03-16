#!/usr/bin/env python3
"""
Weekly Email Campaign Optimizer
Runs every Monday — analyzes Instantly campaigns, pauses losers,
clones winner with new variations, redistributes fresh leads.
Posts report to Discord #email channel.
"""

import requests
import os
import json
import random
from datetime import datetime, timezone
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv("/opt/cmo-analytics/.env")

INSTANTLY_KEY = os.getenv("INSTANTLY_API_KEY")
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1473791364721410139/your-webhook-here"  # #email webhook

HEADERS = {"Authorization": f"Bearer {INSTANTLY_KEY}", "Content-Type": "application/json"}

# Thresholds
MIN_CONTACTS = 40        # Need at least this many contacts to judge a campaign
WINNER_MIN_RATE = 0.03   # 3% reply rate = winner candidate
LOSER_MAX_RATE = 0.015   # <1.5% after MIN_CONTACTS = pause it
DAILY_LIMIT = 50

# Lead reservoir — the 8,830 lead pool that feeds the split testing system each week
# Leads are pulled from here in batches and split across new variation campaigns
RESERVOIR_CAMPAIGN_ID = "f15602ef-169a-4efa-aa30-406cf9607d82"  # KaiCalls - Party Vendors (ABP + AI Calls)
WEEKLY_BATCH_SIZE = 400   # Pull this many from reservoir each week, split across 4 variations (100 each)

SCHEDULE = {
    "schedules": [{
        "name": "Weekday mornings",
        "timing": {"from": "09:00", "to": "11:00"},
        "days": {"1": True, "2": True, "3": True, "4": True},
        "timezone": "America/Detroit"
    }]
}

# Variation hooks — new angles to test off the winner's formula
SUBJECT_VARIATIONS = [
    ("{{firstName}} - who answers?", "standard"),
    ("{{firstName}} - busy season", "seasonal"),
    ("quick question {{firstName}}", "curiosity"),
    ("{{firstName}} - Saturday afternoon", "scenario"),
    ("missed booking {{firstName}}?", "pain"),
    ("{{firstName}} - while you're on a job", "context"),
    ("how {{companyName}} handles calls", "company"),
    ("{{firstName}} - 2 missed calls today", "specific"),
]

BODY_TEMPLATES = [
    # Winner original
    "<div>When you're setting up at an event and a new customer calls — who answers?<br /><br />Kai</div>",
    # Busy season
    "<div>Party season is picking up — who's answering your phone when you're on a job?<br /><br />We built an AI that picks up 24/7 and texts you the lead details instantly.<br /><br />Mind if I show you?<br /><br />Kai</div>",
    # Specific scenario
    "<div>Saturday afternoon, you're setting up a tent, a customer calls about booking you.<br /><br />Who answers?<br /><br />Kai</div>",
    # One question
    "<div>If a customer calls while you're at an event — do they get an answer or a voicemail?<br /><br />Kai</div>",
    # Pain point
    "<div>One party vendor told us he was losing $800/week to missed calls while on jobs.<br /><br />Who answers yours?<br /><br />Kai</div>",
    # Free listing combo
    "<div>When you're setting up at an event and a new customer calls — who answers?<br /><br />We send party leads to vendors in your area for free. But the ones who answer book the most.<br /><br />Mind if I show you how both work?<br /><br />Kai</div>",
    # Upfront
    "<div>Sorry if this is random — but what happens to calls that come in while you're on a job?<br /><br />Kai</div>",
    # Context
    "<div>Most party vendors I talk to say new customer calls go straight to voicemail when they're setting up.<br /><br />Is that the case for {{companyName}}?<br /><br />Kai</div>",
]

FOLLOWUPS = [
    {
        "type": "email", "delay": 2, "delay_unit": "days",
        "variants": [{"subject": "Re: {{firstName}} - who answers?",
                      "body": "<div>Hey — making sure this didn't get buried.<br /><br />Kai</div>"}]
    },
    {
        "type": "email", "delay": 3, "delay_unit": "days",
        "variants": [{"subject": "Re: {{firstName}} - who answers?",
                      "body": "<div>{{firstName}} — one vendor told us he was losing $800/week to missed calls on jobs.<br /><br />Now the AI picks up, gets the details, texts him instantly.<br /><br />Worth a look?<br /><br />Kai</div>"}]
    },
    {
        "type": "email", "delay": 3, "delay_unit": "days",
        "variants": [{"subject": "Re: {{firstName}} - who answers?",
                      "body": "<div>I'll assume timing isn't right. Reach out when it changes.<br /><br />Kai</div>"}]
    }
]


def get_all_campaigns():
    resp = requests.get("https://api.instantly.ai/api/v2/campaigns?limit=50", headers=HEADERS)
    return {c["id"]: c for c in resp.json().get("items", [])}


def get_campaign_stats():
    """Paginate through all leads and compute per-campaign stats."""
    stats = defaultdict(lambda: {"contacted": 0, "replies": 0, "fresh": 0})
    cursor = None
    while True:
        payload = {"limit": 100}
        if cursor:
            payload["starting_after"] = cursor
        resp = requests.post("https://api.instantly.ai/api/v2/leads/list", headers=HEADERS, json=payload)
        items = resp.json().get("items", [])
        if not items:
            break
        for lead in items:
            cid = lead.get("campaign")
            if not cid:
                continue
            if lead.get("timestamp_last_contact"):
                stats[cid]["contacted"] += 1
            else:
                stats[cid]["fresh"] += 1
            if lead.get("email_reply_count", 0) > 0:
                stats[cid]["replies"] += 1
        cursor = resp.json().get("next_starting_after")
        if not cursor:
            break
    return stats


def get_fresh_leads(campaign_id, limit=2000):
    """Get uncontacted leads from a campaign."""
    leads = []
    cursor = None
    while len(leads) < limit:
        payload = {"campaign": campaign_id, "limit": 100}
        if cursor:
            payload["starting_after"] = cursor
        resp = requests.post("https://api.instantly.ai/api/v2/leads/list", headers=HEADERS, json=payload)
        items = resp.json().get("items", [])
        if not items:
            break
        for l in items:
            if not l.get("timestamp_last_contact") and l.get("email"):
                leads.append({
                    "email": l["email"],
                    "firstName": l.get("first_name", ""),
                    "lastName": l.get("last_name", ""),
                    "companyName": l.get("company_name", ""),
                    "website": l.get("website", "")
                })
        cursor = resp.json().get("next_starting_after")
        if not cursor:
            break
    return leads


def pause_campaign(cid):
    return requests.post(f"https://api.instantly.ai/api/v2/campaigns/{cid}/pause", headers=HEADERS, json={}).json()


def activate_campaign(cid):
    return requests.post(f"https://api.instantly.ai/api/v2/campaigns/{cid}/activate", headers=HEADERS, json={}).json()


ALL_SENDING_ACCOUNTS = [
    "hello@startkaicalls.com", "kai@startkaicalls.com",
    "support@hellokaicalls.com", "kai@hellokaicalls.com",
    "kai@meetkaicalls.com", "team@meetkaicalls.com",
    "hello@usekaicalls.com", "kai@usekaicalls.com",
    "kai@getkaicalls.com", "kai@trykaicalls.com",
]

def create_variation(name, subject, body):
    payload = {
        "name": name,
        "daily_limit": DAILY_LIMIT,
        "stop_on_reply": True,
        "text_only": True,
        "email_list": ALL_SENDING_ACCOUNTS,
        "campaign_schedule": SCHEDULE,
        "sequences": [{"steps": [
            {"type": "email", "delay": 1, "delay_unit": "days",
             "variants": [{"subject": subject, "body": body}]}
        ] + FOLLOWUPS}]
    }
    resp = requests.post("https://api.instantly.ai/api/v2/campaigns", headers=HEADERS, json=payload)
    return resp.json()


def upload_leads(campaign_id, leads):
    total = 0
    for i in range(0, len(leads), 500):
        batch = leads[i:i+500]
        resp = requests.post(
            "https://api.instantly.ai/api/v2/leads/add",
            headers=HEADERS,
            json={"campaign_id": campaign_id, "leads": batch}
        )
        total += resp.json().get("leads_uploaded", 0)
    return total


def run_weekly_optimization():
    print(f"\n{'='*60}")
    print(f"WEEKLY EMAIL OPTIMIZER — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    campaigns = get_all_campaigns()
    stats = get_campaign_stats()

    # Only evaluate active/paused campaigns, skip completed
    active = {cid: s for cid, s in stats.items()
              if campaigns.get(cid, {}).get("status") in [1, 2]
              and s["contacted"] >= MIN_CONTACTS}

    if not active:
        print("Not enough data yet. Check back next week.")
        return

    # Rank by reply rate
    ranked = sorted(active.items(), key=lambda x: x[1]["replies"] / max(x[1]["contacted"], 1), reverse=True)

    winner_id, winner_stats = ranked[0]
    winner_rate = winner_stats["replies"] / winner_stats["contacted"]
    winner_name = campaigns.get(winner_id, {}).get("name", winner_id)
    winner_seq = campaigns.get(winner_id, {}).get("sequences", [{}])[0].get("steps", [{}])[0]
    winner_subject = winner_seq.get("variants", [{}])[0].get("subject", "{{firstName}} - who answers?")

    print(f"🏆 WINNER: {winner_name}")
    print(f"   Rate: {winner_rate*100:.1f}% ({winner_stats['replies']} replies / {winner_stats['contacted']} contacted)")
    print(f"   Subject: {winner_subject}\n")

    # Identify losers (active campaigns below threshold)
    losers = [(cid, s) for cid, s in active.items()
              if cid != winner_id
              and s["contacted"] >= MIN_CONTACTS
              and s["replies"] / s["contacted"] < LOSER_MAX_RATE
              and campaigns.get(cid, {}).get("status") == 1]

    paused_campaigns = []
    fresh_leads = []

    for cid, s in losers:
        name = campaigns.get(cid, {}).get("name", cid)
        pause_campaign(cid)
        leads = get_fresh_leads(cid)
        fresh_leads.extend(leads)
        paused_campaigns.append({"name": name, "rate": f"{(s['replies']/s['contacted']*100):.1f}%", "leads_recovered": len(leads)})
        print(f"⏸️  Paused: {name} ({s['replies']}/{s['contacted']} = {s['replies']/s['contacted']*100:.1f}%) — {len(leads)} leads recovered")

    print(f"\n📦 Fresh leads recovered from paused campaigns: {len(fresh_leads)}")

    # Always top up from reservoir regardless of how many were recovered from losers
    reservoir_leads = get_fresh_leads(RESERVOIR_CAMPAIGN_ID, limit=WEEKLY_BATCH_SIZE)
    print(f"📦 Reservoir pull: {len(reservoir_leads)} leads from main pool ({RESERVOIR_CAMPAIGN_ID})")
    fresh_leads.extend(reservoir_leads)
    print(f"📦 Total leads for this week's variations: {len(fresh_leads)}")

    if not fresh_leads:
        print("No fresh leads available — reservoir may be exhausted.")
        return

    # Pick 4 unused body/subject combos for new campaigns
    week_num = datetime.now().isocalendar()[1]
    used_subjects = {campaigns.get(cid, {}).get("name", "") for cid in stats}
    
    # Select 4 variation combos
    random.seed(week_num)
    bodies = random.sample(BODY_TEMPLATES[1:], min(4, len(BODY_TEMPLATES)-1))
    subjects = random.sample(SUBJECT_VARIATIONS, min(4, len(SUBJECT_VARIATIONS)))

    new_campaigns = []
    chunk = len(fresh_leads) // len(bodies)

    for i, (body, (subject, tag)) in enumerate(zip(bodies, subjects)):
        name = f"PV W{week_num} V{i+1} - {tag.title()}"
        camp = create_variation(name, subject, body)
        camp_id = camp.get("id")
        if not camp_id:
            print(f"Failed to create {name}: {camp}")
            continue

        start = i * chunk
        end = start + chunk if i < len(bodies) - 1 else len(fresh_leads)
        batch = fresh_leads[start:end]
        uploaded = upload_leads(camp_id, batch)
        activate_campaign(camp_id)

        new_campaigns.append({"name": name, "id": camp_id, "subject": subject, "leads": uploaded})
        print(f"✅ Created + live: {name} | Subject: {subject} | {uploaded} leads")

    # Post to Discord
    report = build_discord_report(winner_name, winner_rate, winner_stats,
                                   paused_campaigns, new_campaigns, len(fresh_leads))
    post_to_discord(report)
    print("\nReport posted to #email ✅")


def build_discord_report(winner_name, winner_rate, winner_stats, paused, new_camps, total_leads):
    date = datetime.now(timezone.utc).strftime("%b %d")
    lines = [
        f"## 📊 Weekly Email Optimization — {date}",
        f"",
        f"### 🏆 Winner",
        f"**{winner_name}**",
        f"Reply rate: **{winner_rate*100:.1f}%** ({winner_stats['replies']} replies / {winner_stats['contacted']} contacted)",
        f"",
        f"### ⏸️ Paused ({len(paused)} campaigns)",
    ]
    for p in paused:
        lines.append(f"- {p['name']} — {p['rate']} reply rate | {p['leads_recovered']} leads recovered")

    lines += [
        f"",
        f"### 🚀 New Variations Live ({len(new_camps)} campaigns, {total_leads} leads split)",
    ]
    for c in new_camps:
        lines.append(f"- **{c['name']}** | `{c['subject']}` | {c['leads']} leads")

    lines += [
        f"",
        f"All new campaigns follow the winning hook formula with fresh copy angles.",
        f"Next optimization: next Monday 9am ET."
    ]
    return "\n".join(lines)


def post_to_discord(message):
    # Uses OpenClaw message tool — post to #email channel
    # This is called externally by the cron via openclaw
    report_path = "/opt/cmo-analytics/reports/email_optimizer_latest.md"
    with open(report_path, "w") as f:
        f.write(message)
    print(f"\n--- DISCORD REPORT ---\n{message}\n---")


if __name__ == "__main__":
    run_weekly_optimization()
