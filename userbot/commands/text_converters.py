__all__ = [
    "commands",
]

import logging
import re

from pyrogram.enums import MessageEntityType, ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message, MessageEntity

from ..constants import Icons
from ..meta.modules import CommandObject, CommandsModule
from ..utils import edit_or_reply, get_text
from ..utils.translations import Translation

_log = logging.getLogger(__name__)
_kb_en = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
_kb_ru = 'ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГШЩЗХЪ/ФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,'
_ru2en_tr = str.maketrans(_kb_ru, _kb_en)
_en2ru_tr = str.maketrans(_kb_en, _kb_ru)
_enru2ruen_tr = str.maketrans(_kb_ru + _kb_en, _kb_en + _kb_ru)

commands = CommandsModule("Text converters")


def _len(text: str) -> int:
    """Returns the length of the text in utf-16 code units."""

    # `timeit` says it's the fastest way of other possible ones.
    return len(text.encode("utf-16-le")) // 2


class _ReplaceHelper:
    def __init__(self, replace_template: str):
        self.entities: list[MessageEntity] = []
        self._template = replace_template
        self._diff = 0

    def __call__(self, match: re.Match[str]) -> str:
        res = match.expand(self._template)
        res_len = _len(res)
        self.entities.append(
            MessageEntity(
                type=MessageEntityType.UNDERLINE,
                offset=_len(match.string[: match.start()]) + self._diff,
                length=res_len,
            )
        )
        self._diff += res_len - (match.end() - match.start())
        return res


@commands.add("tr", usage="<reply> ['en'|'ru']")
async def sw(message: Message, command: CommandObject, tr: Translation) -> None:
    """Swaps keyboard layout from en to ru or vice versa

    If no argument is provided, the layout will be switched between en and ru."""
    # TODO (2021-12-01): detect ambiguous replacements via previous char
    # TODO (2022-02-17): work with entities
    text = get_text(message.reply_to_message)
    target_layout = command.args
    match target_layout:
        case "en":
            tr_abc = _ru2en_tr
        case "ru":
            tr_abc = _en2ru_tr
        case "":
            tr_abc = _enru2ruen_tr
        case _:
            raise ValueError(f"Unknown {target_layout=}")
    translated = text.translate(tr_abc)
    answer, delete = edit_or_reply(message, tr)
    try:
        await answer(translated)
    except MessageNotModified:
        pass
    if delete:
        await message.delete()


@commands.add("s", usage="<reply> <find-re>/<replace-re>/[flags]")
async def sed(
    message: Message,
    command: CommandObject,
    icons: type[Icons],
    tr: Translation,
) -> str | None:
    """sed-like replacement"""
    # TODO (2022-02-17): work with entities
    _ = tr.gettext
    text = get_text(message.reply_to_message)
    args = command.args
    try:
        find_re, replace_re, flags_str = re.split(r"(?<!\\)/", args)
    except ValueError as e:
        if "not enough values to unpack" in str(e) and (args[-1] != "/" or args[-2:] == "\\/"):
            return _(
                "{icon} Not enough values to unpack. Seems like you forgot to add trailing slash.\n"
                "\nPossible fix: <code>{message_text}/</code>"
            ).format(icon=icons.WARNING, message_text=message.text)
        raise
    find_re = find_re.replace("\\/", "/")
    replace_re = replace_re.replace("\\/", "/")
    flags = 0
    for flag in flags_str:
        flags |= getattr(re, flag.upper())
    answer, delete = edit_or_reply(message, tr)
    rh = _ReplaceHelper(replace_re)
    text = re.sub(find_re, rh, text, flags=flags)
    if not delete:
        prefix = _("Maybe you mean:")
        for entity in rh.entities:
            entity.offset += len(prefix) + 2  # +2 for \n\n, see below
        await message.edit(
            f"{prefix}\n\n{text}",
            parse_mode=ParseMode.DISABLED,
            entities=[
                MessageEntity(
                    type=MessageEntityType.BOLD,
                    offset=0,
                    length=len(prefix),
                ),
                *rh.entities,
            ],
        )
        return
    try:
        await answer(text)
    except MessageNotModified:
        pass
    if delete:
        await message.delete()


@commands.add("caps", usage="<reply>")
async def caps(message: Message, tr: Translation) -> None:
    """Toggles capslock on the message"""
    text = get_text(message.reply_to_message)
    answer, delete = edit_or_reply(message, tr)
    try:
        await answer(text.swapcase())
    except MessageNotModified:
        pass
    if delete:
        await message.delete()
