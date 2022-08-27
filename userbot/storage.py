__all__ = [
    "RedisStorage",
    "Storage",
]

import logging
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Type, TypeVar

from redis.asyncio import Redis

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

    @abstractmethod
    async def is_react2ban_enabled(self, chat_id: int, message_id: int) -> bool:
        pass

    @abstractmethod
    async def add_react2ban(self, chat_id: int, message_id: int) -> None:
        _log.debug("react2ban is enabled in chat %d on message %d", chat_id, message_id)

    @abstractmethod
    async def remove_react2ban(self, chat_id: int, message_id: int) -> None:
        _log.debug("react2ban is disabled in chat %d on message %d", chat_id, message_id)

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


class RedisStorage(Storage):
    def __init__(self, host: str, port: int, db: int) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._pool: Redis = Redis(host=host, port=port, db=db, decode_responses=True)
        super().__init__()

    async def connect(self) -> None:
        if not await self._pool.ping():
            raise RuntimeError("Redis server is not available")

    async def close(self) -> None:
        await self._pool.close()

    @staticmethod
    def _key(*parts: Any) -> str:
        return "userbot:" + ":".join(map(str, parts))

    async def enable_hook(self, name: str, chat_id: int) -> None:
        await self._pool.sadd(self._key("hooks", name), chat_id)
        await super().enable_hook(name, chat_id)

    async def disable_hook(self, name: str, chat_id: int) -> None:
        await self._pool.srem(self._key("hooks", name), chat_id)
        await super().disable_hook(name, chat_id)

    async def is_hook_enabled(self, name: str, chat_id: int) -> bool:
        return await self._pool.sismember(self._key("hooks", name), chat_id)

    async def list_enabled_hooks(self, chat_id: int) -> list[str]:
        return await self._pool.smembers(self._key("hooks"))

    async def is_react2ban_enabled(self, chat_id: int, message_id: int) -> bool:
        return await self._pool.sismember(self._key("react2ban", chat_id), message_id)

    async def add_react2ban(self, chat_id: int, message_id: int) -> None:
        await self._pool.sadd(self._key("react2ban", chat_id), message_id)
        await super().add_react2ban(chat_id, message_id)

    async def remove_react2ban(self, chat_id: int, message_id: int) -> None:
        await self._pool.srem(self._key("react2ban", chat_id), message_id)
        await super().remove_react2ban(chat_id, message_id)
