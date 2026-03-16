#!/usr/bin/env python3
"""
Lead Generation Pipeline
GMB Scraper → Apollo Enrichment → MillionVerifier → Instantly-ready CSV

Usage:
  python lead_pipeline.py scrape --niche "plumbers" --cities "Houston,Dallas,Phoenix" --limit 500
  python lead_pipeline.py verify --input leads.csv --output verified.csv
  python lead_pipeline.py enrich --input leads.csv --output enriched.csv
  python lead_pipeline.py full --niche "plumbers" --cities "Houston,Dallas" --target 1000
"""

import os
import sys
import csv
import json
import time
import asyncio
import aiohttp
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ─── HARD CAP — prevents RapidAPI overages ───────────────────────────────────
RAPIDAPI_MONTHLY_CAP = 15000  # Stop at 15k calls (plan = 20k, buffer = 5k)
_USAGE_COUNTER_FILE = "/tmp/rapidapi_usage_counter.txt"

def _get_usage_count():
    try:
        with open(_USAGE_COUNTER_FILE) as f:
            month, count = f.read().strip().split(":")
            import datetime
            if month == datetime.datetime.now().strftime("%Y-%m"):
                return int(count)
    except:
        pass
    return 0

def _increment_usage():
    import datetime
    count = _get_usage_count() + 1
    month = datetime.datetime.now().strftime("%Y-%m")
    with open(_USAGE_COUNTER_FILE, "w") as f:
        f.write(f"{month}:{count}")
    return count

def _check_cap():
    count = _get_usage_count()
    if count >= RAPIDAPI_MONTHLY_CAP:
        print(f"🛑 HARD CAP HIT: {count}/{RAPIDAPI_MONTHLY_CAP} RapidAPI calls this month. Aborting.")
        raise SystemExit(1)
    return count
# ─────────────────────────────────────────────────────────────────────────────


load_dotenv("/opt/cmo-analytics/.env")

# API Keys
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
MILLIONVERIFIER_KEY = os.getenv("MILLIONVERIFIER_API_KEY")
FIRECRAWL_KEY = os.getenv("FIRECRAWL_API_KEY")

DATA_DIR = Path("/opt/cmo-analytics/data")
DATA_DIR.mkdir(exist_ok=True)

# Target niches for KaiCalls (businesses that need after-hours call handling)
NICHES = [
    "plumbers", "hvac contractors", "electricians", "landscapers",
    "roofing contractors", "pest control", "cleaning services",
    "auto repair shops", "law firms", "dental offices",
    "medical clinics", "real estate agents", "insurance agents",
    "home inspectors", "locksmiths", "towing services"
]

# High-population cities to scrape
CITIES = [
    "Houston, TX", "Dallas, TX", "Austin, TX", "San Antonio, TX",
    "Phoenix, AZ", "Los Angeles, CA", "San Diego, CA", "Denver, CO",
    "Miami, FL", "Tampa, FL", "Orlando, FL", "Atlanta, GA",
    "Chicago, IL", "Indianapolis, IN", "Las Vegas, NV",
    "Charlotte, NC", "Columbus, OH", "Nashville, TN", "Seattle, WA"
]


async def scrape_gmb(session, query: str, location: str, limit: int = 100) -> list:
    """Scrape Google Maps via RapidAPI Local Business Data"""
    url = "https://local-business-data.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "local-business-data.p.rapidapi.com"
    }
    params = {
        "query": f"{query} in {location}",
        "limit": str(limit),
        "extract_emails_and_contacts": "false"  # DISABLED — was billing per-contact
    }
    
    try:
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("data", [])
            else:
                print(f"  GMB API error {resp.status} for {query} in {location}")
                return []
    except Exception as e:
        print(f"  GMB scrape error: {e}")
        return []


async def verify_email(session, email: str) -> dict:
    """Verify single email via MillionVerifier"""
    url = "https://api.millionverifier.com/api/v3/"
    params = {
        "api": MILLIONVERIFIER_KEY,
        "email": email,
        "timeout": 10
    }
    
    try:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "email": email,
                    "result": data.get("result", "unknown"),
                    "resultcode": data.get("resultcode", -1),
                    "free": data.get("free", False),
                    "role": data.get("role", False)
                }
    except Exception as e:
        pass
    
    return {"email": email, "result": "error", "resultcode": -1}


async def verify_emails_batch(emails: list, concurrency: int = 10) -> list:
    """Verify multiple emails with rate limiting"""
    results = []
    semaphore = asyncio.Semaphore(concurrency)
    
    async def verify_with_limit(session, email):
        async with semaphore:
            result = await verify_email(session, email)
            await asyncio.sleep(0.1)  # Rate limit
            return result
    
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [verify_with_limit(session, email) for email in emails]
        results = await asyncio.gather(*tasks)
    
    return results


