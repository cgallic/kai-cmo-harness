---
issue: 3
title: "📊 SEO Check-In Report: 9 Sites, 14 Days Post-Deploy (March 29)"
state: OPEN
labels: []
assignees: []
created: 2026-03-29T13:00:40Z
updated: 2026-03-29T13:00:40Z
author: cgallic
url: https://github.com/cgallic/kai-cmo-harness/issues/3
comments_count: 0
reactions_count: 0
---

# #3: 📊 SEO Check-In Report: 9 Sites, 14 Days Post-Deploy (March 29)

## Description

## Executive Summary

**Period:** March 15-29, 2026 (14 days post-deploy)  
**Sites Audited:** 9  
**Total Clicks:** 98  
**Total Impressions:** 1,882  
**Average CTR:** 5.2%

---

## 🚨 CRITICAL Issues

### Starrs Party: Not in GSC
**Issue:** [#7](https://github.com/cgallic/starrs_party/issues/7)  
**Status:** ❌ BLOCKING  
**Impact:** Zero organic visibility  
**Timeline:** Fix by March 31

---

## 🔴 High Priority Issues

### KaiCalls

1. **Comparison pages not indexed** — [#195](https://github.com/cgallic/kai_calls/issues/195)
   - /compare/human-receptionist (expected 208 impr)
   - /compare/goodcall (expected 62 impr)
   - Status: Normal 2-6 week indexing delay

2. **FAQ schema for Featured Snippets** — [#196](https://github.com/cgallic/kai_calls/issues/196)
   - 53 impressions, 0% CTR on zero-click query
   - Add FAQ schema to capture snippet

3. **/about meta description** — [#197](https://github.com/cgallic/kai_calls/issues/197)
   - 101 impressions, pos 2.8, **0% CTR**
   - Quick win: rewrite meta description

### ABP

4. **Homepage CTR too low** — [#15](https://github.com/cgallic/amazingbackyardparties/issues/15)
   - 1.84% CTR (should be 5-10%)
   - Rewrite meta description

### ConnorGallic

5. **/resources not indexed** — [#104](https://github.com/cgallic/connorgallic.com/issues/104)
   - Expected 21 impressions, getting 0
   - Submit to GSC for indexing

---

## ✅ What's Working

- **Brand queries crushing it:**
  - KaiCalls: 21 clicks, 44.68% CTR, pos 1.7
  - BuildWithKai: 5 clicks, 100% CTR, pos 1.0
  - VocalScribe: 7 clicks, 43.75% CTR, pos 1.0

- **ABP geo-targeted pages:**
  - /pa/Cochranton/tables-chairs: 2 clicks, 66.67% CTR
  - Local search working

---

## 📅 Next Check-In

**Date:** April 12, 2026 (28 days post-deploy)

**Goals:**
- ✅ Starrs Party in GSC
- ✅ Compare pages indexed
- ✅ CTR improvements on fixed pages

---

## Related

- Master Topo Map: `content/kaicalls-seo/MASTER-TOPO-MAP.md`
- Full GSC data: `/opt/cmo-analytics/scripts/gsc.py`
- March 15 deploy tracking: MEMORY.md
