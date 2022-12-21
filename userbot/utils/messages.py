__all__ = [
    "edit_replied_or_reply",
    "get_message_content",
    "get_message_entities",
    "get_message_text",
]

import html

from pyrogram.enums import MessageEntityType, MessageMediaType, ParseMode
from pyrogram.types import Chat, Message, MessageEntity, User


def get_message_text(message: Message, *, as_html: bool = False) -> str | None:
    text = message.text or message.caption
    if text is None:
        return None
    if as_html:
        text = text.html
    return str(text)


def get_message_entities(message: Message) -> list[MessageEntity] | None:
    return message.entities or message.caption_entities


def get_sender(message: Message) -> User | Chat:
    return message.from_user or message.sender_chat


async def edit_replied_or_reply(
    message: Message,
    text: str,
    *,
    maybe_you_mean_prefix: str,
    entities: list[MessageEntity] | None = None,
) -> Message:
    reply = message.reply_to_message
    is_my_message = get_sender(reply).id == get_sender(message).id
    if not is_my_message:
        method = message.edit_text
        entities_key = "entities"
    elif reply.text:
        method = reply.edit_text
        entities_key = "entities"
    elif reply.caption:
        method = reply.edit_caption
        entities_key = "caption_entities"
    else:
        raise ValueError("Unsupported message type")

    entities = entities if entities is not None else []
    parse_mode = ParseMode.DISABLED if entities else ParseMode.HTML
    if not is_my_message and maybe_you_mean_prefix:
        prefix = maybe_you_mean_prefix + "\n\n"
        for entity in entities:
            entity.offset += len(prefix)
    else:
        prefix = ""
    if prefix:
        if entities:
            entities.insert(
                0, MessageEntity(type=MessageEntityType.BOLD, offset=0, length=len(prefix))
            )
        else:
            prefix = f"<b>{html.escape(prefix)}</b>"
    r = await method(f"{prefix}{text}", parse_mode=parse_mode, **{entities_key: entities})
    if is_my_message:
        await message.delete()
    return r


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
        media_type: str = media.value
        if media == MessageMediaType.STICKER:
            # `file_id` for stickers doesn't expire, so we can use it directly
            return {media_type: message.sticker.file_id}, media_type
        return {"from_chat_id": message.chat.id, "message_id": message.id}, media_type
    raise ValueError("Unsupported message type")
