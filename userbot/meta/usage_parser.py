from __future__ import annotations

__all__ = [
    "Argument",
    "LiteralArgumentVariant",
    "parser",
    "Usage",
    "UsageParser",
    "UsageVariant",
    "VariableArgumentVariant",
]

from dataclasses import dataclass
from typing import Literal, TypeAlias

from lark import Lark, ParseTree

_GRAMMAR = r"""
// The Lark grammar for the usage string of evgfilim1/userbot.
//
// Usage string is a string that is passed to the `usage` keyword argument of the `commands.add`
//  decorator. It follows some rules:
// * Each argument may be required or optional;
//   * Required args are surrounded by angle brackets: `<arg>`;
//   * Optional args are surrounded by square brackets: `[arg]`;
//   * Required arguments cannot follow optional ones;
// * Each argument is usually either a literal or a variable;
//   * Literals are surrounded by single quotes: `'literal'`;
//   * Variables are just a valid ASCII identifier from Python except it cannot start with
//     an underscore: `foo`, `a1_b2_c3`, `FooBar`;
//   * Variable name cannot be "reply", this is because usage string contained a literal "reply"
//     in earlier versions that meant a reply to another message is required, but I decided to
//     remove it due to increased args parsing complexity, so now it's a reserved word;
// * Alternatives are separated by a pipe: `arg1 | arg2`;
// * The last argument may be one of:
//   * a "rest" argument ending with `...`, it means that argument consumes the rest of the string;
//     * An example would be a usage for ban command: `<user> [timeout] [reason...]`
//   * an ellipsis, it means that the argument can be repeated;
//     * If a required argument repeats, it means "one or more times";
//     * If an optional argument repeats, it means "zero or more times";
//     * An example would be a usage for invite command: `<user_id | username>...`;
// * Spaces between tokens are ignored and only improve readability of usage string;
//
// Some examples:
// * `<foo | bar | baz> ['42'] [meaningful_message...]`;
// * `<name> [id]...`;
//
// TODO:
// * Allow specifying the regex for the rule:
//   * `<username:/@\w+/ | user_id:/\d+/> <action:/(ban|kick|unban)/>`;
//   * `<sed_command: /[^\/]+\/[^\/]+\/[ig]/>`: "/" in regexp must be escaped with preceding "\";
// * Allow specifying the arguments via keywords:
//   * `<user> [timeout] [reason...]`: `reason:"calm down lol" timeout:42s user:@evgfilim1`
// * Mark default literal arguments in optional args:
//   * `<foo> ['bar'*|'baz']`: if no second argument is passed, "bar" is used;
//   * `<foo> <'bar'*|'baz'>`: invalid, required arguments cannot have a default value;

// Terminals (const)
_REQUIRED_START: "<"
_REQUIRED_END: ">"
_OPTIONAL_START: "["
_OPTIONAL_END: "]"
_ALTERNATIVE: "|"
_QUOTE: "'"
_LITERAL_START: _QUOTE
_LITERAL_END: _QUOTE
_ELLIPSIS: "..."

// Named terminals (captured user input)
LITERAL_CONTENT: /[^']+/
CNAME_NOT_REPLY_TOKEN: /(?!reply\b)[a-zA-Z][a-zA-Z0-9_]*/

// Template rules
required_arg{_p_inner}: _REQUIRED_START _p_inner _REQUIRED_END
optional_arg{_p_inner}: _OPTIONAL_START _p_inner _OPTIONAL_END
_any_arg{_p_inner}: required_arg{_p_inner} | optional_arg{_p_inner}
repeated{_p_inner}: _p_inner _ELLIPSIS
_any_repeated_arg{_p_inner}: repeated{required_arg{_p_inner}} | repeated{optional_arg{_p_inner}}

// Rules
identifier: CNAME_NOT_REPLY_TOKEN
literal: _LITERAL_START LITERAL_CONTENT _LITERAL_END
_token: identifier | literal
_tokens: (_token _ALTERNATIVE)* _token
rest_identifier: CNAME_NOT_REPLY_TOKEN _ELLIPSIS
_identifiers: (identifier _ALTERNATIVE)* identifier
_any_last_arg: _any_arg{rest_identifier} | _any_repeated_arg{_identifiers}
_optional_last_arg: optional_arg{rest_identifier} | repeated{optional_arg{_identifiers}}
usage_variant: required_arg{_tokens}* _any_last_arg?
    | required_arg{_tokens}* optional_arg{_tokens}+ _optional_last_arg?

// Main rule
usage: (usage_variant _ALTERNATIVE)* usage_variant

// Parser directives
%ignore " "
"""

_ArgumentVariant: TypeAlias = "VariableArgumentVariant | LiteralArgumentVariant"


@dataclass(kw_only=True, frozen=True)
class Usage:
    variants: list[UsageVariant]


@dataclass(kw_only=True, frozen=True)
class UsageVariant:
    args: list[Argument]


@dataclass(kw_only=True, frozen=True)
class Argument:
    required: bool
    variants: list[_ArgumentVariant]
    repeat: bool = False


@dataclass(kw_only=True, frozen=True)
class VariableArgumentVariant:
    name: str
    kind: Literal["identifier", "rest"]


@dataclass(kw_only=True, frozen=True)
class LiteralArgumentVariant:
    value: str


def _parse_usage_tree(tree: ParseTree) -> Usage:
    usage_variants = []
    for usage_variant in tree.children:
        args = []
        for arg in usage_variant.children:
            if arg.data == "repeated":
                arg = arg.children[0]
                repeat = True
            else:
                repeat = False
            required = arg.data == "required_arg"
            arg_variants = []
            for child in arg.children:
                match child.data:
                    case "identifier":
                        arg_variants.append(
                            VariableArgumentVariant(name=child.children[0], kind="identifier")
                        )
                    case "literal":
                        arg_variants.append(LiteralArgumentVariant(value=child.children[0]))
                    case "rest_identifier":
                        arg_variants.append(
                            VariableArgumentVariant(name=child.children[0], kind="rest")
                        )
                    case _:
                        raise ValueError(f"Unexpected child: {child}")
            args.append(Argument(variants=arg_variants, required=required, repeat=repeat))
        usage_variants.append(UsageVariant(args=args))
    return Usage(variants=usage_variants)


class UsageParser:
    __slots__ = ("_parser",)

    def __init__(self, grammar: str, *, start: str = "usage") -> None:
        self._parser = Lark(grammar, start=start)

    def parse_to_raw(self, usage: str) -> ParseTree:
        return self._parser.parse(usage)

    def parse(self, usage: str) -> Usage:
        return _parse_usage_tree(self.parse_to_raw(usage))


parser = UsageParser(_GRAMMAR)
