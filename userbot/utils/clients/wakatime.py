from __future__ import annotations

__all__ = [
    "StatElement",
    "WakatimeStats",
    "WakatimeClient",
]

import logging
from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict

from .base import BaseClient

_log = logging.getLogger(__name__)


class _StatElementDict(TypedDict):
    name: str
    text: str
    percent: float
    total_seconds: float


@dataclass()
class StatElement:
    name: str
    text: str
    percent: float
    total_seconds: float

    @classmethod
    def from_dict(cls, data: _StatElementDict) -> StatElement:
        return cls(
            name=data["name"],
            text=data["text"],
            percent=data["percent"],
            total_seconds=data["total_seconds"],
        )


@dataclass()
class WakatimeStats:
    total_time: float
    languages: list[StatElement]
    editors: list[StatElement]
    projects: list[StatElement]


class WakatimeClient(BaseClient, base_url="https://wakatime.com/api/v1/"):
    def __init__(self, token: str):
        super().__init__()
        self._client.headers = {"Authorization": f"Basic {b64encode(token.encode()).decode()}"}

    async def get_today_time(self) -> float:
        date = datetime.today().strftime("%Y-%m-%d")

        response: dict[str, Any] = (
            await self._client.get(
                "/users/current/durations",
                params={"date": date},
            )
        ).json()

        return sum(project["duration"] for project in response["data"])

    async def get_stats(self) -> WakatimeStats | None:
        response = await self._client.get("/users/current/stats/last_7_days")
        response_json = response.json()
        _log.debug("get_stats got %r", response_json)
        if response.status_code == 202:
            return None
        response.raise_for_status()

        data = response_json["data"]
        total_time = data["total_seconds"]
        languages = [StatElement.from_dict(x) for x in data["languages"]]
        editors = [StatElement.from_dict(x) for x in data["editors"]]
        projects = [StatElement.from_dict(x) for x in data["projects"]]

        return WakatimeStats(
            total_time=total_time,
            languages=languages,
            editors=editors,
            projects=projects,
        )
