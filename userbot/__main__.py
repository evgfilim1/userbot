__all__: list[str] = []

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
from userbot.config import AppConfig, RedisConfig, StorageConfig, TelegramConfig
from userbot.hooks import hooks
from userbot.meta.job_manager import AsyncJobManager
from userbot.meta.modules import CommandsModule, HooksModule
from userbot.middlewares import (
    KwargsMiddleware,
    ParseCommandMiddleware,
    icon_middleware,
    translate_middleware,
    update_command_stats_middleware,
)
from userbot.shortcuts import shortcuts
from userbot.storage import RedisStorage, Storage
from userbot.utils import (
    AppLimitsController,
    GitHubClient,
    SecretValue,
    StatsController,
    fetch_stickers,
)

_log = logging.getLogger(__name__)


async def _fetch_and_put_stickers_to_cache(storage: Storage, client: Client) -> None:
    await storage.put_sticker_cache(await fetch_stickers(client))


async def _main(
    *,
    client: Client,
    storage: Storage,
    github_client: GitHubClient,
    job_manager: AsyncJobManager,
    stats: StatsController,
    app_limits_controller: AppLimitsController,
) -> None:
    async with client, storage, github_client, job_manager:
        _log.debug("Checking for sticker cache presence...")
        cache = await storage.get_sticker_cache()
        if len(cache) == 0:
            # don't wait for it, let it run in the background
            job_manager.add_job(_fetch_and_put_stickers_to_cache(storage, client))
        job_manager.add_job(storage.sticker_cache_job(lambda: fetch_stickers(client)))
        await app_limits_controller.load_limits(client)
        stats.startup()
        _log.info("Bot started")
        await idle()


def main() -> None:
    app_config = AppConfig.from_env()
    logging.basicConfig(level=app_config.log_level.upper())
    # pyrogram is too verbose IMO, silence it a bit, respecting the log level set by user
    logging.getLogger("pyrogram").setLevel(max(logging.WARNING, logging.root.level))

    storage_config = StorageConfig.from_env()
    if not storage_config.data_location.exists():
        storage_config.data_location.mkdir()
    os.chdir(storage_config.data_location)

    telegram_config = TelegramConfig.from_env()
    client = Client(
        name=storage_config.session_name,
        api_id=telegram_config.api_id,
        api_hash=telegram_config.api_hash.value,
        app_version=f"evgfilim1/userbot {__version__}",
        device_model="Linux",
        workdir=str(storage_config.data_location),
        **{
            k: (v.value if isinstance(v, SecretValue) else v)
            for k, v in telegram_config.pyrogram_kwargs.items()
        },
    )

    redis_config = RedisConfig.from_env()
    password = redis_config.password.value if redis_config.password else None
    storage = RedisStorage(
        redis_config.host,
        redis_config.port,
        redis_config.db,
        password,
    )

    # third_party_services_config = ThirdPartyServicesConfig.from_env()
    github_client = GitHubClient()

    stats = StatsController()
    app_limits = AppLimitsController()

    _log.debug("Registering handlers...")
    client.add_handler(
        RawUpdateHandler(partial(react2ban_raw_reaction_handler, storage=storage)),
        group=1,
    )

    root_commands = CommandsModule(default_prefix=app_config.command_prefix)
    root_commands.add_submodule(commands)

    root_hooks = HooksModule(commands=root_commands, storage=storage)
    root_hooks.add_submodule(hooks)

    # `HooksModule` must be present before `CommandsModule` because it adds some commands
    # when calling `register()`.
    all_modules = (root_hooks, root_commands, shortcuts)

    kwargs_middleware = KwargsMiddleware(
        {
            "storage": storage,
            "data_dir": storage_config.data_location,
            "notes_chat": app_config.media_notes_chat,
            "github_client": github_client,
            "traceback_chat": app_config.tracebacks_chat,
            "stats": stats,
            "limits": app_limits,
            "allow_unsafe": app_config.allow_unsafe_commands,
        }
    )
    for module, middleware in product(
        all_modules, (kwargs_middleware, translate_middleware, icon_middleware)
    ):
        module.add_middleware(middleware)
    root_commands.add_middleware(ParseCommandMiddleware(app_config.command_prefix))
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
            app_limits_controller=app_limits,
        )
    )


main()
