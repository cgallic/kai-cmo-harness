"""Tests for local evidence-pack export from runtime runs and actions."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.harness_config as harness_config
from kai.provenance import EvidencePackExporter
from kai.runtime.actions import ActionStore
from kai.runtime.loader import load_workspace_profile
from kai.runtime.store import RuntimeStore


def _with_config(yaml_content: str):
    @contextlib.contextmanager
    def ctx():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
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
  name: "Kai Test Runtime"

products:
  - id: glowcraft
    name: "GlowCraft"
    description: "DTC skincare ecommerce brand."
"""


def test_export_run_evidence_pack_includes_artifacts_mandates_and_results():
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "runtime"
            runtime_store = RuntimeStore(base_dir=base_dir)
            action_store = ActionStore(base_dir=base_dir)
            exporter = EvidencePackExporter(
                runtime_store=runtime_store,
                action_store=action_store,
                output_dir=base_dir / "evidence_packs",
            )

            run = runtime_store.start_run(
                {
                    "intent": "Run audit for proof export",
                    "workflow": "agent-ready-audit",
                    "brand_id": "glowcraft",
                    "surface": "local",
                }
            )
            run_id = run["run_id"]

            runtime_store.record_artifact(
                {
                    "artifact_type": "audit_findings",
                    "brand_id": "glowcraft",
                    "workflow": "agent-ready-audit",
                    "data": {
                        "sources": [{"source": "fixture://audit-findings", "type": "fixture"}],
                        "claim_cards": [{"claim": "llms.txt missing", "severity": "high"}],
                    },
                },
                run_id=run_id,
            )
            runtime_store.complete_run(
                run_id,
                status="approved",
                outputs={
                    "data_gaps": ["Merchant Center feed not connected"],
                    "gate_report": {"score": 13, "status": "pass"},
                    "connector_health": {"google_merchant_center": "missing"},
                },
            )

            action = action_store.propose_action(
                {
                    "brand_id": "glowcraft",
                    "channel": "website",
                    "action_type": "update_page_copy",
                    "intent": "Patch offer clarity",
                    "source_run_id": run_id,
                    "risk_tier": "high",
                    "mandate_id": "mandate_abc123",
                    "evidence": [{"source": "fixture://action-proof", "url": "https://example.com/proof"}],
                }
            )
            action_store.approve_action(action["action_id"])
            action_store.mark_executing(action["action_id"])
            action_store.mark_completed(action["action_id"], {"status": "success", "changed": True})

            exported = exporter.export_run(run_id)
            pack = exported["evidence_pack"]

            assert Path(exported["json_path"]).exists()
            assert Path(exported["markdown_path"]).exists()
            assert pack["entity"]["type"] == "run"
            assert pack["entity"]["id"] == run_id
            assert "mandate_abc123" in pack["mandate_ids"]
            assert "Merchant Center feed not connected" in pack["data_gaps"]
            assert any(link.get("path") for link in pack["artifact_links"])
            assert any(row.get("source") == "fixture://action-proof" for row in pack["sources"])
            assert pack["action_result"][0]["status"] == "success"


def test_export_action_evidence_pack_surfaces_data_gaps():
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "runtime"
            action_store = ActionStore(base_dir=base_dir)
            exporter = EvidencePackExporter(
                runtime_store=RuntimeStore(base_dir=base_dir),
                action_store=action_store,
                output_dir=base_dir / "evidence_packs",
            )

            action = action_store.propose_action(
                {
                    "brand_id": "glowcraft",
                    "channel": "paid_media",
                    "action_type": "adjust_budget",
                    "intent": "Increase spend without evidence",
                    "risk_tier": "high",
                }
            )

            exported = exporter.export_action(action["action_id"])
            pack = exported["evidence_pack"]

            assert Path(exported["json_path"]).exists()
            assert Path(exported["markdown_path"]).exists()
            assert pack["entity"]["type"] == "action"
            assert pack["approval_state"] == "pending"
            assert any("has no evidence sources" in gap for gap in pack["data_gaps"])
            assert any("missing mandate_id" in gap for gap in pack["data_gaps"])
            assert pack["sources"] == []
