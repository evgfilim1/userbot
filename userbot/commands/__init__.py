__all__ = [
    "commands",
]

from ..modules import CommandsModule
from .about import commands as about_commands
from .chat_admin import commands as chat_admin_commands
from .chat_info import commands as chat_info_commands
from .colors import commands as colors_commands
from .content_converters import commands as content_converters_commands
from .dice import commands as dice_commands
from .download import commands as download_commands
from .messages import commands as messages_commands
from .notes import commands as notes_commands
from .reactions import commands as reactions_commands
from .reminders import commands as reminders_commands
from .stickers import commands as stickers_commands
from .text_converters import commands as text_converters_commands
from .tools import commands as tools_commands

commands = CommandsModule()

for submodule in (
    about_commands,
    chat_admin_commands,
    chat_info_commands,
    colors_commands,
    content_converters_commands,
    dice_commands,
    download_commands,
    messages_commands,
    notes_commands,
    reactions_commands,
    reminders_commands,
    stickers_commands,
    text_converters_commands,
    tools_commands,
):
    commands.add_submodule(submodule)
