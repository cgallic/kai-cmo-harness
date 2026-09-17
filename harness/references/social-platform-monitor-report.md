# Social Platform Monitor Report

Last run: 2026-09-01 14:15 UTC

Checked: 108 sources
Changed: 53
New: 0
Errors: 11
Unchanged: 44

## Impact Cards

### [x] X Rules and Best Practices

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.x.com/en/rules-and-policies/x-rules-and-best-practices
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

### [x] X Authenticity Policy

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.x.com/en/rules-and-policies/authenticity
- **Owner doc:** `harness/references/x-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `x_authenticity` or mark the registry entry deprecated

### [x] X Copyright Policy

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.x.com/en/rules-and-policies/copyright-policy
- **Owner doc:** `harness/references/x-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `x_copyright_policy` or mark the registry entry deprecated

### [x] X API Changelog

- **What changed:** Content hash changed (7d37593ec202 -> 63b6275528d4)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://docs.x.com/changelog
- **Owner doc:** `harness/references/x-organic-posting-rules.md`
- **Next step:** Review `harness/references/x-organic-posting-rules.md` against the live page and update it

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

### [instagram] Instagram Algorithms and Ranking

- **What changed:** Content hash changed (219d40411e73 -> d8a8e4ee6078)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://creators.instagram.com/grow/algorithms-and-ranking
- **Owner doc:** `knowledge/channels/instagram.md`
- **Next step:** Review `knowledge/channels/instagram.md` against the live page and update it

### [instagram] Instagram Terms of Use

- **What changed:** Source unreachable (HTTP Error 400: Bad Request)
- **Why it matters:** platform terms may have changed; recheck the owner doc for new prohibited behavior (area: community-specific rules)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.instagram.com/581066165581870/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `instagram_terms` or mark the registry entry deprecated

### [instagram] About Branded Content on Instagram

- **What changed:** Source unreachable (HTTP Error 400: Bad Request)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://help.instagram.com/128845584325492/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `instagram_branded_content` or mark the registry entry deprecated

### [threads] Threads Terms of Use

- **What changed:** Content hash changed (a9abd398557c -> 3f4c86a078bc)
- **Why it matters:** platform terms may have changed; recheck the owner doc for new prohibited behavior (area: community-specific rules)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://help.instagram.com/769983657850450
- **Monitor fetch URL:** https://about.fb.com/news/2023/07/introducing-threads-new-app-text-sharing/
- **Owner doc:** `knowledge/channels/threads-organic.md`
- **Next step:** Review `knowledge/channels/threads-organic.md` against the live page and update it

### [tiktok] TikTok Content Posting API

- **What changed:** Content hash changed (6e0de66f0989 -> 351720d4182f)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.tiktok.com/doc/content-posting-api-get-started
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Developer Guidelines

- **What changed:** Content hash changed (d1ce783e85f5 -> d5136e51fc7c)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.tiktok.com/doc/our-guidelines-developer-guidelines
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Content Sharing Guidelines

- **What changed:** Content hash changed (a159b43b2f5e -> 9ea9f653dd21)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.tiktok.com/doc/content-sharing-guidelines
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Ad Policy Change Log 2026

- **What changed:** Content hash changed (056ef8c5e044 -> 6bfb841282a2)
- **Why it matters:** ad eligibility or prohibited-content rules may have changed; recheck ad copy gates before the next paid run (area: paid amplification)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://ads.tiktok.com/help/article/tiktok-ad-policy-change-log-2026
- **Owner doc:** `harness/references/tiktok-ads-policy-reference.md`
- **Next step:** Review `harness/references/tiktok-ads-policy-reference.md` against the live page and update it

### [youtube] YouTube Community Guidelines

- **What changed:** Content hash changed (528b7c244414 -> 691d93282b03)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/9288567?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Fake Engagement Policy

- **What changed:** Content hash changed (c10255e4b9e5 -> bf92b9cdc3f8)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `block` (guardrail: matched 'fake engagement')
- **Risk:** `critical` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/3399767?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] Copyright on YouTube

