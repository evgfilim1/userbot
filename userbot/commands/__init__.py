__all__ = [
    "commands",
    "download",
]

from .about import commands as about_commands
from .chat_admin import commands as chat_admin_commands
from .colors import commands as colors_commands
from .content_converters import commands as content_converters_commands
from .dice import commands as dice_commands
from .download import download
from .messages import commands as messages_commands
from .reactions import commands as reactions_commands
from .reminders import commands as reminders_commands
from .stickers import commands as stickers_commands
from .text_converters import commands as text_converters_commands
from .tools import commands as tools_commands
from ..modules import CommandsModule

commands = CommandsModule()

for submodule in (
    about_commands,
    chat_admin_commands,
    colors_commands,
    content_converters_commands,
    dice_commands,
    messages_commands,
    reactions_commands,
    reminders_commands,
    stickers_commands,
    text_converters_commands,
    tools_commands,
):
    commands.add_submodule(submodule)
