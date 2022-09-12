__all__ = [
    "commands",
]

import asyncio
import html
from calendar import TextCalendar
from datetime import datetime
from typing import NoReturn

from pyrogram import Client
from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule

commands = CommandsModule("Tools")


@commands.add("id", usage="<reply>")
async def mention_with_id(_: Client, message: Message, __: CommandObject) -> str:
    """Sends replied user's ID as link"""
    user = message.reply_to_message.from_user
    return f"<a href='tg://user?id={user.id}'>{user.id}</a>"


@commands.add("calc", usage="<python-expr>")
async def calc(_: Client, __: Message, command: CommandObject) -> str:
    """Evaluates Python expression"""
    expr = command.args
    return f"<code>{html.escape(f'{expr} = {eval(expr)!r}', quote=False)}</code>"


@commands.add("cal", usage="[month] [year]")
async def calendar(_: Client, message: Message, command: CommandObject) -> str:
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
async def test_error(_: Client, __: Message, ___: CommandObject) -> NoReturn:
    """Always throws an error

    This is a test command to see if the error handler works."""
    raise RuntimeError("Test error")


@commands.add("sleep", usage="<seconds>", hidden=True)
async def sleep(client: Client, _: Message, command: CommandObject) -> str:
    """Sleeps for a specified amount of time

    This is a test command to check the command waiting message and timeout."""
    sec = float(command.args)
    await asyncio.sleep(sec)
    return f"{Icons.WATCH.get_icon(client.me.is_premium)} Done sleeping for {sec} seconds"
