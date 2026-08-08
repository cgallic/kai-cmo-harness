# TAM Domination Automation Template

## Overview

This template enables rapid deployment of the TAM Domination cold email system for any B2B client. Based on Sales Automation Systems' methodology that generated 42% of RB2B's $4M ARR.

**Core Principle:** Send 1 email every 60 days to 100% of TAM. No sequences.

---

## Client Intake Questionnaire

### Required Information

```yaml
# CLIENT INTAKE FORM
# Complete all fields before starting automation

company:
  name: ""                    # e.g., "Kai Calls"
  website: ""                 # e.g., "kaicalls.com"
  product_type: ""            # SaaS, Service, Agency, etc.
  price_point: ""             # e.g., "$300/mo"
  trial_available: true/false
  trial_url: ""               # e.g., "https://kaicalls.com/trial"

value_proposition:
  one_liner: ""               # 10 words max
  problem_solved: ""          # What pain do you fix?
  proof_point: ""             # Best customer result
  differentiation: ""         # Why you vs. competitors

target_market:
  industries: []              # e.g., ["Law Firms", "Medical", "Insurance"]
  company_size: ""            # e.g., "2-50 employees"
  titles: []                  # e.g., ["Owner", "Partner", "Office Manager"]
  geography: ""               # e.g., "US only"
  estimated_tam: 0            # Total addressable contacts

competitors:
  direct: []                  # Direct competitors
  alternatives: []            # What they do instead (e.g., "answering service")
  price_comparison: ""        # How your price compares

existing_assets:
  case_studies: []            # Customer success stories
  testimonials: []            # Quotes from customers
  data_points: []             # Statistics you can cite
```

### Example (Kai Calls)

```yaml
company:
  name: "Kai Calls"
  website: "kaicalls.com"
  product_type: "SaaS"
  price_point: "$300/mo"
  trial_available: true
  trial_url: "https://kaicalls.com/trial"

value_proposition:
  one_liner: "AI receptionist that never misses a call"
  problem_solved: "Missed calls = lost revenue"
  proof_point: "One PI firm signed 40% more cases"
  differentiation: "AI qualifies leads in real-time, $300 vs $4K/mo answering service"

target_market:
  industries: ["Law Firms", "Medical Practices", "Insurance Agencies", "Home Services"]
  company_size: "2-50 employees"
  titles: ["Owner", "Managing Partner", "Office Manager", "Marketing Director"]
  geography: "US only"
  estimated_tam: 900000

competitors:
  direct: ["Ruby", "Smith.ai", "Nexa"]
  alternatives: ["Answering services", "Voicemail", "Missing calls"]
  price_comparison: "$300/mo vs $2-4K/mo for human answering"

existing_assets:
  case_studies: ["PI firm 40% more cases", "750+ calls handled"]
  testimonials: []
  data_points: ["67% of callers never call back", "Average firm misses 23% of calls"]
```

---

## Automation Scripts

### Script 1: Infrastructure Calculator

