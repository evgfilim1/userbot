from __future__ import annotations

import functools
import html
import logging
import re
from dataclasses import dataclass
from typing import Optional, Awaitable, Callable, TypeAlias

from pyrogram import Client, filters as flt
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from storage import Storage

_HandlerWithArgs: TypeAlias = Callable[[Client, Message, str], Awaitable[Optional[str]]]
_Handler: TypeAlias = Callable[[Client, Message], Awaitable[None]]
_TransformHandler: TypeAlias = Callable[[re.Match[str]], Awaitable[Optional[str]]]

_log = logging.getLogger(__name__)


@dataclass()
class _CommandHandler:
    command: str
    prefix: str
    handler: _HandlerWithArgs
    usage: str | None
    doc: str | None
    can_be_long: bool = False

    async def __call__(self, client: Client, message: Message):
        args = message.text.lstrip(self.prefix)
        if not isinstance(self.command, str):
            for cmd in self.command:
                args = args.removeprefix(cmd)
        else:
            args = args.removeprefix(self.command)
        args = args.lstrip()
        if self.can_be_long:
            await message.edit(f"<b>⌚ Executing</b> <code>{html.escape(message.text)}</code>")
        try:
            result = await self.handler(client, message, args)
        except Exception as e:
            await message.edit(
                f"<b>[‼] An error occurred during executing command.</b>\n\n"
                f"<b>Command:</b> <code>{html.escape(message.text)}</code>\n"
                f"<b>Error:</b> <code>{html.escape(f'{e.__class__.__name__}: {e}')}</code>",
                parse_mode="HTML",
            )
            _log.exception(
                "An error occurred during executing %r",
                message.text,
                extra={"command": self.command},
            )
        else:
            if result is not None:
                await message.edit(result, parse_mode="HTML")


@dataclass()
class _HookHandler:
    name: str
    filters: flt.Filter
    handler: _Handler

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
    handler: _TransformHandler

    async def __call__(self, client: Client, message: Message):
        text = message.text.html
        while match := self.regex.search(text):
            if (result := await self.handler(match)) is not None:
                text = f"{text[:match.start()]}{result}{text[match.end():]}"
        await message.edit(text, parse_mode="HTML")


def _generate_auto_help_handler(text: str) -> _HandlerWithArgs:
    async def _auto_help_handler(_: Client, __: Message, ___: str) -> str:
        return text

    return _auto_help_handler


class CommandsModule:
    def __init__(self):
        self._handlers: list[_CommandHandler] = []

    def add(
        self,
        command: str | list[str],
        prefix: str = ".",
        *,
        usage: str | None = None,
        doc: str | None = None,
        can_be_long: bool = False,
    ) -> Callable[[_HandlerWithArgs], _HandlerWithArgs]:
        def _decorator(f: _HandlerWithArgs) -> _HandlerWithArgs:
            self.add_handler(
                handler=f,
                command=command,
                prefix=prefix,
                usage=usage,
                doc=doc,
                can_be_long=can_be_long,
            )
            return f

        return _decorator

    def add_handler(
        self,
        handler: _HandlerWithArgs,
        command: str | list[str],
        prefix: str = ".",
        *,
        usage: str | None = None,
        doc: str | None = None,
        can_be_long: bool = False,
    ) -> None:
        self._handlers.append(
            _CommandHandler(
                command=command,
                prefix=prefix,
                handler=handler,
                usage=usage,
                doc=doc or getattr(handler, "__doc__", None),
                can_be_long=can_be_long,
            )
        )

    def add_submodule(self, module: CommandsModule) -> None:
        self._handlers.extend(module._handlers)

    def register(self, client: Client, *, with_help: bool = False) -> None:
        if with_help:
            text = "<b>List of commands available:</b>\n\n"
            for handler in self._handlers:
                if handler.usage is None:
                    continue
                if isinstance(handler.command, str):
                    commands = handler.command
                else:
                    commands = "|".join(handler.command)
                usage = f" {html.escape(handler.usage)}".rstrip()
                description = f" — {html.escape(handler.doc)}" if handler.doc else ""
                text += f"{commands}{usage}{description}\n"
            text += f"help — Sends this message\n"
            self._handlers.append(
                _CommandHandler(
                    command="help",
                    prefix=".",
                    handler=_generate_auto_help_handler(text),
                    usage="",
                    doc="Sends this message",
                )
            )
        for handler in self._handlers:
            client.add_handler(
                MessageHandler(
                    handler.__call__, flt.me & flt.command(handler.command, handler.prefix)
                )
            )


class HooksModule:
    def __init__(self):
        self._handlers: list[_HookHandler] = []

    def add(self, name: str, filters: flt.Filter) -> Callable[[_Handler], _Handler]:
        def _decorator(f: _Handler) -> _Handler:
            self.add_handler(
                handler=f,
                name=name,
                filters=filters,
            )
            return f

        return _decorator

    def add_handler(
        self,
        handler: _Handler,
        name: str,
        filters: flt.Filter,
    ) -> None:
        self._handlers.append(_HookHandler(name=name, filters=filters, handler=handler))

    def add_submodule(self, module: HooksModule) -> None:
        self._handlers.extend(module._handlers)

    @staticmethod
    def _wrapper(
        f: Callable[[Client, Message, Storage], Awaitable[None]],
        storage: Storage,
    ) -> _Handler:
        @functools.wraps(f)
        async def wrapper(client: Client, message: Message) -> None:
            return await f(client, message, storage)

        return wrapper

    def register(self, client: Client, storage: Storage) -> None:
        for handler in self._handlers:
            client.add_handler(
                MessageHandler(
                    self._wrapper(handler.add_handler, storage=storage),
                    (
                        flt.me
                        & flt.command([f"{handler.name}here", f"{handler.name}_here"], prefixes=".")
                    ),
                )
            )
            client.add_handler(
                MessageHandler(
                    self._wrapper(handler.del_handler, storage=storage),
                    (
                        flt.me
                        & flt.command(
                            [f"no{handler.name}here", f"no_{handler.name}_here"], prefixes="."
                        )
                    ),
                )
            )
            client.add_handler(
                MessageHandler(
                    self._wrapper(handler, storage=storage),
                    flt.incoming & handler.filters,
                )
            )


class ShortcutTransformersModule:
    def __init__(self):
        self._handlers: list[_ShortcutHandler] = []

    def add(
        self,
        pattern: str | re.Pattern[str],
    ) -> Callable[[_TransformHandler], _TransformHandler]:
        def _decorator(f: _TransformHandler) -> _TransformHandler:
            self.add_handler(
                handler=f,
                pattern=pattern,
            )
            return f

        return _decorator

    def add_handler(self, handler: _TransformHandler, pattern: str | re.Pattern[str]) -> None:
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self._handlers.append(_ShortcutHandler(regex=pattern, handler=handler))

    def add_submodule(self, module: ShortcutTransformersModule) -> None:
        self._handlers.extend(module._handlers)

    def register(self, client: Client) -> None:
        for handler in self._handlers:
            client.add_handler(
                MessageHandler(
                    handler.__call__,
                    flt.outgoing & flt.regex(handler.regex),
                )
            )
