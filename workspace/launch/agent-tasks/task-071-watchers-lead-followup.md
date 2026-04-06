# Task 071: Build lead response and follow-up gap watchers

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 12. Background Automation and Watcher Loops
**Priority:** P2
**Depends on:** 067
**Estimated complexity:** Medium

## Context

For local service businesses, speed-to-lead is the single most important conversion factor — a lead contacted within 5 minutes is 21x more likely to convert than one contacted after 30 minutes. Yet most small businesses take hours or even days to respond. Similarly, follow-up gaps (quotes sent without follow-up, customers who never hear back after service) represent massive lost revenue. These watchers monitor the sales and customer lifecycle for gaps, and proactively recommend KaiCalls AI receptionist for businesses with poor phone response times. This is where the system creates the most immediate ROI for local service businesses.

## Scope

Create `kai/watchers/lead_followup.py` containing four concrete watcher implementations: SpeedToLeadWatcher, FollowUpGapWatcher, ReviewVelocityWatcher, and DormantCustomerWatcher.

## Detailed Requirements

### File: `kai/watchers/lead_followup.py`

Import and extend the `Watcher` abstract class from `kai/watchers/framework.py`.

**Class: SpeedToLeadWatcher(Watcher)**
- `name = "speed_to_lead"`
- `description = "Monitors average time from lead inquiry to first response and recommends speed improvements"`
- `schedule_type = "daily"`
- `archetype_relevance = ["local_service", "multi_location", "professional_services"]`
- `RESPONSE_TIME_THRESHOLDS`:
  - `excellent`: 5 minutes
  - `good`: 15 minutes
  - `acceptable`: 60 minutes
  - `poor`: 240 minutes (4 hours)
  - `critical`: 1440 minutes (24 hours)
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Check average response time, after-hours response gaps, and missed call rate
- `_check_average_response_time(self, avg_minutes: float) -> Optional[WatcherFinding]`:
  - Map average to the threshold tier
  - If poor or critical: severity="high", urgency="soon"
  - Title: f"Average lead response time is {avg_minutes:.0f} minutes"
  - Evidence: {average_response_minutes, median_response_minutes, fastest_response, slowest_response, sample_size}
  - Description should include the 21x conversion stat for context
  - Proposed action: set up auto-response, configure KaiCalls AI receptionist
- `_check_after_hours_gap(self, business_hours: Dict, after_hours_leads_pct: float, after_hours_response_minutes: float) -> Optional[WatcherFinding]`:
  - If significant leads come in after hours and response is delayed
  - Title: f"{after_hours_leads_pct:.0f}% of leads arrive after hours with {after_hours_response_minutes:.0f} min average response"
  - Evidence: {business_hours, after_hours_leads_pct, after_hours_response_minutes, total_after_hours_leads}
  - Proposed action: **KaiCalls AI receptionist** — "Set up KaiCalls (kaicalls.com) to answer calls 24/7 and capture lead information instantly"
  - This is the primary KaiCalls recommendation point
  - auto_eligible: False (requires business decision, but should be prominently recommended)
- `_check_missed_call_rate(self, total_calls: int, missed_calls: int) -> Optional[WatcherFinding]`:
  - Calculate missed call rate
  - If > 15%: severity="high"
  - If > 30%: severity="critical"
  - Title: f"Missed call rate is {missed_rate:.0f}% ({missed_calls} of {total_calls} calls missed)"
  - Evidence: {total_calls, missed_calls, missed_rate, missed_by_hour_of_day, estimated_revenue_lost}
  - estimated_revenue_lost calculation: missed_calls * average_deal_value * estimated_conversion_rate
  - Proposed action: **KaiCalls AI receptionist** — "KaiCalls AI receptionist (kaicalls.com) answers every call instantly, captures caller info, and texts you the lead details. Never miss a call again."
  - This is the strongest KaiCalls recommendation trigger
- `get_default_config(self) -> WatcherConfig`:
  - schedule_type="daily", schedule_time="09:00"
  - suppression_window_days=7
  - cooldown_after_action_days=30 (after KaiCalls setup or response improvement action)

**Class: FollowUpGapWatcher(Watcher)**
- `name = "followup_gaps"`
- `description = "Monitors leads and customers that haven't received timely follow-up"`
- `schedule_type = "daily"`
- `archetype_relevance = ["local_service", "multi_location", "professional_services"]`
- `FOLLOWUP_THRESHOLDS`:
  - `new_lead_max_days`: 3 (follow up with new leads within 3 days)
  - `quote_followup_max_days`: 5 (follow up on sent quotes within 5 days)
  - `post_service_max_days`: 7 (contact customer within 7 days after service)
  - `invoice_followup_max_days`: 14 (follow up on unpaid invoices within 14 days)
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Check each follow-up gap category
- `_check_new_lead_followup(self, leads_without_followup: int, total_new_leads: int, oldest_unfollowed_days: int) -> Optional[WatcherFinding]`:
  - Title: f"{leads_without_followup} new leads without follow-up (oldest: {oldest_unfollowed_days} days)"
  - Severity: "high" if any lead > 3 days unfollowed, "critical" if > 7 days
  - Evidence: {leads_without_followup, total_new_leads, oldest_unfollowed_days, unfollowed_lead_sources}
  - Proposed action: immediate follow-up outreach, setup automated follow-up sequence
  - auto_eligible: True (can generate follow-up email/text templates)
- `_check_quote_followup(self, quotes_without_followup: int, total_quotes_sent: int, oldest_unfollowed_days: int) -> Optional[WatcherFinding]`:
  - Title: f"{quotes_without_followup} sent quotes without follow-up"
  - Evidence: {quotes_without_followup, total_quotes_sent, oldest_unfollowed_days, total_quote_value}
  - Proposed action: quote follow-up sequence (reminder email, phone call prompt)