- **What changed:** Content hash changed (e579cba13cc5 -> e46623c06068)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/2797466?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube GenAI Disclosure

- **What changed:** Content hash changed (f4096627d250 -> 3d765047fd95)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/14328491?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube API Services Terms of Service

- **What changed:** Content hash changed (0f52aeb0234a -> 057ca96b8a49)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.google.com/youtube/terms/api-services-terms-of-service
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube API Services Developer Policies

- **What changed:** Content hash changed (e01778aa426c -> 3be6890b4866)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.google.com/youtube/terms/developer-policies
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Advertiser-Friendly Guideline Updates

- **What changed:** Content hash changed (298f952ddb0b -> 1c21dd9b20fa)
- **Why it matters:** ad eligibility or prohibited-content rules may have changed; recheck ad copy gates before the next paid run (area: paid amplification)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/9725604?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [linkedin] LinkedIn Developer AI Policy

- **What changed:** Content hash changed (51e5e9dec465 -> 68f894b37449)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://learn.microsoft.com/en-us/linkedin/marketing/developer-ai-policy?view=li-lms-2026-07
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Community Guidelines

- **What changed:** Content hash changed (ecff5fc74b88 -> fb929f8d8d8b)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/community-guidelines
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Terms of Service

- **What changed:** Content hash changed (14c5a4a48463 -> 1a0a8fb39b58)
- **Why it matters:** platform terms may have changed; recheck the owner doc for new prohibited behavior (area: community-specific rules)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/terms-of-service
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest GenAI Acceptable Use Guidelines

- **What changed:** Content hash changed (4689b10b2866 -> c44c0558093a)
- **Why it matters:** AI/synthetic media disclosure rules may have changed; the pre-publish gate may need an AI/synthetic-media question (area: AI/synthetic media labels)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/genai-acceptable-use-guidelines
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Developers Changelog

- **What changed:** Content hash changed (f5bb700a9fdf -> 5a597fa07d40)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.pinterest.com/docs/changelog/changelog/
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Developer Guidelines

- **What changed:** Content hash changed (0b23044172a7 -> 942cb09ee299)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/developer-guidelines
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [snapchat] Snap Terms of Service

- **What changed:** Content hash changed (9739c41dee46 -> a260540037ca)
- **Why it matters:** platform terms may have changed; recheck the owner doc for new prohibited behavior (area: community-specific rules)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.snap.com/terms
- **Owner doc:** `harness/references/snapchat-organic-posting-rules.md`
- **Next step:** Review `harness/references/snapchat-organic-posting-rules.md` against the live page and update it

### [reddit] Reddit User Agreement

- **What changed:** Content hash changed (8020b7d2ad1c -> f28ecbf66da7)
- **Why it matters:** platform terms may have changed; recheck the owner doc for new prohibited behavior (area: community-specific rules)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://redditinc.com/policies/user-agreement
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Review `harness/references/reddit-organic-posting-rules.md` against the live page and update it

### [reddit] Reddit Content Policy

- **What changed:** Content hash changed (201a9c1f269b -> 3f418934fce3)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://redditinc.com/policies/content-policy
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Review `harness/references/reddit-organic-posting-rules.md` against the live page and update it

### [reddit] Reddit Developer Terms

- **What changed:** Content hash changed (0c19b94e9e1e -> ab381fadc7f6)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://redditinc.com/policies/developer-terms
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Review `harness/references/reddit-organic-posting-rules.md` against the live page and update it

### [reddit] Reddit Data API Terms

- **What changed:** Content hash changed (27879efae1dd -> 42f1d52f9296)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://redditinc.com/policies/data-api-terms
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Review `harness/references/reddit-organic-posting-rules.md` against the live page and update it

### [reddit] Reddit Public Content Policy

- **What changed:** Content hash changed (635bd0f01aca -> 6bb6c36c5f55)
- **Why it matters:** data-use or privacy terms may have changed; recheck what data automations may collect or store (area: privacy/data use)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.reddithelp.com/hc/en-us/articles/26410290525844-Public-Content-Policy
- **Monitor fetch URL:** https://redditinc.com/news/publishing-our-public-content-policy-and-introducing-a-new-community-for-researchers
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Review `harness/references/reddit-organic-posting-rules.md` against the live page and update it

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

