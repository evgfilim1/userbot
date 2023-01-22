__all__ = [
    "HooksModule",
]

from typing import Any, Callable, overload

from pyrogram import Client
from pyrogram import filters as pyrogram_filters
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.handlers.handler import Handler
from pyrogram.types import Message

from ...storage import Storage
from ...utils import Translation
from . import CommandsModule
from .base import BaseHandler, BaseModule, HandlerT


class _HookEnabledFilter(pyrogram_filters.Filter):
    def __init__(self, hook_name: str, storage: Storage) -> None:
        self.storage = storage
        self.hook_name = hook_name

    async def __call__(self, client: Client, message: Message) -> bool:
        return await self.storage.is_hook_enabled(self.hook_name, message.chat.id)


async def _list_enabled_hooks(message: Message, storage: Storage, tr: Translation) -> str:
    """List enabled hooks in the chat"""
    _ = tr.gettext
    hooks = ""
    async for hook in storage.list_enabled_hooks(message.chat.id):
        hooks += f"• <code>{hook}</code>\n"
    return _("Hooks in this chat:\n{hooks}").format(hooks=hooks)


class HooksHandler(BaseHandler):
    def __init__(
        self,
        *,
        name: str,
        filters: pyrogram_filters.Filter,
        handler: HandlerT,
        handle_edits: bool,
    ) -> None:
        super().__init__(
            handler=handler,
            handle_edits=handle_edits,
            waiting_message=None,
            timeout=None,
        )
        self.name = name
        self.filters = filters

    def __repr__(self) -> str:
        name = self.name
        handle_edits = self.handle_edits
        return f"<{self.__class__.__name__} {name=} {handle_edits=}>"

    async def add_handler(self, message: Message, storage: Storage) -> None:
        await storage.enable_hook(self.name, message.chat.id)
        await message.delete()

    async def remove_handler(self, message: Message, storage: Storage) -> None:
        await storage.disable_hook(self.name, message.chat.id)
        await message.delete()

    async def _send_waiting_message(self, data: dict[str, Any]) -> None:
        return


class HooksModule(BaseModule):
    def __init__(
        self,
        commands: CommandsModule | None = None,
        storage: Storage | None = None,
    ) -> None:
        super().__init__()
        self.commands = commands
        self.storage = storage

    @overload
    def add(
        self,
        name: str,
        filters_: pyrogram_filters.Filter,
        none: None = None,
        /,
        *,
        handle_edits: bool = False,
    ) -> Callable[[HandlerT], HandlerT]:
        # usage as a decorator
        pass

    @overload
    def add(
        self,
        callable_: HandlerT,
        name: str,
        filters_: pyrogram_filters.Filter,
        /,
        *,
        handle_edits: bool = False,
    ) -> None:
        # usage as a function
        pass

    def add(
        self,
        callable_or_name: HandlerT | str,
        name_or_filters: str | pyrogram_filters.Filter,
        filters_: pyrogram_filters.Filter | None = None,
        /,
        *,
        handle_edits: bool = False,
    ) -> Callable[[HandlerT], HandlerT] | None:
        """Registers a hook handler. Can be used as a decorator or as a registration function.

        Example:
            Example usage as a decorator::

                hooks = HooksModule()
                @hooks.add("hello", filters.regex(r"(hello|hi)"))
                async def hello_hook(message: Message, command: CommandObject) -> str:
                    return "Hello!"

            Example usage as a function::

                hooks = HooksModule()
                def hello_hook(message: Message, command: CommandObject) -> str:
                    return "Hello!"
                hooks.add(hello_hook, "hello", filters.regex(r"(hello|hi)"))

        Returns:
            The original handler function if used as a decorator, otherwise `None`.
        """

        def decorator(handler: HandlerT) -> HandlerT:
            self.add_handler(
                HooksHandler(
                    name=name_or_filters,
                    filters=filters_,
                    handler=handler,
                    handle_edits=handle_edits,
                )
            )
            return handler

        if callable(callable_or_name):
            if filters_ is None:
                raise TypeError("No filters specified")
            decorator(callable_or_name)
            return

        filters_ = name_or_filters
        name_or_filters = callable_or_name
        return decorator

    def _create_handlers_filters(
        self,
        handler: HooksHandler,
    ) -> tuple[list[type[Handler]], pyrogram_filters.Filter]:
        h: list[type[Handler]] = [MessageHandler]
        if handler.handle_edits:
            h.append(EditedMessageHandler)
        return (
            h,
            pyrogram_filters.incoming
            & _HookEnabledFilter(handler.name, self.storage)
            & handler.filters,
        )

    def register(self, client: Client) -> None:
        if self.commands is None:
            raise RuntimeError("Please set commands attribute before registering hooks module")
        if self.storage is None:
            raise RuntimeError("Please set storage attribute before registering hooks module")
        commands = CommandsModule("Hooks")
        commands.add(
            _list_enabled_hooks,
            "hookshere",
            "hooks_here",
        )
        commands.add(
            self._list_hooks,
            "hooklist",
            "hook_list",
        )
        for handler in self._handlers:
            commands.add(
                handler.add_handler,
                f"{handler.name}here",
                f"{handler.name}_here",
                doc=f"Enable {handler.name} hook for this chat",
                hidden=True,
            )
            commands.add(
                handler.remove_handler,
                f"no{handler.name}here",
                f"no_{handler.name}_here",
                doc=f"Disable {handler.name} hook for this chat",
                hidden=True,
            )
        super().register(client)
        self.commands.add_submodule(commands)

    async def _list_hooks(self, tr: Translation) -> str:
        """List all available hooks"""
        _ = tr.gettext
        hooks = ""
        for handler in self._handlers:
            hooks += f"• <code>{handler.name}</code>\n"
        return _("Available hooks:\n{hooks}").format(hooks=hooks)
