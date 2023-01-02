__all__ = [
    "commands",
]

from typing import NamedTuple

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import PeerIdInvalid
from pyrogram.raw.types import InputPeerUser
from pyrogram.types import Message

from ..constants import Icons
from ..meta.modules import CommandObject, CommandsModule
from ..storage import Storage
from ..utils import Translation

commands = CommandsModule("User groups")


class _ResolveResult(NamedTuple):
    result: list[int]
    errors: list[str]


async def _resolve_ids(client: Client, ids: list[str], tr: Translation) -> _ResolveResult:
    if len(ids) == 0:
        raise ValueError("No IDs provided")
    _ = tr.gettext
    result: list[int] = []
    errors: list[str] = []
    for chat_id in ids:
        try:
            chat = await client.resolve_peer(chat_id)
        except PeerIdInvalid:
            errors.append(_("{chat_id}: Cannot resolve peer").format(chat_id=chat_id))
            continue
        if not isinstance(chat, InputPeerUser):
            errors.append(_("{chat_id}: Not a user").format(chat_id=chat_id))
            continue
        result.append(chat.user_id)
    return _ResolveResult(result, errors)


@commands.add("usergroupadd", "ugadd", usage="<group-name> <reply|id> [id]...")
async def group_add(
    client: Client,
    message: Message,
    command: CommandObject,
    storage: Storage,
    icons: type[Icons],
    tr: Translation,
) -> str:
    """Adds a user to the user group for later use with user resolving"""
    _ = tr.gettext
    __ = tr.ngettext
    errors: list[str] | None = None
    args = command.args.split()
    group_name = args[0]
    if len(args) == 1:
        user_ids = [message.reply_to_message.from_user.id]
    else:
        user_ids, errors = await _resolve_ids(client, args[1:], tr)
    await storage.add_users_to_group(user_ids, group_name)
    t = __(
        "{icon} Added {count} user to user group {group_name}",
        "{icon} Added {count} users to user group {group_name}",
        len(user_ids),
    ).format(
        icon=icons.PERSON_TICK,
        count=len(user_ids),
        group_name=group_name,
    )
    if errors:
        t += "\n" + _("<b>Errors:</b>")
        for error in errors:
            t += f"\n• {error}"
    return t


@commands.add("usergroupdel", "ugdel", usage="<group-name> <reply|id> [id]...")
async def group_del(
    client: Client,
    message: Message,
    command: CommandObject,
    storage: Storage,
    icons: type[Icons],
    tr: Translation,
) -> str:
    """Removes a user from the user group"""
    _ = tr.gettext
    __ = tr.ngettext
    errors: list[str] | None = None
    args = command.args.split()
    group_name = args[0]
    if len(args) == 1:
        user_ids = [message.reply_to_message.from_user.id]
    else:
        user_ids, errors = await _resolve_ids(client, args[1:], tr)
    await storage.remove_users_from_group(user_ids, group_name)
    t = __(
        "{icon} Removed {count} user from user group {group_name}",
        "{icon} Removed {count} users from user group {group_name}",
        len(user_ids),
    ).format(
        icon=icons.PERSON_BLOCK,
        count=len(user_ids),
        group_name=group_name,
    )
    if errors:
        t += "\n" + _("<b>Errors:</b>")
        for error in errors:
            t += f"\n• {error}"
    return t


@commands.add("usergrouplist", "uglist", usage="<group-name> ['resolve']")
async def group_list(
    client: Client,
    command: CommandObject,
    storage: Storage,
    icons: type[Icons],
    tr: Translation,
) -> str:
    """Lists the users in the user group

    If 'resolve' is passed as the second argument, the user ids will be resolved to usernames"""
    _ = tr.gettext
    args = command.args.split()
    group_name = args[0]
    resolve = len(args) > 1 and args[1] == "resolve"
    users: list[int] = [x async for x in storage.list_users_in_group(group_name)]
    t = _("{icon} Users in user group {key}:").format(icon=icons.GROUP_CHAT, key=group_name)
    if resolve:
        for user in await client.get_users(users):
            username = f"@{user.username}" if user.username is not None else None
            t += f"\n• {user.mention(username, style=ParseMode.HTML)} (<code>{user.id}</code>)"
    else:
        for user in users:
            t += f"\n• <a href='tg://user?id={user}'>id{user}</a>"
    return t


@commands.add("usergroups", "ugs")
async def groups(
    storage: Storage,
    icons: type[Icons],
    tr: Translation,
) -> str:
    """Lists all the user groups"""
    _ = tr.gettext
    t = _("{icon} User groups:").format(icon=icons.GROUP_CHAT)
    async for group in storage.list_groups():
        t += f"\n• <code>{group}</code>"
    return t
