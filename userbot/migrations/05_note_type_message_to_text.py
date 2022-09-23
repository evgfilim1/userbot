#!/usr/bin/env python3
"""Migrate from note type "message" to "text" (commit 99b9af6)."""

import asyncio
import logging

from userbot.config import RedisConfig
from userbot.storage import RedisStorage

_log = logging.getLogger(__name__)


async def _main(storage: RedisStorage) -> None:
    async with storage:
        async for note in storage.saved_messages():
            content, type_ = await storage.get_message(note)
            if type_ == "message":
                _log.debug("Migrating note %r", note)
                await storage.save_message(note, content, "text")
            elif type != "sticker":
                _log.warning(
                    "File reference for note %r is probably expired, re-save the note again",
                    note,
                )


def main():
    redis_config = RedisConfig.from_env()
    storage = RedisStorage(redis_config.host, redis_config.port, redis_config.db)

    asyncio.run(_main(storage))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
