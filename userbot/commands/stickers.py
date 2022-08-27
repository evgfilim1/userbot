__all__ = [
    "commands",
    "random_sticker",
]

import random
from base64 import b64decode

from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.types import Message

from ..constants import LONGCAT, PACK_ALIASES
from ..modules import CommandsModule
from ..storage import Storage
from ..utils import StickerInfo

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


async def random_sticker(client: Client, message: Message, args: str, *, storage: Storage) -> None:
    """Sends random sticker from specified pack or one matching specified emoji"""
    if not args.isalnum():
        # assume it's an emoji
        cache = await storage.get_sticker_cache()
        if len(cache) == 0:
            # Background job may be already running, wait for it to finish
            cache = await storage.wait_sticker_cache()
        # \uFE0F is a variation selector, it's not needed for matching
        sticker: StickerInfo = random.choice(cache[args.rstrip(" \n\uFE0F")])
        input_sticker = types.InputDocument(
            id=sticker["id"],
            access_hash=sticker["access_hash"],
            file_reference=b64decode(sticker["file_reference_b64"].encode("ascii")),
        )
    else:
        # assume it's a pack shortlink or alias
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
        input_sticker = types.InputDocument(
            id=sticker_raw.id,
            access_hash=sticker_raw.access_hash,
            file_reference=sticker_raw.file_reference,
        )
    await client.invoke(
        functions.messages.SendMedia(
            peer=await client.resolve_peer(message.chat.id),
            media=types.InputMediaDocument(id=input_sticker),
            message="",
            random_id=random.randint(0, 2**63),
            reply_to_msg_id=message.reply_to_message_id,
        )
    )
    await message.delete()
