# YouTube Organic Posting Rules

Last researched: 2026-08-03

Primary sources:
- Community Guidelines: https://support.google.com/youtube/answer/9288567?hl=en
- Recommendations on YouTube: https://www.youtube.com/howyoutubeworks/recommendations/
- Fake engagement policy: https://support.google.com/youtube/answer/3399767?hl=en
- Copyright on YouTube: https://support.google.com/youtube/answer/2797466?hl=en
- Spam policy: https://support.google.com/youtube/answer/2801973?hl=en
- External links policy: https://support.google.com/youtube/answer/9054257?hl=en
- Paid promotion declarations: https://support.google.com/youtube/answer/154235?hl=en
- GenAI disclosure: https://support.google.com/youtube/answer/14328491?hl=en
- Upload video settings: https://support.google.com/youtube/answer/57407?hl=en
- YouTube API Services Terms: https://developers.google.com/youtube/terms/api-services-terms-of-service
- YouTube API Developer Policies: https://developers.google.com/youtube/terms/developer-policies
- YouTube Data API revision history: https://developers.google.com/youtube/v3/revision_history
- Advertiser-friendly guideline updates: https://support.google.com/youtube/answer/9725604?hl=en

## Required Checks

- Check Community Guidelines for every video, Short, live stream, community post, and comment strategy.
- Check fake engagement rules before any view, like, comment, share, subscriber, giveaway, or engagement CTA.
- Disclose realistic AI-generated or altered content during upload when the platform requires it, especially when a real person appears to say/do something they did not, a real event/place is altered, or a realistic event is shown that never happened. YouTube's current GenAI help also says disclosure itself does not reduce audience or monetization eligibility, repeated non-disclosure can trigger manual labels, removals, or YouTube Partner Program suspension, and YouTube may auto-label content from YouTube GenAI tools, C2PA metadata, or internal AI detection. Source: https://support.google.com/youtube/answer/14328491?hl=en (accessed 2026-07-27).
- Clear music, clip, image, and footage rights before upload. YouTube's copyright help still points to permission, copyright exceptions, Creative Commons, Audio Library, and Creator Music as the main safe-use paths, while warning that none of them guarantees avoiding a Content ID claim or copyright strike. Source: https://support.google.com/youtube/answer/2797466?hl=en (accessed 2026-08-03).
- Declare paid promotion, sponsorship, endorsement, or product placement in upload settings when required, including Shorts, live streams, descriptions, comments, and other YouTube features tied to the promotion.
- Set made-for-kids, age restriction, remixing, license, caption, and altered-content fields intentionally.
- Use YouTube API only with compliant user consent, privacy policy, Terms link, data deletion, and quota/rate handling. The July 7, 2026 revision history added `brandPartner` support to `videos.insert`, `videos.update`, and `videos.list` for creator-initiated brand partner access, and the same revision-history page keeps `status.containsSyntheticMedia` as the altered/synthetic disclosure field for API uploads. Source: https://developers.google.com/youtube/v3/revision_history (accessed 2026-07-13).
- Monitor quota by method, not as one flat bucket. As of June 1, 2026, `videos.insert` and `search.list` have their own quota buckets, and June 3, 2026 added `videos.batchGetStats` with a separate quota bucket. Source: https://developers.google.com/youtube/v3/revision_history (accessed 2026-07-13).
- Check advertiser-friendly updates before monetized videos or paid amplification. The current help page still surfaces March 2026 shocking-content clarification and February 2026 firearms/magazine eligibility changes, so monetization assumptions can move independently of Community Guidelines. Source: https://support.google.com/youtube/answer/9725604?hl=en (accessed 2026-07-13).

## Organic Distribution Guidance

- YouTube recommendations appear in Watch Next, Search, home surfaces, Shorts, and news/shelf surfaces.
- Search ranking uses relevance, engagement, and quality with different weights by query type.
- Watch history, broader viewer trends, current video topics, quality, and user controls affect recommendations.
- YouTube's current creator-facing recommendation page explicitly frames the system around helping each viewer find videos they want to watch and maximizing long-term viewer satisfaction. Optimize for audience fit first, not “beating the algorithm.” Source: https://support.google.com/youtube/answer/16533387?hl=en (accessed 2026-07-13).
- Optimize for honest click-through, viewer satisfaction, retention, session fit, and topic clarity.
- Avoid artificial metric inflation, engagement incentives, misleading metadata, reused/mass-produced content, and clickbait that disappoints viewers. That includes view exchanges, subscriber swaps, or other "sub4sub" mechanics. YouTube's fake-engagement page also now explicitly folds deceptive AI voice/likeness impersonation into the same enforcement surface when it misleads viewers about who owns or authorizes a channel. Source: https://support.google.com/youtube/answer/3399767?hl=en (accessed 2026-07-13).
- Treat spam policy scope as broader than public uploads only. YouTube's current spam page says the policy also applies to unlisted/private content, comments, links, posts, thumbnails, and coordinated channel networks. Source: https://support.google.com/youtube/answer/2801973?hl=en (accessed 2026-07-13).
- Treat tags as a minor discovery input, mainly useful for misspellings, not as a ranking lever.
- Check topic interest, competition, and seasonality before assuming a reach drop is a creative failure.
- Mark analytics trend breaks when YouTube changes Shorts view counting or API metric definitions.

## Harness Guardrails

- Load this file for YouTube videos, Shorts, community posts, podcast clips, and YouTube repurposing.
- Treat “subscribe/comment/like” CTAs as optional and never as an incentive.
- Do not script realistic AI likeness, civic, medical, financial, or youth-sensitive content without disclosure and policy review.
- Do not use scraped reposting, repetitive AI batches with minimal changes, or technical manipulation to bypass duplicate/spam systems.
- Re-check advertiser-friendly guidance for shocking content, firearms, controversial issues, or child-safety-adjacent material before monetized or paid-amplified publishing.
