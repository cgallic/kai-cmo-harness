# Marketing Growth Prompt Library

A reusable, agent-neutral working system for researching buyers, mapping journeys, building conversion loops and learning from verified business outcomes. It contains **30 prompts: one business-profile router, 23 growth prompts and six client-intelligence prompts**. This is a prompt library and operating design, not evidence that the prompts have been run or any campaign has launched.

## Start here

Run R0 to select the appropriate business profile and modules from available evidence. Then run P1–P3, close the most important measurement gap, and choose the next highest-value prompt. Do not run everything in parallel by default.

The assistant may select and combine profiles itself. Explain the selection, evidence and confidence; do not force a business into one category. Ask only when a missing fact materially affects the chosen goal, scope, permissions or recommendation.

<a id="r0"></a>

### R0: Select the business profile and next useful work

Review the business information and authorized evidence available to you. Identify how the business creates value, who buys, who uses or benefits, how money is earned, how delivery works and where capacity is constrained. Select one or more profiles from this library, explain the evidence and confidence, and note unresolved facts. For a hybrid, map each offer to its own journey and outcome instead of blending incompatible metrics. Populate the business profile below, recommend which prompts to run now and which to defer, and identify the first verifiable result we need. Ask only for missing information that would materially change the plan. Do not assume connected accounts, access, permissions or historical records exist merely because a tool or repository is listed.

**Output:** selected profile(s), supporting evidence, populated configuration, uncertainty/gap list, chosen prompts and first acceptance criterion.
**Feeds next:** P1, P2 and P3.

## Business configuration

- Business and selected type(s): [name; profile or hybrid]
- Offers and eligible products/services: [confirmed scope]
- Geography and eligible audience: [actual markets and restrictions]
- Purchaser, user, beneficiary and gatekeeper: [separate roles where applicable]
- North Star: [specific verified outcome and target]
- Progress: [verified amount] / [target]; **unknown until reconciled, never assumed zero**
- Measurement period and timezone: [confirmed dates; do not invent a deadline]
- Authoritative source: [orders, payments, jobs, billing, bookings, contracts or other system]
- Qualification and reversal rules: [what counts; refunds, cancellations, returns, churn]
- Economics and capacity: [contribution margin, servicing cost, staff/stock/slots]
- Operator strengths and channel owners: [named people and responsibilities]
- Approved claims, brand rules and asset rights: [sources and limits]
- Consent, suppression, privacy and regulated-work constraints: [applicable rules]
- Account/access register: [requested, connected, tested, approved uses]
- Working file and reporting destination: [this client’s authorized destination]
- Existing holds and approvals: [preserve them]

## Selectable business profiles

| Profile | Primary outcome and unit definition | Typical journey | Cadence and capacity | Critical metrics and buyer distinction |
|---|---|---|---|---|
| Local services and trades | Completed, paid, profitable jobs; qualified inquiries and bookings are leading indicators, not completed jobs | Discovery → call/form → qualification → estimate → scheduled job → completion/payment → maintenance/referral | Response time, seasonality, crew hours, dispatch and service area | Qualified inquiry-to-job, show/completion rate, contribution/job, repeat work. Caller, property owner and payer may differ |
| Ecommerce and physical products | Paid/fulfilled eligible units or orders, net of defined returns/cancellations; do not equate units with customers | Discovery → product → cart → checkout/payment → shipment → use → return or reorder | Inventory, shipping, stockouts, replenishment and seasonality | Contribution/order, conversion, AOV, returns, repeat purchase. Purchaser may be buying a gift or for another user |
| SaaS and subscriptions | Activated, retained paying accounts or appropriately defined recurring revenue; trial/sign-up is not activation/payment | Discovery → trial/demo → setup → first value → payment → sustained use → renewal/expansion/churn | Onboarding time, renewal cohorts, support/service costs | Activation, trial-to-paid, retention/churn, contribution and payback. Champion, admin, user, budget owner and buyer can differ |
| Local retail and hospitality | Completed profitable transactions, visits, reservations or stays; specify the unit | Discovery → reservation or walk-in → visit/service → payment → review/revisit | Opening hours, seats/rooms, staffing, local seasons and no-shows | Booking-to-visit, utilization, spend/visit, contribution, repeat rate. Booker, guest and payer may differ |
| Rentals and events | Completed, paid rentals/events with defined deposit, cancellation and refund treatment | Inquiry → date/availability → quote → deposit → logistics/setup → event → return/settlement → repeat/referral | Date-specific inventory, delivery routes, setup crew, damage and return timing | Quote-to-book, utilization, contribution/event, cancellations, delivery reliability. Planner, end client, venue and payer may differ |
| Professional practices | Suitable completed and paid engagements/appointments under the practice’s own permitted criteria; inquiry is not accepted service | Discovery/referral → permissioned intake → suitability/scheduling → appointment/engagement → service → payment/follow-up | Practitioner capacity, appointment cycles, confidentiality and professional obligations | Qualified-intake conversion, attendance, capacity and collection where appropriate. Client/patient, referrer, decision-maker and payer can differ; no automated sensitive eligibility judgments |
| B2B agencies and consulting | Signed, delivered and paid engagements or retained accounts, with each stage separately recorded | Introduction/inbound → discovery → qualification → proposal → procurement → signed engagement → delivery → invoice/payment → expansion | Longer buying cycles, procurement, billable capacity and scope control | Stage conversion, sales cycle, delivery margin, retention, receivables. Champion, economic buyer, procurement and users differ |

