__all__ = [
    "commands",
]

import asyncio
from io import BytesIO
from os import path
from tempfile import NamedTemporaryFile
from typing import BinaryIO, Type

from PIL import Image
from pyrogram import Client
from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..translation import Translation
from ..utils import _

commands = CommandsModule("Content converters")


async def _call_ffmpeg(
    input_file: str,
    output_file: str,
    *args: str,
) -> None:
    """Call ffmpeg with the given arguments"""
    proc = await asyncio.subprocess.create_subprocess_exec(
        "/usr/bin/env",
        "ffmpeg",
        "-hide_banner",
        "-i",
        input_file,
        *args,
        "-y",
        output_file,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    __, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Process finished with error code {proc.returncode}\n{stderr.decode()}")


def _convert_to_sticker(photo: BinaryIO, fmt: str) -> BytesIO:
    img: Image.Image = Image.open(photo)
    img.thumbnail((512, 512))
    sticker = BytesIO()
    sticker.name = f"sticker.{fmt}"
    img.save(sticker, fmt)
    sticker.seek(0)
    return sticker


@commands.add("togif", usage="[reply]", waiting_message=_("<i>Converting to mpeg4gif...</i>"))
async def video_to_gif(
    client: Client,
    message: Message,
    icons: Type[Icons],
    tr: Translation,
) -> str | None:
    """Converts a video to a mpeg4 gif"""
    _ = tr.gettext
    msg = message.reply_to_message if message.reply_to_message else message
    if (video := msg.video) is None:
        return _("{icon} No video found").format(icon=icons.STOP)
    with NamedTemporaryFile(suffix=".mp4") as src, NamedTemporaryFile(suffix=".mp4") as dst:
        await client.download_media(video.file_id, src.name)
        await _call_ffmpeg(src.name, dst.name, *("-c copy -an -movflags +faststart".split()))
        await msg.reply_animation(dst.name)
    if message.reply_to_message:
        await message.delete()


@commands.add(
    "tosticker",
    usage="[reply] ['png'|'webp']",
    waiting_message=_("<i>Converting to sticker...</i>"),
)
async def photo_to_sticker(client: Client, message: Message, command: CommandObject) -> None:
    """Converts a photo to a sticker-ready png or webp

    Both are assumed when no argument is specified."""
    msg = message.reply_to_message if message.reply_to_message else message
    image = await client.download_media(msg, in_memory=True)
    image.seek(0)
    args = command.args.lower()
    if not args:
        fmts = ("png", "webp")
    else:
        if args not in ("png", "webp"):
            raise ValueError(f"Unsupported format: {args}")
        fmts = (args,)
    for fmt in fmts:
        sticker = _convert_to_sticker(image, fmt)
        match fmt:
            case "png":
                await msg.reply_document(sticker, file_name="sticker.png")
            case "webp":
                await msg.reply_sticker(sticker)
            case _:
                raise AssertionError("Wrong format, this should never happen")
    if message.reply_to_message:
        await message.delete()


@commands.add("toaudio", usage="[reply]", waiting_message=_("<i>Extracting audio...</i>"))
async def video_to_audio(
    client: Client,
    message: Message,
    icons: Type[Icons],
    tr: Translation,
) -> str | None:
    """Extracts audio from video"""
    _ = tr.gettext
    msg = message.reply_to_message if message.reply_to_message else message
    if (video := msg.video) is None:
        return _("{icon} No video found").format(icon=icons.STOP)
    with NamedTemporaryFile(suffix=".mp4") as src, NamedTemporaryFile(suffix=".m4a") as dst:
        await client.download_media(video.file_id, src.name)
        await _call_ffmpeg(src.name, dst.name, *("-vn -acodec copy".split()))
        if video.file_name is not None:
            file_name = path.splitext(video.file_name)[0] + path.splitext(dst.name)[1]
        else:
            file_name = dst.name
        await client.send_audio(
            message.chat.id,
            dst.name,
            file_name=file_name,
            reply_to_message_id=msg.id,
        )
    if message.reply_to_message:
        await message.delete()
