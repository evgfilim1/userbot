__all__ = [
    "commands",
]

from typing import Iterable

from httpx import ConnectTimeout, ReadTimeout

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..utils import Translation, format_timedelta, gettext
from ..utils.clients import WakatimeClient
from ..utils.clients.wakatime import StatElement

commands = CommandsModule("Wakatime")

_EDITORS: dict[str, Icons] = {
    "clion": Icons.EDITOR_CLION,
    "datagrip": Icons.EDITOR_DATAGRIP,
    "goland": Icons.EDITOR_GOLAND,
    "intellij": Icons.EDITOR_IDEA,
    "phpstorm": Icons.EDITOR_PHPSTORM,
    "pycharm": Icons.EDITOR_PYCHARM,
    "rider": Icons.EDITOR_RIDER,
    "sublime text": Icons.EDITOR_SUBLIME,
    "vscode": Icons.EDITOR_VSCODE,
    "vim": Icons.EDITOR_VIM,
    "webstorm": Icons.EDITOR_WEBSTORM,
}
_LANGUAGES: dict[str, Icons] = {
    "bash": Icons.LANG_BASH,
    "c": Icons.LANG_C,
    "c#": Icons.LANG_CSHARP,
    "c++": Icons.LANG_CPP,
    "dart": Icons.LANG_DART,
    "docker": Icons.LANG_DOCKER,
    "docker file": Icons.LANG_DOCKER,
    "git": Icons.LANG_GIT,
    "git config": Icons.LANG_GIT,
    "gitignore file": Icons.LANG_GIT,
    "go": Icons.LANG_GO,
    "html": Icons.LANG_HTML,
    "http request": Icons.LANG_HTTP,
    "java": Icons.LANG_JAVA,
    "javascript": Icons.LANG_JS,
    "kotlin": Icons.LANG_KOTLIN,
    "markdown": Icons.LANG_MARKDOWN,
    "nginx configuration": Icons.LANG_NGINX,
    "nginx configuration file": Icons.LANG_NGINX,
    "objectivec": Icons.LANG_OBJECTIVE_C,
    "php": Icons.LANG_PHP,
    "python": Icons.LANG_PYTHON,
    "rust": Icons.LANG_RUST,
    "shell script": Icons.LANG_BASH,
    "typescript": Icons.LANG_TYPESCRIPT,
    "vue.js": Icons.LANG_VUE,
}


def _format_top(
    entities: list[StatElement],
    icon_dict: dict[str, Icons] | None = None,
    length: int = 3,
) -> Iterable[str]:
    if icon_dict is None:
        icon_dict = {}
    for i, stat in enumerate(entities[:length], start=1):
        icon = icon_dict.get(stat.name.lower(), "")
        yield "{i}. {name}: {total_time} ({percent}%)".format(
            i=i,
            icon=icon,
            name=f"{icon}<b>{stat.name}</b>",
            total_time=format_timedelta(stat.total_seconds),
            percent=stat.percent,
        )


@commands.add("wakatime", "waka", waiting_message=gettext("Collecting Wakatime stats..."))
async def wakatime_handler(
    icons: type[Icons],
    wakatime_client: WakatimeClient | None,
    tr: Translation,
) -> str:
    """Gets your Wakatime stats for today and the last 7 days."""
    _ = tr.gettext
    if wakatime_client is None:
        return _(
            "{icon} <b>Wakatime is not configured.</b>"
            " Please set up your API key in order to use this command. See project README for more."
        ).format(icon=icons.STOP)

    try:
        today_time = await wakatime_client.get_today_time()
        stats = await wakatime_client.get_stats()
    except (ConnectTimeout, ReadTimeout):
        return _("{icon} <b>Wakatime is not responding. Please, try again later.</b>").format(
            icon=icons.WARNING,
        )
    if stats is None:
        return _("{icon} Stats are refreshing, please try again in a few seconds.").format(
            icon=icons.WATCH,
        )

    top_languages = _format_top(stats.languages, _LANGUAGES, length=5)
    top_editors = _format_top(stats.editors, _EDITORS)
    top_projects = _format_top(stats.projects)

    lines = [
        _("<b>My Wakatime stats:</b>"),
        _("• <i>Total time for today:</i> {today_time}").format(
            today_time=format_timedelta(today_time)
        ),
        _("• <i>Total time for the last 7 days:</i> {total_time}").format(
            total_time=format_timedelta(stats.total_time)
        ),
        "",
        _("• <i>Top languages:</i>"),
        *top_languages,
        "",
        _("• <i>Top editors:</i>"),
        *top_editors,
        "",
        _("• <i>Top projects:</i>"),
        *top_projects,
    ]

    return "\n".join(lines)