```python
#!/usr/bin/env python3
"""
TAM Domination Infrastructure Calculator

Calculates required domains, inboxes, and costs based on TAM size.
"""

def calculate_infrastructure(tam_size: int, cycle_days: int = 60) -> dict:
    """
    Calculate infrastructure requirements for TAM Domination.

    Args:
        tam_size: Total addressable market size
        cycle_days: Days between contacting same lead (default 60)

    Returns:
        Dictionary with infrastructure requirements
    """
    # Constants
    EMAILS_PER_INBOX_PER_DAY = 50
    INBOXES_PER_DOMAIN = 3
    DOMAIN_COST_DINODOT = 0.50  # At scale
    DOMAIN_COST_NAMECHEAP = 10.00
    WORKSPACE_COST_PER_INBOX = 6.00  # Monthly
    COLDSEND_COST = 250  # Monthly for 1K inboxes
    CLAY_EXPLORER_COST = 314
    CLAY_PRO_COST = 720

    # Calculations
    emails_per_day = tam_size / cycle_days
    inboxes_needed = int(emails_per_day / EMAILS_PER_INBOX_PER_DAY) + 1
    domains_needed = int(inboxes_needed / INBOXES_PER_DOMAIN) + 1

    # Determine best infrastructure option
    if inboxes_needed <= 1000:
        infra_option = "ColdSend"
        infra_monthly = COLDSEND_COST
    else:
        infra_option = "DIY (Smartlead + Workspace)"
        infra_monthly = (domains_needed * DOMAIN_COST_NAMECHEAP / 12) + \
                        (inboxes_needed * WORKSPACE_COST_PER_INBOX) + 94  # Smartlead

    # Clay tier
    credits_needed = tam_size * 10  # ~10 credits per lead
    if credits_needed <= 10000:
        clay_tier = "Explorer"
        clay_cost = CLAY_EXPLORER_COST
    elif credits_needed <= 50000:
        clay_tier = "Pro 50K"
        clay_cost = CLAY_PRO_COST
    else:
        clay_tier = "Pro 100K+"
        clay_cost = 1350

    total_monthly = infra_monthly + clay_cost

    return {
        "tam_size": tam_size,
        "cycle_days": cycle_days,
        "emails_per_day": int(emails_per_day),
        "inboxes_needed": inboxes_needed,
        "domains_needed": domains_needed,
        "infrastructure": {
            "option": infra_option,
            "monthly_cost": infra_monthly
        },
        "enrichment": {
            "clay_tier": clay_tier,
            "monthly_cost": clay_cost,
            "credits_needed": credits_needed
        },
        "total_monthly_cost": total_monthly,
        "cost_per_contact": round(total_monthly / (tam_size / cycle_days * 30), 4)
    }


def print_infrastructure_report(config: dict):
    """Print formatted infrastructure report."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           TAM DOMINATION INFRASTRUCTURE REPORT               ║
╠══════════════════════════════════════════════════════════════╣
║ TAM Size:           {config['tam_size']:>15,} contacts          ║
║ Cycle Length:       {config['cycle_days']:>15} days              ║
║ Daily Send Volume:  {config['emails_per_day']:>15,} emails           ║
╠══════════════════════════════════════════════════════════════╣
║ INFRASTRUCTURE REQUIREMENTS                                  ║
╠══════════════════════════════════════════════════════════════╣
║ Domains Needed:     {config['domains_needed']:>15}                   ║
║ Inboxes Needed:     {config['inboxes_needed']:>15}                   ║
║ Platform:           {config['infrastructure']['option']:>15}        ║
║ Platform Cost:      ${config['infrastructure']['monthly_cost']:>14.2f}/mo       ║
╠══════════════════════════════════════════════════════════════╣
║ ENRICHMENT                                                   ║
╠══════════════════════════════════════════════════════════════╣
║ Clay Tier:          {config['enrichment']['clay_tier']:>15}             ║
║ Credits Needed:     {config['enrichment']['credits_needed']:>15,}                ║
║ Clay Cost:          ${config['enrichment']['monthly_cost']:>14.2f}/mo       ║
╠══════════════════════════════════════════════════════════════╣
║ TOTAL MONTHLY:      ${config['total_monthly_cost']:>14.2f}              ║
║ Cost per Contact:   ${config['cost_per_contact']:>14.4f}              ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    import sys

    tam = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    config = calculate_infrastructure(tam)
    print_infrastructure_report(config)
```

### Script 2: Domain Generator

```python
#!/usr/bin/env python3
"""
Domain Name Generator for TAM Domination

Generates domain name variants for cold email infrastructure.
"""

import itertools
from typing import List

def generate_domains(brand_name: str, count: int = 100) -> List[str]:
    """
    Generate domain name variants for a brand.

    Args:
        brand_name: Core brand name (e.g., "kaicalls")
        count: Number of domains to generate

    Returns:
        List of domain suggestions
    """
    prefixes = [
        "try", "get", "use", "meet", "hello", "start",
        "go", "my", "the", "with", "join", "discover"
    ]

    suffixes = [
        "app", "hq", "now", "ai", "io", "pro",
        "team", "hub", "labs", "co", "inc", "tools"
    ]

    tlds = [".com", ".io", ".co", ".ai", ".app"]

    domains = []

    # Pattern 1: prefix + brand + tld
    for prefix, tld in itertools.product(prefixes, tlds):
        domains.append(f"{prefix}{brand_name}{tld}")

    # Pattern 2: brand + suffix + tld
    for suffix, tld in itertools.product(suffixes, tlds):
        domains.append(f"{brand_name}{suffix}{tld}")

    # Pattern 3: prefix + brand + suffix + tld (limited)
    for prefix, suffix in itertools.product(prefixes[:4], suffixes[:4]):
        domains.append(f"{prefix}{brand_name}{suffix}.com")

    # Pattern 4: brand variations
    brand_variations = [
        brand_name,
        brand_name.replace("_", ""),
        f"{brand_name}s",
    ]
    for var, tld in itertools.product(brand_variations, tlds):
        if var != brand_name:  # Avoid duplicates
            domains.append(f"{var}{tld}")

    # Remove duplicates and limit
    domains = list(dict.fromkeys(domains))[:count]

    return domains


def check_availability(domains: List[str]) -> dict:
    """
    Check domain availability (stub - implement with registrar API).
    """
    # TODO: Integrate with Namecheap/DinoDot API
    return {domain: "unknown" for domain in domains}


if __name__ == "__main__":
    import sys

    brand = sys.argv[1] if len(sys.argv) > 1 else "kaicalls"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    domains = generate_domains(brand, count)

    print(f"\n{'='*50}")
    print(f"DOMAIN SUGGESTIONS FOR: {brand.upper()}")
    print(f"{'='*50}\n")

    for i, domain in enumerate(domains, 1):
        print(f"{i:3}. {domain}")

    print(f"\nTotal: {len(domains)} domains")
```

