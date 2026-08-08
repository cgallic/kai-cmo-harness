# Pinterest Organic Posting Rules

Last researched: 2026-08-03

Primary sources:
- Community Guidelines: https://policy.pinterest.com/en/community-guidelines
- Terms of Service: https://policy.pinterest.com/en/terms-of-service
- Business Terms: https://business.pinterest.com/business-terms-of-service/
- GenAI Acceptable Use Guidelines: https://policy.pinterest.com/en/genai-acceptable-use-guidelines
- Developer Guidelines: https://policy.pinterest.com/en-gb/developer-guidelines
- Developer and API Terms: https://developers.pinterest.com/terms/

## Required Checks

- Check Community Guidelines for content, destination links, deceptive practices, regulated goods, and spam risk.
- Treat Pinterest's harmful/deceptive-products section as a hard block for growth-hack offers involving bought social accounts, account credentials, safety-bypass tools, or services built around deception/privacy violation. Source: https://policy.pinterest.com/en/community-guidelines (accessed 2026-08-03).
- Use Pinterest API only under the current Developer and API Terms.
- Follow Pinterest's developer-data constraints. Pinterest's current Developer Guidelines say you generally may not store information accessed through Pinterest Materials except campaign analytics about your own account, should call the API each time you need Pinterest account data, and cannot offer platform insights or competitor benchmarking without explicit written authorization. Source: https://policy.pinterest.com/en/developer-guidelines (accessed 2026-07-27).
- Follow Business Terms for commercial accounts, catalogs, shops, affiliates, and promoted content. Pinterest's current Terms of Service say commercial use should run through a business account and that sponsored/branded posts are subject to the Commercial and Branded Content Guidelines. Source: https://policy.pinterest.com/en/terms-of-service and https://policy.pinterest.com/en/commercial-and-branded-content-guidelines (accessed 2026-07-20).
- Apply Pinterest's GenAI acceptable-use rules when using Pinterest AI tools or AI-generated creative destined for Pinterest.
- Do not use Pinterest GenAI tools or Pinterest data for scraping, reverse engineering, jailbreaking, or collecting personal/sensitive information without rights. Pinterest's current GenAI rules also treat misleading/deceptive AI use, impersonation, misinformation, scams, and privacy abuse as policy violations, not just quality issues. Source: https://policy.pinterest.com/en/genai-acceptable-use-guidelines and https://policy.pinterest.com/en/terms-of-service (accessed 2026-07-20).
- Use accurate links, landing pages, product data, and disclosures.
- For paid partnerships, require a clear commercial disclosure such as `#ad` or Pinterest's paid partnership tool. Pinterest's current branded-content page also warns against paying people to save Pins, fake-account distribution, quid-pro-quo saves, irrelevant boards, and repetitive affiliate Pin volume. Source: https://policy.pinterest.com/en/commercial-and-branded-content-guidelines (accessed 2026-07-20).

## Organic Distribution Guidance

- Pinterest is search-and-discovery led. Keyword clarity, image quality, destination quality, board relevance, and freshness matter.
- Create fresh Pin creatives for existing URLs instead of repeatedly pinning the same creative.
- Avoid link cloaking, misleading images, irrelevant boards, mass pinning, duplicate assets, and low-quality affiliate pages.
- Treat affiliate content as one authentic-account workflow. Pinterest's affiliate guidance says affiliate content should add unique value, operate from your authentic presence, and avoid repetitive or spammy affiliate distribution. Source: https://policy.pinterest.com/en/commercial-and-branded-content-guidelines (accessed 2026-07-20).
- AI-generated Pins still need accurate attribution, safe claims, and no impersonation, misinformation, privacy abuse, or spam.
- Pinterest's current community guidelines explicitly cover harmful synthetic/manipulated content used to degrade, shame, or mislead people. Treat synthetic harassment or deceptive edits as removal/distribution-risk content, not just a creative concern. Source: https://policy.pinterest.com/en/community-guidelines and https://policy.pinterest.com/en/genai-acceptable-use-guidelines (accessed 2026-07-06).
- Treat claims about health, finance, body image, employment, and regulated goods as high-risk.

## Harness Guardrails

- Load this file for Pins, idea Pins, affiliate Pins, catalog content, and Pinterest scheduling.
- Require source URL QA before publishing: destination must match the Pin promise.
- Check `pinterest-ads-rules.md` before paid promotion.
- Do not use Pinterest GenAI tools for scraping, jailbreaking, impersonation, or deceptive affiliate workflows.
