__all__ = [
    "commands",
]

from typing import NamedTuple

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import PeerIdInvalid
from pyrogram.types import Message

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..storage import Storage
from ..utils import Translation, resolve_users

commands = CommandsModule("User groups")


class _ResolveResult(NamedTuple):
    result: list[int]
    errors: list[str]


async def _resolve_users(
    client: Client,
    ids: list[str],
    storage: Storage,
    tr: Translation,
) -> _ResolveResult:
    if len(ids) == 0:
        raise ValueError("No IDs provided")
    _ = tr.gettext
    result: list[int] = []
    errors: list[str] = []
    for chat_id in ids:
        try:
            user_ids = await resolve_users(client, storage, chat_id, resolve_ids=True)
        except PeerIdInvalid:
            errors.append(_("{chat_id}: Cannot resolve peer").format(chat_id=chat_id))
            continue
        except AttributeError as e:
            e_msg = str(e)
            if not ("user_id" in e_msg and "Peer" in e_msg):
                # FIXME (2023-01-23): Temporary workaround unless I implement custom exceptions
                raise
            errors.append(_("{chat_id}: Not a user").format(chat_id=chat_id))
            continue
        result.extend(user_ids)
    return _ResolveResult(result, errors)


@commands.add(
    "usergroupadd",
    "ugadd",
    usage="<group_name> [user_id|username|user_group]...",
)
async def group_add(
    client: Client,
    command: CommandObject,
    reply: Message | None,
    storage: Storage,
    icons: type[Icons],
    tr: Translation,
) -> str:
    """Adds a user to the user group for later use with user resolving"""
    _ = tr.gettext
    __ = tr.ngettext
    errors: list[str] | None = None
    group_name, users = command.args
    if len(users) == 0:
        user_ids = [reply.from_user.id]
    else:
        user_ids, errors = await _resolve_users(client, users, storage, tr)
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


@commands.add(
    "usergroupdel",
    "ugdel",
    usage="<group_name> [user_id|username|user_group]...",
)
async def group_del(
    client: Client,
    command: CommandObject,
    reply: Message | None,
    storage: Storage,
    icons: type[Icons],
    tr: Translation,
) -> str:
    """Removes a user from the user group"""
    _ = tr.gettext
    __ = tr.ngettext
    errors: list[str] | None = None
    group_name, users = command.args
    if len(users) == 0:
        user_ids = [reply.from_user.id]
    else:
        user_ids, errors = await _resolve_users(client, users, storage, tr)
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


@commands.add("usergrouplist", "uglist", usage="<group_name> ['resolve']")
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
    args = command.args
    group_name = args["group_name"]
    resolve = args[1] == "resolve"
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
