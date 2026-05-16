from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from kai.memory.schemas import (
    CreatorPerformanceEntry,
    CreatorPerformanceMemory,
    load_memory_layer,
    save_memory_layer,
)


def test_creator_performance_layer_round_trips_via_storage(tmp_path: Path) -> None:
    layer = CreatorPerformanceMemory(
        business_id="brand_123",
        entries=[
            CreatorPerformanceEntry(
                creator_id="creator_alpha",
                platform="tiktok_shop",
                campaign_id="camp_001",
                spend_usd=250.0,
                attributed_revenue_usd=800.0,
                attributed_orders=19,
                affiliate_clicks=230,
                affiliate_conversions=24,
                gmv_usd=920.0,
                disclosure_compliant=True,
                usage_rights_expires_at="2099-01-01T00:00:00+00:00",
                whitelisting_enabled=True,
            )
        ],
    )

    save_memory_layer(layer, str(tmp_path))
    loaded = load_memory_layer("brand_123", "creator_performance", str(tmp_path))

    assert isinstance(loaded, CreatorPerformanceMemory)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].creator_id == "creator_alpha"
    assert loaded.entries[0].platform == "tiktok_shop"
    assert loaded.entries[0].roas == 3.2


def test_creator_performance_queries_flag_disclosure_and_rights_expiry() -> None:
    soon = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    later = (datetime.now(timezone.utc) + timedelta(days=45)).isoformat()
    layer = CreatorPerformanceMemory(
        business_id="brand_123",
        entries=[
            CreatorPerformanceEntry(
                creator_id="creator_alpha",
                platform="youtube_shopping",
                disclosure_compliant=False,
                usage_rights_expires_at=soon,
                spend_usd=100.0,
                attributed_revenue_usd=150.0,
            ),
            CreatorPerformanceEntry(
                creator_id="creator_beta",
                platform="amazon_influencer",
                disclosure_compliant=True,
                usage_rights_expires_at=later,
                spend_usd=120.0,
                attributed_revenue_usd=420.0,
            ),
        ],
    )

    non_compliant = layer.get_non_compliant_disclosures()
    expiring = layer.get_rights_expiring_within(days=14)
    top_roas = layer.get_top_creators_by_roas(limit=1)

    assert len(non_compliant) == 1
    assert non_compliant[0].creator_id == "creator_alpha"
    assert len(expiring) == 1
    assert expiring[0].creator_id == "creator_alpha"
    assert len(top_roas) == 1
    assert top_roas[0].creator_id == "creator_beta"
