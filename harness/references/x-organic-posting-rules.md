# X Organic Posting, Automation, and Promotion Guardrails

> **Use when**: Scheduling X posts, generating X replies, setting up automation, planning contests, using creator/affiliate disclosures, or preparing organic posts that may later become promoted posts.

Last updated: 2026-07-20

Ruleset ID: `x_twitter_posting_automation_2026_06_17`

Primary sources:
- X Automation Rules: https://help.x.com/en/rules-and-policies/x-automation
- X Developer Policy: https://docs.x.com/developer-terms/policy
- X Restricted API Uses: https://docs.x.com/developer-terms/restricted-use-cases
- X Authenticity Policy: https://help.x.com/en/rules-and-policies/authenticity
- X Rules: https://help.x.com/en/rules-and-policies/x-rules
- X Professional Account Policy: https://help.x.com/en/rules-and-policies/professional-account-policy
- X Promotions Guidelines: https://help.x.com/en/rules-and-policies/x-contest-rules
- X Ads Policies: https://business.x.com/en/help/ads-policies
- X Enforcement Options: https://help.x.com/en/rules-and-policies/enforcement-options
- X Community Notes: https://help.x.com/en/using-x/community-notes
- X Civic Integrity Policy: https://help.x.com/en/rules-and-policies/election-integrity-policy
- X Creator Revenue Sharing: https://help.x.com/en/using-x/creator-revenue-sharing
- FTC Disclosures 101: https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers
- FTC Endorsement Guides FAQ: https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking

---

## Required Preflight Fields

Every X publishing workflow must set:

- `mode`: `organic | automation | promoted_candidate | ad`
- `account_type`: `brand | founder | professional | bot | parody_commentary_fan | support`
- `consent_source`: where express consent for automated action came from
- `opt_out_path`: how recipients can stop automated replies, mentions, or DMs
- `claim_sources`: sources for numbers, outcomes, rankings, savings, earnings, health claims, or timelines
- `regulated_category`: `none | political | civic | finance | crypto | health | gambling | alcohol | tobacco | cannabis | weight_loss | adult | sensitive_event | other`
- `sensitive_media`: `none | adult | violent | graphic | other`
- `contest_or_incentive`: boolean
- `affiliate_or_creator_relationship`: boolean
- `ai_generated_or_manipulated_media`: boolean
- `may_promote`: boolean
- `account_capability`: `standard | premium | premium_plus | premium_business | verified_org | unknown`
- `long_form_surface`: `none | longer_post | article | space`
- `community_note_risk`: `none | possible | high`
- `api_use_case_id`: approved developer use case or `manual_only`
- `api_app_environment`: `none | development | staging | production`

---

## Must

- Use the official X API or approved developer path for automation.
- Keep the approved API use case current.
- Notify X and receive approval before materially changing an API use case.
- Get express consent before posting, following, unfollowing, DMing, deleting, or adding hashtags on a user's behalf.
- Show exactly what will be published before posting through a user-authorized workflow.
- Honor opt-outs immediately for automated replies, mentions, and DMs.
- Clearly identify API-based bot accounts and who is responsible for them.
- If an API-published organic or creator post is a paid partnership, set `paid_partnership=true` so X applies the paid-promotion label. Source: https://docs.x.com/changelog (accessed 2026-07-13).
- Keep development, staging, and production API applications clearly identified and do not use development or staging apps for production.
- Keep API keys and access credentials private.
- Respect API rate limits and plan limits. Do not circumvent limits.
- For X search/listening automations, assume the v2 search endpoints now use X's core search index. X's May 4, 2026 API changelog says keyword-based search no longer returns reposts and adds `min_likes:`, `min_replies:`, and `min_reposts:` precision operators. Source: https://docs.x.com/changelog (accessed 2026-07-20).
- Preserve X Content integrity when displaying posts through the API, and remove unavailable content promptly when required.
- Keep professional profiles authentic, complete, and clearly identified.
- Label sensitive, adult, or violent media when allowed.
- Keep adult content out of highly visible profile surfaces.
- For contests, publish rules that discourage duplicate posts, disqualify multiple-account entry, cap repeat entries, require relevant hashtags only when needed, and comply with law.
- Disclose paid, incentivized, affiliate, creator, whitelisted, contest-entry, or sponsored relationships with clear labels such as `#ad`, `#sponsored`, or `#contest` near the claim.

---

## Block Publish

Block publishing when any condition is true:

