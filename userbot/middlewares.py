from typing import Any

from .constants import DefaultIcons, PremiumIcons
from .middleware_manager import Handler, Middleware


class KwargsMiddleware(Middleware[str | None]):
    def __init__(self, kwargs: dict[str | Any]):
        self.kwargs = kwargs

    async def __call__(
        self,
        handler: Handler[str | None],
        data: dict[str | Any],
    ) -> str | None:
        data.update(self.kwargs)
        return await handler(data)


async def icon_middleware(
    handler: Handler[str | None],
    data: dict[str | Any],
) -> str | None:
    data["icons"] = PremiumIcons if data["client"].me.is_premium else DefaultIcons
    return await handler(data)
