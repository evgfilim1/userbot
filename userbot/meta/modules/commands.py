from __future__ import annotations

__all__ = [
    "CommandT",
    "CommandsHandler",
    "CommandsModule",
]

import functools
import html
import inspect
import logging
import operator
import re
from io import BytesIO
from pathlib import Path
from traceback import FrameSummary, extract_tb
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Iterable, TypeAlias, overload

from httpx import AsyncClient, HTTPError
from lark import Lark
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.filters import Filter
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.handlers.handler import Handler
from pyrogram.types import Message

from ...constants import Icons
from ...utils import Translation
from ..args_parser import create_args_parser_grammar
from ..usage_parser import parser as usage_parser
from .base import BaseHandler, BaseModule, HandlerT

if TYPE_CHECKING:
    from ...middlewares import CommandObject

_DEFAULT_TIMEOUT = 30

_log = logging.getLogger(__name__)

CommandT: TypeAlias = str | re.Pattern[str]


def _get_handler_docstring(handler: HandlerT) -> str | None:
    """Gets the docstring of the handler."""
    return inspect.getdoc(inspect.unwrap(handler))


def _extract_frames(traceback: TracebackType) -> tuple[FrameSummary, FrameSummary]:
    """Extracts the last frames from the traceback.

    Returns a tuple of the last own frame, and the last frame in traceback.
    """
    last_own_frame: FrameSummary | None = None
    last_frame: FrameSummary | None = None
    # Path(__file__):         .../userbot/meta/modules/commands.py
    # Path(__file__).parents: ...   [2]   [1]    [0]
    own_package_path = Path(__file__).parents[2]
    for frame in extract_tb(traceback):
        if frame.filename is not None and own_package_path in Path(frame.filename).parents:
            last_own_frame = frame
        last_frame = frame
    if last_frame is None:
        raise RuntimeError("Unable to extract frames from traceback")
    if last_own_frame is None:
        raise RuntimeError("Unable to extract own frames from traceback")
    return last_own_frame, last_frame


def _format_frames(last_own_frame: FrameSummary, last_frame: FrameSummary) -> str:
    """Formats the traceback to a string."""
    tb = '  <...snip...>\n  File "{}", line {}, in {}\n    {}\n'.format(
        last_own_frame.filename,
        last_own_frame.lineno,
        last_own_frame.name,
        last_own_frame.line.strip(),
    )
    if last_frame is not last_own_frame:
        tb += '  <...snip...>\n  File "{}", line {}, in {}\n    {}\n'.format(
            last_frame.filename,
            last_frame.lineno,
            last_frame.name,
            last_frame.line.strip(),
        )
    return tb


def _format_exception(exc: Exception) -> str:
    """Formats the exception to a string."""
    res = type(exc).__qualname__
    if exc_value := str(exc):
        res += f": {exc_value}"
    return res


