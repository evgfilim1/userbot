from __future__ import annotations

__all__ = [
    "Config",
    "RedisConfig",
]

import os
from dataclasses import dataclass
from pathlib import Path

from .utils import SecretStr


@dataclass()
class RedisConfig:
    host: str
    port: int = 6379
    db: int = 0
    password: SecretStr | None = None

    @classmethod
    def from_env(cls) -> RedisConfig:
        env = os.environ
        password = env.get("REDIS_PASSWORD", None)
        return cls(
            host=env["REDIS_HOST"],
            port=int(env.get("REDIS_PORT", cls.port)),
            db=int(env.get("REDIS_DB", cls.db)),
            password=None if password is None else SecretStr(password),
        )


@dataclass()
class Config:
    session: str
    api_id: int
    api_hash: SecretStr
    data_location: Path
    media_notes_chat: int | str
    kwargs: dict[str, SecretStr]

    @classmethod
    def from_env(cls) -> Config:
        env = os.environ
        return cls(
            session=env["SESSION"],
            api_id=int(env["API_ID"]),
            api_hash=SecretStr(env["API_HASH"]),
            data_location=Path(env.get("DATA_LOCATION", ".dockerdata/userbot")).resolve(),
            media_notes_chat=env.get("MEDIA_NOTES_CHAT", "self"),
            kwargs={
                key.lower().removeprefix("pyrogram_"): SecretStr(value)
                for key, value in env.items()
                if key.startswith("PYROGRAM_")
            },
        )
