# Task 012: Build per-archetype fixtures and golden examples

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 2. Archetypes and Module System
**Priority:** P3
**Depends on:** 006, 007, 008, 009
**Estimated complexity:** Medium

## Context

Every system needs realistic test data. These fixture files are complete BusinessProfile examples in YAML format that represent real-world businesses with enough detail to run through the full audit, proposal, and action pipeline. They serve as: (1) golden test cases for the activation and audit engines, (2) examples for operators onboarding new businesses, and (3) development fixtures during overnight builds. Each fixture should feel like a real business that someone actually runs.

## Scope

Create `kai/archetypes/fixtures/` directory with 4 YAML fixture files, one per archetype, each containing a complete BusinessProfile that can be loaded by the profile loader (Task 002).

## Detailed Requirements

### File: `kai/archetypes/fixtures/local_service_example.yaml`

A realistic **residential plumbing company** in the Houston, TX metro area.

```yaml
# Top-level key matching the profile loader's expected format
business_profile:
  id: "clearflow-plumbing-houston"
  profile_version: "1.0.0"

  identity:
    business_name: "ClearFlow Plumbing"
    dba: null
    legal_entity: "ClearFlow Plumbing LLC"
    website_url: "https://clearflowplumbing.com"
    phone: "(713) 555-0142"
    email: "service@clearflowplumbing.com"
    logo_url: null
    tagline: "Fast, Fair, Fixed Right"
    elevator_pitch: "ClearFlow Plumbing provides emergency and scheduled plumbing services to homeowners across the Greater Houston area. Licensed, insured, and backed by 15 years of 5-star service."

  classification:
    industry: "home_services"
    vertical: "residential_plumbing"
    business_model: "service"
    archetype: "local-service"
    stage: "growth"

  # Include at least 4 offers with varying detail levels
  offers:
    - name: "Emergency Plumbing Repair"
      description: "24/7 emergency response for burst pipes, major leaks, sewer backups, and water heater failures"
      price_range: "$150-500"
      margin_tier: "high"
      is_seasonal: false
      is_primary: true
      primary_cta: "Call Now"
      category: "emergency"
    - name: "Drain Cleaning"
      description: "Professional drain cleaning for kitchen, bathroom, and main sewer lines"
      price_range: "$99-250"
      margin_tier: "medium"
      is_seasonal: false
      is_primary: false
      primary_cta: "Book Online"
      category: "maintenance"
    - name: "Water Heater Installation"
      description: "Tank and tankless water heater installation and replacement"
      price_range: "$1,200-3,500"
      margin_tier: "high"
      is_seasonal: true
      is_primary: false
      primary_cta: "Get Free Estimate"
      category: "installation"
    - name: "Repiping"
      description: "Whole-home repiping for homes with galvanized or polybutylene pipes"
      price_range: "$4,000-12,000"
      margin_tier: "premium"
      is_seasonal: false
      is_primary: false
      primary_cta: "Schedule Inspection"
      category: "major_project"

  geography:
    service_areas:
      - "Houston, TX"
      - "Katy, TX"
      - "Sugar Land, TX"
      - "The Woodlands, TX"
      - "Pearland, TX"
    locations:
      - name: "Main Office"
        address: "4521 Westheimer Rd"
        city: "Houston"
        state: "TX"
        zip_code: "77027"
        country: "US"
        phone: "(713) 555-0142"
        hours:
          monday: "7am-6pm"
          tuesday: "7am-6pm"
          wednesday: "7am-6pm"
          thursday: "7am-6pm"
          friday: "7am-6pm"
          saturday: "8am-2pm"
          sunday: "Emergency Only"
        gbp_url: "https://goo.gl/maps/example"
        is_primary: true
    geo_scope: "local"
    is_mobile: true
    has_storefront: false

  # Include at least 2 personas
  personas:
    - name: "Emergency Eddie"
      demographics: "Homeowner, 35-60, household income $75K+, owns home built before 2000"
      pain_points:
        - "Pipe just burst and water is everywhere"
        - "Can't find a plumber who answers on weekends"
        - "Worried about being overcharged in an emergency"
        - "Previous plumber did a bad job and now it's worse"
      buying_triggers:
        - "Active water emergency"
        - "Water heater stopped working"
        - "Sewer backup into house"
      objections:
        - "How fast can you get here?"
        - "How much will this cost?"
        - "Are you licensed and insured?"
      channels_used: ["google", "nextdoor", "facebook"]
      decision_timeline: "same-day"
      is_primary: true
    - name: "Planning Pam"
      demographics: "Homeowner, 40-65, household income $100K+, proactive about home maintenance"
      pain_points:
        - "Water pressure has been dropping gradually"
        - "Old galvanized pipes need replacing before they fail"
        - "Want a water heater upgrade but unsure about tankless"
      buying_triggers:
        - "Noticed early signs of plumbing problems"
        - "Neighbor had a major plumbing disaster"
        - "Seasonal maintenance reminder"
      objections:
        - "Can I get multiple estimates?"
        - "How long will the work take?"
        - "What's the warranty?"
      channels_used: ["google", "yelp", "email"]
      decision_timeline: "1-2 weeks"
      is_primary: false

  trust:
    testimonials:
      - signal_type: "testimonial"
        title: null
        content: "ClearFlow saved us when our water heater burst at 11pm. Mike was here in 40 minutes and had it fixed by 1am. Fair price, professional work."
        source: "Google Review - Sarah M."
        url: null
        date: "2025-11"
      - signal_type: "testimonial"
        content: "Best plumber in Houston. They repiped our entire 1970s home in 3 days. Clean, professional, and the price was exactly what they quoted."
        source: "Google Review - James K."
        date: "2025-09"
    case_studies: []
    certifications:
      - "Texas Master Plumber License #MP-44821"
      - "Rinnai Certified Installer"
      - "State Licensed and Insured"
    awards:
      - "Best of Houston Plumbing 2024 - Houston Chronicle"
    years_in_business: 15
    team_size: "6-20"
    notable_clients: []
    insurance_details: "General liability $1M, workers comp active"
    licenses:
      - "TX Master Plumber MP-44821"
      - "City of Houston Plumbing Contractor"

  goals:
    primary_goals:
      - "Increase monthly leads from 40 to 60"
      - "Grow Google reviews from 87 to 150 by Q4 2026"
      - "Launch service in Conroe/Spring TX market"
    target_kpis:
      leads_per_month: 60
      cost_per_lead: 75
      review_count: 150
      review_rating: 4.8
      website_conversion_rate: 5.0
    timeframe: "Q2-Q4 2026"
    north_star_metric: "leads_per_month"

  channels:
    - platform: "website"
      url: "https://clearflowplumbing.com"
      is_connected: false
      is_active: true
      last_activity: "2026-03-28"
      follower_count: null
      notes: "WordPress site, needs speed optimization"
    - platform: "gbp"
      url: "https://goo.gl/maps/example"
      is_connected: false
      is_active: true
      last_activity: "2026-03-15"
      follower_count: null
      notes: "87 reviews, 4.7 rating, posts inconsistent"
    - platform: "facebook"
      url: "https://facebook.com/clearflowplumbing"
      is_connected: false
      is_active: false
      last_activity: "2025-11-01"
      follower_count: 340
      notes: "Dormant - last post 5 months ago"
    - platform: "google_ads"
      is_connected: false
      is_active: false
      notes: "Ran briefly in 2024, stopped due to budget concerns"
    - platform: "yelp"
      url: "https://yelp.com/biz/clearflow-plumbing-houston"
      is_connected: false
      is_active: true
      follower_count: null
      notes: "23 reviews, 4.5 rating"

  constraints:
    compliance_notes:
      - "Texas requires master plumber license number in all advertising"
    regulated_industry: false
    claims_restrictions:
      - "Cannot claim 'guaranteed same-day service' — weather events can delay"
    brand_voice_notes: "Friendly, direct, no corporate jargon. Talk like a trusted neighbor who happens to be an expert plumber."
    topics_to_avoid:
      - "DIY plumbing advice that could cause liability"
      - "Criticizing other plumbing companies by name"

  budget:
    monthly_marketing_budget: 2500.00
    risk_tolerance: "moderate"
    auto_execution_enabled: false
    max_auto_spend_per_action: 100.00

  sales_cycle:
    buyer_type: "b2c"
    sales_cycle_length: "same-day to 2 weeks"
    average_deal_size: 450.00
    decision_makers:
      - "Homeowner"
      - "Spouse/partner"
    sales_process: "Phone call or online form -> estimate (free for standard, $49 diagnostic fee for complex) -> service -> follow-up"

  brand_voice:
    tone_descriptors:
      - "friendly"
      - "direct"
      - "trustworthy"
      - "expert but not condescending"
    writing_samples: []
    approved_messaging_blocks:
      - "Fast, Fair, Fixed Right — That's the ClearFlow Promise"
      - "Licensed Master Plumber • 15 Years Serving Houston"
    competitor_differentiation: "We answer the phone 24/7 with a real human (or AI receptionist), provide upfront pricing before work begins, and back everything with a 1-year labor warranty."
    personality_traits:
      - "reliable"
      - "knowledgeable"
      - "honest"

  operator:
    operator_hours_per_week: 5.0
    operator_skill_level: "beginner"
    preferred_channels:
      - "gbp"
      - "google_ads"
    delegation_preferences: "Handle everything automated — I just want to approve ad spend and review monthly reports."

  raw_notes: "Owner Mike has been in plumbing for 22 years, started ClearFlow 15 years ago. Wife Sarah handles the books. They have 4 trucks and 8 employees. Emergency calls are their best margin work. They want to grow but Mike doesn't have time for marketing."
  metadata:
    source: "onboarding_interview"
    onboarded_date: "2026-03-15"
```

