__all__ = [
    "Translation",
]

from gettext import NullTranslations, translation
from pathlib import Path
from typing import Final, Iterable


class Translation:
    DOMAIN: Final[str] = "evgfilim1-userbot"
    _LOCALE_DIR = Path.cwd() / "locales"

    @classmethod
    def _get_translation(cls, language: str | None) -> NullTranslations:
        return translation(
            cls.DOMAIN,
            localedir=cls._LOCALE_DIR,
            languages=(language,) if language else None,
            fallback=True,
        )

    def __init__(self, language: str | None):
        self.tr = self._get_translation(language)

    def change_language(self, language: str | None) -> None:
        self.tr = self._get_translation(language)

    def gettext(self, message: str) -> str:
        return self.tr.gettext(message)

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        return self.tr.ngettext(singular, plural, n)

    @classmethod
    def get_available_languages(cls) -> Iterable[str]:
        yield "en"  # English is always available as fallback because source code is in English
        for lang in cls._LOCALE_DIR.iterdir():
            if (lang / "LC_MESSAGES" / f"{cls.DOMAIN}.mo").is_file():
                yield lang.name
