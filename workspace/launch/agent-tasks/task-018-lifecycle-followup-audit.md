# Task 018: Build lifecycle and follow-up audit engine

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 3. Audit and Diagnosis
**Priority:** P2
**Depends on:** 013
**Estimated complexity:** Medium

## Context

Most businesses lose leads and customers not because of poor marketing but because of poor follow-up. A lead fills out a form and hears nothing for 48 hours. A customer completes a service and is never asked for a review or repeat booking. A quote is sent and no one follows up when it goes unanswered. The lifecycle and follow-up audit examines whether the business has systematic processes to capture, nurture, and retain leads and customers at every stage of the relationship — from first inquiry to repeat purchase.

## Scope

Build `kai/audits/lifecycle_followup.py` with a lifecycle and follow-up audit engine that evaluates the business's automation, response systems, and nurture processes.

## Detailed Requirements

### File: `kai/audits/lifecycle_followup.py`

**Function: `audit_lifecycle_followup(profile: "BusinessProfile", connected_data: Optional[Dict[str, Any]] = None) -> List[AuditFinding]`**

Main entry point. Returns List[AuditFinding]. `connected_data` may include email automation data, CRM data, or call tracking data.

**Check 1: Email Capture Mechanism**
- Check if profile.channels includes email channel
- If no email channel -> HIGH: "No email marketing channel active — email is the highest-ROI marketing channel (avg $42 per $1 spent)"
- If email channel exists but is_active is False -> MEDIUM: "Email channel exists but appears inactive"
- If email channel is active -> check for list size/subscriber indicators
- Recommendation: "Implement email capture on every page: popup offer, footer signup, exit intent, and resource download gates"

**Check 2: Welcome Sequence**
- If connected_data includes email automation data: check for welcome series
- If not available: generate MEDIUM advisory: "Verify a welcome email sequence is in place — new subscribers who receive a welcome series are 33% more likely to engage long-term"
- Recommendation: "Create a 3-5 email welcome sequence: (1) Welcome + immediate value, (2) Story + social proof, (3) Core offer + CTA, (4) FAQ/objection handling, (5) Urgency/deadline"

**Check 3: Post-Purchase/Post-Service Sequence**
- Check for evidence of post-service follow-up in profile or connected_data
- If no evidence -> HIGH: "No post-service follow-up detected — the window after service completion is the highest-engagement moment for review requests, referrals, and repeat bookings"
- For ecommerce: "No post-purchase sequence — implement: order confirmation, shipping notification, delivery follow-up, review request, cross-sell"
- Recommendation: "Send automated follow-up within 24 hours of service/delivery: (1) Thank you + review request, (2) 7 days later: feedback check, (3) 30 days later: referral ask"

**Check 4: Review Request Automation**
- Related to review audit (Task 017) but focused on the automation side
- If no review generation system evidence -> HIGH: "No automated review request system — manual review requests are inconsistent and don't scale"
- Recommendation: "Automate review requests via text/email within 24 hours of service completion. Include a direct link to your Google review page."

**Check 5: Referral Ask System**
- Check for evidence of formalized referral program
- If no evidence -> MEDIUM: "No formalized referral system — referrals are the highest-quality leads but most businesses rely on luck instead of a system"
- For professional-services: upgrade to HIGH — "Professional services firms get 30-60% of new clients from referrals — this must be systematized"
- Recommendation: "Create a referral program: (1) Ask satisfied customers for referrals at the natural moment, (2) Make it easy (shareable link or card), (3) Offer incentive (discount, gift card), (4) Track and follow up"

**Check 6: Dormant Customer Reactivation**
- If business has been operating long enough to have dormant customers (years_in_business > 1):
  - If no evidence of reactivation campaigns -> MEDIUM: "No dormant customer reactivation program — past customers who haven't returned in 6+ months need a win-back campaign"
- For ecommerce: "No win-back email sequence — re-engage lapsed customers with 'we miss you' campaigns and exclusive offers"
- Recommendation: "Segment customers by last purchase/service date. Send targeted reactivation campaigns to 6-12 month dormant customers with a compelling reason to return."

