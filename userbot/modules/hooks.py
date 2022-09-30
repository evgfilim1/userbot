__all__ = [
    "HooksModule",
]

from dataclasses import dataclass
from typing import Awaitable, Callable

from pyrogram import Client
from pyrogram import filters as flt
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.types import Message

from ..storage import Storage
from ..translation import Translation
from ..utils import async_partial
from .commands import CommandsModule

_HandlerT = Callable[[Client, Message], Awaitable[None]]


async def _list_enabled_hooks(message: Message, storage: Storage, tr: Translation) -> str:
    """List enabled hooks in the chat"""
    _ = tr.gettext
    hooks = ""
    async for hook in storage.list_enabled_hooks(message.chat.id):
        hooks += f"• <code>{hook}</code>\n"
    return _("Hooks in this chat:\n{hooks}").format(hooks=hooks)


@dataclass()
class _HookHandler:
    name: str
    filters: flt.Filter
    handler: _HandlerT
    handle_edits: bool

    async def add_handler(self, message: Message, storage: Storage) -> None:
        await storage.enable_hook(self.name, message.chat.id)
        await message.delete()

    async def del_handler(self, message: Message, storage: Storage) -> None:
        await storage.disable_hook(self.name, message.chat.id)
        await message.delete()

    async def __call__(self, client: Client, message: Message, storage: Storage) -> None:
        if await storage.is_hook_enabled(self.name, message.chat.id):
            await self.handler(client, message)


class HooksModule:
    def __init__(self):
        self._handlers: list[_HookHandler] = []

    def add(
        self,
        name: str,
        filters: flt.Filter,
        *,
        handle_edits: bool = False,
    ) -> Callable[[_HandlerT], _HandlerT]:
        def _decorator(f: _HandlerT) -> _HandlerT:
            self.add_handler(
                handler=f,
                name=name,
                filters=filters,
                handle_edits=handle_edits,
            )
            return f

        return _decorator

    def add_handler(
        self,
        handler: _HandlerT,
        name: str,
        filters: flt.Filter,
        *,
        handle_edits: bool = False,
    ) -> None:
        self._handlers.append(
            _HookHandler(
                name=name,
                filters=filters,
                handler=handler,
                handle_edits=handle_edits,
            )
        )

    def add_submodule(self, module: "HooksModule") -> None:
        self._handlers.extend(module._handlers)

    def register(self, client: Client, storage: Storage, commands: CommandsModule) -> None:
        cmds = CommandsModule("Hooks")
        for handler in self._handlers:
            cmds.add_handler(
                handler.add_handler,
                [f"{handler.name}here", f"{handler.name}_here"],
                doc=f"Enable {handler.name} hook for this chat",
                hidden=True,
            )
            cmds.add_handler(
                handler.del_handler,
                [f"no{handler.name}here", f"no_{handler.name}_here"],
                doc=f"Disable {handler.name} hook for this chat",
                hidden=True,
            )
            f = flt.incoming & handler.filters
            callback = async_partial(handler, storage=storage)
            client.add_handler(MessageHandler(callback, f))
            if handler.handle_edits:
                client.add_handler(EditedMessageHandler(callback, f))
        cmds.add_handler(
            _list_enabled_hooks,
            ["hookshere", "hooks_here"],
        )
        cmds.add_handler(
            self._list_hooks,
            ["hooklist", "hook_list"],
        )
        commands.add_submodule(cmds)

    async def _list_hooks(self, tr: Translation) -> str:
        """List all available hooks"""
        _ = tr.gettext
        hooks = ""
        for handler in self._handlers:
            hooks += f"• <code>{handler.name}</code>\n"
        return _("Available hooks:\n{hooks}").format(hooks=hooks)
