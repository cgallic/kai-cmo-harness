"""Shared Kai source-backed data acquisition API.

The implementation currently lives in ``scripts.audit`` so existing audit
commands keep working, but non-audit workflows should import from
``kai.source_data``.
"""

from scripts.audit.collect import collect_audit_data, collect_kai_data, collect_third_party_sources
from scripts.audit.data_sources import AuditDataset, AuditMetric, AuditMode, AuditSource, DataGap, SourceTier

__all__ = [
    "AuditDataset",
    "AuditMetric",
    "AuditMode",
    "AuditSource",
    "DataGap",
    "SourceTier",
    "collect_audit_data",
    "collect_kai_data",
    "collect_third_party_sources",
]
