from __future__ import annotations

__all__ = [
    "AppConfig",
    "RedisConfig",
    "StorageConfig",
    "TelegramConfig",
    "ThirdPartyServicesConfig",
    "TypeCastError",
]

import enum
import inspect
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar, Union, get_type_hints, overload

from pyrogram import Client

from .utils import SecretValue, Unset

_T = TypeVar("_T")

_TRUTHY_VALUES = frozenset(("1", "true", "yes"))
_FALSY_VALUES = frozenset(("0", "false", "no", ""))
_UNION_TYPES = (type(int | str), type(Union[int, str]))
_SECRETS = frozenset(("phone_number", "password", "session_string"))


class TypeCastError(ValueError):
    def __init__(self, value: Any, type_: type[Any], *, arg_name: str | None = None) -> None:
        if arg_name is not None:
            super().__init__(f"Invalid {type!r} value for {arg_name!r}: {value!r}")
        else:
            super().__init__(f"Invalid {type_!r} value: {value!r}")


def _cast_value(value: str, type_: type[_T], *, arg_name: str | None = None) -> _T:
    if type_ is str:
        return value
    if type_ is bool:
        if value.lower() not in _TRUTHY_VALUES | _FALSY_VALUES:
            raise TypeCastError(value, type_, arg_name=arg_name)
        return value.lower() in _TRUTHY_VALUES
    if type_ is int or type_ is float:
        try:
            return type_(value)
        except ValueError:
            raise TypeCastError(value, type_, arg_name=arg_name) from None
    if issubclass(type_, enum.Enum):
        try:
            return type_(value)
        except ValueError:
            try:
                return type_[value]
            except KeyError:
                raise TypeCastError(value, type_, arg_name=arg_name) from None
    if isinstance(type_, _UNION_TYPES):
        for t in type_.__args__:
            try:
                return _cast_value(value, t)
            except TypeCastError:
                continue
        raise TypeCastError(value, type_, arg_name=arg_name)
    if arg_name is not None:
        raise NotImplementedError(f"Type {type_!r} for {arg_name!r} is not supported")
    raise NotImplementedError(f"Type {type_!r} is not supported")


def _parse_pyrogram_kwargs(raw_kwargs: dict[str, str]) -> dict[str, Any]:
    signature = inspect.signature(Client)
    type_hints = get_type_hints(Client.__init__)
    kwargs = {}
    unset = Unset()
    for key, value in raw_kwargs.items():
        arg_name = key.lower().removeprefix("pyrogram_")
        arg = signature.parameters.get(arg_name, unset)
        if arg is unset:
            raise TypeError(f"Unexpected keyword argument for `pyrogram.Client` class: {key!r}")
        type_ = type_hints.get(arg_name, unset)
        if type_ is unset:
            raise AssertionError(
                f"No type hint found for `pyrogram.Client` constructor argument {arg_name!r}"
            )
        casted_value = _cast_value(value, type_, arg_name=key)
        if arg_name in _SECRETS:
            casted_value = SecretValue(casted_value)
        kwargs[arg_name] = casted_value
    return kwargs


@overload
def _get_env_value(key: str, type_: type[_T] = str, *, default: _T | Unset = Unset()) -> _T:
    pass


@overload
def _get_env_value(key: str, type_: type[_T], *, default: None) -> _T | None:
    pass


def _get_env_value(
    key: str,
    type_: type[_T] = str,
    *,
    default: _T | None | Unset = Unset(),
) -> _T | None:
    unset = Unset()
    value = os.environ.get(key, unset)
    if value is unset:
        if default is unset:
            raise ValueError(f"Required environment variable {key!r} is not set")
        return default
    return _cast_value(value, type_, arg_name=key)


@dataclass()
class TelegramConfig:
    api_id: int
    api_hash: SecretValue[str]
    pyrogram_kwargs: dict[str, Any]

    @classmethod
    def from_env(cls) -> TelegramConfig:
        """Load TelegramConfig from environment variables."""
        return cls(
            api_id=_get_env_value("API_ID", int),
            api_hash=SecretValue(_get_env_value("API_HASH")),
            pyrogram_kwargs=_parse_pyrogram_kwargs(
                {key: value for key, value in os.environ.items() if key.startswith("PYROGRAM_")},
            ),
        )


@dataclass()
class StorageConfig:
    session_name: str
    data_location: Path

    def __post_init__(self) -> None:
        resolved_data_location = self.data_location.resolve()
        # non-existent data location is ok, it will be created later
        if resolved_data_location.exists() and not resolved_data_location.is_dir():
            raise NotADirectoryError(
                f"Data location must be a directory: {str(resolved_data_location)!r}",
            )
        self.data_location = resolved_data_location

    @classmethod
    def from_env(cls) -> StorageConfig:
        """Load StorageConfig from environment variables."""
        return cls(
            session_name=_get_env_value("SESSION"),
            data_location=Path(_get_env_value("DATA_LOCATION", default="/data")),
        )


@dataclass()
class RedisConfig:
    host: str
    port: int = 6379
    db: int = 0
    password: SecretValue[str] | None = None

    @classmethod
    def from_env(cls) -> RedisConfig:
        """Load RedisConfig from environment variables."""
        password = _get_env_value("REDIS_PASSWORD", default=None)
        return cls(
            host=_get_env_value("REDIS_HOST"),
            port=_get_env_value("REDIS_PORT", int, default=cls.port),
            db=_get_env_value("REDIS_DB", int, default=cls.db),
            password=None if password is None else SecretValue(password),
        )


@dataclass()
class AppConfig:
    command_prefix: str
    log_level: str
    media_notes_chat: int | str
    tracebacks_chat: int | str | None
    allow_unsafe_commands: bool

    def __post_init__(self) -> None:
        if len(self.command_prefix) != 1:
            raise ValueError("`command_prefix` must be a single character")

    @classmethod
    def from_env(cls) -> AppConfig:
        """Load AppConfig from environment variables."""
        return cls(
            command_prefix=_get_env_value("COMMAND_PREFIX", default=","),
            log_level=_get_env_value("LOG_LEVEL", default="INFO").upper(),
            media_notes_chat=_get_env_value("MEDIA_NOTES_CHAT", default="self"),
            tracebacks_chat=_get_env_value("TRACEBACK_CHAT", default=None),
            allow_unsafe_commands=_get_env_value("ALLOW_UNSAFE_COMMANDS", bool, default=True),
        )


@dataclass()
class ThirdPartyServicesConfig:
    ...

    @classmethod
    def from_env(cls) -> ThirdPartyServicesConfig:
        """Load ThirdPartyServicesConfig from environment variables."""
        # stub for future use
        return cls()
