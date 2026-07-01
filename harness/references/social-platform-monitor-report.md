# Social Platform Monitor Report

Last run: 2026-07-01 12:20 UTC

Checked: 88 sources
Changed: 26
New: 0
Errors: 7
Unchanged: 55

## Impact Cards

### [x] X Rules

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.x.com/en/rules-and-policies/x-rules
- **Owner doc:** `knowledge/channels/twitter-x.md`
- **Next step:** Find a canonical replacement URL for `x_rules` or mark the registry entry deprecated

### [x] X Automation Rules

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
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

### [tiktok] How TikTok Recommends Content

- **What changed:** Content hash changed (11b8b994ed84 -> 4b7fa6feed35)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content
- **Owner doc:** `knowledge/channels/tiktok-algorithm.md`
- **Next step:** Review `knowledge/channels/tiktok-algorithm.md` against the live page and update it

### [tiktok] TikTok Content Posting API

- **What changed:** Content hash changed (b52f2b1ad2f4 -> 9ad617ae3d9a)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.tiktok.com/doc/content-posting-api-get-started
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Content Sharing Guidelines

- **What changed:** Content hash changed (9e082ae2297d -> 44bb942c0cc6)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.tiktok.com/doc/content-sharing-guidelines
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Community Guidelines

- **What changed:** Content hash changed (2a258c5148bd -> a7cc5b2b29a4)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/9288567?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Fake Engagement Policy

- **What changed:** Source unreachable (The read operation timed out)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `block` (guardrail: matched 'fake engagement')
- **Risk:** `critical` · **Confidence:** high
- **Source:** https://support.google.com/youtube/answer/3399767?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `youtube_fake_engagement` or mark the registry entry deprecated

### [youtube] YouTube GenAI Disclosure

- **What changed:** Content hash changed (7a175ad431e9 -> 4d6fcedfb506)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/14328491?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Advertiser-Friendly Guideline Updates

- **What changed:** Content hash changed (8ee91100174d -> 1b03246e49b7)
- **Why it matters:** ad eligibility or prohibited-content rules may have changed; recheck ad copy gates before the next paid run (area: paid amplification)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/9725604?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Community Guidelines

- **What changed:** Content hash changed (e4bcb9cb3cee -> c1fd1879b1c5)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/community-guidelines
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest GenAI Acceptable Use Guidelines

- **What changed:** Content hash changed (ddde3b5fed5f -> 4689b10b2866)
- **Why it matters:** AI/synthetic media disclosure rules may have changed; the pre-publish gate may need an AI/synthetic-media question (area: AI/synthetic media labels)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/genai-acceptable-use-guidelines
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [reddit] Reddit Responsible Builder Policy Announcement

- **What changed:** Source unreachable (HTTP Error 403: Blocked)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://www.reddit.com/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `reddit_responsible_builder_policy` or mark the registry entry deprecated

### [linkedin] LinkedIn Professional Community Policies

- **What changed:** Content hash changed (fddda86fb916 -> 20413d76a22b)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a403270/linkedin-professional-community-policies
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [linkedin] How LinkedIn Feed Ranks Content

- **What changed:** Content hash changed (79a7cfaef58f -> ba4641c791c4)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a9554004
- **Owner doc:** `knowledge/channels/linkedin-organic.md`
- **Next step:** Review `knowledge/channels/linkedin-organic.md` against the live page and update it

### [linkedin] LinkedIn Publishing Platform Guidelines

- **What changed:** Content hash changed (1c200efa98ec -> 190bebfb564a)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a519782
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [linkedin] LinkedIn Prohibited Software and Extensions