### Script 3: Email Variant Generator

```python
#!/usr/bin/env python3
"""
Email Variant Generator for TAM Domination

Generates email copy variants based on client intake.
"""

from dataclasses import dataclass
from typing import List, Dict
import json

@dataclass
class ClientIntake:
    company_name: str
    one_liner: str
    problem_solved: str
    proof_point: str
    price_point: str
    differentiation: str
    industries: List[str]

def generate_subject_lines(intake: ClientIntake) -> List[str]:
    """Generate subject line variants."""
    return [
        "calls",
        "quick q",
        f"{{{{firstName}}}}?",
        intake.problem_solved.split()[0].lower(),  # First word of problem
        "heard this helps",
        f"{{{{companyName}}}} {intake.problem_solved.split()[0].lower()}",
        "67%",  # Data point hook
        "idea",
        "your phones",
        f"{intake.one_liner.split()[0].lower()}"
    ]

def generate_body_variants(intake: ClientIntake) -> List[Dict]:
    """Generate body copy variants."""

    variants = []

    # Variant 1: Problem-focused
    variants.append({
        "name": "problem_focused",
        "subject": "calls",
        "body": f"""Hey {{{{firstName}}}},

What happens when someone calls {{{{companyName}}}} after 5pm?

{intake.problem_solved}

{intake.proof_point}

Reply "yes" to try it free.

{{{{senderName}}}}"""
    })

    # Variant 2: Result-focused
    variants.append({
        "name": "result_focused",
        "subject": "quick q",
        "body": f"""Hey {{{{firstName}}}},

If {intake.one_liner.lower()}, how would that change things at {{{{companyName}}}}?

{intake.proof_point}

Reply "yes" if you want to see it work.

{{{{senderName}}}}"""
    })

    # Variant 3: Cost-focused
    variants.append({
        "name": "cost_focused",
        "subject": "idea",
        "body": f"""Hey {{{{firstName}}}},

{intake.differentiation}

Most similar companies spend way more for worse results.

Reply "yes" if you want details.

{{{{senderName}}}}"""
    })

    # Variant 4: Social proof
    variants.append({
        "name": "social_proof",
        "subject": "heard this helps",
        "body": f"""Hey {{{{firstName}}}},

{intake.proof_point}

We built {intake.company_name} to {intake.one_liner.lower()}.

Reply "yes" for a free trial.

{{{{senderName}}}}"""
    })

    # Variant 5: FOMO
    variants.append({
        "name": "fomo",
        "subject": f"{{{{companyName}}}}",
        "body": f"""Hey {{{{firstName}}}},

Your competitors are already doing this.

{intake.one_liner}. {intake.price_point}.

Reply "yes" before they all catch on.

{{{{senderName}}}}"""
    })

    # Variant 6: Direct/Simple
    variants.append({
        "name": "direct",
        "subject": "{{firstName}}?",
        "body": f"""Hey {{{{firstName}}}},

{intake.one_liner}. {intake.price_point}. 5 minute setup.

Reply "yes" to try it.

{{{{senderName}}}}"""
    })

    return variants

def generate_industry_variants(intake: ClientIntake, base_variant: Dict) -> List[Dict]:
    """Generate industry-specific variants from a base template."""

    industry_hooks = {
        "Law Firms": "When a potential client calls at 6pm on Friday",
        "Medical Practices": "When a patient needs to schedule after hours",
        "Insurance Agencies": "When a lead calls during your busiest time",
        "Home Services": "When a homeowner with an emergency calls at midnight",
        "Real Estate": "When a hot buyer calls while you're showing another property"
    }

    variants = []
    for industry in intake.industries:
        hook = industry_hooks.get(industry, "When someone important calls")
        variant = base_variant.copy()
        variant["name"] = f"{base_variant['name']}_{industry.lower().replace(' ', '_')}"
        variant["industry"] = industry
        variant["body"] = variant["body"].replace(
            intake.problem_solved,
            f"{hook}, what happens?"
        )
        variants.append(variant)

    return variants

def export_to_smartlead_format(variants: List[Dict]) -> str:
    """Export variants in Smartlead-compatible format."""
    output = []
    for v in variants:
        output.append({
            "name": v["name"],
            "subject": v["subject"],
            "body": v["body"],
            "delay_days": 0,
            "step": 1
        })
    return json.dumps(output, indent=2)

if __name__ == "__main__":
    # Example usage
    intake = ClientIntake(
        company_name="Kai Calls",
        one_liner="AI receptionist that never misses a call",
        problem_solved="67% of callers who hit voicemail never call back",
        proof_point="One PI firm signed 40% more cases after switching",
        price_point="$300/mo",
        differentiation="$300/mo vs $4K/mo for human answering services",
        industries=["Law Firms", "Medical Practices", "Insurance Agencies"]
    )

    subjects = generate_subject_lines(intake)
    bodies = generate_body_variants(intake)

    print("SUBJECT LINE VARIANTS:")
    print("="*50)
    for i, s in enumerate(subjects, 1):
        print(f"{i}. {s}")

    print("\nBODY COPY VARIANTS:")
    print("="*50)
    for v in bodies:
        print(f"\n--- {v['name'].upper()} ---")
        print(f"Subject: {v['subject']}")
        print(f"Body:\n{v['body']}")
```

