__all__ = [
    "AppLimits",
    "get_app_limits",
    "Limit",
]

from dataclasses import dataclass
from typing import Any, NamedTuple

from pyrogram import Client
from pyrogram.raw import functions

from .telegram_json import json_value_to_python


class Limit(NamedTuple):
    default: int
    premium: int

    def get(self, is_premium: bool) -> int:
        return self.premium if is_premium else self.default


@dataclass()
class AppLimits:
    channels: Limit
    saved_gifs: Limit
    # https://limits.tginfo.me/
    stickers: Limit = Limit(200, 200)


async def get_app_limits(client: Client) -> AppLimits:
    res: dict[str, Any] = json_value_to_python(await client.invoke(functions.help.GetAppConfig()))
    return AppLimits(
        channels=Limit(
            default=int(res["channels_limit_default"]),
            premium=int(res["channels_limit_premium"]),
        ),
        saved_gifs=Limit(
            default=int(res["saved_gifs_limit_default"]),
            premium=int(res["saved_gifs_limit_premium"]),
        ),
    )
