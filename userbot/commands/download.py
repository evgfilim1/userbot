__all__ = [
    "commands",
]

from pathlib import Path
from typing import Type

import aiofiles
import magic
from pyrogram import Client
from pyrogram.enums import MessageMediaType
from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..translation import Translation
from ..utils import _

_CHUNK_SIZE = 1048576 * 4  # 4 MiB

commands = CommandsModule("Download")


async def _downloader(
    client: Client,
    message: Message,
    filename: str,
    data_dir: Path,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    _ = tr.gettext
    if message.media in (
        None,
        MessageMediaType.CONTACT,
        MessageMediaType.LOCATION,
        MessageMediaType.VENUE,
        MessageMediaType.POLL,
        MessageMediaType.WEB_PAGE,
        MessageMediaType.DICE,
        MessageMediaType.GAME,
    ):
        return _("{icon} No downloadable media found").format(icon=icons.STOP)
    media_type = message.media.value
    media_dir = data_dir
    if not filename:
        media_dir /= media_type
        if not media_dir.exists():
            media_dir.mkdir()
    media = getattr(message, media_type)
    filename = filename or getattr(media, "file_name", None)
    output_io = await client.download_media(message, in_memory=True)
    output_io.seek(0)
    if not filename:
        filename = f"{message.date.strftime('%Y%m%d%H%M%S')}_{message.chat.id}_{message.id}"
        mime = getattr(media, "mime_type", None)
        if not mime:
            mime = magic.from_buffer(output_io.read(2048), mime=True)
        ext = client.guess_extension(mime)
        if not ext:
            ext = ".bin"
        filename += ext
    output_io.seek(0)
    output = media_dir / filename
    async with aiofiles.open(output, "wb") as f:
        while chunk := output_io.read(_CHUNK_SIZE):
            await f.write(chunk)
    return _("{icon} The file has been downloaded to <code>{output}</code>").format(
        icon=icons.DOWNLOAD,
        output=output,
    )


@commands.add(
    "download",
    "dl",
    usage="[reply] [filename]",
    waiting_message=_("<i>Downloading file(s)...</i>"),
)
async def download(
    client: Client,
    message: Message,
    command: CommandObject,
    data_dir: Path,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    """Downloads a file or files"""
    msg = message.reply_to_message if message.reply_to_message else message
    if msg.media_group_id:
        all_messages = await msg.get_media_group()
    else:
        all_messages = [msg]

    t = ""
    for m in all_messages:
        try:
            t += await _downloader(
                client,
                m,
                command.args if len(all_messages) == 1 else "",
                data_dir,
                icons,
                tr,
            )
        except Exception as e:
            t += f"{icons.WARNING} <code>{type(e).__name__}: {e}</code>"
        finally:
            t += "\n"
    return t
