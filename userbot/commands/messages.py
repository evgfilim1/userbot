__all__ = [
    "commands",
]

import asyncio
import html
import json

import jq
from pyrogram import Client
from pyrogram.errors import BadRequest
from pyrogram.raw import functions, types
from pyrogram.types import Message

from ..modules import CommandsModule

commands = CommandsModule("Messages")


@commands.add(["delete", "delet", "del"], usage="<reply>")
async def delete_this(_: Client, message: Message, __: str) -> None:
    """Deletes replied message for everyone"""
    try:
        await message.reply_to_message.delete()
    except BadRequest:
        pass
    await message.delete()


@commands.add("dump", usage="[jq-query]")
async def dump(_: Client, message: Message, args: str) -> str:
    """Dumps entire message or its attribute specified with jq syntax"""
    obj = message.reply_to_message or message
    result = jq.compile(f".{args}").input(text=str(obj)).all()
    text = json.dumps(
        result if len(result) > 1 else result[0],
        indent=2,
        ensure_ascii=False,
    )
    return f"<b>Attribute</b> <code>{args}</code>\n\n<pre>{html.escape(text)}</pre>"


@commands.add(
    "userfirstmsg",
    usage="[reply]",
    waiting_message="<i>Searching for user's first message...</i>",
)
async def user_first_message(client: Client, message: Message, _: str) -> str | None:
    """Replies to user's very first message in the chat"""
    if (user := (message.reply_to_message or message).from_user) is None:
        return "Cannot search for first message from channel"
    chat_peer = await client.resolve_peer(message.chat.id)
    user_peer = await client.resolve_peer(user.id)
    first_msg_raw = None
    while True:
        # It's rather slow, but it works properly
        messages: types.messages.Messages = await client.invoke(
            functions.messages.Search(
                peer=chat_peer,
                q="",
                filter=types.InputMessagesFilterEmpty(),
                min_date=0,
                max_date=first_msg_raw.date if first_msg_raw else 0,
                offset_id=0,
                add_offset=0,
                limit=100,
                min_id=0,
                max_id=0,
                from_id=user_peer,
                hash=0,
            ),
            sleep_threshold=60,
        )
        prev_max_id = first_msg_raw.id if first_msg_raw else 0
        for m in messages.messages:
            if m.id < (first_msg_raw.id if first_msg_raw is not None else 2**64):
                first_msg_raw = m
        await asyncio.sleep(0.1)
        if not messages.messages or prev_max_id == first_msg_raw.id:
            break
    if not first_msg_raw:
        return "🐞⚠ Cannot find any messages from this user (wtf?)"
    text = f"This is the first message of {user.mention}"
    if isinstance(first_msg_raw.peer_id, types.PeerChannel):
        text += f"\nPermalink: https://t.me/c/{first_msg_raw.peer_id.channel_id}/{first_msg_raw.id}"
    await client.send_message(
        message.chat.id,
        text,
        reply_to_message_id=first_msg_raw.id,
        disable_notification=True,
    )
    await message.delete()
