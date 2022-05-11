from __future__ import annotations

import logging
import pickle
from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path
from types import TracebackType
from typing import Type, TypeVar

_T = TypeVar("_T", bound="Storage")

_log = logging.getLogger(__name__)


class Storage(ABC):
    @abstractmethod
    async def connect(self) -> None:
        _log.debug("Storage %r connected", self.__class__.__name__)

    @abstractmethod
    async def close(self) -> None:
        _log.debug("Storage %r disconnected", self.__class__.__name__)

    @abstractmethod
    async def enable_hook(self, name: str, chat_id: int) -> None:
        _log.debug("Hook %r enabled in chat %d", name, chat_id)

    @abstractmethod
    async def disable_hook(self, name: str, chat_id: int) -> None:
        _log.debug("Hook %r disabled in chat %d", name, chat_id)

    @abstractmethod
    async def is_hook_enabled(self, name: str, chat_id: int) -> bool:
        pass

    @abstractmethod
    async def list_enabled_hooks(self, chat_id: int) -> list[str]:
        pass

    async def __aenter__(self: _T) -> _T:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Type[Exception],
        exc_val: Exception,
        exc_tb: TracebackType,
    ) -> None:
        await self.close()
        return


class PickleStorage(Storage):
    def __init__(self, filename: str | PathLike):
        self._file = Path(filename)
        self._data = {}

    async def connect(self) -> None:
        try:
            with self._file.open("rb") as f:
                self._data = pickle.load(f)
        except FileNotFoundError:
            pass
        await super().connect()

    async def close(self) -> None:
        with self._file.open("wb") as f:
            pickle.dump(self._data, f)
        await super().close()

    async def enable_hook(self, name: str, chat_id: int) -> None:
        self._data.setdefault("hooks", {}).setdefault(name, set()).add(chat_id)
        await super().enable_hook(name, chat_id)

    async def disable_hook(self, name: str, chat_id: int) -> None:
        self._data.setdefault("hooks", {}).setdefault(name, set()).discard(chat_id)
        await super().disable_hook(name, chat_id)

    async def is_hook_enabled(self, name: str, chat_id: int) -> bool:
        return chat_id in self._data.setdefault("hooks", {}).setdefault(name, set())

    async def list_enabled_hooks(self, chat_id: int) -> list[str]:
        res = []
        for name, chats in self._data.setdefault("hooks", {}).items():
            if chat_id in chats:
                res.append(name)
        return res