- **What changed:** Content hash changed (5a5254ca9f6b -> ab38dc566959)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a9554004
- **Owner doc:** `knowledge/channels/linkedin-organic.md`
- **Next step:** Review `knowledge/channels/linkedin-organic.md` against the live page and update it

### [linkedin] LinkedIn Publishing Platform Guidelines

- **What changed:** Content hash changed (7cda788e1fef -> 0c0a865f72dd)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a519782
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [linkedin] LinkedIn Spam

- **What changed:** Content hash changed (c2a8142593e6 -> 6ac91796e3d2)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a1338787
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [linkedin] LinkedIn Prohibited Software and Extensions

- **What changed:** Content hash changed (244ff8e2efc7 -> a06f29999ec9)
- **Why it matters:** automation rules may have changed; the scheduler or write actions may need updated guardrails (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a1341387
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Review `harness/references/social-automation-rules.md` against the live page and update it

### [linkedin] LinkedIn Posts API

- **What changed:** Content hash changed (a53f27ee41b8 -> f55831fd7e92)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-07
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [linkedin] LinkedIn Marketing API Recent Changes

- **What changed:** Content hash changed (6203f7d289a4 -> 4d35123bf404)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://learn.microsoft.com/en-us/linkedin/marketing/integrations/recent-changes?view=li-lms-2026-07
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [meta] Meta Other Policies Hub

- **What changed:** Content hash changed (4b4c11dc45b3 -> 000f50b6683b)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://transparency.meta.com/policies/other-policies/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [threads] Meta AI labeling on Facebook, Instagram, and Threads

- **What changed:** Content hash changed (40f25d16e16b -> a53843007a65)
- **Why it matters:** AI/synthetic media disclosure rules may have changed; the pre-publish gate may need an AI/synthetic-media question (area: AI/synthetic media labels)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Promoting a Brand, Product, or Service

- **What changed:** Content hash changed (682653aed0a0 -> 2a86a70c2779)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://ads.tiktok.com/help/article/about-the-commercial-content-disclosure-setting-for-advertisers
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] Commercial Use of Music on TikTok

- **What changed:** Content hash changed (930972aa038d -> 81a2d652d3c0)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://ads.tiktok.com/help/article/commercial-music-library
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Developer Changelog

- **What changed:** Content hash changed (679cd248f235 -> 5c164b167778)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.tiktok.com/doc/changelog
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Recommendation System

- **What changed:** Content hash changed (6738252cb7ee -> f8ccdf97e054)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/16533387?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] How YouTube Search Works

- **What changed:** Content hash changed (19cc67701499 -> 7ee5bcd8800c)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/16090438?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] YouTube Search and Discovery Tips

- **What changed:** Content hash changed (0d233918b287 -> 559d9ccb6abc)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/11914225?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] YouTube Paid Promotion Declarations

- **What changed:** Content hash changed (f20245ec24dd -> 0cd6022f891b)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/154235?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Spam Policy

- **What changed:** Content hash changed (11b969b6fc47 -> b405555c891b)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/2801973?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Data API Revision History

- **What changed:** Content hash changed (cbe2d5d1c6cc -> e3dde5102c15)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.google.com/youtube/v3/revision_history
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [snapchat] Snap for Developers

- **What changed:** Content hash changed (75b295816d80 -> cd5d27d88a98)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.snap.com/
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Review `harness/references/social-automation-rules.md` against the live page and update it

### [reddit] Reddit Rules

- **What changed:** Content hash changed (201a9c1f269b -> 3f418934fce3)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://redditinc.com/policies/reddit-rules
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Review `harness/references/reddit-organic-posting-rules.md` against the live page and update it

### [reddit] Reddit Spam Policy

- **What changed:** Content hash changed (201a9c1f269b -> 3f418934fce3)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam
- **Monitor fetch URL:** https://redditinc.com/policies/reddit-rules
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Review `harness/references/reddit-organic-posting-rules.md` against the live page and update it

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

