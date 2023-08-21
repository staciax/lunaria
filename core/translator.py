from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

from discord import Locale
from discord.app_commands import (
    Choice,
    Command,
    ContextMenu,
    Group,
    Parameter,
    TranslationContext,
    TranslationContextLocation as TCL,
    Translator as _Translator,
    locale_str,
)

if TYPE_CHECKING:
    from .bot import Lunaria
    from .cog import LunaCog

    Localizable = Command | Group | ContextMenu | Parameter | Choice

log = logging.getLogger(__name__)


class OptionLocalization(TypedDict, total=False):
    display_name: str
    description: str
    choices: dict[str | int | float, str]


class ContextMenuLocalization(TypedDict):
    name: str


class AppCommandLocalization(ContextMenuLocalization, total=False):
    description: str
    options: dict[str, OptionLocalization]


def get_parameter_payload(
    parameter: Parameter,
    data: OptionLocalization | None = None,
    *,
    merge: bool = False,
) -> OptionLocalization:
    payload: OptionLocalization = {
        'display_name': parameter.display_name,
        'description': parameter.description,
    }

    if len(parameter.choices) > 0:
        payload['choices'] = {str(choice.value): choice.name for choice in parameter.choices}

    if data is None:
        return payload

    if merge:
        if 'display_name' in data and payload['display_name'] != data['display_name']:
            payload['display_name'] = data['display_name']

        if 'description' in data and payload['description'] != data['description'] and data['description'] != '…':
            payload['description'] = data['description']

        if len(parameter.choices) > 0:
            payload['choices'] = {}
            for choice in parameter.choices:
                if str(choice.value) in data.get('choices', {}):
                    payload['choices'][str(choice.value)] = data.get('choices', {})[str(choice.value)]
                else:
                    payload['choices'][str(choice.value)] = choice.name

    return payload


def get_app_command_payload(
    command: Command | Group,
    data: AppCommandLocalization | None = None,
    *,
    merge: bool = False,
) -> AppCommandLocalization:
    payload: AppCommandLocalization = {
        'name': command.name,
        'description': command.description,
    }

    if data is None:
        return payload

    if merge:
        if data['name'] != command.name:
            payload['name'] = data['name']

        if 'description' in data and data['description'] != command.description and data['description'] != '…':
            payload['description'] = data['description']

    if isinstance(command, Group):
        return payload

    if len(command.parameters) > 0:
        payload['options'] = {param.name: get_parameter_payload(param) for param in command.parameters}
        if merge:
            payload['options'] = {
                param.name: get_parameter_payload(param, data.get('options', {}).get(param.name, {}), merge=merge)
                for param in command.parameters
            }

    return payload


def get_path(
    cog_folder: Path,
    locale: str,
    *,
    fmt: str = 'json',
) -> Path:
    return cog_folder / 'locales' / 'app_commands' / f'{locale}.{fmt}'


