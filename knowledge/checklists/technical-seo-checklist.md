# SEO Expert Technical SEO Security Checklist

A comprehensive technical SEO security checklist extracted from SEO Expert's consulting sessions. This checklist focuses on preventing hacks, securing WordPress installations, and handling recovery from security breaches.

---

## Pre-Hack Prevention

### Query Parameter Security
- [ ] **Return 404 for unknown query parameters** - If a query parameter doesn't exist in your site, return 404, NEVER return 200
  - *Why it matters*: Returning 200 for unknown parameters means attackers can create infinite URLs that self-canonicalize, bloating your index without even hacking you
  - *Implementation*: Configure in htaccess to define which query parameters are valid; all others return 404
  - *Common mistake*: Allowing any query parameter to return 200 with self-referencing canonicals

- [ ] **Define a standardized query parameter set** - Maintain a whitelist of valid parameters (e.g., search, pagination)
  - *Why it matters*: Like your standardized plugin set, having a defined parameter set prevents exploitation
  - *Implementation*: In htaccess, specify which parameters return results vs which return 404

- [ ] **Use hash values instead of query parameters for search** - Implement search using JavaScript hash values (#search=query)
  - *Why it matters*: Hash URLs don't create new indexable URLs, preventing search parameter exploitation
  - *Alternative*: Use Google Programmable Search Engine as embedded internal search

### Content Security Policy (CSP)
- [ ] **Implement Content Security Policy response headers** - Define where the site can load resources from
  - *Why it matters*: Even if hacked, CSP prevents injected scripts from executing or loading external resources
  - *What it blocks*: Click-jacking attempts, DDoS attack vectors, unauthorized script injection
  - *Implementation*: Configure as HTTP response headers specifying allowed sources for scripts, images, styles

- [ ] **Prevent hot-linking** - CSP implementation automatically prevents hot-linking
  - *Why it matters*: Stops others from using your server resources and protects bandwidth

### htaccess Security
- [ ] **Protect htaccess file from public access** - Block all external access to .htaccess
  - *Why it matters*: htaccess files control server behavior; exposure reveals security configurations
  - *Implementation*: Add rules to deny access to htaccess files

- [ ] **Protect functions.php** - Block external access to WordPress functions.php
  - *Why it matters*: This file contains database credentials; hackers target it to breach your database
  - *Common attack*: Hackers access functions.php to find database addresses and inject malicious data

- [ ] **Add security lines to htaccess** - Include standard WordPress security rules
  - *What to include*: File access restrictions, redirect rules for hacked URL patterns, parameter handling

### Plugin Security
- [ ] **Maintain a standardized plugin set** - Use the same approved plugins across all sites
  - *Why it matters*: Each plugin is a potential vulnerability; standardization reduces attack surface
  - *Best practice*: Document your approved plugin list and enforce it across all client sites

- [ ] **Delete unused plugins completely** - Don't just deactivate, fully delete
  - *Why it matters*: Even deactivated plugins carry hacking risk; they still exist in the file system
  - *Common mistake*: Deactivating instead of deleting plugins you no longer need

- [ ] **Avoid unnecessary security plugins** - You don't need extra plugins for security
  - *Why it matters*: Security plugins themselves can be attack vectors; proper configuration is better
  - *Better approach*: 2FA + protected htaccess + protected functions.php = sufficient protection

- [ ] **Enable regular automatic updates** - Keep WordPress, plugins, and themes updated
  - *Why it matters*: Outdated software is the primary attack vector for WordPress hacks
  - *Trade-off*: May occasionally break things, but security benefits outweigh inconvenience

### Authentication Security
- [ ] **Require two-factor authentication (2FA)** - All admin accounts must use 2FA
  - *Why it matters*: Prevents brute force attacks even if passwords are compromised
  - *Implementation*: Enforce for all client sites as part of standard security protocol

### Directory Security
- [ ] **Prevent directory browsing** - Block access to directory listings (wp-includes, etc.)
  - *Why it matters*: Directory browsing reveals your file structure and available attack vectors
  - *Verification*: Test by accessing /wp-includes/ - should return 403 Forbidden
  - *Implementation*: Add "Options -Indexes" to htaccess

### Robots.txt Security
- [ ] **Consider hosting robots.txt on separate server** - Place robots.txt on different infrastructure
  - *Why it matters*: Even if main site is hacked, robots.txt remains protected
  - *Benefit*: Can disallow hacked URL patterns without hackers modifying it

---

## Post-Hack Recovery (Japanese Keyword Hack)

### Identification
- [ ] **Check for Japanese/foreign characters in URLs** - Review Search Console for unusual character sets
  - *Signs*: Japanese, Chinese, or Cyrillic characters in indexed URLs
  - *Common pattern*: shop.php paths, random parameter strings, unfamiliar subfolders

- [ ] **Check for pattern-based hacked URLs** - Look for common prefixes/suffixes in hacked URLs
  - *Why it matters*: Pattern identification enables bulk redirect rules
  - *Common patterns*: Query parameters starting with specific letters, subfolder patterns

- [ ] **Analyze log files for sitemap injection** - Check if hackers submitted their own sitemaps
  - *Why it matters*: Hackers often create and submit sitemaps to get URLs indexed faster
  - *Action*: Search logs for any XML file requests you didn't create

### Cleanup Process
- [ ] **Redirect hacked URLs to homepage** - Use pattern-based redirects in htaccess
  - *Important*: Don't redirect to itself (creates canonicalization to hacked URL)
  - *Correct*: Redirect to actual homepage or appropriate canonical
  - *For multilingual*: Redirect Spanish hacked URLs to Spanish homepage, etc.

- [ ] **Use URL Removal Tool with patterns** - Submit removal requests using URL patterns
  - *Why it matters*: Bulk removal is faster than individual URL requests
  - *Example*: Remove all URLs starting with "/shop.php" or containing specific parameters

- [ ] **Keep query parameters temporarily crawlable** - Don't disallow while redirecting
  - *Why it matters*: Search engines need to crawl URLs to process redirects and removal requests
  - *After recovery*: Once URLs drop from index, then disallow parameters

- [ ] **Check for residual indexed pages** - Use site: search to find remaining hacked URLs
  - *Why it matters*: Search Console doesn't show all indexed URLs
  - *Implementation*: Regular site:domain.com searches for unusual content

### Recovery Monitoring
- [ ] **Monitor crawl delay and frequency** - Track time between sitemap update and crawl
  - *Why it matters*: Decreased crawl delay indicates Google is re-evaluating your site positively
  - *Tool*: Python script comparing sitemap last-modified dates with log file crawl times

- [ ] **Track URL count stabilization** - Watch for indexed URL count to normalize
  - *Why it matters*: 500K+ hacked URLs take time to drop; monitor progress weekly
  - *Expectation*: May take months to fully clean index of hacked URLs

---

## Tools Reference

| Tool | Purpose |
|------|---------|
| **Google Search Console URL Removal Tool** | Bulk remove hacked URLs using patterns |
| **Log File Analyzer** | Check crawl patterns, identify injected sitemaps |
| **Python Sitemap/Crawl Delay Script** | Compare publication time vs crawl time |
| **Screaming Frog** | Crawl site to identify 200 responses on invalid parameters |
| **htaccess Generators** | Create security rules for WordPress |

---

## Common Mistakes Summary

| Mistake | Impact | Fix |
|---------|--------|-----|
| Returning 200 for unknown parameters | Infinite URL generation without hacking | Return 404 for undefined parameters |
| Deactivating instead of deleting plugins | Vulnerable code remains on server | Fully delete unused plugins |
| Self-referencing redirects on hacked URLs | Validates hacked URLs as canonical | Redirect to actual homepage |
| Disallowing parameters while cleaning | Prevents redirect processing | Keep crawlable until URLs drop |
| No 2FA on admin accounts | Vulnerable to brute force | Require 2FA for all admins |
| Exposing functions.php | Database credentials leaked | Block access via htaccess |

---

## Implementation Priority

### Immediate (Before Any Hack)
1. Implement 2FA on all admin accounts
2. Protect htaccess and functions.php
3. Return 404 for unknown query parameters
4. Prevent directory browsing

### Short-term (Within 30 Days)
5. Implement Content Security Policy
6. Standardize plugin set across all sites
7. Delete all unused plugins
8. Enable automatic updates

### Ongoing
- Regular log file reviews
- Monitor Search Console for unusual URLs
- Test query parameter responses quarterly
- Update standardized plugin list as needed

---

*Source: SEO Expert Tugberk Gubur SEO Consulting Sessions, 2025*
