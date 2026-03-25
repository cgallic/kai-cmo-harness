"""
A/B Test Tracker — Real variant tracking with statistical significance.

Tracks content and ad variants, records performance metrics,
calculates statistical significance, and declares winners.

Usage:
    tracker = ABTracker()
    test_id = tracker.create_test("headline-test", variants=["pain-hook", "data-hook", "social-hook"])
    tracker.record_result(test_id, "pain-hook", impressions=1000, clicks=45, conversions=8)
    tracker.record_result(test_id, "data-hook", impressions=1000, clicks=62, conversions=12)
    report = tracker.analyze(test_id)
    # report.winner = "data-hook", report.confidence = 0.94, report.significant = False (need 0.95)
"""

import json
import math
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


KAI_DIR = Path.home() / ".kai-marketing"
DB_PATH = KAI_DIR / "ab_tests.db"


@dataclass
class VariantResult:
    """Metrics for a single variant."""
    variant: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    ctr: float = 0.0
    cvr: float = 0.0
    cpa: float = 0.0
    roas: float = 0.0

    def compute_rates(self, spend: float = 0.0):
        self.ctr = (self.clicks / self.impressions * 100) if self.impressions > 0 else 0
        self.cvr = (self.conversions / self.clicks * 100) if self.clicks > 0 else 0
        self.cpa = (spend / self.conversions) if self.conversions > 0 else float('inf')
        self.roas = (self.revenue / spend) if spend > 0 else 0


@dataclass
class TestReport:
    """Analysis result for an A/B test."""
    test_id: str
    test_name: str
    metric: str
    variants: list  # list of VariantResult
    winner: Optional[str] = None
    confidence: float = 0.0
    significant: bool = False
    sample_needed: int = 0
    recommendation: str = ""
    status: str = "running"  # running | significant | insufficient_data


