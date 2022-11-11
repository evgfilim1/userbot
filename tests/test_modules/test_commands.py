import string
from unittest.mock import patch

from hypothesis import assume, given
from hypothesis import strategies as st
from pyrogram import Client

from userbot.modules.base import HandlerT
from userbot.modules.commands import CommandsHandler, CommandsModule


async def _sample_handler() -> str | None:
    pass


# region Test `CommandsModule`
# TODO (2022-11-07): check expected failure cases
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


@given(
    handler=st.builds(
        CommandsHandler,
        commands=st.lists(st.text(string.ascii_letters), min_size=1),
        prefix=st.sampled_from(string.punctuation),
        handler=st.functions(like=_sample_handler),
    ),
)
def test_add_args(handler: CommandsHandler) -> None:
    """Tests add() arguments are passed to the handler."""
    assume(handler.category != "" and handler.doc != "")  # These values are considered `None`

    commands = CommandsModule()

    with patch.object(
        CommandsModule,
        "add_handler",
        autospec=True,
    ) as mock:
        commands.add(
            handler.handler,
            *handler.commands,
            prefix=handler.prefix,
            usage=handler.usage,
            doc=handler.doc,
            category=handler.category,
            hidden=handler.hidden,
            handle_edits=handler.handle_edits,
            waiting_message=handler.waiting_message,
            timeout=handler.timeout,
        )

        h: CommandsHandler = mock.call_args.args[1]

    assert all(expected == actual for expected, actual in zip(handler.commands, iter(h.commands)))
    assert h.prefix == handler.prefix
    assert h.handler is handler.handler
    assert h.usage == handler.usage
    assert h.doc == handler.doc
    assert h.category == handler.category
    assert h.hidden == handler.hidden
    assert h.handle_edits == handler.handle_edits
    assert h.waiting_message == handler.waiting_message
    assert h.timeout == handler.timeout


@given(
    handlers=st.lists(
        st.tuples(
            st.functions(like=_sample_handler),
            st.lists(st.text(string.ascii_letters), min_size=1, unique=True),
            st.booleans(),
        ),
    )
)
def test_register(handlers: list[tuple[HandlerT, list[str], bool]]) -> None:
    """Tests register() adds all handlers to pyrogram Client"""
    # Don't repeat commands between handlers
    all_commands = set()
    for _, commands, _ in handlers:
        for command in commands:
            assume(command not in all_commands)
            all_commands.add(command)

    commands = CommandsModule()
    fake_client = Client("fake", in_memory=True)
    handler_count = 0
    for handler, command_list, handle_edits in handlers:
        commands.add(handler, *command_list, handle_edits=handle_edits)
        handler_count += 1 + int(handle_edits)

    with patch.object(
        Client,
        "add_handler",
        autospec=True,
    ) as mock:
        commands.register(fake_client)

        # Three handlers will be added: "foo", edited "foo" and "bar".
        assert mock.call_count == handler_count


def test_register_root() -> None:
    """Tests register() adds a handler + help handler to pyrogram Client"""

    commands = CommandsModule(root=True)
    fake_client = Client("fake", in_memory=True)

    @commands.add("foo")
    async def foo() -> None:
        """Test handler"""
        pass

    with patch.object(
        Client,
        "add_handler",
        autospec=True,
    ) as mock:
        commands.register(fake_client)

        # Two handlers will be added: "foo", edited "foo", "help" and edited "help".
        assert mock.call_count == 4
        # Root CommandsModule also registers some necessary middlewares
        assert commands._middleware.has_handlers


# endregion
