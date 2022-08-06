__all__ = [
    "commands",
]

from io import BytesIO

from PIL import Image
from pyrogram import Client
from pyrogram.types import Message

from ..modules import CommandsModule

commands = CommandsModule("Colors")


def _create_filled_pic(col: str, size: tuple[int, int] = (100, 100)) -> BytesIO:
    tmp = BytesIO()
    tmp.name = "foo.png"
    im = Image.new("RGB", size, col)
    im.save(tmp, "png")
    im.close()
    tmp.seek(0)
    return tmp


@commands.add("color", usage="<color-spec>")
async def color(client: Client, message: Message, args: str) -> None:
    """Sends a specified color sample"""
    tmp = _create_filled_pic(args)
    reply = getattr(message.reply_to_message, "message_id", None)
    await client.send_photo(
        message.chat.id,
        tmp,
        caption=f"Color {args}",
        reply_to_message_id=reply,
        disable_notification=True,
    )
    await message.delete()


@commands.add("usercolor", usage="<reply>")
async def user_color(client: Client, message: Message, _: str) -> None:
    """Sends a color sample of user's color as shown in clients"""
    colors = ("e17076", "eda86c", "a695e7", "7bc862", "6ec9cb", "65aadd", "ee7aae")
    c = f"#{colors[message.reply_to_message.from_user.id % 7]}"
    tmp = _create_filled_pic(c)
    await client.send_photo(
        message.chat.id,
        tmp,
        caption=f"Your color is {c}",
        reply_to_message_id=message.reply_to_message.id,
        disable_notification=True,
    )
    await message.delete()