- **What changed:** Content hash changed (d387713f6a0e -> df9d1c5d2760)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.reddit.com/docs
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Review `harness/references/social-automation-rules.md` against the live page and update it

### [reddit] Developer Platform & Accessing Reddit Data

- **What changed:** Content hash changed (27879efae1dd -> 42f1d52f9296)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data
- **Monitor fetch URL:** https://redditinc.com/policies/data-api-terms
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Review `harness/references/social-automation-rules.md` against the live page and update it

### [reddit] Manipulated Content and Misleading Behavior

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://support.reddithelp.com/hc/en-us/articles/41180423371156-Manipulated-Content-and-Misleading-Behavior
- **Owner doc:** `harness/references/reddit-organic-posting-rules.md`
- **Next step:** Find a canonical replacement URL for `reddit_manipulated_content` or mark the registry entry deprecated

### [reddit] Apps on Reddit and how to get a label for your app

- **What changed:** Source unreachable (HTTP Error 403: Forbidden)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Flagged for manual review; registry entry left unchanged
- **Remaining risk:** Guidance for this source cannot be verified until the link is fixed or replaced
- **Decision:** `escalate` (source unresolved; needs manual review)
- **Risk:** `medium` · **Confidence:** high
- **Source:** https://support.reddithelp.com/hc/en-us/articles/45376380316052-Apps-on-Reddit-and-how-to-get-a-label-for-your-app
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Find a canonical replacement URL for `reddit_app_labels` or mark the registry entry deprecated

### [bluesky] Bluesky Rate Limits

