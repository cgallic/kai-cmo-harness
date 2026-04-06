"""Base analytics connector and canonical metric models.

Every analytics connector in the Kai system outputs ``MetricPoint``
objects — a single, uniform format that all downstream subsystems
(KPI models, attribution, anomaly detection, scorecards, watchers)
consume.  This module defines that format and the abstract base class
that concrete connectors must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kai.runtime.models import SerializableModel


# ---------------------------------------------------------------------------
# Canonical models
# ---------------------------------------------------------------------------


@dataclass
class MetricPoint(SerializableModel):
    """A single metric observation from an analytics platform.

    This is the atomic data unit flowing through all Kai analytics
    pipelines.  Downstream systems never touch raw platform responses;
    they receive lists of ``MetricPoint`` objects instead.

    Attributes:
        metric_name: Canonical metric name (e.g., "sessions", "clicks",
            "phone_calls").  All connectors map platform-specific names
            to this canonical vocabulary.
        value: The numeric metric value.
        date: ISO date string (YYYY-MM-DD) for the observation period.
        dimension: Optional dimension value (e.g., "organic", "mobile",
            "homepage").
        dimension_name: Dimension key (e.g., "traffic_source", "device",
            "page").
        source: Which connector produced this point (e.g., "ga4", "gsc",
            "call_tracking", "gbp").
        metadata: Arbitrary additional context — confidence interval,
            sample size, currency, comparison period values, etc.
    """

    metric_name: str = ""
    value: float = 0.0
    date: str = ""
    dimension: Optional[str] = None
    dimension_name: Optional[str] = None
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DateRange(SerializableModel):
    """Start/end date pair for queries.

    Both dates are ISO date strings (YYYY-MM-DD), inclusive.
    """

    start_date: str = ""
    end_date: str = ""


@dataclass
class ConnectorConfig(SerializableModel):
    """Configuration for a single analytics connector instance.

    Attributes:
        connector_type: Connector identifier (e.g., "ga4", "gsc",
            "call_tracking", "gbp").
        credentials: API keys, OAuth tokens, or service account paths.
            **Never log this dict.**
        property_id: Platform-specific resource identifier — GA4 property
            ID, GSC site URL, GBP location ID, ad account ID, etc.
        enabled: Whether this connector should be used in collection runs.
        metadata: Connector-specific config that does not fit the common
            fields (polling intervals, custom dimension maps, etc.).
    """

    connector_type: str = ""
    credentials: Dict[str, Any] = field(default_factory=dict)
    property_id: Optional[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Abstract base connector
# ---------------------------------------------------------------------------


class AnalyticsConnector(ABC):
    """Abstract base class for all Kai analytics connectors.

    Concrete implementations wrap a single analytics platform and
    expose its data through a uniform interface.  Every method that
    returns metric data must yield ``List[MetricPoint]`` so that
    downstream consumers are platform-agnostic.

    Subclass contract:
        1. Set ``connector_type`` as a class attribute (e.g., ``"ga4"``).
        2. Implement every abstract method — even if the platform does
           not support that query type (return an empty list).
        3. Every stub must include a docstring explaining which real API
           endpoint it would call and what parameters it would send.
    """

    connector_type: str = ""

    def __init__(self, config: ConnectorConfig) -> None:
        """Store the connector configuration.

        Args:
            config: Credentials, property identifiers, and connector-
                specific settings.
        """
        self.config = config

    def connect(self) -> bool:
        """Validate credentials and connectivity.

        In a production implementation this would make a lightweight
        API call (e.g., list properties or fetch a single metric for
        today) to verify that the credentials work and the target
        resource exists.

        Returns:
            True if the connector can reach the platform, False otherwise.
        """
        return True

    # ------------------------------------------------------------------
    # Abstract query methods
    # ------------------------------------------------------------------

    @abstractmethod
    def get_metrics(
        self,
        date_range: DateRange,
        dimensions: List[str],
        metrics: List[str],
    ) -> List[MetricPoint]:
        """Fetch metric data for the given date range, dimensions, and metrics.

        Args:
            date_range: Period to query.
            dimensions: List of dimension keys to break results by
                (e.g., ["page_path", "traffic_source"]).
            metrics: List of metric names to retrieve
                (e.g., ["sessions", "conversions"]).

        Returns:
            One ``MetricPoint`` per unique (metric, dimension-value, date)
            combination.
        """

    @abstractmethod
    def get_events(
        self,
        event_name: str,
        date_range: DateRange,
    ) -> List[MetricPoint]:
        """Fetch event-level data for a specific event.

        Args:
            event_name: Platform event name (e.g., "purchase",
                "generate_lead", "phone_call").
            date_range: Period to query.

        Returns:
            One ``MetricPoint`` per event occurrence or daily aggregate,
            depending on the platform.
        """

    @abstractmethod
    def get_real_time(self) -> List[MetricPoint]:
        """Fetch a real-time snapshot of current activity.

        Returns:
            A list of ``MetricPoint`` objects reflecting the most recent
            data the platform can provide (typically last 30 minutes or
            current active users).
        """

    @abstractmethod
    def get_conversion_data(
        self,
        date_range: DateRange,
    ) -> List[MetricPoint]:
        """Fetch conversion-specific metrics for the given period.

        Returns:
            ``MetricPoint`` objects for conversion events, conversion
            rates, and related metrics.
        """

    @abstractmethod
    def available_metrics(self) -> List[str]:
        """Return the canonical metric names this connector can provide.

        Returns:
            Sorted list of metric name strings.
        """

    @abstractmethod
    def available_dimensions(self) -> List[str]:
        """Return the dimension keys this connector supports.

        Returns:
            Sorted list of dimension key strings.
        """
