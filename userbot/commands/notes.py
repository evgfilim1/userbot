import json

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

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
    if not (key := command.args):
        return "❗ No name specified"
    data = await storage.get_message(key)
    if data is None:
        return f"❓ Message with key={key!r} not found"
    content, type_ = json.loads(data[0]), data[1]
    if "caption" in content or "text" in content:
        content["parse_mode"] = ParseMode.HTML
    await getattr(client, f"send_{type_}")(
        message.chat.id,
        **content,
        reply_to_message_id=message.reply_to_message_id,
    )
    await message.delete()


@commands.add(["save", "note_add", "nadd"], usage="<reply> <name>")
async def save_message(
    _: Client,
    message: Message,
    command: CommandObject,
    *,
    storage: Storage,
) -> str:
    """Saves replied message for later use"""
    if not (key := command.args):
        return f"❓ Please specify message key\n\nPossible fix: <code>{message.text} key</code>"
    content, type_ = get_message_content(message.reply_to_message)
    await storage.save_message(key, json.dumps(content), type_)
    return f"💾 Message <code>{key}</code> saved"


@commands.add(["saved", "notes", "ns"])
async def saved_messages(_: Client, __: Message, ___: CommandObject, *, storage: Storage) -> str:
    """Shows all saved messages"""
    t = ""
    async for key in storage.saved_messages():
        _, type_ = await storage.get_message(key)
        t += f"• <code>{key}</code> ({type_})\n"
    return f"<b>Saved messages:</b>\n{t}"


@commands.add(["note_del", "ndel"], usage="<name>")
async def delete_message(
    _: Client,
    message: Message,
    command: CommandObject,
    *,
    storage: Storage,
) -> str:
    """Deletes saved message"""
    if not (key := command.args):
        return f"❓ Please specify message key\n\nPossible fix: <code>{message.text} key</code>"
    await storage.delete_message(key)
    return f"🗑 Message <code>{key}</code> deleted"