---

## Clay Table Templates

### Template 1: TAM Builder Table

**Import this CSV structure to Clay:**

```csv
company_domain,company_name,industry,employee_count,person_name,person_title,person_email,email_verified,inbox_type,icp_score,campaign_status
example.com,Example Corp,Legal,25,John Smith,Managing Partner,john@example.com,true,gmail,85,ready
```

**Clay Columns to Add:**

| Column Name | Type | Source | Condition |
|-------------|------|--------|-----------|
| `company_domain` | Import | CSV | - |
| `company_name` | Enrichment | Clearbit | Always |
| `industry` | Enrichment | Clearbit | Always |
| `employee_count` | Enrichment | Clearbit | Always |
| `person_name` | Enrichment | Apollo Waterfall | Always |
| `person_title` | Enrichment | Apollo | After person_name |
| `person_email` | Enrichment | Email Waterfall | After person_name |
| `email_verified` | Enrichment | ZeroBounce | After person_email |
| `inbox_type` | AI (Claygent) | "Is this a Gmail address?" | After person_email |
| `icp_score` | Formula | See below | After all enrichment |
| `campaign_status` | Formula | See below | After icp_score |

**ICP Score Formula (Clay):**
```
=IF(
  AND(
    industry IN ["Legal", "Medical", "Insurance", "Home Services"],
    employee_count >= 2,
    employee_count <= 50,
    title CONTAINS ["Owner", "Partner", "Director", "Manager"],
    email_verified = true
  ),
  IF(inbox_type = "Gmail", 90, 70),
  IF(email_verified = true, 50, 0)
)
```

**Campaign Status Formula:**
```
=IF(icp_score >= 70, "ready", IF(icp_score >= 50, "review", "skip"))
```

### Template 2: Master Suppression Table

```csv
email,domain,first_contact_date,last_contact_date,campaign_id,status,reply_type
john@example.com,example.com,2026-01-15,2026-01-15,lawfirms_q1,contacted,none
jane@acme.com,acme.com,2025-11-15,2025-11-15,medical_q4,replied,interested
```

**Workflow Integration:**
```
1. Before enriching new batch:
   - Lookup email in Master Table
   - If exists AND last_contact_date > (today - 60): SKIP
   - If exists AND status = "unsubscribed": SKIP PERMANENTLY

2. After sending:
   - Add to Master Table with status = "contacted"

3. After reply:
   - Update Master Table with reply_type
```

---

## Smartlead Campaign Setup

### Campaign Configuration

```json
{
  "name": "{{client_name}} - {{industry}} - Q{{quarter}} {{year}}",
  "settings": {
    "stop_on_reply": true,
    "stop_on_auto_reply": true,
    "track_opens": true,
    "track_clicks": false,
    "send_as_plain_text": true,
    "schedule": {
      "days": ["monday", "tuesday", "wednesday", "thursday"],
      "start_time": "09:00",
      "end_time": "11:00",
      "timezone": "recipient"
    }
  },
  "sender_rotation": {
    "accounts_per_campaign": 50,
    "daily_limit_per_account": 30,
    "ramp_up_enabled": true,
    "ramp_up_increment": 5
  }
}
```

### Sequence Setup (Single Email)

