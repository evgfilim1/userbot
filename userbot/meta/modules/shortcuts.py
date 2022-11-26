__all__ = [
    "ShortcutsModule",
]

import re
from typing import Any, Callable, overload

from pyrogram import ContinuePropagation, filters
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.handlers.handler import Handler
from pyrogram.types import Message

from .base import BaseHandler, BaseModule, HandlerT

_DEFAULT_TIMEOUT = 5


class ShortcutsHandler(BaseHandler):
    def __init__(
        self,
        *,
        pattern: re.Pattern[str],
        handler: HandlerT,
        handle_edits: bool,
        waiting_message: str | None,
        timeout: int | None,
    ) -> None:
        super().__init__(
            handler=handler,
            handle_edits=handle_edits,
            waiting_message=waiting_message,
            timeout=timeout,
        )
        self.pattern = pattern

    def __repr__(self) -> str:
        pattern = self.pattern
        handle_edits = self.handle_edits
        timeout = self.timeout
        return f"<{self.__class__.__name__} {pattern=} {handle_edits=} {timeout=}>"

    async def _invoke_handler(self, data: dict[str, Any]) -> str | None:
        message: Message = data["message"]
        raw_text = message.text or message.caption
        if raw_text is None:
            return
        text = raw_text.html
        while match := self.pattern.search(text):
            data["match"] = match
            if (result := await super()._invoke_handler(data)) is not None:
                text = f"{text[:match.start()]}{result}{text[match.end():]}"
        return text

    async def _timed_out_handler(self, data: dict[str, Any]) -> str | None:
        raise

    async def _result_handler(self, result: str, data: dict[str, Any]) -> None:
        await super()._result_handler(result, data)
        raise ContinuePropagation  # allow other shortcut handlers to run


class ShortcutsModule(BaseModule):
    @overload
    def add(
        self,
        pattern: str | re.Pattern[str],
        none: None = None,
        /,
        *,
        handle_edits: bool = True,
        waiting_message: str | None = None,
        timeout: int | None = _DEFAULT_TIMEOUT,
    ) -> Callable[[HandlerT], HandlerT]:
        # usage as a decorator
        pass

    @overload
    def add(
        self,
        callable_: HandlerT,
        pattern: str | re.Pattern[str],
        /,
        *,
        handle_edits: bool = True,
        waiting_message: str | None = None,
        timeout: int | None = _DEFAULT_TIMEOUT,
    ) -> None:
        # usage as a function
        pass

    def add(
        self,
        callable_or_pattern: HandlerT | str | re.Pattern[str],
        pattern: str | re.Pattern[str] | None = None,
        /,
        *,
        handle_edits: bool = True,
        waiting_message: str | None = None,
        timeout: int | None = _DEFAULT_TIMEOUT,
    ) -> Callable[[HandlerT], HandlerT] | None:
        """Registers a shortcut handler. Can be used as a decorator or as a registration function.

        Example:
            Example usage as a decorator::

                shortcuts = ShortcutsModule()
                @shortcuts.add(r"(hello|hi)")
                async def hello_shortcut(message: Message, command: CommandObject) -> str:
                    return "Hello!"

            Example usage as a function::

                shortcuts = ShortcutsModule()
                def hello_shortcut(message: Message, command: CommandObject) -> str:
                    return "Hello!"
                shortcuts.add(hello_shortcut, r"(hello|hi)")

        Returns:
            The original handler function if used as a decorator, otherwise `None`.
        """

        def decorator(handler: HandlerT) -> HandlerT:
            if isinstance(pattern, str):
                p = re.compile(pattern)
            else:
                p = pattern
            self.add_handler(
                ShortcutsHandler(
                    pattern=p,
                    handler=handler,
                    handle_edits=handle_edits,
                    waiting_message=waiting_message,
                    timeout=timeout,
                )
            )
            return handler

        if callable(callable_or_pattern):
            if pattern is None:
                raise ValueError("No pattern specified")
            decorator(callable_or_pattern)
            return

        pattern = callable_or_pattern
        return decorator

    def _create_handlers_filters(
        self,
        handler: ShortcutsHandler,
    ) -> tuple[list[type[Handler]], filters.Filter]:
        h: list[type[Handler]] = [MessageHandler]
        if handler.handle_edits:
            h.append(EditedMessageHandler)
        return h, filters.outgoing & ~filters.scheduled & filters.regex(handler.pattern)
