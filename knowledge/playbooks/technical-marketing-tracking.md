# Technical Marketing — Tracking, Pixels & GTM Playbook

> **Use when:** Setting up marketing tracking infrastructure, configuring GTM, installing pixels, implementing consent management, or debugging tracking issues.

---

## The Tracking Stack

```
LAYER 4: DASHBOARDS & REPORTING
  Looker Studio, Mixpanel, custom dashboards
  ↑ data flows up
LAYER 3: ANALYTICS PLATFORMS
  GA4, Mixpanel, Amplitude, PostHog
  ↑ events fire to
LAYER 2: TAG MANAGEMENT
  Google Tag Manager (GTM), Segment, RudderStack
  ↑ triggers from
LAYER 1: DATA LAYER + CONSENT
  dataLayer.push(), consent mode, cookie banner
  ↑ user actions
WEBSITE / APP
```

Work bottom-up. If Layer 1 is wrong, everything above it is garbage.

---

## Layer 1: Data Layer

### What Is It?

A JavaScript object that holds structured data about the page and user. GTM reads from it. It decouples your tracking from your HTML.

```javascript
// Basic data layer setup — add before GTM container
window.dataLayer = window.dataLayer || [];
dataLayer.push({
  'event': 'page_view',
  'page_type': 'product',
  'page_category': 'pricing',
  'user_logged_in': true,
  'user_plan': 'pro'
});
```

### Standard Events to Push

| Event | When to Fire | Data |
|-------|-------------|------|
| `page_view` | Every page load | page_type, page_category, page_title |
| `sign_up` | Account creation | method (google, email, etc.) |
| `login` | User logs in | method |
| `begin_checkout` | Checkout/trial start | plan, value |
| `purchase` | Payment completed | transaction_id, value, currency, plan |
| `generate_lead` | Form submission | form_name, form_location |
| `view_item` | Product/pricing page | item_name, item_category, price |
| `add_to_cart` | Added to cart | item_name, price, quantity |
| `scroll` | 25%, 50%, 75%, 90% depth | percent_scrolled |
| `click` | CTA or outbound link click | link_url, link_text, link_location |
| `video_start` | Video play begins | video_title, video_provider |
| `video_complete` | Video finishes | video_title, video_duration |
| `search` | Site search | search_term |

---

## Layer 2: Google Tag Manager (GTM)

### Setup Checklist

- [ ] GTM container created (one per website)
- [ ] GTM snippet installed: `<head>` snippet + `<body>` noscript fallback
- [ ] GTM loads before other scripts (priority loading)
- [ ] Preview mode tested (GTM debug panel shows events)
- [ ] Workspace published (draft → live)

### Essential Tags to Configure

| Tag | Purpose | Trigger |
|-----|---------|---------|
| **GA4 Configuration** | Initialize GA4 | All Pages |
| **GA4 Event — sign_up** | Track signups | Custom Event: sign_up |
| **GA4 Event — purchase** | Track purchases | Custom Event: purchase |
| **GA4 Event — generate_lead** | Track form submissions | Form Submission trigger |
| **Meta Pixel — Base** | Initialize Meta tracking | All Pages |
| **Meta Pixel — Lead** | Track Meta conversions | Custom Event: generate_lead |
| **Meta Pixel — Purchase** | Track Meta purchases | Custom Event: purchase |
| **Google Ads — Conversion** | Track Google Ads conversions | Custom Event: purchase |
| **Google Ads — Remarketing** | Build remarketing audiences | All Pages |
| **LinkedIn Insight Tag** | LinkedIn conversion tracking | All Pages |
| **TikTok Pixel** | TikTok conversion tracking | All Pages |

### GTM Trigger Types

| Trigger | Use For |
|---------|--------|
| **Page View** | Fire on every page (or specific pages) |
| **Click — All Elements** | Track button clicks, CTA clicks |
| **Click — Just Links** | Track outbound links, navigation |
| **Form Submission** | Track form completions |
| **Custom Event** | Fire on dataLayer.push({'event': 'xxx'}) |
| **Timer** | Fire after N seconds (engagement tracking) |
| **Scroll Depth** | Fire at 25%, 50%, 75%, 90% scroll |
| **Element Visibility** | Fire when a specific element becomes visible |

### GTM Variables (most used)

| Variable | Type | Purpose |
|----------|------|---------|
| `Page URL` | Built-in | Current page URL |
| `Page Path` | Built-in | URL path without domain |
| `Click URL` | Built-in | URL of clicked element |
| `Click Text` | Built-in | Text of clicked element |
| `Form ID` | Built-in | ID of submitted form |
| `Data Layer Variable` | Custom | Read any value from dataLayer |
| `1st Party Cookie` | Custom | Read cookie values |
| `Constant` | Custom | Store IDs (GA4 measurement ID, pixel IDs) |

### GTM Debugging

1. **Preview mode** — GTM provides a debug panel showing every tag, trigger, and variable
2. **GA4 DebugView** — Real-time event stream in GA4 (Admin → DebugView)
3. **Meta Pixel Helper** — Chrome extension shows pixel fires
4. **Google Tag Assistant** — Validates all Google tags on the page
5. **Browser DevTools → Network tab** — Filter by `collect?` (GA4), `tr/` (Meta), `bat.bing` (Microsoft)

