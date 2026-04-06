# Task 069: Build social staleness and content freshness watchers

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 12. Background Automation and Watcher Loops
**Priority:** P2
**Depends on:** 067
**Estimated complexity:** Medium

## Context

Social media accounts that go dormant signal to customers (and algorithms) that a business is inactive or doesn't care about its online presence. Content that goes stale — outdated blog posts, old testimonials, unchanged landing page copy — erodes trust and hurts SEO performance. These watchers monitor the "freshness" of a business's content across all channels and flag when something needs a refresh. They are particularly valuable for local service businesses that often let their social and content presence go dormant between busy seasons.

## Scope

Create `kai/watchers/social_freshness.py` containing three concrete watcher implementations: SocialStalenessWatcher (daily), ContentFreshnessWatcher (weekly), and EngagementDeclineWatcher (weekly).

## Detailed Requirements

### File: `kai/watchers/social_freshness.py`

Import and extend the `Watcher` abstract class from `kai/watchers/framework.py`.

**Class: SocialStalenessWatcher(Watcher)**
- `name = "social_staleness"`
- `description = "Monitors days since last post on each social platform and flags dormant accounts"`
- `schedule_type = "daily"`
- `archetype_relevance = []` — relevant for all archetypes
- `STALENESS_THRESHOLDS`:
  - `info`: 7 days since last post
  - `warning`: 14 days since last post
  - `critical`: 30 days since last post
- `PLATFORM_EXPECTATIONS`: dict mapping platform to recommended posting frequency
  - `facebook`: every 3-5 days
  - `instagram`: every 2-3 days
  - `linkedin`: every 3-5 days
  - `tiktok`: every 1-2 days
  - `x_twitter`: daily
  - `youtube`: weekly
  - `google_business`: weekly (GBP posts)
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - For each active social platform in the business profile:
    - Determine days since last post (from workspace state or connector data)
    - If exceeds threshold, generate a finding
    - Findings include proposed action: generate proof-of-life posts
- `_check_platform_staleness(self, platform: str, last_post_date: Optional[str], business_profile: Any) -> Optional[WatcherFinding]`:
  - Compare last_post_date to current date
  - Calculate days_dormant
  - Determine severity from STALENESS_THRESHOLDS
  - Title: f"{platform} account dormant for {days_dormant} days"
  - Evidence: {platform, last_post_date, days_dormant, recommended_frequency}
  - Suppression key: f"social_stale_{platform}_{business_id}"
  - Proposed action (if critical): auto-propose proof-of-life content from content inventory
    - action_type: "social_post"
    - description: f"Publish a proof-of-life post on {platform} to maintain presence"
    - auto_eligible: True (can auto-generate and queue for approval)
- `_suggest_proof_of_life_content(self, platform: str, business_profile: Any) -> Dict[str, Any]`:
  - Return a proposed action dict with content suggestions:
    - Behind-the-scenes photo concept
    - Customer review highlight
    - Seasonal tip related to the business's services
    - Team spotlight
  - Pick based on what type of content performs best on the platform

**Class: ContentFreshnessWatcher(Watcher)**
- `name = "content_freshness"`
- `description = "Monitors content age across website and flags stale pages, outdated testimonials, and unchanged copy"`
- `schedule_type = "weekly"`
- `archetype_relevance = []` — relevant for all
- `FRESHNESS_THRESHOLDS`:
  - `blog_posts`: 12 months without update → flag for refresh
  - `landing_pages`: 6 months without copy change → flag
  - `testimonials`: 24 months old → flag for refresh
  - `team_page`: any change in staff not reflected → flag
  - `pricing_offers`: 3 months without verification → flag
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Check each content category against freshness thresholds
- `_check_blog_freshness(self, workspace_state) -> List[WatcherFinding]`:
  - Stub: would scan blog post dates from CMS or sitemap
  - Return finding for each post older than threshold
  - Title: f"Blog post '{post_title}' hasn't been updated in {months} months"
  - Evidence: {post_url, published_date, last_modified_date, months_since_update}
  - Proposed action: content refresh (update statistics, add new examples, refresh intro)
