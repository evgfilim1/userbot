from unittest.mock import patch

from pyrogram import Client

from userbot.modules.commands import CommandsHandler, CommandsModule


# region Test `CommandsModule`
def test_add_callable() -> None:
    """Tests add() can be used as a callable."""

    commands = CommandsModule()

    async def handler() -> None:
        """Test handler"""
        pass

    with patch.object(
        CommandsModule,
        "add_handler",
        autospec=True,
        side_effect=CommandsModule.add_handler,
    ) as mock:
        commands.add(handler, "test1", "test2", prefix="?", usage="<usage>")

        mock.assert_called_once()

    assert len(commands._handlers) == 1


def test_add_decorator() -> None:
    """Tests add() can be used as a decorator."""
    commands = CommandsModule()

    with patch.object(
        CommandsModule,
        "add_handler",
        autospec=True,
        side_effect=CommandsModule.add_handler,
    ) as mock:

        @commands.add("test1", "test2", prefix="?", usage="<usage>")
        async def handler() -> None:
            """Test handler"""
            pass

        mock.assert_called_once()

    assert len(commands._handlers) == 1


def test_add_args() -> None:
    """Tests add() arguments are passed to the handler."""
    commands = CommandsModule()

    async def handler() -> None:
        """Test handler"""
        pass

    with patch.object(
        CommandsModule,
        "add_handler",
        autospec=True,
    ) as mock:
        commands.add(
            handler,
            "test1",
            "test2",
            prefix="?",
            usage="<usage>",
            category="test",
            hidden=True,
            handle_edits=False,
            waiting_message="test123",
            timeout=42,
        )

        h: CommandsHandler = mock.call_args.args[1]

    assert all(expected == actual for expected, actual in zip(("test1", "test2"), iter(h.commands)))
    assert h.prefix == "?"
    assert h.handler is handler
    assert h.usage == "<usage>"
    assert h.doc == handler.__doc__
    assert h.category == "test"
    assert h.hidden is True
    assert h.handle_edits is False
    assert h.waiting_message == "test123"
    assert h.timeout == 42


def test_register(client: Client) -> None:
    """Tests register() adds all handlers to pyrogram Client"""

    commands = CommandsModule()

    @commands.add("foo")
    async def foo() -> None:
        """Test handler"""
        pass

    @commands.add("bar", handle_edits=False)
    async def bar() -> None:
        """Test handler"""
        pass

    with patch.object(
        Client,
        "add_handler",
        autospec=True,
    ) as mock:
        commands.register(client)

        # Three handlers will be added: "foo", edited "foo" and "bar".
        assert mock.call_count == 3


def test_register_root(client: Client) -> None:
    """Tests register() adds all handlers + help handler to pyrogram Client"""

    commands = CommandsModule(root=True)

    @commands.add("foo")
    async def foo() -> None:
        """Test handler"""
        pass

    with patch.object(
        Client,
        "add_handler",
        autospec=True,
    ) as mock:
        commands.register(client)

        # Two handlers will be added: "foo", edited "foo", "help" and edited "help".
        assert mock.call_count == 4
        # Root CommandsModule also registers some necessary middlewares
        assert commands._middleware.has_handlers


# endregion
