__all__ = [
    "commands",
]

import asyncio
import html
from calendar import TextCalendar
from datetime import datetime
from os import getpid, kill
from signal import SIGINT
from typing import Any, NoReturn, Type

from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..translation import Translation

commands = CommandsModule("Tools")


@commands.add("id", usage="<reply>")
async def mention_with_id(message: Message) -> str:
    """Sends replied user's ID as link"""
    user = message.reply_to_message.from_user
    return f"<a href='tg://user?id={user.id}'>{user.id}</a>"


@commands.add("calc", usage="<python-expr>")
async def calc(**kwargs: Any) -> str:
    """Evaluates Python expression"""
    command: CommandObject = kwargs["command"]
    expr = command.args
    return f"<code>{html.escape(f'{expr} = {eval(expr)!r}', quote=False)}</code>"


@commands.add("cal", usage="[month] [year]")
async def calendar(message: Message, command: CommandObject) -> str:
    """Sends a calendar for a specified month and year

    If no arguments are given, the current month and year are used."""
    args_list = command.args.split()
    # It's more reliable to get current date/time from the message
    now = message.edit_date or message.date or datetime.now()
    if len(args_list) >= 1:
        month = int(args_list[0])
    else:
        month = now.month
    if len(args_list) == 2:
        year = int(args_list[1])
    else:
        year = now.year
    return f"<code>{TextCalendar().formatmonth(year, month)}</code>"


@commands.add("testerror", hidden=True)
async def test_error() -> NoReturn:
    """Always throws an error

    This is a test command to see if the error handler works."""
    raise RuntimeError("Test error")


@commands.add("sleep", usage="<seconds>", hidden=True)
async def sleep(command: CommandObject, icons: Type[Icons], tr: Translation) -> str:
    """Sleeps for a specified amount of time

    This is a test command to check the command waiting message and timeout."""
    _ = tr.gettext
    sec = float(command.args)
    await asyncio.sleep(sec)
    return _("{icon} Done sleeping for {sec} seconds").format(icon=icons.WATCH, sec=sec)


@commands.add("stopself", hidden=True)
async def stop_self(message: Message, icons: Type[Icons], tr: Translation) -> None:
    """Stops the bot

    If it's running in a production Docker container, it will be restarted automatically."""
    _ = tr.gettext
    await message.edit(_("{icon} <b>Stopping userbot...</b>").format(icon=icons.WARNING))
    kill(getpid(), SIGINT)  # Emulate pressing Ctrl-C