- `_check_landing_page_freshness(self, workspace_state) -> List[WatcherFinding]`:
  - Stub: would check landing page last-modified dates
  - Evidence: {page_url, last_modified, months_unchanged}
  - Proposed action: copy refresh, A/B test new headline or CTA
- `_check_testimonial_freshness(self, business_profile) -> Optional[WatcherFinding]`:
  - Check if testimonials/reviews being displayed are older than threshold
  - Evidence: {oldest_testimonial_date, average_testimonial_age_months, total_testimonials}
  - Proposed action: review request campaign to generate fresh testimonials
- `_check_team_page_accuracy(self, business_profile) -> Optional[WatcherFinding]`:
  - Stub: would compare team page content against known employee data
  - Evidence: {team_page_url, potential_issues}
  - Proposed action: update team page
- `_check_pricing_accuracy(self, business_profile, workspace_state) -> Optional[WatcherFinding]`:
  - Check when pricing information was last verified
  - Evidence: {last_verified_date, months_since_verification, pricing_pages}
  - Proposed action: verify pricing with business owner, update if changed

**Class: EngagementDeclineWatcher(Watcher)**
- `name = "engagement_decline"`
- `description = "Monitors engagement rate trends across social platforms and flags declining performance"`
- `schedule_type = "weekly"`
- `archetype_relevance = []` — relevant for all
- `DECLINE_THRESHOLDS`:
  - `warning`: 20% decline in engagement rate over 30 days
  - `critical`: 40% decline in engagement rate over 30 days
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - For each active social platform, check engagement metrics
- `_check_engagement_rate(self, platform: str, current_rate: float, previous_rate: float) -> Optional[WatcherFinding]`:
  - Calculate percent change
  - If decline exceeds threshold, generate finding
  - Title: f"{platform} engagement rate declined {pct_change:.0f}% over 30 days"
  - Evidence: {platform, current_rate, previous_rate, pct_change, period}
  - Possible causes in description: algorithm changes, content quality, posting frequency, audience mismatch
- `_check_follower_growth(self, platform: str, current_followers: int, previous_followers: int, days: int) -> Optional[WatcherFinding]`:
  - Calculate growth rate
  - If negative growth (losing followers): severity="warning"
  - If zero growth over 30+ days: severity="low" (info)
  - Evidence: {platform, current_followers, previous_followers, net_change, daily_growth_rate}
- `_check_reach_decline(self, platform: str, current_reach: float, previous_reach: float) -> Optional[WatcherFinding]`:
  - Compare 30-day reach to previous 30-day reach
  - If > 30% decline: severity="medium", possible algorithm penalty
  - Evidence: {platform, current_reach, previous_reach, pct_change}
  - Proposed action: content strategy review, format diversification

## Output Files

- `kai/watchers/social_freshness.py`

## Acceptance Criteria

- File parses as valid Python
- All three watcher classes properly extend the abstract `Watcher` base class
- SocialStalenessWatcher includes platform-specific posting frequency expectations
- Staleness thresholds are correctly tiered (7d info, 14d warning, 30d critical)
- ContentFreshnessWatcher covers all five content categories with appropriate thresholds
- EngagementDeclineWatcher includes engagement rate, follower growth, and reach checks
- All findings have appropriate suppression_key values
- Proof-of-life content suggestions include specific content ideas (not just "post something")
- All stub methods have docstrings explaining what data source they would query
- Proposed actions are included where auto-generation is feasible
- `get_default_config()` returns appropriate values for each watcher

## Reference Materials

- `kai/watchers/framework.py` (Task 067) — Watcher base class, WatcherFinding
- `kai/connectors/analytics/ga4.py` (Task 056) — website traffic data
- `kai/connectors/analytics/gbp.py` (Task 056) — GBP data
- `knowledge/channels/` — channel-specific posting best practices
