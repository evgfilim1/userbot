__all__ = ["commands"]

from httpx import ConnectTimeout, ReadTimeout

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..utils import Translation, format_timedelta
from ..utils.clients import WakatimeClient
from ..utils.clients.wakatime import StatElement

commands = CommandsModule("Wakatime")

_EDITORS: dict[str, Icons] = {
    # TODO
}
_LANGUAGES: dict[str, Icons] = {
    # TODO
}


def _format_top(entities: list[StatElement], length: int = 3) -> list[str]:
    return [
        f"{i}. <b>{editor.name}</b>: {format_timedelta(editor.total_seconds)} ({editor.percent}%)"
        for i, editor in enumerate(entities[:length], start=1)
    ]


@commands.add("wakatime")
async def wakatime_handler(
    icons: type[Icons],
    wakatime_client: WakatimeClient | None,
    tr: Translation,
) -> str:
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
            icon=icons.WARNING
        )
    if stats is None:
        return _("{icon} Stats are refreshing, please try again in a few seconds.").format(
            icon=icons.WATCH
        )

    top_languages = _format_top(stats.languages, length=5)
    top_editors = _format_top(stats.editors)
    top_projects = _format_top(stats.projects)

    lines = [
        _("<b>Total time for today:</b> {today_time}").format(
            today_time=format_timedelta(today_time)
        ),
        _("<b>Total time for the last week:</b> {total_time}").format(
            total_time=format_timedelta(stats.total_time)
        ),
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
