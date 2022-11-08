__all__ = [
    "StickerFilter",
    "sticker",
]

import logging
import warnings

from pyrogram import Client, filters
from pyrogram.types import Message

_log = logging.getLogger(__name__)


class StickerFilter(filters.Filter):
    def __init__(self, sticker_id: str, debug: bool = False):
        self._sticker_id = sticker_id
        self._debug = debug

    async def __call__(self, _: Client, message: Message):
        if self._debug and message.sticker:
            _log.debug(
                "Got sticker file_id=%r, file_unique_id=%r",
                message.sticker.file_id,
                message.sticker.file_unique_id,
            )
        return message.sticker and message.sticker.file_unique_id == self._sticker_id


def sticker(sticker_id: str, debug: bool = False) -> filters.Filter:
    warnings.warn(
        "sticker() is deprecated, use StickerFilter() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return StickerFilter(sticker_id, debug)