Profiles are starting models, not claims about a particular business. Each prompt below includes an adaptation instruction. Use the actual business configuration and observed journey rather than filling gaps with the typical journey.

## Ownership and operating rules

The designated operator owns commercial judgment and budgets. The assigned assistant supports research, organization and authorized implementation. Name accountable humans for paid, nonpaid, analytics, engineering, claims, creative approval, delivery and launch decisions. Do not invent staffing or override existing owners.

Use available relevant history, not presumed access to “everything.” Keep verified facts, interpretations, hypotheses, estimates and unknowns distinct. Cite important evidence with source and date. A direct quote needs an actual source; fewer verified phrases are better than invented ones.

Reuse working components. Separate prepared, approved, shipped and measured outcomes through the existing harness contracts. Repository features do not prove that a client’s accounts or collectors are connected. A draft, rendered asset, UI success or analytics event does not alone prove a commercial outcome.

Keep each client’s records, credentials, memory and destinations isolated. Open Brane business filters are not authorization boundaries; separate deployments are required across customer trust boundaries. Share sanitized methods and specifically approved deidentified lessons, not raw client history.

Preparing a prompt or deliverable does not authorize outreach, publishing, spending, production changes, new credentials or expanded access. Preserve permissions, holds and relevant industry/privacy constraints. This page does not schedule recurring execution.

## Lifecycle and dependency map

**Set up:** R0 → P1–P3 → P10/P20 → P11
**Learn:** P4–P8 and C1–C4 → evidence, personas, positioning → P9/P11
**Prepare:** P9/P12/P13 → channel plans P14–P17 → P18/P21
**Measure and retain:** verified release/outcomes → P19/P22 and C5
**Compound carefully:** owner-approved extracts → C6 → updated P5/P7/P11 → P23

| Prompt | Required inputs | Main output | Feeds next |
|---|---|---|---|
| R0 Profile router | Available business evidence | Selected profiles, configuration and uncertainty | P1–P3 |
| P1 Baseline | Authoritative outcome/reversal records | Reconciled goal gap and economics | P10, P11, P22 |
| P2 Systems and strengths | Repos, access, relevant prior work | Capability/gap and keep/amplify/automate map | P10, P20, P23 |
| P3 Journey | Observed screens, interactions and outcomes | Journey diagram and screen register | P10, P11, P18 |
| P4 Customer knowledge | Permissioned first-party sources | Source-linked insight bank and research gaps | P5–P9 |
| P5 ICP | Research and observed buyer situations | 50 hypotheses, top five validation priorities | P7, P12–P17 |
| P6 Historical comparisons | Relevant cited cases | Mechanisms, limits and test ideas | P7, P13 |
| P7 Messaging | ICP, motivations, proof | Truthful messaging matrix | P12–P17 |
| P8 Alternatives | Current competitor/alternative evidence | Positioning and differentiation tests | P7, P9 |
| P9 Offer ladder | Confirmed offers, economics and capacity | Approved/proposed offers separated | P12, P18, P19 |
| P10 Measurement | Journey and source systems | Tracking/reconciliation test matrix | P11, P18, P21, P22 |
| P11 Priorities | Evidence, constraints and gaps | Ranked next action and conditional backlog | Selected execution prompt |
| P12 Paid pack | ICP, offers, tracking, economics | Decision-ready paid test plan | P13, P18, P21 |
| P13 Creative | Insight, offer, proof, rights | Versioned briefs/assets/review criteria | P14–P18, P21 |
| P14 Email | Eligible segment, consent and lifecycle | Draft sequence with stops/measurement | P18, P21, P22 |
| P15 Search/content | Intent, existing pages and proof | Content improvement/cluster plan | P13, P18, P22 |
| P16 Social/community | Audience evidence and channel context | Test batch and response ownership | P13, P18, P22 |
| P17 Press/partners | Relevant relationships/news and standing | Ranked opportunities and drafts | Approved outreach, P22 |
| P18 CRO | Baseline and one evidenced bottleneck | Predeclared experiment and decision rules | P21, P22 |
| P19 Retention | Delivery/use/support/repeat evidence | Experience and repeat-value tests | P18, P22 |
| P20 Ownership | Existing roles and permissions | Responsibility/operating-loop diagram | All handoffs |
| P21 Launch | Exact candidate, journey and approvals | Evidence-backed go/no-go | Authorized launch, P22 |
| P22 Review | Mature independent observations | Reconciled decisions and next action | P11, P23 |
| P23 Reuse | Proven work and approved lessons | Portable client setup without data leakage | R0 for next business |
| C1 Deep Extract | Client-selected authorized business history | Owner-reviewed business evidence profile | C2–C4, P4 |
| C2 Persona Forge | Approved client/customer evidence | End-customer hypotheses and unknowns | P5/P7 for that client |
| C3 Purchase Path | Owner-approved actual purchases | Provider-buyer decision/objection map | Provider P5/P7/P12 |
| C4 Nostalgia/Edge/Loops | Relevant local/industry sources | Source-grounded messaging/test ideas | P6/P7/P19 |
| C5 Case Study | Mature outcome records | Draft stories and verification questions | P13/P17 only after public-use approval |
| C6 Aggregation | Reviewed, approved extract and allowed purpose | Provenance-preserving deidentified patterns | P5/P7/P11/P23 |

