#!/usr/bin/env python3
"""Migrate from "duck" hook to "emojis" hook (commit 4edf500)"""

import asyncio
import logging

from userbot.config import Config
from userbot.storage import PickleStorage

logging.basicConfig(level=logging.DEBUG)


async def _main(storage: PickleStorage) -> None:
    async with storage:
        hook: str
        chats: set
        # noinspection PyProtectedMember
        for chats in storage._data.get("hooks", {}).get("duck", set()):
            for chat_id in chats:
                await storage.disable_hook("duck", chat_id)
                await storage.enable_hook(hook, chat_id)


def main():
    config = Config.from_env()
    storage = PickleStorage(config.data_location / f"{config.session}.pkl")

    asyncio.run(_main(storage))