- No consent exists for an automated action.
- The post is duplicate or substantially similar across one or many accounts.
- Automation targets trends or attempts to influence trends.
- The workflow sends unsolicited bulk automated replies, mentions, or DMs.
- The workflow uses keyword-search auto-replies without opt-in.
- The workflow uses automated likes, automated reply hiding, aggressive automated reposting, follow churn, list adds, or collection adds.
- The post uses misleading links, deceptive redirects, phishing, malicious URLs, fraudulent discounts, money-flipping, scams, or social engineering.
- The account or post creates impersonation or confusing affiliation risk.
- The post uses deceptive synthetic, manipulated, or out-of-context media likely to cause harm, public confusion, or safety impact.
- Sensitive media is present but not labeled.
- A quantitative or outcome claim has no source.
- The post includes third-party pre-roll ads or sponsorship graphics inside video content without X approval.
- X API or X Content is being used for off-platform ad targeting, sensitive profiling, surveillance, credit/insurance risk analysis, facial recognition, or foundation/frontier model training outside allowed terms.
- The workflow uses the X API to benchmark, commercially compare, or publicly disclose X platform performance, aggregate X usage, aggregate X posting volume, or spam/security findings without permission.
- The API use case has drifted from the approved description.
- A white-label or multi-client app is being operated under one substantially similar API use case without approval.

---

## Human Review Required

Route to review before posting or scheduling:

- AI-powered automated reply bots
- brand auto-response campaigns using automated mentions or replies
- paid promotion candidates
- contests, giveaways, incentives, affiliate, creator, or whitelisted posts
- political or civic content
- finance, crypto, health, gambling, alcohol, tobacco, cannabis, weight-loss, adult, or sensitive-event content
- claims with numbers, outcomes, rankings, savings, earnings, health benefits, or "results in X days"
- AI-generated or manipulated media that could be mistaken for real events or people
- Community Note risk where a claim is likely to be disputed, lacks context, or compares competitors
- Creator monetization accounts posting AI-generated armed-conflict video or sensitive event content
- Spaces that will be recorded, clipped, or reused in paid/owned content

---

## Community Notes and Enforcement

Community Notes are a public context layer, not a direct rule-enforcement tool. X says helpful Community Notes do not by themselves trigger removals, labels, or reduced distribution.

Still, the harness must treat a Community Note as a trust event:

- pause promotion or reposting of the same claim
- review the source chain
- correct the post, reply with context, or retire the claim
- log the note as a claim-quality issue

Civic Integrity labels are different. X says civic labels can restrict visibility, remove posts from timelines, limit engagement options, and downrank replies. Route civic content to review before posting.

---

## Ads and Promoted Posts

Organic-safe does not mean ad-safe.

- X Ads policies apply to paid posts, trends, and accounts.
- Selecting an organic post for promotion triggers ad review.
- If a promoted post is disapproved, it cannot run as an ad, even if the organic post remains visible.
- Advertiser account profile, handle, bio URL, header, and promoted content all matter.
- Ads eligibility can require a verified account, public posts, compliant profile/header images, and a functional live bio URL that represents the brand and promoted product.
- Serious X Rules or Terms violations can affect both ads access and account standing.
- Posts created through X Ads Composer may show `X for Advertisers`; paid content should still be identified by the promoted/ad label in ad surfaces.

Before promotion, run the ad policy reference in `harness/references/x-ads-policy-reference.md`.

---

## Long-Form and Live Surface Checks

Before using Premium-only or live surfaces:

- Confirm the account has the needed capability for longer posts or Articles.
- For Articles, confirm the piece is worth native long-form treatment and has a short distribution post.
- If publishing Articles through the API, require the same capability check and human review as manual Article publishing. X's changelog added draft and publish Article endpoints on June 11, 2026. Source: https://docs.x.com/changelog (accessed 2026-07-13).
- For Spaces, confirm whether recording is enabled, whether speakers understand clipping/recording, and how recordings or clips will be reused.
- For creator monetization accounts, confirm content follows monetization standards and avoids undisclosed AI-generated armed-conflict video.

---

## Default Harness Decision

Use this decision order:

1. Block if consent, duplicate, impersonation, automation, link safety, sensitive media, or claim support fails.
2. Route to review if the post touches automation, paid promotion, contests, incentives, regulated categories, or sensitive events.
3. Publish or schedule only when the post passes the channel guide, this reference, and the social-post contract.

If an official X Help Center rules page returns `403` in automation, reopen it in a browser before changing guidance. Treat that as a source-reachability issue first, not automatic evidence that the policy itself changed.
