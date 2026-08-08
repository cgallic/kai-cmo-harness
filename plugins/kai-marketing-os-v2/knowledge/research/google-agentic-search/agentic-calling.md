# How to ask Google to call local businesses for you using agentic calling

> **Source:** [blog.google/products-and-platforms/products/shopping/how-to-agentic-calling-let-google-call/](https://blog.google/products-and-platforms/products/shopping/how-to-agentic-calling-let-google-call/)
> **Format:** How-to (no byline shown)
> **Tags:** Shopping, Search, Agentic

---

## Article (verbatim)

We recently released a new agentic calling feature in the U.S. where you can ask Google to call local businesses for you to gather information about what's available near you, if there are any discounts and more. Here's how to use it:

1. On Google Search, search for items like toys, health and beauty products or electronics and add "near me" or "nearby" to your search. This will indicate you want to know about buying something at a local retailer.
2. When you scroll down, you'll see an option to "Let Google call." Select the "Get started" button.
3. You'll see a short list of questions tailored to the product that will help Google understand what you're looking for.
4. Indicate whether you want to get a summary via text, email or both. Once you do, Google will call relevant businesses for you.
5. Once the calls are complete, you'll receive your summary.

---

## Structured Extractions

### Feature

**Name:** "Agentic calling" — Google initiates outbound phone calls to local businesses on behalf of a Search user.

**Surface:** Google Search results page (visible when searching for retail-style items with "near me" / "nearby" intent).

**Trigger:** User selects "Let Google call" → "Get started" button.

### Mechanics

1. User runs a Search query for an item with "near me" / "nearby."
2. Search exposes a "Let Google call" CTA in the SERP.
3. User answers a short list of product-specific clarifying questions.
4. User picks delivery channel for the summary (text, email, or both).
5. Google calls relevant local businesses.
6. User receives a consolidated summary.

### Initial verticals targeted

- Toys
- Health and beauty products
- Electronics

(Restaurants, services, automotive, professional services — not enumerated as launch verticals. Restaurant booking is covered separately by AI Mode's agentic-booking partner network, not by outbound calling.)

### Geographic rollout

United States only (as of the article).

### Mechanics NOT disclosed in this article

- Voice type — synthesized vs. recorded vs. human in the loop.
- Disclosure language used to the called business (does the AI identify itself as an AI?).
- Business opt-out mechanism (can a business mark itself "do not call with AI"?).
- Call volume per business per day.
- What questions the AI asks and how it handles complex/upsell responses.
- How call summaries are reconciled across multiple businesses.

These gaps are important for any business defending against unsolicited AI calls and for any AI-receptionist provider whose customers will receive these calls.

### Related Google product surfaces referenced

- "agentic-checkout-holiday-ai-shopping" (linked) — adjacent agentic feature in Google Shopping.

### No direct quotes attributed (article is in how-to format)
