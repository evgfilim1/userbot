__all__ = [
    "icon_middleware",
    "KwargsMiddleware",
    "parse_command_middleware",
    "translate_middleware",
    "update_command_stats_middleware",
]

from asyncio import create_task
from typing import Any

from pyrogram.types import Message

from .constants import DefaultIcons, PremiumIcons
from .middleware_manager import Handler, Middleware
from .modules import CommandObject
from .modules.commands import CommandsHandler
from .storage import Storage
from .translation import Translation


class KwargsMiddleware(Middleware[str | None]):
    """Updates middleware data with the given kwargs."""

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
    """Provides the icons to the handler."""
    data["icons"] = PremiumIcons if data["client"].me.is_premium else DefaultIcons
    return await handler(data)


async def translate_middleware(
    handler: Handler[str | None],
    data: dict[str | Any],
) -> str | None:
    """Provides the translation function to the handler."""
    storage: Storage = data["storage"]
    message: Message = data["message"]
    lang = await storage.get_chat_language(message.chat.id)
    if lang is None and message.from_user is not None:
        lang = message.from_user.language_code
    tr = Translation(lang)
    data["lang"] = tr.tr.info().get("language", "en")
    data["tr"] = tr
    return await handler(data)


async def parse_command_middleware(
    handler: Handler[str | None],
    data: dict[str | Any],
) -> str | None:
    """Parses the command and its arguments."""
    message: Message = data["message"]
    handler_obj: CommandsHandler = data["handler_obj"]
    command = CommandObject.parse(message.text, handler_obj.commands)
    data["command"] = command
    return await handler(data)


async def update_command_stats_middleware(
    handler: Handler[str | None],
    data: dict[str | Any],
) -> str | None:
    """Updates the command stats."""
    command: CommandObject = data["command"]
    storage: Storage = data["storage"]
    create_task(storage.command_used(command.command))  # I don't care about the result
    return await handler(data)
