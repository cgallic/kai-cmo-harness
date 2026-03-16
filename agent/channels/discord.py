"""
Discord channel implementation using discord.py.

Slash commands route to the shared command router.
Runs as an asyncio task alongside the agent loop.
"""

import asyncio
import os
import re
import traceback
from typing import Any, Dict, Optional

from ..config import agent_config
from ..models import MessageType
from .base import BaseChannel
from . import commands


def _to_discord_md(text: str) -> str:
    """Convert command router markdown (*bold*, _italic_) to Discord markdown."""
    # *text* → **text** (but not **already bold**)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'**\1**', text)
    # _italic_ → *italic*
    text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'*\1*', text)
    return text


class DiscordChannel(BaseChannel):
    """
    Discord communication channel using discord.py.

    Runs a bot that listens for slash commands and routes them
    to the same handlers as WhatsApp.
    """

    def __init__(self):
        self._bot = None
        self._ready = asyncio.Event()

    @property
    def channel_name(self) -> str:
        return "discord"

    @property
    def bot(self):
        return self._bot

    def _create_bot(self):
        """Create the Discord bot with slash commands."""
        try:
            import discord
            from discord import app_commands
        except ImportError:
            print("[Discord] discord.py not installed. Run: pip install discord.py")
            return None

        # Only request non-privileged intents — slash commands only need guilds
        intents = discord.Intents.default()

        client = discord.Client(intents=intents)
        tree = app_commands.CommandTree(client)

        channel_ref = self

        # --- Core commands ---

        @tree.command(name="status", description="Agent status and pending tasks")
        async def cmd_status(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("status", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="report", description="Daily briefing")
        @app_commands.describe(client="Client name (default: kaicalls)")
        async def cmd_report(interaction: discord.Interaction, client: str = "kaicalls"):
            await interaction.response.defer()
            result = await channel_ref._run_handler("report", client, str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="tasks", description="List scheduled tasks")
        async def cmd_tasks(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("tasks", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="mrr", description="Stripe MRR snapshot")
        async def cmd_mrr(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("mrr", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="pause", description="Pause all scheduled tasks")
        async def cmd_pause(interaction: discord.Interaction):
            result = await channel_ref._run_handler("pause", "", str(interaction.user))
            await interaction.response.send_message(result)

        @tree.command(name="resume", description="Resume scheduled tasks")
        async def cmd_resume(interaction: discord.Interaction):
            result = await channel_ref._run_handler("resume", "", str(interaction.user))
            await interaction.response.send_message(result)

        # --- Kai Calls ---

        @tree.command(name="kaistatus", description="Kai Calls health + pending emails")
        async def cmd_kaistatus(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("kaistatus", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="kaiqueue", description="Pending email queue")
        async def cmd_kaiqueue(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("kaiqueue", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="kaisend", description="Auto-send approved pending emails")
        async def cmd_kaisend(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("kaisend", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="kaicalls", description="Full Kai Calls daily report")
        async def cmd_kaicalls(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("kaicalls", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="kaileads", description="Recent leads with scores")
        async def cmd_kaileads(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("kaileads", "", str(interaction.user))
            await interaction.followup.send(result)

        # --- BuildWithKai ---

        @tree.command(name="bwkstatus", description="BWK health + generation stats")
        async def cmd_bwkstatus(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("bwkstatus", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="bwkgens", description="BWK product generation stats")
        async def cmd_bwkgens(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("bwkgens", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="bwkusers", description="BWK user activation funnel")
        async def cmd_bwkusers(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("bwkusers", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="bwkrevenue", description="BWK revenue and published products")
        async def cmd_bwkrevenue(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("bwkrevenue", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="bwkreport", description="Full BWK daily report")
        async def cmd_bwkreport(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("bwkreport", "", str(interaction.user))
            await interaction.followup.send(result)

        # --- Amazing Backyard Parties ---

        @tree.command(name="abpstatus", description="ABP health + lead/vendor stats")
        async def cmd_abpstatus(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("abpstatus", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="abpleads", description="ABP recent leads and match rates")
        async def cmd_abpleads(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("abpleads", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="abpvendors", description="ABP vendor coverage and pipeline")
        async def cmd_abpvendors(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("abpvendors", "", str(interaction.user))
            await interaction.followup.send(result)

        @tree.command(name="abpreport", description="Full ABP daily report")
        async def cmd_abpreport(interaction: discord.Interaction):
            await interaction.response.defer()
            result = await channel_ref._run_handler("abpreport", "", str(interaction.user))
            await interaction.followup.send(result)

        # --- Help ---

        @tree.command(name="agenthelp", description="Show all agent commands")
        async def cmd_help(interaction: discord.Interaction):
            result = await channel_ref._run_handler("help", "", str(interaction.user))
            await interaction.response.send_message(result)

        # --- Events ---

        @client.event
        async def on_ready():
            print(f"[Discord] Logged in as {client.user}")
            print(f"[Discord] In {len(client.guilds)} servers")
            try:
                synced = await tree.sync()
                print(f"[Discord] Synced {len(synced)} slash commands")
            except Exception as e:
                print(f"[Discord] Failed to sync commands: {e}")
            channel_ref._ready.set()

        client._tree = tree
        return client

    async def _run_handler(self, command: str, args: str, sender: str) -> str:
        """Route a command through the shared command router."""
        try:
            result = await commands.route(command, args, sender)
            result = _to_discord_md(result)
            # Discord has a 2000 char limit per message
            if len(result) > 1990:
                result = result[:1990] + "..."
            return result
        except Exception as e:
            return f"Error: {str(e)}"

    async def start(self):
        """Start the Discord bot with auto-reconnect. Call this from the agent loop."""
        token = os.getenv("DISCORD_BOT_TOKEN", "")
        if not token:
            print("[Discord] DISCORD_BOT_TOKEN not set, skipping Discord channel")
            return

        backoff = 5
        max_backoff = 300  # 5 minutes max

        while True:
            self._ready.clear()
            self._bot = self._create_bot()
            if self._bot is None:
                return

            print(f"[Discord] Starting bot...")
            try:
                await self._bot.start(token)
            except Exception as e:
                print(f"[Discord] Bot failed: {e}")
                # 4004 = invalid token — don't retry, it won't fix itself
                err_str = str(e)
                if "4004" in err_str or "Improper token" in err_str:
                    print("[Discord] Token invalid (4004). Regenerate at discord.com/developers. Giving up.")
                    return
                traceback.print_exc()
            finally:
                if self._bot and not self._bot.is_closed():
                    try:
                        await self._bot.close()
                    except Exception:
                        pass

            print(f"[Discord] Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)

    async def stop(self):
        """Stop the Discord bot gracefully."""
        if self._bot and not self._bot.is_closed():
            print("[Discord] Shutting down bot...")
            await self._bot.close()

    async def send_message(
        self,
        recipient: str,
        message: str,
        **kwargs
    ) -> bool:
        """
        Send a message to a Discord channel.

        Args:
            recipient: Discord channel ID
            message: Message content
        """
        if not self._bot or not self._ready.is_set():
            print(f"[Discord] Bot not ready, would send: {message[:100]}...")
            return False

        try:
            channel_id = int(recipient)
            channel = self._bot.get_channel(channel_id)
            if channel is None:
                channel = await self._bot.fetch_channel(channel_id)

            msg = _to_discord_md(message)
            # Split long messages
            while len(msg) > 1990:
                split_at = msg.rfind('\n', 0, 1990)
                if split_at == -1:
                    split_at = 1990
                await channel.send(msg[:split_at])
                msg = msg[split_at:].lstrip('\n')
            if msg:
                await channel.send(msg)

            self.log_message(recipient, message, MessageType.OUTGOING)
            return True

        except Exception as e:
            print(f"[Discord] Failed to send message: {e}")
            return False

    async def process_incoming(
        self,
        sender: str,
        message: str,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process an incoming message."""
        self.log_message(sender, message, MessageType.INCOMING, raw_data)
        result = await commands.route_text(message, sender)
        return _to_discord_md(result)


# Global Discord channel instance
discord_channel = DiscordChannel()
