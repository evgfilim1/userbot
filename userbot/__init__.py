__all__ = [
    "is_prod",
    "__version__",
]

from os import environ
from typing import Final

is_prod: Final[bool] = bool(environ.get("GITHUB_SHA", ""))
__version__: Final[str] = "0.5.x" + ("-dev" if not is_prod else "")
