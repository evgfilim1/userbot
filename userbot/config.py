from __future__ import annotations

__all__ = [
    "Config",
]

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass()
class Config:
    session: str
    api_id: int
    api_hash: str
    data_location: Path
    kwargs: dict[str, str]

    @classmethod
    def from_yaml(cls, yaml_file: str) -> Config:
        try:
            # noinspection PyPackageRequirements
            from yaml import safe_load
        except ImportError:
            raise ImportError("Install 'PyYAML~=6.0.0' to load config from YAML file") from None

        with open(yaml_file) as f:
            config = safe_load(f)
        return cls(
            session=config["session"],
            api_id=int(config["api_id"]),
            api_hash=config["api_hash"],
            data_location=Path(config.get("data_location", "data")).resolve(),
            kwargs=config.get("kwargs", {}),
        )

    @classmethod
    def from_env(cls) -> Config:
        env = os.environ
        return cls(
            session=env["SESSION"],
            api_id=int(env["API_ID"]),
            api_hash=env["API_HASH"],
            data_location=Path(env.get("DATA_LOCATION", "data")).resolve(),
            kwargs={
                key.lower().removeprefix("pyrogram_"): value
                for key, value in env.items()
                if key.startswith("PYROGRAM_")
            },
        )
