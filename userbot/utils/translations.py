__all__ = [
    "_",
    "__",
]


def _(s: str) -> str:
    """A dummy function that marks strings for translation."""
    return s


def __(one: str, many: str, n: int) -> str:
    """A dummy function that marks plural strings for translation."""
    return one if n == 1 else many
