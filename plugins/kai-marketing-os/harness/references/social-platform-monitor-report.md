# Social Platform Monitor Report

Last run: 2026-11-01 16:13 UTC

Checked: 108 sources
Changed: 56
New: 0
Errors: 11
Unchanged: 41

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

### [x] X Developer Policy

- **What changed:** Content hash changed (735cd319eda6 -> f0c694f5106f)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://docs.x.com/developer-terms/policy
- **Owner doc:** `harness/references/x-organic-posting-rules.md`
- **Next step:** Review `harness/references/x-organic-posting-rules.md` against the live page and update it

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

### [x] X API Rate Limits

- **What changed:** Content hash changed (195a2310ad5b -> 7df09660fc36)
- **Why it matters:** automation rules may have changed; the scheduler or write actions may need updated guardrails (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://docs.x.com/fundamentals/rate-limits
- **Owner doc:** `harness/references/x-organic-posting-rules.md`
- **Next step:** Review `harness/references/x-organic-posting-rules.md` against the live page and update it

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

- **What changed:** Content hash changed (45f1970a5fb3 -> 18593a234e70)
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

### [meta] Meta Advertising Standards

- **What changed:** Content hash changed (b4b87b057849 -> 465ab3e57ed2)
- **Why it matters:** ad eligibility or prohibited-content rules may have changed; recheck ad copy gates before the next paid run (area: paid amplification)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://transparency.meta.com/policies/ad-standards/
- **Owner doc:** `harness/references/meta-ads-rules.md`
- **Next step:** Review `harness/references/meta-ads-rules.md` against the live page and update it

### [instagram] Instagram Recommendations and Originality

- **What changed:** Content hash changed (aecd0f809307 -> 4fd8be6ab901)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://creators.instagram.com/blog/recommendations-and-originality
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

### [threads] Threads API Documentation

- **What changed:** Content hash changed (a75b76ba83cf -> 971fcb5d8d9a)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.facebook.com/docs/threads/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [threads] Threads Terms of Use

- **What changed:** Content hash changed (14930923c0d3 -> 7e4ebed32219)
- **Why it matters:** platform terms may have changed; recheck the owner doc for new prohibited behavior (area: community-specific rules)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://help.instagram.com/769983657850450
- **Monitor fetch URL:** https://about.fb.com/news/2023/07/introducing-threads-new-app-text-sharing/
- **Owner doc:** `knowledge/channels/threads-organic.md`
- **Next step:** Review `knowledge/channels/threads-organic.md` against the live page and update it

### [tiktok] TikTok Community Guidelines

- **What changed:** Content hash changed (3da6fae2b4fd -> b9c74cf198d6)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.tiktok.com/community-guidelines/en/
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] Why Is My Account Not Being Recommended?

- **What changed:** Content hash changed (3da6fae2b4fd -> 68fc4a9127db)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.tiktok.com/community-guidelines/en/for-you-feed-and-search/
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Ad Policy Change Log 2026

- **What changed:** Content hash changed (647bac69a115 -> efce879a2c74)
- **Why it matters:** ad eligibility or prohibited-content rules may have changed; recheck ad copy gates before the next paid run (area: paid amplification)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://ads.tiktok.com/help/article/tiktok-ad-policy-change-log-2026
- **Owner doc:** `harness/references/tiktok-ads-policy-reference.md`
- **Next step:** Review `harness/references/tiktok-ads-policy-reference.md` against the live page and update it

### [youtube] YouTube Community Guidelines

- **What changed:** Content hash changed (163a71a07792 -> 943c02165097)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/9288567?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] Recommendations on YouTube

- **What changed:** Content hash changed (6ebb373ab351 -> 89f054482b1d)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.youtube.com/howyoutubeworks/recommendations/
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] YouTube Fake Engagement Policy

- **What changed:** Content hash changed (9b5a18a4b47e -> ce8dd490d0f5)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `block` (guardrail: matched 'fake engagement')
- **Risk:** `critical` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/3399767?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] Copyright on YouTube

