__all__ = [
    "commands",
]

import html
from calendar import TextCalendar
from datetime import datetime

from pyrogram import Client
from pyrogram.types import Message

from ..modules import CommandsModule

commands = CommandsModule()


@commands.add("id", usage="<reply>")
async def mention_with_id(_: Client, message: Message, __: str) -> str:
    """Sends replied user's ID as link"""
    user = message.reply_to_message.from_user
    return f"<a href='tg://user?id={user.id}'>{user.id}</a>"


@commands.add("calc", usage="<python-expr>")
async def calc(_: Client, __: Message, args: str) -> str:
    """Evaluates Python expression"""
    result = html.escape(f"{args} = {eval(args)!r}", quote=False)
    return f"<code>{result}</code>"


@commands.add("cal", usage="[month] [year]")
async def calendar(_: Client, message: Message, args: str) -> str:
    """Sends a calendar for a specified month and year"""
    args_list = args.split()
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


@commands.add("testerror")
async def test_error(_: Client, __: Message, ___: str) -> None:
    """Always throws an error"""
    raise RuntimeError("Test error")
