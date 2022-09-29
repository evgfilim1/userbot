__all__ = [
    "RedisStorage",
    "Storage",
]

import json
import logging
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, AsyncIterable, Awaitable, Callable, NoReturn, Type, TypeAlias, TypeVar

from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from typing_extensions import Self

from .utils import StickerInfo

_T = TypeVar("_T", bound="Storage")
_StickerCache: TypeAlias = dict[str, list[StickerInfo]]
_StickerCacheProvider: TypeAlias = Callable[[], Awaitable[_StickerCache]]

_log = logging.getLogger(__name__)


class Storage(ABC):
    @abstractmethod
    async def connect(self) -> None:
        _log.debug("Storage %r connected", self.__class__.__name__)

    @abstractmethod
    async def close(self) -> None:
        _log.debug("Storage %r disconnected", self.__class__.__name__)

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
        return

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
    async def list_enabled_hooks(self, chat_id: int) -> AsyncIterable[str]:
        yield

    @abstractmethod
    async def is_react2ban_enabled(self, chat_id: int, message_id: int) -> bool:
        pass

    @abstractmethod
    async def add_react2ban(self, chat_id: int, message_id: int) -> None:
        _log.debug("react2ban is enabled in chat %d on message %d", chat_id, message_id)

    @abstractmethod
    async def remove_react2ban(self, chat_id: int, message_id: int) -> None:
        _log.debug("react2ban is disabled in chat %d on message %d", chat_id, message_id)

    @abstractmethod
    async def get_sticker_cache(self) -> _StickerCache:
        pass

    @abstractmethod
    async def wait_sticker_cache(self) -> _StickerCache:
        pass

    @abstractmethod
    async def put_sticker_cache(self, data: _StickerCache, ttl: int = 3600) -> None:
        _log.debug("Sticker cache updated")

    @abstractmethod
    async def sticker_cache_job(
        self,
        provider: _StickerCacheProvider,
        ttl: int = 3600,
    ) -> NoReturn:
        _log.debug("Sticker cache job started, ttl=%d", ttl)

    @abstractmethod
    async def get_message(self, key: str) -> tuple[str, str] | None:
        pass

    @abstractmethod
    async def save_message(self, key: str, content: str, message_type: str) -> None:
        _log.debug("%r %s message saved", key, message_type)

    @abstractmethod
    async def saved_messages(self) -> AsyncIterable[str]:
        yield

    @abstractmethod
    async def delete_message(self, key: str) -> None:
        _log.debug("%r message deleted", key)

    @abstractmethod
    async def get_chat_language(self, chat_id: int) -> str | None:
        pass

    @abstractmethod
    async def set_chat_language(self, chat_id: int, language: str) -> None:
        _log.debug("Language %r set for chat %d", language, chat_id)


class RedisStorage(Storage):
    def __init__(self, host: str, port: int, db: int, password: str | None = None) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._pool: Redis = Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )
        self._pubsub = self._pool.pubsub(ignore_subscribe_messages=True)
        super().__init__()

    async def connect(self) -> None:
        if not await self._pool.ping():
            raise RuntimeError("Redis server is not available")
        await self._pool.config_set("notify-keyspace-events", "Kx$")
        await super().connect()

    async def close(self) -> None:
        await self._pubsub.reset()
        await self._pool.close()
        await super().close()

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

    async def list_enabled_hooks(self, chat_id: int) -> AsyncIterable[str]:
        async for hook in self._pool.scan_iter(match=self._key("hooks", "*"), _type="set"):
            hook_name = hook.rsplit(":", 1)[-1]
            if await self.is_hook_enabled(hook_name, chat_id):
                yield hook_name

    async def is_react2ban_enabled(self, chat_id: int, message_id: int) -> bool:
        return await self._pool.sismember(self._key("react2ban", chat_id), message_id)

    async def add_react2ban(self, chat_id: int, message_id: int) -> None:
        await self._pool.sadd(self._key("react2ban", chat_id), message_id)
        await super().add_react2ban(chat_id, message_id)

    async def remove_react2ban(self, chat_id: int, message_id: int) -> None:
        await self._pool.srem(self._key("react2ban", chat_id), message_id)
        await super().remove_react2ban(chat_id, message_id)

    async def get_sticker_cache(self) -> _StickerCache:
        cache = await self._pool.get(self._key("stickers"))
        if cache is None:
            return {}
        return json.loads(cache)

    async def wait_sticker_cache(self) -> _StickerCache:
        pubsub: PubSub
        async with self._pool.pubsub(ignore_subscribe_messages=True) as pubsub:
            await pubsub.subscribe(f"__keyspace@{self._db}__:{self._key('stickers')}")
            async for message in pubsub.listen():
                if message["data"] == "set":
                    return await self.get_sticker_cache()

    async def put_sticker_cache(self, data: _StickerCache, ttl: int = 3600) -> None:
        await self._pool.set(self._key("stickers"), json.dumps(data, ensure_ascii=False), ex=ttl)
        await super().put_sticker_cache(data, ttl)

    async def sticker_cache_job(
        self,
        provider: _StickerCacheProvider,
        ttl: int = 3600,
    ) -> NoReturn:
        await super().sticker_cache_job(provider, ttl)
        key = self._key("stickers")
        await self._pubsub.subscribe(f"__keyspace@{self._db}__:{key}")
        async for message in self._pubsub.listen():
            if message["data"] != "expired":
                continue
            _log.debug("Sticker cache expired, updating...")
            await self.put_sticker_cache(await provider(), ttl)

    async def get_message(self, key: str) -> tuple[str, str] | None:
        data = await self._pool.hgetall(self._key("messages", key))
        if not data:
            return None
        return data["content"], data["type"]

    async def save_message(self, key: str, content: str, message_type: str) -> None:
        await self._pool.hset(
            self._key("messages", key),
            mapping={"content": content, "type": message_type},
        )
        await super().save_message(key, content, message_type)

    async def saved_messages(self) -> AsyncIterable[str]:
        async for key in self._pool.scan_iter(match=self._key("messages", "*"), _type="hash"):
            yield key.rsplit(":", 1)[-1]

    async def delete_message(self, key: str) -> None:
        await self._pool.delete(self._key("messages", key))
        await super().delete_message(key)

    async def get_chat_language(self, chat_id: int) -> str | None:
        return await self._pool.get(self._key("language", chat_id))

    async def set_chat_language(self, chat_id: int, language: str) -> None:
        await self._pool.set(self._key("language", chat_id), language)
        await super().set_chat_language(chat_id, language)
