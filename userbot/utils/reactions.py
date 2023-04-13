__all__ = [
    "react",
]

from pyrogram import Client
from pyrogram.raw import functions, types


async def react(
    client: Client,
    chat_id: int,
    message_id: int,
    reaction: str | int | None,
    add_to_existing: bool = False,
) -> None:
    """Reacts to a message with a specified emoji or removes any reaction.

    If `add_to_existing` is `True`, the reaction will be added to the existing ones, otherwise
    it will replace them.
    If `reaction` is `None`, and `add_to_existing` is `False` (default), all reactions will be
    removed.
    """
    reactions = []
    chat = await client.resolve_peer(chat_id)
    if reaction is not None:
        if isinstance(reaction, str):
            raw_reaction = types.ReactionEmoji(emoticon=reaction)
        else:
            raw_reaction = types.ReactionCustomEmoji(document_id=reaction)
        if add_to_existing:
            messages: types.messages.MessageReactionsList = await client.invoke(
                functions.messages.GetMessageReactionsList(
                    peer=chat,
                    id=message_id,
                    limit=100,
                )
            )
            for r in messages.reactions:
                if r.peer_id.user_id != client.me.id:
                    continue
                reactions.append(r.reaction)
        reactions.append(raw_reaction)
    elif add_to_existing:
        # Add nothing => leave everything as is
        return
    await client.invoke(
        functions.messages.SendReaction(
            peer=chat,
            msg_id=message_id,
            big=False,
            add_to_recent=False,
            reaction=reactions if reactions else None,
        )
    )