class CommandsHandler(BaseHandler):
    def __init__(
        self,
        *,
        commands: Iterable[CommandT],
        prefix: str | None,
        handler: HandlerT,
        usage: str,
        reply_required: bool,
        summary: str | None,
        description: str | None,
        category: str | None,
        hidden: bool,
        handle_edits: bool,
        waiting_message: str | None,
        timeout: int | None,
    ) -> None:
        if next(iter(commands), None) is None:
            raise ValueError("No commands specified")

        super().__init__(
            handler=handler,
            handle_edits=handle_edits,
            waiting_message=waiting_message,
            timeout=timeout,
        )
        self.commands = commands
        self.prefix = prefix
        self.usage = usage
        self.usage_tree = usage_parser.parse(usage)
        self.args_parser = Lark(
            create_args_parser_grammar(self.usage_tree),
            maybe_placeholders=False,
        )
        self.reply_required = reply_required
        self.summary = summary
        self.description = description
        self.category = category
        self.hidden = hidden

        if self.description is not None:
            self.description = self.description.strip()

    def __repr__(self) -> str:
        commands = self.commands
        prefix = self.prefix
        usage = self.usage
        reply_required = self.reply_required
        category = self.category
        hidden = self.hidden
        handle_edits = self.handle_edits
        timeout = self.timeout
        return (
            f"<{self.__class__.__name__}"
            f" {commands=}"
            f" {prefix=}"
            f" {usage=}"
            f" {reply_required=}"
            f" {category=}"
            f" {hidden=}"
            f" {handle_edits=}"
            f" {timeout=}"
            f">"
        )

    def format_usage(self, *, full: bool = False) -> str:
        """Formats the usage of the command."""
        commands: list[str] = []
        for command in self.commands:
            match command:
                case re.Pattern(pattern=pattern):
                    commands.append(pattern)
                case str():
                    commands.append(command)
                case _:
                    raise AssertionError(f"Unexpected command type: {type(command)}")
        res = ""
        if self.reply_required:
            res += "<in reply> "
        res += "|".join(commands) + " "
        if self.usage:
            res += f"{self.usage} "
        if self.summary:
            res += f"— {self.summary}"
        if full and self.description:
            res += f"\n\n{self.description}"
        return res.rstrip()

    async def _exception_handler(self, e: Exception, data: dict[str, Any]) -> str | None:
        """Handles exceptions raised by the command handler."""
        message: Message = data["message"]
        message_text = message.text
        _log.exception(
            "An error occurred during executing %r",
            message_text,
            extra={"data": data},
        )
        if isinstance(e, MessageNotModified):
            return None

        client: Client = data["client"]
        # In case one of the middlewares failed, we need to fill in the missing data with
        # the fallback values
        if "tr" not in data:
            data["tr"] = Translation(None)
        tr: Translation = data["tr"]
        _ = tr.gettext
        traceback_chat: int | str | None = data.get("traceback_chat", None)

        traceback = _format_frames(*_extract_frames(e.__traceback__))
        traceback += _format_exception(e)
        traceback = f"<pre><code class='language-python'>{html.escape(traceback)}</code></pre>"
        header = _("{icon} <b>An error occurred during executing command.</b>").format(
            icon=Icons.STOP,
        )
        if traceback_chat is None:
            footer = _(
                "<b>Command:</b> <code>{message_text}</code>\n"
                "<b>Traceback:</b>\n{traceback}\n\n"
                "<i>More info can be found in the logs.</i>"
            ).format(
                message_text=html.escape(message_text),
                traceback=traceback,
            )
        else:
            await client.send_message(
                chat_id=traceback_chat,
                text="{header}\n\n{footer}".format(
                    header=header,
                    footer=_("<b>Message:</b> {msg}\n<b>Traceback:</b>\n{traceback}").format(
                        msg=(
                            message.link
                            if message.chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL)
                            else f"<code>{html.escape(message_text)}</code>"
                        ),
                        traceback=traceback,
                    ),
                ),
            )
            exception = f"{e.__class__.__name__}: {e}"
            footer = _(
                "<b>Command:</b> <code>{message_text}</code>\n"
                "<b>Exception:</b> <code>{exception}</code>\n\n"
                "<i>More info can be found in the logs or in the traceback chat.</i>"
            ).format(message_text=html.escape(message_text), exception=html.escape(exception))
        return f"{header}\n\n{footer}"

    async def _message_too_long_handler(self, result: str, data: dict[str, Any]) -> None:
        message: Message = data["message"]
        tr: Translation = data["tr"]
        _ = tr.gettext
        text = _(
            "{icon} <b>Successfully executed.</b>\n\n"
            "<b>Command:</b> <code>{message_text}</code>\n\n"
            "<b>Result:</b>"
        ).format(icon=Icons.INFO, message_text=html.escape(message.text))
        async with AsyncClient(base_url="https://nekobin.com/") as nekobin:
            try:
                res = await nekobin.post("/api/documents", json={"content": result})
                res.raise_for_status()
            except HTTPError:
                await message.edit(
                    _("{text} <i>See reply.</i>").format(text=text),
                    parse_mode=ParseMode.HTML,
                )
                await message.reply_document(
                    BytesIO(result.encode("utf-8")),
                    file_name="result.html",
                )
            else:
                url = f"{nekobin.base_url.join(res.json()['result']['key'])}.html"
                await message.edit(
                    f"{text} {url}",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )

    @property
    def _sort_key(self) -> tuple[str, str]:
        """Returns a key to use for sorting commands."""
        category = self.category or ""
        command = next(iter(self.commands))
        match command:
            case re.Pattern(pattern=pattern):
                cmd = pattern
            case str():
                cmd = command
            case _:
                raise AssertionError(f"Unexpected command type: {type(command)}")
        return category, cmd

    # Implemented for sorting with `sorted(...)`
    def __lt__(self, other: CommandsHandler) -> bool | NotImplemented:
        if not isinstance(other, CommandsHandler):
            return NotImplemented
        return self._sort_key < other._sort_key


