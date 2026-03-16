#!/usr/bin/env python3
"""
Lead Conversion Engine
Analyzes call transcripts, scores leads, generates follow-up emails, creates daily action lists.

The gap: 74/75 leads are status 'new' — zero systematic follow-up.
This closes that gap.

Usage:
    lead_conversion analyze          # Score all recent leads
    lead_conversion hot              # Show hot leads needing follow-up
    lead_conversion email <lead_id>  # Generate personalized follow-up email
    lead_conversion daily            # Daily digest for Connor
    lead_conversion auto-email       # Generate emails for all hot leads (dry run)
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, "/opt/cmo-analytics")
from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")
from analytics.supabase_analytics import SupabaseAnalytics

# Initialize Supabase connection
db = SupabaseAnalytics(
    url=os.getenv("KAICALLS_SUPABASE_URL"),
    key=os.getenv("KAICALLS_SUPABASE_KEY"),
)

# Interest signals and their weights
INTEREST_SIGNALS = {
    'asked_pricing': {
        'patterns': ['price', 'cost', 'pricing', 'how much', 'rate', 'fee'],
        'weight': 3,
        'description': 'Asked about pricing'
    },
    'asked_about_service': {
        'patterns': ['do you offer', 'what service', 'tell me more', 'how does it work', 'what do you', 'can you'],
        'weight': 2,
        'description': 'Wanted to know more'
    },
    'owns_business': {
        'patterns': ['my business', 'our business', 'my company', 'our company', 'i own', 'we have'],
        'weight': 2,
        'description': 'Has a business'
    },
    'ready_to_start': {
        'patterns': ['sign up', 'get started', 'try it', "i'm interested", 'sounds good', "let's do it", 'all in'],
        'weight': 4,
        'description': 'Ready to sign up'
    },
    'specific_use_case': {
        'patterns': ['law firm', 'attorney', 'plumber', 'hvac', 'cleaning', 'contractor', 'service'],
        'weight': 2,
        'description': 'Has specific use case'
    },
    'long_conversation': {
        'min_words': 100,
        'weight': 1,
        'description': 'Engaged in real conversation'
    },
    'provided_contact': {
        'patterns': ['@', 'my email', 'my number', 'call me', 'reach me'],
        'weight': 3,
        'description': 'Shared contact info'
    },
    'positive_sentiment': {
        'patterns': ['great', 'awesome', 'perfect', 'exactly what', 'love it', 'sounds amazing'],
        'weight': 2,
        'description': 'Expressed enthusiasm'
    }
}

# Disqualification signals - must be very specific to avoid false positives
DISQUALIFIERS = {
    'wrong_language': ['need arabic', 'only speak spanish', 'chinese only', 'french only', 'egyptian dialect'],
    'tire_kicker': ['just curious', 'just testing', 'prank call', 'just playing'],
    'competitor': ['already using vapi', 'we use bland', 'currently have retell'],
    'explicit_no': ['not interested', 'no thank you', 'don\'t call me', 'take me off your list']
}

def score_lead(transcript: str, word_count: int) -> dict:
    """Score a lead based on transcript analysis."""
    if not transcript:
        return {'score': 0, 'signals': [], 'disqualified': False, 'tier': 'cold', 'reason': 'No transcript'}
    
    lower = transcript.lower()
    signals = []
    total_score = 0
    
    # Check interest signals
    for signal_name, signal_config in INTEREST_SIGNALS.items():
        if 'patterns' in signal_config:
            for pattern in signal_config['patterns']:
                if pattern in lower:
                    signals.append({
                        'signal': signal_name,
                        'description': signal_config['description'],
                        'weight': signal_config['weight']
                    })
                    total_score += signal_config['weight']
                    break
        elif 'min_words' in signal_config:
            if word_count >= signal_config['min_words']:
                signals.append({
                    'signal': signal_name,
                    'description': signal_config['description'],
                    'weight': signal_config['weight']
                })
                total_score += signal_config['weight']
    
    # Check disqualifiers
    disqualified = False
    disqualify_reason = None
    for reason, patterns in DISQUALIFIERS.items():
        for pattern in patterns:
            if pattern in lower:
                disqualified = True
                disqualify_reason = reason
                break
        if disqualified:
            break
    
    # Tier the lead
    if disqualified:
        tier = 'disqualified'
    elif total_score >= 8:
        tier = 'hot'
    elif total_score >= 4:
        tier = 'warm'
    elif total_score >= 2:
        tier = 'interested'
    else:
        tier = 'cold'
    
    return {
        'score': total_score,
        'signals': signals,
        'tier': tier,
        'disqualified': disqualified,
        'disqualify_reason': disqualify_reason
    }


def extract_caller_info(transcript: str) -> dict:
    """Extract any info the caller shared."""
    info = {}
    
    # Try to find email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', transcript)
    if email_match:
        info['email'] = email_match.group()
    
    # Try to find business type
    business_types = ['law firm', 'attorney', 'lawyer', 'plumber', 'hvac', 'cleaning', 
                      'contractor', 'dental', 'medical', 'real estate', 'insurance']
    for bt in business_types:
        if bt in transcript.lower():
            info['business_type'] = bt
            break
    
    # Try to find location
    location_patterns = [
        r'in ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # "in New York"
        r'from ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # "from Chicago"
    ]
    for pattern in location_patterns:
        match = re.search(pattern, transcript)
        if match:
            info['location'] = match.group(1)
            break
    
    return info


def generate_follow_up_email(lead: dict) -> str:
    """Generate personalized follow-up email based on the conversation."""
    name = lead.get('name', 'there')
    if name in ['Unknown', 'Customer Name Not Mentioned']:
        name = 'there'
    
    transcript = lead.get('transcript', '')
    caller_info = extract_caller_info(transcript)
    scoring = lead.get('scoring', {})
    
    # Build personalized opener
    business_type = caller_info.get('business_type', '')
    
    # Find what they were interested in
    asked_about = []
    if 'asked_pricing' in [s['signal'] for s in scoring.get('signals', [])]:
        asked_about.append('pricing')
    if 'asked_about_service' in [s['signal'] for s in scoring.get('signals', [])]:
        asked_about.append('how our AI phone answering works')
    
    # Generate email
    subject_options = [
        f"Following up on your call, {name}" if name != 'there' else "Following up on your call",
        "Quick follow-up from KaiCalls",
        f"Re: AI phone answering for your {business_type}" if business_type else "Re: AI phone answering"
    ]
    
    body = f"""Hey {name},

