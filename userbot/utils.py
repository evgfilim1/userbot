from __future__ import annotations

import functools
import html
import re
from datetime import timedelta
from typing import Any, ClassVar, Protocol, TypeVar

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Chat, Message, User

_T = TypeVar("_T")


class MessageMethod(Protocol):
    async def __call__(self, text: str, *, parse_mode: ParseMode | None) -> Message:
        pass


class AnswerMethod(Protocol):
    async def __call__(self, text: str, *, prefix_override: str | None = None) -> Message:
        pass


def sticker(sticker_id: str, debug: bool = False) -> filters.Filter:
    @filters.create
    def sticker_filter(_, __, c):
        if debug and c.sticker:
            print(c.sticker.file_id, c.sticker.file_unique_id)
        return c.sticker and c.sticker.file_unique_id == sticker_id

    return sticker_filter


def get_text(message: Message, *, as_html: bool = False) -> str | None:
    text = message.text or message.caption
    if as_html:
        text = text.html
    return text


def get_sender(message: Message) -> User | Chat:
    return message.from_user or message.sender_chat


def send_helper(fn: MessageMethod, prefix: str = "") -> AnswerMethod:
    @functools.wraps(fn)
    async def wrapper(text: str, prefix_override: str | None = None) -> Message:
        return await fn(
            f"{prefix_override or prefix}{html.escape(text)}",
            parse_mode=ParseMode.HTML,
        )

    return wrapper


def edit_or_reply(message: Message) -> tuple[AnswerMethod, bool]:
    reply_sender = get_sender(message.reply_to_message)
    sender = get_sender(message)
    if reply_sender.id == sender.id:  # it's me!
        if message.reply_to_message.caption is not None:
            return send_helper(message.reply_to_message.edit_caption), True
        return send_helper(message.reply_to_message.edit), True
    return send_helper(message.edit, f"<b>Maybe you mean:</b>\n\n"), False


def parse_delta(delta: str) -> timedelta | None:
    total_sec = 0
    for match in re.finditer(r"(\d+)([smhdwy])", delta, re.I):
        time_sec = int(match[1])
        match match[2]:
            case "m" | "M":
                time_sec *= 60
            case "h" | "H":
                time_sec *= 60 * 60
            case "d" | "D":
                time_sec *= 60 * 60 * 24
            case "w" | "W":
                time_sec *= 60 * 60 * 24 * 7
            case "y" | "Y":
                time_sec *= 60 * 60 * 24 * 365
        total_sec += time_sec
    if total_sec > 0:
        return timedelta(seconds=total_sec)
    return None


class Unset:
    """A singleton to represent an unset value"""

    _instance: ClassVar[Unset | None] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Unset:
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __repr__(self) -> str:
        return "<unset>"

    def __str__(self) -> str:
        return repr(self)
