__all__ = [
    "DialogCount",
    "get_dialogs_count",
]

from dataclasses import dataclass
from typing import AsyncIterable, Iterable, NamedTuple

from pyrogram import Client
from pyrogram.raw import base, functions, types


@dataclass()
class DialogCount:
    """A class to store the number of dialogs by type."""

    private: int
    bots: int
    groups: int
    supergroups: int
    channels: int
    muted: int
    unread: int

    @property
    def total(self) -> int:
        """Total number of dialogs"""
        return self.private + self.bots + self.groups + self.supergroups + self.channels

    @property
    def private_chats(self) -> int:
        """Number of private dialogs"""
        return self.private + self.bots

    @property
    def group_chats(self) -> int:
        """Number of group and supergroup dialogs"""
        return self.groups + self.supergroups


class _DialogData(NamedTuple):
    users: dict[int, types.User]
    chats: dict[int, types.Chat]
    channels: dict[int, types.Channel]
    messages: dict[int, types.Message]
    channel_messages: dict[tuple[int, int], types.Message]


def _dialog_data_parser(
    api_result: types.messages.Dialogs | types.messages.DialogsSlice | types.messages.PeerDialogs,
) -> _DialogData:
    users: dict[int, types.User] = {i.id: i for i in api_result.users}
    chats: dict[int, types.Chat] = {}
    channels: dict[int, types.Channel] = {}
    for i in api_result.chats:
        if isinstance(i, (types.Chat, types.ChatForbidden)):
            chats[i.id] = i
        elif isinstance(i, (types.Channel, types.ChannelForbidden)):
            channels[i.id] = i
        else:
            raise ValueError(f"Unknown chat type: {i!r}")
    messages: dict[int, base.Message] = {}
    channel_messages: dict[tuple[int, int], base.Message] = {}
    for i in api_result.messages:
        # Telegram message IDs are unique across all chats except channels
        if isinstance(i.peer_id, types.PeerChannel):
            channel_messages[(i.peer_id.channel_id, i.id)] = i
        else:
            messages[i.id] = i
    return _DialogData(users, chats, channels, messages, channel_messages)


def _dialog_peer_iterator(
    dialogs: list[types.Dialog],
    data: _DialogData,
) -> Iterable[tuple[types.Dialog, base.User | base.Chat]]:
    for dialog in dialogs:
        if isinstance(dialog, types.DialogFolder) and dialog.folder.id == 1:
            continue
        if not isinstance(dialog, types.Dialog):
            raise AssertionError(f"Dialog {dialog!r} is not of type raw.types.Dialog")
        if isinstance(dialog.peer, types.PeerUser):
            peer = data.users[dialog.peer.user_id]
        elif isinstance(dialog.peer, types.PeerChat):
            peer = data.chats[dialog.peer.chat_id]
        elif isinstance(dialog.peer, types.PeerChannel):
            peer = data.channels[dialog.peer.channel_id]
        else:
            raise ValueError(f"Unknown peer type: {dialog.peer!r}")
        yield dialog, peer


async def _list_all_dialogs(
    client: Client,
) -> AsyncIterable[tuple[types.Dialog, base.User | base.Chat]]:
    """Lists all dialogs. Yields a tuple of (dialog, peer) with pinned chats first."""
    pinned: types.messages.PeerDialogs = await client.invoke(
        functions.messages.GetPinnedDialogs(
            folder_id=0,
        )
    )
    data = _dialog_data_parser(pinned)
    for i in _dialog_peer_iterator(pinned.dialogs, data):
        yield i

    offset_date = 0
    offset_id = 0
    offset_peer = types.InputPeerEmpty()
    while True:
        r: types.messages.Dialogs | types.messages.DialogsSlice = await client.invoke(
            functions.messages.GetDialogs(
                offset_date=offset_date,
                offset_id=offset_id,
                offset_peer=offset_peer,
                limit=100,
                hash=0,
                exclude_pinned=True,
            ),
            sleep_threshold=60,
        )

        dialogs: list[types.Dialog] = r.dialogs
        if not dialogs:
            break

        data = _dialog_data_parser(r)
        for i in _dialog_peer_iterator(dialogs, data):
            yield i

        last_dialog = dialogs[-1]
        last_peer = last_dialog.peer
        if isinstance(last_peer, types.PeerChannel):
            top_message = data.channel_messages[(last_peer.channel_id, last_dialog.top_message)]
        else:
            top_message = data.messages[last_dialog.top_message]
        offset_date = top_message.date
        offset_id = top_message.id
        offset_peer = last_peer


async def get_dialogs_count(client: Client) -> tuple[DialogCount, DialogCount]:
    """Get the number of dialogs. Returns a tuple of (total, archived) DialogCount objects."""
    counter = DialogCount(
        private=0,
        bots=0,
        groups=0,
        supergroups=0,
        channels=0,
        muted=0,
        unread=0,
    )
    archived_counter = DialogCount(
        private=0,
        bots=0,
        groups=0,
        supergroups=0,
        channels=0,
        muted=0,
        unread=0,
    )

    pm_notify_settings: types.PeerNotifySettings = await client.invoke(
        functions.account.GetNotifySettings(peer=types.InputNotifyUsers())
    )
    chat_notify_settings: types.PeerNotifySettings = await client.invoke(
        functions.account.GetNotifySettings(peer=types.InputNotifyChats())
    )
    channel_notify_settings: types.PeerNotifySettings = await client.invoke(
        functions.account.GetNotifySettings(peer=types.InputNotifyBroadcasts())
    )
    default_notify_settings: dict[
        type[types.PeerUser | types.PeerChat | types.PeerChannel], bool
    ] = {
        types.PeerUser: not bool(pm_notify_settings.silent or pm_notify_settings.mute_until),
        types.PeerChat: not bool(chat_notify_settings.silent or chat_notify_settings.mute_until),
        types.PeerChannel: not bool(
            channel_notify_settings.silent or channel_notify_settings.mute_until
        ),
    }

    async for dialog, peer in _list_all_dialogs(client):
        c = counter if dialog.folder_id != 1 else archived_counter
        if isinstance(peer, types.User):
            if peer.bot:
                c.bots += 1
            else:
                c.private += 1
        elif isinstance(peer, (types.Chat, types.ChatForbidden)):
            c.groups += 1
        elif isinstance(peer, (types.Channel, types.ChannelForbidden)):
            if peer.broadcast:
                c.channels += 1
            else:
                c.supergroups += 1
        else:
            raise ValueError(f"Unknown peer type: {peer!r}")
        if dialog.notify_settings.silent or dialog.notify_settings.mute_until:
            c.muted += 1
        else:
            for t, notify in default_notify_settings.items():
                if not isinstance(dialog.peer, t):
                    continue
                if not notify:
                    c.muted += 1
                break
            else:
                raise ValueError(f"Unknown peer type: {dialog.peer!r}")
        if dialog.unread_count or dialog.unread_mark or dialog.unread_mentions_count:
            c.unread += 1

    return counter, archived_counter
