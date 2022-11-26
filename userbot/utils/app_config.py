__all__ = [
    "AppLimits",
    "AppLimitsController",
    "get_app_limits",
    "Limit",
]

from dataclasses import dataclass
from typing import NamedTuple

from pyrogram import Client
from pyrogram.raw import functions
from pyrogram.raw.types import JsonObject

from .telegram_json import json_value_to_python


class Limit(NamedTuple):
    default: int
    premium: int

    def get(self, is_premium: bool) -> int:
        return self.premium if is_premium else self.default


@dataclass(kw_only=True)
class AppLimits:
    channels: Limit
    saved_gifs: Limit
    favorite_stickers: Limit
    folders: Limit
    chats_in_folder: Limit
    pinned_chats: Limit
    pinned_chats_in_folder: Limit
    public_links: Limit
    caption_length: Limit
    bio_length: Limit
    reactions_on_message: Limit
    # https://limits.tginfo.me/
    text_length: Limit = Limit(4096, 4096)
    stickers: Limit = Limit(200, 200)


async def get_app_limits(client: Client) -> AppLimits:
    app_config: JsonObject = await client.invoke(functions.help.GetAppConfig())
    res = json_value_to_python(app_config)
    return AppLimits(
        channels=Limit(
            default=int(res["channels_limit_default"]),
            premium=int(res["channels_limit_premium"]),
        ),
        saved_gifs=Limit(
            default=int(res["saved_gifs_limit_default"]),
            premium=int(res["saved_gifs_limit_premium"]),
        ),
        favorite_stickers=Limit(
            default=int(res["stickers_faved_limit_default"]),
            premium=int(res["stickers_faved_limit_premium"]),
        ),
        folders=Limit(
            default=int(res["dialog_filters_limit_default"]),
            premium=int(res["dialog_filters_limit_premium"]),
        ),
        chats_in_folder=Limit(
            default=int(res["dialog_filters_chats_limit_default"]),
            premium=int(res["dialog_filters_chats_limit_premium"]),
        ),
        pinned_chats=Limit(
            default=int(res["dialogs_pinned_limit_default"]),
            premium=int(res["dialogs_pinned_limit_premium"]),
        ),
        pinned_chats_in_folder=Limit(
            default=int(res["dialogs_folder_pinned_limit_default"]),
            premium=int(res["dialogs_folder_pinned_limit_premium"]),
        ),
        public_links=Limit(
            default=int(res["channels_public_limit_default"]),
            premium=int(res["channels_public_limit_premium"]),
        ),
        caption_length=Limit(
            default=int(res["caption_length_limit_default"]),
            premium=int(res["caption_length_limit_premium"]),
        ),
        bio_length=Limit(
            default=int(res["about_length_limit_default"]),
            premium=int(res["about_length_limit_premium"]),
        ),
        reactions_on_message=Limit(
            default=int(res["reactions_user_max_default"]),
            premium=int(res["reactions_user_max_premium"]),
        ),
    )


class AppLimitsController:
    """A class to store Telegram limits."""

    def __init__(self) -> None:
        self._limits: AppLimits | None = None

    async def load_limits(self, client: Client) -> AppLimits:
        self._limits = await get_app_limits(client)
        return self._limits

    @property
    def limits(self) -> AppLimits:
        if self._limits is None:
            raise RuntimeError("App limits have not been loaded yet")
        return self._limits
