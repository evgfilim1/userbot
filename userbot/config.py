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
        """Create a RedisConfig by loading environment variables"""
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
    command_prefix: str
    log_level: str
    traceback_chat: int | str | None
    kwargs: dict[str, SecretStr]
    allow_unsafe_commands: bool

    @classmethod
    def from_env(cls) -> Config:
        """Creates config by loading environment variables"""
        env = os.environ
        return cls(
            session=env["SESSION"],
            api_id=int(env["API_ID"]),
            api_hash=SecretStr(env["API_HASH"]),
            data_location=Path(env.get("DATA_LOCATION", "/data")).resolve(),
            media_notes_chat=env.get("MEDIA_NOTES_CHAT", "self"),
            command_prefix=env.get("COMMAND_PREFIX", ","),
            log_level=env.get("LOG_LEVEL", "INFO").upper(),
            traceback_chat=env.get("TRACEBACK_CHAT", None),
            kwargs={
                key.lower().removeprefix("pyrogram_"): SecretStr(value)
                for key, value in env.items()
                if key.startswith("PYROGRAM_")
            },
            allow_unsafe_commands=env.get("ALLOW_UNSAFE_COMMANDS", "1") != "0",
        )

    def __post_init__(self) -> None:
        """Validates config"""
        if len(self.command_prefix) != 1:
            raise ValueError("`command_prefix` must be a single character")
        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError("`log_level` must be one of (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
