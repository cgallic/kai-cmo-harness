"""
Base channel interface for communication channels.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..models import ConversationMessage, MessageType


class BaseChannel(ABC):
    """
    Abstract base class for communication channels.

    Channels handle:
    - Receiving messages from users
    - Sending messages to users
    - Managing conversation context
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the channel identifier (e.g., 'whatsapp', 'telegram')."""
        pass

    @abstractmethod
    async def send_message(
        self,
        recipient: str,
        message: str,
        **kwargs
    ) -> bool:
        """
        Send a message to a recipient.

        Args:
            recipient: Phone number or user ID
            message: Message content
            **kwargs: Channel-specific options

        Returns:
            True if message was sent successfully
        """
        pass

    @abstractmethod
    async def process_incoming(
        self,
        sender: str,
        message: str,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process an incoming message and return a response.

        Args:
            sender: Phone number or user ID of sender
            message: Message content
            raw_data: Raw webhook data

        Returns:
            Response message to send back
        """
        pass

    def log_message(
        self,
        phone_number: str,
        content: str,
        message_type: MessageType,
        context: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Log a message to the database."""
        from ..models import agent_db

        message = ConversationMessage(
            id=0,  # Will be assigned by DB
            channel=self.channel_name,
            phone_number=phone_number,
            message_type=message_type,
            content=content,
            context=context or {}
        )
        message.id = agent_db.save_message(message)
        return message
