__all__ = [
    "__is_prod__",
    "__version__",
]

from os import environ
from typing import Final

__is_prod__: Final[bool] = bool(environ.get("GITHUB_SHA", ""))
__version__: Final[str] = "0.4.x" + ("-dev" if not __is_prod__ else "")
