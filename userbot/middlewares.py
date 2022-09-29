from typing import Any

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
