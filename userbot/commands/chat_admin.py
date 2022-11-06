__all__ = [
    "commands",
    "react2ban_raw_reaction_handler",
]

import html
from asyncio import sleep
from datetime import datetime, timedelta
from typing import Type

from pyrogram import Client, ContinuePropagation
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserAdminInvalid
from pyrogram.raw import base, functions, types
from pyrogram.types import Message
from pyrogram.utils import get_channel_id

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..storage import Storage
from ..translation import Translation
from ..utils import _, parse_timespec

_REACT2BAN_TEXT = _(
    "<b>⚠⚠⚠ IT'S NOT A JOKE ⚠⚠⚠</b>\n"
    "This message is protected from reactions. Anyone who puts a reaction here will be"
    " <b>banned</b> in the chat for half a year."
)

commands = CommandsModule("Chat administration")


@commands.add("chatban", usage="<reply 'reply'|id> [timespec] [reason...]")
async def chat_ban(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    """Bans a user in a chat

    First argument must be a user ID to be banned or literal "reply" to ban the replied user.
    `timespec` can be a time delta (e.g. "1d3h"), a time string like "12:30" or "2022-12-31_23:59"),
    literal "0" or literal "forever" (for a permanent ban).
    If no time is specified, the user will be banned forever."""
    _ = tr.gettext
    args_list = command.args.split(" ")
    if args_list[0] == "reply":
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = int(args_list[0])
    now = message.edit_date or message.date or datetime.now()
    if len(args_list) <= 1 or args_list[1] == "0" or args_list[1] == "forever":
        t = None
    else:
        t = parse_timespec(now, args_list[1])
    reason = " ".join(args_list[2:])
    await client.ban_chat_member(message.chat.id, user_id, t)
    user = await client.get_chat(user_id)

    user_link = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
    text = _("{icon} {user_link} <b>banned</b> in this chat").format(
        icon=icons.PERSON_BLOCK,
        user_link=user_link,
    )
    if t:
        text += _(" until <i>{t:%Y-%m-%d %H:%M:%S %Z}</i>").format(t=t.astimezone())
    text += "."
    if reason:
        text += _("\n<b>Reason:</b> {reason}").format(reason=html.escape(reason))
    return text


@commands.add("chatunban", usage="<id>")
async def chat_unban(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    """Unbans a user in a chat"""
    _ = tr.gettext
    user_id = int(command.args)
    await client.unban_chat_member(message.chat.id, user_id)
    user = await client.get_chat(user_id)

    user_link = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
    return _("{icon} {user_link} <b>unbanned</b> in this chat").format(
        icon=icons.PERSON_TICK,
        user_link=user_link,
    )


@commands.add("promote", usage="<admin-title>")
async def promote(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    """Promotes a user to an admin without any rights but with title"""
    _ = tr.gettext
    title = command.args
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
            rank=title,
        )
    )
    return _("{icon} Chat title for the person was set to <i>{title}</i>").format(
        icon=icons.PENCIL,
        title=html.escape(title),
    )


async def react2ban_raw_reaction_handler(
    client: Client,
    update: base.Update,
    users: dict[int, types.User],
    ___: dict[int, types.Chat | types.Channel],
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
        case types.PeerUser():
            return
        case _:
            raise AssertionError(f"Unsupported peer type: {update.peer.__class__.__name__}")
    if not await storage.is_react2ban_enabled(chat_id, update.msg_id):
        return

    lang = await storage.get_chat_language(chat_id)
    tr = Translation(lang)
    _ = tr.gettext

    t = _("Recently banned:")
    for r in update.reactions.recent_reactions:
        user_id = r.peer_id.user_id
        name = users[user_id].first_name
        member = await client.get_chat_member(chat_id, user_id)
        if member.status != ChatMemberStatus.BANNED:
            try:
                await client.ban_chat_member(chat_id, user_id, datetime.now() + timedelta(days=180))
            except UserAdminInvalid:
                continue  # ignore, target peer is an admin or client lost the rights to ban anyone
        t += f"\n• <a href='tg://user?id={user_id}'>{name}</a> (#<code>{user_id}</code>)"
    t = "{header}\n\n{footer}".format(header=_(_REACT2BAN_TEXT), footer=t)
    try:
        await client.edit_message_text(chat_id, message_id, t)
    except FloodWait as e:
        await sleep(e.value + 1)
        await client.edit_message_text(chat_id, message_id, t)


@commands.add("react2ban", handle_edits=False)
async def react2ban(
    client: Client,
    message: Message,
    storage: Storage,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    """Bans a user whoever reacted to the message"""
    _ = tr.gettext
    if message.chat.id > 0:
        return _("{icon} Not a group chat").format(icon=icons.STOP)
    self = await client.get_chat_member(message.chat.id, message.from_user.id)
    if self.privileges is None or not self.privileges.can_restrict_members:
        return _("{icon} Cannot ban users in the chat").format(icon=icons.STOP)
    await storage.add_react2ban(message.chat.id, message.id)
    return _(_REACT2BAN_TEXT)


@commands.add("no_react2ban", "noreact2ban", usage="<reply>")
async def no_react2ban(
    message: Message,
    storage: Storage,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    """Stops react2ban on the message"""
    # TODO (2022-08-04): handle the case when the message with react2ban is deleted
    _ = tr.gettext
    if message.chat.id > 0:
        return _("{icon} Not a group chat").format(icon=icons.STOP)
    reply = message.reply_to_message
    await storage.remove_react2ban(message.chat.id, reply.id)
    await reply.edit(
        _("{icon} Reacting to the message to ban a user has been disabled on the message").format(
            icon=icons.INFO
        )
    )
    await message.delete()
