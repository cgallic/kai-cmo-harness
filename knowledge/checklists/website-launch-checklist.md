# Website Launch Checklist

> **Use when:** Launching a new website, redesigning an existing site, or migrating to a new domain/platform.

---

## Pre-Launch (1-2 weeks before)

### Content
- [ ] All pages have unique title tags (under 60 characters, keyword-first)
- [ ] All pages have unique meta descriptions (150-160 characters)
- [ ] All images have descriptive alt text
- [ ] No placeholder text ("Lorem ipsum", "Coming soon", "TODO")
- [ ] Contact information is correct (phone, email, address)
- [ ] Legal pages present: Privacy Policy, Terms of Service, Cookie Policy
- [ ] Copyright year is current
- [ ] All links work (no 404s — run a crawl with Screaming Frog or `kai-gate`)
- [ ] Content passes quality gate (`kai-gate score` on all key pages)

### SEO
- [ ] XML sitemap generated and accessible at /sitemap.xml
- [ ] robots.txt configured correctly (not blocking important pages)
- [ ] Canonical tags set on all pages (prevent duplicate content)
- [ ] 301 redirects set up for all old URLs (if migration)
- [ ] Schema markup implemented (Organization, LocalBusiness, Product, FAQ)
- [ ] Google Search Console verified for new domain
- [ ] Google Analytics / GA4 installed and tracking
- [ ] Open Graph tags set for social sharing (og:title, og:description, og:image)
- [ ] Twitter card tags set

### Technical
- [ ] SSL certificate installed (HTTPS everywhere)
- [ ] Page speed: Core Web Vitals pass (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- [ ] Mobile responsive — tested on iPhone SE, iPhone 14, iPad, Android
- [ ] Cross-browser tested (Chrome, Safari, Firefox, Edge)
- [ ] Forms submit correctly and send to the right inbox
- [ ] 404 page customized (helpful, not default server error)
- [ ] Favicon uploaded (visible in browser tab)
- [ ] Print stylesheet or print-friendly pages (if applicable)
- [ ] No console errors in browser DevTools
- [ ] CDN configured (if applicable)
- [ ] Caching headers set for static assets
- [ ] Gzip/Brotli compression enabled

### Conversion
- [ ] Primary CTA visible above the fold on every key page
- [ ] Phone number clickable on mobile (`tel:` link)
- [ ] Email address clickable (`mailto:` link)
- [ ] Form fields use correct input types (email, tel, number)
- [ ] Thank-you/confirmation pages exist for all forms
- [ ] Conversion tracking pixels installed and verified (GA4, Meta, Google Ads)
- [ ] Chat widget or contact option accessible on every page
- [ ] Exit-intent popup configured (if using)

### Security
- [ ] Admin URLs not publicly accessible (or behind auth)
- [ ] Default credentials changed (WordPress admin, CMS logins)
- [ ] File upload functionality secured (if applicable)
- [ ] Input fields sanitized against XSS and SQL injection
- [ ] CORS headers configured correctly
- [ ] Security headers set (Content-Security-Policy, X-Frame-Options, etc.)
- [ ] Backup system configured and tested

---

## Launch Day

- [ ] DNS updated to point to new server/host
- [ ] SSL certificate works on new domain
- [ ] All pages load correctly (manual spot-check of top 10 pages)
- [ ] Forms still submit correctly after DNS change
- [ ] Google Search Console: submit sitemap
- [ ] Google Analytics: verify real-time tracking shows activity
- [ ] Social media profiles updated with new URL (if changed)
- [ ] Email signatures updated with new URL
- [ ] Team notified of launch
- [ ] Monitor server performance for first 2 hours

---

## Post-Launch (First Week)

- [ ] Run full site crawl (Screaming Frog) — check for 404s, broken links, missing meta
- [ ] Check Google Search Console for crawl errors
- [ ] Verify all conversion tracking is firing (GA4, ad pixels)
- [ ] Monitor page speed (PageSpeed Insights) — compare to pre-launch baseline
- [ ] Check all forms by submitting test entries
- [ ] Review server logs for errors (500s, 404s)
- [ ] Monitor search rankings for key terms (GSC → Performance)
- [ ] Collect team and user feedback on the new site
- [ ] Fix any issues found — prioritize by conversion impact

---

## Migration-Specific (Old Site → New Site)

- [ ] Full URL mapping: every old URL has a 301 redirect to the new equivalent
- [ ] No redirect chains (A → B → C should be A → C directly)
- [ ] Old sitemap replaced with new sitemap
- [ ] Backlinks checked — any high-value inbound links still resolve correctly?
- [ ] Google Search Console: "Change of Address" tool used (if domain change)
- [ ] Monitor organic traffic for 30 days post-migration (expect a temporary dip)
- [ ] Keep old hosting active for 6 months (in case of redirect issues)