class LunaTranslator(_Translator):
    def __init__(
        self,
        bot: Lunaria,
        supported_locales: tuple[Locale, ...] = (
            Locale.american_english,  # default
            Locale.thai,
        ),
    ) -> None:
        super().__init__()
        self.bot: Lunaria = bot
        self.supported_locales: tuple[Locale, ...] = supported_locales
        #
        self._app_command_localizations: dict[Locale, dict[str, AppCommandLocalization]] = {}
        self._context_menu_localizations: dict[Locale, dict[str, ContextMenuLocalization]] = {}
        self.lock = asyncio.Lock()

    async def load(self) -> None:
        log.info('loaded')

    async def unload(self) -> None:
        log.info('unloaded')

    async def translate(self, string: locale_str, locale: Locale, context: TranslationContext) -> str | None:
        localizable: Localizable = context.data
        tcl: TCL = context.location

        if tcl != TCL.other:
            return None

        if locale == Locale.american_english:  # default
            return None

        if locale not in self.supported_locales:
            return None

        keys = self._build_localize_keys(tcl, localizable)
        if not keys:
            log.warn('string: %s not found in %s (tcl: %s)' % (string.message, locale.value, tcl))
            return None

        if isinstance(localizable, ContextMenu):
            localizations = self._context_menu_localizations.get(locale, {})
        else:
            localizations = self._app_command_localizations.get(locale, {})

        if not localizations:
            log.debug('no localizations for %s (tcl: %s)' % (locale.value, tcl))
            return None

        def find_value(data: dict[str, Any], keys: tuple[str, ...]) -> str | dict[str, Any] | None:
            result = data.copy()
            for k in keys:
                try:
                    result = result[k]
                except KeyError:
                    return None
            return result

        value = find_value(localizations, keys)

        if value is None:
            log.warning('string: %s not found in %s (tcl: %s)' % (string.message, locale.value, tcl))
            return None

        if not isinstance(value, str):
            return None

        log.debug('%s locale: %s tcl: %s -> %s}' % (string.message, locale.value, tcl.name, value))
        return value

    def _build_localize_keys(
        self,
        tcl: TCL,
        localizable: Localizable,
    ) -> tuple[str, ...]:
        if tcl in (TCL.command_name, TCL.group_name):
            assert isinstance(localizable, (Command, Group, ContextMenu))
            self.__latest_command = localizable
            return (localizable.qualified_name, 'name')

        elif tcl in (TCL.command_description, TCL.group_description):
            assert isinstance(localizable, (Command, Group))
            return (localizable.qualified_name, 'description')

        elif tcl == TCL.parameter_name:
            assert isinstance(localizable, Parameter)
            self.__latest_parameter = localizable
            return (localizable.command.qualified_name, 'options', localizable.name, 'display_name')

        elif tcl == TCL.parameter_description:
            assert isinstance(localizable, Parameter)
            return (localizable.command.qualified_name, 'options', localizable.name, 'description')

        elif tcl == TCL.choice_name:
            assert isinstance(localizable, Choice)
            if self.__latest_command is not None and self.__latest_parameter is not None:
                return (
                    self.__latest_command.qualified_name,
                    'options',
                    self.__latest_parameter.name,
                    'choices',
                    str(localizable.value),
                )
        return ()

    # app command

    def get_command_localization(
        self,
        locale: str,
        command: Command | Group,
    ) -> AppCommandLocalization | None:
        if locale not in self._app_command_localizations:
            return None
        if command.qualified_name not in self._app_command_localizations[locale]:
            return None
        return self._app_command_localizations[locale][command.qualified_name]

    def add_command_localization(self, command: Command | Group, *, merge: bool = True) -> None:
        for locale in self.supported_locales:
            if locale.value not in self._app_command_localizations:
                self._app_command_localizations[locale] = {}

            self._app_command_localizations[locale][command.qualified_name] = get_app_command_payload(
                command,
                self.get_command_localization(locale.value, command),
                merge=merge,
            )

    def remove_command_localization(self, command: Command | Group) -> None:
        for locale in self.supported_locales:
            self._app_command_localizations.setdefault(locale, {}).pop(command.qualified_name, None)

    # file

    async def load_from_files(self, cog_name: str, cog_folder: str | Path | os.PathLike) -> None:
        for locale in self.supported_locales:
            fp = get_path(Path(cog_folder).resolve().parent, locale.value)

            if not fp.exists():
                continue

            if locale.value not in self._app_command_localizations:
                self._app_command_localizations[locale] = {}

            async with self.lock:
                with fp.open('r', encoding='utf-8') as file:
                    self._app_command_localizations[locale].update(json.load(file))

        log.debug('loaded app command localizations for %s' % cog_name)

    async def save_to_files(
        self,
        app_commands: list[str],
        cog_name: str,
        cog_folder: str | Path | os.PathLike,
    ) -> None:
        for locale in self.supported_locales:
            fp = get_path(Path(cog_folder).resolve().parent, locale.value)

            if not fp.parent.exists():
                fp.parent.mkdir(parents=True)
                log.debug(f'created {fp.parent}')

            localizations = self._app_command_localizations.get(locale, {})
            entries = {command: localization for command, localization in localizations.items() if command in app_commands}
            # entries = dict(sorted(entries.items())) # sort by command name

            with fp.open('w', encoding='utf-8') as file:
                json.dump(entries, file, indent=4, ensure_ascii=False, sort_keys=True)
                log.debug('saved app command localizations for %s in %s' % (cog_name, locale.value))

    # cog

    async def add_cog_localization(self, cog: LunaCog, *, exclude_guild_commands: bool = True) -> None:
        fp = cog._get_file_path()
        if fp is None:
            return

        commands = cog.get_app_commands()
        if exclude_guild_commands:
            commands = filter(lambda x: not x._guild_ids, commands)

        for command in commands:
            self.add_command_localization(command)

        await self.save_to_files(
            [c.qualified_name for c in commands],
            cog.qualified_name,
            fp,
        )

    async def remove_cog_localization(self, cog: LunaCog, *, exclude_guild_commands: bool = True) -> None:
        fp = cog._get_file_path()
        if fp is None:
            return

        commands = cog.get_app_commands()
        if exclude_guild_commands:
            commands = filter(lambda x: not x._guild_ids, commands)

        await self.save_to_files(
            [c.qualified_name for c in commands],  # exclude guild commands
            cog.qualified_name,
            fp,
        )

        for command in commands:
            self.remove_command_localization(command)
