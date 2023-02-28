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
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..utils import Translation, gettext

commands = CommandsModule("Messages")


@commands.add("delete", "delet", "del", reply_required=True)
async def delete_this(message: Message, reply: Message) -> None:
    """Deletes replied message for everyone."""
    try:
        await reply.delete()
    except BadRequest:
        pass
    await message.delete()


@commands.add("dump", usage="[jq_query...]")
async def dump(
    message: Message,
    command: CommandObject,
    reply: Message | None,
    tr: Translation,
) -> str:
    """Dumps entire message or its attribute specified with `jq` syntax."""
    _ = tr.gettext
    obj = reply if reply is not None else message
    q = q_raw if (q_raw := command.args["jq_query"]) is not None else ""
    try:
        prog = jq.compile(q)
    except ValueError as e:
        return _(
            "{icon} <b>Invalid jq query:</b> <code>{attr}</code>\n"
            "<b>Details:</b>\n<pre>{e}</pre>\n\n"
            "<b>Possible fix:</b> <code>{full_command} .{attr}</code>"
        ).format(
            icon=Icons.WARNING,
            attr=html.escape(q),
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
        attr=html.escape(q),
        text=html.escape(text),
    )


@commands.add(
    "userfirstmsg",
    waiting_message=gettext("<i>Searching for user's first message...</i>"),
)
async def user_first_message(
    client: Client,
    message: Message,
    reply: Message | None,
    tr: Translation,
) -> str | None:
    """Looks for the user's very first message in the chat."""
    _ = tr.gettext
    msg = reply if reply is not None else message
    if (user := msg.from_user) is None:
        return _("{icon} Cannot search for first message from channel").format(icon=Icons.WARNING)
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
        if chats.chats[0].forum:
            return text
    await client.send_message(
        message.chat.id,
        text,
        reply_to_message_id=first_msg_raw.id,
        disable_notification=True,
    )
    await message.delete()


@commands.add("copyhere", "cphere", "cph", reply_required=True)
async def copy_here(message: Message, reply: Message) -> None:
    """Copies replied message to current chat."""
    await reply.copy(message.chat.id)
    if reply.from_user.id == message.from_user.id:
        await reply.delete()
    await message.delete()
