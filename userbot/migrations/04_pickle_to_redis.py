#!/usr/bin/env python3
"""Migrate from pickle storage backend to redis one (commit 214bd57)."""

__all__ = []

import asyncio
import logging
import pickle
from typing import Any

from userbot.config import RedisConfig, StorageConfig
from userbot.storage import RedisStorage

_log = logging.getLogger(__name__)


async def _main(old_storage_raw: dict[str, Any], new_storage: RedisStorage) -> None:
    async with new_storage:
        hook: str
        chats: set
        for hook, chats in old_storage_raw.get("hooks", {}).items():
            for chat_id in chats:
                _log.debug("Migrating hook %r for chat %d", hook, chat_id)
                await new_storage.enable_hook(hook, chat_id)
        chat_id: int
        messages: set
        for chat_id, messages in old_storage_raw.get("react2ban", {}).items():
            for message_id in messages:
                _log.debug("Migrating react2ban for chat %d and message %d", chat_id, message_id)
                await new_storage.add_react2ban(chat_id, message_id)


def main():
    config = StorageConfig.from_env()
    pickle_path = config.data_location / f"{config.session_name}.pkl"
    try:
        with open(pickle_path, "rb") as f:
            _log.debug("Loading pickle storage from %s", pickle_path)
            old_storage_raw = pickle.load(f)
    except FileNotFoundError as e:
        _log.warning("Pickle storage not found, skipping migration", exc_info=e)
        return
    redis_config = RedisConfig.from_env()
    password = redis_config.password.value if redis_config.password else None
    new_storage = RedisStorage(
        redis_config.host,
        redis_config.port,
        redis_config.db,
        password,
    )

    asyncio.run(_main(old_storage_raw, new_storage))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
