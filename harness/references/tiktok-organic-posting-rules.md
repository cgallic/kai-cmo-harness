# TikTok Organic Posting Rules

Last researched: 2026-07-20

Primary sources:
- Community Guidelines: https://www.tiktok.com/community-guidelines/en/
- How TikTok recommends content: https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content
- Account recommendation eligibility: https://www.tiktok.com/community-guidelines/en/for-you-feed-and-search/
- Content Posting API: https://developers.tiktok.com/doc/content-posting-api-get-started
- Direct Post API: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Query Creator Info: https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info
- TikTok Developer Changelog: https://developers.tiktok.com/doc/changelog
- Brand/product/service promotion: https://ads.tiktok.com/help/article/about-the-commercial-content-disclosure-setting-for-advertisers
- AI-generated content: https://www.tiktok.com/community-guidelines/en/integrity-authenticity/edited-media-and-ai-generated-content/
- Commercial music: https://ads.tiktok.com/help/article/commercial-music-library
- Content sharing guidelines: https://developers.tiktok.com/doc/content-sharing-guidelines
- TikTok ad policy change log: https://ads.tiktok.com/help/article/tiktok-ad-policy-change-log-2026

## Required Checks

- Confirm the content is allowed by TikTok Community Guidelines before scripting or scheduling.
- Check recommendation eligibility rules for content intended for For You distribution.
- Use the Content Posting API only with the required scopes, user authorization, verified domains/URL prefixes, required export-page UX, and current audit status.
- Use `video.publish` for direct posting and `video.upload` for inbox/review upload flows, based on the current TikTok Content Posting API guide.
- Disclose realistic AI-generated or altered content when required by platform tools or local law. TikTok's AI guidance says realistic AI-generated or meaningfully altered content must be labeled, can be auto-labeled from TikTok effects or C2PA credentials, and can still be removed if it misleads or uses prohibited likenesses. Source: https://www.tiktok.com/community-guidelines/en/integrity-authenticity/edited-media-and-ai-generated-content/ (accessed 2026-07-13).
- Use Content Disclosure settings for own-brand, third-party branded, affiliate, or incentivized posts. TikTok's July 2026 help flow says branded or promotional posts must turn on the disclosure setting and may be removed or restricted if the proper disclosure is missing. Source: https://ads.tiktok.com/help/article/about-the-commercial-content-disclosure-setting-for-advertisers (accessed 2026-07-13).
- If a Direct Post workflow marks content as branded/commercial, do not offer private-only visibility. TikTok's current content-sharing guidelines say branded-content disclosures can only be used with public/friends visibility, and `SELF_ONLY` should be disabled or automatically switched away when the commercial-content toggle is on. Source: https://developers.tiktok.com/doc/content-sharing-guidelines (accessed 2026-07-20).
- Use the Commercial Music Library or documented music rights for commercial/promotional posts. TikTok's music guidance says commercial content should use CML tracks, and off-library music requires confirming that all necessary rights are secured. Source: https://ads.tiktok.com/help/article/commercial-music-library (accessed 2026-07-13).
- For API publishing, fetch creator info before export/publish UI and respect privacy, comment, duet, stitch, and max-duration settings.
- Treat unaudited direct-post clients as private-only until TikTok audit lifts visibility restrictions. TikTok's current developer guidance says unaudited Direct Post clients are capped at 5 users per 24-hour window, all posting accounts must be private at post time, and content stays `SELF_ONLY` until audit approval. Source: https://developers.tiktok.com/doc/content-sharing-guidelines and https://developers.tiktok.com/doc/content-posting-api-get-started (accessed 2026-07-13).
- Post photos only through the documented photo endpoints and verified hosted URLs.
- Do not add brand logos, watermarks, promotional links, or promotional text overlays to content sent through Share Kit or Content Posting flows. TikTok's content-sharing guidelines treat that as a violation. Source: https://developers.tiktok.com/doc/content-sharing-guidelines (accessed 2026-07-13).
- Check TikTok Ads policy before Spark Ads, boosting, TikTok Shop promotion, or paid creator amplification.

## Organic Distribution Guidance

- TikTok ranking is interest-based and prediction-based. Watch behavior, interactions, content information, and account/device signals all matter.
- Build for retention, completion, rewatches, shares, and saves, but do not request fake or incentivized engagement.
- Avoid duplicate uploads, misleading captions, undisclosed commercial content, watermark reposting, low-quality clips, and content designed only to manipulate recommendation systems.
- Do not use multiple accounts or edited near-duplicates to bypass originality or duplicate-content systems.
- Treat comments/DMs as community interaction, not a bot funnel, unless the user opted in and the flow follows TikTok developer rules.
- Treat direct-post/photo support as opt-in capabilities, not a reason to skip creator review, privacy, or disclosure controls.
- Label hard numeric algorithm weights as heuristics unless the source is official and current.
- TikTok's official disclosure help says turning on the commercial disclosure setting does not by itself reduce feed distribution. Treat disclosure as a compliance requirement, not a reach tradeoff. Source: https://ads.tiktok.com/help/article/about-the-commercial-content-disclosure-setting-for-advertisers (accessed 2026-07-13).

## Harness Guardrails

- Load this file for TikTok organic posts, TikTok scripts, and TikTok Shop scripts.
- Remove any tactic that exists mainly to disguise duplicate content or evade recommender detection.
- Run ad/commercial checks before using influencer incentives, product links, Shop content, or paid amplification.
- Mark analytics trend breaks when TikTok or API measurement definitions change.
