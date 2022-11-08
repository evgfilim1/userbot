__all__ = [
    "fetch_stickers",
    "StickerInfo",
]

import logging
from base64 import b64encode
from collections import defaultdict
from typing import TypedDict

from pyrogram import Client
from pyrogram.raw import functions, types

_log = logging.getLogger(__name__)


# It's a dict because I want to serialize it easily to JSON
class StickerInfo(TypedDict):
    id: int
    access_hash: int
    file_reference_b64: str


async def fetch_stickers(client: Client) -> dict[str, list[StickerInfo]]:
    _log.debug("Fetching stickers...")
    all_stickers: types.messages.AllStickers = await client.invoke(
        functions.messages.GetAllStickers(hash=0)
    )
    res: defaultdict[str, list[StickerInfo]] = defaultdict(list)
    for ss in all_stickers.sets:
        stickers_by_id: dict[int, StickerInfo] = {}
        full_set: types.messages.StickerSet = await client.invoke(
            functions.messages.GetStickerSet(
                stickerset=types.InputStickerSetID(id=ss.id, access_hash=ss.access_hash),
                hash=0,
            )
        )
        for doc in full_set.documents:
            stickers_by_id[doc.id] = StickerInfo(
                id=doc.id,
                access_hash=doc.access_hash,
                file_reference_b64=b64encode(doc.file_reference).decode("ascii"),
            )
        for doc in full_set.packs:
            res[doc.emoticon].extend(stickers_by_id[doc_id] for doc_id in doc.documents)
    return res
