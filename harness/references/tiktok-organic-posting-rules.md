# TikTok Organic Posting Rules

Last researched: 2026-06-29

Primary sources:
- Community Guidelines: https://support.tiktok.com/en/safety-hc/account-and-user-safety/community-guidelines
- How TikTok recommends content: https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content
- Account recommendation eligibility: https://support.tiktok.com/en/safety-hc/account-and-user-safety/why-is-my-account-not-being-recommended
- Content Posting API: https://developers.tiktok.com/doc/content-posting-api-get-started
- Direct Post API: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Query Creator Info: https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info
- TikTok Developer Changelog: https://developers.tiktok.com/doc/changelog
- Brand/product/service promotion: https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/promoting-a-brand-product-or-service
- AI-generated content: https://support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content
- Commercial music: https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/commercial-use-of-music-on-tiktok
- Content sharing guidelines: https://developers.tiktok.com/doc/content-sharing-guidelines
- TikTok ad policy change log: https://ads.tiktok.com/help/article/tiktok-ad-policy-change-log-2026

## Required Checks

- Confirm the content is allowed by TikTok Community Guidelines before scripting or scheduling.
- Check recommendation eligibility rules for content intended for For You distribution.
- Use the Content Posting API only with the required scopes, user authorization, verified domains/URL prefixes, required export-page UX, and current audit status.
- Use `video.publish` for direct posting and `video.upload` for inbox/review upload flows, based on the current TikTok Content Posting API guide.
- Disclose realistic AI-generated or altered content when required by platform tools or local law.
- Use Content Disclosure settings for own-brand, third-party branded, affiliate, or incentivized posts.
- Use the Commercial Music Library or documented music rights for commercial/promotional posts.
- For API publishing, fetch creator info before export/publish UI and respect privacy, comment, duet, stitch, and max-duration settings.
- Treat unaudited direct-post clients as private-only until TikTok audit lifts visibility restrictions.
- Post photos only through the documented photo endpoints and verified hosted URLs.
- Do not add brand logos, watermarks, promotional links, or promotional text overlays to content sent through Share Kit or Content Posting flows. TikTok's content-sharing guidelines treat that as a violation. Source: https://developers.tiktok.com/doc/content-sharing-guidelines (accessed 2026-06-29).
- Check TikTok Ads policy before Spark Ads, boosting, TikTok Shop promotion, or paid creator amplification.

## Organic Distribution Guidance

- TikTok ranking is interest-based and prediction-based. Watch behavior, interactions, content information, and account/device signals all matter.
- Build for retention, completion, rewatches, shares, and saves, but do not request fake or incentivized engagement.
- Avoid duplicate uploads, misleading captions, undisclosed commercial content, watermark reposting, low-quality clips, and content designed only to manipulate recommendation systems.
- Do not use multiple accounts or edited near-duplicates to bypass originality or duplicate-content systems.
- Treat comments/DMs as community interaction, not a bot funnel, unless the user opted in and the flow follows TikTok developer rules.
- Treat direct-post/photo support as opt-in capabilities, not a reason to skip creator review, privacy, or disclosure controls.
- Label hard numeric algorithm weights as heuristics unless the source is official and current.

## Harness Guardrails

- Load this file for TikTok organic posts, TikTok scripts, and TikTok Shop scripts.
- Remove any tactic that exists mainly to disguise duplicate content or evade recommender detection.
- Run ad/commercial checks before using influencer incentives, product links, Shop content, or paid amplification.
- Mark analytics trend breaks when TikTok or API measurement definitions change.
