__all__ = [
    "commands",
]

from os import getenv

from pyrogram import Client
from pyrogram.types import Message

from ..modules import CommandObject, CommandsModule

commands = CommandsModule("About")


@commands.add("about")
async def about(_: Client, __: Message, ___: CommandObject) -> str:
    """Shows information about this userbot"""
    base_url = "https://github.com/evgfilim1/userbot"
    commit = getenv("GITHUB_SHA", None)
    # Maybe get this from the git repo, but there's no need for it now
    t = (
        f"ℹ️ <b>About userbot</b>\n"
        f"<i>Repo:</i> <a href='{base_url}'>evgfilim1/userbot</a>\n"
        f"<i>Commit:</i> <code>{commit or 'staging'}</code>"
    )
    if commit:
        t += f" (<a href='{base_url}/deployments'>deployments</a>)"
    return t
