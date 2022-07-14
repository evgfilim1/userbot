__all__ = [
    "commands",
]

import re

from pyrogram import Client
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message

from ..modules import CommandsModule
from ..utils import edit_or_reply, get_text

_kb_en = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
_kb_ru = 'ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГШЩЗХЪ/ФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,'
_ru2en_tr = str.maketrans(_kb_ru, _kb_en)
_en2ru_tr = str.maketrans(_kb_en, _kb_ru)
_enru2ruen_tr = str.maketrans(_kb_ru + _kb_en, _kb_en + _kb_ru)

commands = CommandsModule()


@commands.add("tr", usage="<reply> ['en'|'ru']")
async def tr(_: Client, message: Message, args: str) -> None:
    """Swaps keyboard layout from en to ru or vice versa"""
    # TODO (2021-12-01): detect ambiguous replacements via previous char
    # TODO (2022-02-17): work with entities
    text = get_text(message.reply_to_message)
    if args == "en":
        tr_abc = _ru2en_tr
    elif args == "ru":
        tr_abc = _en2ru_tr
    else:
        tr_abc = _enru2ruen_tr
    translated = text.translate(tr_abc)
    answer, delete = edit_or_reply(message)
    try:
        await answer(translated)
    except MessageNotModified:
        pass
    if delete:
        await message.delete()


@commands.add("s", usage="<reply> <find-re>/<replace-re>/[flags]")
async def sed(_: Client, message: Message, args: str) -> None:
    """sed-like replacement"""
    # TODO (2022-02-17): work with entities
    text = get_text(message.reply_to_message)
    find_re, replace_re, flags_str = re.split(r"(?<!\\)/", args)
    find_re = find_re.replace("\\/", "/")
    replace_re = replace_re.replace("\\/", "/")
    flags = 0
    for flag in flags_str:
        flags |= getattr(re, flag.upper())
    text = re.sub(find_re, replace_re, text, flags=flags)
    answer, delete = edit_or_reply(message)
    try:
        await answer(text)
    except MessageNotModified:
        pass
    if delete:
        await message.delete()


@commands.add("caps", usage="<reply>")
async def caps(_: Client, message: Message, __: str) -> None:
    """Toggles capslock on the message"""
    text = get_text(message.reply_to_message)
    answer, delete = edit_or_reply(message)
    try:
        await answer(text.swapcase())
    except MessageNotModified:
        pass
    if delete:
        await message.delete()
