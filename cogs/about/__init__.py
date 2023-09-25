from __future__ import annotations

from typing import TYPE_CHECKING

from .about import About

if TYPE_CHECKING:
    from core.bot import Lunaria


async def setup(bot: Lunaria) -> None:
    await bot.add_cog(About(bot))
