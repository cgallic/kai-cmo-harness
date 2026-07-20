# LinkedIn Organic Posting Rules

Last researched: 2026-07-20

Primary sources:
- LinkedIn User Agreement: https://www.linkedin.com/legal/user-agreement
- LinkedIn API Terms of Use: https://www.linkedin.com/legal/l/api-terms-of-use
- LinkedIn Marketing API Terms: https://www.linkedin.com/legal/l/marketing-api-terms
- LinkedIn Developer AI Policy: https://learn.microsoft.com/en-us/linkedin/marketing/developer-ai-policy?view=li-lms-2026-05
- LinkedIn Professional Community Policies: https://www.linkedin.com/help/linkedin/answer/a403270/linkedin-professional-community-policies
- How LinkedIn feed ranks content: https://www.linkedin.com/help/linkedin/answer/a9554004
- Prohibited software and extensions: https://www.linkedin.com/help/linkedin/answer/a1341387
- LinkedIn Posts API: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-05
- Marketing API recent changes: https://learn.microsoft.com/en-us/linkedin/marketing/integrations/recent-changes?view=li-lms-2026-05
- LinkedIn product catalog: https://developer.linkedin.com/product-catalog

## Required Checks

- Use LinkedIn member, page, and company data only through approved products and permissions.
- Do not scrape, enrich, resell, or combine LinkedIn data outside approved API terms.
- Review Developer AI Policy before using LinkedIn organic content, comments, profile data, or messages in AI workflows. LinkedIn's current policy says Marketing API page/member data generally cannot be used to train AI or supplied as prompt/input except where the policy expressly allows it, and AI features using LinkedIn data must disclose that they are AI-powered, explain their operation, disclose if end-user data is used to further train/improve the system or shared with third parties, and warn that outputs may be inaccurate. Source: https://learn.microsoft.com/en-us/linkedin/marketing/developer-ai-policy?view=li-lms-2026-05 (accessed 2026-07-20).
- Keep authorization from the relevant Page/admin/account manager for scheduling, moderation, reporting, or publishing.
- Pin LinkedIn API workflows to a currently supported Marketing version and review the recent-changes page before publish/reporting runs. LinkedIn's current recent-changes page warns that Marketing version 202507 is sunset, continues the rolling monthly sunset schedule, and keeps version-gated behavior on Marketing/community APIs. Source: https://learn.microsoft.com/en-us/linkedin/marketing/integrations/recent-changes?view=li-lms-2026-05 (accessed 2026-07-20).
- Check LinkedIn Ads policy before boosting or sponsoring organic posts.
- Treat third-party reach multipliers, timing claims, and algorithm weights as benchmarks only unless LinkedIn documents them directly.
- When posting through the Posts API, keep the `Linkedin-Version` header pinned and validate that the workflow still supports the current post schema before scheduling. LinkedIn's current Posts API examples remain versioned and rely on explicit `lifecycleState` and distribution fields, so stale version pins can break otherwise-valid publish flows. Source: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-05 (accessed 2026-07-20).
- LinkedIn's official feed-ranking help says feed visibility uses hundreds of signals from post context, profile/network/activity, and does not use demographic fields such as age, race, or gender as visibility signals. Source: https://www.linkedin.com/help/linkedin/answer/a9554004 (accessed 2026-07-06).

## Organic Distribution Guidance

- LinkedIn rewards professional relevance, conversation quality, dwell, topical fit, and authentic network engagement.
- Use native documents, images, video, text posts, newsletters, and articles based on the content goal.
- Avoid pods, coordinated engagement, fake employee advocacy, engagement bait, irrelevant tagging, and copy-paste employee posts.
- Put external links where the strategy calls for them, but do not hide material claims or required disclosures.
- Keep AI-assisted content edited into a specific human POV with evidence, examples, and accountable claims.
- Do not use browser extensions or agents to automate profile views, connection requests, likes, comments, shares, scraping, member-data enrichment, or any tool that modifies LinkedIn's UI or manipulates feed ranking. Source: https://www.linkedin.com/help/linkedin/answer/a1341387 (accessed 2026-07-06).

## Harness Guardrails

- Load this file for LinkedIn posts, newsletters, articles, employee advocacy, and community management.
- For employee advocacy, provide talking points and proof, not mandatory identical posts.
- For AI-generated drafts, require a human owner and claim substantiation before posting.
