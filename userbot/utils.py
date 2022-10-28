from __future__ import annotations

__all__ = [
    "_",
    "__",
    "async_partial",
    "edit_or_reply",
    "fetch_stickers",
    "get_message_content",
    "get_text",
    "GitHubClient",
    "parse_timespec",
    "sticker",
    "StickerInfo",
    "Unset",
]

import functools
import html
import logging
import re
from base64 import b64encode
from collections import defaultdict
from datetime import datetime, time, timedelta
from types import TracebackType
from typing import Any, Awaitable, Callable, ClassVar, Protocol, Self, Type, TypedDict, TypeVar

from httpx import AsyncClient
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType, ParseMode
from pyrogram.raw import functions, types
from pyrogram.types import Chat, Message, User

from .translation import Translation

_T = TypeVar("_T")
_log = logging.getLogger(__name__)


class MessageMethod(Protocol):
    async def __call__(self, text: str, *, parse_mode: ParseMode | None) -> Message:
        pass


class AnswerMethod(Protocol):
    async def __call__(self, text: str, *, prefix_override: str | None = None) -> Message:
        pass


def sticker(sticker_id: str, debug: bool = False) -> filters.Filter:
    @filters.create
    def sticker_filter(_, __, c):
        if debug and c.sticker:
            print(c.sticker.file_id, c.sticker.file_unique_id)
        return c.sticker and c.sticker.file_unique_id == sticker_id

    return sticker_filter


def get_text(message: Message, *, as_html: bool = False) -> str | None:
    text = message.text or message.caption
    if as_html:
        text = text.html
    return text


def get_sender(message: Message) -> User | Chat:
    return message.from_user or message.sender_chat


def send_helper(fn: MessageMethod, prefix: str = "") -> AnswerMethod:
    @functools.wraps(fn)
    async def wrapper(text: str, prefix_override: str | None = None) -> Message:
        return await fn(
            f"{prefix_override or prefix}{html.escape(text)}",
            parse_mode=ParseMode.HTML,
        )

    return wrapper


def edit_or_reply(message: Message, tr: Translation) -> tuple[AnswerMethod, bool]:
    _ = tr.gettext
    reply_sender = get_sender(message.reply_to_message)
    sender = get_sender(message)
    if reply_sender.id == sender.id:  # it's me!
        if message.reply_to_message.caption is not None:
            return send_helper(message.reply_to_message.edit_caption), True
        return send_helper(message.reply_to_message.edit), True
    return send_helper(message.edit, _("<b>Maybe you mean:</b>\n\n")), False


def parse_delta(delta: str) -> timedelta | None:
    total_sec = 0
    for match in re.finditer(r"(\d+)([smhdwy])", delta, re.I):
        time_sec = int(match[1])
        match match[2]:
            case "m" | "M":
                time_sec *= 60
            case "h" | "H":
                time_sec *= 60 * 60
            case "d" | "D":
                time_sec *= 60 * 60 * 24
            case "w" | "W":
                time_sec *= 60 * 60 * 24 * 7
            case "y" | "Y":
                time_sec *= 60 * 60 * 24 * 365
        total_sec += time_sec
    if total_sec > 0:
        return timedelta(seconds=total_sec)
    return None


def parse_timespec(now: datetime, timespec: str) -> datetime:
    """Parse a time specification and return target datetime.

    The time specification is a string of the form:
    – HH:MM
    – YYYY-MM-DD_HH:MM
    – N[smhdwy]
    – N[smhdwy]N[smhdwy]...
    """
    if (delta := parse_delta(timespec)) is not None:
        return now + delta
    dt = timespec.split("_", maxsplit=1)
    if len(dt) == 2:  # date and time
        date = datetime.strptime(dt[0], "%Y-%m-%d").date()
        time_string = dt[1]
    else:  # only time
        date = now.date()
        time_string = dt[0]
    h, m = map(int, time_string.split(":", maxsplit=1))
    parsed_time = time(h, m)
    if parsed_time < now.time() and len(dt) == 1:
        return datetime.combine(now + timedelta(days=1), parsed_time)
    return datetime.combine(date, parsed_time)


class Unset:
    """A singleton to represent an unset value"""

    _instance: ClassVar[Unset | None] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Unset:
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __repr__(self) -> str:
        return "<unset>"

    def __str__(self) -> str:
        return repr(self)


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


class GitHubClient:
    def __init__(self, client: AsyncClient) -> None:
        client.base_url = "https://api.github.com"
        self._client = client

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._client.aclose()

    async def get_default_branch(self, owner: str, repo: str) -> str:
        return (await self._client.get(f"/repos/{owner}/{repo}")).json()["default_branch"]


def get_message_content(message: Message) -> tuple[dict[str, str | int], str]:
    if (text := message.text) is not None:
        # TODO (2022-09-08): `disable_web_page_preview`
        return {"text": text.html}, "text"
    if (media := message.media) is not None:
        # noinspection PyTypeChecker, PydanticTypeChecker
        # https://youtrack.jetbrains.com/issue/PY-54503
        media_type: str = media.value
        if media == MessageMediaType.STICKER:
            # `file_id` for stickers doesn't expire, so we can use it directly
            return {media_type: message.sticker.file_id}, media_type
        return {"from_chat_id": message.chat.id, "message_id": message.id}, media_type
    raise ValueError("Unsupported message type")


def _(s: str) -> str:
    """A dummy function that marks strings for translation."""
    return s


def __(one: str, many: str, n: int) -> str:
    """A dummy function that marks plural strings for translation."""
    return one if n == 1 else many


def async_partial(
    func: Callable[..., Awaitable[_T]],
    *args: Any,
    **kwargs: Any,
) -> Callable[..., Awaitable[_T]]:
    """Create a partial function that is awaitable."""

    @functools.wraps(func)
    async def wrapper(*args_: Any, **kwargs_: Any) -> _T:
        return await func(*args, *args_, **kwargs, **kwargs_)

    return wrapper
