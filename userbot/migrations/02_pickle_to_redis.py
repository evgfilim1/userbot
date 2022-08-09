#!/usr/bin/env python3
"""Migrate from pickle storage backend to redis one (commit 214bd57)"""

import asyncio
import logging
import pickle
from typing import Any

from userbot.config import Config, RedisConfig
from userbot.storage import RedisStorage

logging.basicConfig(level=logging.DEBUG)


async def _main(old_storage_raw: dict[str, Any], new_storage: RedisStorage) -> None:
    async with new_storage:
        hook: str
        chats: set
        for hook, chats in old_storage_raw.get("hooks", {}).items():
            for chat_id in chats:
                await new_storage.enable_hook(hook, chat_id)
        chat_id: int
        messages: set
        for chat_id, messages in old_storage_raw.get("react2ban", {}).items():
            for message_id in messages:
                await new_storage.add_react2ban(chat_id, message_id)


def main():
    config = Config.from_env()
    with open(config.data_location / f"{config.session}.pkl", "rb") as f:
        old_storage_raw = pickle.load(f)
    redis_config = RedisConfig.from_env()
    new_storage = RedisStorage(redis_config.host, redis_config.port, redis_config.db)

    asyncio.run(_main(old_storage_raw, new_storage))
