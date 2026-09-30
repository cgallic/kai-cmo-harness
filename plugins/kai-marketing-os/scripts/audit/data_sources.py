"""Source-first Kai data contract.

This module is the upstream guardrail for Kai workflows that need measured
business, marketing, search, crawl, or conversion data. Audits consume this
dataset, but the contract is broader: no downstream workflow should turn model
inference into a metric.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class AuditMode(str, Enum):
    SALES_EXTERNAL = "sales_external"
    ONBOARDING_CONNECTED = "onboarding_connected"
    INTERNAL_DEMO = "internal_demo"


class SourceTier(str, Enum):
    CONNECTED = "connected"
    PUBLIC_OBSERVED = "public_observed"
    USER_PROVIDED = "user_provided"
    THIRD_PARTY_ESTIMATE = "third_party_estimate"
    INFERRED = "inferred"
    MISSING_DATA = "missing_data"


SCORE_ELIGIBLE_TIERS = {
    SourceTier.CONNECTED.value,
    SourceTier.PUBLIC_OBSERVED.value,
    SourceTier.USER_PROVIDED.value,
    SourceTier.THIRD_PARTY_ESTIMATE.value,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class AuditSource:
    source_id: str
    name: str
    tier: str
    access: str
    retrieved_at: str
    used_for: str
    source_url: str = ""
    artifact_path: str = ""
    status: str = "ok"
    notes: str = ""

    def validate_for_metric(self) -> None:
        if self.tier not in SCORE_ELIGIBLE_TIERS:
            raise ValueError(f"Source {self.source_id} is not score eligible: {self.tier}")
        if not self.name:
            raise ValueError("Metric source must have a name")
        if not self.retrieved_at:
            raise ValueError("Metric source must have retrieved_at")
        if not self.source_url and not self.artifact_path:
            raise ValueError("Metric source must have source_url or artifact_path")


@dataclass
class AuditMetric:
    metric_id: str
    label: str
    value: Any
    unit: str
    source_id: str
    source_tier: str
    confidence: str = "high"
    score_eligible: bool = True
    notes: str = ""

    def validate(self, sources: dict[str, AuditSource]) -> None:
        if not self.metric_id:
            raise ValueError("Metric must have metric_id")
        if not self.unit:
            raise ValueError(f"Metric {self.metric_id} must have unit")
        if not self.source_id:
            raise ValueError(f"Metric {self.metric_id} must have source_id")
        if not self.source_tier:
            raise ValueError(f"Metric {self.metric_id} must have source_tier")
        if not self.confidence:
            raise ValueError(f"Metric {self.metric_id} must have confidence")
        source = sources.get(self.source_id)
        if source is None:
            raise ValueError(f"Metric {self.metric_id} references unknown source: {self.source_id}")
        if self.score_eligible:
            source.validate_for_metric()
            if self.source_tier != source.tier:
                raise ValueError(
                    f"Metric {self.metric_id} tier {self.source_tier} does not match source {source.tier}"
                )
        elif self.source_tier in SCORE_ELIGIBLE_TIERS:
            raise ValueError(f"Metric {self.metric_id} has eligible tier but score_eligible=false")


@dataclass
class DataGap:
    missing_source: str
    blocks: str
    sales_version_handling: str
    onboarding_version_handling: str
    required_access: str = ""


@dataclass
class AuditDataset:
    audit_mode: str
    target_url: str
    firm_name: str = ""
    workflow: str = "all"
    generated_at: str = field(default_factory=utc_now_iso)
    sources: list[AuditSource] = field(default_factory=list)
    metrics: list[AuditMetric] = field(default_factory=list)
    data_gaps: list[DataGap] = field(default_factory=list)
    raw_artifacts_dir: str = "raw"

    def source_map(self) -> dict[str, AuditSource]:
        return {source.source_id: source for source in self.sources}

    def add_source(self, source: AuditSource) -> AuditSource:
        if any(existing.source_id == source.source_id for existing in self.sources):
            raise ValueError(f"Duplicate source_id: {source.source_id}")
        self.sources.append(source)
        return source

    def add_metric(self, metric: AuditMetric) -> AuditMetric:
        metric.validate(self.source_map())
        self.metrics.append(metric)
        return metric

    def add_gap(self, gap: DataGap) -> DataGap:
        self.data_gaps.append(gap)
        return gap

    def validate(self) -> None:
        sources = self.source_map()
        for metric in self.metrics:
            metric.validate(sources)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    def write(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        self.validate()
        payload = json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        (out_dir / "audit-data.json").write_text(
            payload,
            encoding="utf-8",
        )
        (out_dir / "kai-data.json").write_text(
            payload,
            encoding="utf-8",
        )
        write_data_sources_md(self, out_dir / "_data-sources.md")
        write_data_gaps_md(self, out_dir / "_data-gaps.md")


def write_data_sources_md(dataset: AuditDataset, path: Path) -> None:
    lines = [
        "# Kai Data Sources",
        "",
        f"Audit Mode: `{dataset.audit_mode}`",
        f"Workflow: `{dataset.workflow}`",
        f"Generated At: `{dataset.generated_at}`",
        "",
        "| Source | Tier | Access | Retrieved At | Used For | Artifact |",
        "|--------|------|--------|--------------|----------|----------|",
    ]
    for source in dataset.sources:
        artifact = source.artifact_path or source.source_url
        lines.append(
            f"| {source.name} | {source.tier} | {source.access} | {source.retrieved_at} | "
            f"{source.used_for} | {artifact} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_data_gaps_md(dataset: AuditDataset, path: Path) -> None:
    lines = [
        "# Audit Data Gaps",
        "",
        "| Missing Source | Blocks | Sales Version Handling | Onboarding Version Handling |",
        "|----------------|--------|------------------------|-----------------------------|",
    ]
    for gap in dataset.data_gaps:
        lines.append(
            f"| {gap.missing_source} | {gap.blocks} | {gap.sales_version_handling} | "
            f"{gap.onboarding_version_handling} |"
        )
    if not dataset.data_gaps:
        lines.append("| None | No known gaps | Use sourced metrics only | Use sourced metrics only |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
