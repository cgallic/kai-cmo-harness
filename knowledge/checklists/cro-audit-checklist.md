# CRO Audit Checklist

> **Use when:** Auditing conversion rate optimization on a website, landing page, or funnel.

---

## Technical Foundation

### Performance
- [ ] Page loads in < 3 seconds on mobile (4G network)
- [ ] Core Web Vitals pass: LCP < 2.5s, FID < 100ms, CLS < 0.1
- [ ] No JS errors in browser console
- [ ] No broken images or missing assets
- [ ] Server response time < 200ms (TTFB)
- [ ] Images optimized (WebP/AVIF, lazy-loaded below fold)

### Mobile Experience
- [ ] Fully responsive — tested on iPhone SE, iPhone 14, Samsung Galaxy
- [ ] CTA visible and tappable without scrolling
- [ ] Touch targets >= 44x44px
- [ ] No horizontal scrolling
- [ ] Forms use appropriate input types (email, tel, number)
- [ ] Keyboard doesn't cover form fields
- [ ] Pop-ups don't block content on mobile

### Tracking
- [ ] Analytics tracking installed and verified (GA4, Mixpanel, etc.)
- [ ] Conversion events configured for all key actions
- [ ] Heatmap/session recording tool active (Clarity, Hotjar)
- [ ] A/B test tool configured (if testing)
- [ ] UTM parameters tracked correctly

---

## Above the Fold

### The 5-Second Test
Can a first-time visitor answer these 3 questions in 5 seconds?
- [ ] What is this? (product/service identification)
- [ ] Who is it for? (target audience)
- [ ] Why should I care? (value proposition)

### Headline
- [ ] Headline communicates primary benefit (not feature)
- [ ] Headline matches the traffic source promise (message match)
- [ ] Headline is specific (includes numbers, outcomes, or timeframes)
- [ ] No jargon or industry-specific terms (unless audience expects it)

### CTA
- [ ] Primary CTA visible without scrolling
- [ ] CTA uses action verb ("Start Free Trial" not "Submit")
- [ ] CTA color contrasts with page background (most prominent element)
- [ ] Only ONE primary CTA above the fold (not 2-3 competing options)
- [ ] CTA text communicates what happens next
- [ ] Micro-copy under CTA reduces anxiety ("No credit card required")

### Visual Hierarchy
- [ ] Eye naturally flows: headline → supporting text → CTA
- [ ] Hero image/video supports the message (not decorative stock photo)
- [ ] No competing visual elements distracting from CTA
- [ ] White space used intentionally (not cluttered)

---

## Trust & Social Proof

### Above the Fold
- [ ] At least one trust element visible without scrolling
- [ ] Options: logo strip, rating, customer count, press mention

### Mid-Page
- [ ] Full testimonials with: real name, photo, title/company
- [ ] Case study excerpt with specific results (numbers, not adjectives)
- [ ] Video testimonial (if available — highest trust format)

### Near CTA
- [ ] Security indicators: SSL badge, payment logos, SOC 2
- [ ] Risk reversal: guarantee, free trial, cancel anytime
- [ ] Privacy assurance: "We never share your email"

### Red Flags (remove these)
- [ ] No anonymous testimonials ("A satisfied customer" = zero trust)
- [ ] No stock photos as "customer" photos
- [ ] No fabricated review counts or ratings
- [ ] No outdated dates (copyright "2023" in 2026)

---

## Forms & Conversion Flow

### Form Design
- [ ] Minimum fields necessary (each field reduces conversion ~5%)
- [ ] Labels above fields (not inside as placeholder text)
- [ ] Required fields clearly marked
- [ ] Inline validation (real-time error feedback)
- [ ] Error messages are helpful ("Email is invalid" not "Error")
- [ ] Auto-fill/autocomplete enabled
- [ ] Progress indicator for multi-step forms
- [ ] Submit button text is specific ("Get My Free Trial" not "Submit")

### Post-Conversion
- [ ] Thank-you page exists (not just inline "thanks" text)
- [ ] Thank-you page sets next expectations ("Check your email")
- [ ] Thank-you page fires conversion pixel
- [ ] Confirmation email sent immediately
- [ ] Redirect to onboarding (if applicable)

---

## Page Content

### Copy Quality
- [ ] Benefits before features
- [ ] Specific > vague ("Saves 12 hours/week" not "Saves time")
- [ ] Addresses top 3 objections directly
- [ ] Active voice ("We help you" not "You will be helped")
- [ ] Short paragraphs (2-3 sentences max)
- [ ] Scannable: headers, bullets, bold key phrases
- [ ] No quality gate violations (`kai-gate score`)

### Content Completeness
- [ ] Product/service clearly explained
- [ ] Pricing visible or path to pricing clear
- [ ] FAQ section addressing common questions
- [ ] Contact options available (chat, email, phone)
- [ ] Comparison to alternatives (if relevant)

---

## Navigation & UX

### Navigation
- [ ] Clear navigation (user knows where they are and how to get elsewhere)
- [ ] Important pages accessible within 2 clicks
- [ ] No dead-end pages (every page has a next action)
- [ ] Search functionality works (if present)
- [ ] Breadcrumbs on deep pages (for complex sites)

### User Flow
- [ ] Clear path from entry → information → conversion
- [ ] No unnecessary steps between interest and conversion
- [ ] Back button doesn't break the flow
- [ ] Session survives page refresh (form data not lost)
- [ ] Exit-intent strategy (popup, sticky CTA, or slide-in)

---

## Scoring

Rate each section 1-5:

| Section | Score (1-5) | Notes |
|---------|------------|-------|
| Technical Performance | | |
| Above the Fold | | |
| Trust & Social Proof | | |
| Forms & Conversion Flow | | |
| Page Content | | |
| Navigation & UX | | |
| **TOTAL** | **/30** | |

**Interpretation:**
- 25-30: Excellent — focus on A/B testing incremental improvements
- 18-24: Good — fix 2-3 specific gaps for significant lift
- 12-17: Needs work — prioritize above-fold + CTA + trust
- < 12: Critical — fundamental redesign needed before optimization
