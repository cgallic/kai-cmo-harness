"""Local evidence-pack exporter for run/action proof bundles."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from kai.runtime.actions import ActionStore, get_default_action_store
from kai.runtime.store import RuntimeStore, get_default_runtime_store


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _dump_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return value.model_dump()
    return value


def _json_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=_dump_value)


def _normalize_source_item(item: Any) -> Optional[dict]:
    if isinstance(item, str):
        text = item.strip()
        if not text:
            return None
        return {"source": text}
    if isinstance(item, dict):
        source = item.get("source") or item.get("url") or item.get("name") or item.get("id")
        if not source:
            return None
        normalized = {"source": str(source)}
        for key in ("url", "type", "note"):
            if key in item and item[key]:
                normalized[key] = item[key]
        return normalized
    return None


def _unique_dict_rows(rows: Iterable[dict]) -> List[dict]:
    seen = set()
    deduped: List[dict] = []
    for row in rows:
        key = json.dumps(row, sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _collect_sources(run: Optional[dict], artifacts: List[dict], actions: List[dict]) -> List[dict]:
    collected: List[dict] = []

    run_sources = ((run or {}).get("outputs") or {}).get("sources")
    if isinstance(run_sources, list):
        for source_item in run_sources:
            normalized = _normalize_source_item(source_item)
            if normalized:
                collected.append(normalized)

    for artifact in artifacts:
        data = artifact.get("data") or {}
        artifact_sources = data.get("sources")
        if isinstance(artifact_sources, list):
            for source_item in artifact_sources:
                normalized = _normalize_source_item(source_item)
                if normalized:
                    collected.append(normalized)

    for action in actions:
        for evidence_item in action.get("evidence") or []:
            normalized = _normalize_source_item(evidence_item)
            if normalized:
                collected.append(normalized)

    return _unique_dict_rows(collected)


def _collect_claim_cards(run: Optional[dict], artifacts: List[dict], actions: List[dict]) -> List[dict]:
    cards: List[dict] = []

    run_claim_cards = ((run or {}).get("outputs") or {}).get("claim_cards")
    if isinstance(run_claim_cards, list):
        for card in run_claim_cards:
            if isinstance(card, dict):
                cards.append(card)

    for artifact in artifacts:
        artifact_cards = (artifact.get("data") or {}).get("claim_cards")
        if isinstance(artifact_cards, list):
            for card in artifact_cards:
                if isinstance(card, dict):
                    cards.append(card)

    for action in actions:
        summary = action.get("result_summary")
        if isinstance(summary, dict) and summary.get("claim_cards"):
            action_cards = summary.get("claim_cards")
            if isinstance(action_cards, list):
                for card in action_cards:
                    if isinstance(card, dict):
                        cards.append(card)

    return cards


def _collect_data_gaps(run: Optional[dict], artifacts: List[dict], actions: List[dict]) -> List[str]:
    gaps: List[str] = []
    run_outputs = (run or {}).get("outputs") or {}
    run_gaps = run_outputs.get("data_gaps")
    if isinstance(run_gaps, list):
        gaps.extend(str(item) for item in run_gaps if str(item).strip())

    for artifact in artifacts:
        artifact_gaps = (artifact.get("data") or {}).get("data_gaps")
        if isinstance(artifact_gaps, list):
            gaps.extend(str(item) for item in artifact_gaps if str(item).strip())

    for action in actions:
        if not action.get("evidence"):
            gaps.append(f"Action {action.get('action_id', '<unknown>')} has no evidence sources")
        if action.get("risk_tier") == "high" and not action.get("mandate_id"):
            gaps.append(f"High-risk action {action.get('action_id', '<unknown>')} is missing mandate_id")

    seen = set()
    unique: List[str] = []
    for gap in gaps:
        if gap in seen:
            continue
        seen.add(gap)
        unique.append(gap)
    return unique


def _collect_mandate_ids(run: Optional[dict], actions: List[dict]) -> List[str]:
    mandate_ids: List[str] = []

    run_outputs = (run or {}).get("outputs") or {}
    output_mandates = run_outputs.get("mandate_ids")
    if isinstance(output_mandates, list):
        mandate_ids.extend(str(item) for item in output_mandates if str(item).strip())
    elif isinstance(run_outputs.get("mandate_id"), str):
        mandate_ids.append(run_outputs["mandate_id"])

    for action in actions:
        mandate_id = action.get("mandate_id")
        if isinstance(mandate_id, str) and mandate_id.strip():
            mandate_ids.append(mandate_id)

    return sorted(set(mandate_ids))


def _collect_policy_results(run: Optional[dict], artifacts: List[dict], actions: List[dict]) -> List[dict]:
    results: List[dict] = []
    run_outputs = (run or {}).get("outputs") or {}
    run_policy = run_outputs.get("policy_result")
    if isinstance(run_policy, dict):
        results.append(run_policy)

    for artifact in artifacts:
        artifact_policy = (artifact.get("data") or {}).get("policy_result")
        if isinstance(artifact_policy, dict):
            results.append(artifact_policy)

    for action in actions:
        action_policy = action.get("policy_result")
        if isinstance(action_policy, dict):
            results.append(action_policy)
    return results


def _collect_quality_gates(run: Optional[dict], artifacts: List[dict]) -> List[dict]:
    gates: List[dict] = []
    run_outputs = (run or {}).get("outputs") or {}
    gate_report = run_outputs.get("gate_report")
    if isinstance(gate_report, dict):
        gates.append(gate_report)

    for artifact in artifacts:
        artifact_gate = (artifact.get("data") or {}).get("gate_report")
        if isinstance(artifact_gate, dict):
            gates.append(artifact_gate)
    return gates


def _artifact_file_path(runtime_store: RuntimeStore, artifact_id: str) -> Optional[str]:
    path = runtime_store.artifacts_dir / f"{artifact_id}.json"
    if not path.exists():
        return None
    return str(path.resolve())


def _artifact_links(runtime_store: RuntimeStore, artifacts: List[dict]) -> List[dict]:
    links: List[dict] = []
    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id")
        if not artifact_id:
            continue
        file_path = _artifact_file_path(runtime_store, str(artifact_id))
        links.append(
            {
                "artifact_id": artifact_id,
                "artifact_type": artifact.get("artifact_type"),
                "path": file_path,
            }
        )
    return links


def _linked_actions_for_run(action_store: ActionStore, run_id: str) -> List[dict]:
    linked: List[dict] = []
    for action in action_store.list_actions(limit=1000):
        if action.get("source_run_id") == run_id:
            linked.append(action)
    linked.sort(key=lambda row: row.get("updated_at", ""))
    return linked


def build_run_evidence_pack(
    *,
    runtime_store: RuntimeStore,
    run_bundle: dict,
    linked_actions: List[dict],
) -> dict:
    run = run_bundle.get("run") or {}
    artifacts = run_bundle.get("artifacts") or []

    action_result = [row.get("result_summary") for row in linked_actions if row.get("result_summary") is not None]
    rollback_references = [
        row.get("rollback_reference") for row in linked_actions if row.get("rollback_reference") is not None
    ]

    payload = {
        "evidence_pack_id": f"evidence_{uuid.uuid4().hex[:12]}",
        "generated_at": _utc_now(),
        "entity": {"type": "run", "id": run.get("run_id")},
        "run_metadata": {
            "run_id": run.get("run_id"),
            "workflow": run.get("workflow"),
            "brand_id": run.get("brand_id"),
            "surface": run.get("surface"),
            "status": run.get("status"),
            "started_at": run.get("started_at"),
            "completed_at": run.get("completed_at"),
        },
        "artifact_ids": [artifact.get("artifact_id") for artifact in artifacts if artifact.get("artifact_id")],
        "artifact_links": _artifact_links(runtime_store, artifacts),
        "sources": _collect_sources(run, artifacts, linked_actions),
        "data_gaps": _collect_data_gaps(run, artifacts, linked_actions),
        "claim_cards": _collect_claim_cards(run, artifacts, linked_actions),
        "quality_gates": _collect_quality_gates(run, artifacts),
        "policy_results": _collect_policy_results(run, artifacts, linked_actions),
        "mandate_ids": _collect_mandate_ids(run, linked_actions),
        "approval_state": (run_bundle.get("approval") or {}).get("status") or run.get("status"),
        "connector_health": ((run.get("outputs") or {}).get("connector_health") or run.get("metadata", {}).get("connector_health")),
        "action_result": action_result if action_result else (run.get("outputs") or {}).get("action_result"),
        "rollback_reference": rollback_references if rollback_references else (run.get("outputs") or {}).get("rollback_reference"),
        "lineage_run_ids": run.get("ancestor_run_ids", []),
    }
    return payload


def build_action_evidence_pack(*, action: dict) -> dict:
    policy_result = action.get("policy_result") if isinstance(action.get("policy_result"), dict) else {}
    data_gaps: List[str] = []
    if not action.get("evidence"):
        data_gaps.append(f"Action {action.get('action_id', '<unknown>')} has no evidence sources")
    if action.get("risk_tier") == "high" and not action.get("mandate_id"):
        data_gaps.append(f"High-risk action {action.get('action_id', '<unknown>')} is missing mandate_id")

    evidence_sources = []
    for item in action.get("evidence") or []:
        normalized = _normalize_source_item(item)
        if normalized:
            evidence_sources.append(normalized)

    payload = {
        "evidence_pack_id": f"evidence_{uuid.uuid4().hex[:12]}",
        "generated_at": _utc_now(),
        "entity": {"type": "action", "id": action.get("action_id")},
        "run_metadata": {
            "source_run_id": action.get("source_run_id"),
            "brand_id": action.get("brand_id"),
            "channel": action.get("channel"),
            "action_type": action.get("action_type"),
            "risk_tier": action.get("risk_tier"),
            "created_at": action.get("created_at"),
            "executed_at": action.get("executed_at"),
        },
        "artifact_ids": [],
        "artifact_links": [],
        "sources": _unique_dict_rows(evidence_sources),
        "data_gaps": data_gaps,
        "claim_cards": [],
        "quality_gates": [],
        "policy_results": [policy_result] if policy_result else [],
        "mandate_ids": [action["mandate_id"]] if action.get("mandate_id") else [],
        "approval_state": action.get("approval_state"),
        "connector_health": (action.get("metadata") or {}).get("connector_health"),
        "action_result": action.get("result_summary"),
        "rollback_reference": action.get("rollback_reference"),
        "lineage_run_ids": [],
    }
    return payload


def render_evidence_pack_markdown(pack: dict) -> str:
    entity = pack.get("entity") or {}
    lines = [
        f"# Evidence Pack: {entity.get('type', 'unknown')} `{entity.get('id', '<unknown>')}`",
        "",
        f"- Generated at: `{pack.get('generated_at')}`",
        f"- Approval state: `{pack.get('approval_state')}`",
        "",
        "## Run metadata",
        "",
        "```json",
        _json_dump(pack.get("run_metadata") or {}),
        "```",
        "",
        "## Artifact links",
        "",
    ]

    artifact_links = pack.get("artifact_links") or []
    if artifact_links:
        for link in artifact_links:
            lines.append(
                f"- `{link.get('artifact_id')}` ({link.get('artifact_type')}) -> `{link.get('path') or 'missing'}'"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Sources",
            "",
        ]
    )
    sources = pack.get("sources") or []
    if sources:
        for source in sources:
            lines.append(f"- `{source.get('source')}`")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Data gaps",
            "",
        ]
    )
    data_gaps = pack.get("data_gaps") or []
    if data_gaps:
        for gap in data_gaps:
            lines.append(f"- {gap}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Action and policy",
            "",
            "```json",
            _json_dump(
                {
                    "mandate_ids": pack.get("mandate_ids"),
                    "policy_results": pack.get("policy_results"),
                    "quality_gates": pack.get("quality_gates"),
                    "connector_health": pack.get("connector_health"),
                    "action_result": pack.get("action_result"),
                    "rollback_reference": pack.get("rollback_reference"),
                }
            ),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


class EvidencePackExporter:
    """Export run/action evidence packs into local JSON and Markdown files."""

    def __init__(
        self,
        *,
        runtime_store: Optional[RuntimeStore] = None,
        action_store: Optional[ActionStore] = None,
        output_dir: Optional[Path] = None,
    ):
        self.runtime_store = runtime_store or get_default_runtime_store()
        self.action_store = action_store or get_default_action_store()
        default_output = self.runtime_store.base_dir / "evidence_packs"
        self.output_dir = _ensure_dir(Path(output_dir or default_output))

    @classmethod
    def default(cls) -> "EvidencePackExporter":
        return cls()

    def export_run(self, run_id: str, *, output_stem: Optional[str] = None) -> dict:
        run_bundle = self.runtime_store.get_run_bundle(run_id)
        if not run_bundle:
            raise KeyError(f"Run not found: {run_id}")

        linked_actions = _linked_actions_for_run(self.action_store, run_id)
        pack = build_run_evidence_pack(
            runtime_store=self.runtime_store,
            run_bundle=run_bundle,
            linked_actions=linked_actions,
        )
        return self._write_pack(pack, output_stem or f"{run_id}-evidence-pack")

    def export_action(self, action_id: str, *, output_stem: Optional[str] = None) -> dict:
        action = self.action_store.get_action(action_id)
        if not action:
            raise KeyError(f"Action not found: {action_id}")
        pack = build_action_evidence_pack(action=action)
        return self._write_pack(pack, output_stem or f"{action_id}-evidence-pack")

    def _write_pack(self, pack: dict, output_stem: str) -> dict:
        safe_stem = output_stem.replace(" ", "-")
        json_path = self.output_dir / f"{safe_stem}.json"
        markdown_path = self.output_dir / f"{safe_stem}.md"

        json_path.write_text(_json_dump(pack), encoding="utf-8")
        markdown_path.write_text(render_evidence_pack_markdown(pack), encoding="utf-8")

        return {
            "evidence_pack": pack,
            "json_path": str(json_path.resolve()),
            "markdown_path": str(markdown_path.resolve()),
        }
