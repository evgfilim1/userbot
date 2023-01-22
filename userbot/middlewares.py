from __future__ import annotations

__all__ = [
    "Arguments",
    "CommandObject",
    "icon_middleware",
    "KwargsMiddleware",
    "ParseCommandMiddleware",
    "translate_middleware",
    "update_command_stats_middleware",
]

import html
import re
from asyncio import create_task
from dataclasses import dataclass
from re import Match
from typing import Any, Iterable, Iterator, NamedTuple

from lark import Lark, UnexpectedInput
from pyrogram.types import Message

from .constants import DefaultIcons, Icons, PremiumIcons
from .meta.middleware_manager import Handler, Middleware
from .meta.modules.commands import CommandsHandler, CommandT
from .meta.usage_parser import Usage, VariableArgumentVariant
from .storage import Storage
from .utils import Translation

_ArgT = str | tuple[str, ...]
_ParsedArgsT = tuple[dict[str, _ArgT | None], tuple[_ArgT | None]]


def _parse_arguments(
    parser: Lark,
    args: str,
    usage_tree: Usage,
) -> _ParsedArgsT:
    args_tree = parser.parse(args)
    args_dict: dict[str, tuple[str] | str | None] = {}
    args_list: list[str] = []
    for arg in args_tree.children:
        key = arg.data
        if len(arg.children) == 0:
            value = None
        elif len(arg.children) == 1:
            value = str(arg.children[0])
        else:
            value = tuple(map(str, arg.children))
        parsed_key = re.fullmatch(r"(arg|literal)(\d+)_(\d+)(?:_(\d+))?", key)
        if parsed_key is not None:
            key = f"_{key}"
            type_, variant_n, arg_n, arg_variant_n = parsed_key.groups()
            arg_obj = usage_tree.variants[int(variant_n)].args[int(arg_n)]
            if type_ == "literal":
                value = arg_obj.variants[int(arg_variant_n)].value
            else:
                # fill aliases
                key_names = [arg_variant.name for arg_variant in arg_obj.variants]
                for key_name in key_names:
                    args_dict[key_name] = value
        args_list.append(value)
        args_dict[key] = value
    for arg in usage_tree.variants[int(args_tree.data.removeprefix("v"))].args:
        for arg_variant in arg.variants:
            # fill missing args
            if arg.repeat:
                value = ()
            else:
                value = None
            if isinstance(arg_variant, VariableArgumentVariant):
                if arg_variant.name in args_dict:
                    continue
                args_dict[arg_variant.name] = value
            args_list.append(value)
    return args_dict, tuple(args_list)


class Arguments:
    def __init__(self, raw_args: str, parsed_args: _ParsedArgsT) -> None:
        self._raw_args = raw_args
        self._args_dict, self._args_list = parsed_args

    def __getitem__(self, item: str | int | slice) -> _ArgT | None:
        if not isinstance(item, str):
            return self._args_list[item]
        return self._args_dict[item]

    def __iter__(self) -> Iterator[_ArgT]:
        return iter(self._args_list)

    @property
    def raw(self) -> str:
        return self._raw_args

    def __str__(self) -> str:
        return self.raw

    def __bool__(self) -> bool:
        return bool(self.raw)


@dataclass()
class CommandObject:
    """Represents a command object."""

    prefix: str
    command: str
    args: Arguments
    match: re.Match[str] | None

    @property
    def full_command(self) -> str:
        """Returns the full command without arguments."""
        return f"{self.prefix}{self.command}"

    def __str__(self) -> str:
        """Returns the full command with arguments."""
        return f"{self.prefix}{self.command} {self.args}"


class _CommandInfo(NamedTuple):
    prefix: str
    command: str
    args: str
    match: Match[str] | None


def _get_command_info(
    text: str,
    commands: Iterable[CommandT],
) -> _CommandInfo:
    command, _, args = text.partition(" ")
    prefix, command = command[0], command[1:]
    m = None
    for cmd in commands:
        if isinstance(cmd, re.Pattern):
            m = cmd.match(command)
            break
    return _CommandInfo(prefix, command, args, m)


class ParseCommandMiddleware(Middleware[str | None]):
    # noinspection PyProtocol
    # https://youtrack.jetbrains.com/issue/PY-49246
    def __init__(self, default_prefix: str) -> None:
        self._default_prefix = default_prefix

    async def __call__(
        self,
        handler: Handler[str | None],
        data: dict[str | Any],
    ) -> str | None:
        """Parses the command and its arguments."""
        message: Message = data["message"]
        handler_obj: CommandsHandler = data["handler_obj"]
        info = _get_command_info(message.text, handler_obj.commands)
        reply = message.reply_to_message
        if handler_obj.reply_required and reply is None:
            _ = data["tr"].gettext
            return self._get_error_message(_("Reply is required."), info, data)
        try:
            parsed_args = _parse_arguments(
                handler_obj.args_parser,
                info.args,
                handler_obj.usage_tree,
            )
        except UnexpectedInput:
            _ = data["tr"].gettext
            return self._get_error_message(_("Invalid syntax."), info, data)
        data["command"] = CommandObject(
            info.prefix,
            info.command,
            Arguments(info.args, parsed_args),
            info.match,
        )
        data["reply"] = message.reply_to_message
        return await handler(data)

    def _get_error_message(
        self,
        error: str,
        command_info: _CommandInfo,
        data: dict[str, Any],
    ) -> str:
        icons: type[Icons] = data["icons"]
        _ = data["tr"].gettext
        handler: CommandsHandler = data["handler_obj"]
        return _(
            "{icon} <b>{error}</b>\n<b>Usage:</b> {usage}\n\n"
            "To get more info about a command, send <code>{prefix}help {command}</code>.",
        ).format(
            icon=icons.STOP,
            error=html.escape(error),
            usage=html.escape(handler.format_usage()),
            prefix=self._default_prefix,
            command=html.escape(command_info.command),
        )


class KwargsMiddleware(Middleware[str | None]):
    """Updates middleware data with the given kwargs."""

    # noinspection PyProtocol
    # https://youtrack.jetbrains.com/issue/PY-49246
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


async def update_command_stats_middleware(
    handler: Handler[str | None],
    data: dict[str | Any],
) -> str | None:
    """Updates the command stats."""
    command: CommandObject = data["command"]
    storage: Storage = data["storage"]
    create_task(storage.command_used(command.command))  # I don't care about the result
    return await handler(data)
