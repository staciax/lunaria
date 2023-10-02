from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord.app_commands import AppCommandError

__all__ = (
    'LunaAppCommandError',
    'UserInputError',
    'BadArgument',
    'ComponentOnCooldown',
    'CheckFailure',
)

if TYPE_CHECKING:
    from discord.app_commands.commands import Command, ContextMenu


class LunaAppCommandError(AppCommandError):
    """Base class for errors that involve errors regarding Luna."""

    pass


class UserInputError(LunaAppCommandError):
    """Base class for errors that involve errors regarding user input."""

    def __init__(self, message: str) -> None:
        self.message: str = message
        super().__init__(message)


class BadArgument(LunaAppCommandError):
    """Raised when a bad argument is passed to a command."""

    pass


class ComponentOnCooldown(LunaAppCommandError):
    """Raised when a component is on cooldown."""

    def __init__(
        self,
        cooldown: discord.app_commands.Cooldown,
        retry_after: float,
    ) -> None:
        self.cooldown: discord.app_commands.Cooldown = cooldown
        self.retry_after: float = retry_after
        super().__init__(f'You are on cooldown. Try again in {self.retry_after:.2f}s')


class CheckFailure(LunaAppCommandError):
    """Raised when a check fails."""

    def __init__(
        self,
        command: Command[Any, ..., Any] | ContextMenu | None,
        author: discord.User | discord.Member | None,
    ) -> None:
        self.command: Command[Any, ..., Any] | ContextMenu | None = command
        self.author: discord.User | discord.Member | None = author
        super().__init__('You are not allowed to use this.')
