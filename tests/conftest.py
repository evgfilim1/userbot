from __future__ import annotations

import asyncio
import json
import os
import random
from typing import AsyncIterable

import pytest
import pytest_asyncio
from pyrogram import Client
from pyrogram.types import TermsOfService, User

from userbot import __version__
from userbot.config import Config, RedisConfig
from userbot.utils import SecretStr


@pytest.fixture(scope="session")
def config() -> Config:
    os.environ.setdefault("SESSION", "test")
    # https://github.com/telegramdesktop/tdesktop/blob/a4b0443/Telegram/cmake/telegram_options.cmake#L15-L18
    os.environ.setdefault("API_ID", "17349")
    os.environ.setdefault("API_HASH", "344583e45741c457fe1862106095a5eb")

    config = Config.from_env()

    config.kwargs.setdefault("test_mode", SecretStr("1"))
    config.kwargs.setdefault("in_memory", SecretStr("1"))
    if config.kwargs.get("phone_number", None) is None:
        try:
            with open(config.data_location / ".test_phone.json") as f:
                phone_number, phone_code = json.load(f)
        except FileNotFoundError:
            dc_n = str(random.randint(1, 3))
            random_n = f"{random.randint(0, 9999):4d}"
            # https://docs.pyrogram.org/topics/test-servers#test-numbers
            phone_number = f"99966{dc_n}{random_n}"
            phone_code = dc_n * 5
            try:
                with open(config.data_location / ".test_phone.json", "w") as f:
                    json.dump([phone_number, phone_code], f)
            except OSError:
                pass
        config.kwargs["phone_number"] = SecretStr(phone_number)
        config.kwargs["phone_code"] = SecretStr(phone_code)

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
async def client(config: Config) -> AsyncIterable[Client]:
    in_memory = config.kwargs.pop("in_memory") == "1"
    app = Client(
        name=config.session,
        api_id=config.api_id,
        api_hash=config.api_hash.value,
        app_version=f"evgfilim1/userbot {__version__} TEST",
        device_model="Linux",
        test_mode=config.kwargs.pop("test_mode") == "1",
        in_memory=in_memory,
        workdir=str(config.data_location),
        **config.kwargs,
    )
    # Make sure we are registered, register otherwise
    is_authorized = await app.connect()
    if not is_authorized:
        phone_number = config.kwargs["phone_number"].value
        code = await app.send_code(phone_number)
        signed_in = await app.sign_in(
            phone_number, code.phone_code_hash, config.kwargs["phone_code"].value
        )
        if not isinstance(signed_in, User):
            await app.sign_up(
                phone_number,
                code.phone_code_hash,
                f"Test {phone_number[-4:]}",
            )
            if isinstance(signed_in, TermsOfService):
                await app.accept_terms_of_service(signed_in.id)
    await app.disconnect()
    await app.start()
    yield app
    if in_memory:
        await app.log_out()
    else:
        await app.stop()
