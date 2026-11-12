"""Ad Library survival scan: collect -> Jev tags -> survival lifts -> brief scores.

Read-only competitive research. Nothing here touches a live ad account.
Doctrine: ``knowledge/playbooks/ad-library-survival-scan.md``.
Skill: ``/kai-ad-library-scan``.

    python -m scripts.ads.ad_library.collect_ads      ...  # Apify / ScrapeCreators / Graph API
    python -m scripts.ads.ad_library.tag_ads          ...  # Jev visible-feature tags + days_running
    python -m scripts.ads.ad_library.survival_report  ...  # advertiser-weighted survivor lifts
    python -m scripts.ads.ad_library.score_briefs     ...  # 0-100 brief score, computed in code
"""
