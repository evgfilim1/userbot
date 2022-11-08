__all__ = []

import logging
import os
from functools import partial

from pyrogram import Client
from pyrogram.handlers import RawUpdateHandler
from pyrogram.methods.utilities.idle import idle

from userbot import __version__, is_prod
from userbot.commands import commands
from userbot.commands.chat_admin import react2ban_raw_reaction_handler
from userbot.config import Config, RedisConfig
from userbot.hooks import hooks
from userbot.job_manager import AsyncJobManager
from userbot.middlewares import KwargsMiddleware, icon_middleware, translate_middleware
from userbot.modules import HooksModule
from userbot.shortcuts import shortcuts
from userbot.storage import RedisStorage, Storage
from userbot.utils import GitHubClient, fetch_stickers

logging.basicConfig(level=logging.WARNING)
_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO if is_prod else logging.DEBUG)


async def _main(
    client: Client,
    storage: Storage,
    github_client: GitHubClient,
    job_manager: AsyncJobManager,
) -> None:
    async with client, storage, github_client, job_manager:
        _log.debug("Checking for sticker cache presence...")
        cache = await storage.get_sticker_cache()
        if len(cache) == 0:
            await storage.put_sticker_cache(await fetch_stickers(client))
        job_manager.add_job(storage.sticker_cache_job(lambda: fetch_stickers(client)))
        _log.info("Bot started")
        await idle()


def main() -> None:
    _log.debug("Loading config...")
    config = Config.from_env()
    if not config.data_location.exists():
        config.data_location.mkdir()
    if not config.data_location.is_dir():
        raise NotADirectoryError(f"{config.data_location} must be a directory (`data_location`)")
    os.chdir(config.data_location)
    client = Client(
        name=config.session,
        api_id=config.api_id,
        api_hash=config.api_hash.value,
        app_version=f"evgfilim1/userbot {__version__}",
        device_model="Linux",
        workdir=str(config.data_location),
        **{k: v.value for k, v in config.kwargs.items()},
    )
    redis_config = RedisConfig.from_env()
    password = redis_config.password.value if redis_config.password else None
    storage = RedisStorage(
        redis_config.host,
        redis_config.port,
        redis_config.db,
        password,
    )
    github_client = GitHubClient()

    _log.debug("Registering handlers...")
    client.add_handler(
        RawUpdateHandler(partial(react2ban_raw_reaction_handler, storage=storage)),
        group=1,
    )

    root_hooks = HooksModule(commands=commands, storage=storage)
    root_hooks.add_submodule(hooks)

    kwargs_middleware = KwargsMiddleware(
        {
            "storage": storage,
            "data_dir": config.data_location,
            "notes_chat": config.media_notes_chat,
            "github_client": github_client,
        }
    )
    commands.add_middleware(kwargs_middleware)
    commands.add_middleware(translate_middleware)
    commands.add_middleware(icon_middleware)
    root_hooks.add_middleware(kwargs_middleware)
    root_hooks.add_middleware(translate_middleware)
    root_hooks.add_middleware(icon_middleware)
    shortcuts.add_middleware(kwargs_middleware)
    shortcuts.add_middleware(translate_middleware)
    shortcuts.add_middleware(icon_middleware)

    # `HooksModule` must be registered before `CommandsModule` because it adds some commands
    root_hooks.register(client)
    commands.register(client)
    shortcuts.register(client)

    job_manager = AsyncJobManager()

    _log.debug("Starting bot...")
    client.run(_main(client, storage, github_client, job_manager))


main()
