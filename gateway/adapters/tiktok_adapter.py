"""
TikTok adapter.

Wraps scripts/tiktok modules for programmatic access.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure scripts path is available
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / "scripts" / ".env")


class TikTokAdapter:
    """Adapter for TikTok CLI commands."""

    def _format_number(self, n: int) -> str:
        """Format number with K/M suffix."""
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)

    async def get_stats(self, client: Optional[str] = None) -> Dict[str, Any]:
        """Get TikTok account statistics."""
        from scripts.tiktok.scraper import TikTokScraper
        from scripts.tiktok.winner_detection import WinnerDetector

        scraper = TikTokScraper()
        detector = WinnerDetector()

        # Get accounts
        accounts = await scraper.get_active_accounts()

        # Filter by client if specified
        if client:
            accounts = [a for a in accounts if a.get('display_name') == client]

        # Get overall stats
        stats = await detector.calculate_account_stats()

        # Get winner counts
        all_winners = await detector.get_winners(limit=1000)
        pending = [w for w in all_winners if w.get("analysis_status") == "pending"]
        completed = [w for w in all_winners if w.get("analysis_status") == "completed"]

        return {
            "accounts": [
                {
                    "username": acc.get("username"),
                    "total_videos": acc.get("total_videos", 0),
                    "last_scraped": acc.get("last_scraped_at", "")[:10] if acc.get("last_scraped_at") else None,
                }
                for acc in accounts
            ],
            "active_accounts": len(accounts),
            "performance": {
                "lookback_days": stats.get("lookback_days"),
                "total_videos": stats.get("total_videos"),
                "avg_views": self._format_number(int(stats.get("avg_views", 0))),
                "avg_engagement": f"{stats.get('avg_engagement', 0) * 100:.2f}%",
            },
            "winners": {
                "total": len(all_winners),
                "pending": len(pending),
                "analyzed": len(completed),
                "by_tier": {
                    f"tier_{tier}": len([w for w in all_winners if w.get("winner_tier") == tier])
                    for tier in [4, 3, 2, 1]
                }
            }
        }

    async def get_videos(
        self,
        client: Optional[str] = None,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent videos."""
        from scripts.tiktok.metrics import MetricsTracker

        tracker = MetricsTracker()
        videos = await tracker.get_recent_videos(days_old=days, limit=limit)

        return [
            {
                "tiktok_id": v.get("tiktok_id"),
                "status": v.get("status"),
                "play_count": v.get("play_count", 0),
                "play_count_formatted": self._format_number(v.get("play_count", 0)),
                "engagement_rate": f"{(v.get('engagement_rate', 0) or 0) * 100:.1f}%",
                "posted_at": v.get("posted_at", "")[:10] if v.get("posted_at") else None,
            }
            for v in videos
        ]

    async def get_winners(
        self,
        client: Optional[str] = None,
        limit: int = 20,
        tier: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get winner videos."""
        from scripts.tiktok.winner_detection import WinnerDetector

        detector = WinnerDetector()
        winners = await detector.get_winners(
            analysis_status=status,
            tier=tier,
            limit=limit,
            include_video=True
        )

        return [
            {
                "winner_tier": w.get("winner_tier"),
                "analysis_status": w.get("analysis_status"),
                "detection_reason": w.get("detection_reason"),
                "detected_at": w.get("detected_at", "")[:10] if w.get("detected_at") else None,
                "video": {
                    "play_count": w.get("tiktok_videos", {}).get("play_count", 0) if w.get("tiktok_videos") else 0,
                }
            }
            for w in winners
        ]

    async def run_scrape(
        self,
        client: Optional[str] = None,
        max_videos: int = 200,
        full_history: bool = False,
        min_duration: int = 0
    ) -> Dict[str, Any]:
        """Run TikTok scrape."""
        from scripts.tiktok.scraper import TikTokScraper

        scraper = TikTokScraper()
        result = await scraper.run_full_scrape(
            max_videos=max_videos,
            force_full_history=full_history,
            min_duration=min_duration
        )

        return {
            "accounts_scraped": result.get("accounts_scraped", 0),
            "total_fetched": result.get("total_fetched", 0),
            "inserted": result.get("inserted", 0),
            "errors": len(result.get("errors", [])),
            "error_details": result.get("errors", [])[:5],
        }

    async def run_detect_winners(
        self,
        client: Optional[str] = None,
        lookback_days: int = 30,
        video_age_limit: int = 72
    ) -> Dict[str, Any]:
        """Run winner detection."""
        from scripts.tiktok.winner_detection import WinnerDetector

        detector = WinnerDetector()

        # Get account stats first
        stats = await detector.calculate_account_stats()

        # Detect winners
        winners = await detector.detect_winners(
            lookback_days=lookback_days,
            video_age_limit=video_age_limit
        )

        return {
            "account_stats": {
                "lookback_days": stats.get("lookback_days"),
                "avg_views": self._format_number(int(stats.get("avg_views", 0))),
                "avg_engagement": f"{stats.get('avg_engagement', 0) * 100:.2f}%",
                "total_videos": stats.get("total_videos"),
            },
            "new_winners": len(winners),
            "winners": [
                {
                    "tier": w.get("tier"),
                    "tiktok_id": w.get("tiktok_id"),
                    "reason": w.get("reason"),
                    "value": self._format_number(int(w.get("value", 0))),
                }
                for w in winners
            ]
        }

    async def run_generate(
        self,
        client: Optional[str] = None,
        num_batches: int = 2,
        posts_per_batch: int = 4
    ) -> Dict[str, Any]:
        """Generate TikTok posts using Claude AI."""
        from scripts.tiktok.post_generator import TikTokPostGenerator

        generator = TikTokPostGenerator()

        # Determine clients
        clients = [client] if client else None

        results = await generator.generate_all_clients_daily(
            num_batches=num_batches,
            posts_per_batch=posts_per_batch,
            clients=clients
        )

        return {
            "clients_processed": len(results),
            "results": {
                client_id: {
                    "success": not result.startswith("ERROR"),
                    "word_count": len(result.split()) if not result.startswith("ERROR") else 0,
                    "error": result if result.startswith("ERROR") else None,
                }
                for client_id, result in results.items()
            }
        }

    async def run_metrics_update(
        self,
        client: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Update video metrics."""
        from scripts.tiktok.metrics import MetricsTracker

        tracker = MetricsTracker()

        # Get videos needing updates
        videos = await tracker.get_videos_needing_update(limit=limit)

        if not videos:
            return {
                "videos_due": 0,
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "message": "No videos need updating"
            }

        # Process updates
        result = await tracker.process_batch_update(videos)

        return {
            "videos_due": len(videos),
            "processed": result.get("processed", 0),
            "succeeded": result.get("succeeded", 0),
            "failed": result.get("failed", 0),
        }

    async def search_videos(self, query: str, count: int = 20) -> List[Dict[str, Any]]:
        """Search TikTok videos."""
        from scripts.tiktok.scraper import TikTokScraper

        scraper = TikTokScraper()
        videos = await scraper.search_videos(query, count=count)

        return [
            {
                "tiktok_id": v.get("tiktok_id"),
                "description": (v.get("description") or "")[:200],
                "play_count": v.get("play_count", 0),
                "play_count_formatted": self._format_number(v.get("play_count", 0)),
                "like_count": v.get("like_count", 0),
                "engagement_rate": f"{(v.get('engagement_rate', 0) or 0) * 100:.1f}%",
                "video_url": v.get("video_url"),
                "duration": v.get("duration"),
            }
            for v in videos
        ]

    async def get_comments(self, video_id: str, count: int = 50) -> List[Dict[str, Any]]:
        """Get video comments."""
        from scripts.tiktok.scraper import TikTokScraper

        scraper = TikTokScraper()
        return await scraper.get_comments(video_id, count=count)

    async def transcribe_video(self, video_id: str) -> Dict[str, Any]:
        """Transcribe a single video."""
        from scripts.tiktok.extraction import ContentExtractor

        extractor = ContentExtractor()
        transcript = await extractor.transcribe_single(video_id)

        if transcript:
            return {
                "video_id": video_id,
                "transcript": transcript,
                "word_count": len(transcript.split()),
            }
        return {
            "video_id": video_id,
            "transcript": None,
            "error": "No speech detected or download failed",
        }

    def list_clients(self) -> List[Dict[str, Any]]:
        """List available TikTok clients for post generation."""
        try:
            from scripts.tiktok.post_generator import TikTokPostGenerator
            generator = TikTokPostGenerator()
            return generator.list_clients()
        except ImportError:
            return []
