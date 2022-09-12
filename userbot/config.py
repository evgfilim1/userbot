from __future__ import annotations

__all__ = [
    "Config",
    "RedisConfig",
]

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass()
class RedisConfig:
    host: str
    port: int = 6379
    db: int = 0
    password: str | None = None

    @classmethod
    def from_env(cls) -> RedisConfig:
        env = os.environ
        return cls(
            host=env["REDIS_HOST"],
            port=int(env.get("REDIS_PORT", cls.port)),
            db=int(env.get("REDIS_DB", cls.db)),
            password=env.get("REDIS_PASSWORD", None),
        )


@dataclass()
class Config:
    session: str
    api_id: int
    api_hash: str
    data_location: Path
    kwargs: dict[str, str]

    @classmethod
    def from_env(cls) -> Config:
        env = os.environ
        return cls(
            session=env["SESSION"],
            api_id=int(env["API_ID"]),
            api_hash=env["API_HASH"],
            data_location=Path(env.get("DATA_LOCATION", ".dockerdata/userbot")).resolve(),
            kwargs={
                key.lower().removeprefix("pyrogram_"): value
                for key, value in env.items()
                if key.startswith("PYROGRAM_")
            },
        )
