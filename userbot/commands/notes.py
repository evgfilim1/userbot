import json

from pyrogram import Client
from pyrogram.enums import MessageMediaType, ParseMode
from pyrogram.errors import FileReferenceExpired
from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..storage import Storage
from ..utils import get_message_content

commands = CommandsModule("Notes")


@commands.add(["get", "note", "n"], usage="<name>")
async def get_message(
    client: Client,
    message: Message,
    command: CommandObject,
    *,
    storage: Storage,
) -> str | None:
    """Sends saved message"""
    warning_icon = Icons.WARNING.get_icon(client.me.is_premium)
    if not (key := command.args):
        return f"{warning_icon} No name specified"
    data = await storage.get_message(key)
    if data is None:
        return f"{warning_icon} Message with key={key!r} not found"
    content, type_ = json.loads(data[0]), data[1]
    if "caption" in content or "text" in content:
        content["parse_mode"] = ParseMode.HTML
    if type_ == "text":
        return content["text"]
    if "message_id" not in content:
        # Backwards compatibility + support for stickers
        try:
            await getattr(client, f"send_{type_}")(
                message.chat.id,
                **content,
                reply_to_message_id=message.reply_to_message_id,
            )
        except FileReferenceExpired:
            return (
                f"{warning_icon} <b>File reference expired, please save the note again.</b>\n"
                f"<i>Note key:</i> <code>{key}</code>"
            )
    else:
        await client.copy_message(
            message.chat.id,
            **content,
            reply_to_message_id=message.reply_to_message_id,
        )
    await message.delete()


@commands.add(["save", "note_add", "nadd"], usage="<reply> <name>")
async def save_message(
    client: Client,
    message: Message,
    command: CommandObject,
    *,
    storage: Storage,
    notes_chat: int | str,
) -> str:
    """Saves replied message for later use"""
    if not (key := command.args):
        icon = Icons.QUESTION.get_icon(client.me.is_premium)
        return f"{icon} Please specify message key\n\nPossible fix: <code>{message.text} key</code>"
    target = message.reply_to_message
    if target.media not in (MessageMediaType.STICKER, None):
        # Stickers and text messages can be saved without problems, other media types should be
        # saved in a chat to be able to send them later even when the original message is deleted.
        target = await target.copy(notes_chat)
    content, type_ = get_message_content(target)
    await storage.save_message(key, json.dumps(content), type_)
    return f"{Icons.BOOKMARK.get_icon(client.me.is_premium)} Message <code>{key}</code> saved"


@commands.add(["saved", "notes", "ns"])
async def saved_messages(client: Client, _: Message, __: CommandObject, *, storage: Storage) -> str:
    """Shows all saved messages"""
    t = ""
    async for key in storage.saved_messages():
        _, type_ = await storage.get_message(key)
        t += f"• <code>{key}</code> ({type_})\n"
    return f"{Icons.BOOKMARK.get_icon(client.me.is_premium)} <b>Saved messages:</b>\n{t}"


@commands.add(["note_del", "ndel"], usage="<name>")
async def delete_message(
    client: Client,
    message: Message,
    command: CommandObject,
    *,
    storage: Storage,
) -> str:
    """Deletes saved message"""
    if not (key := command.args):
        icon = Icons.QUESTION.get_icon(client.me.is_premium)
        return f"{icon} Please specify message key\n\nPossible fix: <code>{message.text} key</code>"
    await storage.delete_message(key)
    return f"{Icons.TRASH.get_icon(client.me.is_premium)} Message <code>{key}</code> deleted"
