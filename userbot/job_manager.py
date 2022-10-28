from __future__ import annotations

__all__ = [
    "AsyncJobManager",
]

from asyncio import Task, create_task
from types import TracebackType
from typing import Any, Coroutine, Self, Type


class AsyncJobManager:
    def __init__(self) -> None:
        self._jobs: list[Task] = []

    def add_job(self, coro: Coroutine[None, None, Any]) -> Task:
        job = create_task(coro)
        self._jobs.append(job)
        return job

    def cancel_all(self) -> None:
        for job in self._jobs:
            job.cancel()
        self._jobs.clear()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.cancel_all()
