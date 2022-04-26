from __future__ import annotations

import functools
import html
from dataclasses import dataclass
from io import BytesIO
from typing import Optional, Protocol, TypeVar

from d20 import SimpleStringifier
from PIL import Image
from pyrogram import filters
from pyrogram.types import Chat, Message, User

_T = TypeVar("_T")

_kb_en = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
_kb_ru = 'ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГШЩЗХЪ/ФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,'
ru2en_tr = str.maketrans(_kb_ru, _kb_en)
en2ru_tr = str.maketrans(_kb_en, _kb_ru)
enru2ruen_tr = str.maketrans(_kb_ru + _kb_en, _kb_en + _kb_ru)


class MessageMethod(Protocol):
    async def __call__(self, text: str, *, parse_mode: str | None) -> Message:
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


def create_filled_pic(col: str, size: tuple[int, int] = (100, 100)) -> BytesIO:
    tmp = BytesIO()
    tmp.name = "foo.png"
    im = Image.new("RGB", size, col)
    im.save(tmp, "png")
    im.close()
    tmp.seek(0)
    return tmp


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
        return await fn(f"{prefix_override or prefix}{html.escape(text)}", parse_mode="HTML")

    return wrapper


def edit_or_reply(message: Message) -> tuple[AnswerMethod, bool]:
    reply_sender = get_sender(message.reply_to_message)
    sender = get_sender(message)
    if reply_sender.id == sender.id:  # it's me!
        if message.reply_to_message.caption is not None:
            return send_helper(message.reply_to_message.edit_caption), True
        return send_helper(message.reply_to_message.edit), True
    return send_helper(message.edit, f"<b>Maybe you mean:</b>\n\n"), False


class HTMLDiceStringifier(SimpleStringifier):
    def __init__(self):
        super().__init__()
        self._in_dropped = False

    def stringify(self, the_roll):
        self._in_dropped = False
        return super().stringify(the_roll)

    def _stringify(self, node):
        if not node.kept and not self._in_dropped:
            self._in_dropped = True
            inside = super()._stringify(node)
            self._in_dropped = False
            return f"<s>{inside}</s>"
        return super()._stringify(node)

    def _str_expression(self, node):
        return f"{self._stringify(node.roll)} = <code>{int(node.total)}</code>"

    def _str_die(self, node):
        the_rolls = []
        for val in node.values:
            inside = self._stringify(val)
            if val.number == 1 or val.number == node.size:
                inside = f"<b>{inside}</b>"
            the_rolls.append(inside)
        return ", ".join(the_rolls)


@dataclass()
class GitHubMatch:
    username: str
    repo: Optional[str]
    issue: Optional[str]
    branch: Optional[str]
    path: Optional[str]
    line1: Optional[str]
    line2: Optional[str]
