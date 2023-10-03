from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands

# fmt: off
__all__ = (
    'LunaTree',
)
# fmt: on

if TYPE_CHECKING:
    from .bot import Lunaria


log = logging.getLogger(__name__)


class LunaTree(app_commands.CommandTree['Lunaria']):
    async def interaction_check(self, interaction: discord.Interaction[Lunaria], /) -> bool:
        user = interaction.user
        guild = interaction.guild
        locale = interaction.locale
        command = interaction.command

        if await self.client.is_owner(user):
            return True

        if self.client.is_blocked(user):
            return False

        return True

    async def sync(self, *, guild: discord.abc.Snowflake | None = None) -> list[app_commands.AppCommand]:
        synced = await super().sync(guild=guild)
        if synced:
            log.info('synced %s application commands %s' % (len(synced), f'for guild {guild.id}' if guild else ''))
        return synced

    async def on_error(
        self,
        interaction: discord.Interaction['Lunaria'],
        error: app_commands.AppCommandError,
        /,
    ) -> None:
        await super().on_error(interaction, error)

    async def insert_model_to_commands(self) -> None:
        server_app_commands = await self.fetch_commands(with_localizations=True)
        for server in server_app_commands:
            command = self.get_command(server.name, type=server.type)
            if command is None:
                log.warn('not found command %s (type: %s)', server.name, server.type.name)
                continue
            command.extras['model'] = server

    # wait for discord adding this feature
    # fetch_commands with localizations
    # https://github.com/Rapptz/discord.py/pull/9452

    async def fetch_commands(
        self, *, guild: discord.abc.Snowflake | None = None, with_localizations: bool = False
    ) -> list[app_commands.AppCommand]:
        if self.client.application_id is None:
            raise app_commands.errors.MissingApplicationID

        application_id = self.client.application_id

        from discord.http import Route

        if guild is None:
            commands = await self._http.request(
                Route('GET', '/applications/{application_id}/commands', application_id=application_id),
                params={'with_localizations': int(with_localizations)},
            )
        else:
            commands = await self._http.request(
                Route(
                    'GET',
                    '/applications/{application_id}/guilds/{guild_id}/commands',
                    application_id=application_id,
                    guild_id=guild.id,
                ),
                params={'with_localizations': int(with_localizations)},
            )

        return [app_commands.AppCommand(data=data, state=self._state) for data in commands]
