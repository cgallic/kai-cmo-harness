# Social Platform Monitor Report

Last run: 2026-07-13 13:31 UTC

Checked: 90 sources
Changed: 12
New: 1
Errors: 6
Unchanged: 71

## Impact Cards

### [x] X Rules

- **What changed:** Previously broken source is reachable again
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot refreshed now that the source is reachable
- **Remaining risk:** Confirm the recovered page still matches the owner doc
- **Decision:** `auto_fix` (safe snapshot change)
- **Risk:** `low` · **Confidence:** high
- **Source:** https://help.x.com/en/rules-and-policies/x-rules
- **Owner doc:** `knowledge/channels/twitter-x.md`
- **Next step:** Spot-check `knowledge/channels/twitter-x.md`

### [x] X Automation Rules

- **What changed:** Source unreachable (The read operation timed out)
- **Why it matters:** automation rules may have changed; the scheduler or write actions may need updated guardrails (area: API automation)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.x.com/en/rules-and-policies/x-automation
- **Owner doc:** `harness/references/x-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `x_automation` or mark the registry entry deprecated

### [x] X Search Recommendations

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.x.com/en/resources/recommender-systems/search-recommendations
- **Owner doc:** `knowledge/channels/twitter-x.md`
- **Next step:** Find a canonical replacement URL for `x_search_recommendations` or mark the registry entry deprecated

### [tiktok] TikTok Content Sharing Guidelines

- **What changed:** Content hash changed (80cc9be73075 -> 1c27ab15f70d)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.tiktok.com/doc/content-sharing-guidelines
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Community Guidelines

- **What changed:** Content hash changed (b9c48a5bd852 -> 85b51b8a070f)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/9288567?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Fake Engagement Policy

- **What changed:** Content hash changed (247ceb5ec827 -> 7305543eef66)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `block` (guardrail: matched 'fake engagement')
- **Risk:** `critical` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/3399767?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube GenAI Disclosure

- **What changed:** Content hash changed (d3ea8790edb0 -> 339808ace247)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/14328491?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Advertiser-Friendly Guideline Updates

- **What changed:** Content hash changed (cad986d56aba -> 9d87038548e7)
- **Why it matters:** ad eligibility or prohibited-content rules may have changed; recheck ad copy gates before the next paid run (area: paid amplification)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/9725604?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [reddit] Reddit Public Content Policy

- **What changed:** Content hash changed (71ea727f8346 -> 6bb6c36c5f55)
- **Why it matters:** data-use or privacy terms may have changed; recheck what data automations may collect or store (area: privacy/data use)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.reddithelp.com/hc/en-us/articles/26410290525844-Public-Content-Policy
- **Monitor fetch URL:** https://redditinc.com/news/publishing-our-public-content-policy-and-introducing-a-new-community-for-researchers
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Review `harness/references/reddit-organic-posting-rules.md` against the live page and update it

### [threads] Threads Terms

- **What changed:** Source unreachable (HTTP Error 400: Bad Request)
- **Why it matters:** platform terms may have changed; recheck the owner doc for new prohibited behavior (area: community-specific rules)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.instagram.com/769983657850450
- **Owner doc:** `knowledge/channels/threads-organic.md`
- **Next step:** Find a canonical replacement URL for `threads_terms` or mark the registry entry deprecated

### [threads] Label AI Content on Threads

- **What changed:** Source unreachable (HTTP Error 400: Bad Request)
- **Why it matters:** AI/synthetic media disclosure rules may have changed; the pre-publish gate may need an AI/synthetic-media question (area: AI/synthetic media labels)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.instagram.com/407718162047721/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `threads_ai_labeling` or mark the registry entry deprecated

### [tiktok] TikTok Developer Changelog

- **What changed:** Content hash changed (93a2dd873951 -> 7e91e9c13bcd)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.tiktok.com/doc/changelog
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Recommendation System

- **What changed:** Content hash changed (8777827eeadb -> 816ecc4da9c4)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/16533387?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] YouTube Search and Discovery Tips

- **What changed:** Content hash changed (88b374a70d6a -> 1f1333c232ae)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/11914225?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] YouTube Paid Promotion Declarations

- **What changed:** Content hash changed (39d7f4d0d886 -> 550bcbc3097c)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/154235?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Spam Policy

- **What changed:** Content hash changed (2ce506e3d5e0 -> d0ea98b18659)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/2801973?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [snapchat] Is Stories content on Snapchat moderated?

- **What changed:** New source added to monitoring; baseline captured
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Baseline snapshot captured
- **Remaining risk:** No prior baseline to diff against yet
- **Decision:** `auto_fix` (safe snapshot change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://help.snapchat.com/hc/en-us/articles/7012263915412-Is-Stories-content-on-Snapchat-moderated
- **Owner doc:** `knowledge/channels/snapchat-organic.md`
- **Next step:** Confirm the owner doc reflects current guidance

### [reddit] Reddit Spam Policy

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `reddit_spam_policy` or mark the registry entry deprecated

### [reddit] Reddit Responsible Builder Policy

- **What changed:** Content hash changed (c0595394b21d -> dc8fd389cd86)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy
- **Monitor fetch URL:** https://old.reddit.com/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Review `harness/references/reddit-organic-posting-rules.md` against the live page and update it

### [reddit] Developer Platform & Accessing Reddit Data

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Find a canonical replacement URL for `reddit_developer_platform_accessing_data` or mark the registry entry deprecated

## Reviewed Sources

- `unchanged` [bluesky] Bluesky Rate Limits - https://docs.bsky.app/docs/advanced-guides/rate-limits
- `unchanged` [bluesky] Bluesky API Blog - https://docs.bsky.app/blog
- `unchanged` [bluesky] Bluesky Community Guidelines - https://bsky.social/about/support/community-guidelines
- `unchanged` [instagram] Instagram Platform Changelog - https://developers.facebook.com/docs/instagram-platform/changelog/
- `unchanged` [instagram] Instagram Content Publishing API - https://developers.facebook.com/docs/instagram-platform/content-publishing/
- `unchanged` [instagram] Instagram Media Publish Reference - https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- `unchanged` [instagram] Instagram Feed AI System - https://transparency.meta.com/features/explaining-ranking/ig-feed/
- `unchanged` [instagram] Instagram Recommendations and Originality - https://creators.instagram.com/blog/recommendations-and-originality
- `unchanged` [instagram] Instagram Algorithms and Ranking - https://creators.instagram.com/grow/algorithms-and-ranking
- `unchanged` [instagram] Instagram Reels Chaining - https://transparency.meta.com/features/explaining-ranking/ig-reels-chaining/
- `unchanged` [linkedin] LinkedIn Prohibited Software and Extensions - https://www.linkedin.com/help/linkedin/answer/a1341387
- `unchanged` [linkedin] LinkedIn Marketing API Recent Changes - https://learn.microsoft.com/en-us/linkedin/marketing/integrations/recent-changes?view=li-lms-2026-05
- `unchanged` [linkedin] LinkedIn API Terms of Use - https://www.linkedin.com/legal/l/api-terms-of-use
- `unchanged` [linkedin] LinkedIn Developer AI Policy - https://learn.microsoft.com/en-us/linkedin/marketing/developer-ai-policy?view=li-lms-2026-05
- `unchanged` [linkedin] LinkedIn Marketing API Terms - https://www.linkedin.com/legal/l/marketing-api-terms
- `unchanged` [linkedin] LinkedIn Posts API - https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-05
- `unchanged` [linkedin] LinkedIn Professional Community Policies - https://www.linkedin.com/help/linkedin/answer/a403270/linkedin-professional-community-policies
- `unchanged` [linkedin] LinkedIn Publishing Platform Guidelines - https://www.linkedin.com/help/linkedin/answer/a519782
- `unchanged` [linkedin] How LinkedIn Feed Ranks Content - https://www.linkedin.com/help/linkedin/answer/a9554004
- `unchanged` [linkedin] LinkedIn User Agreement - https://www.linkedin.com/legal/user-agreement
- `unchanged` [mastodon] Mastodon GitHub Releases - https://github.com/mastodon/mastodon/releases
- `unchanged` [mastodon] Mastodon API Guidelines - https://docs.joinmastodon.org/api/guidelines/
- `unchanged` [mastodon] Mastodon Posting Guide - https://docs.joinmastodon.org/user/posting/
- `unchanged` [mastodon] Mastodon Quote Posts Guide - https://docs.joinmastodon.org/user/quote-posts/
- `unchanged` [meta] Meta Advertising Standards - https://transparency.meta.com/policies/ad-standards/
- `unchanged` [meta] Graph API Changelog - https://developers.facebook.com/docs/graph-api/changelog/
- `unchanged` [meta] Meta Other Policies Hub - https://transparency.meta.com/policies/other-policies/
- `unchanged` [meta] Meta Developer Policies - https://developers.facebook.com/devpolicy/
- `unchanged` [meta] Meta Community Standards - https://transparency.meta.com/policies/community-standards/
- `unchanged` [meta] Facebook Feed AI System - https://transparency.meta.com/features/explaining-ranking/fb-feed/
- `unchanged` [meta] Meta Ranking Explainer Hub - https://transparency.meta.com/features/explaining-ranking/
- `unchanged` [pinterest] Pinterest GenAI Acceptable Use Guidelines - https://policy.pinterest.com/en/genai-acceptable-use-guidelines
- `unchanged` [pinterest] Pinterest Commercial and Branded Content Guidelines - https://policy.pinterest.com/en/commercial-and-branded-content-guidelines
- `unchanged` [pinterest] Pinterest API v5 - https://developers.pinterest.com/docs/api/v5/
- `unchanged` [pinterest] Pinterest Developer Guidelines - https://policy.pinterest.com/en-gb/developer-guidelines
- `unchanged` [pinterest] Pinterest Developer and API Terms - https://developers.pinterest.com/terms/
- `unchanged` [pinterest] Pinterest Community Guidelines - https://policy.pinterest.com/en/community-guidelines
- `unchanged` [pinterest] Pinterest Business Terms - https://business.pinterest.com/business-terms-of-service/
- `unchanged` [pinterest] Pinterest Terms of Service - https://policy.pinterest.com/en/terms-of-service
- `changed` [reddit] Reddit Public Content Policy - https://support.reddithelp.com/hc/en-us/articles/26410290525844-Public-Content-Policy
- `error` [reddit] Developer Platform & Accessing Reddit Data - https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data
- `unchanged` [reddit] Reddit Developer Terms - https://redditinc.com/policies/developer-terms
- `unchanged` [reddit] Reddit Developers Docs - https://developers.reddit.com/docs
- `changed` [reddit] Reddit Responsible Builder Policy - https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy
- `unchanged` [reddit] Reddit Responsible Builder Policy Announcement - https://www.reddit.com/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/
- `unchanged` [reddit] Reddit Content Policy - https://redditinc.com/policies/content-policy
- `unchanged` [reddit] Reddit Rules - https://redditinc.com/policies/reddit-rules
- `error` [reddit] Reddit Spam Policy - https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam
- `unchanged` [reddit] Reddit User Agreement - https://redditinc.com/policies/user-agreement
- `unchanged` [snapchat] Snap Commercial Content Policy - https://values.snap.com/policy/content-guidelines-recommendation-eligibility/recommendation-eligibility/commercial-content
- `unchanged` [snapchat] Snap for Developers - https://developers.snap.com/
- `unchanged` [snapchat] Snap Creator Monetization Policy - https://values.snap.com/policy/creator-monetization-policy
- `unchanged` [snapchat] Snapchat Community Guidelines - https://values.snap.com/policy/policy-community-guidelines
- `new` [snapchat] Is Stories content on Snapchat moderated? - https://help.snapchat.com/hc/en-us/articles/7012263915412-Is-Stories-content-on-Snapchat-moderated
- `unchanged` [snapchat] How Snap Ranks Content on Discover - https://help.snapchat.com/hc/en-us/articles/8961631424020-How-We-Rank-Content-on-Discover
- `unchanged` [snapchat] Snap Content Guidelines for Recommendation Eligibility - https://values.snap.com/policy/content-guidelines-recommendation-eligibility
- `unchanged` [snapchat] How Snap Ranks Content on Spotlight - https://help.snapchat.com/hc/en-us/articles/8961653169940-How-We-Rank-Content-on-Spotlight
- `unchanged` [snapchat] Snap Terms of Service - https://www.snap.com/terms
- `error` [threads] Label AI Content on Threads - https://help.instagram.com/407718162047721/
- `unchanged` [threads] Threads API Changelog - https://developers.facebook.com/docs/threads/changelog/
- `unchanged` [threads] Threads API Documentation - https://developers.facebook.com/docs/threads/
- `unchanged` [threads] Threads Feed AI System - https://transparency.meta.com/features/explaining-ranking/ig-threads-feed/
- `error` [threads] Threads Terms - https://help.instagram.com/769983657850450
- `unchanged` [tiktok] TikTok Ad Policy Change Log 2026 - https://ads.tiktok.com/help/article/tiktok-ad-policy-change-log-2026
- `unchanged` [tiktok] TikTok AI-Generated Content - https://www.tiktok.com/community-guidelines/en/integrity-authenticity/edited-media-and-ai-generated-content/
- `changed` [tiktok] TikTok Developer Changelog - https://developers.tiktok.com/doc/changelog
- `unchanged` [tiktok] TikTok Promoting a Brand, Product, or Service - https://ads.tiktok.com/help/article/about-the-commercial-content-disclosure-setting-for-advertisers
- `unchanged` [tiktok] Commercial Use of Music on TikTok - https://ads.tiktok.com/help/article/commercial-music-library
- `unchanged` [tiktok] TikTok Content Posting API - https://developers.tiktok.com/doc/content-posting-api-get-started
- `changed` [tiktok] TikTok Content Sharing Guidelines - https://developers.tiktok.com/doc/content-sharing-guidelines
- `unchanged` [tiktok] TikTok Community Guidelines - https://www.tiktok.com/community-guidelines/en/
- `unchanged` [tiktok] Why Is My Account Not Being Recommended? - https://www.tiktok.com/community-guidelines/en/for-you-feed-and-search/
- `unchanged` [tiktok] How TikTok Recommends Content - https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content
- `error` [x] X Automation Rules - https://help.x.com/en/rules-and-policies/x-automation
- `unchanged` [x] X API Changelog - https://docs.x.com/changelog
- `unchanged` [x] X Developer Policy - https://docs.x.com/developer-terms/policy
- `unchanged` [x] X Rules - https://help.x.com/en/rules-and-policies/x-rules
- `error` [x] X Search Recommendations - https://help.x.com/en/resources/recommender-systems/search-recommendations
- `changed` [youtube] YouTube Advertiser-Friendly Guideline Updates - https://support.google.com/youtube/answer/9725604?hl=en
- `unchanged` [youtube] YouTube Data API Revision History - https://developers.google.com/youtube/v3/revision_history
- `changed` [youtube] YouTube Paid Promotion Declarations - https://support.google.com/youtube/answer/154235?hl=en
- `unchanged` [youtube] YouTube API Services Terms of Service - https://developers.google.com/youtube/terms/api-services-terms-of-service
- `unchanged` [youtube] YouTube API Services Developer Policies - https://developers.google.com/youtube/terms/developer-policies
- `changed` [youtube] YouTube Community Guidelines - https://support.google.com/youtube/answer/9288567?hl=en
- `changed` [youtube] YouTube Fake Engagement Policy - https://support.google.com/youtube/answer/3399767?hl=en
- `changed` [youtube] YouTube GenAI Disclosure - https://support.google.com/youtube/answer/14328491?hl=en
- `changed` [youtube] YouTube Spam Policy - https://support.google.com/youtube/answer/2801973?hl=en
- `changed` [youtube] YouTube Recommendation System - https://support.google.com/youtube/answer/16533387?hl=en
- `unchanged` [youtube] Recommendations on YouTube - https://www.youtube.com/howyoutubeworks/recommendations/
- `changed` [youtube] YouTube Search and Discovery Tips - https://support.google.com/youtube/answer/11914225?hl=en
