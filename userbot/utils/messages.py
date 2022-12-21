__all__ = [
    "edit_or_reply",
    "get_message_content",
    "get_text",
]

import functools
import html
from typing import Protocol

from pyrogram.enums import MessageEntityType, MessageMediaType, ParseMode
from pyrogram.types import Chat, Message, User

from .translations import Translation


class MessageMethod(Protocol):
    async def __call__(self, text: str, *, parse_mode: ParseMode | None) -> Message:
        pass


class AnswerMethod(Protocol):
    async def __call__(self, text: str, *, prefix_override: str | None = None) -> Message:
        pass


def get_text(message: Message, *, as_html: bool = False) -> str | None:
    text = message.text or message.caption
    if text is None:
        return None
    if as_html:
        text = text.html
    return str(text)


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
    return send_helper(message.edit, _("<b>Maybe you mean:</b>") + "\n\n"), False


def get_message_content(message: Message) -> tuple[dict[str, str | int], str]:
    if (text := message.text) is not None:
        data = {"text": text.html}
        if (
            message.media != MessageMediaType.WEB_PAGE
            and message.entities is not None
            and any(
                entity.type in (MessageEntityType.TEXT_LINK, MessageEntityType.URL)
                for entity in message.entities
            )
        ):
            # Link exists but no preview
            data["disable_web_page_preview"] = True
        return data, "text"
    if (media := message.media) is not None:
        # noinspection PyTypeChecker, PydanticTypeChecker
        # https://youtrack.jetbrains.com/issue/PY-54503
        media_type: str = media.value
        if media == MessageMediaType.STICKER:
            # `file_id` for stickers doesn't expire, so we can use it directly
            return {media_type: message.sticker.file_id}, media_type
        return {"from_chat_id": message.chat.id, "message_id": message.id}, media_type
    raise ValueError("Unsupported message type")
