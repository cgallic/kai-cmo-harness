"""Load, extend and save the shared audit dataset (audit-data.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.audit.data_sources import (
    AuditDataset,
    AuditMetric,
    AuditSource,
    DataGap,
    SourceTier,
    utc_now_iso,
)


def load_or_create(out_dir: Path, *, mode: str, url: str, name: str) -> AuditDataset:
    path = out_dir / "audit-data.json"
    if not path.exists():
        return AuditDataset(audit_mode=mode, target_url=url, firm_name=name, workflow="local-audit")
    data = json.loads(path.read_text(encoding="utf-8"))
    dataset = AuditDataset(
        audit_mode=data.get("audit_mode", mode),
        target_url=data.get("target_url", url),
        firm_name=data.get("firm_name", name),
        workflow=data.get("workflow", "local-audit"),
        generated_at=data.get("generated_at", utc_now_iso()),
        raw_artifacts_dir=data.get("raw_artifacts_dir", "raw"),
    )
    for s in data.get("sources", []):
        dataset.sources.append(AuditSource(**s))
    for m in data.get("metrics", []):
        dataset.metrics.append(AuditMetric(**m))
    for g in data.get("data_gaps", []):
        dataset.data_gaps.append(DataGap(**g))
    return dataset


def replace_source(dataset: AuditDataset, source: AuditSource) -> AuditSource:
    """Re-running a pull replaces its source and that source's metrics."""
    dataset.sources = [s for s in dataset.sources if s.source_id != source.source_id]
    dataset.metrics = [m for m in dataset.metrics if m.source_id != source.source_id]
    dataset.sources.append(source)
    return source


def api_source(source_id: str, name: str, used_for: str, endpoint: str, artifact: str) -> AuditSource:
    return AuditSource(
        source_id=source_id,
        name=name,
        tier=SourceTier.CONNECTED.value,
        access="api",
        retrieved_at=utc_now_iso(),
        used_for=used_for,
        source_url=endpoint,
        artifact_path=artifact,
    )


def observed_source(source_id: str, name: str, used_for: str, url: str, artifact: str) -> AuditSource:
    return AuditSource(
        source_id=source_id,
        name=name,
        tier=SourceTier.PUBLIC_OBSERVED.value,
        access="external",
        retrieved_at=utc_now_iso(),
        used_for=used_for,
        source_url=url,
        artifact_path=artifact,
    )


def metric(dataset: AuditDataset, source: AuditSource, metric_id: str, label: str, value: Any, unit: str, notes: str = "") -> None:
    dataset.add_metric(
        AuditMetric(
            metric_id=metric_id,
            label=label,
            value=value,
            unit=unit,
            source_id=source.source_id,
            source_tier=source.tier,
            notes=notes,
        )
    )


def gap(dataset: AuditDataset, missing: str, blocks: str, sales: str, onboarding: str, access: str = "") -> None:
    if any(g.missing_source == missing for g in dataset.data_gaps):
        return
    dataset.add_gap(DataGap(missing, blocks, sales, onboarding, access))


ARTIFACT_ROOT: Path | None = None  # set by CLIs so artifact paths are relative to the audit folder


def write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    if ARTIFACT_ROOT is not None:
        try:
            return path.resolve().relative_to(Path(ARTIFACT_ROOT).resolve()).as_posix()
        except ValueError:
            pass
    return path.as_posix()
