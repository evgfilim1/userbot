__all__ = [
    "commands",
]

import asyncio
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import BinaryIO, Type

from PIL import Image
from pyrogram import Client
from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule

commands = CommandsModule("Content converters")


@commands.add("togif", usage="[reply]", waiting_message="<i>Converting...</i>")
async def video_to_gif(client: Client, message: Message, icons: Type[Icons]) -> str | None:
    """Converts a video to a mpeg4 gif"""
    msg = message.reply_to_message if message.reply_to_message else message
    video = msg.video
    if not video:
        return f"{icons.STOP} No video found"
    with NamedTemporaryFile(suffix=".mp4") as src, NamedTemporaryFile(suffix=".mp4") as dst:
        await client.download_media(video.file_id, src.name)
        proc = await asyncio.subprocess.create_subprocess_exec(
            "/usr/bin/env",
            "ffmpeg",
            "-hide_banner",
            "-i",
            src.name,
            "-c",
            "copy",
            "-an",
            "-movflags",
            "+faststart",
            "-y",
            dst.name,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"Process finished with error code {proc.returncode}\n{stderr.decode()}"
            )
        await msg.reply_animation(dst.name)
    if message.reply_to_message:
        await message.delete()


def _convert_to_sticker(photo: BinaryIO, fmt: str) -> BytesIO:
    img: Image.Image = Image.open(photo)
    img.thumbnail((512, 512))
    sticker = BytesIO()
    sticker.name = f"sticker.{fmt}"
    img.save(sticker, fmt)
    sticker.seek(0)
    return sticker


@commands.add(
    "tosticker",
    usage="[reply] ['png'|'webp']",
    waiting_message="<i>Converting to sticker...</i>",
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
