"""Unified analytics connector layer.

Every connector in this package produces ``MetricPoint`` objects — a
canonical format that the rest of the Kai runtime consumes for KPI
tracking, anomaly detection, attribution, scorecards, and watcher
subsystems.

Connectors available:
    GA4Connector          — Google Analytics 4 (Data API v1)
    GSCConnector          — Google Search Console (Search Analytics API)
    CallTrackingConnector — Generic call tracking (with KaiCalls integration)
    GBPConnector          — Google Business Profile (Performance API)
    AdMetricsAggregator   — Cross-platform ad metrics normalizer

Models:
    MetricPoint       — Single metric observation
    DateRange         — Start/end date pair
    ConnectorConfig   — Credentials and connector settings
"""

from .ad_metrics import AdMetricsAggregator
from .base import (
    AnalyticsConnector,
    ConnectorConfig,
    DateRange,
    MetricPoint,
)
from .call_tracking import CallTrackingConnector
from .ga4 import GA4Connector
from .gbp import GBPConnector
from .gsc import GSCConnector

__all__ = [
    "AdMetricsAggregator",
    "AnalyticsConnector",
    "CallTrackingConnector",
    "ConnectorConfig",
    "DateRange",
    "GA4Connector",
    "GBPConnector",
    "GSCConnector",
    "MetricPoint",
]
