import asyncio
import contextlib
import logging
from logging.handlers import RotatingFileHandler

from discord import utils

from core.bot import Lunaria

try:
    import uvloop  # type: ignore
except ImportError:
    pass
else:
    uvloop.install()


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name='discord.state')

    def filter(self, record):
        if record.levelname == 'WARNING' and 'referencing an unknown' in record.msg:
            return False
        return True


@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        # __enter__
        max_bytes = 32 * 1024 * 1024  # 32 MiB

        # discord.py
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.state').addFilter(RemoveNoise())

        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename='lattemaid.log', encoding='utf-8', mode='w', maxBytes=max_bytes, backupCount=5
        )
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)
        # if not args.prod:
        handler = logging.StreamHandler()
        if isinstance(handler, logging.StreamHandler) and utils.stream_supports_colour(handler.stream):
            fmt = utils._ColourFormatter()
        handler.setFormatter(fmt)
        log.addHandler(handler)
        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for handler in handlers:
            handler.close()
            log.removeHandler(handler)


async def run_bot():
    async with Lunaria() as bot:
        await bot.start()


def main():
    with setup_logging():
        asyncio.run(run_bot())


if __name__ == '__main__':
    main()
