# Social Automation Rules

Last researched: 2026-06-17

Use this before any scheduled post, API publish, reply automation, DM flow, data collection, listening job, or engagement workflow.

## Global Rule

Only use platform-approved APIs, official partner tools, or a user-controlled scheduler with clear authorization. Do not browser-bot posting, liking, commenting, following, voting, scraping, or DMing. Do not use automation to hide ownership, simulate grassroots support, evade rate limits, bypass duplicate-content systems, or inflate metrics.

## Platform Table

| Platform | Allowed automation path | Hard blocks |
|---|---|---|
| X | X API with disclosed use case, approved app, user auth, and Automation Rules review | Fake engagement, coordinated amplification, unsolicited bulk DMs, duplicate/spam posting, privacy-inconsistent data use |
| Meta / Instagram / Threads | Graph API, Instagram Platform APIs, Threads API, Meta-approved partner surfaces | Browser bots, scraping, fake accounts, coordinated inauthentic behavior, unauthorized DMs/comments/likes/follows |
| TikTok | Content Posting API / Share Kit with approved app, OAuth, required UX, creator-info checks, and rate-limit handling | Duplicate-evasion uploads, unaudited public direct posting, undisclosed branded content, unlicensed commercial music |
| YouTube | YouTube Data API with compliant OAuth, privacy policy, Terms link, quota handling, and required upload fields | Artificial views/likes/comments, mass-produced/reused spam, unsafe external links, missing AI/paid-promo/COPPA fields |
| LinkedIn | LinkedIn approved API products with account/page authorization | Scraping, unauthorized extensions, automated profile actions, engagement pods, data resale/enrichment outside terms |
| Pinterest | Pinterest API with approved access, accurate destinations, and business/developer terms | Link cloaking, bulk duplicate pins, misleading destinations, scraping, unapproved automation |
| Snapchat | Snap-approved tools/APIs and public/commercial disclosure tools | Undisclosed commercial content, recommendation-ineligible public content, regulated goods outside approved channels |
| Reddit | Approved Reddit API/app path, transparent account identity, subreddit-rule review | Vote manipulation, astroturfing, undisclosed brand accounts, scraped personal data, repetitive self-promotion |
| Bluesky | AT Protocol APIs within rate limits and label/moderation rules | Spammy write bursts, label evasion, unauthenticated scraping at scale, misleading bot identity |
| Mastodon / Fediverse | Instance-compliant API usage with local server rules and rate limits | Cross-instance spam, hidden bots, instance-rule violations, mass unsolicited mentions/DMs |

## Preflight Checklist

- [ ] Platform-specific organic rule file loaded.
- [ ] Official API/developer policy checked when the workflow mutates platform state.
- [ ] Account owner/admin authorization confirmed.
- [ ] Rate limits, quotas, and post caps checked from current docs.
- [ ] Commercial, paid partnership, affiliate, or incentive disclosures included.
- [ ] AI/synthetic media disclosures included when required.
- [ ] No artificial engagement, vote manipulation, engagement pods, or bulk unsolicited DMs.
- [ ] No scraping or enrichment outside approved APIs and retention terms.
- [ ] No duplicate-content evasion or near-duplicate cross-account posting.
- [ ] Human approval captured before live-channel mutation unless Connor explicitly approved autonomous publishing.
