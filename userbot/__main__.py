import logging
import os
from functools import partial

from httpx import AsyncClient
from pyrogram import Client
from pyrogram.handlers import RawUpdateHandler
from pyrogram.methods.utilities.idle import idle

from userbot.commands import commands
from userbot.commands.chat_admin import no_react2ban, react2ban, react2ban_raw_reaction_handler
from userbot.commands.download import download
from userbot.config import Config, RedisConfig
from userbot.constants import GH_PATTERN
from userbot.hooks import check_hooks, hooks
from userbot.shortcuts import github, shortcuts
from userbot.storage import RedisStorage, Storage

logging.basicConfig(level=logging.WARNING)
_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO)


async def _main(client: Client, storage: Storage, github_client: AsyncClient) -> None:
    async with client, storage, github_client:
        _log.info("Bot started")
        await idle()


def main() -> None:
    config = Config.from_env()
    if not config.data_location.exists():
        config.data_location.mkdir()
    if not config.data_location.is_dir():
        raise NotADirectoryError(f"{config.data_location} must be a directory (`data_location`)")
    os.chdir(config.data_location)
    env_suffix = "-dev" if os.getenv("GITHUB_SHA", None) is None else ""
    client = Client(
        name=config.session,
        api_id=config.api_id,
        api_hash=config.api_hash,
        app_version=f"evgfilim1/userbot 0.3.x{env_suffix}",
        device_model="Linux",
        workdir=str(config.data_location),
        **config.kwargs,
    )
    redis_config = RedisConfig.from_env()
    storage = RedisStorage(redis_config.host, redis_config.port, redis_config.db)
    github_client = AsyncClient(base_url="https://api.github.com/", http2=True)

    commands.add_handler(
        check_hooks,
        ["hookshere", "hooks_here"],
        usage=None,
        category="Hooks",
        kwargs={"storage": storage},
    )
    commands.add_handler(
        download,
        ["download", "dl"],
        usage="[reply] [filename]",
        waiting_message="<i>Downloading file(s)...</i>",
        category="Download",
        kwargs={"data_dir": config.data_location},
    )
    commands.add_handler(
        react2ban,
        "react2ban",
        handle_edits=False,
        usage="",
        category="Chat administration",
        kwargs={"storage": storage},
    )
    commands.add_handler(
        no_react2ban,
        ["no_react2ban", "noreact2ban"],
        usage="<reply>",
        category="Chat administration",
        kwargs={"storage": storage},
    )
    shortcuts.add_handler(partial(github, client=github_client), GH_PATTERN)
    client.add_handler(
        RawUpdateHandler(partial(react2ban_raw_reaction_handler, storage=storage)),
        group=1,
    )

    commands.register(client, with_help=True)
    hooks.register(client, storage)
    shortcuts.register(client)

    client.run(_main(client, storage, github_client))


main()