## Full growth prompt library

<a id="p1"></a>

### P1: Establish our baseline and path to the configured goal

Define our configured North Star precisely and reconcile current progress against authoritative order, payment, refund and fulfillment records. Distinguish units, orders, customers and subscriptions. Identify the remaining gap, product economics, capacity constraints and measurement period. Build conservative, base and upside scenarios with explicit assumptions. Show the required traffic, conversion and repeat-purchase contribution, without pretending those assumptions are forecasts. Identify the first bottleneck to investigate.

**Business-type adaptation:** Choose the profile’s primary outcome: paid and fulfilled orders, completed profitable jobs, activated retained subscriptions, completed bookings, or signed and paid engagements. Keep leads, signups, bookings and realized outcomes separate.

<a id="p2"></a>

### P2: Audit our systems and amplify the operator’s strengths

Review the relevant authorized repositories, the current business setup and authorized relevant prior assistant sessions, meeting notes and deliverables. Explain what each system actually does, which accounts and analytics are connected, and where there are gaps or duplication. Build a keep/amplify/automate matrix around the operator’s strengths, supported by examples. Use the tools to extend those strengths rather than replace them with generic workflows. Recommend the smallest integration plan that improves our ability to generate and measure sales.

**Business-type adaptation:** Use the profile’s existing CRM, booking, commerce, billing, POS or practice system. Replace operator name, channel owners and working-file references; verify rather than assume integrations.

<a id="p3"></a>

### P3: Map the complete customer journey and funnel

Map every observed entrypoint, screen, decision, action, exit and endpoint from discovery through purchase, fulfillment, repeat purchase and referral. Include failed payments, abandonment, support, cancellation and refunds. Create a journey diagram and a screen-by-screen register with URLs, CTAs, events, backend outcomes and owners. Distinguish live flows from demos and unverified assumptions. Identify the largest evidenced friction and the missing observation most likely to change our priorities.

**Business-type adaptation:** Use the selected profile’s journey row. Include its particular handoffs: dispatch, delivery, activation, reservation, equipment return or professional intake.

<a id="p4"></a>

### P4: Build our first-party customer knowledge base

Review accessible customer conversations, Fathom recordings, meeting notes, support questions, reviews, sales discussions and purchase behavior. Extract customers’ own language about their goals, frustrations, alternatives, objections and buying triggers. Separate direct quotes from interpretation and stated preference from observed behavior. Create a source-linked insight bank. Where evidence is missing, prepare a focused interview or survey plan with an owner and the decision each question should inform. Prepare outreach drafts without sending them.

**Business-type adaptation:** For service businesses review inquiry and job evidence; for products review order/use/returns; for SaaS review activation/churn; for practices use only appropriately permissioned, minimized intake information.

<a id="p5"></a>

### P5: Build the ICP matrix and 50 specific persona hypotheses

Create a table of 50 distinct, research-grounded adult-buyer persona hypotheses. Make them specific enough to guide messaging and creative, without inventing customer facts.

For each, include:
- Buying situation and job to be done
- Trigger and current alternative
- Desired practical and emotional outcome
- Main objection and required proof
- Relevant product or offer
- Messaging angle and creative concept
- Likely discovery channel
- Source evidence and applicable case study
- Confidence, contradictory evidence and validation test

Separate messaging personas from targeting options actually available on ad platforms. Avoid sensitive-trait inference and targeting children. Rank the five strongest starting hypotheses rather than spreading the budget across all 50.

**Business-type adaptation:** Distinguish purchaser, user, beneficiary and gatekeeper. For B2B include buying committee roles; for local services include caller versus property decision-maker. Fifty is a research target, not a license to fabricate.

<a id="p6"></a>

### P6: Find historical stepping stones and useful comparisons

