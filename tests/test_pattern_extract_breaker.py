"""EC-13: pattern_extract's Gemini circuit breaker persists across restarts.

Covers:
- breaker opens after max consecutive failures and blocks calls
- state (failure count + opened_at) survives a simulated process restart
- cooldown expiry closes an open breaker
- success clears persisted state
- corrupt/unreadable/unwritable state files degrade to in-memory, never crash
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.self_improvement.pattern_extract as pe
from scripts.self_improvement.pattern_extract import GeminiCircuitBreaker


def _make(state_path, max_failures=3, cooldown_seconds=3600, **kw):
    return GeminiCircuitBreaker(
        state_path=state_path,
        max_failures=max_failures,
        cooldown_seconds=cooldown_seconds,
        **kw,
    )


class TestBreakerBasics:
    def test_closed_below_threshold(self, tmp_path):
        breaker = _make(tmp_path / "breaker.json")
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open is False
        breaker.check()  # must not raise

    def test_opens_at_threshold_and_blocks(self, tmp_path):
        breaker = _make(tmp_path / "breaker.json")
        for _ in range(3):
            breaker.record_failure()
        assert breaker.is_open is True
        assert breaker.opened_at is not None
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            breaker.check()

    def test_success_resets_counter_and_state_file(self, tmp_path):
        path = tmp_path / "breaker.json"
        breaker = _make(path)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        assert breaker.consecutive_failures == 0
        assert breaker.opened_at is None
        # Persisted too — a restart starts clean
        assert json.loads(path.read_text())["consecutive_failures"] == 0
        assert _make(path).is_open is False


class TestBreakerPersistence:
    def test_state_survives_simulated_restart(self, tmp_path):
        path = tmp_path / "breaker.json"
        first = _make(path)
        for _ in range(3):
            first.record_failure()

        on_disk = json.loads(path.read_text())
        assert on_disk["consecutive_failures"] == 3
        assert on_disk["opened_at"]

        # "Restart": a brand-new instance reads the same file
        second = _make(path)
        assert second.consecutive_failures == 3
        assert second.opened_at is not None
        assert second.is_open is True
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            second.check()

    def test_cooldown_expiry_closes_breaker(self, tmp_path):
        path = tmp_path / "breaker.json"
        opened = datetime.now(timezone.utc) - timedelta(hours=2)
        path.write_text(json.dumps({
            "consecutive_failures": 3,
            "opened_at": opened.isoformat(),
        }))

        breaker = _make(path, cooldown_seconds=3600)  # 1h < 2h elapsed
        breaker.check()  # must not raise — cooldown expired, breaker closes
        assert breaker.is_open is False
        assert breaker.consecutive_failures == 0
        assert json.loads(path.read_text())["consecutive_failures"] == 0

    def test_open_within_cooldown_still_blocks(self, tmp_path):
        path = tmp_path / "breaker.json"
        opened = datetime.now(timezone.utc) - timedelta(minutes=5)
        path.write_text(json.dumps({
            "consecutive_failures": 3,
            "opened_at": opened.isoformat(),
        }))

        breaker = _make(path, cooldown_seconds=3600)
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            breaker.check()

    def test_open_state_without_opened_at_starts_cooldown_clock(self, tmp_path):
        path = tmp_path / "breaker.json"
        path.write_text(json.dumps({"consecutive_failures": 5}))

        breaker = _make(path)
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            breaker.check()
        # The clock started rather than leaving the breaker open forever
        assert breaker.opened_at is not None
        assert json.loads(path.read_text())["opened_at"]

    def test_naive_opened_at_treated_as_utc(self, tmp_path):
        path = tmp_path / "breaker.json"
        naive = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(tzinfo=None)
        path.write_text(json.dumps({
            "consecutive_failures": 3,
            "opened_at": naive.isoformat(),
        }))
        breaker = _make(path, cooldown_seconds=3600)
        breaker.check()  # cooldown expired — closes without raising
        assert breaker.is_open is False


class TestBreakerDegradation:
    def test_corrupt_state_file_falls_back_to_in_memory(self, tmp_path):
        path = tmp_path / "breaker.json"
        path.write_text("{not json")

        breaker = _make(path)  # must not raise
        assert breaker.consecutive_failures == 0
        assert breaker.is_open is False
        # And writes recover the file
        breaker.record_failure()
        assert json.loads(path.read_text())["consecutive_failures"] == 1

    def test_wrong_types_in_state_file_ignored(self, tmp_path):
        path = tmp_path / "breaker.json"
        path.write_text(json.dumps({
            "consecutive_failures": "many",
            "opened_at": "not-a-timestamp",
        }))
        breaker = _make(path)
        assert breaker.consecutive_failures == 0
        assert breaker.opened_at is None

    def test_unwritable_state_path_never_crashes(self, tmp_path):
        blocker = tmp_path / "blocker"
        blocker.write_text("i am a file, not a directory")
        breaker = _make(blocker / "sub" / "breaker.json")
        for _ in range(4):
            breaker.record_failure()  # _save fails silently every time
        # In-memory behavior still intact
        assert breaker.is_open is True
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            breaker.check()
        breaker.record_success()
        assert breaker.is_open is False

    def test_missing_state_file_starts_closed(self, tmp_path):
        breaker = _make(tmp_path / "nope" / "breaker.json")
        assert breaker.is_open is False
        breaker.check()


class TestBreakerConfig:
    def test_state_path_env_override(self, tmp_path, monkeypatch):
        target = tmp_path / "custom" / "breaker.json"
        monkeypatch.setenv("KAI_PATTERN_BREAKER_STATE_FILE", str(target))
        assert pe._breaker_state_path() == str(target)
        breaker = GeminiCircuitBreaker()
        assert breaker.state_path == str(target)

    def test_default_state_path_under_data_dir(self, monkeypatch):
        monkeypatch.delenv("KAI_PATTERN_BREAKER_STATE_FILE", raising=False)
        assert pe._breaker_state_path() == str(
            pe._CFG.data_dir / "learning" / "pattern_extract_breaker.json"
        )

    def test_cooldown_env_override_and_default(self, monkeypatch):
        monkeypatch.delenv("KAI_PATTERN_BREAKER_COOLDOWN_SECONDS", raising=False)
        assert pe._breaker_cooldown_seconds() == 3600.0
        monkeypatch.setenv("KAI_PATTERN_BREAKER_COOLDOWN_SECONDS", "120")
        assert pe._breaker_cooldown_seconds() == 120.0
        monkeypatch.setenv("KAI_PATTERN_BREAKER_COOLDOWN_SECONDS", "garbage")
        assert pe._breaker_cooldown_seconds() == 3600.0


class TestGeminiWiring:
    def test_gemini_call_blocked_while_breaker_open(self, tmp_path, monkeypatch):
        breaker = _make(tmp_path / "breaker.json")
        for _ in range(3):
            breaker.record_failure()
        monkeypatch.setattr(pe, "_BREAKER", breaker)
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            pe._gemini("hello")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
