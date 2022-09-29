from gettext import translation
from pathlib import Path
from typing import Final, Iterable


class Translation:
    DOMAIN: Final[str] = "evgfilim1-userbot"
    _LOCALE_DIR = Path.cwd() / "locales"

    def __init__(self, language: str | None):
        self.tr = translation(
            self.DOMAIN,
            localedir=self._LOCALE_DIR,
            languages=(language,) if language else None,
            fallback=True,
        )

    def gettext(self, message: str) -> str:
        return self.tr.gettext(message)

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        return self.tr.ngettext(singular, plural, n)

    @classmethod
    def get_available_languages(cls) -> Iterable[str]:
        for lang in cls._LOCALE_DIR.iterdir():
            if (lang / "LC_MESSAGES" / f"{cls.DOMAIN}.mo").is_file():
                yield lang.name
