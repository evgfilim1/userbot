__all__ = [
    "commands",
]

import asyncio
from tempfile import NamedTemporaryFile

from PIL import Image
from pyrogram import Client
from pyrogram.types import Message

from ..modules import CommandsModule

commands = CommandsModule("Content converters")


@commands.add("togif", usage="[reply]", waiting_message="<i>Converting...</i>")
async def video_to_gif(client: Client, message: Message, __: str) -> str | None:
    """Converts a video to a mpeg4 gif"""
    msg = message.reply_to_message if message.reply_to_message else message
    video = msg.video
    if not video:
        return "⚠ No video found"
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


@commands.add(
    "tosticker",
    usage="[reply] ['png'|'webp']",
    waiting_message="<i>Converting to sticker...</i>",
)
async def photo_to_sticker(client: Client, message: Message, args: str) -> None:
    """Converts a photo to a sticker-ready png or webp

    'png' is assumed when no argument is specified."""
    msg = message.reply_to_message if message.reply_to_message else message
    output_io = await client.download_media(msg, in_memory=True)
    output_io.seek(0)
    im: Image.Image = Image.open(output_io)
    im.thumbnail((512, 512))
    output_io.seek(0)
    fmt = args.lower() if args else "png"
    if fmt not in ("png", "webp"):
        raise ValueError(f"Unsupported format: {fmt}")
    im.save(output_io, args or "png")
    output_io.seek(0)
    output_io.name = f"sticker.{fmt}"
    match fmt:
        case "png":
            await msg.reply_document(output_io, file_name="sticker.png")
        case "webp":
            await msg.reply_sticker(output_io)
        case _:
            raise AssertionError("Wrong format, this should never happen")
    if message.reply_to_message:
        await message.delete()
