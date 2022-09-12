__all__ = [
    "commands",
]

from os import getenv

from pyrogram import Client
from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule

commands = CommandsModule("About")


@commands.add("about")
async def about(client: Client, __: Message, ___: CommandObject) -> str:
    """Shows information about this userbot"""
    base_url = "https://github.com/evgfilim1/userbot"
    commit = getenv("GITHUB_SHA", None)
    # Maybe get this from the git repo, but there's no need for it now
    if client.me.is_premium:
        header_icon = Icons.INFO.premium_icon
        github_icon = Icons.GITHUB.premium_icon
        commit_icon = Icons.GIT.premium_icon
    else:
        header_icon = Icons.INFO.icon
        github_icon = "<i>Repo:</i>"
        commit_icon = "<i>Commit:</i>"
    t = (
        f"{header_icon} <b>About userbot</b>\n"
        f"{github_icon} <a href='{base_url}'>evgfilim1/userbot</a>\n"
        f"{commit_icon} <code>{commit or 'staging'}</code>"
    )
    if commit:
        t += f" (<a href='{base_url}/deployments'>deployments</a>)"
    return t
