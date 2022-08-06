__all__ = [
    "commands",
]

from datetime import datetime, time, timedelta

from pyrogram import Client
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Message
from pyrogram.utils import get_channel_id

from ..modules import CommandsModule
from ..utils import parse_delta

commands = CommandsModule("Reminders")


def _remind_common(message: Message, args_list: list[str]) -> datetime:
    """Common code for `remind` and `remind_me`"""
    now = message.edit_date or message.date or datetime.now()
    if (delta := parse_delta(args_list[0])) is not None:
        t = now + delta
    else:
        h, m = map(int, args_list[0].split(":", maxsplit=1))
        parsed_time = time(h, m)
        if parsed_time < now.time():
            t = datetime.combine(now + timedelta(days=1), parsed_time)
        else:
            t = datetime.combine(now, parsed_time)
    return t


@commands.add("remind", usage="[reply] <time> [message...]")
async def remind(client: Client, message: Message, args: str) -> str:
    """Sets a reminder"""
    args_list = args.split(" ")
    if len(args_list) >= 2:
        text = " ".join(args_list[1:])
    else:
        text = "⏰ <b>Reminder!</b>"
    t = _remind_common(message, args_list)
    await client.send_message(
        message.chat.id,
        text,
        parse_mode=ParseMode.HTML,
        reply_to_message_id=message.reply_to_message_id,
        schedule_date=t,
    )
    return f"⏰ Reminder was set for <i>{t.time()}</i>"


@commands.add("remindme", usage="[reply] <time> [message...]")
async def remind_me(client: Client, message: Message, args: str) -> str:
    """Sets a reminder for myself"""
    args_list = args.split(" ")
    if len(args_list) >= 2:
        text = " ".join(args_list[1:])
    else:
        text = "⏰ <b>Reminder!</b>"
    if message.reply_to_message_id is not None and message.chat.type == ChatType.SUPERGROUP:
        chat_id = get_channel_id(message.chat.id)
        text += f"\n\nhttps://t.me/c/{chat_id}/{message.reply_to_message_id}"
    t = _remind_common(message, args_list)
    await client.send_message(
        "me",
        text,
        parse_mode=ParseMode.HTML,
        schedule_date=t,
    )
    return f"⏰ Reminder was set for <i>{t.time()}</i>"
