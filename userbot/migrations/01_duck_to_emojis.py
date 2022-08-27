#!/usr/bin/env python3
"""Migrate from "duck" hook to "emojis" hook (commit 4edf500)"""

import logging
import pickle
from pathlib import Path

from userbot.config import Config

logging.basicConfig(level=logging.DEBUG)


def _main(storage_location: Path) -> None:
    chats: set[int]
    with storage_location.open("rb") as f:
        data = pickle.load(f)
    hooks = data.setdefault("hooks", {})
    for chats in hooks.get("duck", set()):
        for chat_id in chats:
            hooks.setdefault("duck", set()).discard(chat_id)
            hooks.setdefault("emojis", set()).add(chat_id)
    with storage_location.open("wb") as f:
        pickle.dump(data, f)


def main():
    config = Config.from_env()
    _main(config.data_location / f"{config.session}.pkl")
