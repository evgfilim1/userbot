__all__ = [
    "ShortcutTransformersModule",
]

import re
from dataclasses import dataclass
from typing import Awaitable, Callable

from pyrogram import Client
from pyrogram import filters as flt
from pyrogram.enums import ParseMode
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.types import Message

_TransformHandlerT = Callable[[re.Match[str]], Awaitable[str]]


@dataclass()
class _ShortcutHandler:
    regex: re.Pattern[str]
    handler: _TransformHandlerT
    handle_edits: bool

    async def __call__(self, client: Client, message: Message):
        raw_text = message.text or message.caption
        if raw_text is None:
            return
        text = raw_text.html
        while match := self.regex.search(text):
            if (result := await self.handler(match)) is not None:
                text = f"{text[:match.start()]}{result}{text[match.end():]}"
        await message.edit(text, parse_mode=ParseMode.HTML)
        message.continue_propagation()  # allow other shortcut handlers to run


class ShortcutTransformersModule:
    def __init__(self):
        self._handlers: list[_ShortcutHandler] = []

    def add(
        self,
        pattern: str | re.Pattern[str],
        *,
        handle_edits: bool = True,
    ) -> Callable[[_TransformHandlerT], _TransformHandlerT]:
        def _decorator(f: _TransformHandlerT) -> _TransformHandlerT:
            self.add_handler(
                handler=f,
                pattern=pattern,
                handle_edits=handle_edits,
            )
            return f

        return _decorator

    def add_handler(
        self,
        handler: _TransformHandlerT,
        pattern: str | re.Pattern[str],
        *,
        handle_edits: bool = True,
    ) -> None:
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self._handlers.append(
            _ShortcutHandler(
                regex=pattern,
                handler=handler,
                handle_edits=handle_edits,
            )
        )

    def add_submodule(self, module: "ShortcutTransformersModule") -> None:
        self._handlers.extend(module._handlers)

    def register(self, client: Client) -> None:
        for handler in self._handlers:
            f = flt.outgoing & ~flt.scheduled & flt.regex(handler.regex)
            client.add_handler(MessageHandler(handler.__call__, f))
            if handler.handle_edits:
                client.add_handler(EditedMessageHandler(handler.__call__, f))
