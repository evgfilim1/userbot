__all__ = [
    "commands",
    "react2ban_raw_reaction_handler",
]

import html
from asyncio import sleep
from datetime import datetime, timedelta
from typing import Literal, overload

from pyrogram import Client, ContinuePropagation
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import (
    FloodWait,
    UserAdminInvalid,
    UserAlreadyParticipant,
    UserNotParticipant,
    UserPrivacyRestricted,
)
from pyrogram.raw import base, functions, types
from pyrogram.types import ChatPermissions, Message
from pyrogram.utils import get_channel_id, zero_datetime

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..storage import Storage
from ..utils import Translation, gettext, parse_timespec, resolve_users

_REACT2BAN_TEXT = gettext(
    "<b>⚠⚠⚠ IT'S NOT A JOKE ⚠⚠⚠</b>\n"
    "This message is protected from reactions. Anyone who puts a reaction here will be"
    " <b>banned</b> in the chat for half a year."
)

commands = CommandsModule("Chat administration")


async def _check_can_ban_members(client: Client, chat_id: int) -> bool:
    self = await client.get_chat_member(chat_id, client.me.id)
    return self.privileges is not None and self.privileges.can_restrict_members


def _parse_restrict_perms(perms: str) -> ChatPermissions:
    """Parses a string of permissions into a ChatPermissions object.

    The string is a comma-separated list of permissions to restrict. Possible permissions are:
    "text", "media", "stickers", "polls", "links", "invite", "pin", "info".
    """
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_send_polls=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_change_info=True,
    )
    for p in perms.split(","):
        match p:
            case "text":
                permissions.can_send_messages = False
            case "media":
                permissions.can_send_media_messages = False
            case "stickers":
                permissions.can_send_other_messages = False
            case "polls":
                permissions.can_send_polls = False
            case "links":
                permissions.can_add_web_page_previews = False
            case "invite":
                permissions.can_invite_users = False
            case "pin":
                permissions.can_pin_messages = False
            case "info":
                permissions.can_change_info = False
            case _:
                raise ValueError(f"Unknown permission: {p}")
    return permissions


def _describe_permissions(
    permissions: ChatPermissions,
    default_permissions: ChatPermissions,
    tr: Translation,
) -> str:
    _ = tr.gettext
    enabled = _("✅")
    disabled = _("❌")
    it = zip(
        (
            permissions.can_send_messages,
            permissions.can_send_media_messages,
            permissions.can_send_other_messages,
            permissions.can_add_web_page_previews,
            permissions.can_send_polls,
            permissions.can_invite_users,
            permissions.can_pin_messages,
            permissions.can_change_info,
        ),
        (
            default_permissions.can_send_messages,
            default_permissions.can_send_media_messages,
            default_permissions.can_send_other_messages,
            default_permissions.can_add_web_page_previews,
            default_permissions.can_send_polls,
            default_permissions.can_invite_users,
            default_permissions.can_pin_messages,
            default_permissions.can_change_info,
        ),
        (
            _("Send messages"),
            _("Send media"),
            _("Send stickers & GIFs"),
            _("Embed links"),
            _("Send polls"),
            _("Add members"),
            _("Pin messages"),
            _("Change group info"),
        ),
    )
    text = ""
    for available, default, name in it:
        if default is False:
            continue  # This permission is disabled by default, so skip it
        text += f"{enabled if available else disabled} {name}\n"
    return text


def _get_restrict_info(
    permissions: ChatPermissions | None,
    default_chat_permissions: ChatPermissions,
    *,
    tr: Translation,
    is_forever: bool,
) -> str:
    """Returns a template string with information about the restrictions."""
    _ = tr.gettext
    if not is_forever:
        text = " " + _("until <i>{t:%Y-%m-%d %H:%M:%S %Z}</i>")
    else:
        text = ""
    if permissions is None:
        text = _("{icon} {users} <b>banned</b> in this chat") + text
    else:
        text = _("{icon} {users} <b>restricted</b> in this chat") + text
        text += ".\n{}\n".format(_("{icon_perms} <b>New permissions:</b>"))
        text += _describe_permissions(permissions, default_chat_permissions, tr)
    return text