---

## Layer 3: Platform Pixel Setup

### Meta Pixel

```html
<!-- Meta Pixel Base Code (via GTM or direct) -->
<script>
  !function(f,b,e,v,n,t,s)
  {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', 'YOUR_PIXEL_ID');
  fbq('track', 'PageView');
</script>
```

**Standard events:**
```javascript
fbq('track', 'Lead');              // Form submission
fbq('track', 'CompleteRegistration'); // Signup
fbq('track', 'Purchase', {value: 99, currency: 'USD'}); // Purchase
fbq('track', 'AddToCart');         // Cart
fbq('track', 'ViewContent');      // Key page view
```

### Google Ads Conversion Tag

Configure in GTM:
1. Tag type: Google Ads Conversion Tracking
2. Conversion ID + Conversion Label (from Google Ads)
3. Conversion Value: read from dataLayer variable
4. Trigger: purchase/signup event

### Enhanced Conversions (Google)

Improves conversion tracking accuracy by sending hashed first-party data:
```javascript
gtag('set', 'user_data', {
  'email': 'hashed_email',      // SHA-256 hashed
  'phone_number': 'hashed_phone',
  'address': {
    'first_name': 'hashed',
    'last_name': 'hashed'
  }
});
```

---

## Consent Management

### Why It Matters

- **GDPR** (EU): Must get consent before tracking cookies
- **CCPA** (California): Must offer opt-out
- **ePrivacy** (EU): Cookie consent required before any non-essential cookies
- **Google Consent Mode v2**: Required for Google ads in EEA — sends cookieless pings when consent is denied

### Implementation

```
USER ARRIVES
  │
  ├── EU/EEA visitor → Show consent banner BEFORE any tracking
  │   ├── Accepts → Fire all tags
  │   └── Declines → Fire GA4 in consent mode (cookieless pings)
  │                  Do NOT fire Meta/LinkedIn/TikTok pixels
  │
  ├── US visitor (California) → Fire tags, show "Do Not Sell" link
  │
  └── US visitor (other) → Fire tags normally
```

### Google Consent Mode v2

```javascript
// Default state — set before GTM loads
gtag('consent', 'default', {
  'ad_storage': 'denied',
  'ad_user_data': 'denied',
  'ad_personalization': 'denied',
  'analytics_storage': 'denied'
});

// When user accepts:
gtag('consent', 'update', {
  'ad_storage': 'granted',
  'ad_user_data': 'granted',
  'ad_personalization': 'granted',
  'analytics_storage': 'granted'
});
```

### Cookie Banner Tools

| Tool | Free Tier | Enterprise | Integration |
|------|-----------|-----------|-------------|
| Cookiebot | 1 domain free | $15+/mo | GTM, WordPress |
| OneTrust | No free tier | $500+/mo | GTM, custom |
| CookieYes | 1 domain free | $10+/mo | GTM, WordPress |
| Termly | 1 domain free | $15+/mo | GTM, any site |

---

## UTM Implementation

### Standard Parameters

Every marketing link should include UTMs. See `playbooks/analytics-attribution.md` for the full UTM standard.

```
https://yoursite.com/page?utm_source=facebook&utm_medium=cpc&utm_campaign=trial-q1&utm_content=pain-hook-v2
```

### UTM Generator Script

```javascript
// In GTM: extract UTMs and store in cookies for attribution
(function() {
  var params = new URLSearchParams(window.location.search);
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(function(p) {
    var v = params.get(p);
    if (v) {
      document.cookie = p + '=' + v + ';max-age=2592000;path=/'; // 30-day cookie
      dataLayer.push({[p]: v});
    }
  });
})();
```

---

## Tracking Audit Checklist

### Before Launch
- [ ] GTM container installed on all pages
- [ ] Data layer events fire correctly (check in Preview mode)
- [ ] GA4 receiving events (check Realtime report)
- [ ] Meta Pixel firing (check with Pixel Helper)
- [ ] Google Ads conversion tag firing (check with Tag Assistant)
- [ ] Enhanced conversions configured (if applicable)
- [ ] Consent banner working (test in EU with VPN)
- [ ] UTM parameters preserved through to conversion
- [ ] Cross-domain tracking configured (if multiple domains)
- [ ] IP anonymization enabled (GDPR requirement)

### Monthly
- [ ] Verify conversion tracking is still firing (platforms change)
- [ ] Check for tag conflicts or duplicate fires
- [ ] Review consent rates (if too low, review banner UX)
- [ ] Audit GTM workspace for unused tags
- [ ] Verify attribution data matches between platforms

### Common Debugging

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| GA4 shows 0 events | GTM not installed or consent blocking | Check GTM installation, consent mode |
| Meta shows "No activity" | Pixel not firing or wrong pixel ID | Check with Pixel Helper |
| Double-counting conversions | Tag fires twice (page reload, duplicate tag) | Add trigger exception for thank-you page |
| UTMs not showing in GA4 | Parameters stripped by redirect | Preserve UTMs through redirects |
| Cross-domain tracking broken | Missing configuration | Set up cross-domain measurement in GA4 |
| Consent banner breaks layout | CSS conflict | Test on mobile, adjust z-index |
