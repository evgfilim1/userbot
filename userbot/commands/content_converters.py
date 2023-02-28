__all__ = [
    "commands",
    "transcribed_audio_raw_handler",
]

import asyncio
from io import BytesIO
from os import path
from tempfile import NamedTemporaryFile
from typing import BinaryIO

from PIL import Image
from pyrogram import Client, ContinuePropagation
from pyrogram.errors import BadRequest
from pyrogram.raw import base, functions, types
from pyrogram.types import Message
from pyrogram.utils import get_channel_id

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..storage import Storage
from ..utils import Translation, gettext

commands = CommandsModule("Content converters")


async def _call_ffmpeg(
    input_file: str,
    output_file: str,
    *args: str,
) -> None:
    """Calls ffmpeg with the given arguments."""
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


@commands.add("togif", waiting_message=gettext("<i>Converting to mpeg4gif...</i>"))
async def video_to_gif(
    client: Client,
    message: Message,
    reply: Message | None,
    icons: type[Icons],
    tr: Translation,
) -> str | None:
    """Converts a video to a mpeg4 gif."""
    _ = tr.gettext
    msg = reply if reply is not None else message
    if (video := msg.video) is None:
        return _("{icon} No video found").format(icon=icons.STOP)
    with NamedTemporaryFile(suffix=".mp4") as src, NamedTemporaryFile(suffix=".mp4") as dst:
        await client.download_media(video.file_id, src.name)
        await _call_ffmpeg(src.name, dst.name, *("-c copy -an -movflags +faststart".split()))
        await msg.reply_animation(dst.name)
    if reply is not None:
        await message.delete()


@commands.add(
    "tosticker",
    usage="['png'|'webp']",
    waiting_message=gettext("<i>Converting to sticker...</i>"),
)
async def photo_to_sticker(
    client: Client,
    message: Message,
    command: CommandObject,
    reply: Message | None,
) -> None:
    """Converts a photo to a sticker-ready png or webp.

    Both are assumed when no argument is specified.
    """
    msg = reply if reply is not None else message
    image = await client.download_media(msg, in_memory=True)
    image.seek(0)
    requested_format = command.args[0]
    if not requested_format:
        fmts = ("png", "webp")
    else:
        fmts = (requested_format,)
    for fmt in fmts:
        sticker = _convert_to_sticker(image, fmt)
        match fmt:
            case "png":
                await msg.reply_document(sticker, file_name="sticker.png")
            case "webp":
                await msg.reply_sticker(sticker)
            case _:
                raise AssertionError("Wrong format, this should never happen")
    if reply is not None:
        await message.delete()


@commands.add("toaudio", waiting_message=gettext("<i>Extracting audio...</i>"))
async def video_to_audio(
    client: Client,
    message: Message,
    reply: Message | None,
    icons: type[Icons],
    tr: Translation,
) -> str | None:
    """Extracts audio from video."""
    _ = tr.gettext
    msg = reply if reply is not None else message
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
    if reply is not None:
        await message.delete()


@commands.add("totext", reply_required=True)
async def speech_to_text(
    client: Client,
    message: Message,
    reply: Message,
    storage: Storage,
    tr: Translation,
) -> str | None:
    """Transcribes speech in voice and video messages to text."""
    _ = tr.gettext
    if reply.video_note is None and reply.voice is None:
        return _("{icon} No voice or video note found").format(icon=Icons.STOP)
    try:
        transcribed: types.messages.TranscribedAudio = await client.invoke(
            functions.messages.TranscribeAudio(
                peer=await client.resolve_peer(reply.chat.id),
                msg_id=reply.id,
            )
        )
    except BadRequest as e:
        if isinstance(e.value, str) and "TRANSCRIPTION_FAILED" in e.value:
            return _(
                "{icon} <i>Transcription failed, maybe the message has no recognizable voice?</i>"
            ).format(icon=Icons.WARNING)
        raise
    if transcribed.pending:
        await storage.save_transcription(transcribed.transcription_id, message.id)
        return _("{icon} <i>Transcription is pending...</i>").format(icon=Icons.WATCH)
    return _("{icon} <b>Transcribed text:</b>\n{text}").format(
        icon=Icons.SPEECH_TO_TEXT,
        text=transcribed.text,
    )


async def transcribed_audio_raw_handler(
    client: Client,
    update: base.Update,
    *___: dict[int, types.User | types.Chat | types.Channel],
    storage: Storage,
) -> None:
    if not isinstance(update, types.UpdateTranscribedAudio) or update.pending:
        raise ContinuePropagation()
    msg_id = await storage.get_transcription(update.transcription_id)
    if msg_id is None:
        raise ContinuePropagation()

    if isinstance(update.peer, types.PeerUser):
        chat_id = update.peer.user_id
    elif isinstance(update.peer, types.PeerChat):
        chat_id = -update.peer.chat_id
    elif isinstance(update.peer, types.PeerChannel):
        chat_id = get_channel_id(update.peer.channel_id)
    else:
        raise AssertionError("Unknown peer type")

    _ = Translation(await storage.get_chat_language(chat_id)).gettext

    await client.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=_("{icon} <b>Transcribed text:</b>\n{text}").format(
            icon=Icons.SPEECH_TO_TEXT,
            text=update.text,
        ),
    )
    await storage.delete_transcription(update.transcription_id)
