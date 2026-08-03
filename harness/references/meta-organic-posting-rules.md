# Meta, Instagram, Facebook, and Threads Organic Posting Rules

Last researched: 2026-08-03

Primary sources:
- Meta Community Standards: https://transparency.meta.com/policies/community-standards/
- Meta Developer Policies: https://developers.facebook.com/devpolicy/
- Instagram ranking guidance: https://creators.instagram.com/grow/algorithms-and-ranking
- Instagram originality guidance: https://creators.instagram.com/blog/recommendations-and-originality
- Threads API docs: https://developers.facebook.com/docs/threads/
- Threads API changelog: https://developers.facebook.com/docs/threads/changelog/
- Threads Terms of Use: https://help.instagram.com/769983657850450
- Instagram Content Publishing API: https://developers.facebook.com/docs/instagram-platform/content-publishing/
- Instagram media publish reference: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/
- Graph API rate limits: https://developers.facebook.com/docs/graph-api/overview/rate-limiting/
- Meta ranking explainers: https://transparency.meta.com/features/explaining-ranking/
- Meta other policies hub: https://transparency.meta.com/policies/other-policies/
- About branded content on Instagram: https://help.instagram.com/128845584325492/
- Facebook Feed AI system: https://transparency.meta.com/features/explaining-ranking/fb-feed/
- Threads Feed AI system: https://transparency.meta.com/features/explaining-ranking/ig-threads-feed/
- Meta AI labeling on Facebook, Instagram, and Threads: https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/
- Meta Community Notes: https://transparency.meta.com/features/community-notes/
- Meta Advertising Standards: https://transparency.meta.com/policies/ad-standards/

## Required Checks

- Apply Meta Community Standards to Facebook, Instagram, Messenger, and Threads content.
- Use the US English version of Meta policy pages as the freshness source when regional pages differ.
- Treat AI-generated content, synthetic media, affiliate content, contests, testimonials, and regulated goods as policy-sensitive.
- Check Meta Advertising Standards before boosting any organic post.
- Check Meta's other-policies hub before branded content, affiliate, partner, Page-admin, or group/community publishing workflows.
- Treat Threads Terms as supplemental to Instagram Terms for Threads workflows. Do not assume Instagram-only product help covers Threads publishing, identity, or federation-specific obligations. Source: https://help.instagram.com/769983657850450 (accessed 2026-08-03).
- Check Graph API rate limits before burst publishing, moderation, or insights jobs. Meta's official rate-limit docs remain the canonical source for how app, user, and business-use-case limits can throttle otherwise-valid automation. Source: https://developers.facebook.com/docs/graph-api/overview/rate-limiting/ (accessed 2026-08-03).
- Use only approved APIs and permission scopes for posting, moderation, messaging, insights, or Threads management.
- Keep user consent, token scope, and account ownership records for any scheduled/published content.
- Check live Instagram/Threads API docs before scheduling. Current Meta publishing-limit language can differ by guide and endpoint.
- If Instagram content is AI-generated or meaningfully AI-altered, set the API self-disclosure field at publish time. The Instagram Platform changelog says `is_ai_generated=true` now applies the AI Info label on media or carousel containers. Source: https://developers.facebook.com/docs/instagram-platform/changelog/ (accessed 2026-06-29).
- Review Community Notes exposure for factual, political, health, finance, public-interest, or brand-claim posts.
- Use the branded-content tool path when a post has a business partner, sponsorship, or other paid-partnership context. Instagram's current branded-content help still ties partner tagging to Partner Monetization Policies and the official business-partner tag flow. Source: https://help.instagram.com/128845584325492/ (accessed 2026-08-03).
- Review AI-generated/manipulated media labeling and branded-content disclosure before publishing. Meta's current AI-labeling post says content may be auto-labeled when Meta detects AI signals, but creators still need to label AI-generated or AI-modified content when required. Source: https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/ (accessed 2026-08-03).

## Organic Distribution Guidance

- Instagram does not use one universal algorithm. Feed, Stories, Explore, and Reels each rank with different signals.
- Facebook Feed, Instagram Feed/Reels, and Threads Feed each have separate AI explainers and should be tested as distinct recommendation surfaces.
- Prioritize original posts, native Reels, carousels with saves, real comments, and topic clarity.
- Avoid repost farms, low-originality compilations, engagement bait, misleading captions, and duplicate cross-posts that add no new context.
- Put commercial or sponsored nature in the platform disclosure tools when applicable.
- Use DMs only when a user clearly initiates or opts in. Do not create unsolicited DM flows.
- Do not automate likes, follows, mass comments, fake reviews, or coordinated engagement.
- Do not browser-bot Meta surfaces. Use Graph, Instagram Platform, Threads API, or approved partner tools.
- Do not assume Threads behaves like X. Threads has Meta policy, Instagram identity dependencies, shorter public-conversation format, federation options, and separate API/changelog behavior.

## Harness Guardrails

- Load this file for `instagram`, `facebook`, `meta`, or `threads` organic posts.
- Load `meta-ads-rules.md` before promoting or turning an organic post into an ad.
- For Instagram DM funnels, require explicit opt-in language and a manual-review path for regulated claims.
- For Threads API use, verify the current Threads API capability and rate/permission constraints before scheduling.
- Threads API capabilities are still moving. The current changelog includes share-to-Instagram Stories, location tagging, and geo-gated posting features, so feature-specific automations need a live permission/capability check before scheduling. Source: https://developers.facebook.com/docs/threads/changelog/ (accessed 2026-06-29).
- For Facebook Groups, capture group rules before drafting and do not post Page-style promotion into community contexts.
- For branded-content workflows, verify the current Meta disclosure tool path before scheduling because policy pages and product surfaces move more often than the core standards.
