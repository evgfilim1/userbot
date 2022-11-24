from __future__ import annotations

__all__ = [
    "async_partial",
    "SecretStr",
    "StatsController",
    "Unset",
]

import functools
import time
from collections import UserString
from typing import Any, Awaitable, Callable, ClassVar, TypeVar

_T = TypeVar("_T")


class Unset:
    """A singleton to represent an unset value"""

    _instance: ClassVar[Unset | None] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Unset:
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __repr__(self) -> str:
        return "<unset>"

    def __str__(self) -> str:
        return repr(self)


def async_partial(
    func: Callable[..., Awaitable[_T]],
    *args: Any,
    **kwargs: Any,
) -> Callable[..., Awaitable[_T]]:
    """Create a partial function that is awaitable."""

    @functools.wraps(func)
    async def wrapper(*args_: Any, **kwargs_: Any) -> _T:
        return await func(*args, *args_, **kwargs, **kwargs_)

    return wrapper


class SecretStr(UserString):
    """A string that doesn't show its value in repr() and str().

    To get the actual value, use the `data` or `value` attribute.
    """

    @property
    def value(self) -> str:
        return self.data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)})"

    def __str__(self) -> str:
        return "******"


class StatsController:
    """A class to store and control the stats of a bot."""

    def __init__(self) -> None:
        self._startup_time: int | None = None

    def startup(self) -> None:
        """Sets the startup time to the current time. Must be done once."""
        if self._startup_time is not None:
            raise RuntimeError("startup() has already been called")
        self._startup_time = int(time.time())

    @property
    def uptime(self) -> int:
        """The uptime of the bot in seconds."""
        return int(time.time()) - self._startup_time
