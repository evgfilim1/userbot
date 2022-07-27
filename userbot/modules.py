import functools
import html
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from traceback import extract_tb
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Protocol

from httpx import AsyncClient, HTTPError
from pyrogram import Client
from pyrogram import filters as flt
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified, MessageTooLong, SlowmodeWait
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.types import Message

from .storage import Storage

if TYPE_CHECKING:
    from traceback import FrameSummary


SNIP = "<...snip...>"
nekobin = AsyncClient(base_url="https://nekobin.com/")


class CommandHandler(Protocol):
    async def __call__(
        self,
        client: Client,
        message: Message,
        args: str,
        **kwargs: Any,
    ) -> str | None:
        pass


class Handler(Protocol):
    async def __call__(
        self,
        client: Client,
        message: Message,
    ) -> None:
        pass


class TransformHandler(Protocol):
    async def __call__(
        self,
        match: re.Match[str],
    ) -> str | None:
        pass


_log = logging.getLogger(__name__)


@dataclass()
class _CommandHandler:
    command: str | list[str]
    prefix: str
    handler: CommandHandler
    handle_edits: bool
    usage: str | None
    doc: str | None
    waiting_message: str | None
    kwargs: dict[str, Any]

    def _report_exception(self, message: Message, e: Exception) -> str:
        """Logs an exception to the logger and returns a message to be sent to the user."""
        _log.exception(
            "An error occurred during executing %r",
            message.text,
            extra={"command": self.command},
        )
        last_own_frame = None
        last_frame = None
        own_package_name = Path(__file__).parent
        for i, frame in enumerate(extract_tb(e.__traceback__)):
            frame: FrameSummary
            if frame.filename is not None and Path(frame.filename).parent == own_package_name:
                last_own_frame = frame
            last_frame = frame
        tb = ""
        if last_own_frame is not None and last_frame is not None:
            tb += '  {snip}\n  File "{}", line {}, in {}\n    {}\n'.format(
                last_own_frame.filename,
                last_own_frame.lineno,
                last_own_frame.name,
                last_own_frame.line.strip(),
                snip=SNIP,
            )
            if last_frame is not last_own_frame:
                tb += '  {snip}\n  File "{}", line {}, in {}\n    {}\n'.format(
                    last_frame.filename,
                    last_frame.lineno,
                    last_frame.name,
                    last_frame.line.strip(),
                    snip=SNIP,
                )
        tb += type(e).__qualname__
        exc_value = str(e)
        if exc_value:
            tb += f": {exc_value}"
        tb = f"<pre><code class='language-python'>{html.escape(tb)}</code></pre>"
        return (
            f"<b>[‼] An error occurred during executing command.</b>\n\n"
            f"<b>Command:</b> <code>{html.escape(message.text)}</code>\n"
            f"<b>Traceback:</b>\n{tb}\n\n"
            f"<i>More info can be found in logs.</i>"
        )

    async def __call__(self, client: Client, message: Message):
        args = message.text.lstrip(self.prefix)
        if not isinstance(self.command, str):
            for cmd in self.command:
                args = args.removeprefix(cmd)
        else:
            args = args.removeprefix(self.command)
        args = args.lstrip()
        if self.waiting_message is not None:
            if self.waiting_message == "":
                await message.edit(f"<b>⌚ Executing</b> <code>{html.escape(message.text)}</code>")
            else:
                await message.edit(f"⌚ {self.waiting_message}")
        try:
            result = await self.handler(client, message, args, **self.kwargs)
        except Exception as e:
            text = self._report_exception(message, e)
            await message.edit(text, parse_mode=ParseMode.HTML)
        else:
            if result is None:
                return
            try:
                await message.edit(result, parse_mode=ParseMode.HTML)
            except MessageTooLong as e:
                text = (
                    f"<b>[✅] Successfully executed.</b>\n\n"
                    f"<b>Command:</b> <code>{html.escape(message.text)}</code>\n"
                    f"<b>Result:</b>"
                )
                try:
                    res = await nekobin.post("/api/documents", json={"content": result})
                    res.raise_for_status()
                except HTTPError:
                    # Nekobin is down, try to send result as a file
                    try:
                        await message.reply_document(
                            BytesIO(result.encode("utf-8")),
                            file_name="result.html",  # default parse mode for the bot is html
                        )
                    except SlowmodeWait:
                        # Cannot send file, report `MessageTooLong` exception.
                        # It's ok to log entire exception chain here
                        text = self._report_exception(message, e)
                        await message.edit(text, parse_mode=ParseMode.HTML)
                    else:
                        await message.edit(f"{text} <i>See reply</i>", parse_mode=ParseMode.HTML)
                else:
                    await message.edit(
                        f"{text} {nekobin.base_url.join(res.json()['result']['key'])}.html",
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                    )
            except MessageNotModified:
                await message.edit(
                    f"{result}\n\n⚠ <i><b>MessageNotModified</b> was raised, check that there is"
                    f" only one userbot instance is running</i>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                text = self._report_exception(message, e)
                await message.edit(text, parse_mode=ParseMode.HTML)


@dataclass()
class _HookHandler:
    name: str
    filters: flt.Filter
    handler: Handler
    handle_edits: bool

    async def add_handler(self, _: Client, message: Message, storage: Storage):
        await storage.enable_hook(self.name, message.chat.id)
        await message.delete()

    async def del_handler(self, _: Client, message: Message, storage: Storage):
        await storage.disable_hook(self.name, message.chat.id)
        await message.delete()

    async def __call__(self, client: Client, message: Message, storage: Storage):
        if await storage.is_hook_enabled(self.name, message.chat.id):
            await self.handler(client, message)


@dataclass()
class _ShortcutHandler:
    regex: re.Pattern[str]
    handler: TransformHandler
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


def _format_handler_usage(handler: _CommandHandler) -> str | None:
    if handler.usage is None:
        return None
    if isinstance(handler.command, str):
        commands = handler.command
    else:
        commands = "|".join(handler.command)
    usage = f" {handler.usage}".rstrip()
    description = f" — {handler.doc}" if handler.doc else ""
    return f"{commands}{usage}{description}"


def _command_handler_sort_key(handler: _CommandHandler) -> str:
    if isinstance(handler.command, str):
        return handler.command
    return handler.command[0]


class CommandsModule:
    def __init__(self):
        self._handlers: list[_CommandHandler] = []

    def add(
        self,
        command: str | list[str],
        prefix: str = ".",
        *,
        handle_edits: bool = True,
        usage: str | None = None,
        doc: str | None = None,
        waiting_message: str | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Callable[[CommandHandler], CommandHandler]:
        def _decorator(f: CommandHandler) -> CommandHandler:
            self.add_handler(
                handler=f,
                command=command,
                prefix=prefix,
                handle_edits=handle_edits,
                usage=usage,
                doc=doc,
                waiting_message=waiting_message,
                kwargs=kwargs,
            )
            return f

        return _decorator

    def add_handler(
        self,
        handler: CommandHandler,
        command: str | list[str],
        prefix: str = ".",
        *,
        handle_edits: bool = True,
        usage: str | None = None,
        doc: str | None = None,
        waiting_message: str | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        self._handlers.append(
            _CommandHandler(
                command=command,
                prefix=prefix,
                handler=handler,
                handle_edits=handle_edits,
                usage=usage,
                doc=doc or getattr(handler, "__doc__", None),
                waiting_message=waiting_message,
                kwargs=kwargs or {},
            )
        )

    def add_submodule(self, module: "CommandsModule") -> None:
        self._handlers.extend(module._handlers)

    def register(self, client: Client, *, with_help: bool = False) -> None:
        if with_help:
            self._handlers.append(
                _CommandHandler(
                    command="help",
                    prefix=".",
                    handler=self._auto_help_handler,
                    handle_edits=True,
                    usage="[command]",
                    doc="Sends help for all commands (this message) or for a specific one",
                    waiting_message=None,
                    kwargs={},
                )
            )
        for handler in self._handlers:
            f = flt.me & flt.command(handler.command, handler.prefix)
            client.add_handler(MessageHandler(handler.__call__, f))
            if handler.handle_edits:
                client.add_handler(EditedMessageHandler(handler.__call__, f))

    async def _auto_help_handler(self, _: Client, __: Message, args: str) -> str:
        logging.info(f"Sending help for {args}")
        if args:
            for h in self._handlers:
                if isinstance(h.command, str) and h.command == args or args in h.command:
                    return f"<b>Help for {args}:</b>\n{html.escape(_format_handler_usage(h))}"
            else:
                return f"<b>No help found for {args}</b>"
        text = "<b>List of commands available:</b>\n\n"
        for handler in sorted(self._handlers, key=_command_handler_sort_key):
            if (usage := _format_handler_usage(handler)) is None:
                continue
            text += f"{html.escape(usage)}\n"
        return text


class HooksModule:
    def __init__(self):
        self._handlers: list[_HookHandler] = []

    def add(
        self,
        name: str,
        filters: flt.Filter,
        *,
        handle_edits: bool = False,
    ) -> Callable[[Handler], Handler]:
        def _decorator(f: Handler) -> Handler:
            self.add_handler(
                handler=f,
                name=name,
                filters=filters,
                handle_edits=handle_edits,
            )
            return f

        return _decorator

    def add_handler(
        self,
        handler: Handler,
        name: str,
        filters: flt.Filter,
        *,
        handle_edits: bool = False,
    ) -> None:
        self._handlers.append(
            _HookHandler(
                name=name,
                filters=filters,
                handler=handler,
                handle_edits=handle_edits,
            )
        )

    def add_submodule(self, module: "HooksModule") -> None:
        self._handlers.extend(module._handlers)

    @staticmethod
    def _wrapper(
        f: Callable[[Client, Message, Storage], Awaitable[None]],
        storage: Storage,
    ) -> Handler:
        @functools.wraps(f)
        async def wrapper(client: Client, message: Message) -> None:
            return await f(client, message, storage)

        return wrapper

    def register(self, client: Client, storage: Storage) -> None:
        for handler in self._handlers:
            f_reg = flt.me & flt.command(
                [f"{handler.name}here", f"{handler.name}_here"], prefixes="."
            )
            f_unreg = flt.me & flt.command(
                [f"no{handler.name}here", f"no_{handler.name}_here"], prefixes="."
            )
            f = flt.incoming & handler.filters
            client.add_handler(
                MessageHandler(
                    self._wrapper(handler.add_handler, storage=storage),
                    f_reg,
                )
            )
            client.add_handler(
                MessageHandler(
                    self._wrapper(handler.del_handler, storage=storage),
                    f_unreg,
                )
            )
            client.add_handler(MessageHandler(self._wrapper(handler, storage=storage), f))
            if handler.handle_edits:
                client.add_handler(
                    EditedMessageHandler(
                        self._wrapper(handler.add_handler, storage=storage),
                        f_reg,
                    )
                )
                client.add_handler(
                    EditedMessageHandler(
                        self._wrapper(handler.del_handler, storage=storage),
                        f_unreg,
                    )
                )
                client.add_handler(EditedMessageHandler(self._wrapper(handler, storage=storage), f))


class ShortcutTransformersModule:
    def __init__(self):
        self._handlers: list[_ShortcutHandler] = []

    def add(
        self,
        pattern: str | re.Pattern[str],
        *,
        handle_edits: bool = True,
    ) -> Callable[[TransformHandler], TransformHandler]:
        def _decorator(f: TransformHandler) -> TransformHandler:
            self.add_handler(
                handler=f,
                pattern=pattern,
                handle_edits=handle_edits,
            )
            return f

        return _decorator

    def add_handler(
        self,
        handler: TransformHandler,
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
            f = flt.outgoing & flt.regex(handler.regex)
            client.add_handler(MessageHandler(handler.__call__, f))
            if handler.handle_edits:
                client.add_handler(EditedMessageHandler(handler.__call__, f))
