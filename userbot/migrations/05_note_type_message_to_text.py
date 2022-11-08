#!/usr/bin/env python3
"""Migrate from note type "message" to "text" (commit 99b9af6)."""

__all__ = []

import asyncio
import logging

from userbot.config import RedisConfig
from userbot.storage import RedisStorage

_log = logging.getLogger(__name__)


async def _main(storage: RedisStorage) -> None:
    async with storage:
        async for note in storage.saved_notes():
            content, type_ = await storage.get_note(note)
            if type_ == "message":
                _log.debug("Migrating note %r", note)
                await storage.save_note(note, content, "text")
            elif type_ != "sticker":
                _log.warning(
                    "File reference for note %r is probably expired, re-save the note again",
                    note,
                )


def main():
    redis_config = RedisConfig.from_env()
    password = redis_config.password.value if redis_config.password else None
    storage = RedisStorage(
        redis_config.host,
        redis_config.port,
        redis_config.db,
        password,
    )

    asyncio.run(_main(storage))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
