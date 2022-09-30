from __future__ import annotations

import asyncio
import html
import inspect
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from traceback import FrameSummary, extract_tb
from types import TracebackType
from typing import Any, Awaitable, Callable, ParamSpec, Type, TypeAlias, TypeVar

from httpx import AsyncClient, HTTPError
from pyrogram import Client
from pyrogram import filters as flt
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified, MessageTooLong
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.types import Message

from ..constants import DefaultIcons, Icons, PremiumIcons
from ..middleware_manager import Middleware, MiddlewareManager
from ..translation import Translation
from ..utils import async_partial, is_prod

_DEFAULT_PREFIX = "." if is_prod() else ","
_DEFAULT_TIMEOUT = 30

_PS = ParamSpec("_PS")
_RT = TypeVar("_RT")
_CommandT: TypeAlias = list[str] | re.Pattern[str]
_CommandHandlerT: TypeAlias = Callable[_PS, Awaitable[str | None]]

_log = logging.getLogger(__name__)
_nekobin = AsyncClient(base_url="https://nekobin.com/")


def _extract_frames(traceback: TracebackType) -> tuple[FrameSummary, FrameSummary]:
    """Extract the last frames from the traceback.

    Returns a tuple of the last own frame, and the last frame in traceback.
    """
    last_own_frame: FrameSummary | None = None
    last_frame: FrameSummary | None = None
    own_package_name = Path(__file__).parent.parent
    for frame in extract_tb(traceback):
        if frame.filename is not None and own_package_name in Path(frame.filename).parents:
            last_own_frame = frame
        last_frame = frame
    if last_frame is None:
        raise RuntimeError("Unable to extract frames from traceback")
    if last_own_frame is None:
        raise RuntimeError("Unable to extract own frames from traceback")
    return last_own_frame, last_frame


def _format_frames(last_own_frame: FrameSummary, last_frame: FrameSummary) -> str:
    """Format the traceback to a string."""
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
    """Format the exception to a string."""
    res = type(exc).__qualname__
    if exc_value := str(exc):
        res += f": {exc_value}"
    return res


async def _post_to_nekobin(text: str) -> str:
    """Posts the text to nekobin. Returns the URL."""
    res = await _nekobin.post("/api/documents", json={"content": text})
    res.raise_for_status()
    return f"{_nekobin.base_url.join(res.json()['result']['key'])}.html"


def _handle_command_exception(e: Exception, data: dict[str, Any]) -> str:
    """Handles the exception raised by the command."""
    client: Client = data["client"]
    message: Message = data["message"]
    command: CommandObject = data["command"]
    # In case one of the middlewares failed, we need to fill in the missing data with the fallback
    # values
    icons_default = PremiumIcons if client.me.is_premium else DefaultIcons
    icons: Type[Icons] = data.setdefault("icons", icons_default)
    tr: Translation = data.setdefault("tr", Translation(None))
    _ = tr.gettext
    message_text = message.text
    _log.exception(
        "An error occurred during executing %r",
        message_text,
        extra={"command": command},
    )
    tb = _format_frames(*_extract_frames(e.__traceback__))
    tb += _format_exception(e)
    tb = f"<pre><code class='language-python'>{html.escape(tb)}</code></pre>"
    return _(
        "{icon} <b>An error occurred during executing command.</b>\n\n"
        "<b>Command:</b> <code>{message_text}</code>\n"
        "<b>Traceback:</b>\n{tb}\n\n"
        "<i>More info can be found in logs.</i>"
    ).format(
        icon=icons.STOP,
        message_text=html.escape(message_text),
        tb=tb,
    )


