#!/usr/bin/env python3
"""Migrate from "duck" hook to "emojis" hook (commit 4edf500)."""

import logging
import pickle
from pathlib import Path

from userbot.config import Config

_log = logging.getLogger(__name__)


def _main(storage_location: Path) -> None:
    with storage_location.open("rb") as f:
        _log.debug("Loading storage from %s", storage_location)
        data = pickle.load(f)
    hooks: dict[str, set[int]] = data.get("hooks", {})
    duck_hooks = hooks.get("duck", set()).copy()
    for chat_id in duck_hooks:
        _log.debug("Migrating chat %d", chat_id)
        hooks.setdefault("duck", set()).discard(chat_id)
        hooks.setdefault("emojis", set()).add(chat_id)
    with storage_location.open("wb") as f:
        _log.debug("Saving storage to %s", storage_location)
        pickle.dump(data, f)


def main():
    config = Config.from_env()
    try:
        _main(config.data_location / f"{config.session}.pkl")
    except FileNotFoundError as e:
        _log.warning("Pickle storage not found, skipping migration", exc_info=e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