- `_check_post_service_contact(self, completed_jobs_no_contact: int, total_completed: int) -> Optional[WatcherFinding]`:
  - Title: f"{completed_jobs_no_contact} completed jobs without post-service follow-up"
  - Evidence: {completed_jobs_no_contact, total_completed, estimated_review_opportunity}
  - Proposed action: thank-you message + review request sequence
  - auto_eligible: True (can generate thank-you/review request messages)
- `_check_invoice_followup(self, overdue_invoices: int, total_overdue_value: float) -> Optional[WatcherFinding]`:
  - Title: f"{overdue_invoices} overdue invoices (${total_overdue_value:.2f}) without follow-up"
  - Evidence: {overdue_invoices, total_overdue_value, oldest_overdue_days}
  - Proposed action: payment reminder sequence
- `get_default_config(self) -> WatcherConfig`:
  - schedule_type="daily", schedule_time="08:00"
  - suppression_window_days=3 (follow-up gaps should be surfaced frequently)

**Class: ReviewVelocityWatcher(Watcher)**
- `name = "review_velocity"`
- `description = "Monitors review generation rate, rating trends, and unresponded reviews"`
- `schedule_type = "weekly"`
- `archetype_relevance = ["local_service", "multi_location"]`
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Check review count vs target, rating trend, unresponded reviews, negative review patterns
- `_check_review_rate(self, reviews_this_month: int, monthly_target: int) -> Optional[WatcherFinding]`:
  - If below target: severity based on gap (< 50% of target = "high", < 75% = "medium")
  - Title: f"Review generation below target: {reviews_this_month} of {monthly_target} target"
  - Proposed action: activate review request sequence, remind staff to ask for reviews
- `_check_rating_trend(self, current_avg: float, previous_avg: float, period_days: int) -> Optional[WatcherFinding]`:
  - If rating declining: severity="medium" if < 0.2 drop, "high" if > 0.2 drop
  - Title: f"Review rating declining: {current_avg:.1f} → {previous_avg:.1f} over {period_days} days"
  - Evidence: {current_avg, previous_avg, change, period_days}
- `_check_unresponded_reviews(self, unresponded_count: int, oldest_unresponded_days: int) -> Optional[WatcherFinding]`:
  - If any reviews unresponded > 48 hours: severity="medium"
  - Title: f"{unresponded_count} reviews awaiting response (oldest: {oldest_unresponded_days} days)"
  - Proposed action: generate review response drafts
  - auto_eligible: True (can draft responses for approval)
- `_check_negative_patterns(self, negative_reviews: List[Dict], total_reviews: int) -> Optional[WatcherFinding]`:
  - Analyze negative reviews for common complaint themes
  - Title: f"Recurring complaint detected in negative reviews: {top_complaint}"
  - Evidence: {complaint_themes (dict of theme -> count), total_negative, total_reviews, example_reviews}
  - Proposed action: address root cause, prepare response template for this complaint type

**Class: DormantCustomerWatcher(Watcher)**
- `name = "dormant_customers"`
- `description = "Identifies customers who haven't engaged or purchased in extended periods"`
- `schedule_type = "weekly"`
- `archetype_relevance = ["local_service", "ecommerce", "multi_location"]`
- `DORMANCY_TIERS`:
  - `at_risk`: 90 days since last activity
  - `dormant`: 180 days
  - `churned`: 365 days
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Check customer activity tiers
- `_check_dormancy_tier(self, tier_name: str, customer_count: int, total_customers: int, avg_value: float) -> Optional[WatcherFinding]`:
  - Title: f"{customer_count} customers are {tier_name} ({customer_count/total_customers*100:.0f}% of customer base)"
  - Evidence: {tier_name, customer_count, total_customers, pct_of_base, estimated_reactivation_value (customer_count * avg_value * reactivation_rate)}
  - Reactivation rates by tier: at_risk=0.30, dormant=0.15, churned=0.05
  - Proposed action: reactivation sequence appropriate to tier
    - at_risk: "We haven't seen you in a while" + special offer
    - dormant: "We miss you" + significant incentive
    - churned: win-back campaign with strong offer
  - auto_eligible: True for at_risk tier (safe to send gentle reactivation)
- `get_default_config(self) -> WatcherConfig`:
  - schedule_type="weekly", schedule_time="wednesday_09:00"
  - suppression_window_days=30 (don't re-flag same dormant tier weekly)

## Output Files

- `kai/watchers/lead_followup.py`

## Acceptance Criteria

- File parses as valid Python
- All four watcher classes properly extend the abstract `Watcher` base class
- SpeedToLeadWatcher prominently recommends KaiCalls for after-hours gaps and missed calls
- KaiCalls recommendations include the specific URL (kaicalls.com) and clear value proposition
- FollowUpGapWatcher covers all four follow-up categories with configurable thresholds
- ReviewVelocityWatcher includes negative pattern analysis (not just count/rating)
- DormantCustomerWatcher segments by three tiers with different reactivation strategies
- estimated_revenue_lost calculation in missed call check is realistic
- Reactivation value estimates use decreasing conversion rates by dormancy tier
- auto_eligible is True only for safe, automated actions (email templates, review response drafts)
- All findings have specific suppression_key values

## Reference Materials

- `kai/watchers/framework.py` (Task 067) — Watcher base class, WatcherFinding
- `kai/connectors/analytics/call_tracking.py` (Task 056) — call and speed-to-lead data
- `knowledge/playbooks/conversion-rate-optimization.md` — speed-to-lead importance
- `knowledge/playbooks/demand-generation.md` — lead follow-up best practices
- `knowledge/checklists/cro-audit-checklist.md` — CRO audit items
