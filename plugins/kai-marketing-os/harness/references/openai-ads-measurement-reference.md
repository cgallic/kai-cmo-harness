# OpenAI Ads Measurement Reference

Use this reference when implementing, auditing, or QAing OpenAI Ads conversion tracking for Kai sites and client growth stacks.

Sources:
- OpenAI JavaScript Pixel: https://developers.openai.com/ads/measurement-pixel
- OpenAI Conversions API: https://developers.openai.com/ads/conversions-api
- OpenAI Supported Events: https://developers.openai.com/ads/supported-events

Source rank: official OpenAI developer docs only. Do not use third-party blog posts for OpenAI parameter names, endpoint shape, event names, or matching fields.

---

## When to Load

Load this file for:

- OpenAI Ads Manager conversion setup.
- OpenAI Ads Measurement Pixel review.
- Server-side OpenAI Ads Conversions API work.
- Event fan-out changes that touch signup, lead, checkout, subscription, trial, or purchase events.
- Pixel/CAPI deduplication audits.
- Paid acquisition launch QA where ChatGPT/OpenAI Ads is part of the media mix.

This file covers measurement implementation. It does not replace `harness/references/advertising-compliance.md` for consent, disclosure, privacy, and claim compliance.

---

## Measurement Model

Use both measurement paths when possible:

| Path | Runs Where | Role |
|------|------------|------|
| JavaScript Pixel | Browser | Captures browser-side conversion events after a ChatGPT ad click, initializes with the Pixel ID, can include request-scoped hashed user data, and can pass an `event_id` for deduplication. |
| Conversions API | Server | Sends server-to-server conversion events, improves reliability beyond pixel-only tracking, supports batched events, and can use the same event identifier as the browser pixel for deduplication. |

Do not treat CAPI as a replacement for consent review. Server-side tracking still requires the same privacy basis as browser tracking.

---

## JavaScript Pixel Requirements

Install the OpenAI pixel script in the page `<head>` where conversion measurement is required, initialize with the Ads Manager Pixel ID, then call `oaiq("measure", ...)` when a conversion happens.

Implementation checks:

- `pixelId` is required and comes from the conversions tab in OpenAI Ads Manager.
- `debug` is optional and should be limited to test environments.
- User data belongs in `oaiq("init", { user: ... })`, not individual `measure` calls.
- If user data becomes available after the first init, call `init` again with the user object.
- Use supported standard event names when possible.
- Set `event_id` in the options object when the same event is also sent from the server.
- For custom events, pass `custom_event_name` in options.

User data fields supported by the pixel:

- `email_sha256`
- `external_id_sha256`
- `country`
- `city`
- `zip_code`

Hashing rules:

- Hash email after trimming whitespace and lowercasing.
- Hash external IDs only when they are stable, pseudonymous customer identifiers from your system.
- Send hashes as lowercase 64-character hexadecimal strings.
- Do not send raw emails, raw external IDs, phone numbers, or phone-number hashes.

---

## Conversions API Requirements

Send server-side events from the server only.

Endpoint:

```text
POST https://bzr.openai.com/v1/events?pid=<PIXEL-ID>
Authorization: Bearer <API-KEY>
Content-Type: application/json
```

Request body:

```json
{
  "validate_only": false,
  "events": []
}
```

Required request fields:

| Field | Requirement |
|-------|-------------|
| `pid` query param | Required. The OpenAI Ads Pixel ID. |
| `Authorization` | Required. Bearer Conversions API key from OpenAI Ads Manager. |
| `events` | Required. Array of conversion events. |
| `validate_only` | Optional. Use `true` to validate without saving events. |

Batching:

- OpenAI accepts batches up to 1,000 events.
- If one event in a batch fails validation, the full batch fails.
- Keep batch retries idempotent by reusing stable event IDs.

Verify in docs or Ads Manager before implementing:

- Response schema.
- Retry/backoff limits.
- Rate limits.
- Whether partial diagnostics are available after a failed batch.

