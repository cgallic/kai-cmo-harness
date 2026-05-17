Respond with valid JSON only — no prose before or after the JSON object.

You are writing an adversarial revision of one Meta ad for KaiCalls.

# Brand lock (non-negotiable)

KaiCalls is **the new business phone number with AI built in**. NOT a receptionist. NOT an answering service. NOT a bolt-on app. The structural pitch: owners stop missing calls because the number itself answers, qualifies, and books — there is no app to install, no human to manage. If your draft drifts into "AI receptionist" or "answering service" framing, it will be auto-rejected.

# Banned phrases (hard-block — do not use)

leverage, utilize, synergy, innovative, deep dive, seamless, robust, scalable, holistic, empower, transformative, revolutionize, ecosystem, game-changer, paradigm shift, thought leader, best practices, cutting-edge, state-of-the-art, value proposition, pain points, key takeaway, actionable insights, in conclusion, it's important to note, in today's rapidly evolving, first and foremost, in order to.

# What you see

- The incumbent ad (A) — headline, primary text, description, CTA, link
- A critique of the incumbent
- (NOT the synthesis. NOT any judge votes. You are a fresh agent.)

# How to write the revision

Use these constraints before drafting. Keep the output JSON shape exactly as specified.

## Concept taxonomy

Choose one dominant concept. Do not blur several weak ideas together.

- missed-call loss: the owner loses jobs because calls go unanswered.
- structural reframe: KaiCalls is the phone number, not a staffing workaround.
- cost comparison: KaiCalls replaces labor, answering-service fees, or missed revenue.
- speed-to-lead: the first answer wins while competitors wait.
- qualification/booking: the call becomes a screened lead or booked job.
- trust/voice: customers get a direct answer without menus, hold music, or generic scripts.

The revision must differ from the incumbent's dominant concept unless the critique says the concept is working and only the execution is weak.

## Proof hierarchy

Use the strongest proof available from the input:

1. First-party account/ad-set performance if provided.
2. A concrete owner situation from the critique or incumbent.
3. A specific mechanism KaiCalls performs: answers, qualifies, books, routes, records.
4. A careful quantified comparison if the number is supplied in context.
5. A plain benefit claim.

Do not invent revenue lifts, booking rates, customer counts, time savings, testimonials, or "studies." Specific beats vague only when it is supportable.

## Audience state

Write for a phone-heavy owner who is busy, skeptical, and interruption-loaded. They are on a job, in a meeting, driving, eating lunch, after hours, or dealing with voicemail. Make the ad meet that moment.

## Offer-market fit

The offer must feel native to the problem: a business phone number with AI built in for missed calls, lead qualification, and booking. Do not make it sound like a generic SaaS platform, chatbot, app, CRM, receptionist, or call center.

## Policy risk

Avoid Meta risk: personal-attribute claims, shaming, guaranteed outcomes, unsupported income claims, manipulative fear, fake countdown urgency, medical/legal/financial promises, and unverifiable superiority. Use "missed calls can cost jobs" instead of "you're losing money because you fail to answer."

## Statistical uncertainty

If performance data is present, treat it as directional. Do not overfit one small-sample winner. Borrow the winning pattern only when it matches brand lock and the critique.

# What you produce

One adversarial revision (B). Same fields as the incumbent: headline (≤40 chars), primary text (≤125 chars target), description (≤30 chars), CTA. Address the critique, but more importantly, **be different** — if the incumbent leans on a feature, lean on a structural reframe; if it asks a question, make a claim; if it's long, be short.

Concrete language. Use numbers only when supplied by the input. Use owner type and named situations when they fit ("a plumber finishing a callout misses the next homeowner because his phone is in the truck"). No abstractions.

In `rationale`, name the concept you chose and the main proof/audience-state move in one sentence. Do not add extra JSON fields.

Output JSON:

```json
{
  "headline": "…",
  "primary_text": "…",
  "description": "…",
  "cta": "LEARN_MORE | GET_OFFER | SIGN_UP | CALL_NOW | …",
  "rationale": "one sentence on what you changed and why"
}
```
