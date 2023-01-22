__all__ = [
    "Handler",
    "Middleware",
    "MiddlewareManager",
]

import functools
from abc import abstractmethod
from typing import Any, Protocol, TypeVar

_ReturnT = TypeVar("_ReturnT")


class Handler(Protocol[_ReturnT]):
    async def __call__(self, data: dict[str, Any]) -> _ReturnT:
        pass


class Middleware(Protocol[_ReturnT]):
    # https://peps.python.org/pep-0544/#explicitly-declaring-implementation
    @abstractmethod
    async def __call__(
        self,
        handler: Handler[_ReturnT],
        data: dict[str, Any],
    ) -> _ReturnT:
        pass


class MiddlewareManager(Middleware[_ReturnT]):
    # noinspection PyProtocol
    # https://youtrack.jetbrains.com/issue/PY-49246
    def __init__(self):
        self._middlewares: list[Middleware[_ReturnT]] = []

    def register(self, middleware: Middleware[_ReturnT]) -> None:
        self._middlewares.append(middleware)

    def chain(self, handler: Handler[_ReturnT]) -> Handler[_ReturnT]:
        for middleware in reversed(self._middlewares):
            handler = functools.partial(middleware, handler)
        return handler

    async def __call__(
        self,
        handler: Handler[_ReturnT],
        data: dict[str, Any],
    ) -> _ReturnT:
        return await self.chain(handler)(data)

    @property
    def has_handlers(self) -> bool:
        return len(self._middlewares) > 0

    def __contains__(self, item: Middleware[_ReturnT]) -> bool:
        return item in self._middlewares
