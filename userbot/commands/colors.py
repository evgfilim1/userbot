__all__ = [
    "commands",
]

from io import BytesIO

from PIL import Image
from pyrogram import Client
from pyrogram.types import Message

from ..constants import Icons
from ..meta.modules import CommandsModule
from ..middlewares import CommandObject
from ..storage import Storage
from ..utils import Translation, resolve_users

commands = CommandsModule("Colors")


def _create_filled_pic(col: str, size: tuple[int, int] = (100, 100)) -> BytesIO:
    tmp = BytesIO()
    tmp.name = "foo.png"
    im = Image.new("RGB", size, col)
    im.save(tmp, "png")
    im.close()
    tmp.seek(0)
    return tmp


@commands.add("color", usage="<color_spec>")
async def color(
    client: Client,
    message: Message,
    command: CommandObject,
    tr: Translation,
) -> None:
    """Sends a specified color sample.

    <color-spec> can be a hex color code prefixed by #, or a color name.
    """
    _ = tr.gettext
    color_spec = command.args[0]
    tmp = _create_filled_pic(color_spec)
    reply = getattr(message.reply_to_message, "message_id", None)
    await client.send_photo(
        message.chat.id,
        tmp,
        caption=_("{icon} Color {color_spec}").format(icon=Icons.COLOR, color_spec=color_spec),
        reply_to_message_id=reply,
        disable_notification=True,
    )
    await message.delete()


@commands.add("usercolor", usage="[user_id|username|user_group]")
async def user_color(
    client: Client,
    message: Message,
    command: CommandObject,
    storage: Storage,
    reply: Message,
    tr: Translation,
) -> None:
    """Sends a color sample of user's color as shown in clients."""
    _ = tr.gettext
    user = command.args[0]
    if user is not None:
        user_ids = await resolve_users(client, storage, user)
        if len(user_ids) == 0:
            return _("{icon} No users were specified").format(icon=Icons.STOP)
        if len(user_ids) > 1:
            return _("{icon} Multiple user are not supported here").format(icon=Icons.STOP)
        user_id = user_ids.pop()
    else:
        user_id = reply.from_user.id
    colors = ("e17076", "eda86c", "a695e7", "7bc862", "6ec9cb", "65aadd", "ee7aae")
    c = f"#{colors[user_id % 7]}"
    tmp = _create_filled_pic(c)
    await client.send_photo(
        message.chat.id,
        tmp,
        caption=_("{icon} Color of the user {user} is {c}").format(
            icon=Icons.COLOR,
            user=user_id,
            c=c,
        ),
        reply_to_message_id=message.reply_to_message_id,
        disable_notification=True,
    )
    await message.delete()