### File: `kai/archetypes/fixtures/ecommerce_example.yaml`

A realistic **DTC skincare brand** selling online.

Requirements for this fixture:
- Business name: "Dew & Bloom" — a clean beauty skincare brand
- Stage: growth
- 4+ products with prices and margin tiers
- Website (Shopify), Meta Ads active, email active (Klaviyo), Instagram active, TikTok testing
- 2 personas: "Ingredient Investigator" (researches everything) and "Gift Giver" (buying for someone)
- Trust: 200+ product reviews, featured in 2 beauty publications
- Goals: increase AOV from $48 to $62, grow email list by 5K subscribers
- Budget: $8,000/mo
- Constraints: clean beauty claims must be substantiated, no "anti-aging" claims without evidence
- Brand voice: warm, science-informed, empowering
- Include realistic sales cycle, buyer type (b2c, d2c), and operator capacity

### File: `kai/archetypes/fixtures/professional_services_example.yaml`

A realistic **personal injury law firm** with B2B and B2C elements.

Requirements for this fixture:
- Business name: "Reeves & Associates" — personal injury law firm
- Stage: growth
- 4+ practice areas (auto accidents, slip and fall, medical malpractice, wrongful death)
- Website, Google Ads active, some LinkedIn, no real social presence
- 2 personas: "Accident Victim Andy" (just got hurt, urgent) and "Referral Attorney Rachel" (other lawyers sending cases)
- Trust: 50+ case results, state bar certifications, $50M+ in settlements
- Goals: increase qualified leads to 30/month, improve close rate to 40%
- Budget: $15,000/mo (heavy Google Ads spend)
- Constraints: state bar advertising rules, no guaranteed outcomes, client confidentiality
- Brand voice: compassionate but authoritative, fighter mentality
- Include realistic sales cycle (30-90 days for direct, varies for referrals)

