__all__ = [
    "commands",
]

from asyncio import sleep
from random import randint

from pyrogram import Client
from pyrogram.enums import MessagesFilter
from pyrogram.errors import BadRequest, PhotoCropSizeSmall
from pyrogram.types import Message

from ..modules import CommandsModule

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
async def random_chat_info(client: Client, message: Message, args: str) -> str:
    """Sets random chat photo and/or title"""
    text = ""
    if args == "photo" or args == "":
        msg = await set_random_chat_photo(message.chat.id, client)
        text += f"🖼 <b>New chat avatar was set!</b> <a href='{msg.link}'>Source</a>\n\n"
        await sleep(0.1)
    if args == "title" or args == "":
        msg = await set_random_chat_title(message.chat.id, client)
        text += f"📝 <b>New chat title was set!</b> <a href='{msg.link}'>Source</a>"
        await sleep(0.1)
    return text


@commands.add("rndmsg", usage="")
async def random_chat_message(client: Client, message: Message, _: str) -> str:
    """Sends a random message from the chat"""
    msg = await get_random_message(message.chat.id, MessagesFilter.EMPTY, client)
    return f"<a href='{msg.link}'>Random message (#{msg.id})</a>"