Research relevant historical products, campaigns, communities and market shifts that can inform our strategy. Look beyond direct competitors, but explain the underlying mechanism that makes each comparison useful. Investigate nostalgia, identity, ritual, collecting, belonging, convenience and repeat-use patterns where supported by evidence. Include failures as well as successes. Cite original sources where possible, explain where the analogy breaks, and turn the strongest lessons into testable ideas for our market.

**Business-type adaptation:** Use market-relevant historical analogies and local/cultural context. Nostalgia is optional, not a universal strategy. Avoid applying one trade’s behavior to another business.

<a id="p7"></a>

### P7: Map purchase motivations and messaging angles

Map the emotional and practical journey from initial interest to purchase for our priority personas. Identify motivations, hesitation, trust requirements, identity, perceived risk and the moments when the customer needs reassurance or proof. Build a messaging matrix connecting each insight to a truthful promise, supporting evidence, creative angle, CTA and destination. Include several approaches, such as demonstration, comparison, founder expertise, customer proof and nostalgia. Avoid manufactured urgency, shame, deceptive claims or exploiting vulnerabilities.

**Business-type adaptation:** Match the decision’s stakes and time horizon: urgency for a service need, confidence for a product, adoption risk for SaaS, availability for a booking, trust and fit for a professional engagement.

<a id="p8"></a>

### P8: Analyze competitors and alternatives

Compare what customers choose instead of us, including direct competitors, adjacent products, informal workarounds and doing nothing. Examine verified offers, pricing, proof, distribution, onboarding, customer complaints and retention mechanisms. Identify where competitors genuinely outperform us and where evidence suggests an unmet need. Produce a positioning recommendation and three differentiation hypotheses. Do not mistake an absent feature for demonstrated demand.

**Business-type adaptation:** Compare the customer’s real alternative in that profile: another operator, DIY, another product, an incumbent workflow, a competing venue or an internal team.

<a id="p9"></a>

### P9: Design our offer ladder, bundles and upsells

Map verified products and customer needs into an entry offer, core purchase, bundle, repeat purchase and upsell path where appropriate. For each offer, document audience, value, contents, price status, margin assumptions, fulfillment requirements and terms. Separate existing offers from proposed tests. Identify which combinations simplify the buying decision and which add confusion. Do not invent prices, discounts, scarcity, renewal benefits or shipping commitments. Recommend the first offer test and the evidence needed to approve it.

**Business-type adaptation:** Use capacity and economics appropriate to the profile: crew hours, SKU margin/stock, recurring servicing cost, room/table slots, equipment utilization or practitioner/consultant time.

<a id="p10"></a>

### P10: Verify tracking and reconcile actual revenue

Audit tracking from the first customer action through the authoritative business outcome. Document event definitions, account ownership, stable identifiers, consent, attribution limits, deduplication and refund reconciliation. Show what currently fires, what reaches each destination and what is missing.

Apply the selected business profile’s revenue, consent and audience rules. Separate actual cash from credits, points or noncash activity; mixed transactions count actual cash only. Do not place raw email in analytics parameters or dataLayer. Deliver a test matrix and discrepancy report. A thank-you screen or analytics event alone is not proof of a sale.

**Business-type adaptation:** Use authoritative work-order, commerce, subscription, POS/reservation, rental or practice/contract records. Define taxes, fees, credits, refunds and revenue-recognition treatment rather than conflating all cash with margin.

<a id="p11"></a>

### P11: Build the prioritized growth backlog

Combine customer evidence, funnel friction, offer opportunities and system gaps into one ranked backlog. Compare expected impact, confidence, effort, dependencies, reversibility and downside. Make assumptions visible. Recommend one immediate task and the next three conditional tasks, each with an owner, deliverable and acceptance criteria. Explain what we should deliberately postpone. Prioritize fixing broken paths and measurement before increasing traffic to them.

**Business-type adaptation:** Score opportunities against the chosen outcome and the profile’s bottleneck. A full calendar, low stock or weak activation can make more traffic the wrong next step.

<a id="p12"></a>

### P12: Build the paid acquisition research and testing pack

Prepare a decision-ready paid acquisition pack for the designated operator. Connect priority personas, offers, messages, creative concepts and landing pages into a small set of distinct test hypotheses. Include account and platform eligibility, available targeting options, existing performance evidence, tracking readiness and economic break-even assumptions. Propose budget scenarios and stop conditions for the designated budget owner to approve. Prepare briefs and campaign structures without launching, changing spend or treating recommendations as approved budgets.

**Business-type adaptation:** Resolve the paid owner and applicable platform/industry restrictions. Break-even uses contribution per completed outcome and observed retention, not an unverified lifetime-value estimate.

<a id="p13"></a>

### P13: Build the creative production and review system