---

## Server Event Shape

Each event has metadata plus a `data` object.

Required or conditionally required fields:

| Field | Requirement |
|-------|-------------|
| `id` | Required. Unique event identifier; used with `type` for deduplication. |
| `type` | Required. Supported standard event name or `custom`. |
| `timestamp_ms` | Required. Event time in milliseconds; must be within the last 7 days and no more than 10 minutes ahead. |
| `source_url` | Required when `action_source` is `web`. |
| `custom_event_name` | Required when `type` is `custom`. |
| `data` | Required. Must match the selected event type's data shape. |

Optional fields:

- `oppref`: OpenAI-provided privacy-preserving identifier. The server API does not capture this automatically; capture and pass it when available.
- `action_source`: one of `web`, `mobile_app`, `offline`, `physical_store`, `phone_call`, `email`, `other`.
- `user`: optional event-scoped matching fields.
- `opt_out`: set `true` to opt the event out of future user-level personalization. Defaults to `false`.

User fields supported by CAPI:

- `email_sha256`
- `external_id_sha256`
- `country`
- `city`
- `zip_code`
- `ip_address`
- `user_agent`

CAPI user-data rules:

- Put user data inside each `events[].user`, not at the request root.
- Hash email after trimming whitespace and lowercasing.
- Hash stable external IDs before sending.
- Send hash values as lowercase 64-character hexadecimal strings.
- Send geography, IP address, and user agent as raw values when available.
- Do not send raw emails, raw external IDs, phone numbers, or phone-number hashes.

---

## Supported Event Mapping

Use official standard names when they match the conversion. Current supported OpenAI Ads events include:

| OpenAI Event | Data Type | Use For |
|--------------|-----------|---------|
| `appointment_scheduled` | `customer_action` | Demo, meeting, consultation, or booking completion. |
| `checkout_started` | `contents` | Checkout start. |
| `contents_viewed` | `contents` | Product, listing, article, or other content-unit view. |
| `items_added` | `contents` | Cart, bundle, or selection add. |
| `lead_created` | `customer_action` | Lead form submit or contact request. |
| `order_created` | `contents` | Completed purchase. |
| `page_viewed` | `contents` | Important page view. |
| `registration_completed` | `customer_action` | Account or event registration completion. |
| `subscription_created` | `plan_enrollment` | Paid subscription start. |
| `trial_started` | `plan_enrollment` | Free trial start. |
| `custom` | `custom` | Only when no standard event fits. |

Common Kai fan-out mapping:

| Kai Helper | Preferred OpenAI CAPI Event | Notes |
|------------|-----------------------------|-------|
| `trackSignupServer` | `registration_completed` | Use `customer_action` data. |
| `trackFirstAgentCreatedServer` | `lead_created` | Use when first agent creation indicates qualified lead intent. |
| `trackSubscriptionServer` | `subscription_created` or `order_created` | Use `subscription_created` for a paid subscription start; use `order_created` for a one-time purchase. |

Do not silently rename existing browser pixel events if OpenAI Ads Manager conversions already depend on legacy names such as `purchase`, `lead`, or `subscribe`. Plan a migration that preserves reporting continuity.

Dedup warning: for browser/server dedup, OpenAI docs require the same Pixel ID and the same browser `event_id` / API `id`. When event names differ between client and server, verify in OpenAI docs or Ads Manager diagnostics before assuming deduplication will work. For custom events, use the same `custom_event_name` on both sides.

---

## Monetary Values

OpenAI event data supports `amount` plus `currency`.

Rules:

- Send monetary values as integers in the standard ISO 4217 minor unit for the currency.
- Example: `$129.99` USD becomes `12999` with `currency: "USD"`.
- Include `currency` whenever `amount` is present.
- Use event-level amount for the conversion value unless item-level values are needed.
- Use `contents[]` only with supported fields: `id`, `name`, `content_type`, `quantity`, `amount`, `currency`.