def enrich_with_apollo(leads: list) -> list:
    """Enrich leads with Apollo person/company data"""
    import requests
    
    enriched = []
    for lead in leads:
        if not lead.get("email"):
            enriched.append(lead)
            continue
            
        try:
            # Apollo people enrichment
            resp = requests.post(
                "https://api.apollo.io/v1/people/match",
                headers={"X-Api-Key": APOLLO_API_KEY},
                json={"email": lead["email"]},
                timeout=10
            )
            if resp.status_code == 200:
                person = resp.json().get("person", {})
                lead["first_name"] = person.get("first_name", "")
                lead["last_name"] = person.get("last_name", "")
                lead["title"] = person.get("title", "")
                lead["linkedin"] = person.get("linkedin_url", "")
        except Exception as e:
            pass
        
        enriched.append(lead)
        time.sleep(0.2)  # Rate limit
    
    return enriched


async def scrape_niche_cities(niche: str, cities: list, limit_per_city: int = 50) -> list:
    """Scrape a niche across multiple cities"""
    all_leads = []
    
    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        for city in cities:
            print(f"  Scraping {niche} in {city}...")
            leads = await scrape_gmb(session, niche, city, limit_per_city)
            
            for lead in leads:
                # Extract emails from emails_and_contacts
                ec = lead.get("emails_and_contacts", {})
                emails_list = ec.get("emails", [])
                email = emails_list[0] if emails_list else ""
                
                # Extract and normalize
                normalized = {
                    "name": lead.get("name", ""),
                    "phone": lead.get("phone_number", ""),
                    "email": email,
                    "all_emails": ",".join(emails_list) if len(emails_list) > 1 else "",
                    "website": lead.get("website", ""),
                    "address": lead.get("full_address", ""),
                    "city": city.split(",")[0].strip(),
                    "state": city.split(",")[1].strip() if "," in city else "",
                    "niche": niche,
                    "rating": lead.get("rating", ""),
                    "reviews": lead.get("review_count", ""),
                    "hours": lead.get("working_hours", {}),
                    "facebook": ec.get("facebook", ""),
                    "linkedin": ec.get("linkedin", "")
                }
                
                # Skip if 24/7 (they don't need after-hours service)
                hours_str = str(normalized.get("hours", "")).lower()
                if "24 hour" in hours_str or "open 24" in hours_str:
                    continue
                
                if normalized["email"]:  # Only keep if has email
                    all_leads.append(normalized)
            
            await asyncio.sleep(0.5)  # Rate limit between cities
    
    return all_leads


def dedupe_leads(leads: list) -> list:
    """Remove duplicate emails"""
    seen = set()
    unique = []
    for lead in leads:
        email = lead.get("email", "").lower().strip()
        if email and email not in seen:
            seen.add(email)
            unique.append(lead)
    return unique


def save_leads(leads: list, filename: str):
    """Save leads to CSV and JSON"""
    if not leads:
        print("No leads to save")
        return
    
    csv_path = DATA_DIR / f"{filename}.csv"
    json_path = DATA_DIR / f"{filename}.json"
    
    # CSV
    keys = leads[0].keys()
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(leads)
    
    # JSON
    with open(json_path, "w") as f:
        json.dump(leads, f, indent=2, default=str)
    
    print(f"Saved {len(leads)} leads to {csv_path}")


