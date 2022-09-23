__all__ = [
    "commands",
]

from datetime import datetime, time, timedelta

from pyrogram import Client
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Message
from pyrogram.utils import get_channel_id

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..utils import parse_delta

commands = CommandsModule("Reminders")


def _remind_common(message: Message, args_list: list[str]) -> datetime:
    """Common code for `remind` and `remindme`"""
    now = message.edit_date or message.date or datetime.now()
    if (delta := parse_delta(args_list[0])) is not None:
        result = now + delta
    else:
        dt = args_list[0].split("_", maxsplit=1)
        if len(dt) == 2:
            date = datetime.strptime(dt[0], "%Y-%m-%d").date()
            time_string = dt[1]
        else:
            date = now.date()
            time_string = dt[0]
        h, m = map(int, time_string.split(":", maxsplit=1))
        parsed_time = time(h, m)
        if parsed_time < now.time() and len(dt) == 1:
            result = datetime.combine(now + timedelta(days=1), parsed_time)
        else:
            result = datetime.combine(date, parsed_time)
    return result


@commands.add("remind", usage="[reply] <time> [message...]")
async def remind(client: Client, message: Message, command: CommandObject) -> str:
    """Sets a reminder in the chat

    `time` can be a time delta (e.g. "1d3h") or a time string (e.g. "12:30" or "2022-12-31_23:59").
    Message will be scheduled via Telegram's message scheduling system."""
    args_list = command.args.split(" ")
    reminder_icon = Icons.NOTIFICATION.get_icon(client.me.is_premium)
    if len(args_list) >= 2:
        text = " ".join(args_list[1:])
    else:
        text = f"{reminder_icon} <b>Reminder!</b>"
    t = _remind_common(message, args_list)
    await client.send_message(
        message.chat.id,
        text,
        parse_mode=ParseMode.HTML,
        reply_to_message_id=message.reply_to_message_id,
        schedule_date=t,
    )
    t = t.astimezone()
    return f"{reminder_icon} Reminder was set for <i>{t:%Y-%m-%d %H:%M:%S %Z}</i>"


@commands.add("remindme", usage="[reply] <time> [message...]")
async def remind_me(client: Client, message: Message, command: CommandObject) -> str:
    """Sets a reminder for myself

    `time` can be a time delta (e.g. "1d3h") or a time string (e.g. "12:30" or "2022-12-31_23:59").
    Message will be scheduled via Telegram's message scheduling system."""
    args_list = command.args.split(" ")
    reminder_icon = Icons.NOTIFICATION.get_icon(client.me.is_premium)
    if len(args_list) >= 2:
        text = " ".join(args_list[1:])
    else:
        text = f"{reminder_icon} <b>Reminder!</b>"
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
    t = t.astimezone()
    return f"{reminder_icon} Reminder for myself was set for <i>{t:%Y-%m-%d %H:%M:%S %Z}</i>"
