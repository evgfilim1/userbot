__all__ = [
    "commands",
]

from os import getenv

from pyrogram import Client

from ..constants import DefaultIcons, PremiumIcons
from ..modules import CommandsModule
from ..translation import Translation

commands = CommandsModule("About")


@commands.add("about")
async def about(client: Client, tr: Translation) -> str:
    """Shows information about this userbot"""
    _ = tr.gettext
    base_url = "https://github.com/evgfilim1/userbot"
    # TODO (2022-07-13): get this from the git repo also
    commit = getenv("GITHUB_SHA", None)
    if client.me.is_premium:
        header_icon = PremiumIcons.INFO
        github_icon = PremiumIcons.GITHUB
        commit_icon = PremiumIcons.GIT
    else:
        header_icon = DefaultIcons.INFO
        github_icon = _("<i>Repo:</i>")
        commit_icon = _("<i>Commit:</i>")
    t = _("{header_icon} <b>About userbot</b>\n").format(header_icon=header_icon)
    t += (
        f"{github_icon} <a href='{base_url}'>evgfilim1/userbot</a>\n"
        f"{commit_icon} <code>{commit or 'staging'}</code>"
    )
    if commit:
        t += _(" (<a href='{base_url}/deployments'>deployments</a>)").format(
            base_url=base_url,
        )
    return t
