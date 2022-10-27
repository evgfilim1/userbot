#!/usr/bin/env python3
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
    return catalog


def write_message_template_catalog(
    catalog: Catalog,
    file: str = DEFAULT_POT_NAME,
) -> None:
    if file is None:
        file = DEFAULT_POT_NAME
    with open(file, "wb") as f:
        write_po(f, catalog, width=100)


def is_pot_creation_date_line(line: bytes) -> bool:
    return line.startswith(b'"POT-Creation-Date')


def diff_message_templates(
    old_filename: str = DEFAULT_POT_NAME,
) -> bytes | None:
    if old_filename is None:
        old_filename = DEFAULT_POT_NAME
    with open(old_filename, "rb") as f:
        old_catalog_lines = f.readlines()
        f.seek(0)
        old_catalog = read_po(f)
    new_catalog = extract_message_template_catalog()
    new_catalog.creation_date = old_catalog.creation_date  # don't diff it
    new_catalog_file = BytesIO()
    write_po(new_catalog_file, new_catalog, width=100)
    new_catalog_file.seek(0)
    gen = difflib.diff_bytes(
        difflib.unified_diff,
        old_catalog_lines,
        new_catalog_file.readlines(),
        fromfile=old_filename.encode(),
        tofile=f"{DEFAULT_POT_NAME}.gen".encode(),
    )
    diff = b"".join(gen)
    if len(diff) != 0:
        return diff
    return None


def main() -> None:
    parser = ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    not_specified = object()
    actions.add_argument(
        "--diff",
        nargs="?",
        default=not_specified,
        metavar="FILE",
        help="Check if the template message catalog contained in FILE is up to date.",
    )
    actions.add_argument(
        "--write",
        nargs="?",
        default=not_specified,
        metavar="FILE",
        help="Write the template message catalog to a file FILE.",
    )
    args = parser.parse_args()
    if args.diff is not not_specified:
        if (diff := diff_message_templates(args.diff)) is not None:
            print("The template message catalog is NOT up to date.", file=sys.stderr)
            print(f"Please run `{sys.argv[0]} --write` to update it.", file=sys.stderr)
            print(diff.decode())
            sys.exit(1)
        print("The template message catalog is up to date.", file=sys.stderr)
        return
    if args.write is not not_specified:
        write_message_template_catalog(extract_message_template_catalog(), args.write)
        print("The template message catalog has been written.", file=sys.stderr)
        return
    raise AssertionError("This should never happen")


if __name__ == "__main__":
    main()
