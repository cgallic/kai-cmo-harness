"""Existing-page SEO: refresh queue, portfolio triage, and fix-outcome tracking.

The harness's measured wins came from improving pages that already rank on
established properties, not from new sites. These modules point the work there
and grade every fix against Search Console.

- ``gsc_data``         load a query x page export (CSV/JSON) or pull it from the API
- ``striking_distance`` rank pages by click upside (CTR gaps + positions 8-20)
- ``portfolio``         classify properties as invest / maintain / freeze
- ``refresh_tracker``   record a fix with its baseline, grade it 28 days later
"""
