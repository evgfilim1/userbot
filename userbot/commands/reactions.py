__all__ = [
    "commands",
]

import random

from pyrogram import Client
from pyrogram.errors import MsgIdInvalid, ReactionEmpty, ReactionInvalid
from pyrogram.raw import functions, types
from pyrogram.types import Message

from ..modules import CommandsModule

commands = CommandsModule("Reactions")


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
    """Gets message reactions with users who reacted to it"""
    chat_peer = await client.resolve_peer(message.chat.id)
    t = ""
    try:
        messages: types.messages.MessageReactionsList = await client.invoke(
            functions.messages.GetMessageReactionsList(
                peer=chat_peer,
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
                    peer_name = user.first_name or "Deleted Account"
                    break
            else:
                peer_name = "Unknown user"
            t += f"- <a href='tg://user?id={peer_id}'>{peer_name}</a> (#<code>{peer_id}</code>)\n"
    return t or "<i>No reactions here</i>"


@commands.add("rr", usage="<reply>")
async def put_random_reaction(client: Client, message: Message, _: str) -> None:
    """Reacts to a message with a random available emoji"""
    chat = await client.get_chat(message.chat.id)
    await message.reply_to_message.react(random.choice(chat.available_reactions))
    await message.delete()
