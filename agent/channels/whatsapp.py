"""
WhatsApp channel implementation using Twilio.

Transport layer only — all command logic lives in commands.py.
"""

from typing import Any, Dict, Optional

from ..config import agent_config
from ..models import MessageType
from .base import BaseChannel
from . import commands


class WhatsAppChannel(BaseChannel):
    """
    WhatsApp communication channel via Twilio.

    Receives messages, delegates to the shared command router,
    and sends responses back via Twilio.
    """

    @property
    def channel_name(self) -> str:
        return "whatsapp"

    async def send_message(
        self,
        recipient: str,
        message: str,
        **kwargs
    ) -> bool:
        """Send a WhatsApp message via Twilio."""
        if not agent_config.twilio_account_sid:
            print(f"[WhatsApp] Twilio not configured, would send to {recipient}: {message[:100]}...")
            return False

        try:
            from twilio.rest import Client

            client = Client(
                agent_config.twilio_account_sid,
                agent_config.twilio_auth_token
            )

            from_number = f"whatsapp:{agent_config.twilio_whatsapp_number}"
            to_number = f"whatsapp:{recipient}" if not recipient.startswith("whatsapp:") else recipient

            msg = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )

            self.log_message(
                recipient,
                message,
                MessageType.OUTGOING,
                {"sid": msg.sid}
            )

            return True

        except Exception as e:
            print(f"[WhatsApp] Failed to send message: {e}")
            return False

    async def process_incoming(
        self,
        sender: str,
        message: str,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process an incoming WhatsApp message."""
        self.log_message(sender, message, MessageType.INCOMING, raw_data)
        return await commands.route_text(message, sender)


# Global WhatsApp channel instance
whatsapp_channel = WhatsAppChannel()
