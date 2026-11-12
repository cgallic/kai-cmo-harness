"""Fail-closed monthly dollar cap for Apify runs (per-result actors).

Fail-closed: if the ledger cannot be read or written, spending is refused. A
reservation is taken before a run at the published per-result price, and
settled with what Apify reports the run cost (``usageTotalUsd``). An unsettled
reservation keeps its estimate on the books, so unknown spend counts against
the cap until proven otherwise.

    APIFY_MONTHLY_CAP_USD   monthly cap (default 65)
    APIFY_BUDGET_DB         ledger path (default <data_dir>/ads/apify_budget.db)

    python -m scripts.ads.ad_library.budget status
"""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Published per-result prices (USD per 1,000 results), used for the pre-run reservation only.
# curious_coder/facebook-ads-library-scraper: $0.00075/ad + $0.00005/run start, checked on the actor 2026-11-12;
# finished runs settled about 10% under list (1,571 ads cost $1.11).
PRICE_PER_1K = {
    "curious_coder/facebook-ads-library-scraper": 0.75,
}


class BudgetExceeded(RuntimeError):
    """A reservation would cross the monthly cap."""


class BudgetUnavailable(RuntimeError):
    """The ledger is unusable. Fail-closed: refuse to spend."""


def default_cap() -> float:
    return float(os.environ.get("APIFY_MONTHLY_CAP_USD", "65"))


def default_db() -> Path:
    if os.environ.get("APIFY_BUDGET_DB"):
        return Path(os.environ["APIFY_BUDGET_DB"])
    from scripts.harness_config import get_config

    return get_config().data_dir / "ads" / "apify_budget.db"


def estimate_usd(actor: str, n_results: int) -> float:
    per_1k = PRICE_PER_1K.get(actor)
    if per_1k is None:
        raise BudgetUnavailable(f"no published price for actor {actor!r}; add it to PRICE_PER_1K rather than spending blind")
    return round(per_1k * n_results / 1000.0, 6)


def _cycle(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).strftime("%Y-%m")


@dataclass
class Reservation:
    budget: "ApifyBudget"
    rowid: int
    est_usd: float
    settled: bool = False

    def settle(self, actual_usd: float) -> None:
        self.budget._settle(self.rowid, actual_usd)
        self.settled = True

    def release(self) -> None:
        self.budget._settle(self.rowid, 0.0, released=True)
        self.settled = True


class ApifyBudget:
    def __init__(self, db_path: str | Path | None = None, cap_usd: float | None = None):
        self.db_path = Path(db_path) if db_path else default_db()
        self.cap_usd = float(cap_usd if cap_usd is not None else default_cap())
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, timeout=30)
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS spend (id INTEGER PRIMARY KEY AUTOINCREMENT, cycle TEXT NOT NULL, "
                "actor TEXT NOT NULL, note TEXT, est_usd REAL NOT NULL, actual_usd REAL, "
                "released INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, settled_at TEXT)"
            )
            self._conn.commit()
        except (OSError, sqlite3.Error) as exc:
            raise BudgetUnavailable(f"apify budget ledger unusable at {self.db_path}: {exc}") from exc

    def spent_usd(self, cycle: str | None = None) -> float:
        try:
            row = self._conn.execute(
                "SELECT COALESCE(SUM(COALESCE(actual_usd, est_usd)), 0) FROM spend WHERE cycle = ? AND released = 0",
                (cycle or _cycle(),),
            ).fetchone()
        except sqlite3.Error as exc:
            raise BudgetUnavailable(f"cannot read apify spend: {exc}") from exc
        return round(float(row[0] or 0.0), 6)

    def remaining_usd(self, cycle: str | None = None) -> float:
        return round(self.cap_usd - self.spent_usd(cycle), 6)

    @contextlib.contextmanager
    def reserve(self, actor: str, est_usd: float, note: str = ""):
        """Reserve ``est_usd`` before a run; raises BudgetExceeded if it does not fit under the cap."""
        cycle = _cycle()
        remaining = self.remaining_usd(cycle)
        if est_usd > remaining:
            raise BudgetExceeded(f"{actor}: needs ${est_usd:.2f}, only ${remaining:.2f} left of ${self.cap_usd:.2f} for {cycle}")
        try:
            cur = self._conn.execute(
                "INSERT INTO spend (cycle, actor, note, est_usd, created_at) VALUES (?,?,?,?,?)",
                (cycle, actor, note, float(est_usd), datetime.now(timezone.utc).isoformat()),
            )
            self._conn.commit()
        except sqlite3.Error as exc:
            raise BudgetUnavailable(f"cannot record apify reservation: {exc}") from exc
        res = Reservation(self, int(cur.lastrowid), float(est_usd))
        try:
            yield res
        except Exception:
            if not res.settled:
                res.release()
            raise

    def _settle(self, rowid: int, actual_usd: float, released: bool = False) -> None:
        try:
            self._conn.execute(
                "UPDATE spend SET actual_usd = ?, released = ?, settled_at = ? WHERE id = ?",
                (float(actual_usd), 1 if released else 0, datetime.now(timezone.utc).isoformat(), rowid),
            )
            self._conn.commit()
        except sqlite3.Error as exc:
            raise BudgetUnavailable(f"cannot settle apify spend row {rowid}: {exc}") from exc

    def status(self, cycle: str | None = None) -> dict:
        cycle = cycle or _cycle()
        spent = self.spent_usd(cycle)
        return {"cycle": cycle, "cap_usd": self.cap_usd, "spent_usd": spent, "remaining_usd": round(self.cap_usd - spent, 6)}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if (argv[:1] or ["status"])[0] != "status":
        print("usage: python -m scripts.ads.ad_library.budget status", file=sys.stderr)
        return 2
    print(json.dumps(ApifyBudget().status(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
