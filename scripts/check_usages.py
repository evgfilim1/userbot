#!/usr/bin/env python3
"""Helper script to check usage strings for correctness and consistency."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from lark import Lark, ParseTree

GRAMMAR = r"""
// The Lark grammar for the usage string of evgfilim1/userbot.
//
// Usage string is a string that is passed to the `usage` keyword argument of the `commands.add`
//  decorator. It follows some rules:
// * It is a space-separated list of arguments;
// * Each argument may be required or optional;
//   * Required args are surrounded by angle brackets: `<arg>`;
//   * Optional args are surrounded by square brackets: `[arg]`;
// * Each argument is usually either a literal or a variable;
//   * Literals are surrounded by single quotes: `'literal'`;
// * Alternatives are separated by a pipe: `arg1|arg2`;
// * The first argument may be a `<reply>` or `[reply]` argument;
//   * It is a special argument that denotes the command can be used in reply to a message;
// * The last argument may be a "rest" argument ending with `...`;
//   * It is a special argument that consumes all the remaining arguments;

usage: (usage_variant "|")* usage_variant
usage_variant: _arg{_reply_tokens}? (_arg{_tokens} | literal)* _arg{rest_identifier}?

_arg{_p_inner}: required_arg{_p_inner} | optional_arg{_p_inner}
required_arg{_p_inner}: _REQUIRED_START _p_inner _REQUIRED_END
optional_arg{_p_inner}: _OPTIONAL_START _p_inner _OPTIONAL_END

_reply_tokens: (_reply_tokens "|")* (reply | _token)
reply: _REPLY_TOKEN

_tokens: (_token "|")* _token
_token: literal | identifier
literal: "'" ASCII_NOQUOTE_STRING "'"
identifier: CNAME

rest_identifier: identifier _REST_TOKEN

ASCII_NOQUOTE_STRING: /[^'"]+/
_REQUIRED_START: "<"
_REQUIRED_END: ">"

_OPTIONAL_START: "["
_OPTIONAL_END: "]"

_REPLY_TOKEN: "reply"
_REST_TOKEN: "..."

%import common (CNAME, LETTER, DIGIT)
%ignore " "
"""


@dataclass()
class Usage:
    file: Path
    line: int
    column: int
    function_name: str
    usage: str


def all_usages(srcdir: Path) -> Iterable[Usage]:
    for path in srcdir.glob("**/*.py"):
        with path.open() as f:
            code = ast.parse(f.read())
        for node in ast.iter_child_nodes(code):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                for keyword in decorator.keywords:
                    if keyword.arg != "usage":
                        continue
                    if not isinstance(keyword.value, ast.Constant):
                        continue
                    yield Usage(
                        file=path,
                        line=keyword.value.lineno,
                        column=keyword.value.col_offset,
                        function_name=node.name,
                        usage=keyword.value.value,
                    )


def check_usage(usage: str) -> ParseTree:
    parser = Lark(GRAMMAR, start="usage")
    return parser.parse(usage)


def main() -> None:
    srcdir = Path.cwd() / "userbot"
    success = True
    for usage in all_usages(srcdir):
        try:
            check_usage(usage.usage)
        except Exception as e:
            print(
                "{file}:{line}:{column}: {function_name}(): {usage}".format(
                    file=usage.file,
                    line=usage.line,
                    column=usage.column,
                    function_name=usage.function_name,
                    usage=usage.usage,
                ),
            )
            print(e)
            success = False
    if not success:
        exit(1)
    print("All `usage`s are correct and consistent.")


if __name__ == "__main__":
    main()
