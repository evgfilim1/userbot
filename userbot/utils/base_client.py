__all__ = [
    "BaseClient",
]

from abc import ABC
from types import TracebackType
from typing import ClassVar, Self, Type

from httpx import AsyncClient


class BaseClient(ABC):
    _base_url: ClassVar[str]

    def __init__(self) -> None:
        self._client = AsyncClient(base_url=self.__class__._base_url, http2=True)

    def __init_subclass__(cls, **kwargs):
        if (base_url := kwargs.get("base_url", None)) is None:
            raise TypeError(
                "base_url is required\n"
                "`class {cls.__name__}(BaseClient, base_url='https://example.com'): ...`"
            )
        super().__init_subclass__()
        cls._base_url = base_url

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._client.aclose()
