"""KaiCalls new-business outreach data pipeline.

Pulls new business registrations from open-data sources (FL Sunbiz first),
filters for outreach-ready records (RA-trap filter, ICP skew), enriches via
Google Places (signal-only — ToS) + Apollo (stored phone), scores P1/P2/P3,
dedupes across runs, and writes a CSV ready for the multi-touch postcard +
email + human-call sequence.

See README.md for usage. Implements §11 of:
  brain/wiki/guides/kaicalls-new-business-formation-outreach.md
"""
__all__ = ["sunbiz_fl", "ra_blocklist", "enrich", "dedupe", "pipeline"]