---

## Environment Variables

Recommended harness/application envs:

```dotenv
OPENAI_ADS_CONVERSIONS_TOKEN=
```

Legacy Kai scripts may still accept `OPENAI_ADS_CONVERSION_KEY` as a fallback, but new implementations should use `OPENAI_ADS_CONVERSIONS_TOKEN`.

The public Pixel ID is also required, but the exact env name may vary by target app. If the app already has a default Pixel ID or an existing `OpenAIPixel.tsx` config, do not rename it casually. If adding from scratch, use a clear public env name such as:

```dotenv
NEXT_PUBLIC_OPENAI_ADS_PIXEL_ID=
```

Operational rules:

- Keep the CAPI token server-only.
- Never expose `OPENAI_ADS_CONVERSIONS_TOKEN` to client bundles.
- Redact token values and hashed identifiers from logs.
- Document the Ads Manager source for the Pixel ID and CAPI key in the implementation PR or launch checklist.

Related non-OpenAI envs often changed in the same measurement pass:

```dotenv
NEXT_PUBLIC_PINTEREST_TAG_ID=
PINTEREST_AD_ACCOUNT_ID=
PINTEREST_CONVERSIONS_TOKEN=
TIKTOK_PIXEL_ID=
TIKTOK_ACCESS_TOKEN=
```

Do not use Pinterest or TikTok docs to infer OpenAI parameter names.

---

## Privacy and Consent Gates

Before shipping OpenAI Ads measurement:

- Confirm cookie/advertising consent handling for browser pixel calls.
- Confirm server events are suppressed or marked according to consent and opt-out state.
- Use `opt_out: true` only when the event should be excluded from future user-level personalization; otherwise suppress events if consent/legal basis is missing.
- Do not send prohibited raw identifiers.
- Avoid logging request bodies that include user matching fields.
- Update privacy disclosures when OpenAI Ads tracking is added to a site.
- Load `harness/references/advertising-compliance.md` for FTC, GDPR, CCPA/CPRA, COPPA, CAN-SPAM, and platform-neutral compliance review.

---

## QA Checklist

Run this before marking OpenAI Ads measurement complete:

- [ ] Pixel script loads once and initializes with the intended Pixel ID.
- [ ] Pixel user data is only sent through `init`, and only with hashed email/external ID fields.
- [ ] Server events post only from server code to `https://bzr.openai.com/v1/events?pid=<PIXEL-ID>`.
- [ ] `Authorization: Bearer <API-KEY>` uses a server-only secret.
- [ ] `validate_only: true` succeeds in test mode before saved events are enabled.
- [ ] Event `id` is stable and unique per conversion.
- [ ] Browser `event_id` and CAPI `id` match when dual-sending the same event.
- [ ] Standard event names match the intended conversion action.
- [ ] `timestamp_ms` is within OpenAI's accepted window.
- [ ] `source_url` is present for web events.
- [ ] Email and external ID hashes are lowercase 64-character SHA-256 hex strings.
- [ ] No raw email, raw external ID, phone number, or phone hash appears in payloads or logs.
- [ ] Amounts are integers in minor units and include `currency`.
- [ ] Consent and opt-out behavior has been tested.
- [ ] OpenAI Ads Manager diagnostics or conversion reports show received events after launch.

---

## Implementation Notes for Kai Agents

When reviewing a codebase that already has an OpenAI client pixel:

1. Confirm the snippet matches the current OpenAI JavaScript Pixel docs.
2. Add CAPI as the missing server half when only client-side measurement exists.
3. Fold CAPI into the existing server fan-out instead of changing every call site.
4. Preserve existing client-side event names when Ads Manager conversions depend on them.
5. Use official OpenAI event names for new server-side CAPI events unless a migration plan says otherwise.
6. Record the client/server event-name alignment decision in the PR or handoff.
7. Treat any undocumented OpenAI field, response behavior, or retry claim as `verify-in-docs`.
