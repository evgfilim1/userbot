#!/usr/bin/env python3
"""Helper script to check usage strings for correctness and consistency."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from userbot.meta.usage_parser import parser
except ImportError as e:
    import os
    import sys

    print(os.getcwd())
    sys.path.append(os.getcwd())  # https://stackoverflow.com/a/37927943/12519972
    print(sys.path)
    try:
        from userbot.meta.usage_parser import parser
    except ImportError as e2:
        print(e, e2, sep="\n\n")
        raise RuntimeError("This script must be run from the root of the project.") from e


@dataclass()
class Usage:
    file: Path
    line: int
    column: int
    function_name: str
    usage: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}: {self.function_name}(): {self.usage}"


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


def main() -> None:
    srcdir = Path.cwd() / "userbot"
    success = True
    for usage in all_usages(srcdir):
        try:
            parser.parse_to_raw(usage.usage)
        except Exception as e:
            print(usage, e, sep="\n")
            success = False
    if not success:
        exit(1)
    print("All `usage`s are correct and consistent.")


if __name__ == "__main__":
    main()
