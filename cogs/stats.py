from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.app_commands import Command, ContextMenu
from discord.ext import commands
from dotenv import load_dotenv

if TYPE_CHECKING:
    from core.bot import Lunaria

log = logging.getLogger(__name__)


class Stats(commands.Cog, name='stats'):
    """Stats cog"""

    def __init__(self, bot: Lunaria) -> None:
        load_dotenv()
        self.bot: Lunaria = bot

    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction: discord.Interaction[Lunaria],
        app_command: Command | ContextMenu,
    ) -> None:
        if self.bot.is_debug_mode():
            return

        if await self.bot.is_owner(interaction.user):
            return

        if self.bot.is_blocked(interaction.user):
            return

        command_type = app_command.type.value if isinstance(app_command, ContextMenu) else 1  # 1 is slash command
        channel = interaction.channel

        destination = None
        if interaction.guild is None:
            destination = 'Private Message'
        else:
            destination = f'#{channel} ({interaction.guild})'

        log.info(
            f'{interaction.created_at}: {interaction.user} in {destination}: /{app_command.qualified_name} (type: {command_type})'
        )


async def setup(bot: Lunaria) -> None:
    await bot.add_cog(Stats(bot))