- **What changed:** Content hash changed (5989964333b2 -> 452ebb03b790)
- **Why it matters:** automation rules may have changed; the scheduler or write actions may need updated guardrails (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a1341387
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Review `harness/references/social-automation-rules.md` against the live page and update it

### [instagram] Instagram Content Publishing API

- **What changed:** Content hash changed (e818fb09af63 -> 4507fc7b8c62)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.facebook.com/docs/instagram-platform/content-publishing/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [instagram] Instagram Media Publish Reference

- **What changed:** Content hash changed (9bf19c9ef19d -> 79df4ee02d0b)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [instagram] Instagram Platform Changelog

- **What changed:** Content hash changed (995426d940a7 -> b86154172226)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.facebook.com/docs/instagram-platform/changelog/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Promoting a Brand, Product, or Service

- **What changed:** Content hash changed (8b14aa07f002 -> c65bfbfd08dd)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/promoting-a-brand-product-or-service
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok AI-Generated Content

- **What changed:** Content hash changed (efc66004db41 -> 12700beccdc3)
- **Why it matters:** AI/synthetic media disclosure rules may have changed; the pre-publish gate may need an AI/synthetic-media question (area: AI/synthetic media labels)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] Commercial Use of Music on TikTok

- **What changed:** Content hash changed (e24071b694c5 -> e6d060004e5f)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/commercial-use-of-music-on-tiktok
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Developer Changelog

- **What changed:** Content hash changed (d9e3b336ec5a -> 28f14aac7035)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.tiktok.com/doc/changelog
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Recommendation System

- **What changed:** Content hash changed (33a4b01b701f -> 49bcbd2af876)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/16533387?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] YouTube Search and Discovery Tips

- **What changed:** Content hash changed (414a8d9efdb6 -> 02a35c9a6ab6)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/11914225?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] YouTube Paid Promotion Declarations

- **What changed:** Content hash changed (feaec5e707da -> 2e404a1c93c9)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/154235?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Spam Policy

- **What changed:** Content hash changed (b8cbebbeb5ef -> 332c6ad2beb2)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/2801973?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Commercial and Branded Content Guidelines

- **What changed:** Content hash changed (39d831ebb6c5 -> b78290b8a176)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/commercial-and-branded-content-guidelines
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

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

- **What changed:** Source unreachable (HTTP Error 403: Blocked)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `reddit_responsible_builder_help` or mark the registry entry deprecated

### [reddit] Reddit Developers Docs

- **What changed:** Content hash changed (d316157b5701 -> fda6dedf2440)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.reddit.com/docs
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Review `harness/references/social-automation-rules.md` against the live page and update it

### [mastodon] Mastodon GitHub Releases

- **What changed:** Content hash changed (6b4a5486aa90 -> d96fdbf939c4)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://github.com/mastodon/mastodon/releases
- **Owner doc:** `knowledge/channels/mastodon-fediverse.md`
- **Next step:** Review `knowledge/channels/mastodon-fediverse.md` against the live page and update it

## Reviewed Sources

