# Reddit Organic Posting Rules

Last researched: 2026-07-27

Primary sources:
- User Agreement: https://redditinc.com/policies/user-agreement
- Reddit Rules: https://redditinc.com/policies/reddit-rules
- Developer Terms: https://redditinc.com/policies/developer-terms
- Data API Terms: https://redditinc.com/policies/data-api-terms
- Public Content Policy: https://support.reddithelp.com/hc/en-us/articles/26410290525844-Public-Content-Policy
- Spam policy: https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam
- Responsible Builder Policy announcement: https://www.reddit.com/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/
- Responsible Builder Policy help article: https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy

## Required Checks

- Follow Reddit User Agreement and Content Policy for all posts, comments, usernames, and subreddit participation.
- Read and follow each subreddit rule before posting. Subreddit rules can be stricter than platform rules.
- Use Reddit API/data only under Developer Terms, Data API Terms, and Public Content Policy. Reddit's current Data API Terms say app access must use Reddit-issued OAuth/user-agent identity, content can only be copied/displayed as needed to develop and run the app, and commercial use beyond the stated license may require a separate agreement. Source: https://redditinc.com/policies/data-api-terms (accessed 2026-07-20).
- Use approved API or licensed access for commercial Reddit data use. Do not scrape Reddit public content for AI/model-training, enrichment, or monitoring outside approved terms.
- Do not display Reddit content inside an ads-backed, paywalled, or otherwise monetized product surface without Reddit's permission and contract path. Reddit's current developer-access help says you cannot display Reddit content and run advertisements in your app, website, or service, and it treats monetized publishing of Reddit content as a commercial use that requires permission. Source: https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data (accessed 2026-07-27).
- Treat ads-backed tools, subscription products, monetized publishing of Reddit content, paid services, and model training as permission-gated commercial uses until Reddit approves the exact use case or contract path. Source: https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data and https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy (accessed 2026-07-13).
- Do not use the Data APIs to spam, incentivize, or harass users, and do not train AI on Reddit user content without the applicable rightsholder permission. Source: https://redditinc.com/policies/data-api-terms (accessed 2026-07-20).
- Do not use undisclosed brand accounts, fake users, bought accounts, coordinated voting, vote manipulation, astroturfing, or scraped personal data.
- Get approval for any new OAuth/API access path if Reddit requires it.
- Check reputation, account age, karma, flair, moderation queue, and community-specific self-promotion tolerance before posting.
- Reddit's spam page currently describes mass-posting repetitive content for exposure or financial gain, mass-tagging or unsolicited chats/DMs, and tooling that breaks Reddit or facilitates spam as enforcement risk. Keep this as a browser-verified source when the help-center URL is bot-blocked in automation. Source: https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam (accessed 2026-07-20 in browser/search).
- If Reddit Help policy pages fail in automation, use the official Reddit news Public Content Policy post and the old.reddit `redditdev` Responsible Builder announcement as monitor fallbacks, then verify the live help-center pages manually in a browser before changing guidance. Sources: https://redditinc.com/news/publishing-our-public-content-policy-and-introducing-a-new-community-for-researchers and https://old.reddit.com/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/ (accessed 2026-06-29).

## Organic Distribution Guidance

- Reddit is community-led, not broadcast-led. Trust, relevance, and subreddit fit decide whether a post survives.
- Default to useful participation, direct answers, transparent affiliation, and source-backed claims.
- Avoid drive-by self-promotion, link drops, generic comments, repetitive posting, mass tagging, unsolicited outreach, and posting before the account has community context.
- Treat each subreddit as its own channel with separate norms, mod preferences, flair rules, karma/account-age rules, and promotion tolerance.
- Treat deleted, private, quarantined, or sensitive-targeting-adjacent content as off-limits for reuse even if it was previously visible elsewhere.

## Harness Guardrails

- Load this file for Reddit listening, posting, comments, AMAs, and outreach.
- Require subreddit-specific rule notes in the brief before drafting.
- Disclose Connor/Kai affiliation when recommending Kai-owned products or participating commercially.
- Never stage Reddit actions that hide ownership or simulate grassroots support.
- Prefer listening and direct answers over links. Links should be earned by context, not used as the opening move.
