__all__ = [
    "commands",
]

import random

from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.types import Message, Sticker

from ..constants import LONGCAT, PACK_ALIASES
from ..modules import CommandsModule

commands = CommandsModule("Stickers")


@commands.add("longcat", usage="")
async def longcat(client: Client, message: Message, _: str) -> None:
    """Sends random longcat"""
    key = "black" if random.random() >= 0.5 else "white"
    head, body, tail = (
        random.choice(LONGCAT[f"head_{key}"]),
        LONGCAT[f"body_{key}"],
        random.choice(LONGCAT[f"feet_{key}"]),
    )
    body_len = random.randint(0, 3)
    await message.delete()
    for s in (head, *((body,) * body_len), tail):
        await client.send_sticker(message.chat.id, s)


@commands.add("rnds", usage="<pack-link|pack-alias>")
async def random_sticker(client: Client, message: Message, args: str) -> None:
    """Sends random sticker from specified pack"""
    set_name = PACK_ALIASES.get(args, args)
    stickerset: types.messages.StickerSet = await client.invoke(
        functions.messages.GetStickerSet(
            stickerset=types.InputStickerSetShortName(
                short_name=set_name,
            ),
            hash=0,
        ),
    )
    sticker_raw: types.Document = random.choice(stickerset.documents)
    attributes = {type(i): i for i in sticker_raw.attributes}
    s = await Sticker._parse(  # huh...
        client,
        sticker_raw,
        attributes.get(types.DocumentAttributeImageSize, None),
        attributes[types.DocumentAttributeSticker],
        attributes[types.DocumentAttributeFilename],
    )
    kw = {}
    if message.reply_to_message is not None:
        kw["reply_to_message_id"] = message.reply_to_message.id
    await client.send_sticker(message.chat.id, s.file_id, **kw)
    await message.delete()