### File: `kai/archetypes/fixtures/multi_location_example.yaml`

A realistic **multi-location dental practice** with 5 locations.

Requirements for this fixture:
- Business name: "Bright Smile Dental" — general and cosmetic dentistry
- Stage: scale
- 5 locations across the Dallas-Fort Worth metro (Dallas, Plano, Arlington, Frisco, Fort Worth)
- Each location has different review counts, hours, and GBP status
- Services: general dentistry, cosmetic, orthodontics, pediatric, emergency
- 2 personas: "Anxious Adult Amanda" (dental anxiety, needs a gentle practice) and "Busy Parent Brian" (needs convenient scheduling for family)
- Trust: 500+ total reviews (unevenly distributed), accreditations
- Goals: bring all locations to 4.5+ Google rating, 50+ reviews each
- Budget: $25,000/mo total across locations
- Constraints: healthcare/HIPAA overlay needed, no before/after without consent
- Include realistic per-location channel states (some locations have better GBP than others)
- Franchise vs company-owned: company-owned

## Output Files

- `kai/archetypes/fixtures/local_service_example.yaml`
- `kai/archetypes/fixtures/ecommerce_example.yaml`
- `kai/archetypes/fixtures/professional_services_example.yaml`
- `kai/archetypes/fixtures/multi_location_example.yaml`

## Acceptance Criteria

- [ ] All 4 YAML files exist and are valid YAML
- [ ] Each fixture has a `business_profile:` top-level key matching the loader format (Task 002)
- [ ] Local service fixture has complete data for all BusinessProfile sections
- [ ] Ecommerce fixture represents a realistic DTC brand with Shopify, Klaviyo, and Meta Ads
- [ ] Professional services fixture includes bar advertising constraints and case result metrics
- [ ] Multi-location fixture has 5 distinct locations with varying states and review counts
- [ ] Each fixture has at least 2 personas with pain points, triggers, and objections
- [ ] Each fixture has realistic budget, goals, and KPI targets
- [ ] Each fixture has realistic trust signals (not placeholder data)
- [ ] Each fixture has channel presence entries showing a mix of active and inactive channels
- [ ] Data feels like real businesses — names, addresses, prices, and details are plausible
- [ ] Each fixture can be loaded by `load_from_yaml()` (Task 002) — structure matches the BusinessProfile schema (Task 001)

## Reference Materials

- `kai/models/business_profile.py` (Task 001) — the schema these fixtures must conform to
- `kai/loaders/profile_loader.py` (Task 002) — the loader that will parse these files
- `kai/archetypes/local_service.py` (Task 006) — archetype KPIs and channel mix
- `kai/archetypes/ecommerce.py` (Task 007) — ecommerce archetype
- `kai/archetypes/professional_services.py` (Task 008) — professional services archetype
- `kai/archetypes/multi_location.py` (Task 009) — multi-location archetype
- `knowledge/checklists/local-service-business-checklist.md` — local service details
- `knowledge/checklists/healthcare-medical-checklist.md` — healthcare overlay details
