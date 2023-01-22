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

from pyrogram.types import Message

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..utils import Translation

commands = CommandsModule("Tools")


@commands.add("id", reply_required=True)
async def mention_with_id(reply: Message) -> str:
    """Sends replied user's ID as link"""
    user = reply.from_user
    return f"<a href='tg://user?id={user.id}'>{user.id}</a>"


@commands.add("calc", "eval", usage="<python_expr...>")
async def calc(tr: Translation, allow_unsafe: bool, **kwargs: Any) -> str:
    """Evaluates Python expression"""
    _ = tr.gettext
    if not allow_unsafe:
        return _("{icon} Unsafe commands are disabled in the config").format(icon=Icons.STOP)
    command: CommandObject = kwargs["command"]
    expr = command.args["python_expr"]
    return f"<code>{html.escape(f'{expr} = {eval(expr)!r}', quote=False)}</code>"


@commands.add("exec", usage="<python_code...>")
async def python_exec(tr: Translation, allow_unsafe: bool, **kwargs: Any) -> str:
    """Executes Python expression"""
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
    """Sends a calendar for a specified month and year

    If no arguments are given, the current month and year are used."""
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
    """Always throws an error

    This is a test command to see if the error handler works."""
    raise RuntimeError("Test error")


@commands.add("sleep", usage="<seconds>", hidden=True)
async def sleep(command: CommandObject, icons: type[Icons], tr: Translation) -> str:
    """Sleeps for a specified amount of time

    This is a test command to check the command waiting message and timeout."""
    _ = tr.gettext
    sec = float(command.args["seconds"])
    await asyncio.sleep(sec)
    return _("{icon} Done sleeping for {sec} seconds").format(icon=icons.WATCH, sec=sec)


@commands.add("stopself", hidden=True)
async def stop_self(message: Message, icons: type[Icons], tr: Translation) -> None:
    """Stops the bot

    If it's running in a production Docker container, it will be restarted automatically."""
    _ = tr.gettext
    await message.edit(_("{icon} <b>Stopping userbot...</b>").format(icon=icons.WARNING))
    kill(getpid(), SIGINT)  # Emulate pressing Ctrl-C