@commands.add(
    "chatban",
    "chatrestrict",
    usage="<'reply'|user_id|username|user_group> ['0'|'forever'|timespec] ['*'|perms] [reason...]",
)
async def restrict_user(
    client: Client,
    message: Message,
    command: CommandObject,
    storage: Storage,
    tr: Translation,
) -> str:
    """Restricts or bans a user in a chat.

    First argument must be a user ID to be banned or literal "reply" to ban the replied user.

    `timespec` can be a time delta (e.g. "1d3h"), a time string like "12:30" or "2022-12-31_23:59"),
    literal "0" or literal "forever" (for a permanent restrict). If no time is specified, the user
    will be restricted forever.

    `perms` is a comma-separated list of permissions to be revoked from the user. To ban a user,
    pass "*" as `perms` (or omit it). Possible permissions are: "text", "media", "stickers",
    "polls", "links", "invite", "pin", "info".

    `reason` is an optional argument that will be shown in the ban message.
    """
    _ = tr.gettext
    user_arg, time, perms_str, reason = command.args
    if user_arg == "reply":
        user_ids = {message.reply_to_message.from_user.id}
    else:
        user_ids = await resolve_users(client, storage, user_arg)
    now = message.edit_date or message.date or datetime.now()
    if is_forever := (time in ("0", "forever", None)):
        t = zero_datetime()
    else:
        t = parse_timespec(now, time)
    ban = perms_str in ("*", None)
    if not ban:
        perms = _parse_restrict_perms(perms_str)
    else:
        perms = None
    users: list[str] = []
    for user_id in user_ids:
        user = await client.get_chat(user_id)
        info = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
        if user.username is not None:
            info += f" (@{user.username})"
        users.append(info)
        if not ban:
            await client.restrict_chat_member(message.chat.id, user_id, perms, t)
        else:
            await client.ban_chat_member(message.chat.id, user_id, t)
    chat = await client.get_chat(message.chat.id)
    text = _get_restrict_info(perms, chat.permissions, tr=tr, is_forever=is_forever).format(
        icon=Icons.PERSON_BLOCK,
        icon_perms=Icons.LOCK,
        users=", ".join(users),
        t=t.astimezone(),
    )
    if reason:
        text += "\n" + _("<b>Reason:</b> {reason}").format(reason=html.escape(reason))
    return text


@commands.add("chatunban", usage="<'reply'|user_id|username|user_group>")
async def chat_unban(
    client: Client,
    message: Message,
    command: CommandObject,
    storage: Storage,
    tr: Translation,
) -> str:
    """Unbans a user in a chat.

    First argument must be a user ID to be banned or literal "reply" to ban the replied user.
    """
    _ = tr.gettext
    user_arg = command.args[0]
    if user_arg == "reply":
        user_ids = {message.reply_to_message.from_user.id}
    else:
        user_ids = await resolve_users(client, storage, user_arg)
    links: list[str] = []
    for user_id in user_ids:
        user = await client.get_chat(user_id)
        info = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
        if user.username is not None:
            info += f" (@{user.username})"
        links.append(info)
        await client.unban_chat_member(message.chat.id, user_id)
    return (
        _("{icon} {user_links} <b>unbanned</b> in this chat").format(
            icon=Icons.PERSON_TICK,
            user_links=", ".join(links),
        )
        + "\n"
    )


@commands.add("promote", usage="<admin_title...>", reply_required=True)
async def promote(
    client: Client,
    message: Message,
    command: CommandObject,
    tr: Translation,
) -> str:
    """Promotes a user to an admin without any rights but with title."""
    # TODO (2023-01-21): promote to admin with custom permissions
    _ = tr.gettext
    title = command.args[0]
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
        icon=Icons.PENCIL,
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
    tr: Translation,
) -> str:
    """Bans a user whoever reacted to the message."""
    _ = tr.gettext
    if message.chat.id > 0:
        return _("{icon} Not a group chat").format(icon=Icons.STOP)
    if not await _check_can_ban_members(client, message.chat.id):
        return _("{icon} Cannot ban users in the chat").format(icon=Icons.STOP)
    await storage.add_react2ban(message.chat.id, message.id)
    return _(_REACT2BAN_TEXT)


@commands.add("no_react2ban", "noreact2ban", reply_required=True)
async def no_react2ban(
    message: Message,
    storage: Storage,
    tr: Translation,
) -> str:
    """Stops react2ban on the message."""
    # TODO (2022-08-04): handle the case when the message with react2ban is deleted
    _ = tr.gettext
    if message.chat.id > 0:
        return _("{icon} Not a group chat").format(icon=Icons.STOP)
    reply = message.reply_to_message
    await storage.remove_react2ban(message.chat.id, reply.id)
    await reply.edit(
        _("{icon} Reacting to the message to ban a user has been disabled on the message").format(
            icon=Icons.INFO
        )
    )
    await message.delete()


@overload
async def _pin_common(
    message: Message,
    *,
    no_notify: bool,
    tr: Translation,
    return_result: Literal[False],
) -> None:
    ...


@overload
async def _pin_common(
    message: Message,
    *,
    no_notify: bool,
    tr: Translation,
    return_result: Literal[True],
) -> str:
    ...


async def _pin_common(
    message: Message,
    *,
    no_notify: bool,
    tr: Translation,
    return_result: bool,
) -> str | None:
    """Common code for `pin` and `s_pin`."""
    _ = tr.gettext
    await message.pin(disable_notification=no_notify, both_sides=True)
    if return_result:
        r = _("{icon} Message pinned").format(icon=Icons.PIN)
        if no_notify:
            r += " " + _("silently")
        return r
    return None