- **What changed:** Content hash changed (f890cfe300e9 -> 28cd3c895e78)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/2797466?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube GenAI Disclosure

- **What changed:** Content hash changed (406641d460b1 -> ba5e20783be2)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/14328491?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube API Services Developer Policies

- **What changed:** Content hash changed (e646c75ab201 -> f522cc098b6f)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.google.com/youtube/terms/developer-policies
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Advertiser-Friendly Guideline Updates

- **What changed:** Content hash changed (4fcf2eecd0f0 -> 94e3837bd03f)
- **Why it matters:** ad eligibility or prohibited-content rules may have changed; recheck ad copy gates before the next paid run (area: paid amplification)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/9725604?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [linkedin] LinkedIn Developer AI Policy

- **What changed:** Content hash changed (3f2f87da440e -> c95381a1d3fd)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://learn.microsoft.com/en-us/linkedin/marketing/developer-ai-policy?view=li-lms-2026-07
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Community Guidelines

- **What changed:** Content hash changed (d19e1570a342 -> 28c3d3067c04)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/community-guidelines
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Terms of Service

- **What changed:** Content hash changed (46b923df5fd7 -> e78b42e5c87e)
- **Why it matters:** platform terms may have changed; recheck the owner doc for new prohibited behavior (area: community-specific rules)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/terms-of-service
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest GenAI Acceptable Use Guidelines

- **What changed:** Content hash changed (031e945dd456 -> 8e10c6e23f6f)
- **Why it matters:** AI/synthetic media disclosure rules may have changed; the pre-publish gate may need an AI/synthetic-media question (area: AI/synthetic media labels)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/genai-acceptable-use-guidelines
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Developers Changelog

- **What changed:** Content hash changed (553355a53c02 -> 3b031cf941c7)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.pinterest.com/docs/changelog/changelog/
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [snapchat] Snapchat Community Guidelines

- **What changed:** Content hash changed (e107bb46c2c7 -> ffcceb80178d)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://values.snap.com/policy/policy-community-guidelines
- **Owner doc:** `harness/references/snapchat-organic-posting-rules.md`
- **Next step:** Review `harness/references/snapchat-organic-posting-rules.md` against the live page and update it

### [snapchat] Snap Content Guidelines for Recommendation Eligibility

- **What changed:** Content hash changed (bc44fa6dd150 -> 391069612145)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://values.snap.com/policy/content-guidelines-recommendation-eligibility
- **Owner doc:** `harness/references/snapchat-organic-posting-rules.md`
- **Next step:** Review `harness/references/snapchat-organic-posting-rules.md` against the live page and update it

### [snapchat] Snap Creator Monetization Policy

- **What changed:** Content hash changed (efb5cd2971ea -> b5ae5fc6ec07)
- **Why it matters:** monetization or eligibility rules may have changed; recheck program assumptions (area: paid amplification)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://values.snap.com/policy/creator-monetization-policy
- **Owner doc:** `harness/references/snapchat-organic-posting-rules.md`
- **Next step:** Review `harness/references/snapchat-organic-posting-rules.md` against the live page and update it

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

- **What changed:** Content hash changed (20413d76a22b -> 013053672679)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a403270/linkedin-professional-community-policies
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [linkedin] How LinkedIn Feed Ranks Content

- **What changed:** Content hash changed (5ded689fbfa8 -> 45160e04bdf0)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a9554004
- **Owner doc:** `knowledge/channels/linkedin-organic.md`
- **Next step:** Review `knowledge/channels/linkedin-organic.md` against the live page and update it

### [linkedin] LinkedIn Publishing Platform Guidelines

- **What changed:** Content hash changed (513036f229d8 -> 958beac56082)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a519782
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [linkedin] LinkedIn Spam

- **What changed:** Content hash changed (d91019bfcdce -> e5898d392869)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a1338787
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [linkedin] LinkedIn Prohibited Software and Extensions

