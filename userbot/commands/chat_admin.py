__all__ = [
    "commands",
]

import html
from datetime import datetime

from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.types import Message

from ..utils import parse_delta
from ..modules import CommandsModule

commands = CommandsModule()


@commands.add("chatban", usage="<id> [time] [reason...]")
async def chat_ban(client: Client, message: Message, args: str) -> str:
    """Bans a user in a chat"""
    args_list = args.split(" ")
    user_id = int(args_list[0])
    now = message.edit_date or message.date or datetime.now()
    if len(args_list) > 1:
        delta = parse_delta(args_list[1])
        t = now + delta
    else:
        delta = None
        t = datetime.fromtimestamp(0)
    reason = " ".join(args_list[2:])
    await client.ban_chat_member(message.chat.id, user_id, t)
    user = await client.get_chat(user_id)
    text = f"<a href='tg://user?id={user_id}'>{user.first_name}</a> <b>banned</b> in this chat"
    if delta:
        text += f" for <i>{args_list[1]}</i>."
    if reason:
        text += f"\n<b>Reason:</b> {reason}"
    return text


@commands.add("promote", usage="<admin-title>")
async def promote(client: Client, message: Message, args: str) -> str:
    """Promotes a user to an admin without any rights but with title"""
    await client.invoke(
        functions.channels.EditAdmin(
            channel=await client.resolve_peer(message.chat.id),
            user_id=await client.resolve_peer(message.reply_to_message.from_user.id),
            admin_rights=types.chat_admin_rights.ChatAdminRights(
                change_info=False,
                delete_messages=False,
                ban_users=False,
                invite_users=False,
                pin_messages=False,
                add_admins=False,
                anonymous=False,
                manage_call=False,
                other=True,
            ),
            rank=args,
        )
    )
    return f"Должность в чате установлена на <i>{html.escape(args)}</i>"
