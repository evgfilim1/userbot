__all__ = [
    "commands",
]

from os import getenv
from typing import Type

from pyrogram import Client

from .. import __is_prod__
from ..constants import Icons, PremiumIcons
from ..modules import CommandsModule
from ..translation import Translation

commands = CommandsModule("About")


@commands.add("about")
async def about(client: Client, icons: Type[Icons], tr: Translation) -> str:
    """Shows information about this userbot"""
    _ = tr.gettext
    base_url = "https://github.com/evgfilim1/userbot"
    # TODO (2022-07-13): get this from the git repo also
    commit = getenv("GITHUB_SHA", _("staging"))
    if client.me.is_premium:
        github_icon = PremiumIcons.GITHUB
        commit_icon = PremiumIcons.GIT
    else:
        github_icon = _("<i>Repo:</i>")
        commit_icon = _("<i>Commit:</i>")
    t = _("{icon} <b>About userbot</b>\n").format(icon=icons.INFO)
    t += (
        f"{github_icon} <a href='{base_url}'>evgfilim1/userbot</a>\n"
        f"{commit_icon} <code>{commit}</code>"
    )
    if __is_prod__:
        t += _(" (<a href='{base_url}/deployments'>deployments</a>)").format(
            base_url=base_url,
        )
    t += _("\n{icon} <a href='{url}'>Contribute userbot translations</a>").format(
        icon=icons.GLOBE,
        url="https://crowdin.com/project/evgfilim1-userbot",
    )
    return t
