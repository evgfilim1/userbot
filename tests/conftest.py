from __future__ import annotations

import asyncio
import os
import random

import pytest
import pytest_asyncio
from pyrogram import Client

from userbot import __version__
from userbot.config import Config, RedisConfig


@pytest.fixture(scope="session")
def config() -> Config:
    os.environ.setdefault("SESSION", "test")
    # https://github.com/telegramdesktop/tdesktop/blob/a4b0443/Telegram/cmake/telegram_options.cmake#L15-L18
    os.environ.setdefault("API_ID", "17349")
    os.environ.setdefault("API_HASH", "344583e45741c457fe1862106095a5eb")

    config = Config.from_env()

    config.kwargs.setdefault("test_mode", "1")
    config.kwargs.setdefault("in_memory", "1")
    if config.kwargs.get("phone_number", None) is None:
        dc_n = str(random.randint(1, 3))
        random_n = f"{random.randint(0, 9999):4d}"
        # https://docs.pyrogram.org/topics/test-servers#test-numbers
        config.kwargs["phone_number"] = f"99966{dc_n}{random_n}"
        config.kwargs["phone_code"] = dc_n * 5

    return config


@pytest.fixture(scope="session")
def redis_config() -> RedisConfig:
    os.environ.setdefault("REDIS_HOST", "localhost")
    os.environ.setdefault("REDIS_DB", "2")
    return RedisConfig.from_env()


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def client(config: Config) -> Client:
    app = Client(
        name=config.session,
        api_id=config.api_id,
        api_hash=config.api_hash,
        app_version=f"evgfilim1/userbot {__version__} TEST",
        device_model="Linux",
        test_mode=config.kwargs.pop("test_mode") == "1",
        in_memory=config.kwargs.pop("in_memory") == "1",
        workdir=str(config.data_location),
        **config.kwargs,
    )
    await app.start()
    yield app
    await app.stop()
