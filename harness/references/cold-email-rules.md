# Cold Email — Harness Rules

## Non-Negotiables

- **Subject line**: under 50 chars, no spam triggers, no ALL CAPS, curiosity or direct value
- **First line**: NOT "I hope this email finds you well" — open with an observation about THEM
- **Body**: max 150 words. One idea. One CTA. No attachments on first touch.
- **CTA**: one question or one low-friction ask. Never "Can we jump on a 30-min call?" on touch 1.
- **Relevance evidence**: at least one verifiable reason this recipient, this company, and this moment are plausible
- **Sequence**: max 3 touches per lead, 3-5 days between touches
- **Opt-out**: include a simple unsubscribe or "reply no" mechanism, and honor it globally
- **Sender risk**: do not send if SPF/DKIM/DMARC, bounce handling, complaint handling, or suppression sync is unverified

Legal compliance is the floor, not the quality bar. Spamhaus treats unsolicited bulk email as spam and warns that scaled cold outreach, scraping, cousin domains, fake engagement, and bulk domain creation are sender-risk behaviors.

## 3-Part Structure (required)

```
[HOOK] — specific observation about them (1 sentence)
[BRIDGE] — how this connects to a pain you solve (1-2 sentences)
[CTA] — single, low-friction ask (1 sentence)
```

Example (KaiCalls → law firm):
```
Subject: after-hours intake

Saw your firm handles personal injury cases in [city] — 
after-hours intake looks like a material lead-capture risk for firms with urgent calls.

KaiCalls answers every call with an AI trained on legal intake, 
captures case details, and routes urgent matters to the right person.

Worth a quick look, or should I close the loop? Reply "no" and I will not follow up.
```

Replace bracketed or inferred claims with sourced evidence before sending. Do not include client counts, missed-call rates, price comparisons, or local-market statistics unless the source is documented.

## Banned Cold Email Patterns
- "I came across your profile and was impressed by..."
- "I wanted to reach out because..."
- "We help companies like yours to..."
- "As a fellow [industry] professional..."
- Any sentence starting with "I" (first sentence especially)
- Walls of text (>3 sentences per paragraph)
- Multiple CTAs
- "Let me know if you have any questions"
- "Looking forward to hearing from you"

## Subject Line Formulas (use these)

| Formula | Example |
|---------|---------|
| Observed trigger | "after-hours intake" |
| Direct outcome | "More answered calls, no extra staff" |
| Named problem | "The intake gap costing [city] firms leads" |
| Question (use sparingly) | "How many calls did you miss last week?" |
| Personalized observation | "[Company] + AI intake — worth 5 min?" |

## Sequence Structure

**Touch 1:** Hook + bridge + soft CTA ("Worth a look?")
**Touch 2 (3-5 days):** Different angle, same offer. Reference T1 briefly. ("Sent this last week — wanted to follow up with a quick case study")
**Touch 3 (5-7 days):** Breakup email. "Closing the loop — if now's not the time, no worries. We'll be here."

## TCPA / CAN-SPAM Compliance
- Business email only — no personal Gmail scrapes
- Must include physical address in signature
- Unsubscribe mechanism required for bulk sends (use Instantly/Loops properly)
- No purchased consumer lists
- No deceptive `Re:`/`Fwd:`, misleading sender names, or hidden commercial intent
- Opt-outs must be processed within CAN-SPAM timing requirements and synced across tools
- Marketing/subscribed bulk mail to Gmail must satisfy applicable Gmail sender requirements, including authentication, DMARC alignment where required, low spam rates, and one-click unsubscribe

## Relevance Evidence Gate

Do not send until each prospect has a row in the outreach ledger.

| Field | Required Evidence |
|-------|-------------------|
| `account_fit` | Industry, segment, company size, geography, or tech stack match |
| `trigger_event` | Hiring, funding, expansion, job change, new location, compliance change, product launch, visible demand signal |
| `problem_evidence` | Public page, job post, review, support pattern, ad, call data, content engagement, or known category pain |
| `recipient_role` | Why this person owns, influences, or feels the problem |
| `source_url_or_note` | URL, CRM note, event attendance, referral, or internal source |
| `confidence` | `high`, `medium`, or `hypothesis` |

If confidence is `hypothesis`, write the email as a soft research question, not a claim.

## Sender Risk Grading

| Grade | Conditions | Action |
|-------|------------|--------|
| **Green** | Authenticated domain, clean suppression sync, low recent bounces, no complaint spike, human-reviewed list | Send limited test cohort |
| **Yellow** | New domain/IP, unproven list source, incomplete DMARC reporting, weak trigger evidence | Reduce volume, enrich evidence, test manually |
| **Red** | Purchased/scraped list, cousin domains, fake warmup/engagement, complaints/blocklist signals, missing opt-out | Do not send |

## Source Notes

References retrieved 2026-05-17: Google Email Sender Guidelines, Yahoo Sender Hub, FTC CAN-SPAM compliance guide, Spamhaus cold-email guidance, Lavender cold-email benchmark notes, Gong cold-email guide, 6sense 2025 B2B Buyer Experience Report, and Gartner B2B buying journey guidance where accessible. Vendor benchmarks are context only; account-level reply, complaint, bounce, and opportunity data decide the operating threshold.
