import random
import re

from pyrogram import Client, filters
from pyrogram.types import Message

from .constants import MIBIB_FLT, MIBIB_STICKER, TAP_FLT, TAP_STICKER
from .modules import HooksModule
from .storage import Storage
from .utils import sticker

hooks = HooksModule()


@hooks.add("duck", filters.regex(r"\b(?:дак|кря)\b", flags=re.I))
async def on_duck(_: Client, message: Message) -> None:
    await message.reply("🦆" * len(message.matches))


@hooks.add("tap", (filters.regex(r"\b(?:тык|nsr)\b", flags=re.I) | sticker(TAP_FLT)))
async def on_tap(_: Client, message: Message) -> None:
    await message.reply_sticker(TAP_STICKER)


@hooks.add("mibib", filters.sticker & sticker(MIBIB_FLT))
async def mibib(client: Client, message: Message) -> None:
    # TODO (2022-02-13): Don't send it again for N minutes
    if random.random() <= (1 / 5):
        await client.send_sticker(message.chat.id, MIBIB_STICKER)


async def check_hooks(_: Client, message: Message, __: str, *, storage: Storage) -> str:
    enabled = await storage.list_enabled_hooks(message.chat.id)
    return "Hooks in this chat: <code>" + "</code>, <code>".join(enabled) + "</code>"
