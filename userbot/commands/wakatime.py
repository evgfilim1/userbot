__all__ = ["commands"]

from operator import itemgetter

from httpx import ConnectTimeout

from ..meta.modules import CommandsModule
from ..utils import WakatimeClient, Translation

commands = CommandsModule("Chat info")


def format_stats(entities, length: int = 3):
    return [
        f"{index + 1}. <b>{editor['name']}</b> - {editor['text']} ({editor['percent']}%)"
        for index, editor in enumerate(entities[:length])
    ]


@commands.add("wakatime")
async def wakatime_handler(wakatime_client: WakatimeClient, tr: Translation) -> str:
    _ = tr.gettext

    try:
        today_time = await wakatime_client.get_today_time()
        total_time, languages, editors, projects = itemgetter(
            "total_time", "languages", "editors", "projects"
        )(await wakatime_client.get_stats())
    except ConnectTimeout:
        return _("<b>Wakatime is not responding. Please, try again later</b>")

    top_languages = format_stats(languages, length=5)
    top_editors = format_stats(editors)
    top_projects = format_stats(projects)

    lines = [
        _("<b>Total time for today:</b> {today_time}").format(today_time=today_time),
        _("<b>Total time for the last week:</b> {total_time}").format(total_time=total_time),
        "",
        _("<b>Top languages:</b>"),
        *top_languages,
        "",
        _("<b>Top editors:</b>"),
        *top_editors,
        "",
        _("<b>Top projects:</b>"),
        *top_projects,
    ]

    return "\n".join(lines)