async def _handle_message_too_long(result: str, data: dict[str, Any]) -> None:
    """Handles the case when the result is too long to be sent."""
    message: Message = data["message"]
    icons: Type[Icons] = data["icons"]
    tr: Translation = data["tr"]
    _ = tr.gettext
    text = _(
        "{icon} <b>Successfully executed.</b>\n\n"
        "<b>Command:</b> <code>{message_text}</code>\n\n"
        "<b>Result:</b>"
    ).format(icon=icons.INFO, message_text=html.escape(message.text))
    try:
        url = await _post_to_nekobin(result)
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
        await message.edit(
            f"{text} {url}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )


@dataclass()
class CommandObject:
    prefix: str
    command: str
    args: str
    match: re.Match[str] | None

    @property
    def full_command(self) -> str:
        """Returns the full command without arguments."""
        return f"{self.prefix}{self.command}"

    def __str__(self) -> str:
        """Returns the full command with arguments."""
        return f"{self.prefix}{self.command} {self.args}"


@dataclass()
class _CommandHandler:
    commands: _CommandT
    prefix: str
    handler: _CommandHandlerT
    usage: str
    doc: str | None
    category: str | None
    hidden: bool
    handle_edits: bool
    waiting_message: str | None
    timeout: int | None

    def __post_init__(self) -> None:
        if self.doc is not None:
            self.doc = re.sub(r"\n(\n?)\s+", r"\n\1", self.doc).strip()
        self._signature = inspect.signature(self.handler)

    def _parse_command(self, text: str) -> CommandObject:
        """Parses the command from the text."""
        command, _, args = text.partition(" ")
        prefix, command = command[0], command[1:]
        if isinstance(self.commands, re.Pattern):
            m = self.commands.match(command)
        else:
            m = None
        return CommandObject(prefix=prefix, command=command, args=args, match=m)

    async def _call_handler(self, data: dict[str, Any]) -> str | None:
        """Filter data and call the handler."""
        suitable_kwargs = {}
        for name, param in self._signature.parameters.items():
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                suitable_kwargs = data  # pass all kwargs
                break
            if name in data:
                suitable_kwargs[name] = data[name]
        return await self.handler(**suitable_kwargs)

    async def _call_with_timeout(self, data: dict[str, Any]) -> str | None:
        """Call the handler with a timeout."""
        icons: Type[Icons] = data["icons"]
        tr: Translation = data["tr"]
        _ = tr.gettext
        waiting_task = asyncio.create_task(self._send_waiting_message(data))
        try:
            return await asyncio.wait_for(self._call_handler(data), timeout=self.timeout)
        except asyncio.TimeoutError as e:
            message: Message = data["message"]
            command: CommandObject = data["command"]
            _log.warning(
                "Command %r timed out",
                message.text,
                exc_info=e,
                extra={"command": command},
            )
            return _(
                "{icon} <b>Command timed out after {timeout} seconds.</b>\n\n"
                "<b>Command:</b> <code>{message_text}</code>\n\n"
                "<i>More info can be found in logs.</i>"
            ).format(
                icon=icons.STOP,
                timeout=self.timeout,
                message_text=html.escape(message.text),
            )
        finally:
            waiting_task.cancel()

    async def _send_waiting_message(self, data: dict[str, Any]) -> None:
        """Edit a message after some time to show that the bot is working on the command."""
        await asyncio.sleep(0.75)
        message: Message = data["message"]
        icons: Type[Icons] = data["icons"]
        tr: Translation = data["tr"]
        _ = tr.gettext
        if self.waiting_message is not None:
            # Waiting messages are marked for translation, so we need to translate them here.
            text = _(self.waiting_message).strip()
        else:
            text = _("<i>Executing</i> <code>{command}</code>...").format(
                command=html.escape(message.text),
            )
        await message.edit_text(f"{icons.WATCH} {text}", parse_mode=ParseMode.HTML)

    async def __call__(
        self,
        client: Client,
        message: Message,
        *,
        middleware: MiddlewareManager[str | None],
    ) -> None:
        """Entry point for the command handler. Edits and errors are handled here."""
        command = self._parse_command(message.text)
        data = {
            "client": client,
            "message": message,
            "command": command,
        }
        try:
            result = await middleware(self._call_with_timeout, data)
        except Exception as e:
            result = _handle_command_exception(e, data)
        if not result:  # empty string or None
            return  # no reply
        try:
            await message.edit(result, parse_mode=ParseMode.HTML)
        except MessageTooLong:
            await _handle_message_too_long(result, data)
        except MessageNotModified as e:
            _log.warning(
                "Message was not modified while executing %r",
                message.text,
                exc_info=e,
                extra={"command": command},
            )
            if not is_prod():
                # data was modified along the way, so we can access attributes from middlewares
                icons: Type[Icons] = data["icons"]
                tr: Translation = data["tr"]
                _ = tr.gettext
                await message.edit(
                    _(
                        "{result}\n\n"
                        "{icon} <i><b>MessageNotModified</b> was raised, check that there's only"
                        " one instance of userbot is running.</i>"
                    ).format(result=result, icon=icons.WARNING),
                )

    def format_usage(self, *, full: bool = False) -> str:
        match self.commands:
            case re.Pattern(pattern=pattern):
                commands = pattern
            case list(commands):
                commands = "|".join(commands)
            case _:
                raise AssertionError(f"Unexpected command type: {type(self.commands)}")
        usage = f" {self.usage}".rstrip()
        doc = self.doc or ""
        if not full:
            doc = doc.strip().split("\n")[0].strip()
        description = f" — {doc}" if self.doc else ""
        return f"{commands}{usage}{description}"

    def sort_key(self) -> tuple[str, str]:
        """Return a key to sort the commands by."""
        category = self.category or ""
        match self.commands:
            case re.Pattern(pattern=pattern):
                cmd = pattern
            case list(commands):
                cmd = commands[0]
            case _:
                raise AssertionError(f"Unexpected command type: {type(self.commands)}")
        return category, cmd


class CommandsModule:
    def __init__(self, category: str | None = None):
        self._handlers: list[_CommandHandler] = []
        self._category = category
        self._middleware: MiddlewareManager[str | None] = MiddlewareManager()

    def add_handler(
        self,
        handler: _CommandHandlerT,
        command: str | _CommandT,
        prefix: str = _DEFAULT_PREFIX,
        *,
        usage: str = "",
        doc: str | None = None,
        category: str | None = None,
        hidden: bool = False,
        handle_edits: bool = True,
        waiting_message: str | None = None,
        timeout: int | None = _DEFAULT_TIMEOUT,
    ) -> None:
        if isinstance(command, str):
            command = [command]
        self._handlers.append(
            _CommandHandler(
                commands=command,
                prefix=prefix,
                handler=handler,
                usage=usage,
                doc=doc,
                category=category or self._category,
                hidden=hidden,
                handle_edits=handle_edits,
                waiting_message=waiting_message,
                timeout=timeout,
            )
        )

    def add(
        self,
        command: str | _CommandT,
        prefix: str = _DEFAULT_PREFIX,
        *,
        usage: str = "",
        doc: str | None = None,
        category: str | None = None,
        hidden: bool = False,
        handle_edits: bool = True,
        waiting_message: str | None = None,
        timeout: int | None = _DEFAULT_TIMEOUT,
    ) -> Callable[[_CommandHandlerT], _CommandHandlerT]:
        def decorator(f: _CommandHandlerT) -> _CommandHandlerT:
            self.add_handler(
                handler=f,
                command=command,
                prefix=prefix,
                usage=usage,
                doc=doc,
                category=category,
                hidden=hidden,
                handle_edits=handle_edits,
                waiting_message=waiting_message,
                timeout=timeout,
            )
            return f

        return decorator

    def add_middleware(self, middleware: Middleware[str | None]) -> None:
        self._middleware.register(middleware)

    def add_submodule(self, module: CommandsModule) -> None:
        self._handlers.extend(module._handlers)
        if module._middleware.has_handlers:
            raise ValueError("Submodule has middleware, which is not supported")

    def register(
        self,
        client: Client,
        *,
        with_help: bool = False,
    ):
        if with_help:
            self.add_handler(
                self._help_handler,
                command="help",
                usage="[command]",
                doc="Sends help for all commands or for a specific one",
                category="About",
            )
        all_commands = set()
        for handler in self._handlers:
            if isinstance(handler.commands, re.Pattern):
                command_re = re.compile(
                    f"^[{re.escape(handler.prefix)}]{handler.commands.pattern}",
                    flags=handler.commands.flags,
                )
                f = flt.regex(command_re)
            elif isinstance(handler.commands, list):
                for c in (commands := handler.commands):
                    if c in all_commands:
                        raise ValueError(f"Duplicate command detected: {c}")
                all_commands.update(commands)
                f = flt.command(handler.commands, prefixes=handler.prefix)
            else:
                raise AssertionError(f"Unexpected command type: {type(handler.commands)}")
            f &= flt.me & ~flt.scheduled
            callback = async_partial(handler.__call__, middleware=self._middleware)
            client.add_handler(MessageHandler(callback, f))
            if handler.handle_edits:
                client.add_handler(EditedMessageHandler(callback, f))

    async def _help_handler(self, command: CommandObject, tr: Translation) -> str:
        _ = tr.gettext
        if args := command.args:
            for h in self._handlers:
                match h.commands:
                    case re.Pattern() as pattern:
                        matches = pattern.fullmatch(args) is not None
                    case list(cmds):
                        matches = args in cmds
                    case _:
                        raise AssertionError(f"Unexpected command type: {type(h.commands)}")
                if matches:
                    usage = h.format_usage(full=True)
                    return _("<b>Help for {args}:</b>\n{usage}").format(
                        args=html.escape(args),
                        usage=html.escape(usage),
                    )
            else:
                return f"<b>No help found for {args}</b>"
        text = _("<b>List of userbot commands available:</b>\n\n")
        prev_cat = ""
        for handler in sorted(self._handlers, key=_CommandHandler.sort_key):
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
