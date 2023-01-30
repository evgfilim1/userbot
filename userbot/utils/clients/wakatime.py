__all__ = [
    "WakatimeClient",
]

from base64 import b64encode
from datetime import datetime
from math import floor

from .base import BaseClient


def format_time(seconds: int) -> str:
    if seconds < 60:
        return "no coding stats for today"

    hours = int(seconds // 3600)
    minutes = int((seconds - hours * 3600) // 60)

    return "{0}{1}".format(f"{hours}h" if hours > 0 else "", f" {minutes}m" if minutes > 0 else "")


class WakatimeClient(BaseClient, base_url="https://wakatime.com/api/v1/"):
    def __init__(self, token: str):
        super().__init__()
        self._client.headers = {"Authorization": f"Basic {b64encode(token.encode()).decode()}"}

    @staticmethod
    def __process_stats_entity(entities) -> list[dict]:
        return [
            {"name": entity["name"], "text": entity["text"], "percent": entity["percent"]}
            for entity in entities
        ]

    async def get_today_time(self) -> str:
        date = datetime.today().strftime("%Y-%m-%d")

        response: dict = (
            await self._client.get(
                "/users/current/durations",
                params={"date": date},
            )
        ).json()

        return format_time(sum([floor(project["duration"]) for project in response["data"]]))

    async def get_stats(self) -> dict:
        response: dict = (await self._client.get("/users/current/stats/last_7_days")).json()["data"]

        total_time = format_time(response["total_seconds"])
        languages = self.__process_stats_entity(response["languages"])
        editors = self.__process_stats_entity(response["editors"])
        projects = self.__process_stats_entity(response["projects"])

        result = {
            "total_time": total_time,
            "languages": languages,
            "editors": editors,
            "projects": projects,
        }

        return result