Thanks for calling and trying out Kai earlier. """

    if business_type:
        body += f"Sounds like you're running a {business_type} and could use some help handling calls.\n\n"
    elif asked_about:
        body += f"You asked about {' and '.join(asked_about)} — happy to fill in any gaps.\n\n"
    else:
        body += "I wanted to make sure you had everything you need.\n\n"
    
    body += """Here's the quick rundown:
- Kai answers your calls 24/7 with a real conversation (not a phone tree)
- Takes messages, collects lead info, sends you instant alerts
- $69.99/mo flat, no per-minute fees, cancel anytime

Want me to set up a quick 15-min call to get you live? Or if you're ready, you can just reply and I'll send you the signup link.

— Connor
KaiCalls.com"""

    return {
        'subject': subject_options[0],
        'body': body,
        'to': lead.get('email') or caller_info.get('email'),
        'phone': lead.get('phone')
    }


def get_leads_with_transcripts(days: int = 30, min_words: int = 0) -> list:
    """Get all leads with transcripts from Supabase.
    
    Transcripts are stored in the 'notes' field with 'Transcript:' prefix.
    Also check 'extracted_data' JSON field for call data.
    """
    from datetime import datetime, timedelta, timezone
    
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Get leads from Supabase - only phone call sources have transcripts
    client = db._get_client()
    result = client.table('leads').select('*').gte('created_at', cutoff).order('created_at', desc=True).execute()
    
    leads = []
    for row in result.data:
        # Parse transcript from notes field (format: "...Transcript: <text>")
        notes = row.get('notes') or ''
        transcript = ''
        if 'Transcript:' in notes:
            transcript = notes.split('Transcript:')[-1].strip()
        
        # Also check extracted_data for transcript
        if not transcript:
            extracted = row.get('extracted_data')
            if isinstance(extracted, dict):
                transcript = extracted.get('transcript', '') or ''
        
        word_count = len(transcript.split()) if transcript else 0
        
        if word_count >= min_words:
            leads.append({
                'id': str(row.get('id')),
                'name': row.get('name'),
                'email': row.get('email'),
                'phone': row.get('phone'),
                'source': row.get('source'),
                'status': row.get('status'),
                'created_at': row.get('created_at'),
                'notes': notes,  # Keep full notes for context
                'transcript': transcript,
                'word_count': word_count
            })
    
    return leads


def analyze_all_leads(days: int = 30) -> list:
    """Analyze and score all recent leads."""
    leads = get_leads_with_transcripts(days)
    
    for lead in leads:
        lead['scoring'] = score_lead(lead['transcript'], lead['word_count'])
    
    # Sort by score
    leads.sort(key=lambda x: x['scoring']['score'], reverse=True)
    return leads


def get_hot_leads(days: int = 14, kaicalls_only: bool = False) -> list:
    """Get leads that need follow-up (hot and warm tiers).
    
    Args:
        days: Number of days to look back
        kaicalls_only: If True, only return leads from KaiCalls sources
    """
    leads = analyze_all_leads(days)
    
    hot = [l for l in leads if l['scoring']['tier'] in ['hot', 'warm'] 
           and not l['scoring']['disqualified']
           and l['word_count'] > 50]  # Had a real conversation
    
    if kaicalls_only:
        kaicalls_sources = ['phone - Kai Calls Vapi', 'kaicalls', 'kai calls']
        hot = [l for l in hot if any(
            src.lower() in (l.get('source') or '').lower() 
            for src in kaicalls_sources
        )]
    
    return hot


def format_daily_digest(hot_leads: list) -> str:
    """Format hot leads as a daily action digest."""
    if not hot_leads:
        return "No hot leads today. Time to generate more inbound."
    
    output = f"# Lead Conversion Daily Digest\n"
    output += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
    output += f"**Hot Leads:** {len(hot_leads)}\n\n"
    output += "---\n\n"
    
    for i, lead in enumerate(hot_leads[:10], 1):
        scoring = lead['scoring']
        output += f"## {i}. {lead['name']}\n"
        output += f"**Score:** {scoring['score']} ({scoring['tier'].upper()})\n"
        output += f"**Phone:** {lead['phone'] or 'Not captured'}\n"
        output += f"**Email:** {lead['email'] if lead['email'] and '@placeholder' not in lead['email'] else 'Not captured'}\n"
        output += f"**Called:** {lead['created_at'][:10] if lead['created_at'] else 'Unknown'}\n"
        
        signals = [s['description'] for s in scoring['signals']]
        if signals:
            output += f"**Signals:** {', '.join(signals)}\n"
        
        # Transcript preview
        preview = lead['transcript'][:400] + '...' if len(lead['transcript']) > 400 else lead['transcript']
        output += f"\n> {preview}\n\n"
        
        # Action recommendation
        if lead['phone']:
            output += f"**→ ACTION:** Call back {lead['phone']}\n"
        elif lead['email'] and '@placeholder' not in lead['email']:
            output += f"**→ ACTION:** Email {lead['email']}\n"
        else:
            output += f"**→ ACTION:** Lead captured name '{lead['name']}' — check if number is in call logs\n"
        
        output += "\n---\n\n"
    
    # Summary stats
    total_score = sum(l['scoring']['score'] for l in hot_leads)
    with_phone = len([l for l in hot_leads if l['phone']])
    
    output += "## Summary\n"
    output += f"- **Total hot leads:** {len(hot_leads)}\n"
    output += f"- **With phone numbers:** {with_phone}\n"
    output += f"- **Average score:** {total_score / len(hot_leads):.1f}\n"
    output += f"\n**Conversion opportunity:** If just 1 of these converts at $69.99/mo, that's your first paying customer.\n"
    
    return output


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == 'analyze':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        leads = analyze_all_leads(days)
        
        print(f"\n=== Lead Analysis ({len(leads)} leads, last {days} days) ===\n")
        
        # Group by tier
        tiers = {'hot': [], 'warm': [], 'interested': [], 'cold': [], 'disqualified': []}
        for lead in leads:
            tier = lead['scoring']['tier']
            tiers[tier].append(lead)
        
        for tier_name, tier_leads in tiers.items():
            if tier_leads:
                print(f"\n{tier_name.upper()} ({len(tier_leads)}):")
                for lead in tier_leads[:5]:
                    signals = ', '.join([s['description'] for s in lead['scoring']['signals']])
                    print(f"  • {lead['name']} (score: {lead['scoring']['score']}) - {signals or 'No signals'}")
    
    elif command == 'hot':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 14
        hot_leads = get_hot_leads(days)
        
        print(json.dumps(hot_leads, indent=2, default=str))
    
    elif command == 'email':
        if len(sys.argv) < 3:
            print("Usage: lead_conversion email <lead_id>")
            return
        
        lead_id = sys.argv[2]
        leads = analyze_all_leads(30)
        lead = next((l for l in leads if l['id'] == lead_id), None)
        
        if not lead:
            print(f"Lead {lead_id} not found")
            return
        
        email = generate_follow_up_email(lead)
        print(f"\n=== Follow-up Email for {lead['name']} ===\n")
        print(f"To: {email['to'] or '(no email - use phone: ' + str(lead['phone']) + ')'}")
        print(f"Subject: {email['subject']}\n")
        print(email['body'])
    
    elif command == 'daily':
        # Check for --kaicalls flag
        kaicalls_only = '--kaicalls' in sys.argv
        days = 14
        for arg in sys.argv[2:]:
            if arg.isdigit():
                days = int(arg)
        
        hot_leads = get_hot_leads(days, kaicalls_only=kaicalls_only)
        digest = format_daily_digest(hot_leads)
        print(digest)
        
        # Also save to file
        suffix = '_kaicalls' if kaicalls_only else ''
        output_path = f'/opt/cmo-analytics/reports/lead_digest{suffix}_latest.md'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(digest)
        print(f"\n[Saved to {output_path}]")
    
    elif command == 'auto-email':
        # Generate follow-up emails for all hot leads (dry run)
        hot_leads = get_hot_leads(14)
        
        print(f"\n=== Auto-Generated Follow-up Emails ({len(hot_leads)} hot leads) ===\n")
        
        for lead in hot_leads:
            lead['scoring'] = score_lead(lead['transcript'], lead['word_count'])
            email = generate_follow_up_email(lead)
            
            print(f"--- {lead['name']} (score: {lead['scoring']['score']}) ---")
            print(f"To: {email['to'] or lead['phone']}")
            print(f"Subject: {email['subject']}")
            print(f"\n{email['body'][:300]}...\n")
    
    elif command == 'json':
        # Output hot leads as JSON for dashboard
        kaicalls_only = '--kaicalls' in sys.argv
        hot_leads = get_hot_leads(14, kaicalls_only=kaicalls_only)
        output = {
            'generated_at': datetime.now().isoformat(),
            'count': len(hot_leads),
            'kaicalls_only': kaicalls_only,
            'leads': []
        }
        
        for lead in hot_leads:
            email = generate_follow_up_email(lead)
            output['leads'].append({
                'id': lead['id'],
                'name': lead['name'],
                'phone': lead['phone'],
                'email': lead['email'],
                'score': lead['scoring']['score'],
                'tier': lead['scoring']['tier'],
                'signals': [s['description'] for s in lead['scoring']['signals']],
                'created_at': lead['created_at'],
                'transcript_preview': lead['transcript'][:500] if lead['transcript'] else '',
                'follow_up_email': email
            })
        
        print(json.dumps(output, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == '__main__':
    main()
