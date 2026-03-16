"""
Communication channels for the autonomous agent.

Supports WhatsApp (via Twilio) and Discord (via discord.py).
Command logic lives in commands.py, shared by all channels.
"""

from .base import BaseChannel
from .discord import discord_channel
from .whatsapp import whatsapp_channel
from . import commands

__all__ = ["BaseChannel", "whatsapp_channel", "discord_channel", "commands"]
