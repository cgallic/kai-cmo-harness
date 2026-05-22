# Email & Lifecycle Marketing Checklist

> **Use when:** Setting up email infrastructure, launching automation flows, or auditing email program health.

## Infrastructure Setup
- [ ] Platform selected (Klaviyo/Braze/Customer.io/HubSpot) based on business model
- [ ] SPF record configured in DNS
- [ ] DKIM authentication enabled
- [ ] DMARC policy set (start with p=none, plan progression)
- [ ] From-domain alignment verified for bulk mail
- [ ] PTR/reverse DNS and TLS requirements checked for sending infrastructure
- [ ] One-click unsubscribe headers implemented for marketing/subscribed bulk mail
- [ ] Visible unsubscribe link included in the email body
- [ ] Dedicated IP requested (if volume >100k/month)
- [ ] IP warming schedule documented and ready
- [ ] Real-time email validation tool integrated (NeverBounce, ZeroBounce)

## Email Authentication Verification
- [ ] SPF passing (check with mail-tester.com)
- [ ] DKIM signing verified
- [ ] DMARC reports being received
- [ ] BIMI setup initiated (if DMARC at quarantine/reject)

## IP Warming (If Applicable)
- [ ] Start with recently engaged, consented recipients only
- [ ] Increase volume only after ESP logs and mailbox-provider dashboards are stable
- [ ] Monitor bounces, deferrals, spam complaints, authentication, domain reputation, and blocklist signals
- [ ] Pause scaling if complaints approach provider thresholds or reputation drops
- [ ] Exclude inactive users according to documented suppression policy

## Sequence Design

- [ ] Every flow declares lifecycle state: subscribed prospect, customer lifecycle, transactional, cold outbound, retention, win-back, or suppressed
- [ ] Every flow declares message class: marketing, subscribed, transactional, sales, support, or legal/service notice
- [ ] Every flow has exit criteria tied to product or purchase events
- [ ] Preference center and global suppression rules are tested before launch
- [ ] Frequency caps apply by message class and lifecycle state

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
- [ ] Open rate treated as directional only when Apple MPP or image proxying may inflate opens
- [ ] Flow reports separate attributed revenue from holdout-measured lift
- [ ] Data gaps listed when source data is unavailable

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
- [ ] Complaint rate reviewed against mailbox-provider thresholds and internal risk limits
- [ ] Engagement trends analyzed (opens, clicks trending)
- [ ] Sunset suppressions applied
- [ ] Incrementality results reviewed
- [ ] Contribution margin calculated
- [ ] DMARC aggregate reports reviewed for unauthorized senders
- [ ] Preference-center choices and unsubscribe processing verified
- [ ] Source references checked for policy changes: Google sender guidelines, Yahoo Sender Hub, FTC CAN-SPAM, Spamhaus

---

## Source Notes

Primary source requirements should be rechecked before launch. Current references retrieved 2026-05-17: Google Email Sender Guidelines, Yahoo Sender Hub FAQs and best practices, FTC CAN-SPAM compliance guide, Spamhaus cold-email guidance, and ESP/provider docs for the sending platform in use.
