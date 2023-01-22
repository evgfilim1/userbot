__all__ = [
    "commands",
]

from datetime import datetime
from typing import NamedTuple

from pyrogram import Client
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Message
from pyrogram.utils import get_channel_id

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..utils import parse_timespec
from ..utils.translations import Translation

commands = CommandsModule("Reminders")


class _Result(NamedTuple):
    """A simple container for the result of `_remind_common`."""

    text: str
    datetime: datetime
    response: str | None


def _remind_common(
    message: Message,
    command: CommandObject,
    icons: type[Icons],
    tr: Translation,
    *,
    for_myself: bool,
    silent: bool = False,
) -> _Result:
    """Common code for reminder commands below which set a reminder in the chat"""
    _ = tr.gettext
    args = command.args
    text = args["message"]
    if text is None:
        text = _("{icon} <b>Reminder!</b>").format(icon=icons.NOTIFICATION)
    if for_myself and message.reply_to_message is not None:
        # Add a link to the replied message
        if message.chat.type == ChatType.SUPERGROUP:
            chat_id = get_channel_id(message.chat.id)
            text += f"\n\nhttps://t.me/c/{chat_id}/{message.reply_to_message_id}"
        elif message.chat.type == ChatType.PRIVATE and message.chat.username is not None:
            text += f"\n\n@{message.chat.username}"
    now = message.edit_date or message.date or datetime.now()
    t = parse_timespec(now, args["time"])
    if not silent:
        response = _(
            "{icon} Reminder {maybe_for_self}was set for <i>{t:%Y-%m-%d %H:%M:%S %Z}</i>"
        ).format(
            icon=icons.NOTIFICATION,
            t=t.astimezone(),
            maybe_for_self=(_("for myself") + " ") if for_myself else "",
        )
    else:
        response = None
    return _Result(text, t, response)


@commands.add("remind", usage="<time> [message...]")
async def remind(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: type[Icons],
    tr: Translation,
) -> str:
    """Sets a reminder in the chat

    `time` can be a time delta (e.g. "1d3h") or a time string (e.g. "12:30" or "2022-12-31_23:59").
    Message will be scheduled via Telegram's message scheduling system."""
    r = _remind_common(message, command, icons, tr, for_myself=False)
    await client.send_message(
        message.chat.id,
        r.text,
        parse_mode=ParseMode.HTML,
        reply_to_message_id=message.reply_to_message_id,
        schedule_date=r.datetime,
    )
    return r.response


@commands.add("remindme", usage="<time> [message...]")
async def remind_me(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: type[Icons],
    tr: Translation,
) -> str:
    """Sets a reminder for myself

    `time` can be a time delta (e.g. "1d3h") or a time string (e.g. "12:30" or "2022-12-31_23:59").
    Message will be scheduled via Telegram's message scheduling system."""
    r = _remind_common(message, command, icons, tr, for_myself=True)
    await client.send_message(
        "me",
        r.text,
        parse_mode=ParseMode.HTML,
        schedule_date=r.datetime,
    )
    return r.response


@commands.add("sremind", usage="<time> [message...]")
async def silent_remind(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: type[Icons],
    tr: Translation,
) -> None:
    """Sets a silent reminder in the chat (no confirmation about scheduled message)

    `time` can be a time delta (e.g. "1d3h") or a time string (e.g. "12:30" or "2022-12-31_23:59").
    Message will be scheduled via Telegram's message scheduling system."""
    r = _remind_common(message, command, icons, tr, for_myself=False, silent=True)
    await client.send_message(
        message.chat.id,
        r.text,
        parse_mode=ParseMode.HTML,
        reply_to_message_id=message.reply_to_message_id,
        schedule_date=r.datetime,
    )
    await message.delete()


@commands.add("sremindme", usage="<time> [message...]")
async def silent_remind_me(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: type[Icons],
    tr: Translation,
) -> None:
    """Sets a silent reminder for myself (no confirmation about scheduled message)

    `time` can be a time delta (e.g. "1d3h") or a time string (e.g. "12:30" or "2022-12-31_23:59").
    Message will be scheduled via Telegram's message scheduling system."""
    r = _remind_common(message, command, icons, tr, for_myself=True, silent=True)
    await client.send_message(
        "me",
        r.text,
        parse_mode=ParseMode.HTML,
        schedule_date=r.datetime,
    )
    await message.delete()
