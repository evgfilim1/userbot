__all__ = [
    "transcribe_message",
]

from pyrogram import Client
from pyrogram.errors import BadRequest
from pyrogram.raw import functions, types
from pyrogram.types import Message


async def transcribe_message(client: Client, message: Message) -> str | int | None:
    """Transcribes a voice message or a video note.

    Returns `None` if the message cannot be transcribed, `transcription_id` as an integer
    if the transcription is pending, or the transcribed text as a string if it's ready.
    """
    try:
        transcribed: types.messages.TranscribedAudio = await client.invoke(
            functions.messages.TranscribeAudio(
                peer=await client.resolve_peer(message.chat.id),
                msg_id=message.id,
            )
        )
    except BadRequest as e:
        if isinstance(e.value, str) and "TRANSCRIPTION_FAILED" in e.value:
            return None
        raise
    if transcribed.pending:
        return transcribed.transcription_id
    if transcribed.text == "":
        return None
    return transcribed.text