Turn the strongest customer insights into creative briefs with audience, problem, promise, proof, offer, CTA and destination. Develop variants that test meaningfully different hypotheses, not just colors or wording. Use the Visual Factory and Video Review workflows where appropriate. Check brand-specific copy, asset rights, quote accuracy, claims, mobile readability and exact rendered-version approval. Keep a registry connecting each creative to its hypothesis, version, destination and eventual results.

**Business-type adaptation:** Use profile-specific product proof: actual demonstrations, approved before/after work, onboarding flows, spaces/experiences, setups or professional expertise. Obtain rights and claim approval.

<a id="p14"></a>

### P14: Build the email conversion loop

Identify the most valuable eligible email segment and its specific journey friction. Review consent, suppression, delivery history and existing sequences before proposing changes. Design a focused lifecycle flow with triggers, message purposes, stopping conditions, destinations and conversion measurement. Draft the first messages in the client’s voice. Include unsubscribe, complaint and customer-quality guardrails. Preserve existing follow-up ownership and avoid duplicate outreach. Sending requires the appropriate authorization.

**Business-type adaptation:** Use valid lifecycle triggers: inquiry/quote follow-up, abandoned checkout, onboarding, renewal, reservation reminders, return dates or an agreed engagement milestone.

<a id="p15"></a>

### P15: Build the organic search and content loop

Research buyer questions with genuine commercial relevance and map them to the right offer or next action. Audit existing pages before creating more. Prioritize a focused content cluster based on demand evidence, differentiation and conversion opportunity. Produce briefs, source requirements, internal-link plans and CTAs. Identify pages to improve or consolidate. Measure qualified traffic and downstream outcomes, not rankings or article volume alone.

**Business-type adaptation:** Match intent and geography: local service areas, product comparisons, software problems, destination/venue searches, event requirements or professional service-fit questions.

<a id="p16"></a>

### P16: Build the social and community loop

Identify relevant adult audiences, communities and content formats. Study what earns useful attention and trust, then propose recurring formats grounded in real expertise, demonstrations or customer evidence. Connect each format to a journey stage and next action. Draft a small test batch with platform-specific execution and response ownership. Include a reuse plan across channels without copying the same post everywhere. Do not manufacture testimonials, personas or engagement.

**Business-type adaptation:** Choose channels from evidence about eligible buyers, not persona stereotypes. Separate buyer marketing from communications to children or other protected audiences.

<a id="p17"></a>

### P17: Build the press, partnership and sponsorship loop

Find timely stories and complementary partners where we have a defensible contribution and a relevant audience. Review existing meetings, introductions, partnerships and sponsorships before proposing new outreach. Verify claims, dates, rights and relationship status. Produce a ranked opportunity list with angle, audience fit, evidence required, proposed wording, owner and route to qualified demand. Distinguish awareness opportunities from measurable acquisition tests. Prepare drafts without implying unapproved relationships or commitments.

**Business-type adaptation:** Check profile-specific partner fit: complementary trades, retailers, integrations, local institutions, event venues or professional referral partners. Referral arrangements remain proposals until approved.

<a id="p18"></a>

### P18: Design and evaluate CRO experiments

Select one evidenced funnel bottleneck and propose a controlled test. Declare the hypothesis, eligible audience, baseline, comparison, primary outcome, guardrails, observation window and minimum evidence before launch. Use the existing experiment and outcome contracts. Explain how low traffic, seasonality and other changes affect interpretation. Define approval and rollback requirements. Classify results as supported, unsupported, invalid or inconclusive; do not call improved clicks a sales win without downstream evidence.

**Business-type adaptation:** Choose the outcome that matters for the profile; do not optimize qualified leads by destroying close quality, purchases by eroding margin, or trials by ignoring activation and retention.

<a id="p19"></a>

### P19: Build retention, repeat purchase and referral loops

Map the post-purchase experience, including onboarding, product use, fulfillment, support, repeat need and refunds. Find ways to improve customer value before asking for another purchase. Propose eligible repeat-purchase, upsell and referral tests with clear economics and terms. Identify natural milestones for follow-up and who owns each handoff. Do not invent incentives or pressure dissatisfied customers. Measure retained value, customer experience and incremental sales together.

**Business-type adaptation:** Use real repeat cycles: maintenance, replenishment, renewals, repeat visits, annual events, extensions or follow-on work. Not every business needs a subscription or upsell.

<a id="p20"></a>

### P20: Map the organization and operating loops

Create an org and responsibility diagram covering paid acquisition, nonpaid channels, creative, analytics, engineering, customer support, commercial decisions and approvals. Use existing people and responsibilities; flag missing owners rather than inventing staff. For each role, define its inputs, recurring loop, outputs, handoffs and contribution to the configured North Star. Make it clear who can prepare, approve, publish, spend and verify. Recommend a lightweight operating cadence that keeps decisions moving.

**Business-type adaptation:** Substitute actual roles, including dispatch/field teams, fulfillment, product/customer success, front-of-house, event operations or professional delivery. Avoid inventing a universal org chart.