class ABTracker:
    """SQLite-backed A/B test tracker with statistical significance."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
        self._ensure_schema()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _ensure_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS ab_tests (
                test_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                metric TEXT NOT NULL DEFAULT 'cvr',
                variants_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                winner TEXT,
                confidence REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata_json TEXT
            );

            CREATE TABLE IF NOT EXISTS ab_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL REFERENCES ab_tests(test_id),
                variant TEXT NOT NULL,
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0.0,
                spend REAL DEFAULT 0.0,
                recorded_at TEXT NOT NULL,
                source TEXT,
                UNIQUE(test_id, variant, recorded_at)
            );

            CREATE INDEX IF NOT EXISTS idx_results_test ON ab_results(test_id);
        """)

    def create_test(
        self,
        name: str,
        variants: list[str],
        metric: str = "cvr",
        metadata: dict = None,
    ) -> str:
        """Create a new A/B test. Returns test_id."""
        test_id = f"ab-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """INSERT INTO ab_tests (test_id, name, metric, variants_json, status, created_at, updated_at, metadata_json)
               VALUES (?, ?, ?, ?, 'running', ?, ?, ?)""",
            (test_id, name, metric, json.dumps(variants), now, now, json.dumps(metadata or {})),
        )
        self.conn.commit()
        return test_id

    def record_result(
        self,
        test_id: str,
        variant: str,
        impressions: int = 0,
        clicks: int = 0,
        conversions: int = 0,
        revenue: float = 0.0,
        spend: float = 0.0,
        source: str = "manual",
    ):
        """Record performance data for a variant. Cumulative — call repeatedly."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Upsert: add to today's record
        existing = self.conn.execute(
            "SELECT id, impressions, clicks, conversions, revenue, spend FROM ab_results WHERE test_id=? AND variant=? AND recorded_at=?",
            (test_id, variant, now),
        ).fetchone()

        if existing:
            self.conn.execute(
                """UPDATE ab_results SET
                   impressions=impressions+?, clicks=clicks+?, conversions=conversions+?,
                   revenue=revenue+?, spend=spend+?
                   WHERE id=?""",
                (impressions, clicks, conversions, revenue, spend, existing["id"]),
            )
        else:
            self.conn.execute(
                """INSERT INTO ab_results (test_id, variant, impressions, clicks, conversions, revenue, spend, recorded_at, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (test_id, variant, impressions, clicks, conversions, revenue, spend, now, source),
            )
        self.conn.execute("UPDATE ab_tests SET updated_at=? WHERE test_id=?", (now, test_id))
        self.conn.commit()

    def analyze(self, test_id: str) -> TestReport:
        """Analyze an A/B test for statistical significance."""
        test = self.conn.execute("SELECT * FROM ab_tests WHERE test_id=?", (test_id,)).fetchone()
        if not test:
            raise ValueError(f"Test {test_id} not found")

        variants = json.loads(test["variants_json"])
        metric = test["metric"]

        # Aggregate results per variant
        variant_results = []
        total_spend = {}
        for v in variants:
            rows = self.conn.execute(
                "SELECT SUM(impressions) as imp, SUM(clicks) as clk, SUM(conversions) as conv, SUM(revenue) as rev, SUM(spend) as sp FROM ab_results WHERE test_id=? AND variant=?",
                (test_id, v),
            ).fetchone()
            vr = VariantResult(
                variant=v,
                impressions=rows["imp"] or 0,
                clicks=rows["clk"] or 0,
                conversions=rows["conv"] or 0,
                revenue=rows["rev"] or 0.0,
            )
            sp = rows["sp"] or 0.0
            total_spend[v] = sp
            vr.compute_rates(sp)
            variant_results.append(vr)

        # Find best and worst by metric
        def _get_metric(vr: VariantResult) -> float:
            return {"ctr": vr.ctr, "cvr": vr.cvr, "roas": vr.roas, "cpa": -vr.cpa}.get(metric, vr.cvr)

        variant_results.sort(key=_get_metric, reverse=True)
        best = variant_results[0]
        second = variant_results[1] if len(variant_results) > 1 else None

        # Statistical significance via two-proportion z-test
        confidence = 0.0
        significant = False
        sample_needed = 0

        if second and best.impressions > 0 and second.impressions > 0:
            if metric in ("ctr", "cvr"):
                # Use conversion/click data for proportions
                if metric == "ctr":
                    n1, x1 = best.impressions, best.clicks
                    n2, x2 = second.impressions, second.clicks
                else:
                    n1, x1 = best.clicks or best.impressions, best.conversions
                    n2, x2 = second.clicks or second.impressions, second.conversions

                p1 = x1 / n1 if n1 > 0 else 0
                p2 = x2 / n2 if n2 > 0 else 0
                p_pool = (x1 + x2) / (n1 + n2) if (n1 + n2) > 0 else 0

                if p_pool > 0 and p_pool < 1:
                    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
                    if se > 0:
                        z = abs(p1 - p2) / se
                        # Approximate p-value from z-score (one-tailed)
                        confidence = _z_to_confidence(z)
                        significant = confidence >= 0.95

                # Sample size needed for significance (if not yet significant)
                if not significant and p1 > 0 and p2 > 0:
                    effect_size = abs(p1 - p2)
                    if effect_size > 0:
                        # Simplified sample size formula for 95% confidence, 80% power
                        sample_needed = int(math.ceil(
                            2 * ((1.96 + 0.84) ** 2) * p_pool * (1 - p_pool) / (effect_size ** 2)
                        ))

        # Build recommendation
        if not second:
            recommendation = "Only one variant — add a comparison variant."
            status = "insufficient_data"
        elif best.impressions < 100 or second.impressions < 100:
            recommendation = f"Need more data. Min 100 impressions per variant. Current: {best.variant}={best.impressions}, {second.variant}={second.impressions}."
            status = "insufficient_data"
        elif significant:
            lift = ((_get_metric(best) - _get_metric(second)) / abs(_get_metric(second)) * 100) if _get_metric(second) != 0 else 0
            recommendation = f"WINNER: '{best.variant}' ({confidence:.1%} confidence, {lift:+.1f}% lift over '{second.variant}'). Kill the loser."
            status = "significant"
        else:
            recommendation = f"Not yet significant ({confidence:.1%}). Need ~{sample_needed} impressions per variant. Keep running."
            status = "running"

        # Update test status in DB
        winner = best.variant if significant else None
        self.conn.execute(
            "UPDATE ab_tests SET status=?, winner=?, confidence=?, updated_at=? WHERE test_id=?",
            (status, winner, confidence, datetime.now(timezone.utc).isoformat(), test_id),
        )
        self.conn.commit()

        return TestReport(
            test_id=test_id,
            test_name=test["name"],
            metric=metric,
            variants=variant_results,
            winner=winner,
            confidence=confidence,
            significant=significant,
            sample_needed=sample_needed,
            recommendation=recommendation,
            status=status,
        )

    def list_tests(self, status: str = None) -> list[dict]:
        """List all A/B tests, optionally filtered by status."""
        if status:
            rows = self.conn.execute("SELECT * FROM ab_tests WHERE status=? ORDER BY updated_at DESC", (status,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM ab_tests ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

    def format_report(self, report: TestReport) -> str:
        """Format a test report as a readable string."""
        lines = [
            f"A/B TEST: {report.test_name} ({report.test_id})",
            f"Metric: {report.metric.upper()}  |  Status: {report.status.upper()}",
            "",
            f"{'Variant':<20} {'Impressions':>12} {'Clicks':>10} {'CTR':>8} {'Conv':>8} {'CVR':>8}",
            "-" * 70,
        ]
        for vr in report.variants:
            marker = " *" if report.winner == vr.variant else ""
            lines.append(
                f"{vr.variant:<20} {vr.impressions:>12,} {vr.clicks:>10,} {vr.ctr:>7.2f}% {vr.conversions:>8,} {vr.cvr:>7.2f}%{marker}"
            )
        lines.extend([
            "",
            f"Confidence: {report.confidence:.1%}  |  Significant: {'YES' if report.significant else 'NO'}",
            f"Recommendation: {report.recommendation}",
        ])
        return "\n".join(lines)


def _z_to_confidence(z: float) -> float:
    """Approximate cumulative normal distribution (one-tailed) from z-score."""
    # Abramowitz and Stegun approximation
    if z < 0:
        return 1 - _z_to_confidence(-z)
    t = 1 / (1 + 0.2316419 * z)
    d = 0.3989422804014327  # 1/sqrt(2*pi)
    p = d * math.exp(-z * z / 2) * (
        0.3193815 * t - 0.3565638 * t**2 + 1.781478 * t**3
        - 1.821256 * t**4 + 1.330274 * t**5
    )
    return 1 - p
