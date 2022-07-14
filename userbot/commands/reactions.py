__all__ = [
    "commands",
]

import random

from pyrogram import Client
from pyrogram.errors import MsgIdInvalid, ReactionEmpty, ReactionInvalid
from pyrogram.raw import functions, types
from pyrogram.types import Message

from ..modules import CommandsModule

commands = CommandsModule()


@commands.add("r", usage="<reply> [emoji]")
async def put_reaction(_: Client, message: Message, args: str) -> str | None:
    """Reacts to a message with a specified emoji or removes any reaction"""
    try:
        await message.reply_to_message.react(args)
    except ReactionInvalid:
        return args
    except ReactionEmpty:
        pass  # ignore
    await message.delete()


@commands.add("rs", usage="<reply>")
async def get_reactions(client: Client, message: Message, __: str) -> str:
    """Gets message reactions"""
    peer = await client.resolve_peer(message.chat.id)
    ids = [types.InputMessageID(id=message.reply_to_message.id)]
    if not isinstance(peer, types.InputPeerChannel):
        messages: types.messages.Messages = await client.invoke(
            functions.messages.GetMessages(
                id=ids,
            )
        )
    else:
        messages: types.messages.Messages = await client.invoke(
            functions.channels.GetMessages(
                channel=types.InputChannel(
                    channel_id=peer.channel_id,
                    access_hash=peer.access_hash,
                ),
                id=ids,
            )
        )
    t = ""
    if (
        not isinstance(messages.messages[0], types.MessageEmpty)
        and (reactions := messages.messages[0].reactions) is not None
    ):
        for r in reactions.results:
            t += f"<code>{r.reaction}</code>: {r.count}\n"
            for rr in reactions.recent_reactions or []:
                if rr.reaction == r.reaction:
                    peer = await client.get_chat(rr.peer_id.user_id)
                    peer_name = f"{peer.first_name or 'Deleted Account'} (#{peer.id})"
                    t += f"- <a href='tg://user?id={rr.peer_id.user_id}'>{peer_name}</a>\n"
    else:
        try:
            messages: types.messages.MessageReactionsList = await client.invoke(
                functions.messages.GetMessageReactionsList(
                    peer=peer,
                    id=message.reply_to_message.id,
                    limit=100,
                )
            )
        except MsgIdInvalid:
            return "<i>Message not found or has no reactions</i>"
        reactions = {}
        for r in messages.reactions:
            reactions.setdefault(r.reaction, set()).add(r.peer_id.user_id)
        for reaction, peers in reactions.items():
            t += f"<code>{reaction}</code>: {len(peers)}\n"
            for peer_id in peers:
                for user in messages.users:
                    if user.id == peer_id:
                        peer_name = f"{user.first_name or 'Deleted Account'} (#{user.id})"
                        break
                else:
                    peer_name = peer_id
                t += f"- <a href='tg://user?id={peer_id}'>{peer_name}</a>\n"
    return t or "<i>No reactions here</i>"


@commands.add("rr", usage="<reply>")
async def put_random_reaction(client: Client, message: Message, _: str) -> None:
    """Reacts to a message with a random emoji"""
    chat = await client.get_chat(message.chat.id)
    await message.reply_to_message.react(random.choice(chat.available_reactions))
    await message.delete()