<a id="p21"></a>

### P21: Run launch readiness and failure testing

Review the complete proposed launch from the first click through payment, delivery and support. Verify offers, links, mobile screens, eligibility, consent, tracking, payment outcomes, asset rights and recovery paths. Distinguish demos from production behavior. Produce a go/no-go checklist with evidence, blockers and accountable owners. Test in authorized environments without using real charges or customer communications as shortcuts. Keep unresolved blockers visible.

**Business-type adaptation:** Test the profile’s full promised outcome, not only checkout: work scheduled/completed, delivery, entitlement/access, reserved capacity, equipment logistics or professional engagement handoff.

<a id="p22"></a>

### P22: Run the weekly review and decide what happens next

Reconcile progress toward the configured goal using verified business outcomes. Review channel costs, refunds, margins, funnel changes and mature experiments. Explain what changed, what we learned and what remains uncertain. Recommend continue, change, stop or investigate for each meaningful test. Keep immature results open. Update the working file and end with the single highest-value next action, its owner and the evidence it should produce.

**Business-type adaptation:** Use cohort-appropriate maturity windows. Distinguish rapid purchase cycles from long sales cycles, seasonal bookings and recurring churn. Never force weekly causal conclusions.

<a id="p23"></a>

### P23: Turn proven work into reusable client setups

Extract the parts of this setup that genuinely generalize: discovery, journey mapping, evidence records, creative QA, experiment contracts, reporting and handoffs. Separate them from client-specific facts, offers, brand rules, revenue definitions, data and permissions. Reuse the existing tools rather than building another learning engine. Test the template against a second business with different needs. Keep client memory, credentials and outputs isolated; business labels alone are not security boundaries.

**Business-type adaptation:** Validate portability with a materially different business profile. Share schemas and approved deidentified lessons, not client records, credentials, identities or permissions.

## Client intelligence prompts

These six prompts extend the growth library with owner-reviewed knowledge contributed by a participating business. They are drafts for a client to run in its own authorized context, not a request to export all messages, customer identities, calendar records or private account data to a vendor.

The business owner reviews, redacts and approves what is shared, with whom and for what purpose before transmission. Keep private supporting evidence in that client’s isolated workspace. A source client identifier in the private ledger does not belong in a cross-client marketing bank.

<a id="c1"></a>

### C1: The Deep Extract

Act as a research analyst building a knowledge profile of [business] for [approved recipient/provider] to improve [agreed service or purpose]. Use only relevant information actually available and authorized for this task. Be specific; mark inferences INFERRED, estimates ESTIMATED and missing information UNKNOWN.

Produce: (1) the business in one page: offers, confirmed price points, team/capacity, seasonality, geography and how demand arrives; (2) up to five evidenced customer types, their situation when they inquire or buy, actual opening questions and observed reasons they proceed or stop; (3) missed or abandoned opportunities, when they occur, any verified value and separately labeled hypotheses about what happened next; (4) the owner’s reasons for buying or considering [service/category], including trigger, frustration, objections and required proof; (5) up to 30 actual customer phrases with source references, without inventing phrases to reach the number; (6) alternatives actually considered and the owner’s stated view; (7) conditions that would earn an unsolicited recommendation.

Return an owner-review draft and a separate proposed sharing version. Identify facts, identities or sensitive material to remove or obtain permission for before sharing. Do not transmit either version.

**Business-type adaptation:** Substitute [inquiry/interaction channel] for calls: phone/forms for services, cart/support for ecommerce, demo/trial/support for SaaS, reservations/walk-ins for hospitality, quote/date/logistics for rentals, permissioned intake for practices, and discovery/procurement for B2B. Missed interaction value is not booked revenue.

<a id="c2"></a>

### C2: Persona Forge

Using authorized evidence about [business] and its customers, build up to 10 specific end-customer persona hypotheses. For each, describe the buying/use situation, problem moment, desired outcome, consequence of delay, search questions, channels supported by evidence, reassurance or proof needed at first contact, and observed reasons for repeat use, a review or referral. Include age range only when relevant, appropriately sourced and necessary; do not infer sensitive traits or vulnerabilities.

Ground each persona in evidence. Label unsupported possibilities HYPOTHESIS rather than treating an invented persona as a real customer. Rank likely annual business value only when sufficient revenue/frequency evidence exists; otherwise give assumptions and confidence, not fabricated totals. Distinguish purchaser, user, beneficiary and gatekeeper.

**Business-type adaptation:** For B2B, model buying roles as well as use cases; for services, caller and decision-maker may differ; for gifts, events or hospitality, booker and recipient/guest may differ. These are this client’s end customers. They are not automatically the provider’s owner-buying ICP or available paid-targeting categories.

<a id="c3"></a>

### C3: Purchase Path Autopsy

