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

from ..constants import Icons
from ..meta.modules import CommandObject, CommandsModule
from ..utils import _
from ..utils.translations import Translation

commands = CommandsModule("Messages")


@commands.add("delete", "delet", "del", usage="<reply>")
async def delete_this(message: Message) -> None:
    """Deletes replied message for everyone"""
    try:
        await message.reply_to_message.delete()
    except BadRequest:
        pass
    await message.delete()


@commands.add("dump", usage="[jq_query]")
async def dump(
    message: Message,
    command: CommandObject,
    icons: type[Icons],
    tr: Translation,
) -> str:
    """Dumps entire message or its attribute specified with jq syntax"""
    _ = tr.gettext
    obj = message.reply_to_message or message
    attr = command.args
    try:
        prog = jq.compile(attr)
    except ValueError as e:
        return _(
            "{icon} <b>Invalid jq query:</b> <code>{attr}</code>\n"
            "<b>Details:</b>\n<pre>{e}</pre>\n\n"
            "<b>Possible fix:</b> <code>{full_command} .{attr}</code>"
        ).format(
            icon=icons.WARNING,
            attr=html.escape(attr),
            e=str(e),
            full_command=command.full_command,
        )
    result = prog.input(text=str(obj)).all()
    text = json.dumps(
        result if len(result) > 1 else result[0],
        indent=2,
        ensure_ascii=False,
    )
    return _("<b>Attribute</b> <code>{attr}</code>\n\n<pre>{text}</pre>").format(
        attr=html.escape(attr),
        text=html.escape(text),
    )


@commands.add(
    "userfirstmsg",
    usage="[reply]",
    waiting_message=_("<i>Searching for user's first message...</i>"),
)
async def user_first_message(
    client: Client,
    message: Message,
    icons: type[Icons],
    tr: Translation,
) -> str | None:
    """Replies to user's very first message in the chat"""
    _ = tr.gettext
    if (user := (message.reply_to_message or message).from_user) is None:
        return _("{icon} Cannot search for first message from channel").format(icon=icons.WARNING)
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
        raise AssertionError("Cannot find any messages from this user")
    text = _("This is the first message of {mention}").format(mention=user.mention)
    if isinstance(first_msg_raw.peer_id, types.PeerChannel):
        text += "\n{text} https://t.me/c/{channel_id}/{msg_id}".format(
            text=_("Permalink:"),
            channel_id=first_msg_raw.peer_id.channel_id,
            msg_id=first_msg_raw.id,
        )
        chats: types.messages.Chats = await client.invoke(
            functions.channels.GetChannels(id=[chat_peer])
        )
        is_forum = chats.chats[0].forum
    else:
        is_forum = False  # a legacy group cannot be a forum
    if is_forum:
        return text
    await client.send_message(
        message.chat.id,
        text,
        reply_to_message_id=first_msg_raw.id,
        disable_notification=True,
    )
    await message.delete()


@commands.add("copyhere", "cphere", "cph", usage="<reply>")
async def copy_here(message: Message) -> None:
    """Copies replied message to current chat"""
    await message.reply_to_message.copy(message.chat.id)
    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.reply_to_message.delete()
    await message.delete()
