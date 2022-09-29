__all__ = [
    "commands",
]

from os import getenv

from pyrogram import Client

from ..constants import DefaultIcons, PremiumIcons
from ..modules import CommandsModule

commands = CommandsModule("About")


@commands.add("about")
async def about(client: Client) -> str:
    """Shows information about this userbot"""
    base_url = "https://github.com/evgfilim1/userbot"
    # TODO (2022-07-13): get this from the git repo also
    commit = getenv("GITHUB_SHA", None)
    if client.me.is_premium:
        header_icon = PremiumIcons.INFO
        github_icon = PremiumIcons.GITHUB
        commit_icon = PremiumIcons.GIT
    else:
        header_icon = DefaultIcons.INFO
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