```json
{
  "steps": [
    {
      "step": 1,
      "delay_days": 0,
      "subject": "{{subject_variant}}",
      "body": "{{body_variant}}",
      "variants": [
        {"a": "calls", "b": "quick q", "c": "{{firstName}}?"}
      ]
    }
  ]
}
```

**Note:** No follow-up steps. TAM Domination uses single-email cycles.

---

## Testing Protocol Template

### Week 1-2: Subject Line Testing

```yaml
test_name: "Subject Line Testing"
segment: "{{primary_industry}}"
volume: 10000
variants: 10
emails_per_variant: 1000

variants:
  - id: s1
    subject: "calls"
  - id: s2
    subject: "quick q"
  - id: s3
    subject: "{{firstName}}?"
  # ... add 7 more

success_criteria:
  open_rate: ">= 40%"

output:
  top_3_subjects: []
  bottom_3_subjects: []
```

### Week 3-4: Body Copy Testing

```yaml
test_name: "Body Copy Testing"
segment: "{{primary_industry}}"
volume: 15000
variants: 15  # 3 subjects × 5 bodies

test_matrix:
  subjects: ["{{top_subject_1}}", "{{top_subject_2}}", "{{top_subject_3}}"]
  bodies: ["problem_focused", "result_focused", "cost_focused", "social_proof", "fomo"]

success_criteria:
  reply_rate: ">= 1%"
  signup_rate: ">= 0.5%"

output:
  winning_combination: {}
```

### Week 5-8: Segment Testing

```yaml
test_name: "Segment Testing"
winning_copy: "{{winning_combination}}"
volume_per_segment: 5000

segments:
  - name: "Law Firms"
    criteria: {industry: "Legal"}
  - name: "Medical"
    criteria: {industry: "Medical"}
  - name: "Insurance"
    criteria: {industry: "Insurance"}
  # ... add more segments

success_criteria:
  emails_per_positive: "<= 1500"

output:
  segment_performance: []
  evergreen_pillars: []
```

---

## Monitoring Dashboard

### Key Metrics to Track

```sql
-- Daily metrics query (adapt to your analytics system)
SELECT
  date,
  campaign_id,
  SUM(emails_sent) as sent,
  SUM(opens) as opens,
  ROUND(SUM(opens) * 100.0 / SUM(emails_sent), 2) as open_rate,
  SUM(replies) as replies,
  ROUND(SUM(replies) * 100.0 / SUM(emails_sent), 2) as reply_rate,
  SUM(positive_replies) as positive,
  SUM(signups) as signups,
  ROUND(SUM(emails_sent) * 1.0 / NULLIF(SUM(signups), 0), 0) as emails_per_signup
FROM campaign_metrics
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY date, campaign_id
ORDER BY date DESC;
```

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Open Rate | < 35% | < 25% | Check deliverability |
| Bounce Rate | > 3% | > 5% | Pause, check data quality |
| Spam Complaints | > 0.05% | > 0.1% | Stop immediately |
| Domain Reputation | Score < 80 | Score < 60 | Rotate domain |

---

## Client Onboarding Checklist

### Pre-Launch (Days 1-7)

- [ ] Complete client intake questionnaire
- [ ] Calculate infrastructure requirements
- [ ] Purchase domains
- [ ] Setup ColdSend/Smartlead account
- [ ] Setup Clay account
- [ ] Configure DNS (SPF/DKIM/DMARC)
- [ ] Build TAM list (minimum 50K contacts)
- [ ] Enrich TAM in Clay
- [ ] Generate email variants
- [ ] Setup Master Suppression Table
- [ ] Create Smartlead campaigns

### Testing Phase (Days 8-28)

- [ ] Launch subject line tests
- [ ] Analyze subject line results
- [ ] Launch body copy tests
- [ ] Analyze body copy results
- [ ] Identify winning combination
- [ ] Test across segments
- [ ] Build evergreen pillars

### Scale Phase (Day 29+)

- [ ] Deploy to full TAM
- [ ] Set 60-day cycle schedule
- [ ] Configure monitoring alerts
- [ ] Setup response handling
- [ ] Weekly performance reviews
- [ ] Monthly optimization cycles

---

## File Outputs

When running this automation for a new client, generate these files:

```
clients/{client_name}/
├── knowledge/
│   └── tam-domination-system.md      # Client-specific system doc
├── scripts/
│   └── analytics/
│       └── cold_email_metrics.py     # Tracking queries
├── leads/
│   ├── tam_master.csv                # Full TAM list
│   └── suppression_list.csv          # Do-not-contact
└── outputs/
    └── email-copy/
        ├── subject_variants.md       # All subject lines
        ├── body_variants.md          # All body copy
        └── test_results.md           # Testing documentation
```
