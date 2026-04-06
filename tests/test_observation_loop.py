"""Tests for anomaly detection and proposal generation — the observation loop."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.harness_config as harness_config
from kai.runtime.loader import load_workspace_profile
from kai.execution.anomaly_proposals import (
    detect_traffic_anomalies,
    create_proposals_from_anomalies,
)


# ---------------------------------------------------------------------------
# Config isolation
# ---------------------------------------------------------------------------


def _with_config(yaml_content: str):
    @contextlib.contextmanager
    def ctx():
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(textwrap.dedent(yaml_content))
            handle.flush()
            previous = os.environ.get("CMO_CONFIG_PATH")
            os.environ["CMO_CONFIG_PATH"] = handle.name
            harness_config._config = None
            load_workspace_profile.cache_clear()
            try:
                yield Path(handle.name)
            finally:
                if previous is None:
                    os.environ.pop("CMO_CONFIG_PATH", None)
                else:
                    os.environ["CMO_CONFIG_PATH"] = previous
                harness_config._config = None
                load_workspace_profile.cache_clear()
                try:
                    os.unlink(handle.name)
                except OSError:
                    pass

    return ctx()


YAML_CONTENT = """
workspace:
  id: "kai-test"
  name: "Kai Test Loop"
products: []
"""


# ---------------------------------------------------------------------------
# Tests: Anomaly detection
# ---------------------------------------------------------------------------


class TestAnomalyDetection:
    def test_detects_traffic_drop(self):
        previous = [
            {"metric_name": "sessions", "dimension": "/services", "value": 1000},
        ]
        current = [
            {"metric_name": "sessions", "dimension": "/services", "value": 700},
        ]
        anomalies = detect_traffic_anomalies(current, previous)
        assert len(anomalies) == 1
        assert anomalies[0]["anomaly_type"] == "traffic_drop"
        assert anomalies[0]["page"] == "/services"
        assert anomalies[0]["pct_change"] < -20

    def test_no_anomaly_for_small_change(self):
        previous = [
            {"metric_name": "sessions", "dimension": "/home", "value": 1000},
        ]
        current = [
            {"metric_name": "sessions", "dimension": "/home", "value": 900},
        ]
        anomalies = detect_traffic_anomalies(current, previous)
        assert len(anomalies) == 0  # 10% drop is below 20% threshold

    def test_detects_conversion_drop(self):
        previous = [
            {"metric_name": "conversions", "dimension": "/pricing", "value": 50},
        ]
        current = [
            {"metric_name": "conversions", "dimension": "/pricing", "value": 30},
        ]
        anomalies = detect_traffic_anomalies(current, previous)
        assert len(anomalies) == 1
        assert anomalies[0]["anomaly_type"] == "conversion_drop"

    def test_detects_bounce_rate_spike(self):
        previous = [
            {"metric_name": "bounce_rate", "dimension": "/blog", "value": 40},
        ]
        current = [
            {"metric_name": "bounce_rate", "dimension": "/blog", "value": 60},
        ]
        anomalies = detect_traffic_anomalies(current, previous)
        assert len(anomalies) == 1
        assert anomalies[0]["anomaly_type"] == "bounce_rate_spike"

    def test_multiple_anomalies(self):
        previous = [
            {"metric_name": "sessions", "dimension": "/a", "value": 1000},
            {"metric_name": "sessions", "dimension": "/b", "value": 500},
            {"metric_name": "conversions", "dimension": "/c", "value": 100},
        ]
        current = [
            {"metric_name": "sessions", "dimension": "/a", "value": 600},  # -40%
            {"metric_name": "sessions", "dimension": "/b", "value": 450},  # -10% (ok)
            {"metric_name": "conversions", "dimension": "/c", "value": 50},  # -50%
        ]
        anomalies = detect_traffic_anomalies(current, previous)
        assert len(anomalies) == 2
        types = {a["anomaly_type"] for a in anomalies}
        assert types == {"traffic_drop", "conversion_drop"}

    def test_empty_data(self):
        assert detect_traffic_anomalies([], []) == []

    def test_custom_thresholds(self):
        previous = [
            {"metric_name": "sessions", "dimension": "/", "value": 100},
        ]
        current = [
            {"metric_name": "sessions", "dimension": "/", "value": 90},  # -10%
        ]
        # Default threshold (20%) — no anomaly
        assert len(detect_traffic_anomalies(current, previous)) == 0
        # Custom threshold (5%) — anomaly detected
        anomalies = detect_traffic_anomalies(
            current, previous, thresholds={"traffic_drop_pct": 5.0}
        )
        assert len(anomalies) == 1


# ---------------------------------------------------------------------------
# Tests: Proposal generation
# ---------------------------------------------------------------------------


class TestProposalGeneration:
    def test_creates_proposals_from_anomalies(self):
        anomalies = [
            {
                "anomaly_type": "traffic_drop",
                "page": "/services",
                "pct_change": -30.0,
            },
        ]
        proposals = create_proposals_from_anomalies(
            anomalies, brand_id="testbrand", auto_propose=False
        )
        assert len(proposals) == 1
        assert proposals[0]["channel"] == "website"
        assert proposals[0]["action_type"] == "update_metadata"
        assert proposals[0]["brand_id"] == "testbrand"
        assert "/services" in proposals[0]["intent"]

    def test_conversion_drop_proposal(self):
        anomalies = [
            {"anomaly_type": "conversion_drop", "page": "/pricing", "pct_change": -20.0},
        ]
        proposals = create_proposals_from_anomalies(
            anomalies, brand_id="testbrand", auto_propose=False
        )
        assert proposals[0]["action_type"] == "update_page_copy"
        assert proposals[0]["risk_tier"] == "medium"

    def test_auto_propose_with_action_store(self, tmp_path):
        with _with_config(YAML_CONTENT):
            from kai.runtime.actions import ActionStore

            store = ActionStore(base_dir=tmp_path / "runtime", auto_approve_low_risk=True)

            anomalies = [
                {"anomaly_type": "traffic_drop", "page": "/about", "pct_change": -25.0},
            ]

            proposals = create_proposals_from_anomalies(
                anomalies,
                brand_id="testbrand",
                action_store=store,
                auto_propose=True,
            )

            assert len(proposals) == 1
            assert "action_id" in proposals[0]
            assert proposals[0]["approval_state"] == "auto_approved"

            # Verify it's actually in the store
            stored = store.get_action(proposals[0]["action_id"])
            assert stored is not None
            assert stored["intent"].startswith("Page /about")

    def test_unknown_anomaly_type_skipped(self):
        anomalies = [
            {"anomaly_type": "unknown_type", "page": "/", "pct_change": -50.0},
        ]
        proposals = create_proposals_from_anomalies(
            anomalies, brand_id="testbrand", auto_propose=False
        )
        assert len(proposals) == 0
