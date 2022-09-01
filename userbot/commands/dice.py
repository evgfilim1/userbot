__all__ = [
    "commands",
]

import d20
from d20 import SimpleStringifier
from pyrogram import Client
from pyrogram.types import Message

from ..modules import CommandsModule

commands = CommandsModule("Dice")


class _HTMLDiceStringifier(SimpleStringifier):
    def __init__(self):
        super().__init__()
        self._in_dropped = False

    def stringify(self, the_roll):
        self._in_dropped = False
        return super().stringify(the_roll)

    def _stringify(self, node):
        if not node.kept and not self._in_dropped:
            self._in_dropped = True
            inside = super()._stringify(node)
            self._in_dropped = False
            return f"<s>{inside}</s>"
        return super()._stringify(node)

    def _str_expression(self, node):
        return f"{self._stringify(node.roll)} = <code>{int(node.total)}</code>"

    def _str_die(self, node):
        the_rolls = []
        for val in node.values:
            inside = self._stringify(val)
            if val.number == 1 or val.number == node.size:
                inside = f"<b>{inside}</b>"
            the_rolls.append(inside)
        return ", ".join(the_rolls)


@commands.add(["roll", "dice"], usage="<dice-spec>")
async def dice(_: Client, __: Message, args: str) -> str:
    """Rolls dice according to d20.roll syntax

    More: https://github.com/avrae/d20#dice-syntax."""
    return f"🎲 {d20.roll(args, stringifier=_HTMLDiceStringifier())}"
