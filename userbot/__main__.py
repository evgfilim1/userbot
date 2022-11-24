__all__ = []

import logging
import os
from functools import partial
from itertools import product

from pyrogram import Client
from pyrogram.handlers import RawUpdateHandler
from pyrogram.methods.utilities.idle import idle

from userbot import __version__
from userbot.commands import commands
from userbot.commands.chat_admin import react2ban_raw_reaction_handler
from userbot.config import Config, RedisConfig
from userbot.hooks import hooks
from userbot.job_manager import AsyncJobManager
from userbot.middlewares import (
    KwargsMiddleware,
    icon_middleware,
    parse_command_middleware,
    translate_middleware,
    update_command_stats_middleware,
)
from userbot.modules import CommandsModule, HooksModule
from userbot.shortcuts import shortcuts
from userbot.storage import RedisStorage, Storage
from userbot.utils import GitHubClient, StatsController, fetch_stickers, get_app_limits

_log = logging.getLogger(__name__)


async def _main(
    *,
    client: Client,
    storage: Storage,
    github_client: GitHubClient,
    job_manager: AsyncJobManager,
    stats: StatsController,
    kwargs_middleware: KwargsMiddleware,
) -> None:
    async with client, storage, github_client, job_manager:
        _log.debug("Checking for sticker cache presence...")
        cache = await storage.get_sticker_cache()
        if len(cache) == 0:
            await storage.put_sticker_cache(await fetch_stickers(client))
        job_manager.add_job(storage.sticker_cache_job(lambda: fetch_stickers(client)))
        kwargs_middleware.set_arg("limits", await get_app_limits(client))
        stats.startup()
        _log.info("Bot started")
        await idle()


def main() -> None:
    config = Config.from_env()
    log_level: int = getattr(logging, config.log_level)
    logging.basicConfig(level=log_level)
    # pyrogram is too verbose IMO, silence it a bit, respecting the log level set by user
    logging.getLogger("pyrogram").setLevel(max(logging.WARNING, log_level))
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
    stats = StatsController()

    _log.debug("Registering handlers...")
    client.add_handler(
        RawUpdateHandler(partial(react2ban_raw_reaction_handler, storage=storage)),
        group=1,
    )

    root_commands = CommandsModule(default_prefix=config.command_prefix)
    root_commands.add_submodule(commands)

    root_hooks = HooksModule(commands=root_commands, storage=storage)
    root_hooks.add_submodule(hooks)

    # `HooksModule` must be present before `CommandsModule` because it adds some commands
    # when calling `register()`.
    all_modules = (root_hooks, root_commands, shortcuts)

    kwargs_middleware = KwargsMiddleware(
        {
            "storage": storage,
            "data_dir": config.data_location,
            "notes_chat": config.media_notes_chat,
            "github_client": github_client,
            "traceback_chat": config.traceback_chat,
            "stats": stats,
            "limits": None,  # will be set later
        }
    )
    root_commands.add_middleware(parse_command_middleware)
    for module, middleware in product(
        all_modules, (kwargs_middleware, translate_middleware, icon_middleware)
    ):
        module.add_middleware(middleware)
    root_commands.add_middleware(update_command_stats_middleware)

    for module in all_modules:
        module.register(client)

    job_manager = AsyncJobManager()

    _log.debug("Starting bot...")
    client.run(
        _main(
            client=client,
            storage=storage,
            github_client=github_client,
            job_manager=job_manager,
            stats=stats,
            kwargs_middleware=kwargs_middleware,
        )
    )


main()
