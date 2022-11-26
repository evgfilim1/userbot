__all__ = [
    "commands",
]

from io import BytesIO

from PIL import Image
from pyrogram import Client
from pyrogram.types import Message

from ..constants import Icons
from ..meta.modules import CommandObject, CommandsModule
from ..utils.translations import Translation

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
async def color(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: type[Icons],
    tr: Translation,
) -> None:
    """Sends a specified color sample

    <color-spec> can be a hex color code prefixed by #, or a color name."""
    _ = tr.gettext
    color_spec = command.args
    tmp = _create_filled_pic(color_spec)
    reply = getattr(message.reply_to_message, "message_id", None)
    await client.send_photo(
        message.chat.id,
        tmp,
        caption=_("{icon} Color {color_spec}").format(icon=icons.COLOR, color_spec=color_spec),
        reply_to_message_id=reply,
        disable_notification=True,
    )
    await message.delete()


@commands.add("usercolor", usage="<reply|id>")
async def user_color(
    client: Client,
    message: Message,
    command: CommandObject,
    icons: type[Icons],
    tr: Translation,
) -> None:
    """Sends a color sample of user's color as shown in clients"""
    _ = tr.gettext
    user_id = int(command.args) if command.args else message.reply_to_message.from_user.id
    colors = ("e17076", "eda86c", "a695e7", "7bc862", "6ec9cb", "65aadd", "ee7aae")
    c = f"#{colors[user_id % 7]}"
    tmp = _create_filled_pic(c)
    await client.send_photo(
        message.chat.id,
        tmp,
        caption=_("{icon} Color of the user is {c}").format(icon=icons.COLOR, c=c),
        reply_to_message_id=message.reply_to_message.id,
        disable_notification=True,
    )
    await message.delete()