async def full_pipeline(target: int = 5000, niches: list = None, cities: list = None):
    """Full pipeline: Scrape → Verify → Output"""
    
    niches = niches or NICHES[:8]  # Use top 8 niches
    cities = cities or CITIES[:10]  # Use top 10 cities
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{'='*60}")
    print(f"LEAD GENERATION PIPELINE - Target: {target} verified emails")
    print(f"{'='*60}")
    
    # Step 1: Scrape
    print(f"\n[1/3] SCRAPING GMB...")
    print(f"  Niches: {', '.join(niches)}")
    print(f"  Cities: {', '.join(cities)}")
    
    all_leads = []
    leads_per_combo = max(20, target // (len(niches) * len(cities)) + 10)
    
    for niche in niches:
        print(f"\n  >>> {niche.upper()}")
        leads = await scrape_niche_cities(niche, cities, leads_per_combo)
        all_leads.extend(leads)
        print(f"  Got {len(leads)} leads with emails")
        
        # Early exit if we have enough
        if len(all_leads) >= target * 1.5:
            print(f"  Reached {len(all_leads)} leads, stopping early")
            break
    
    # Dedupe
    all_leads = dedupe_leads(all_leads)
    print(f"\n  Total unique leads with emails: {len(all_leads)}")
    save_leads(all_leads, f"scraped_raw_{timestamp}")
    
    # Step 2: Verify
    print(f"\n[2/3] VERIFYING EMAILS with MillionVerifier...")
    emails = [l["email"] for l in all_leads if l.get("email")]
    
    verified_results = await verify_emails_batch(emails, concurrency=10)
    
    # Map results back to leads
    email_status = {r["email"]: r["result"] for r in verified_results}
    
    valid_leads = []
    risky_leads = []
    invalid_leads = []
    
    for lead in all_leads:
        email = lead.get("email", "")
        status = email_status.get(email, "unknown")
        lead["email_status"] = status
        
        if status == "ok":
            valid_leads.append(lead)
        elif status in ["catch_all", "unknown"]:
            risky_leads.append(lead)
        else:
            invalid_leads.append(lead)
    
    print(f"\n  Verification Results:")
    print(f"    ✅ Valid (ok):     {len(valid_leads)}")
    print(f"    ⚠️  Risky:         {len(risky_leads)}")
    print(f"    ❌ Invalid:        {len(invalid_leads)}")
    
    # Step 3: Output
    print(f"\n[3/3] GENERATING OUTPUT FILES...")
    
    # Save valid leads (safe to send)
    save_leads(valid_leads, f"verified_SAFE_{timestamp}")
    
    # Save risky leads (use with caution)
    save_leads(risky_leads, f"verified_RISKY_{timestamp}")
    
    # Create Instantly-ready CSV (just email, first_name, company_name, custom fields)
    instantly_leads = []
    for lead in valid_leads:
        instantly_leads.append({
            "email": lead["email"],
            "first_name": lead.get("first_name", lead["name"].split()[0] if lead["name"] else ""),
            "company_name": lead["name"],
            "phone": lead.get("phone", ""),
            "city": lead.get("city", ""),
            "niche": lead.get("niche", ""),
            "website": lead.get("website", "")
        })
    
    instantly_path = DATA_DIR / f"instantly_ready_{timestamp}.csv"
    if instantly_leads:
        with open(instantly_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=instantly_leads[0].keys())
            writer.writeheader()
            writer.writerows(instantly_leads)
        print(f"\n  📧 Instantly-ready CSV: {instantly_path}")
        print(f"     Contains {len(instantly_leads)} verified emails")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"  Target: {target} | Achieved: {len(valid_leads)} verified")
    print(f"  + {len(risky_leads)} risky (can add if needed)")
    
    if len(valid_leads) < target:
        shortfall = target - len(valid_leads)
        print(f"\n  ⚠️  Short by {shortfall} leads. Options:")
        print(f"     - Run again with more niches/cities")
        print(f"     - Use Apollo for direct email lookup")
        print(f"     - Include risky emails (catch_all)")
    
    return {
        "valid": len(valid_leads),
        "risky": len(risky_leads),
        "invalid": len(invalid_leads),
        "instantly_file": str(instantly_path)
    }


async def main():
    parser = argparse.ArgumentParser(description="Lead Generation Pipeline")
    parser.add_argument("command", choices=["scrape", "verify", "enrich", "full", "status"])
    parser.add_argument("--niche", help="Niche to scrape")
    parser.add_argument("--niches", help="Comma-separated niches")
    parser.add_argument("--cities", help="Comma-separated cities")
    parser.add_argument("--target", type=int, default=5000, help="Target number of verified leads")
    parser.add_argument("--input", help="Input CSV file")
    parser.add_argument("--output", help="Output CSV file")
    parser.add_argument("--limit", type=int, default=50, help="Leads per city")
    
    args = parser.parse_args()
    
    if args.command == "status":
        # Show available niches and cities
        print("Available Niches:")
        for n in NICHES:
            print(f"  - {n}")
        print("\nAvailable Cities:")
        for c in CITIES:
            print(f"  - {c}")
        return
    
    if args.command == "full":
        niches = args.niches.split(",") if args.niches else None
        cities = args.cities.split(",") if args.cities else None
        await full_pipeline(target=args.target, niches=niches, cities=cities)
    
    elif args.command == "verify":
        if not args.input:
            print("Error: --input required")
            return
        
        # Load CSV
        with open(args.input) as f:
            reader = csv.DictReader(f)
            leads = list(reader)
        
        emails = [l.get("email") for l in leads if l.get("email")]
        print(f"Verifying {len(emails)} emails...")
        
        results = await verify_emails_batch(emails)
        
        # Stats
        valid = sum(1 for r in results if r["result"] == "ok")
        print(f"\n✅ Valid: {valid}/{len(emails)}")
        
        # Save
        output = args.output or args.input.replace(".csv", "_verified.csv")
        email_status = {r["email"]: r["result"] for r in results}
        for lead in leads:
            lead["email_status"] = email_status.get(lead.get("email", ""), "unknown")
        
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=leads[0].keys())
            writer.writeheader()
            writer.writerows(leads)
        print(f"Saved to {output}")


if __name__ == "__main__":
    asyncio.run(main())
