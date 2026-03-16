# Email & Lifecycle Marketing Checklist

> **Use when:** Setting up email infrastructure, launching automation flows, or auditing email program health.

## Infrastructure Setup
- [ ] Platform selected (Klaviyo/Braze/Customer.io/HubSpot) based on business model
- [ ] SPF record configured in DNS
- [ ] DKIM authentication enabled
- [ ] DMARC policy set (start with p=none, plan progression)
- [ ] Dedicated IP requested (if volume >100k/month)
- [ ] IP warming schedule documented and ready
- [ ] Real-time email validation tool integrated (NeverBounce, ZeroBounce)

## Email Authentication Verification
- [ ] SPF passing (check with mail-tester.com)
- [ ] DKIM signing verified
- [ ] DMARC reports being received
- [ ] BIMI setup initiated (if DMARC at quarantine/reject)

## IP Warming (If Applicable)
- [ ] Days 1-3: 50-200 emails to most engaged users only
- [ ] Days 4-7: 500-1,000 to opened-last-7-days segment
- [ ] Days 8-14: 2,000-5,000 to opened-last-30-days segment
- [ ] Days 15-21: 10,000-25,000 to opened-last-60-days segment
- [ ] Days 22-30: Full volume excluding 90-180 day inactive
- [ ] Monitoring: >25% open rate, <0.1% complaint rate maintained

## Sequence Design

### B2B SaaS Onboarding
- [ ] Welcome email with magic link (immediate)
- [ ] Empty state solver (Day 1-2, triggered if NOT activated)
- [ ] Team invite prompt (Day 3-5, triggered if activated)
- [ ] Sales hand-raiser (Day 7+, triggered by high usage)
- [ ] Logic prevents sending empty-state email to activated users

### B2B SaaS Trial Expiration
- [ ] T-3 days: Value summary with dynamic usage data
- [ ] T-1 day: Loss aversion messaging
- [ ] T-0 day: Grace period offer

### DTC Abandonment
- [ ] Browse abandonment: Soft touch, no discount
- [ ] Cart abandonment: Helpful reminder, address friction points
- [ ] Checkout abandonment: Urgency + discount/free shipping offer
- [ ] Flows exclude users who converted

### DTC Inventory Triggers
- [ ] Low stock alert configured (threshold defined)
- [ ] Back-in-stock flow with tiered delivery (VIPs first)

### Fintech/Crypto Compliance
- [ ] No prohibited terms (guaranteed returns, risk-free, passive income)
- [ ] Risk disclaimers present and formatted per jurisdiction
- [ ] Security alerts (new device, withdrawal) deliver <1 minute
- [ ] Transactional emails remain primarily transactional

## List Hygiene
- [ ] Sunset policy defined (90-180 day inactivity threshold)
- [ ] Re-engagement campaign created (runs before sunset)
- [ ] Suppression list maintained (unsubscribes, hard bounces, spam complaints)
- [ ] Regular list cleaning scheduled (quarterly minimum)
- [ ] No purchased or scraped lists in database

## Segmentation
- [ ] Engagement tiers defined (Active, Lapsing, Inactive)
- [ ] Broadcasts segmented by engagement level
- [ ] Full-list sends reserved for major announcements only
- [ ] Product/category interest segments created (DTC)
- [ ] PQL scoring configured (B2B SaaS)

## Measurement Setup
- [ ] Revenue Per Recipient (RPR) tracking enabled
- [ ] Conversion rate tracking by flow/campaign
- [ ] Unsubscribe rate per campaign monitored
- [ ] Holdout groups configured for incrementality testing
- [ ] P&L model implemented (not just revenue tracking)

## Subject Lines
- [ ] Under 50 characters (mobile optimization)
- [ ] Critical keywords front-loaded
- [ ] Appropriate formula used for context (scarcity, question, utility)
- [ ] A/B testing configured for major campaigns

## Campaign Launch
- [ ] Test email sent and reviewed on mobile + desktop
- [ ] Links verified and working
- [ ] Personalization tokens rendering correctly
- [ ] Unsubscribe link present and functional
- [ ] Suppression lists applied
- [ ] Send time optimized (or A/B tested)

## Monthly Audit
- [ ] Deliverability metrics reviewed (inbox placement, bounce rate)
- [ ] Complaint rate below 0.1%
- [ ] Engagement trends analyzed (opens, clicks trending)
- [ ] Sunset suppressions applied
- [ ] Incrementality results reviewed
- [ ] Contribution margin calculated
