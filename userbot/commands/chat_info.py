__all__ = [
    "commands",
]

from asyncio import sleep
from random import randint
from typing import Type

from pyrogram import Client
from pyrogram.enums import MessagesFilter
from pyrogram.errors import BadRequest, PhotoCropSizeSmall
from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..translation import Translation

commands = CommandsModule("Chat info")


async def get_random_message(
    chat_id: int,
    message_filter: MessagesFilter,
    client: Client,
) -> Message:
    total = await client.search_messages_count(chat_id, filter=message_filter)
    offset = randint(0, total - 1)
    gen = client.search_messages(chat_id, filter=message_filter, offset=offset, limit=1)
    return await gen.__anext__()


async def set_random_chat_photo(chat_id: int, client: Client) -> Message:
    """Sets a random chat photo"""
    retries = 20
    while retries >= 0:
        message = await get_random_message(chat_id, MessagesFilter.PHOTO, client)
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


async def set_random_chat_title(chat_id: int, client: Client) -> Message:
    """Sets a random chat title"""
    retries = 50
    chat = await client.get_chat(chat_id)
    title_prefix = chat.title.split(" — ")[0]
    while retries >= 0:
        message = await get_random_message(chat_id, MessagesFilter.EMPTY, client)
        try:
            if message.text is None:
                continue
            stripped_text = message.text[: 128 - len(title_prefix) - 3]
            await client.set_chat_title(chat_id, f"{title_prefix} — {stripped_text}")
        except BadRequest as e:
            print(f"An exception occurred: {e}")
            continue
        else:
            return message
        finally:
            retries -= 1
    else:
        raise RuntimeError("Retries exceeded")


@commands.add("rndinfo", usage="['photo'|'title']")
async def random_chat_info(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    """Sets random chat photo and/or title

    Sets both if no argument is given."""
    _ = tr.gettext
    text = ""
    args = command.args
    if args == "photo" or args == "":
        msg = await set_random_chat_photo(message.chat.id, client)
        text += _(
            "{icon} <b>New chat avatar was set!</b> <a href='{msg_link}'>Source</a>\n"
        ).format(icon=icons.PICTURE, msg_link=msg.link)
        await sleep(0.1)
    if args == "title" or args == "":
        msg = await set_random_chat_title(message.chat.id, client)
        text += _("{icon} <b>New chat title was set!</b> <a href='{msg_link}'>Source</a>").format(
            icon=icons.PENCIL, msg_link=msg.link
        )
        await sleep(0.1)
    return text


@commands.add("rndmsg")
async def random_chat_message(client: Client, message: Message, tr: Translation) -> str:
    """Sends a random message from the chat"""
    _ = tr.gettext
    msg = await get_random_message(message.chat.id, MessagesFilter.EMPTY, client)
    return _("<a href='{msg.link}'>Random message (#{msg.id})</a>").format(msg=msg)
