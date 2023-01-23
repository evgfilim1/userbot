__all__ = [
    "create_args_parser_grammar",
]

from typing import NamedTuple

from .usage_parser import Argument, LiteralArgumentVariant, Usage, VariableArgumentVariant


class _Rule(NamedTuple):
    name: str
    definition: str

    def __str__(self) -> str:
        return f"{self.name}: {self.definition}"


_SINGLE_ARG_RULE = _Rule(name="SINGLE_ARG", definition="/[^ ]+/")
_REST_ARG_RULE = _Rule(name="REST_ARG", definition="/.+$/s")


def _parse_argument(arg: Argument, *, variant_n: int, arg_n: int) -> _Rule:
    alternatives: list[str] = []
    for i, arg_variant in enumerate(arg.variants):
        if isinstance(arg_variant, LiteralArgumentVariant):
            alternatives.append(f'"{arg_variant.value}" -> literal{variant_n}_{arg_n}_{i}')
        elif isinstance(arg_variant, VariableArgumentVariant):
            if arg_variant.kind == "identifier":
                rule = _SINGLE_ARG_RULE.name
                if arg.repeat:
                    rule = f'(({rule} " ")* {rule})'
            elif arg_variant.kind == "rest":
                rule = _REST_ARG_RULE.name
            else:
                raise ValueError(f"Unexpected child: {arg_variant}")
            alternatives.append(rule)
    if len(alternatives) == 1 and isinstance(arg.variants[0], VariableArgumentVariant):
        rule_name = arg.variants[0].name
    else:
        rule_name = f"arg{variant_n}_{arg_n}"
    return _Rule(name=rule_name, definition=" | ".join(alternatives))


def create_args_parser_grammar(usage: Usage) -> str:
    start_rules: list[str] = []
    rules: dict[str, _Rule] = {r.name: r for r in (_SINGLE_ARG_RULE, _REST_ARG_RULE)}
    for i, usage_variant in enumerate(usage.variants):
        start_rule: list[str] = []
        optionals = 0
        for j, arg in enumerate(usage_variant.args):
            rule = _parse_argument(arg, variant_n=i, arg_n=j)
            append_rule = rule.name
            if len(start_rule) > 0:
                append_rule = f'" " {append_rule}'
            if not arg.required:
                # Don't allow required arg follow optional explicitly
                optionals += 1
                append_rule = f"[{append_rule}"
            start_rule.append(append_rule)
            if (existing_rule := rules.get(rule.name)) is not None and existing_rule != rule:
                raise ValueError(
                    f"Rule {rule.name!r} already defined and is different:"
                    f" {existing_rule.definition!r} != {rule.definition!r}"
                )
            rules[rule.name] = rule
        variant_rule_name = f"v{i}"
        rules[variant_rule_name] = _Rule(
            name=variant_rule_name,
            definition=" ".join(start_rule) + "]" * optionals,
        )
        start_rules.append(variant_rule_name)
    full_start_rule = _Rule(name="?start", definition=" | ".join(start_rules))
    rules[full_start_rule.name] = full_start_rule
    return "\n".join(map(str, rules.values()))
