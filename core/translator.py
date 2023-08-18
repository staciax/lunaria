from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Locale
from discord.app_commands import Translator as _Translator

if TYPE_CHECKING:
    from .bot import Lunaria


class LunaTranslator(_Translator):
    def __init__(
        self,
        bot: Lunaria,
        supported_locales: list[Locale] = [
            Locale.american_english,  # default
            Locale.thai,
        ],
    ) -> None:
        super().__init__()
        self.bot: Lunaria = bot
        self.supported_locales: list[Locale] = supported_locales
