__all__ = [
    "commands",
]

from pyrogram import Client
from pyrogram.raw import functions, types

from .. import __git_commit__
from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..storage import Storage
from ..utils import (
    AppLimitsController,
    DialogCount,
    StatsController,
    Translation,
    call_subprocess,
    format_timedelta,
    get_dialogs_count,
    gettext,
)

commands = CommandsModule("About")


@commands.add("about")
async def about(client: Client, tr: Translation) -> str:
    """Shows information about this userbot."""
    _ = tr.gettext
    base_url = "https://github.com/evgfilim1/userbot"
    if __git_commit__:
        commit = __git_commit__
    else:
        is_git_installed = bool(await call_subprocess("git", "--version"))
        if is_git_installed:
            commit = (await call_subprocess("git", "rev-parse", "HEAD")).stdout.decode().strip()
            is_clean = bool(await call_subprocess("git", "diff", "--quiet"))
            if not is_clean:
                commit += " " + _("(dirty)")
        else:
            commit = _("staging")
    me = await client.get_me()
    if me.is_premium:
        github_icon = Icons.GITHUB
        commit_icon = Icons.GIT
    else:
        github_icon = _("<i>Repo:</i>")
        commit_icon = _("<i>Commit:</i>")
    t = _("{icon} <b>About userbot</b>").format(icon=Icons.INFO)
    t += (
        f"\n{github_icon} <a href='{base_url}'>evgfilim1/userbot</a>"
        f"\n{commit_icon} <code>{commit}</code>"
    )
    if __git_commit__:
        t += " " + _("(<a href='{base_url}/deployments'>deployments</a>)").format(
            base_url=base_url,
        )
    t += "\n" + _("{icon} <a href='{url}'>Contribute userbot translations</a>").format(
        icon=Icons.GLOBE,
        url="https://crowdin.com/project/evgfilim1-userbot",
    )
    return t


@commands.add(
    "stats",
    usage="['bot'|'short'|'full']",
    waiting_message=gettext("<i>Collecting stats...</i>"),
    timeout=120,
)
async def stats_handler(
    client: Client,
    command: CommandObject,
    storage: Storage,
    tr: Translation,
    stats: StatsController,
    limits: AppLimitsController,
) -> str:
    """Shows some statistics about this userbot.

    If 'bot' is passed as an argument, shows userbot stats only. This is the default.
    No API calls will be made.

    If 'short' is passed as an argument, shows the stats without dialogs count.

    If 'full' is passed as an argument, shows full stats. If you have a lot of dialogs, this may
    take a while.
    """
    _ = tr.gettext

    report_type = command.args[0]
    if report_type in ("short", "full"):
        saved_gifs: types.messages.SavedGifs | None = await client.invoke(
            functions.messages.GetSavedGifs(hash=0),
        )
        saved_stickers: types.messages.AllStickers | None = await client.invoke(
            functions.messages.GetAllStickers(hash=0),
        )
        archived_stickers_count: int | None = (
            await client.invoke(
                functions.messages.GetArchivedStickers(
                    offset_id=0,
                    limit=1,
                ),
            )
        ).count
        saved_emoji: types.messages.AllStickers | None = await client.invoke(
            functions.messages.GetEmojiStickers(hash=0),
        )
        if report_type == "full":
            dialogs_count, archived_dialogs_count = await get_dialogs_count(client)
        else:
            dialogs_count: DialogCount | None = None
            archived_dialogs_count: DialogCount | None = None
    else:
        saved_gifs = None
        saved_stickers = None
        saved_emoji = None
        dialogs_count = None
        archived_dialogs_count = None
        archived_stickers_count = None

    top5 = [
        f"• {Icons.DIAGRAM} <code>{cmd}</code>: {count}"
        async for cmd, count in storage.list_command_usage(limit=5)
    ]

    lines = [
        _("<b>Statistics:</b>"),
        _("{icon} Uptime: {uptime}").format(
            icon=Icons.SETTINGS,
            uptime=format_timedelta(stats.uptime),
        ),
        _("{icon} Commands used: {count}").format(
            icon=Icons.COMMAND,
            count=await storage.get_total_command_usage(),
        ),
        *top5,
    ]
    if dialogs_count is not None and archived_dialogs_count is not None:
        lines.extend(
            (
                _("{icon} Total chats: {count}").format(
                    icon=Icons.MESSAGE,
                    count=dialogs_count.total + archived_dialogs_count.total,
                ),
                _("• {icon} Private: {count}").format(
                    icon=Icons.PRIVATE_CHAT,
                    count=dialogs_count.private,
                ),
                _("• {icon} Bots: {count}").format(
                    icon=Icons.BOT,
                    count=dialogs_count.bots,
                ),
                _("• {icon} Groups and supergroups: {count}").format(
                    icon=Icons.GROUP_CHAT,
                    count=dialogs_count.group_chats,
                ),
                _("• {icon} Channels: {count}").format(
                    icon=Icons.CHANNEL_CHAT,
                    count=dialogs_count.channels,
                ),
                _("• {icon} Archived: {count}").format(
                    icon=Icons.ARCHIVED_CHAT,
                    count=archived_dialogs_count.total,
                ),
            )
        )
    if (
        saved_gifs is not None
        and saved_stickers is not None
        and archived_stickers_count is not None
    ):
        me = await client.get_me()
        lines.extend(
            (
                _("{icon} GIFs: {count}/{total}").format(
                    icon=Icons.GIF,
                    count=len(saved_gifs.gifs),
                    total=limits.limits.saved_gifs.get(me.is_premium),
                ),
                _("{icon} Stickers: {count}/{total}").format(
                    icon=Icons.STICKER,
                    count=len(saved_stickers.sets),
                    total=limits.limits.stickers.get(me.is_premium),
                ),
                _("{icon} Archived stickers: {count}").format(
                    icon=Icons.ARCHIVED_STICKER,
                    count=archived_stickers_count,
                ),
                _("{icon} Custom emoji: {count}").format(
                    icon=Icons.EMOJI,
                    count=len(saved_emoji.sets),
                ),
            )
        )

    return "\n".join(lines)
