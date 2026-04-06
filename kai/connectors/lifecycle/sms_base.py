"""SMS connector base — abstract interface for SMS providers.

Defines the ``SMSConnector`` abstract class and ``SMSMessage`` model.
Concrete implementations (e.g. Twilio, Vonage) are left for future tasks;
this module establishes the interface contract.
"""

from __future__ import annotations

import copy
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic import with fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data: Any) -> None:
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"

else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]


# ============================================================================
# SMS Data Model
# ============================================================================


class SMSMessage(BaseModel):
    """A single SMS message."""

    id: Optional[str] = Field(None, description="Provider-assigned message ID")
    to_phone: str = Field(..., description="Recipient phone number (E.164 format)")
    from_phone: Optional[str] = Field(None, description="Sender phone number")
    body: str = Field(..., description="Message body (max 160 chars per segment)")
    status: str = Field(
        "draft",
        description="draft|queued|sent|delivered|failed",
    )
    segments: int = Field(1, description="Number of SMS segments")
    sent_at: Optional[str] = Field(None, description="ISO timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Abstract SMS Connector
# ============================================================================


class SMSConnector(ABC):
    """Abstract base for SMS provider connectors.

    Concrete implementations (Twilio, Vonage, etc.) must implement all
    abstract methods.  This class defines the interface contract only.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self._connected: bool = False

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical SMS provider name (e.g. 'twilio')."""
        ...

    @abstractmethod
    def connect(self) -> bool:
        """Validate credentials and test connection.  Return True on success."""
        ...

    @abstractmethod
    def send_sms(self, message: SMSMessage) -> SMSMessage:
        """Send a single SMS message.

        Returns the message with updated status, provider-assigned ID,
        and sent_at timestamp.
        """
        ...

    @abstractmethod
    def send_batch_sms(self, messages: List[SMSMessage]) -> List[SMSMessage]:
        """Send multiple SMS messages.

        Returns a list of messages with updated statuses.
        """
        ...

    @abstractmethod
    def get_opt_out_list(self) -> List[str]:
        """Return phone numbers that have opted out of SMS.

        Numbers should be in E.164 format (e.g. ``+15551234567``).
        """
        ...

    @abstractmethod
    def check_opt_out(self, phone: str) -> bool:
        """Return True if *phone* has opted out of SMS messages."""
        ...
