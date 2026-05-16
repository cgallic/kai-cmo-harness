# Agentic Commerce Readiness Checklist

Use this checklist for `agentic-commerce-readiness` audits in static fixture mode or connected mode.

## Audit Modes

- Static mode (OSS default): run with local JSON/HTML/catalog fixtures and report missing connected data as explicit gaps.
- Connected mode (optional): include live connector evidence from Merchant Center, Shopify, analytics, and checkout systems.
- Never guess missing data. List missing signals in a data-gap section.

## Required Categories

1. Product schema coverage (`Product` JSON-LD, offers, availability, currency)
2. Catalog field completeness (id, title, sku, price, availability, URL, image)
3. Pricing and inventory clarity (sale/list price consistency, stock status)
4. Shipping + return policy clarity (timelines, regions, exclusions, costs)
5. Reviews and proof signals (review volume, quality, source transparency)
6. Checkout readiness (guest checkout, payment methods, checkout URL)
7. `robots.txt` and `llms.txt` availability and relevance
8. AI crawler policy (allow/deny, licensing, policy owner)
9. Offer readability (eligibility, expiration, stackability, region rules)
10. Protocol notes (ACP/UCP/AP2/x402 readiness and blockers)

## Output Requirements

- Include scored findings with severity.
- Include top prioritized fixes.
- Include data gaps for anything unavailable in static mode.
- Include clear note that live execution requires connected accounts.
