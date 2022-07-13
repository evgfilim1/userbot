import random
import re

from pyrogram import Client, filters
from pyrogram.types import Message

from .constants import (
    BRA_MEME_PICTURE,
    MIBIB_FLT,
    MIBIB_STICKER,
    TAP_FLT,
    TAP_STICKER,
    UWU_MEME_PICTURE,
)
from .modules import HooksModule
from .storage import Storage
from .utils import sticker

hooks = HooksModule()


@hooks.add("emojis", filters.regex(r"\b((?:дак\b|кря(?:к.?|\b))|блин)", flags=re.I))
async def on_duck(_: Client, message: Message) -> None:
    t = ""
    for m in message.matches:
        match m[1].lower():
            case "дак" | "кря":
                t += "🦆"
            case x if x.startswith("кряк"):
                t += "🦆"
            case "блин":
                t += "🥞"
    await message.reply(t)


@hooks.add("tap", (filters.regex(r"\b(?:тык|nsr)\b", flags=re.I) | sticker(TAP_FLT)))
async def on_tap(_: Client, message: Message) -> None:
    await message.reply_sticker(TAP_STICKER)


@hooks.add("mibib", filters.sticker & sticker(MIBIB_FLT))
async def mibib(client: Client, message: Message) -> None:
    # TODO (2022-02-13): Don't send it again for N minutes
    if random.random() <= (1 / 5):
        await client.send_sticker(message.chat.id, MIBIB_STICKER)


@hooks.add("bra", filters.regex(r"\b(?:бра|bra)\b", flags=re.I))
async def on_bra(_: Client, message: Message) -> None:
    await message.reply_photo(BRA_MEME_PICTURE)


@hooks.add("uwu", filters.regex(r"\b(?:uwu|owo|уву|ово)\b", flags=re.I))
async def on_uwu(_: Client, message: Message) -> None:
    await message.reply_photo(UWU_MEME_PICTURE)


async def check_hooks(_: Client, message: Message, __: str, *, storage: Storage) -> str:
    enabled = await storage.list_enabled_hooks(message.chat.id)
    return "Hooks in this chat: <code>" + "</code>, <code>".join(enabled) + "</code>"