Reconstruct how the owner or buying group purchases [business-service category], using only relevant, authorized evidence of actual purchases or serious considerations. For each example map the trigger, discovery source, alternatives, key objection, proof that mattered, elapsed time, decision-makers and final outcome. Separate direct statements from inference.

Then identify repeatable requirements a provider must meet, in sequence, to earn consideration and trust. Document what the buyer has explicitly rejected and where evidence is too thin to generalize. Produce a source-backed decision/objection map and practical sales guidance without exposing unrelated personal history. The owner must approve any provider-facing version.

**Business-type adaptation:** Local owner-led purchases may be fast and personal; B2B/SaaS purchases may require security, procurement, adoption and budget owners; practices may have professional/privacy obligations; rentals/hospitality may be constrained by dates and operations. Do not assume one person or one funnel decides all purchases.

<a id="c4"></a>

### C4: Nostalgia, Edge and Loop Scout

Research the relevant history, rituals, seasons, institutions and communities around [business type] in [market]. Find where familiarity or nostalgia genuinely matters to eligible customers, what evidence connects it to purchase behavior, what durable operating advantages exist, and what brings customers back or creates referrals.

For each finding include its source, confidence, limits and one concrete proposed message, post or service script. Distinguish actual customer language from newly drafted copy. Explain the mechanism, not just a slogan. Do not assume nostalgia affects willingness to pay without evidence, or use distress, shame or deceptive scarcity as a tactic.

**Business-type adaptation:** Use local/trade context for services, product culture and use rituals for commerce, workflow/community for SaaS, place/occasion for hospitality, event traditions for rentals, and trust/expertise or professional networks for practices and B2B. Omit nostalgia when it is not useful.

<a id="c5"></a>

### C5: Case Study Miner

Review the last [appropriate cohort window] of [business] records and find up to three supported stories where an interaction or delivery change plausibly affected a meaningful outcome. For each, provide the timeline, exact documented numbers, source references, key turning point, competing explanations and what remains unverified.

Draft a one-paragraph version the owner could review for public use. Label estimates ESTIMATED, distinguish association from causal evidence and do not invent testimonials or round up outcomes. Finish with the specific facts, quote permissions and public-use approval needed before publication. If there are fewer than three supported stories, report fewer.

**Business-type adaptation:** Use completed jobs for services, paid/delivered orders for commerce, activated/retained cohorts for SaaS, completed visits/stays for hospitality, fulfilled events/returns for rentals and permitted engagement outcomes for practices/B2B. Day 30 is a useful checkpoint only when outcomes have matured; do not force a 30-day result for a longer cycle.

<a id="c6"></a>

### C6: Approved Insight Aggregation

Fold a newly returned, owner-reviewed extract into the appropriate private evidence ledger and approved learning library. First verify the permitted recipient, purpose and scope of reuse. Keep client identities and raw evidence in the isolated client workspace. Promote only deidentified patterns approved for the proposed cross-client use; do not copy confidential histories, contact information or sensitive attributes.

Tag every claim with provenance, evidence type (direct record, owner-stated, inferred or estimated), date and confidence. Keep conflicting claims and their contexts instead of overwriting them. Distinguish the provider’s business-buyer ICP from a client’s end-customer personas. Store actual sourced quotes separately from paraphrases and proposed copy, and preserve quote/public-use permissions.

Update the relevant persona, language and objection maps only where evidence supports it. Finish with up to three justified messaging changes or tests; if the extract does not justify a change, say so. Avoid duplicate observations and do not treat repetition of one source as independent confirmation.

**Business-type adaptation:** Aggregate within comparable business models, outcomes and contexts first. A missed urgent service call, abandoned product cart and unactivated software trial are different events. Use profile-specific units and economics; transfer a lesson across profiles only with an explicit hypothesis and validation test.

## Client intelligence cadence

- **Onboarding:** client runs C1 in its authorized context; owner reviews/redacts/approves any shared extract.
- **Initial research:** use C2–C4 as evidence permits. Route useful material into P4–P9.
- **After outcomes mature:** C5, using a suitable cohort window; day 30 is an optional starting example, not a universal requirement.
- **Quarterly or material change:** refresh relevant evidence and retire stale assumptions.
- **On each approved return:** C6 validates scope, preserves provenance and proposes defensible updates.

This is the intended operating cadence, not a configured automation or authorization to contact customers.

## Connor’s documented working practices

These are working preferences reflected in Connor’s instructions and the existing marketing workflow, not invented quotations.

