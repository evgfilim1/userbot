__all__ = [
    "commands",
]

import ast
import asyncio
import html
from calendar import TextCalendar
from datetime import datetime
from os import getpid, kill
from signal import SIGINT
from typing import Any, NoReturn

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..storage import Storage
from ..utils import Translation, resolve_users

commands = CommandsModule("Tools")


@commands.add("id", reply_required=True)
async def mention_with_id(reply: Message) -> str:
    """Sends replied user's ID as link."""
    user = reply.from_user
    return f"<a href='tg://user?id={user.id}'>{user.id}</a>"


@commands.add("calc", "eval", usage="<python_expr...>")
async def calc(tr: Translation, allow_unsafe: bool, **kwargs: Any) -> str:
    """Evaluates Python expression."""
    _ = tr.gettext
    if not allow_unsafe:
        return _("{icon} Unsafe commands are disabled in the config").format(icon=Icons.STOP)
    command: CommandObject = kwargs["command"]
    expr = command.args["python_expr"]
    return f"<code>{html.escape(f'{expr} = {eval(expr)!r}', quote=False)}</code>"


@commands.add("exec", usage="<python_code...>")
async def python_exec(tr: Translation, allow_unsafe: bool, **kwargs: Any) -> str:
    """Executes Python code."""
    _ = tr.gettext
    if not allow_unsafe:
        return _("{icon} Unsafe commands are disabled in the config").format(icon=Icons.STOP)
    command: CommandObject = kwargs["command"]
    expr = command.args["python_code"] or "pass"
    ns = {"__builtins__": __builtins__}
    # Manually building AST to ignore boilerplate lines in line count while formatting an exception
    code_tree = ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__",
                names=[ast.alias(name="annotations", asname=None, lineno=0, col_offset=0)],
                level=0,
                lineno=0,
                col_offset=0,
            ),
            ast.AsyncFunctionDef(
                name="runner",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="kwargs", annotation=None, lineno=0, col_offset=0)],
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[],
                ),
                body=ast.parse(expr).body,
                decorator_list=[],
                returns=None,
                type_comment=None,
                lineno=0,
                col_offset=0,
            ),
        ],
        type_ignores=[],
    )
    code = compile(
        code_tree,
        filename="<input>",
        mode="exec",
    )
    exec(code, ns)
    answer = _("<b>Code:</b>\n<pre><code class='language-python'>{code}</code></pre>").format(
        code=html.escape(expr, quote=False)
    )
    result = _("<b>Result:</b>\n<pre><code class='language-python'>{result}</code></pre>").format(
        result=html.escape(repr(await ns["runner"](kwargs)), quote=False)
    )
    return f"{answer}\n\n{result}"


@commands.add("cal", usage="[month] [year]")
async def calendar(message: Message, command: CommandObject) -> str:
    """Sends a calendar for a specified month and year.

    If no arguments are given, the current month and year are used.
    """
    args = command.args
    # It's more reliable to get current date/time from the message
    now = message.edit_date or message.date or datetime.now()
    if args["month"] is not None:
        month = int(args[0])
    else:
        month = now.month
    if args["year"] is not None:
        year = int(args[1])
    else:
        year = now.year
    return f"<pre><code>{TextCalendar().formatmonth(year, month)}</code></pre>"


@commands.add("testerror", hidden=True)
async def test_error() -> NoReturn:
    """Always throws an error.

    This is a test command to see if the error handler works."""
    raise RuntimeError("Test error")


@commands.add("sleep", usage="<seconds>", hidden=True)
async def sleep(command: CommandObject, tr: Translation) -> str:
    """Sleeps for a specified amount of time.

    This is a test command to check the command waiting message and timeout.
    """
    _ = tr.gettext
    sec = float(command.args["seconds"])
    await asyncio.sleep(sec)
    return _("{icon} Done sleeping for {sec} seconds").format(icon=Icons.WATCH, sec=sec)


@commands.add("stopself", hidden=True)
async def stop_self(message: Message, tr: Translation) -> None:
    """Stops the bot.

    This effectively works like pressing Ctrl-C in the terminal.

    This command is useful to restart the bot if it's running in a Docker container or under
    a process manager like systemd and is configured to restart unless manually stopped, which is
    the default behavior for production docker-compose config in this repo.
    """
    _ = tr.gettext
    await message.edit(_("{icon} <b>Stopping userbot...</b>").format(icon=Icons.WARNING))
    kill(getpid(), SIGINT)


@commands.add("ugping", usage="<user_group> [text...]")
async def ping_user_group(
    client: Client,
    message: Message,
    command: CommandObject,
    storage: Storage,
    tr: Translation,
) -> None:
    """Pings a user group with optional text."""
    _ = tr.gettext
    user_group = command.args["user_group"]
    text = command.args["text"]
    res = ""
    users = list(await resolve_users(client, storage, user_group))  # Pyrogram doesn't like sets
    if len(users) == 0:
        return _("{icon} No users in <code>{user_group}</code>").format(
            icon=Icons.WARNING,
            user_group=user_group,
        )
    for user in await client.get_users(users):
        if user.username is not None:
            res += f"@{user.username}"
        else:
            res += f"{user.mention(style=ParseMode.HTML)}"
        res += " "
    if text is not None:
        res += text
    await client.send_message(
        chat_id=message.chat.id,
        text=res,
        parse_mode=ParseMode.HTML,
        reply_to_message_id=message.reply_to_message_id,
    )
    await message.delete()
