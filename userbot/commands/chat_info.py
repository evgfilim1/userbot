__all__ = [
    "commands",
]

import logging
from asyncio import sleep
from random import randint

from pyrogram import Client
from pyrogram.enums import MessagesFilter
from pyrogram.errors import BadRequest, PhotoCropSizeSmall
from pyrogram.types import Message

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..utils import Translation

commands = CommandsModule("Chat info")

_log = logging.getLogger(__name__)

ChatTitle = str


async def _get_random_message(
    chat_id: int,
    message_filter: MessagesFilter,
    client: Client,
) -> Message:
    """Gets a random message"""
    total = await client.search_messages_count(chat_id, filter=message_filter)
    offset = randint(0, total - 1)
    gen = client.search_messages(chat_id, filter=message_filter, offset=offset, limit=1)
    return await gen.__anext__()


async def _get_random_photo_message(
    chat_id: int,
    client: Client,
) -> Message:
    """Gets a random photo message"""
    return await _get_random_message(chat_id, MessagesFilter.PHOTO, client)


async def _set_random_chat_photo(chat_id: int, client: Client) -> Message:
    """Sets a random chat photo."""
    retries = 20
    while retries >= 0:
        message = await _get_random_photo_message(chat_id, client)
        try:
            await client.set_chat_photo(chat_id, photo=message.photo.file_id)
        except PhotoCropSizeSmall:
            continue
        else:
            return message
        finally:
            retries -= 1
    else:
        raise RuntimeError("Retries exceeded")


async def _get_random_chat_title(chat_id: int, client: Client) -> tuple[Message, ChatTitle]:
    """Gets a random chat title."""
    retries = 50
    chat = await client.get_chat(chat_id)
    title_prefix = chat.title.split(" — ")[0]
    while retries >= 0:
        message = await _get_random_message(chat_id, MessagesFilter.EMPTY, client)
        if message.text is not None:
            stripped_text = message.text[: 128 - len(title_prefix) - 3]
            chat_title = f"{title_prefix} — {stripped_text}"

            return message, chat_title
        retries -= 1
    raise RuntimeError("Retries exceeded")


async def _set_random_chat_title(chat_id: int, client: Client) -> Message:
    """Sets a random chat title."""
    message, chat_title = await _get_random_chat_title(chat_id, client)
    try:
        await client.set_chat_title(chat_id, chat_title)
    except BadRequest as e:
        _log.warning(
            "An error occurred while setting the chat title in %d",
            chat_id,
            exc_info=e,
        )
    return message


@commands.add("rndinfo", usage="['photo'|'title'|'all'] ['dry-run']")
async def random_chat_info(
    client: Client,
    message: Message,
    command: CommandObject,
    tr: Translation,
) -> str:
    """Sets random chat photo and/or title.

    Sets both if no argument is given.
    Specify `dry-run` as the second argument to get the message without actually setting it.
    """
    _ = tr.gettext
    text = ""
    what = command.args[0]
    if what is None:
        what = "all"
        is_dry_run = False
    else:
        is_dry_run = command.args[1] == "dry-run"
    if what in {"photo", "all"}:
        if is_dry_run:
            msg = await _get_random_photo_message(message.chat.id, client)
        else:
            msg = await _set_random_chat_photo(message.chat.id, client)
        text += _(
            "{icon} <b>New chat avatar was set!</b> <a href='{msg_link}'>Source</a>\n"
        ).format(icon=Icons.PICTURE, msg_link=msg.link)
        await sleep(0.1)
    if what in {"title", "all"}:
        if is_dry_run:
            msg, _chat_title = await _get_random_chat_title(message.chat.id, client)
        else:
            msg = await _set_random_chat_title(message.chat.id, client)
        text += _("{icon} <b>New chat title was set!</b> <a href='{msg_link}'>Source</a>").format(
            icon=Icons.PENCIL, msg_link=msg.link
        )
        await sleep(0.1)
    return text


@commands.add("rndmsg")
async def random_chat_message(client: Client, message: Message, tr: Translation) -> str:
    """Sends a random message from the chat."""
    _ = tr.gettext
    msg = await _get_random_message(message.chat.id, MessagesFilter.EMPTY, client)
    return _("<a href='{msg.link}'>Random message (#{msg.id})</a>").format(msg=msg)