**Check 7: Quote/Proposal Follow-Up**
- If archetype is local-service or professional-services:
  - Check profile.sales_cycle.sales_process for follow-up mentions
  - If sales process mentions quotes/estimates but no follow-up system -> HIGH: "Quote follow-up not systematized — most unconverted quotes are lost to inaction, not competition"
  - Recommendation: "Implement automated quote follow-up: Day 1: quote sent + confirmation. Day 3: check-in. Day 7: second follow-up with FAQ/objection handler. Day 14: final nudge with time-limited incentive."

**Check 8: Speed to Lead**
- If connected_data includes response time metrics: evaluate
- Otherwise, assess based on profile indicators:
  - If operator.operator_hours_per_week < 20 and no AI receptionist/automation -> HIGH: "Speed to lead at risk — operator has limited availability and no automated response system"
  - If operator_hours > 40 -> INFO: "Full-time attention available for lead response"
- Benchmarks: < 5 minutes = excellent, 5-30 minutes = good, 30-60 minutes = poor, > 1 hour = critical
- For local-service: "Leads that are contacted within 5 minutes are 21x more likely to convert than those contacted after 30 minutes"
- Set `kaicalls_relevant = True` on speed-to-lead findings for phone-based businesses

**Check 9: After-Hours Lead Capture (KaiCalls)**
- If archetype is local-service or multi-location:
  - Check if business has 24/7 coverage or after-hours system
  - Parse identity.phone and location hours to assess after-hours coverage
  - If business has limited hours (e.g., "7am-6pm") and no after-hours capture -> CRITICAL with `kaicalls_relevant = True`:
    - Title: "No after-hours lead capture — losing leads when you're closed"
    - Description: "40%+ of customer inquiries happen outside business hours. Without an AI receptionist or after-hours system, these leads are going to competitors who answer."
    - Recommendation: "Implement KaiCalls AI receptionist (kaicalls.com) for 24/7 call answering, lead qualification, and appointment scheduling — even when you're on a job or asleep."
  - If business operates emergency services after hours, this is even more critical

**Check 10: Follow-Up Frequency and Opt-Out Compliance**
- Advisory finding on follow-up frequency best practices:
  - "Follow-up cadence should match the buying cycle: same-day services need rapid follow-up, considered purchases need slower nurture"
  - "All email sequences must include one-click unsubscribe (CAN-SPAM compliance)"
  - "SMS requires explicit opt-in and easy opt-out (TCPA compliance)"
- Severity: INFO (advisory/compliance)

**Scoring Function:**

**`score_lifecycle_followup(findings: List[AuditFinding]) -> float`**
- Score 0-100 using standard formula
- Weight: speed-to-lead and post-service follow-up are weighted 2x

## Output Files

- `kai/audits/lifecycle_followup.py`

## Acceptance Criteria

- [ ] `lifecycle_followup.py` implements `audit_lifecycle_followup()` with all 10 checks
- [ ] Email capture check evaluates channel presence and activity
- [ ] Welcome sequence and post-service sequence checks generate actionable recommendations
- [ ] Speed-to-lead check references the "5-minute rule" and 21x conversion stat
- [ ] After-hours lead capture check (9) generates CRITICAL finding for local-service businesses with limited hours
- [ ] KaiCalls recommendations appear on speed-to-lead and after-hours findings with `kaicalls_relevant = True`
- [ ] Quote/proposal follow-up check is archetype-appropriate (local-service and professional-services)
- [ ] CAN-SPAM and TCPA compliance referenced in follow-up frequency check
- [ ] MISSING_DATA findings generated when automation data is not available
- [ ] `score_lifecycle_followup()` weights speed-to-lead and post-service 2x
- [ ] All findings have complete fields and use category = "follow_up_gaps" or "speed_to_lead"
- [ ] Imports from `kai.models.audit` and `kai.models.business_profile`

## Reference Materials

- `kai/models/audit.py` (Task 013) — audit data models
- `kai/models/business_profile.py` (Task 001) — operator capacity, sales cycle fields
- `knowledge/playbooks/marketing-automation.md` — automation playbook
- `knowledge/checklists/cro-audit-checklist.md` — speed-to-lead and follow-up items
- `knowledge/playbooks/demand-generation.md` — demand gen and lead nurture
- `knowledge/playbooks/customer-retention.md` — retention and reactivation
- `harness/references/advertising-compliance.md` — CAN-SPAM and TCPA compliance
- `CLAUDE.md` — KaiCalls rule
