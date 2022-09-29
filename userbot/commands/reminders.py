__all__ = [
    "commands",
]

from datetime import datetime
from typing import Type

from pyrogram import Client
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Message
from pyrogram.utils import get_channel_id

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..utils import parse_timespec

commands = CommandsModule("Reminders")


@commands.add("remind", usage="[reply] <time> [message...]")
async def remind(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: Type[Icons],
) -> str:
    """Sets a reminder in the chat

    `time` can be a time delta (e.g. "1d3h") or a time string (e.g. "12:30" or "2022-12-31_23:59").
    Message will be scheduled via Telegram's message scheduling system."""
    args_list = command.args.split(" ")
    if len(args_list) >= 2:
        text = " ".join(args_list[1:])
    else:
        text = f"{icons.NOTIFICATION} <b>Reminder!</b>"
    now = message.edit_date or message.date or datetime.now()
    t = parse_timespec(now, args_list[0])
    await client.send_message(
        message.chat.id,
        text,
        parse_mode=ParseMode.HTML,
        reply_to_message_id=message.reply_to_message_id,
        schedule_date=t,
    )
    t = t.astimezone()
    return f"{icons.NOTIFICATION} Reminder was set for <i>{t:%Y-%m-%d %H:%M:%S %Z}</i>"


@commands.add("remindme", usage="[reply] <time> [message...]")
async def remind_me(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: Type[Icons],
) -> str:
    """Sets a reminder for myself

    `time` can be a time delta (e.g. "1d3h") or a time string (e.g. "12:30" or "2022-12-31_23:59").
    Message will be scheduled via Telegram's message scheduling system."""
    args_list = command.args.split(" ")
    if len(args_list) >= 2:
        text = " ".join(args_list[1:])
    else:
        text = f"{icons.NOTIFICATION} <b>Reminder!</b>"
    if message.reply_to_message_id is not None and message.chat.type == ChatType.SUPERGROUP:
        chat_id = get_channel_id(message.chat.id)
        text += f"\n\nhttps://t.me/c/{chat_id}/{message.reply_to_message_id}"
    now = message.edit_date or message.date or datetime.now()
    t = parse_timespec(now, args_list[0])
    await client.send_message(
        "me",
        text,
        parse_mode=ParseMode.HTML,
        schedule_date=t,
    )
    t = t.astimezone()
    return f"{icons.NOTIFICATION} Reminder for myself was set for <i>{t:%Y-%m-%d %H:%M:%S %Z}</i>"
