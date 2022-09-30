from typing import Any

from pyrogram.types import Message

from .constants import DefaultIcons, PremiumIcons
from .middleware_manager import Handler, Middleware
from .storage import Storage
from .translation import Translation


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


async def translate_middleware(
    handler: Handler[str | None],
    data: dict[str | Any],
) -> str | None:
    storage: Storage = data["storage"]
    message: Message = data["message"]
    lang = await storage.get_chat_language(message.chat.id)
    if lang is None:
        lang = message.from_user.language_code
    tr = Translation(lang)
    data["lang"] = tr.tr.info().get("language", "en")
    data["tr"] = tr
    return await handler(data)
