#!/usr/bin/env python3
"""Helper script to extract strings, check and update the message catalog template."""

import difflib
import re
import sys
from argparse import ArgumentParser
from io import BytesIO

try:
    from babel.messages.catalog import Catalog, Message
    from babel.messages.extract import extract_from_dir
    from babel.messages.pofile import read_po, write_po
except ImportError as e:
    raise ImportError(
        "You need to install the `babel` package to use this script."
        " You can do so by running `pip install -r dev-requirements.txt`."
    ) from e

from userbot import __version__

# https://docs.python.org/3/library/string.html#format-string-syntax
BRACES_RE = re.compile(r"(?<!{)\{\w+(?:![rsa])?(?::[^}]+)?}")

DEFAULT_POT_NAME = "locales/evgfilim1-userbot.pot"


def extract_message_template_catalog() -> Catalog:
    """Extracts the messages from the source code and return a message catalog."""
    catalog = Catalog(
        domain="evgfilim1-userbot",
        project="evgfilim1/userbot",
        version=__version__.removesuffix("-dev"),
        copyright_holder="Evgeniy Filimonov",
        msgid_bugs_address="https://github.com/evgfilim1/userbot/issues",
    )
    for (filename, lineno, message, comments, context) in extract_from_dir(
        "userbot",
        keywords={"_": None, "__": (1, 2)},
        comment_tags=("i18n",),
    ):
        if isinstance(message, str):
            texts = (message,)
        else:
            texts = message
        flags = set()
        if any(BRACES_RE.search(text) is not None for text in texts):
            flags.add("python-brace-format")
        msg = Message(
            message,
            locations=[(f"userbot/{filename}", lineno)],
            flags=flags,
            auto_comments=comments,
        )
        msg.flags.discard("python-format")  # we don't use this
        catalog[message] = msg
    catalog.header_comment = (
        f"# =============== WARNING ===============\n"
        f"# This is an automatically generated file. Do not edit it manually. All changes will be"
        f" lost.\n"
        f"# To update this file, use `potctl.py` in the root of the project.\n"
        f"# =======================================\n#\n"
        f"{catalog.header_comment.removesuffix('#')}"
    )
    return catalog


def read_message_catalog(file: str = DEFAULT_POT_NAME) -> Catalog:
    """Reads a message catalog from a file."""
    with open(file, "rb") as f:
        return read_po(f)


def write_message_catalog(
    catalog: Catalog,
    file: str = DEFAULT_POT_NAME,
) -> None:
    """Writes a message catalog to a file."""
    if file is None:
        file = DEFAULT_POT_NAME
    with open(file, "wb") as f:
        write_po(f, catalog, width=100)


def check_write_message_template_catalog(
    catalog: Catalog,
    file: str = DEFAULT_POT_NAME,
) -> None:
    """Checks if the message catalog template is up-to-date and updates it if needed."""
    if file is None:
        file = DEFAULT_POT_NAME
    if diff_message_templates(file) is None:
        return  # up to date
    write_message_catalog(catalog, file)


def diff_message_templates(
    old_filename: str = DEFAULT_POT_NAME,
) -> bytes | None:
    """Returns the unified diff between the old and the new message catalog template."""
    if old_filename is None:
        old_filename = DEFAULT_POT_NAME
    old_catalog = read_message_catalog(old_filename)
    new_catalog = extract_message_template_catalog()

    new_catalog.creation_date = old_catalog.creation_date  # don't diff it
    for msg in old_catalog:
        msg.flags.discard("python-format")  # auto-inserted, we don't use this

    old_catalog_file = BytesIO()
    write_po(old_catalog_file, old_catalog, width=100)
    old_catalog_file.seek(0)
    new_catalog_file = BytesIO()
    write_po(new_catalog_file, new_catalog, width=100)
    new_catalog_file.seek(0)

    gen = difflib.diff_bytes(
        difflib.unified_diff,
        old_catalog_file.readlines(),
        new_catalog_file.readlines(),
        fromfile=old_filename.encode(),
        tofile=f"{DEFAULT_POT_NAME}.gen".encode(),
    )
    diff = b"".join(gen)
    if len(diff) != 0:
        return diff
    return None


def main() -> None:
    """Entry point for the script."""
    parser = ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    not_specified = object()
    actions.add_argument(
        "--diff",
        nargs="?",
        default=not_specified,
        metavar="FILE",
        help="Check if the message catalog template contained in FILE is up to date.",
    )
    actions.add_argument(
        "--write",
        nargs="?",
        default=not_specified,
        metavar="FILE",
        help="Write the message catalog template to a file FILE.",
    )
    args = parser.parse_args()
    if args.diff is not not_specified:
        if (diff := diff_message_templates(args.diff)) is not None:
            print("The message catalog template is NOT up to date.", file=sys.stderr)
            print(f"Please run `{sys.argv[0]} --write` to update it.", file=sys.stderr)
            print(diff.decode())
            sys.exit(1)
        print("The message catalog template is up to date.", file=sys.stderr)
        return
    if args.write is not not_specified:
        check_write_message_template_catalog(extract_message_template_catalog(), args.write)
        print("The message catalog template has been written.", file=sys.stderr)
        return
    raise AssertionError("This should never happen")


if __name__ == "__main__":
    main()