@commands.add("pin", usage="['silent']", reply_required=True)
async def pin(
    command: CommandObject,
    reply: Message,
    tr: Translation,
) -> str:
    """Pins the message.

    If 'silent' is specified, the message will be pinned without notification.
    """
    return await _pin_common(
        reply,
        no_notify=command.args[0] == "silent",
        tr=tr,
        return_result=True,
    )


@commands.add("s_pin", usage="['silent']", reply_required=True)
async def s_pin(
    message: Message,
    command: CommandObject,
    reply: Message,
    tr: Translation,
) -> None:
    """Pins the message silently (without returning the result).

    If 'silent' is specified, the message will be pinned without notification.
    """
    await _pin_common(
        reply,
        no_notify=command.args[0] == "silent",
        tr=tr,
        return_result=True,
    )
    await message.delete()


@commands.add(
    "chatcleardel",
    waiting_message=gettext("<i>Clearing Deleted Accounts...</i>"),
    timeout=1800,
)
async def kick_deleted_accounts(
    client: Client,
    message: Message,
    tr: Translation,
) -> str:
    """Kicks Deleted Accounts from the chat."""
    _ = tr.gettext
    __ = tr.ngettext
    chat_id = message.chat.id
    if chat_id > 0:
        return _("{icon} Not a group chat").format(icon=Icons.STOP)
    if not await _check_can_ban_members(client, chat_id):
        return _("{icon} Cannot ban users in the chat").format(icon=Icons.STOP)
    kicked = 0
    failed = 0
    total = 0
    async for member in client.get_chat_members(chat_id):
        total += 1
        if not member.user.is_deleted:
            continue
        try:
            await client.ban_chat_member(
                chat_id,
                member.user.id,
                datetime.now() + timedelta(minutes=1),
            )
        except UserAdminInvalid:
            # Target user is an admin or client lost the rights to ban anyone
            failed += 1
            continue
        else:
            kicked += 1
    kicked_text = _("<b>Kicked</b> Deleted Accounts: <i>{n}/{total_deleted}</i>").format(
        n=kicked,
        total_deleted=kicked + failed,
    )
    total_checked_text = __(
        "<i>({n} member checked)</i>",
        "<i>({n} members checked)</i>",
        total,
    ).format(n=total)
    return f"{Icons.PERSON_BLOCK} {kicked_text} {total_checked_text}"


@commands.add("chatinvite", usage="<user_id|username|user_group> ['verify']")
async def invite_to_chat(
    client: Client,
    message: Message,
    command: CommandObject,
    storage: Storage,
    tr: Translation,
) -> None:
    """Invites users to the current chat.

    If 'verify' is specified, the bot will verify the users were actually added to the group.
    """
    _ = tr.gettext
    value = command.args[0]
    users = await resolve_users(client, storage, value)
    if message.chat.type == ChatType.GROUP:
        for user in users:
            try:
                await client.add_chat_members(message.chat.id, user)
            except UserAlreadyParticipant:
                pass  # ignore
            except UserPrivacyRestricted:
                pass  # ignore
    else:
        try:
            await client.add_chat_members(message.chat.id, list(users))
        except UserPrivacyRestricted:
            pass  # ignore
    if command.args[1] == "verify":
        added = set()
        failed = set()
        if message.chat.type == ChatType.GROUP:
            full_chat: types.messages.ChatFull = await client.invoke(
                functions.messages.GetFullChat(
                    chat_id=(await client.resolve_peer(message.chat.id)).chat_id,
                )
            )
            members = set(p.user_id for p in full_chat.full_chat.participants.participants)
            for user in users:
                if user not in members:
                    failed.add(user)
                else:
                    added.add(user)
        else:
            for user in users:
                try:
                    participant: types.channels.ChannelParticipant = await client.invoke(
                        functions.channels.GetParticipant(
                            channel=await client.resolve_peer(message.chat.id),
                            participant=await client.resolve_peer(user),
                        )
                    )
                except UserNotParticipant:
                    failed.add(user)
                    continue
                p = participant.participant
                if isinstance(p, (types.ChannelParticipantLeft, types.ChannelParticipantBanned)):
                    failed.add(user)
                else:
                    added.add(user)
        return _(
            "{icon} Add <code>{value}</code> to the chat:"
            " <i>{added}</i> added, <i>{failed}</i> failed."
        ).format(
            icon=Icons.PERSON_TICK,
            value=value,
            added=len(added),
            failed=len(failed),
        )
    return _("{icon} <code>{value}</code> has been invited to the chat").format(
        icon=Icons.PERSON_TICK,
        value=value,
    )
