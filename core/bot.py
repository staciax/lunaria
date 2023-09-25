from __future__ import annotations

import asyncio
import datetime
import logging
import os
import random
from typing import Any, Literal, overload

import aiohttp
import discord
from colorthief import ColorThief
from discord.ext import commands
from dotenv import load_dotenv

from .cog import LunaCog
from .translator import LunaTranslator
from .tree import LunaTree

load_dotenv()

log = logging.getLogger(__name__)

# jishaku
os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
os.environ['JISHAKU_HIDE'] = 'True'

description = 'Hello, I\'m lunaria bot, a bot made by discord: stacia.(240059262297047041)'

INITIAL_EXTENSIONS = (
    'cogs.admin',
    'cogs.events',
    'cogs.jsk',
    'cogs.stats',
    # 'cogs.about',
    # 'cogs.errors',
    # 'cogs.help',
)


class Lunaria(commands.AutoShardedBot):
    user: discord.ClientUser
    bot_app_info: discord.AppInfo
    tree: LunaTree
    translator: LunaTranslator

    def __init__(
        self,
        *,
        debug_mode: bool = False,
        tree_sync_at_startup: bool = False,
    ) -> None:
        # intents
        intents = discord.Intents.none()
        intents.guilds = True
        intents.emojis_and_stickers = True
        # intents.dm_messages = True # TODO: implementation modmail?

        # allowed_mentions
        allowed_mentions = discord.AllowedMentions(roles=False, everyone=False, replied_user=False, users=True)

        super().__init__(
            command_prefix=commands.when_mentioned,
            help_command=None,
            allowed_mentions=allowed_mentions,
            case_insensitive=True,
            intents=intents,
            description=description,
            tree_cls=LunaTree,
            activity=discord.CustomActivity(name='lunaria ♡ ₊˚'),
        )
        self._debug_mode: bool = debug_mode
        self._tree_sync_at_startup: bool = tree_sync_at_startup
        self.version: str = '0.1.0a'
        self.support_guild_id: int = 1155822090025451520
        self.support_invite_url: str = 'https://discord.gg/'
        # palettes
        self.palettes: dict[str, list[discord.Colour]] = {}

    @property
    def owner(self) -> discord.User:
        """Returns the bot owner."""
        return self.bot_app_info.owner

    @property
    def support_guild(self) -> discord.Guild | None:
        if self.support_guild_id is None:
            raise ValueError('Support guild ID is not set.')
        return self.get_guild(self.support_guild_id)

    @discord.utils.cached_property
    def traceback_log(self) -> discord.TextChannel | None:
        return self.get_channel(1102897424235761724)  # type: ignore

    # def is_maintenance(self) -> bool:
    #     return self._is_maintenance

    def is_debug_mode(self) -> bool:
        return self._debug_mode

    def get_invite_url(self) -> str:
        scopes = ('bot', 'applications.commands')
        permissions = discord.Permissions(int(os.getenv('INVITE_PERMISSIONS', 280576)))
        return discord.utils.oauth_url(self.application_id, permissions=permissions, scopes=scopes)  # type: ignore

    # def get_oauth2_url(self) -> str:
    #     scopes = ('identify', 'guilds')
    #     return discord.utils.oauth_url(self.application_id, scopes=scopes)

    # @discord.utils.cached_property
    # def webhook(self) -> discord.Webhook:
    #     wh_id, wh_token = self.config.stat_webhook
    #     hook = discord.Webhook.partial(id=wh_id, token=wh_token, session=self.session)
    #     return hook

    # @discord.utils.cached_property
    # def traceback_log(self) -> Optional[Union[discord.abc.GuildChannel, discord.Thread, discord.abc.PrivateChannel]]:
    #     return self.get_channel(config.traceback_channel_id)

    def is_blocked(self, obj: discord.abc.User | discord.Guild | int, /) -> bool:
        return False

    # bot extension setup

    async def tree_sync(self) -> None:
        await self.tree.sync()
        await self.tree.sync(guild=discord.Object(id=self.support_guild_id))

    async def cogs_load(self) -> None:
        await asyncio.gather(*[self.load_extension(extension) for extension in INITIAL_EXTENSIONS])

    async def cogs_unload(self) -> None:
        await asyncio.gather(*[self.unload_extension(extension) for extension in INITIAL_EXTENSIONS])

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        self.translator = LunaTranslator(self)
        await self.tree.set_translator(self.translator)

        self.bot_app_info = await self.application_info()
        self.owner_ids = [self.bot_app_info.owner.id, 385049730222129152]

        # load cogs
        await self.cogs_load()

        # tree sync
        if self._tree_sync_at_startup:
            await self.tree_sync()

        await self.tree.insert_model_to_commands()

    # cogs property

    @property
    def admin(self) -> commands.Cog | LunaCog | None:
        return self.get_cog('developer')

    @property
    def jsk(self) -> commands.Cog | LunaCog | None:
        return self.get_cog('jishaku')

    # bot event

    async def on_ready(self) -> None:
        if not hasattr(self, 'launch_time'):
            self.launch_time: datetime.datetime = datetime.datetime.now()

        if self.is_debug_mode():
            await self.change_presence(
                activity=discord.CustomActivity(
                    name='lunaria is in debug mode',
                ),
                status=discord.Status.idle,
            )

        log.info('Ready: %s (ID: %s)', self.user, self.user.id)

    # async def on_shard_resumed(self, shard_id: int):
    #     log.info('Shard ID %s has resumed...', shard_id)

    async def on_message(self, message: discord.Message, /) -> None:
        if message.author == self.user:
            return

        await self.process_commands(message)

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        log.error('Ignoring error in %s', event_method)

    # palettes

    @overload
    def get_palettes(self, id: str, /, *, onlyone: Literal[True] = True) -> discord.Colour | None:
        ...

    @overload
    def get_palettes(self, id: str, /, *, onlyone: Literal[False] = False) -> list[discord.Colour] | None:
        ...

    def get_palettes(self, id: str, /, *, onlyone: bool = False) -> list[discord.Color] | discord.Colour | None:
        if id not in self.palettes:
            return None
        palettes = self.palettes[id]
        if onlyone:
            return random.choice(palettes)
        return palettes

    def store_palettes(self, id: str, color: list[discord.Colour]) -> list[discord.Colour]:
        self.palettes[id] = color
        return color

    async def fetch_palettes(
        self,
        id: str,
        image: discord.Asset | str,
        palette: int = 5,
        *,
        store: bool = True,
    ) -> list[discord.Colour]:
        palettes = self.get_palettes(id, onlyone=False)
        if palettes is not None:
            return palettes
        if not isinstance(image, discord.Asset):
            state = self._get_state()
            image = discord.Asset(state, url=str(image), key=id)
        file = await image.to_file(filename=id)
        to_bytes = file.fp
        if palette > 0:
            palettes = [discord.Colour.from_rgb(*c) for c in ColorThief(to_bytes).get_palette(color_count=palette)]
        else:
            palettes = [discord.Colour.from_rgb(*ColorThief(to_bytes).get_color())]
        if store:
            self.store_palettes(id, palettes)
        return palettes

    # bot methods

    async def load_extension(self, name: str, *, package: str | None = None) -> None:
        try:
            await super().load_extension(name, package=package)
        except Exception as e:
            log.error('failed to load extension %s', name, exc_info=e)
            raise e
        else:
            log.info('loaded extension %s', name)

    async def unload_extension(self, name: str, *, package: str | None = None) -> None:
        try:
            await super().unload_extension(name, package=package)
        except Exception as e:
            log.error('failed to unload extension %s', name, exc_info=e)
            raise e
        else:
            log.info('unloaded extension %s', name)

    async def reload_extension(self, name: str, *, package: str | None = None) -> None:
        try:
            await super().reload_extension(name, package=package)
        except Exception as e:
            log.error('failed to reload extension %s', name, exc_info=e)
            raise e
        else:
            log.info('reloaded extension %s', name)

    async def close(self) -> None:
        await self.cogs_unload()
        await self.session.close()
        await super().close()

    async def start(self) -> None:
        if self.is_debug_mode():
            token = os.getenv('DISCORD_TOKEN_TEST')
        else:
            token = os.getenv('DISCORD_TOKEN')
        if token is None:
            raise RuntimeError('No token provided.')
        await super().start(token=token, reconnect=True)