1. **Research before strategy.** Inspect the actual product, market and relevant evidence before building a recommendation. Verify capabilities against the canonical source rather than inventing a feature or a build requirement.
2. **Use real customer language and proof.** Preserve the distinction between quotes, interpretations and proposed copy. Support claims and case studies with sources and outcomes.
3. **Preserve the operator’s strengths.** Use prior work and examples to decide what to keep, amplify or automate instead of imposing generic tools over existing judgment.
4. **Make the customer path clear.** Pages, content and creative should lead coherently from the customer’s question through relevant proof to a useful next step, not read as disconnected blocks.
5. **Get the message and story right before polishing the surface.** Identify why the customer should care and what proof supports the promise before multiplying visual variations.
6. **Match the channel and speaker.** Learn the client’s approved voice from actual examples and corrections. Credit borrowed words to their real speaker rather than recasting them as a new company claim. Connor prefers direct writing without unrequested em dashes; do not force his personal voice on every client.
7. **Connect work to the outcome.** Prioritize genuine conversions and sound economics. Separate activity, preparation, release and verified results.
8. **Reuse what works.** Inspect the CMO harness and existing tools before creating another system. Make the smallest useful integration and preserve unrelated work.
9. **Be concrete about missing evidence.** State the gap, owner, next action and completion evidence rather than substituting confident generalities.
10. **Keep the work reusable without mixing clients.** Generalize the process and interfaces while retaining each business’s facts, brand, permissions and outcomes separately.

**Attribution:** These practices are adapted from the owner-approved source library and the harness contracts linked below. They are preferences and operating guidance, not verbatim quotations or evidence of client outcomes.

**Implementation defaults, not claimed personal quotations:** predeclared experiment metrics, independent outcome reconciliation, exact asset-version approval, privacy boundaries and client-isolated data are operational recommendations in this library and/or documented tool contracts. They are not presented as words Connor said.

## Illustrative examples

See [sanitized examples](examples.md). Examples are fictional and remain outside portable configuration. They do not establish connected accounts, approvals or measured results.

## Reusable tools and verified design limits

- [Kai CMO Harness](https://github.com/cgallic/kai-cmo-harness): discovery, channel playbooks, voice scope, quality/approval gates and outcome contracts. An installed capability is not proof of client feed integration.
- [Visual Factory Kit](https://github.com/cgallic/visual-factory-kit): versioned creative inputs, brand variants, deterministic rendering and QA. Remove or explicitly scope brand-specific defaults before reuse.
- [Video Review OS](https://github.com/cgallic/video-review-os): source/quote review, edits, renders and exact-version approval. A configured workspace alone is not a tenant authorization boundary.
- [Open Brane](https://github.com/cgallic/open-brane): evidence, revisions and project continuity. Its full-owner token and business filters require separate deployments across customer trust boundaries.

Relevant source contracts:
- [Customer voice scope](https://github.com/cgallic/kai-cmo-harness/blob/main/docs/system/customer-voice-engine.md)
- [Outcome contracts](https://github.com/cgallic/kai-cmo-harness/blob/main/docs/system/models-and-outcome-learning.md)
- [Evidence-backed funnel audits](https://github.com/cgallic/kai-cmo-harness/blob/main/harness/skills/kai-funnel-audit/SKILL.md)
- [Client dashboard isolation](https://github.com/cgallic/kai-cmo-harness/blob/main/harness/skills/kai-client-dashboard/SKILL.md)
- [Visual renderer](https://github.com/cgallic/visual-factory-kit/blob/main/visual_factory/render.py)
- [Open Brane customer trust boundary](https://github.com/cgallic/open-brane/blob/main/docs/CUSTOMER-HANDOFF.md)

## Systems to maintain

Keep these as practical sections or linked records, not separate tools unless needed:
1. Business profile: offers, audiences, claims, economics and constraints.
2. Access register: requested, connected, tested and approved uses.
3. Evidence library: source material, customer language, contradictions and dates.
4. ICP and messaging matrix: hypotheses, proof and validation status.
5. Journey/screen register: entrypoints, actions, failures, outcomes and owners.
6. Offer registry: contents, terms, economics, approvals and version.
7. Creative registry: briefs, rights, assets, reviewed versions and result links.
8. Experiment backlog: priorities, baselines, guardrails and decisions.
9. Outcome ledger: verified outcomes, reversals, costs and reconciled attribution.
10. Decision log: what changed, why, owner and next action.

## Standard report back

- Task and selected business profile:
- Decision or finding:
- Evidence, date and confidence:
- Deliverable:
- What was actually changed versus proposed:
- Effect on the configured goal:
- Unknowns or blockers:
- Owner and next action:
- Approval required:
- Working-file save status and verified reference:

## Acceptance criteria

The first proof is one complete, correctly measured customer path and one properly evaluated experiment. A prompt or plan is not execution evidence. Scale only after the relevant outcome and guardrails can be verified. Packaging in the CMO harness is a possible later implementation step, not completed by this page.

## Source and revision note

Adapted from the owner-approved Marketing Growth Prompt Library, version 2026-10-27. The [source receipt](source-receipt.json) records the verified body hash. Private links, customer examples and conversation identifiers were removed. The packaged copy generalizes repository inventory and keeps fictional examples separate. It is a local draft; no installation, campaigns, outreach, purchases, credentials, production settings or automations are established by these files.
