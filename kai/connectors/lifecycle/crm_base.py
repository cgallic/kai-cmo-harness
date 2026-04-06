"""CRM connector base — abstract interface for lightweight CRM integrations.

Defines the ``CRMConnector`` abstract class for contact, deal, and activity
management.  Concrete implementations (HubSpot, Airtable, Pipedrive, etc.)
are left for future tasks; this module establishes the interface contract.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CRMConnector(ABC):
    """Abstract base for CRM provider connectors.

    Provides a uniform interface for contact management, deal/opportunity
    tracking, and activity logging across CRM platforms.

    Concrete implementations (HubSpot, Airtable, Pipedrive, etc.) must
    implement all abstract methods below.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self._connected: bool = False

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical CRM provider name (e.g. 'hubspot')."""
        ...

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    @abstractmethod
    def connect(self) -> bool:
        """Validate credentials and test connection.  Return True on success."""
        ...

    # ------------------------------------------------------------------
    # Contact management
    # ------------------------------------------------------------------

    @abstractmethod
    def get_contacts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch contacts, optionally filtered.

        Parameters
        ----------
        filters:
            Provider-specific filter criteria (e.g. ``{"email": "foo@bar.com"}``).
        limit:
            Maximum number of contacts to return.

        Returns
        -------
        list
            List of contact dicts with at minimum ``id``, ``email``,
            ``first_name``, ``last_name`` fields.
        """
        ...

    @abstractmethod
    def create_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact.

        Parameters
        ----------
        data:
            Contact fields (email, first_name, last_name, phone, etc.).

        Returns
        -------
        dict
            The created contact with provider-assigned ``id``.
        """
        ...

    @abstractmethod
    def update_contact(self, contact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing contact.

        Parameters
        ----------
        contact_id:
            Provider-assigned contact identifier.
        data:
            Fields to update.

        Returns
        -------
        dict
            The updated contact.
        """
        ...

    # ------------------------------------------------------------------
    # Deal / opportunity tracking
    # ------------------------------------------------------------------

    @abstractmethod
    def get_deals(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch deals/opportunities, optionally filtered.

        Parameters
        ----------
        filters:
            Provider-specific filter criteria.

        Returns
        -------
        list
            List of deal dicts with at minimum ``id``, ``name``,
            ``stage``, ``value`` fields.
        """
        ...

    @abstractmethod
    def create_deal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new deal/opportunity.

        Parameters
        ----------
        data:
            Deal fields (name, stage, value, associated contact IDs, etc.).

        Returns
        -------
        dict
            The created deal with provider-assigned ``id``.
        """
        ...

    # ------------------------------------------------------------------
    # Activity logging
    # ------------------------------------------------------------------

    @abstractmethod
    def get_activities(self, contact_id: str) -> List[Dict[str, Any]]:
        """Fetch the activity log for a contact.

        Parameters
        ----------
        contact_id:
            Provider-assigned contact identifier.

        Returns
        -------
        list
            List of activity dicts (calls, emails, meetings, notes, etc.)
            with at minimum ``id``, ``type``, ``timestamp``, ``summary``.
        """
        ...

    @abstractmethod
    def log_activity(
        self, contact_id: str, activity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Log an activity against a contact.

        Parameters
        ----------
        contact_id:
            Provider-assigned contact identifier.
        activity:
            Activity details: ``type`` (call, email, meeting, note),
            ``summary``, ``timestamp``, and any provider-specific fields.

        Returns
        -------
        dict
            The created activity record with provider-assigned ``id``.
        """
        ...
