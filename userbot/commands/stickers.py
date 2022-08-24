__all__ = [
    "commands",
]

import random

from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.types import Message

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
    await client.invoke(
        functions.messages.SendMedia(
            peer=await client.resolve_peer(message.chat.id),
            media=types.InputMediaDocument(
                id=types.InputDocument(
                    id=sticker_raw.id,
                    access_hash=sticker_raw.access_hash,
                    file_reference=sticker_raw.file_reference,
                ),
            ),
            message="",
            random_id=sticker_raw.id,
            reply_to_msg_id=message.reply_to_message_id,
        )
    )
    await message.delete()