- `unchanged` [bluesky] Bluesky Rate Limits - https://docs.bsky.app/docs/advanced-guides/rate-limits
- `unchanged` [bluesky] Bluesky API Blog - https://docs.bsky.app/blog
- `unchanged` [bluesky] Bluesky Community Guidelines - https://bsky.social/about/support/community-guidelines
- `changed` [instagram] Instagram Platform Changelog - https://developers.facebook.com/docs/instagram-platform/changelog/
- `changed` [instagram] Instagram Content Publishing API - https://developers.facebook.com/docs/instagram-platform/content-publishing/
- `changed` [instagram] Instagram Media Publish Reference - https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- `unchanged` [instagram] Instagram Feed AI System - https://transparency.meta.com/features/explaining-ranking/ig-feed/
- `unchanged` [instagram] Instagram Recommendations and Originality - https://creators.instagram.com/blog/recommendations-and-originality
- `unchanged` [instagram] Instagram Algorithms and Ranking - https://creators.instagram.com/grow/algorithms-and-ranking
- `unchanged` [instagram] Instagram Reels Chaining - https://transparency.meta.com/features/explaining-ranking/ig-reels-chaining/
- `changed` [linkedin] LinkedIn Prohibited Software and Extensions - https://www.linkedin.com/help/linkedin/answer/a1341387
- `unchanged` [linkedin] LinkedIn Marketing API Recent Changes - https://learn.microsoft.com/en-us/linkedin/marketing/integrations/recent-changes?view=li-lms-2026-05
- `unchanged` [linkedin] LinkedIn API Terms of Use - https://www.linkedin.com/legal/l/api-terms-of-use
- `unchanged` [linkedin] LinkedIn Developer AI Policy - https://learn.microsoft.com/en-us/linkedin/marketing/developer-ai-policy?view=li-lms-2026-05
- `unchanged` [linkedin] LinkedIn Marketing API Terms - https://www.linkedin.com/legal/l/marketing-api-terms
- `unchanged` [linkedin] LinkedIn Posts API - https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-05
- `changed` [linkedin] LinkedIn Professional Community Policies - https://www.linkedin.com/help/linkedin/answer/a403270/linkedin-professional-community-policies
- `changed` [linkedin] LinkedIn Publishing Platform Guidelines - https://www.linkedin.com/help/linkedin/answer/a519782
- `changed` [linkedin] How LinkedIn Feed Ranks Content - https://www.linkedin.com/help/linkedin/answer/a9554004
- `unchanged` [linkedin] LinkedIn User Agreement - https://www.linkedin.com/legal/user-agreement
- `changed` [mastodon] Mastodon GitHub Releases - https://github.com/mastodon/mastodon/releases
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
- `changed` [pinterest] Pinterest GenAI Acceptable Use Guidelines - https://policy.pinterest.com/en/genai-acceptable-use-guidelines
- `changed` [pinterest] Pinterest Commercial and Branded Content Guidelines - https://policy.pinterest.com/en/commercial-and-branded-content-guidelines
- `unchanged` [pinterest] Pinterest API v5 - https://developers.pinterest.com/docs/api/v5/
- `unchanged` [pinterest] Pinterest Developer Guidelines - https://policy.pinterest.com/en-gb/developer-guidelines
- `unchanged` [pinterest] Pinterest Developer and API Terms - https://developers.pinterest.com/terms/
- `changed` [pinterest] Pinterest Community Guidelines - https://policy.pinterest.com/en/community-guidelines
- `unchanged` [pinterest] Pinterest Business Terms - https://business.pinterest.com/business-terms-of-service/
- `unchanged` [pinterest] Pinterest Terms of Service - https://policy.pinterest.com/en/terms-of-service
- `unchanged` [reddit] Reddit Public Content Policy - https://support.reddithelp.com/hc/en-us/articles/26410290525844-Public-Content-Policy
- `unchanged` [reddit] Reddit Developer Terms - https://redditinc.com/policies/developer-terms
- `changed` [reddit] Reddit Developers Docs - https://developers.reddit.com/docs
- `error` [reddit] Reddit Responsible Builder Policy - https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy
- `error` [reddit] Reddit Responsible Builder Policy Announcement - https://www.reddit.com/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/
- `unchanged` [reddit] Reddit Content Policy - https://redditinc.com/policies/content-policy
- `unchanged` [reddit] Reddit Rules - https://redditinc.com/policies/reddit-rules
- `error` [reddit] Reddit Spam Policy - https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam
- `unchanged` [reddit] Reddit User Agreement - https://redditinc.com/policies/user-agreement
- `unchanged` [snapchat] Snap Commercial Content Policy - https://values.snap.com/policy/content-guidelines-recommendation-eligibility/recommendation-eligibility/commercial-content
- `unchanged` [snapchat] Snap for Developers - https://developers.snap.com/
- `unchanged` [snapchat] Snap Creator Monetization Policy - https://values.snap.com/policy/creator-monetization-policy
- `unchanged` [snapchat] Snapchat Community Guidelines - https://values.snap.com/policy/policy-community-guidelines
- `unchanged` [snapchat] How Snap Ranks Content on Discover - https://help.snapchat.com/hc/en-us/articles/8961631424020-How-We-Rank-Content-on-Discover
- `unchanged` [snapchat] Snap Content Guidelines for Recommendation Eligibility - https://values.snap.com/policy/content-guidelines-recommendation-eligibility
- `unchanged` [snapchat] How Snap Ranks Content on Spotlight - https://help.snapchat.com/hc/en-us/articles/8961653169940-How-We-Rank-Content-on-Spotlight
- `unchanged` [snapchat] Snap Terms of Service - https://www.snap.com/terms
- `unchanged` [threads] Label AI Content on Threads - https://help.instagram.com/407718162047721/
- `unchanged` [threads] Threads API Changelog - https://developers.facebook.com/docs/threads/changelog/
- `unchanged` [threads] Threads API Documentation - https://developers.facebook.com/docs/threads/
- `unchanged` [threads] Threads Feed AI System - https://transparency.meta.com/features/explaining-ranking/ig-threads-feed/
- `unchanged` [threads] Threads Terms - https://help.instagram.com/769983657850450
- `unchanged` [tiktok] TikTok Ad Policy Change Log 2026 - https://ads.tiktok.com/help/article/tiktok-ad-policy-change-log-2026
- `changed` [tiktok] TikTok AI-Generated Content - https://support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content
- `changed` [tiktok] TikTok Developer Changelog - https://developers.tiktok.com/doc/changelog
- `changed` [tiktok] TikTok Promoting a Brand, Product, or Service - https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/promoting-a-brand-product-or-service
- `changed` [tiktok] Commercial Use of Music on TikTok - https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/commercial-use-of-music-on-tiktok
- `changed` [tiktok] TikTok Content Posting API - https://developers.tiktok.com/doc/content-posting-api-get-started
- `changed` [tiktok] TikTok Content Sharing Guidelines - https://developers.tiktok.com/doc/content-sharing-guidelines
- `unchanged` [tiktok] TikTok Community Guidelines - https://support.tiktok.com/en/safety-hc/account-and-user-safety/community-guidelines
- `unchanged` [tiktok] Why Is My Account Not Being Recommended? - https://support.tiktok.com/en/safety-hc/account-and-user-safety/why-is-my-account-not-being-recommended
- `changed` [tiktok] How TikTok Recommends Content - https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content
- `error` [x] X Automation Rules - https://help.x.com/en/rules-and-policies/x-automation
- `unchanged` [x] X API Changelog - https://docs.x.com/changelog
- `unchanged` [x] X Developer Policy - https://docs.x.com/developer-terms/policy
- `error` [x] X Rules - https://help.x.com/en/rules-and-policies/x-rules
- `error` [x] X Search Recommendations - https://help.x.com/en/resources/recommender-systems/search-recommendations
- `changed` [youtube] YouTube Advertiser-Friendly Guideline Updates - https://support.google.com/youtube/answer/9725604?hl=en
- `unchanged` [youtube] YouTube Data API Revision History - https://developers.google.com/youtube/v3/revision_history
- `changed` [youtube] YouTube Paid Promotion Declarations - https://support.google.com/youtube/answer/154235?hl=en
- `unchanged` [youtube] YouTube API Services Terms of Service - https://developers.google.com/youtube/terms/api-services-terms-of-service
- `unchanged` [youtube] YouTube API Services Developer Policies - https://developers.google.com/youtube/terms/developer-policies
- `changed` [youtube] YouTube Community Guidelines - https://support.google.com/youtube/answer/9288567?hl=en
- `error` [youtube] YouTube Fake Engagement Policy - https://support.google.com/youtube/answer/3399767?hl=en
- `changed` [youtube] YouTube GenAI Disclosure - https://support.google.com/youtube/answer/14328491?hl=en
- `changed` [youtube] YouTube Spam Policy - https://support.google.com/youtube/answer/2801973?hl=en
- `changed` [youtube] YouTube Recommendation System - https://support.google.com/youtube/answer/16533387?hl=en
- `unchanged` [youtube] Recommendations on YouTube - https://www.youtube.com/howyoutubeworks/recommendations/
- `changed` [youtube] YouTube Search and Discovery Tips - https://support.google.com/youtube/answer/11914225?hl=en
