__all__ = [
    "__git_commit__",
    "__version__",
]

from os import environ
from typing import Final

__git_commit__: Final[str] = environ.get("GITHUB_SHA", None)
__version__: Final[str] = "0.6.x" + ("-dev" if not __git_commit__ else "")
