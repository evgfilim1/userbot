from __future__ import annotations

__all__ = [
    "resolve_user_or_user_group",
]

from dataclasses import dataclass, field

from lark import Lark, ParseTree, Tree, UnexpectedInput
from pyrogram import Client

from ..storage import Storage

_GRAMMAR = r"""
// The Lark grammar for the user group string of evgfilim1/userbot
//
// User group string consists of a user group name and an optional list of parameters in square
//  brackets. Parameters are separated by semicolons and have the following format:
// * `exclude=<comma-separated user_ids, usernames or user group strings>`
//   * This temporarily excludes users from the group
// * `include=<comma-separated user_ids, usernames or user group strings>`
//   * This temporarily includes users to the group
// `include` have more priority than `exclude`.
// The square brackets are optional if there are no parameters.
//
// Examples:
// * `admins`
// * `admins[]`: same as `admins`
// * `users[exclude=@user1,42,@user2,admins]`: exclude users by ID, username and user group
// * `users[exclude=@user1;include=@user2,admins]`: exclude and include users
// * `users[include=admins[exclude=@user1]]`: exclude users from nested user group

// Named terminals (captured user input)
USERNAME: "@" CNAME

// Rules
key: "exclude" -> exclude
    | "include" -> include
_value: INT | USERNAME | user_group
values: (_value ",")* _value
param: key "=" values
_params: (param ";")* param

// Main rule
user_group: CNAME ["[" _params? "]"]

// Parser directives
%import common (CNAME, INT, WORD)
"""
_parser = Lark(_GRAMMAR, start="user_group")


@dataclass()
class _UserGroup:
    name: str
    exclude: set[str | _UserGroup] = field(default_factory=set)
    include: set[str | _UserGroup] = field(default_factory=set)

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.exclude), tuple(self.include)))


def _parse_user_group_tree(tree: ParseTree) -> _UserGroup:
    result = _UserGroup(name=tree.children[0].value)
    for param in tree.children[1:]:
        key_name = param.children[0].data
        values = (
            _parse_user_group_tree(child) if isinstance(child, Tree) else child.value
            for child in param.children[1].children
        )
        if key_name == "exclude":
            result.exclude.update(values)
        elif key_name == "include":
            result.include.update(values)
        else:
            raise AssertionError(f"Unexpected key name: {key_name}")
    return result


def _parse_user_group_spec(user_group_spec: str) -> _UserGroup:
    """Parses user group spec and returns user group name and excluded users"""
    try:
        tree: ParseTree = _parser.parse(user_group_spec)
    except UnexpectedInput:
        raise ValueError(f"Invalid user group spec: {user_group_spec}")

    return _parse_user_group_tree(tree)


async def resolve_user_or_user_group(
    client: Client,
    storage: Storage,
    value: str | int,
) -> set[int]:
    """Resolves user by ID, username or user group by user group string

    User group string consists of a user group name and an optional list of parameters in square
    brackets. Parameters are separated by semicolons and have the following format:

    * `exclude=<comma-separated user_ids, usernames or user group strings>`: this temporarily
      excludes users from the group;
    * `include=<comma-separated user_ids, usernames or user group strings>`: this temporarily
      includes users to the group;
    * `include` have more priority than `exclude`;
    * The square brackets are optional if there are no parameters.
    """
    if isinstance(value, int):
        return [value]
    if value.isdecimal():
        return [int(value)]
    if value.startswith("@"):
        peer = await client.resolve_peer(value)
        return [peer.user_id]
    user_group = _parse_user_group_spec(value)
    exclude_ids: set[int] = set()
    include_ids: set[int] = set()
    for item in user_group.exclude:
        exclude_ids.update(await resolve_user_or_user_group(client, storage, item))
    for item in user_group.include:
        include_ids.update(await resolve_user_or_user_group(client, storage, item))
    users = set()
    async for user_id in storage.list_users_in_group(user_group.name):
        if user_id not in exclude_ids:
            users.add(user_id)
    users.update(include_ids)
    return users