- **What changed:** Content hash changed (a06f29999ec9 -> 6968df60b4ab)
- **Why it matters:** automation rules may have changed; the scheduler or write actions may need updated guardrails (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://www.linkedin.com/help/linkedin/answer/a1341387
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Review `harness/references/social-automation-rules.md` against the live page and update it

### [linkedin] LinkedIn Posts API

- **What changed:** Content hash changed (0401b886d455 -> 8db7f962804f)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-07
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [linkedin] LinkedIn Marketing API Recent Changes

- **What changed:** Content hash changed (b86101d80fb4 -> 2f66d72cf6d3)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://learn.microsoft.com/en-us/linkedin/marketing/integrations/recent-changes?view=li-lms-2026-07
- **Owner doc:** `harness/references/linkedin-organic-posting-rules.md`
- **Next step:** Review `harness/references/linkedin-organic-posting-rules.md` against the live page and update it

### [meta] Meta Ranking Explainer Hub

- **What changed:** Content hash changed (256e8d97e15f -> c7ba2adc4ba5)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://transparency.meta.com/features/explaining-ranking/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [meta] Facebook Feed AI System

- **What changed:** Content hash changed (0ce568056cef -> ec40069a8ff6)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://transparency.meta.com/features/explaining-ranking/fb-feed/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [instagram] Instagram Feed AI System

- **What changed:** Content hash changed (85209b0e80d8 -> d8bbdf0c4378)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://transparency.meta.com/features/explaining-ranking/ig-feed/
- **Owner doc:** `knowledge/channels/instagram.md`
- **Next step:** Review `knowledge/channels/instagram.md` against the live page and update it

### [instagram] Instagram Reels Chaining

- **What changed:** Content hash changed (735119cb72bb -> 67e9645689af)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://transparency.meta.com/features/explaining-ranking/ig-reels-chaining/
- **Owner doc:** `knowledge/channels/instagram.md`
- **Next step:** Review `knowledge/channels/instagram.md` against the live page and update it

### [threads] Threads API Changelog

- **What changed:** Content hash changed (041be65d6921 -> 236658a8fe5f)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.facebook.com/docs/threads/changelog/
- **Owner doc:** `knowledge/channels/threads-organic.md`
- **Next step:** Review `knowledge/channels/threads-organic.md` against the live page and update it

### [threads] Threads Feed AI System

- **What changed:** Content hash changed (bd7f816b4b03 -> d2d88b744481)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://transparency.meta.com/features/explaining-ranking/ig-threads-feed/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [threads] Meta AI labeling on Facebook, Instagram, and Threads

- **What changed:** Content hash changed (4d6dacce5ebd -> 85cfe098156c)
- **Why it matters:** AI/synthetic media disclosure rules may have changed; the pre-publish gate may need an AI/synthetic-media question (area: AI/synthetic media labels)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [instagram] Instagram Content Publishing API

- **What changed:** Content hash changed (7eb7d697e3be -> b8a0f7b7a5af)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.facebook.com/docs/instagram-platform/content-publishing/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [instagram] Instagram Media Publish Reference

- **What changed:** Content hash changed (d0565841ef8c -> c59089b281fb)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [instagram] Instagram Platform Changelog

- **What changed:** Content hash changed (6d3e4294820c -> 453302f258dd)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.facebook.com/docs/instagram-platform/changelog/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [meta] Graph API Changelog

- **What changed:** Content hash changed (47d381a9622c -> e108d36e5455)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.facebook.com/docs/graph-api/changelog/version25.0/
- **Owner doc:** `harness/references/meta-organic-posting-rules.md`
- **Next step:** Review `harness/references/meta-organic-posting-rules.md` against the live page and update it

### [tiktok] TikTok Promoting a Brand, Product, or Service

- **What changed:** Content hash changed (2a86a70c2779 -> d37e1347d6a4)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://ads.tiktok.com/help/article/about-the-commercial-content-disclosure-setting-for-advertisers
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [tiktok] Commercial Use of Music on TikTok

- **What changed:** Content hash changed (81a2d652d3c0 -> 6a63bbefbc4d)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://ads.tiktok.com/help/article/commercial-music-library
- **Owner doc:** `harness/references/tiktok-organic-posting-rules.md`
- **Next step:** Review `harness/references/tiktok-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Recommendation System

- **What changed:** Content hash changed (4cbaee41dafe -> fd0b93a32601)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/16533387?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] How YouTube Search Works

- **What changed:** Content hash changed (4f7a5d774be3 -> 32be7c3c2709)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/16090438?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] YouTube Search and Discovery Tips

- **What changed:** Content hash changed (ce45d96428a4 -> 6664f6de8487)
- **Why it matters:** ranking or eligibility guidance may have changed; recheck distribution playbooks (area: recommendation eligibility)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/11914225?hl=en
- **Owner doc:** `knowledge/channels/youtube.md`
- **Next step:** Review `knowledge/channels/youtube.md` against the live page and update it

### [youtube] YouTube Paid Promotion Declarations

- **What changed:** Content hash changed (2524cec01cfe -> 37f7aa88dd99)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/154235?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Spam Policy

- **What changed:** Content hash changed (8d77e0a71f07 -> 34a0c1af8396)
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://support.google.com/youtube/answer/2801973?hl=en
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [youtube] YouTube Data API Revision History

- **What changed:** Content hash changed (bae42920112f -> 2fadefb71dbe)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.google.com/youtube/v3/revision_history
- **Owner doc:** `harness/references/youtube-organic-posting-rules.md`
- **Next step:** Review `harness/references/youtube-organic-posting-rules.md` against the live page and update it

### [pinterest] Pinterest Commercial and Branded Content Guidelines

- **What changed:** Content hash changed (458176d75664 -> 7ba6f6d1dfe0)
- **Why it matters:** branded-content or disclosure requirements may have changed; recheck commercial-disclosure rules (area: commercial disclosure)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://policy.pinterest.com/en/commercial-and-branded-content-guidelines
- **Owner doc:** `harness/references/pinterest-organic-posting-rules.md`
- **Next step:** Review `harness/references/pinterest-organic-posting-rules.md` against the live page and update it

### [snapchat] Snap for Developers

- **What changed:** Content hash changed (cd5d27d88a98 -> 95638ef19675)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.snap.com/
- **Owner doc:** `harness/references/social-automation-rules.md`
- **Next step:** Review `harness/references/social-automation-rules.md` against the live page and update it

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

- **What changed:** Content hash changed (a2ed7b8687aa -> 4c8b11a5ca97)
- **Why it matters:** developer terms may have changed; API usage limits or content-usage rules may affect automations (area: API automation)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://developers.reddit.com/docs
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

- **What changed:** Previously broken source is reachable again
- **Why it matters:** automation rules may have changed; the scheduler or write actions may need updated guardrails (area: API automation)
- **Action taken:** Snapshot refreshed now that the source is reachable
- **Remaining risk:** Confirm the recovered page still matches the owner doc
- **Decision:** `auto_fix` (safe snapshot change)
- **Risk:** `low` · **Confidence:** high
- **Source:** https://docs.bsky.app/docs/advanced-guides/rate-limits
- **Owner doc:** `knowledge/channels/bluesky-organic.md`
- **Next step:** Spot-check `knowledge/channels/bluesky-organic.md`

### [bluesky] Labels and moderation

- **What changed:** Previously broken source is reachable again
- **Why it matters:** allowed-content rules may have shifted; recheck the owner doc and the pre-publish gate (area: allowed content)
- **Action taken:** Snapshot refreshed now that the source is reachable
- **Remaining risk:** Confirm the recovered page still matches the owner doc
- **Decision:** `auto_fix` (safe snapshot change)
- **Risk:** `low` · **Confidence:** high
- **Source:** https://docs.bsky.app/docs/advanced-guides/moderation
- **Owner doc:** `knowledge/channels/bluesky-organic.md`
- **Next step:** Spot-check `knowledge/channels/bluesky-organic.md`

### [bluesky] Bluesky API Blog

- **What changed:** Content hash changed (e3b0c44298fc -> 883e06c70245)
- **Why it matters:** an API change may affect posting limits, required upload fields, or the scheduler (area: scheduling/rate limits)
- **Action taken:** Snapshot hash updated; change logged for owner-doc review
- **Remaining risk:** The specific rule change is not yet read into the owner doc
- **Decision:** `auto_fix` (safe docs change)
- **Risk:** `low` · **Confidence:** medium
- **Source:** https://docs.bsky.app/blog
- **Owner doc:** `knowledge/channels/bluesky-organic.md`
- **Next step:** Review `knowledge/channels/bluesky-organic.md` against the live page and update it

### [mastodon] Mastodon GitHub Releases

- **What changed:** Content hash changed (9546d9d5a59a -> a4bc13f6c33a)
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
- `changed` [bluesky] Bluesky API Blog - https://docs.bsky.app/blog
- `unchanged` [bluesky] Bluesky Community Guidelines - https://bsky.social/about/support/community-guidelines
- `unchanged` [bluesky] Labels and moderation - https://docs.bsky.app/docs/advanced-guides/moderation
- `unchanged` [bluesky] Bluesky Terms of Service - https://bsky.social/about/support/tos
- `changed` [instagram] Instagram Platform Changelog - https://developers.facebook.com/docs/instagram-platform/changelog/
- `error` [instagram] About Branded Content on Instagram - https://help.instagram.com/128845584325492/
- `changed` [instagram] Instagram Content Publishing API - https://developers.facebook.com/docs/instagram-platform/content-publishing/
- `changed` [instagram] Instagram Media Publish Reference - https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- `changed` [instagram] Instagram Feed AI System - https://transparency.meta.com/features/explaining-ranking/ig-feed/
- `changed` [instagram] Instagram Recommendations and Originality - https://creators.instagram.com/blog/recommendations-and-originality
- `unchanged` [instagram] Instagram Algorithms and Ranking - https://creators.instagram.com/grow/algorithms-and-ranking
- `changed` [instagram] Instagram Reels Chaining - https://transparency.meta.com/features/explaining-ranking/ig-reels-chaining/
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
- `changed` [meta] Meta Advertising Standards - https://transparency.meta.com/policies/ad-standards/
- `unchanged` [meta] Graph API Rate Limits - https://developers.facebook.com/docs/graph-api/overview/rate-limiting/
- `changed` [meta] Graph API Changelog - https://developers.facebook.com/docs/graph-api/changelog/version25.0/
- `unchanged` [meta] Meta Other Policies Hub - https://transparency.meta.com/policies/other-policies/
- `unchanged` [meta] Meta Developer Policies - https://developers.facebook.com/devpolicy/
- `unchanged` [meta] Meta Community Notes - https://transparency.meta.com/features/community-notes/
- `unchanged` [meta] Meta Community Standards - https://transparency.meta.com/policies/community-standards/
- `changed` [meta] Facebook Feed AI System - https://transparency.meta.com/features/explaining-ranking/fb-feed/
- `changed` [meta] Meta Ranking Explainer Hub - https://transparency.meta.com/features/explaining-ranking/
- `changed` [pinterest] Pinterest GenAI Acceptable Use Guidelines - https://policy.pinterest.com/en/genai-acceptable-use-guidelines
- `changed` [pinterest] Pinterest Developers Changelog - https://developers.pinterest.com/docs/changelog/changelog/
- `changed` [pinterest] Pinterest Commercial and Branded Content Guidelines - https://policy.pinterest.com/en/commercial-and-branded-content-guidelines
- `unchanged` [pinterest] Pinterest API v5 - https://developers.pinterest.com/docs/api/v5/
- `unchanged` [pinterest] Pinterest Developer Guidelines - https://policy.pinterest.com/en/developer-guidelines
- `unchanged` [pinterest] Pinterest Developer and API Terms - https://developers.pinterest.com/terms/
- `changed` [pinterest] Pinterest Community Guidelines - https://policy.pinterest.com/en/community-guidelines
- `unchanged` [pinterest] Pinterest Business Terms - https://business.pinterest.com/business-terms-of-service/
- `changed` [pinterest] Pinterest Terms of Service - https://policy.pinterest.com/en/terms-of-service
- `unchanged` [reddit] Reddit Public Content Policy - https://support.reddithelp.com/hc/en-us/articles/26410290525844-Public-Content-Policy
- `error` [reddit] Apps on Reddit and how to get a label for your app - https://support.reddithelp.com/hc/en-us/articles/45376380316052-Apps-on-Reddit-and-how-to-get-a-label-for-your-app
- `unchanged` [reddit] Reddit Data API Terms - https://redditinc.com/policies/data-api-terms
- `unchanged` [reddit] Developer Platform & Accessing Reddit Data - https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data
- `unchanged` [reddit] Reddit Developer Terms - https://redditinc.com/policies/developer-terms
- `changed` [reddit] Reddit Developers Docs - https://developers.reddit.com/docs
- `error` [reddit] Reddit Responsible Builder Policy - https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy
- `error` [reddit] Reddit Responsible Builder Policy Announcement - https://www.reddit.com/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/
- `unchanged` [reddit] Reddit Content Policy - https://redditinc.com/policies/content-policy
- `error` [reddit] Manipulated Content and Misleading Behavior - https://support.reddithelp.com/hc/en-us/articles/41180423371156-Manipulated-Content-and-Misleading-Behavior
- `unchanged` [reddit] Reddit Rules - https://redditinc.com/policies/reddit-rules
- `unchanged` [reddit] Reddit Spam Policy - https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam
- `unchanged` [reddit] Reddit User Agreement - https://redditinc.com/policies/user-agreement
- `unchanged` [snapchat] Snap Commercial Content Policy - https://values.snap.com/policy/content-guidelines-recommendation-eligibility/recommendation-eligibility/commercial-content
- `changed` [snapchat] Snap for Developers - https://developers.snap.com/
- `changed` [snapchat] Snap Creator Monetization Policy - https://values.snap.com/policy/creator-monetization-policy
- `changed` [snapchat] Snapchat Community Guidelines - https://values.snap.com/policy/policy-community-guidelines
- `unchanged` [snapchat] About Copyright Infringement on Snapchat - https://help.snapchat.com/hc/en-us/articles/7012315652500-About-Copyright-Infringement-on-Snapchat
- `unchanged` [snapchat] Is Stories content on Snapchat moderated? - https://help.snapchat.com/hc/en-us/articles/7012263915412-Is-Stories-content-on-Snapchat-moderated
- `unchanged` [snapchat] How Snap Ranks Content on Discover - https://help.snapchat.com/hc/en-us/articles/8961631424020-How-We-Rank-Content-on-Discover
- `changed` [snapchat] Snap Content Guidelines for Recommendation Eligibility - https://values.snap.com/policy/content-guidelines-recommendation-eligibility
- `unchanged` [snapchat] How Snap Ranks Content on Spotlight - https://help.snapchat.com/hc/en-us/articles/8961653169940-How-We-Rank-Content-on-Spotlight
- `unchanged` [snapchat] Snap Terms of Service - https://www.snap.com/terms
- `changed` [threads] Meta AI labeling on Facebook, Instagram, and Threads - https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/
- `changed` [threads] Threads API Changelog - https://developers.facebook.com/docs/threads/changelog/
- `changed` [threads] Threads API Documentation - https://developers.facebook.com/docs/threads/
- `changed` [threads] Threads Feed AI System - https://transparency.meta.com/features/explaining-ranking/ig-threads-feed/
- `changed` [threads] Threads Terms of Use - https://help.instagram.com/769983657850450
- `changed` [tiktok] TikTok Ad Policy Change Log 2026 - https://ads.tiktok.com/help/article/tiktok-ad-policy-change-log-2026
- `unchanged` [tiktok] TikTok AI-Generated Content - https://www.tiktok.com/community-guidelines/en/integrity-authenticity/edited-media-and-ai-generated-content/
- `unchanged` [tiktok] TikTok Developer Changelog - https://developers.tiktok.com/doc/changelog
- `changed` [tiktok] TikTok Promoting a Brand, Product, or Service - https://ads.tiktok.com/help/article/about-the-commercial-content-disclosure-setting-for-advertisers
- `changed` [tiktok] Commercial Use of Music on TikTok - https://ads.tiktok.com/help/article/commercial-music-library
- `unchanged` [tiktok] TikTok Content Posting API - https://developers.tiktok.com/doc/content-posting-api-get-started
- `unchanged` [tiktok] TikTok Content Sharing Guidelines - https://developers.tiktok.com/doc/content-sharing-guidelines
- `unchanged` [tiktok] TikTok Developer Guidelines - https://developers.tiktok.com/doc/our-guidelines-developer-guidelines
- `changed` [tiktok] TikTok Community Guidelines - https://www.tiktok.com/community-guidelines/en/
- `changed` [tiktok] Why Is My Account Not Being Recommended? - https://www.tiktok.com/community-guidelines/en/for-you-feed-and-search/
- `unchanged` [tiktok] How TikTok Recommends Content - https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content
- `error` [x] X Automation Rules - https://help.x.com/en/rules-and-policies/x-automation
- `changed` [x] X API Rate Limits - https://docs.x.com/fundamentals/rate-limits
- `changed` [x] X API Changelog - https://docs.x.com/changelog
- `changed` [x] X Developer Policy - https://docs.x.com/developer-terms/policy
- `error` [x] X Authenticity Policy - https://help.x.com/en/rules-and-policies/authenticity
- `error` [x] X Copyright Policy - https://help.x.com/en/rules-and-policies/copyright-policy
- `error` [x] X Rules and Best Practices - https://help.x.com/en/rules-and-policies/x-rules-and-best-practices
- `error` [x] X Search Recommendations - https://help.x.com/en/resources/recommender-systems/search-recommendations
- `changed` [youtube] YouTube Advertiser-Friendly Guideline Updates - https://support.google.com/youtube/answer/9725604?hl=en
- `changed` [youtube] YouTube Data API Revision History - https://developers.google.com/youtube/v3/revision_history
- `changed` [youtube] YouTube Paid Promotion Declarations - https://support.google.com/youtube/answer/154235?hl=en
- `unchanged` [youtube] YouTube API Services Terms of Service - https://developers.google.com/youtube/terms/api-services-terms-of-service
- `changed` [youtube] YouTube API Services Developer Policies - https://developers.google.com/youtube/terms/developer-policies
- `changed` [youtube] YouTube Community Guidelines - https://support.google.com/youtube/answer/9288567?hl=en
- `changed` [youtube] Copyright on YouTube - https://support.google.com/youtube/answer/2797466?hl=en
- `changed` [youtube] YouTube Fake Engagement Policy - https://support.google.com/youtube/answer/3399767?hl=en
- `changed` [youtube] YouTube GenAI Disclosure - https://support.google.com/youtube/answer/14328491?hl=en
- `changed` [youtube] YouTube Spam Policy - https://support.google.com/youtube/answer/2801973?hl=en
- `changed` [youtube] YouTube Recommendation System - https://support.google.com/youtube/answer/16533387?hl=en
- `changed` [youtube] Recommendations on YouTube - https://www.youtube.com/howyoutubeworks/recommendations/
- `changed` [youtube] YouTube Search and Discovery Tips - https://support.google.com/youtube/answer/11914225?hl=en
- `changed` [youtube] How YouTube Search Works - https://support.google.com/youtube/answer/16090438?hl=en
