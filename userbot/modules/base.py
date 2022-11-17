__all__ = [
    "BaseHandler",
    "BaseModule",
    "HandlerT",
]

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Generic, NamedTuple, TypeVar

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified, MessageTooLong
from pyrogram.filters import Filter
from pyrogram.handlers.handler import Handler
from pyrogram.types import Message

from ..constants import Icons
from ..middleware_manager import Middleware, MiddlewareManager
from ..translation import Translation
from ..utils import async_partial

_log = logging.getLogger(__name__)

HandlerT = TypeVar("HandlerT", bound=Callable[..., Awaitable[str | None]])


class _NewMessage(NamedTuple):
    message: Message
    edited: bool


class BaseHandler(ABC):
    def __init__(
        self,
        *,
        handler: HandlerT,
        handle_edits: bool,
        waiting_message: str | None,
        timeout: int | None,
    ) -> None:
        self._handler = handler
        self._handle_edits = handle_edits
        self._waiting_message = waiting_message
        self._timeout = timeout

        self._signature = inspect.signature(self.handler)

    @property
    def handler(self) -> HandlerT:
        return self._handler

    @property
    def handle_edits(self) -> bool:
        return self._handle_edits

    @property
    def waiting_message(self) -> str | None:
        return self._waiting_message

    @property
    def timeout(self) -> int | None:
        return self._timeout

    @staticmethod
    async def _edit_or_reply_html_text(message: Message, text: str, **kwargs: Any) -> _NewMessage:
        """Edit a message if it's outgoing, otherwise reply to it."""
        if message.outgoing or message.from_user is not None and message.from_user.is_self:
            return _NewMessage(
                message=await message.edit_text(text, parse_mode=ParseMode.HTML, **kwargs),
                edited=True,
            )
        return _NewMessage(
            message=await message.reply_text(text, parse_mode=ParseMode.HTML, **kwargs),
            edited=False,
        )

    async def _invoke_handler(self, data: dict[str, Any]) -> str | None:
        """Filter data and call the handler."""
        suitable_kwargs = {}
        # TODO (2022-11-01): check all params are passed, otherwise raise an error
        for name, param in self._signature.parameters.items():
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                suitable_kwargs = data  # pass all kwargs
                break
            if name in data:
                suitable_kwargs[name] = data[name]
        return await self.handler(**suitable_kwargs)

    async def _send_waiting_message(self, data: dict[str, Any]) -> None:
        """Edit a message after some time to show that the bot is working on the message."""
        await asyncio.sleep(0.75)
        message: Message = data["message"]
        icons: type[Icons] = data["icons"]
        tr: Translation = data["tr"]
        _ = tr.gettext
        if self.waiting_message is not None:
            # Waiting messages may be marked for translation, so we need to translate them here.
            text = _(self.waiting_message).strip()
        else:
            text = _("<i>Userbot is processing the message...</i>")
        message, edited = await self._edit_or_reply_html_text(message, f"{icons.WATCH} {text}")
        if not edited:
            data["new_message"] = message

    async def _timed_out_handler(self, data: dict[str, Any]) -> str | None:
        """Handles the case when the handler times out. Reports an error by default."""
        _log.warning(
            f"Handler %r timed out",
            self,
            exc_info=True,
            extra={"data": data},
        )
        icons: type[Icons] = data["icons"]
        tr: Translation = data["tr"]
        _ = tr.gettext
        __ = tr.ngettext
        # cannot be None as `TimeoutError` is raised only if timeout is not None
        timeout: int = self.timeout
        return _(
            "{icon} <b>Timed out after {timeout} while processing the message.</b>\n"
            "<i>More info can be found in logs.</i>"
        ).format(
            icon=icons.STOP,
            timeout=__("{timeout} second", "{timeout} seconds", timeout).format(timeout=timeout),
        )

    async def _invoke_with_timeout(self, data: dict[str, Any]) -> str | None:
        """Call the handler with a timeout."""
        waiting_task = asyncio.create_task(self._send_waiting_message(data))
        try:
            return await asyncio.wait_for(self._invoke_handler(data), timeout=self.timeout)
        except asyncio.TimeoutError:
            waiting_task.cancel()
            return await self._timed_out_handler(data)
        finally:
            waiting_task.cancel()

    async def _exception_handler(self, e: Exception, data: dict[str, Any]) -> str | None:
        """Handle exceptions raised by the handler. Re-raises an exception by default."""
        raise

    async def _message_too_long_handler(self, result: str, data: dict[str, Any]) -> None:
        """Handles the case when the result is too long to be sent.
        Re-raises an exception by default."""
        raise

    async def _message_not_modified_handler(self, result: str, data: dict[str, Any]) -> None:
        """Handles the case when the result doesn't modify the message.
        Logs a warning to console by default."""
        _log.warning(
            "Message was not modified while executing handler %r",
            self,
            exc_info=True,
            extra={"data": data},
        )
        return

    async def _result_handler(self, result: str, data: dict[str, Any]) -> None:
        """Handle the result of the handler. Edits a message by default."""
        actual_message: Message = data.get("new_message", data["message"])
        try:
            await self._edit_or_reply_html_text(actual_message, result)
        except MessageTooLong:
            await self._message_too_long_handler(result, data)
        except MessageNotModified:
            await self._message_not_modified_handler(result, data)

    async def __call__(
        self,
        client: Client,
        message: Message,
        *,
        middleware: MiddlewareManager[str | None],
    ) -> None:
        data = {
            "client": client,
            "message": message,
        }
        try:
            result = await middleware(self._invoke_with_timeout, data)
        except Exception as e:
            result = await self._exception_handler(e, data)
        if not result:  # empty string or None
            return  # nothing to send or edit
        await self._result_handler(result, data)


_HT = TypeVar("_HT", bound=BaseHandler)


class BaseModule(Generic[_HT]):
    """Base class for modules"""

    def __init__(self):
        self._handlers: list[_HT] = []
        self._middleware: MiddlewareManager[str | None] = MiddlewareManager()

    def add_handler(self, handler: _HT) -> None:
        self._handlers.append(handler)

    def add_submodule(self, module: "BaseModule[_HT]") -> None:
        if module is self:
            raise ValueError("Cannot add a module to itself")
        self._handlers.extend(module._handlers)
        if module._middleware.has_handlers:
            raise NotImplementedError(
                "Submodule has middlewares registered, this is not supported yet"
            )

    def add_middleware(self, middleware: Middleware[str | None]) -> None:
        self._middleware.register(middleware)

    @abstractmethod
    def _create_handlers_filters(self, handler: _HT) -> tuple[list[type[Handler]], Filter]:
        """Create Pyrogram handlers and filters for the given handler."""
        pass

    def register(self, client: Client) -> None:
        for handler in self._handlers:
            handlers, filters = self._create_handlers_filters(handler)
            for handler_cls in handlers:
                client.add_handler(
                    handler_cls(
                        async_partial(handler.__call__, middleware=self._middleware),
                        filters,
                    ),
                )