class CommandsModule(BaseModule[CommandsHandler]):
    def __init__(
        self,
        category: str | None = None,
        *,
        default_prefix: str | None = None,
        ensure_middlewares_registered: bool = False,
    ):
        super().__init__()
        self._category = category
        self._default_prefix = default_prefix
        self._ensure_middlewares_registered = ensure_middlewares_registered

    @overload
    def add(
        self,
        command: CommandT,
        /,
        *commands: CommandT,
        prefix: str | None = None,
        usage: str = "",
        reply_required: bool = False,
        doc: str | None = None,
        category: str | None = None,
        hidden: bool = False,
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
        command: CommandT,
        /,
        *commands: CommandT,
        prefix: str | None = None,
        usage: str = "",
        reply_required: bool = False,
        doc: str | None = None,
        category: str | None = None,
        hidden: bool = False,
        handle_edits: bool = True,
        waiting_message: str | None = None,
        timeout: int | None = _DEFAULT_TIMEOUT,
    ) -> None:
        # usage as a function
        pass

    def add(
        self,
        command_or_callable: CommandT | HandlerT,
        /,
        *commands: CommandT,
        prefix: str | None = None,
        usage: str = "",
        reply_required: bool = False,
        doc: str | None = None,
        category: str | None = None,
        hidden: bool = False,
        handle_edits: bool = True,
        waiting_message: str | None = None,
        timeout: int | None = _DEFAULT_TIMEOUT,
    ) -> Callable[[HandlerT], HandlerT] | None:
        """Registers a command handler. Can be used as a decorator or as a registration function.

        Example:
            Example usage as a decorator::

                commands = CommandsModule()
                @commands.add("start", "help")
                async def start_command(message: Message, command: CommandObject) -> str:
                    return "Hello!"

            Example usage as a function::

                commands = CommandsModule()
                def start_command(message: Message, command: CommandObject) -> str:
                    return "Hello!"
                commands.add(start_command, "start", "help")

        Returns:
            The original handler function if used as a decorator, otherwise `None`.
        """

        def decorator(handler: HandlerT) -> HandlerT:
            docstring = doc or _get_handler_docstring(handler)
            if docstring is not None:
                summary, __, description = docstring.partition("\n\n")
                if description:
                    description = re.sub(r"([^\n])\n([^\n])", r"\1 \2", description)
                    description = re.sub(r"([^\n])\n\n([^\n])", r"\1\n\2", description)
                else:
                    description = None
            else:
                summary, description = None, None
            self.add_handler(
                CommandsHandler(
                    commands=commands,
                    prefix=prefix,
                    handler=handler,
                    usage=usage,
                    reply_required=reply_required,
                    summary=summary,
                    description=description,
                    category=category or self._category,
                    hidden=hidden,
                    handle_edits=handle_edits,
                    waiting_message=waiting_message,
                    timeout=timeout,
                )
            )
            return handler

        if callable(command_or_callable):
            if len(commands) == 0:
                raise ValueError("No commands specified")
            decorator(command_or_callable)
            return

        commands = (command_or_callable, *commands)
        return decorator

    async def _help_handler(self, command: CommandObject, tr: Translation) -> str:
        """Sends help for all commands or for a specific one."""
        _ = tr.gettext
        if query := command.args["command"]:
            for h in self._handlers:
                for cmd in h.commands:
                    match cmd:
                        case re.Pattern() as pattern:
                            matches = pattern.fullmatch(query) is not None
                        case str():
                            matches = cmd == query
                        case _:
                            raise AssertionError(f"Unexpected command type: {type(cmd)}")
                    if matches:
                        usage = h.format_usage(full=True)
                        return _("<b>Help for {query}:</b>\n{usage}").format(
                            query=html.escape(query),
                            usage=html.escape(usage),
                        )
            else:
                return f"<b>No help found for {query}</b>"
        text = _("<b>List of userbot commands available:</b>") + "\n\n"
        prev_cat = ""
        for handler in sorted(self._handlers):
            if handler.hidden:
                continue
            usage = handler.format_usage()
            if (handler.category or "") != prev_cat:
                text += f"\n<i>{handler.category}:</i>\n"
                prev_cat = handler.category
            text += f"• {html.escape(usage)}\n"
        # This will happen if there are no handlers without category
        text = text.replace("\n\n\n", "\n\n")
        return text

    def _check_duplicates(self) -> None:
        """Checks for duplicate commands and raises an error if any are found."""
        commands = set()
        for handler in self._handlers:
            for cmd in handler.commands:
                if cmd in commands:
                    raise ValueError(f"Duplicate command: {cmd}")
                commands.add(cmd)

    def _set_prefix(self) -> None:
        """Sets the prefix for all handlers if not set."""
        if self._default_prefix is None:
            raise ValueError("No default prefix specified")
        for handler in self._handlers:
            if handler.prefix is None:
                handler.prefix = self._default_prefix

    def _create_handlers_filters(
        self,
        handler: CommandsHandler,
    ) -> tuple[list[type[Handler]], Filter]:
        f: list[Filter] = []
        for cmd in handler.commands:
            if isinstance(cmd, re.Pattern):
                command_re = re.compile(
                    f"^[{re.escape(handler.prefix)}]{cmd.pattern}",
                    flags=cmd.flags,
                )
                f.append(filters.regex(command_re))
            elif isinstance(cmd, str):
                f.append(filters.command(cmd, prefixes=handler.prefix))
            else:
                raise AssertionError(f"Unexpected command type: {type(cmd)}")
        h: list[type[Handler]] = [MessageHandler]
        if handler.handle_edits:
            h.append(EditedMessageHandler)
        return h, functools.reduce(operator.or_, f) & filters.me & ~filters.scheduled

    def register(self, client: Client) -> None:
        """Registers the module with the client."""
        self.add(
            self._help_handler,
            "help",
            usage="[command]",
            category="About",
        )
        if self._ensure_middlewares_registered:
            # Prevent circular import
            from ...middlewares import translate_middleware

            # These middlewares are expected by the base module to be registered
            if translate_middleware not in self._middleware:
                self.add_middleware(translate_middleware)
        self._set_prefix()
        self._check_duplicates()
        super().register(client)
