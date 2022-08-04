__all__ = [
    "commands",
    "react2ban",
    "react2ban_raw_reaction_handler",
]

import html
from asyncio import sleep
from datetime import datetime, timedelta

from pyrogram import Client, ContinuePropagation
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserAdminInvalid
from pyrogram.raw import base, functions, types
from pyrogram.types import Message
from pyrogram.utils import get_channel_id

from ..modules import CommandsModule
from ..storage import Storage
from ..utils import parse_delta

_REACT2BAN_TEXT = (
    "<b>⚠⚠⚠ ЭТО НЕ ШУТКА ⚠⚠⚠</b>\n"
    "На этом сообщении включена защита от реакций. Любой, кто поставит сюда реакцию, будет"
    " <b>забанен</b> в чате на полгода.\n"
    "\n"
    "<b>⚠⚠⚠ IT'S NOT A JOKE ⚠⚠⚠</b>\n"
    "This message is protected from reactions. Anyone who puts a reaction here will be"
    " <b>banned</b> in the chat for half a year.\n"
)

commands = CommandsModule()


@commands.add("chatban", usage="<reply 'reply'|id> [time|'0'|'forever'] [reason...]")
async def chat_ban(client: Client, message: Message, args: str) -> str:
    """Bans a user in a chat"""
    args_list = args.split(" ")
    if args_list[0] == "reply":
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = int(args_list[0])
    now = message.edit_date or message.date or datetime.now()
    if len(args_list) <= 1 or args_list[1] == "0" or args_list[1] == "forever":
        delta = None
        t = datetime.fromtimestamp(0)
    else:
        delta = parse_delta(args_list[1])
        t = now + delta
    reason = " ".join(args_list[2:])
    await client.ban_chat_member(message.chat.id, user_id, t)
    user = await client.get_chat(user_id)
    text = f"<a href='tg://user?id={user_id}'>{user.first_name}</a> <b>banned</b> in this chat"
    if delta:
        text += f" for <i>{args_list[1]}</i>."
    if reason:
        text += f"\n<b>Reason:</b> {reason}"
    return text


@commands.add("chatunban", usage="<id>")
async def chat_unban(client: Client, message: Message, args: str) -> str:
    """Unbans a user in a chat"""
    user_id = int(args)
    await client.unban_chat_member(message.chat.id, user_id)
    user = await client.get_chat(user_id)
    return f"<a href='tg://user?id={user_id}'>{user.first_name}</a> <b>unbanned</b> in this chat"


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


async def react2ban_raw_reaction_handler(
    client: Client,
    update: base.Update,
    users: dict[int, types.User],
    _: dict[int, types.Chat | types.Channel],
    *,
    storage: Storage,
) -> None:
    if not isinstance(update, types.UpdateMessageReactions):
        raise ContinuePropagation()  # don't consume an update here, it's not for this handler

    message_id = update.msg_id
    match update.peer:
        case types.PeerChannel(channel_id=peer_id):
            chat_id = get_channel_id(peer_id)
        case types.PeerChat(chat_id=peer_id):
            chat_id = -peer_id
        case _:
            raise AssertionError(f"Unsupported peer type: {update.peer.__class__.__name__}")
    if not await storage.is_react2ban_enabled(chat_id, update.msg_id):
        return
    t = f"{_REACT2BAN_TEXT}\nRecently banned:\n"
    for r in update.reactions.recent_reactions:
        user_id = r.peer_id.user_id
        name = users[user_id].first_name
        member = await client.get_chat_member(chat_id, user_id)
        if member.status != ChatMemberStatus.BANNED:
            try:
                await client.ban_chat_member(chat_id, user_id, datetime.now() + timedelta(days=180))
            except UserAdminInvalid:
                pass  # ignore, target peer is an admin or client lost the rights to ban anyone
            else:
                t += f"• <a href='tg://user?id={user_id}'>{name}</a> (#<code>{user_id}</code>)\n"
    try:
        await client.edit_message_text(chat_id, message_id, t)
    except FloodWait as e:
        await sleep(e.value + 1)
        await client.edit_message_text(chat_id, message_id, t)


async def react2ban(client: Client, message: Message, _: str, *, storage: Storage) -> str:
    """Bans a user whoever reacted to the message"""
    if message.chat.id > 0:
        return "❌ Not a group chat"
    self = await client.get_chat_member(message.chat.id, message.from_user.id)
    if self.privileges is None or not self.privileges.can_restrict_members:
        return "❌ Cannot ban users in the chat"
    await storage.add_react2ban(message.chat.id, message.id)
    return _REACT2BAN_TEXT
