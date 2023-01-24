__all__ = [
    "commands",
]

import logging
import re

from pyrogram.enums import MessageEntityType
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message, MessageEntity

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..utils import (
    Translation,
    _,
    edit_replied_or_reply,
    get_message_entities,
    get_message_text,
    is_my_message,
)

MAYBE_YOU_MEAN_PREFIX = _("Maybe you mean:")

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


@commands.add("tr", usage="['en'|'ru']", reply_required=True)
async def sw(message: Message, command: CommandObject, reply: Message, tr: Translation) -> None:
    """Swaps keyboard layout from en to ru or vice versa.

    If no argument is provided, the layout will be switched between en and ru.
    """
    # TODO (2021-12-01): detect ambiguous replacements via previous char
    _ = tr.gettext
    target_layout = command.args[0]
    match target_layout:
        case "en":
            tr_abc = _ru2en_tr
        case "ru":
            tr_abc = _en2ru_tr
        case None:
            tr_abc = _enru2ruen_tr
        case _:
            raise ValueError(f"Unknown {target_layout=}")
    try:
        await edit_replied_or_reply(
            message,
            get_message_text(reply).translate(tr_abc),
            maybe_you_mean_prefix=_(MAYBE_YOU_MEAN_PREFIX),
            entities=get_message_entities(reply),
        )
    except MessageNotModified:
        pass


@commands.add("s", usage="<args...>", reply_required=True)
async def sed(
    message: Message,
    command: CommandObject,
    reply: Message,
    icons: type[Icons],
    tr: Translation,
) -> str | None:
    """sed-like replacement.

    `args` is a string of a pattern to find, replacement string and optional regex flags separated
    by '/'. If no flags are specified, trailing slash is mandatory.
    """
    # TODO (2022-02-17): work with entities
    _ = tr.gettext
    text = get_message_text(reply)
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
    rh = _ReplaceHelper(replace_re)
    text = re.sub(find_re, rh, text, flags=flags)
    try:
        await edit_replied_or_reply(
            message,
            text,
            maybe_you_mean_prefix=_(MAYBE_YOU_MEAN_PREFIX),
            entities=rh.entities if not is_my_message(reply) else None,
        )
    except MessageNotModified:
        pass


@commands.add("caps", reply_required=True)
async def caps(message: Message, reply: Message, tr: Translation) -> None:
    """Toggles capslock on the message."""
    _ = tr.gettext
    try:
        await edit_replied_or_reply(
            message,
            get_message_text(reply).swapcase(),
            maybe_you_mean_prefix=_(MAYBE_YOU_MEAN_PREFIX),
            entities=get_message_entities(reply),
        )
    except MessageNotModified:
        pass