- **What changed:** Content hash changed (73dcc7eb4b66 -> e3b0c44298fc)
- **Why it matters:** automation rules may have changed; the scheduler or write actions may need updated guardrails (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://docs.bsky.app/docs/advanced-guides/rate-limits
- **Owner doc:** `knowledge/channels/bluesky-organic.md`
- **Next step:** Review `knowledge/channels/bluesky-organic.md` against the live page and update it

### [bluesky] Labels and moderation

- **What changed:** Content hash changed (1bb4d7ee90fc -> e3b0c44298fc)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://docs.bsky.app/docs/advanced-guides/moderation
- **Owner doc:** `knowledge/channels/bluesky-organic.md`
- **Next step:** Review `knowledge/channels/bluesky-organic.md` against the live page and update it

### [bluesky] Bluesky API Blog

- **What changed:** Content hash changed (482151d246db -> e3b0c44298fc)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://docs.bsky.app/blog
- **Owner doc:** `knowledge/channels/bluesky-organic.md`
- **Next step:** Review `knowledge/channels/bluesky-organic.md` against the live page and update it

### [mastodon] Mastodon GitHub Releases

- **What changed:** Content hash changed (752295779273 -> b49ae081c95a)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://github.com/mastodon/mastodon/releases
- **Owner doc:** `knowledge/channels/mastodon-fediverse.md`
- **Next step:** Review `knowledge/channels/mastodon-fediverse.md` against the live page and update it

## Reviewed Sources

- `changed` [bluesky] Bluesky Rate Limits - https://docs.bsky.app/docs/advanced-guides/rate-limits
- `changed` [bluesky] Bluesky API Blog - https://docs.bsky.app/blog
- `unchanged` [bluesky] Bluesky Community Guidelines - https://bsky.social/about/support/community-guidelines
- `changed` [bluesky] Labels and moderation - https://docs.bsky.app/docs/advanced-guides/moderation
- `unchanged` [bluesky] Bluesky Terms of Service - https://bsky.social/about/support/tos
- `unchanged` [instagram] Instagram Platform Changelog - https://developers.facebook.com/docs/instagram-platform/changelog/
- `error` [instagram] About Branded Content on Instagram - https://help.instagram.com/128845584325492/
- `unchanged` [instagram] Instagram Content Publishing API - https://developers.facebook.com/docs/instagram-platform/content-publishing/
- `unchanged` [instagram] Instagram Media Publish Reference - https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- `unchanged` [instagram] Instagram Feed AI System - https://transparency.meta.com/features/explaining-ranking/ig-feed/
- `unchanged` [instagram] Instagram Recommendations and Originality - https://creators.instagram.com/blog/recommendations-and-originality
- `changed` [instagram] Instagram Algorithms and Ranking - https://creators.instagram.com/grow/algorithms-and-ranking
- `unchanged` [instagram] Instagram Reels Chaining - https://transparency.meta.com/features/explaining-ranking/ig-reels-chaining/
- `error` [instagram] Instagram Terms of Use - https://help.instagram.com/581066165581870/
- `changed` [linkedin] LinkedIn Prohibited Software and Extensions - https://www.linkedin.com/help/linkedin/answer/a1341387
- `changed` [linkedin] LinkedIn Marketing API Recent Changes - https://learn.microsoft.com/en-us/linkedin/marketing/integrations/recent-changes?view=li-lms-2026-07
- `unchanged` [linkedin] LinkedIn API Terms of Use - https://www.linkedin.com/legal/l/api-terms-of-use
- `changed` [linkedin] LinkedIn Developer AI Policy - https://learn.microsoft.com/en-us/linkedin/marketing/developer-ai-policy?view=li-lms-2026-07
- `unchanged` [linkedin] LinkedIn Marketing API Terms - https://www.linkedin.com/legal/l/marketing-api-terms
- `changed` [linkedin] LinkedIn Posts API - https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-07
- `changed` [linkedin] LinkedIn Professional Community Policies - https://www.linkedin.com/help/linkedin/answer/a403270/linkedin-professional-community-policies
- `changed` [linkedin] LinkedIn Publishing Platform Guidelines - https://www.linkedin.com/help/linkedin/answer/a519782
- `changed` [linkedin] LinkedIn Spam - https://www.linkedin.com/help/linkedin/answer/a1338787
- `changed` [linkedin] How LinkedIn Feed Ranks Content - https://www.linkedin.com/help/linkedin/answer/a9554004
- `unchanged` [linkedin] LinkedIn User Agreement - https://www.linkedin.com/legal/user-agreement
- `changed` [mastodon] Mastodon GitHub Releases - https://github.com/mastodon/mastodon/releases
- `unchanged` [mastodon] Mastodon API Guidelines - https://docs.joinmastodon.org/api/guidelines/
- `unchanged` [mastodon] Mastodon Posting Guide - https://docs.joinmastodon.org/user/posting/
- `unchanged` [mastodon] Mastodon Quote Posts Guide - https://docs.joinmastodon.org/user/quote-posts/
- `unchanged` [meta] Meta Advertising Standards - https://transparency.meta.com/policies/ad-standards/
- `unchanged` [meta] Graph API Rate Limits - https://developers.facebook.com/docs/graph-api/overview/rate-limiting/
- `unchanged` [meta] Graph API Changelog - https://developers.facebook.com/docs/graph-api/changelog/version25.0/
- `changed` [meta] Meta Other Policies Hub - https://transparency.meta.com/policies/other-policies/
- `unchanged` [meta] Meta Developer Policies - https://developers.facebook.com/devpolicy/
- `unchanged` [meta] Meta Community Notes - https://transparency.meta.com/features/community-notes/
- `unchanged` [meta] Meta Community Standards - https://transparency.meta.com/policies/community-standards/
- `unchanged` [meta] Facebook Feed AI System - https://transparency.meta.com/features/explaining-ranking/fb-feed/
- `unchanged` [meta] Meta Ranking Explainer Hub - https://transparency.meta.com/features/explaining-ranking/
- `changed` [pinterest] Pinterest GenAI Acceptable Use Guidelines - https://policy.pinterest.com/en/genai-acceptable-use-guidelines
- `changed` [pinterest] Pinterest Developers Changelog - https://developers.pinterest.com/docs/changelog/changelog/
- `unchanged` [pinterest] Pinterest Commercial and Branded Content Guidelines - https://policy.pinterest.com/en/commercial-and-branded-content-guidelines
- `unchanged` [pinterest] Pinterest API v5 - https://developers.pinterest.com/docs/api/v5/
- `changed` [pinterest] Pinterest Developer Guidelines - https://policy.pinterest.com/en/developer-guidelines
- `unchanged` [pinterest] Pinterest Developer and API Terms - https://developers.pinterest.com/terms/
- `changed` [pinterest] Pinterest Community Guidelines - https://policy.pinterest.com/en/community-guidelines
- `unchanged` [pinterest] Pinterest Business Terms - https://business.pinterest.com/business-terms-of-service/
- `changed` [pinterest] Pinterest Terms of Service - https://policy.pinterest.com/en/terms-of-service
- `changed` [reddit] Reddit Public Content Policy - https://support.reddithelp.com/hc/en-us/articles/26410290525844-Public-Content-Policy
- `error` [reddit] Apps on Reddit and how to get a label for your app - https://support.reddithelp.com/hc/en-us/articles/45376380316052-Apps-on-Reddit-and-how-to-get-a-label-for-your-app
- `changed` [reddit] Reddit Data API Terms - https://redditinc.com/policies/data-api-terms
- `changed` [reddit] Developer Platform & Accessing Reddit Data - https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data
- `changed` [reddit] Reddit Developer Terms - https://redditinc.com/policies/developer-terms
- `changed` [reddit] Reddit Developers Docs - https://developers.reddit.com/docs
- `error` [reddit] Reddit Responsible Builder Policy - https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy
- `error` [reddit] Reddit Responsible Builder Policy Announcement - https://www.reddit.com/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/
- `changed` [reddit] Reddit Content Policy - https://redditinc.com/policies/content-policy
- `error` [reddit] Manipulated Content and Misleading Behavior - https://support.reddithelp.com/hc/en-us/articles/41180423371156-Manipulated-Content-and-Misleading-Behavior
- `changed` [reddit] Reddit Rules - https://redditinc.com/policies/reddit-rules
- `changed` [reddit] Reddit Spam Policy - https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam
- `changed` [reddit] Reddit User Agreement - https://redditinc.com/policies/user-agreement
- `unchanged` [snapchat] Snap Commercial Content Policy - https://values.snap.com/policy/content-guidelines-recommendation-eligibility/recommendation-eligibility/commercial-content
- `changed` [snapchat] Snap for Developers - https://developers.snap.com/
- `unchanged` [snapchat] Snap Creator Monetization Policy - https://values.snap.com/policy/creator-monetization-policy
- `unchanged` [snapchat] Snapchat Community Guidelines - https://values.snap.com/policy/policy-community-guidelines
- `unchanged` [snapchat] About Copyright Infringement on Snapchat - https://help.snapchat.com/hc/en-us/articles/7012315652500-About-Copyright-Infringement-on-Snapchat
- `unchanged` [snapchat] Is Stories content on Snapchat moderated? - https://help.snapchat.com/hc/en-us/articles/7012263915412-Is-Stories-content-on-Snapchat-moderated
- `unchanged` [snapchat] How Snap Ranks Content on Discover - https://help.snapchat.com/hc/en-us/articles/8961631424020-How-We-Rank-Content-on-Discover
- `unchanged` [snapchat] Snap Content Guidelines for Recommendation Eligibility - https://values.snap.com/policy/content-guidelines-recommendation-eligibility
- `unchanged` [snapchat] How Snap Ranks Content on Spotlight - https://help.snapchat.com/hc/en-us/articles/8961653169940-How-We-Rank-Content-on-Spotlight
- `changed` [snapchat] Snap Terms of Service - https://www.snap.com/terms
- `changed` [threads] Meta AI labeling on Facebook, Instagram, and Threads - https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/
- `unchanged` [threads] Threads API Changelog - https://developers.facebook.com/docs/threads/changelog/
- `unchanged` [threads] Threads API Documentation - https://developers.facebook.com/docs/threads/
- `unchanged` [threads] Threads Feed AI System - https://transparency.meta.com/features/explaining-ranking/ig-threads-feed/
- `changed` [threads] Threads Terms of Use - https://help.instagram.com/769983657850450
- `changed` [tiktok] TikTok Ad Policy Change Log 2026 - https://ads.tiktok.com/help/article/tiktok-ad-policy-change-log-2026
- `unchanged` [tiktok] TikTok AI-Generated Content - https://www.tiktok.com/community-guidelines/en/integrity-authenticity/edited-media-and-ai-generated-content/
- `changed` [tiktok] TikTok Developer Changelog - https://developers.tiktok.com/doc/changelog
- `changed` [tiktok] TikTok Promoting a Brand, Product, or Service - https://ads.tiktok.com/help/article/about-the-commercial-content-disclosure-setting-for-advertisers
- `changed` [tiktok] Commercial Use of Music on TikTok - https://ads.tiktok.com/help/article/commercial-music-library
- `changed` [tiktok] TikTok Content Posting API - https://developers.tiktok.com/doc/content-posting-api-get-started
- `changed` [tiktok] TikTok Content Sharing Guidelines - https://developers.tiktok.com/doc/content-sharing-guidelines
- `changed` [tiktok] TikTok Developer Guidelines - https://developers.tiktok.com/doc/our-guidelines-developer-guidelines
- `unchanged` [tiktok] TikTok Community Guidelines - https://www.tiktok.com/community-guidelines/en/
- `unchanged` [tiktok] Why Is My Account Not Being Recommended? - https://www.tiktok.com/community-guidelines/en/for-you-feed-and-search/
- `unchanged` [tiktok] How TikTok Recommends Content - https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content
- `error` [x] X Automation Rules - https://help.x.com/en/rules-and-policies/x-automation
- `unchanged` [x] X API Rate Limits - https://docs.x.com/fundamentals/rate-limits
- `changed` [x] X API Changelog - https://docs.x.com/changelog
- `unchanged` [x] X Developer Policy - https://docs.x.com/developer-terms/policy
- `error` [x] X Authenticity Policy - https://help.x.com/en/rules-and-policies/authenticity
- `error` [x] X Copyright Policy - https://help.x.com/en/rules-and-policies/copyright-policy
- `error` [x] X Rules and Best Practices - https://help.x.com/en/rules-and-policies/x-rules-and-best-practices
- `error` [x] X Search Recommendations - https://help.x.com/en/resources/recommender-systems/search-recommendations
- `changed` [youtube] YouTube Advertiser-Friendly Guideline Updates - https://support.google.com/youtube/answer/9725604?hl=en
- `changed` [youtube] YouTube Data API Revision History - https://developers.google.com/youtube/v3/revision_history
- `changed` [youtube] YouTube Paid Promotion Declarations - https://support.google.com/youtube/answer/154235?hl=en
- `changed` [youtube] YouTube API Services Terms of Service - https://developers.google.com/youtube/terms/api-services-terms-of-service
- `changed` [youtube] YouTube API Services Developer Policies - https://developers.google.com/youtube/terms/developer-policies
- `changed` [youtube] YouTube Community Guidelines - https://support.google.com/youtube/answer/9288567?hl=en
- `changed` [youtube] Copyright on YouTube - https://support.google.com/youtube/answer/2797466?hl=en
- `changed` [youtube] YouTube Fake Engagement Policy - https://support.google.com/youtube/answer/3399767?hl=en
- `changed` [youtube] YouTube GenAI Disclosure - https://support.google.com/youtube/answer/14328491?hl=en
- `changed` [youtube] YouTube Spam Policy - https://support.google.com/youtube/answer/2801973?hl=en
- `changed` [youtube] YouTube Recommendation System - https://support.google.com/youtube/answer/16533387?hl=en
- `unchanged` [youtube] Recommendations on YouTube - https://www.youtube.com/howyoutubeworks/recommendations/
- `changed` [youtube] YouTube Search and Discovery Tips - https://support.google.com/youtube/answer/11914225?hl=en
- `changed` [youtube] How YouTube Search Works - https://support.google.com/youtube/answer/16090438?hl=en
